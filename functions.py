import time
import ccxt
import requests
import numpy as np
import pandas as pd
from testConfig import *
from exchangeConfig import *
from logSet import *

RULE = "USDT"
MARKET = "spot"
MIN_SPOT_COST = 1.0
logger = logging.getLogger("app.func")


def testfun(msg):
    logger.info(msg)


def sendMixin(msg, _type="PLAIN_TEXT"):
    MIXIN_TOKEN = "mrbXSz6rSoQjtrVnDlOH9ogK8UubLdNKClUgx1kGjGoq39usdEzbHlwtFIvHHO3C"
    token = MIXIN_TOKEN
    url = f"https://webhook.exinwork.com/api/send?access_token={token}"
    value = {
        'category': _type,
        'data': msg,
        }
    
    r = requests.post(url, data=value, timeout=2).json()
    if r["success"] is False:
        logger.warning(f"Mixin failure: {r.text}")


def sendAndRaise(msg):
    logger.error(msg)
    sendMixin(msg)
    raise RuntimeError(msg)

def getReport(df):
    _df = df.copy()
    report = pd.DataFrame()

    report.loc[0, "轮动池"] = "-".join(SYMBOLS)
    report.loc[0, "轮动周期"] = LEVEL
    report.loc[0, "测试区间"] = f"{TEST_START}~{TEST_END}"
    report.loc[0, "最终净值"] = round(_df.iloc[-1]["equity"],2)

    # 计算年化 apy = (equityEnd/equityStart) ** tradeTimesPerYear - 1
    times = "1 days 00:00:00" / (_df.iloc[-1]["candle_begin_time"] - _df.iloc[0]["candle_begin_time"]) * 365
    apy = (_df.iloc[-1]["equity"]) ** times - 1
    report.loc[0, "年化收益"] = round(apy, 2)

    # 计算最大回撤
    # https://mp.weixin.qq.com/s/Dwt4lkKR_PEnWRprLlvPVw
    temp = _df[["candle_begin_time", "equity"]].copy()
    temp["candle_begin_time"] = pd.to_datetime(temp["candle_begin_time"])
    temp["max2here"] = temp["equity"].expanding().max()
    temp["dd2here"] = temp["equity"] / temp["max2here"]
    endTime, remains = tuple(temp.sort_values(by=["dd2here"]).iloc[0][["candle_begin_time", "dd2here"]])
    startTime = temp[temp["candle_begin_time"]<=endTime].sort_values(by="equity", ascending=False).iloc[0]["candle_begin_time"]
    report.loc[0, "最大回撤"] = round(1-remains, 2)
    report.loc[0, "最大回撤开始时间"] = startTime
    report.loc[0, "最大回撤结束时间"] = endTime

    # 计算收益回撤比
    report.loc[0, "收益回撤比"] = round(report.loc[0, "年化收益"]/report.loc[0, "最大回撤"], 2)

    # 计算交易次数
    _dfG = _df.groupby("actionTime")
    
    faultTimes = _dfG["equity"].apply(lambda x: 1 if (x.iloc[-1]-x.iloc[0])<=0 else 0).sum()
    winTimes = len(_dfG) - faultTimes
    report.loc[0, "交易次数"] = len(_dfG)
    report.loc[0, "盈利次数"] = winTimes
    report.loc[0, "亏损次数"] = faultTimes
    report.loc[0, "胜率"] = round(winTimes/len(_dfG), 2)
    

    # 计算持仓时间
    minPeriod = (_df.iloc[1]["candle_begin_time"] - _df.iloc[0]["candle_begin_time"]) / pd.Timedelta(hours=1)
    holdMin = _df.groupby("actionTime").apply(lambda x: x.iloc[-1]["candle_begin_time"] - x.iloc[0]["candle_begin_time"]).min()
    holdMin /= pd.Timedelta(hours=1)
    holdMax = _df.groupby("actionTime").apply(lambda x: x.iloc[-1]["candle_begin_time"] - x.iloc[0]["candle_begin_time"]).max()
    holdMax /= pd.Timedelta(hours=1)
    holdAvg = _df.groupby("actionTime").apply(lambda x: x.iloc[-1]["candle_begin_time"] - x.iloc[0]["candle_begin_time"]).mean()
    holdAvg /= pd.Timedelta(hours=1)
    report.loc[0, "最长持仓(小时)"] = max(round(holdMax, 1), round(minPeriod, 1))
    report.loc[0, "最短持仓"] = max(round(holdMin, 1), round(minPeriod, 1))
    report.loc[0, "平均持仓"] = max(round(holdAvg, 1), round(minPeriod, 1))

    # 计算币种持仓时间，按币种和订单排序以后计算candle_begin_time最大值与最小值的差值np.ptp()
    temp = _df.groupby(["chosen", "actionTime"])["candle_begin_time"]
    totleTime = dict.fromkeys(SYMBOLS, 0)
    for name,content in temp:
        hoursSum = np.ptp(content) / pd.Timedelta(hours=1)
        totleTime[name[0]] += max(round(hoursSum, 1), round(minPeriod, 1))
    
    for symbol in SYMBOLS:
        report.loc[0, f"{symbol}持仓时间"] = totleTime[symbol]
    
    return report


