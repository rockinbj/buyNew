import math
import time

from exchangeConfig import *
from functions import *
from logSet import *


# symbol = "CORE/USDT"
# tradingTime = 1673935200
symbol = "BLUR/USDT"
tradingTime = int(time.time()) + 10

buyParas = [
    # [price, amountCoins]
    # 定义多个买入策略，在哪个价格挂单买入多少个币
    # [70, 0.7],
    [0.1, 200],
]

sellParas = [
    # [times, amountU]
    # 定义多个卖出策略，[在成交价多少倍数挂单卖出, 挂单百分比]
    # [2, 0.5], 以买入价2倍挂卖单，挂买入数量50%的币
    [2, 0.5],
    [5, 0.5],
]


def main():
    logger.info(f"\n\n\n当前交易所：{EXCHANGE} 当前币种：{symbol}")
    ex = getattr(ccxt, EXCHANGE)(EXCHANGE_CONFIG)

    mkts = ex.loadMarkets()
    # tks = ex.fetchTicker(symbol)
    mkt = mkts[symbol]

    symbolId = mkt["id"]
    precisionAmount = mkt["precision"]["amount"]
    minAmount = mkt["limits"]["amount"]["min"]
    minCost = mkt["limits"]["cost"]["min"]
    logger.debug(f"{symbolId} precisionAmount:{precisionAmount} minAmount:{minAmount} minCost:{minCost}")
    logger.debug(f"币种信息：{mkt}")

    orderIdsBuy = []
    orderIdsSell = []

    tradingTimeStr = dt.datetime.fromtimestamp(tradingTime).strftime('%Y-%m-%d %H:%M:%S')
    logger.info(f"{symbol}抢新准备就绪，等待开始时间{tradingTimeStr}")
    while True:
        if time.time() >= tradingTime:
            logger.info("时间到！开始下单！")

            for bp in buyParas:
                price = bp[0]
                price = ex.priceToPrecision(symbol, price)
                amount = max(bp[1], minAmount)
                amount = ex.amountToPrecision(symbol, amount)
                logger.debug(f"买单要求: price-{price} amount-{amount}")

                for i in range(TRY_TIMES):
                    try:
                        order = ex.createOrder(symbol, type="limit", side="buy", price=price, amount=amount)
                        orderId = order["id"]
                        logger.debug(f"{symbol}买入订单已提交，orderId: {orderId} price:{price} amount:{amount}")
                        orderIdsBuy.append(orderId)
                        break
                    except Exception as e:
                        logger.error(f"提交买单报错{symbol} {price} {amount}: {e}")
                        logger.exception(e)
                        if i == TRY_TIMES - 1: raise RuntimeError(f"下买单失败次数过多，退出。")
                        continue

            logger.debug(f"orderBuyList: {orderIdsBuy}")
            time.sleep(SLEEP_MEDIUM)
            for id in orderIdsBuy:
                if id:
                    for i in range(TRY_TIMES):
                        try:
                            orderInfo = ex.fetchOrder(id, symbol)

                            if orderInfo["status"] == "closed":
                                price = orderInfo["average"]
                                amount = orderInfo["filled"] - orderInfo["fee"]["cost"]
                                logger.info(f"√√√ 买入成功 {symbol} √√√   "
                                            f"实际成交参数: price:{price} amount:{amount}")
                                break
                            else:
                                logger.info(
                                    f"买入订单状态未成交{symbol} price:{price} amount:{amount} : {orderInfo['status']} 过1s重试"
                                    )
                                time.sleep(SLEEP_LONG)
                                continue

                        except Exception as e:
                            logger.error(f"{symbol}获取订单信息失败，重试{e}")
                            logger.exception(e)
                            if i == TRY_TIMES - 1:
                                logger.error(f"{symbol}获取订单信息多次失败，无法完成后续平仓，请手动平仓。")
                                raise
                            time.sleep(SLEEP_MEDIUM)
                            continue

                    for orderInfo in sellParas:
                        logger.debug(f"卖单要求: {orderInfo}")
                        times = orderInfo[0]
                        pct = orderInfo[1]
                        tk = ex.fetchTicker(symbol)
                        priceThisTime = price * times
                        amountThisTime = amount * pct
                        # amount *= priceBuy1
                        # price = ex.priceToPrecision(symbol, price)
                        # amount = max(amount, minAmount)
                        if minCost and amountThisTime * priceThisTime < minCost:
                            amountThisTime = math.ceil(minCost / priceThisTime)
                        logger.debug(f"卖单参数: times-{times} pct-{pct} priceThisTime-{priceThisTime} amountThisTime-{amountThisTime}")
                        for i in range(TRY_TIMES):
                            try:
                                order = ex.createOrder(symbol, type="limit", side="sell", price=priceThisTime, amount=amountThisTime)
                                # print(order)
                                orderId = order["id"]
                                orderPrice = order["price"]
                                orderAmount = order["amount"]
                                logger.debug(f"{symbol}卖出订单已提交，orderId: {orderId} price:{orderPrice} amount:{orderAmount}")
                                orderIdsSell.append(order["id"])
                                break
                            except Exception as e:
                                logger.error(f"提交卖单报错{symbol} {priceThisTime} {amountThisTime}: {e}")
                                logger.exception(e)
                                if i == TRY_TIMES - 1: raise RuntimeError(f"下卖单失败次数过多，退出。")
                                time.sleep(0.002)
                                continue

            break
        time.sleep(0.005)

    logger.info("任务结束")
    exit()


if __name__ == "__main__":

    while True:
        try:
            start = time.time()
            main()
            logger.info(f"用时{round(time.time() - start, 2)}s")
        except ccxt.BadSymbol as e:
            logger.info(f"{symbol}交易对未开启,继续等待")
            logger.exception(e)
            time.sleep(SLEEP_MEDIUM)
            continue