def getKlines(exchangeId, level, amount, symbols):
    # getKlines要在子进程里使用，进程之间不能直接传递ccxt实例，因此只能在进程内部创建实例
    exchange = getattr(ccxt, exchangeId)(EXCHANGE_CONFIG)
    amount += 10
    klines = dict.fromkeys(symbols, None)

    for symbol in symbols:
        k = exchange.fetchOHLCV(symbol, level, limit=amount)
        k = pd.DataFrame(k, columns=[
            "candle_begin_time",
            "open",
            "high",
            "low",
            "close",
            "volume"
        ])
        k.drop_duplicates(subset=["candle_begin_time"], keep="last", inplace=True)
        k.sort_values(by="candle_begin_time", inplace=True)
        k["candle_begin_time"] = pd.to_datetime(k["candle_begin_time"], unit="ms") + dt.timedelta(hours=8)
        k = k[:-1]
        klines[symbol] = k
        logger.debug(f"获取到{symbol} k线{len(k)}根")

        if len(symbols)>1: time.sleep(SLEEP_SHORT)

    return klines

def getPositions(exchange):
    # swap positions:
    # info    id  contracts  contractSize  unrealizedPnl  leverage liquidationPrice  collateral  notional markPrice  entryPrice timestamp  initialMargin  initialMarginPercentage  maintenanceMargin  maintenanceMarginPercentage marginRatio datetime marginMode marginType  side  hedged percentage
    # spot positions:
    # free
    try:
        if MARKET == "swap":
            p = exchange.fetchPositions()
            p = pd.DataFrame(p)
            p.set_index("symbol", inplace=True)
            p.index.name = None
            return p
        elif MARKET == "spot":
            p = exchange.fetchBalance()["free"]
            p = pd.DataFrame.from_dict(p, orient="index", columns=["free"])
            return p
    except Exception as e:
        logger.exception(e)
        sendAndRaise(f"{STRATEGY_NAME}: getPositions()错误, 程序退出。{e}")


def getOpenPosition(exchange):
    pos = getPositions(exchange)

    if MARKET == "swap":
        op = pos.loc[pos["contracts"] != 0]
        op = op.astype(
            {
                "contracts": float,
                "unrealizedPnl": float,
                "leverage": float,
                "liquidationPrice": float,
                "collateral": float,
                "notional": float,
                "markPrice": float,
                "entryPrice": float,
                "marginType": str,
                "side": str,
                "percentage": float,
                "timestamp": float,
            }
        )
        op = op[["contracts", "notional", "percentage", "unrealizedPnl", "leverage", "entryPrice", "markPrice",
                 "liquidationPrice", "datetime", "side", "marginType", "timestamp"]]
        return op

    elif MARKET == "spot":
        quote = ["USDT", "BUSD", "USDC"]
        op = pos.loc[(pos["free"] != 0) & ~pos.index.isin(quote)]
        if not op.empty:
            op = op.rename(index=lambda s: f"{s}/{RULE}")
            for s,row in op.iterrows():
                op.loc[s, "price"] = exchange.fetchTicker(s)["last"]
                op.loc[s, "cost"] = op.loc[s, "price"] * op.loc[s, "free"]
            op = op[op["cost"] > MIN_SPOT_COST]
        return op


def getBalance(exchange, asset="usdt"):
    symbol = asset.upper()
    b = exchange.fetchBalance()[symbol]
    # b = {'free': 18.89125761, 'used': 27.08454256, 'total': 45.97736273}
    return b


def closePositionForce(exchange, markets, openPostions, symbol=None):
    # 如果没有symbol参数, 清空所有持仓, 如果有symbol只平仓指定币种
    for s, pos in openPostions.iterrows():
        if symbol is not None and s != symbol: continue
        symbolId = markets[s]["id"]
        para = {
            "symbol": symbolId,
            "side": "SELL",
            "type": "MARKET",
            "quantity": pos["contracts"],
            "reduceOnly": True,
        }
        try:
            exchange.fapiPrivatePostOrder(para)
        except Exception as e:
            logger.error(f"closePositionForce({s})强制平仓出错: {e}")
            logger.exception(e)
