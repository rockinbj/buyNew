import math

from functions import *
from logSet import *


# symbol = "wAXL/USDT"
# tradingTime = 1676455199
symbol = "BLUR/USDT"
tradingTime = int(time.time()) + 7

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
    [1.5, 1],
    # [3, 0.3],
]


def main():
    logger.info(f"\n\n\n当前交易所：{EXCHANGE} 当前币种：{symbol}")
    if EXCHANGE == "mexc":
        logger.warning(f"!!!注意 MEXC 交易所对API只开放 指定交易对，请检查 {symbol} 是否在列!!!")
    elif EXCHANGE == "kucoin":
        logger.warning(f"KUCOIN 交易所的API地址白名单有bug，记得交易完重新开启API地址买名单")
    ex = getattr(ccxt, EXCHANGE)(EXCHANGE_CONFIG)

    mkts = ex.loadMarkets()
    # tks = ex.fetchTicker(symbol)
    mkt = mkts[symbol]

    symbolId = mkt["id"]
    precisionAmount = mkt["precision"]["amount"]
    minAmount = mkt["limits"]["amount"]["min"]
    minCost = mkt["limits"]["cost"]["min"]
    logger.info(f"symbol-{symbol} symbolId-{symbolId} precisionAmount-{precisionAmount} minAmount-{minAmount} minCost-{minCost}")
    logger.debug(f"币种信息：{mkt}")

    orderIdsBuy = []
    orderIdsSell = []

    tradingTimeStr = dt.datetime.fromtimestamp(tradingTime).strftime('%Y-%m-%d %H:%M:%S')
    logger.info(f"{symbol}抢新准备就绪，等待开始时间{tradingTimeStr}")
    while True:
        if time.time() >= tradingTime:
            logger.info("吉时已到！开枪！！！")

            # 买入操作
            logger.info(f"=========== 开始执行买入 ===========")
            for bp in buyParas:
                price = bp[0]
                price = ex.priceToPrecision(symbol, price)
                amount = bp[1]
                if minAmount:
                    amount = max(bp[1], minAmount)
                amount = ex.amountToPrecision(symbol, amount)
                logger.info(f"买单要求: symbol={symbol} price={price} amount={amount}")

                for i in range(TRY_TIMES):
                    try:
                        order = ex.createOrder(symbol, type="limit", side="buy", price=price, amount=amount)
                        orderId = order["id"]
                        logger.info(f"{symbol}买入订单已提交, price={price} amount={amount} orderId={orderId}")
                        orderIdsBuy.append(orderId)
                        break
                    except ccxt.InsufficientFunds as e:
                        logger.error(f"余额不足，停止 {e}")
                        # logger.exception(e)
                        raise RuntimeError("余额不足，停止")
                    except Exception as e:
                        logger.error(f"提交买单报错{symbol} {price} {amount}: {e}")
                        # logger.exception(e)
                        if i == TRY_TIMES - 1: raise RuntimeError(f"下买单失败次数过多，退出。")
                        continue

            logger.info(f"已发送的订单列表: orderBuyList={orderIdsBuy}")
            time.sleep(SLEEP_MEDIUM)

            # 查询买入结果
            logger.info(f"=========== 开始查询买入结果 ===========")
            for id in orderIdsBuy:
                if id:
                    for i in range(TRY_TIMES):
                        try:
                            orderInfo = ex.fetchOrder(id, symbol)
                            logger.debug(f"交易所买单信息: {orderInfo}")
                            if orderInfo["status"] == "closed":
                                logger.info(f"√√√ {symbol} 买入成功  √√√")
                                price = orderInfo["average"]
                                amount = orderInfo["filled"]
                                if orderInfo["fee"]:
                                    amount = orderInfo["filled"] - orderInfo["fee"]["cost"]
                                logger.info(f"实际成交参数: price={price} amount={amount}")
                                break
                            else:
                                logger.warning(
                                    f"买入订单状态未成交{symbol} price:{price} amount:{amount} : {orderInfo['status']} 过1s重试"
                                    )
                                if i == TRY_TIMES - 1:
                                    logger.error(f"{symbol} 买入订单最终未成交，退出")
                                    raise RuntimeError(f"买单最终未成交")
                                time.sleep(SLEEP_LONG)
                                continue

                        except ccxt.OrderNotFound as e:
                            logger.error(f"暂时未找到订单, 重新查询, 一共会重试 {TRY_TIMES} 次")
                            if i == TRY_TIMES - 1:
                                logger.error(f"{symbol} 查询买入结果失败，无法挂卖出单，请手动挂单")
                                raise
                            time.sleep(SLEEP_MEDIUM)
                            continue
                        except Exception as e:
                            logger.error(f"{symbol}获取订单信息失败，重试{e}")
                            # logger.exception(e)
                            if i == TRY_TIMES - 1:
                                logger.error(f"{symbol} 查询买入结果失败，无法挂卖出单，请手动挂单")
                                raise
                            time.sleep(SLEEP_MEDIUM)
                            continue

                    # 执行卖出操作
                    logger.info(f"=========== 开始执行卖出挂单 ===========")
                    for orderInfo in sellParas:

                        logger.info(f"卖单要求: {orderInfo}")
                        times = orderInfo[0]
                        pct = orderInfo[1]
                        priceThisTime = price * times
                        amountThisTime = amount * pct

                        if minCost and ((amountThisTime * priceThisTime) < minCost):
                            logger.warning(f"本次下单价值过低 cost={amountThisTime*priceThisTime}U price={priceThisTime} amount={amountThisTime}，"
                                           f"按最小价值 {minCost}U 下单，可能导致oversold")
                            amountThisTime = math.ceil(minCost / priceThisTime)

                        logger.info(f"卖单参数: times={times} pct={pct} "
                                    f"priceThisTime={priceThisTime} amountThisTime={amountThisTime}")

                        for i in range(TRY_TIMES):
                            try:
                                order = ex.createOrder(symbol, type="limit", side="sell", price=priceThisTime, amount=amountThisTime)
                                if "id" in order:
                                    logger.info(f"√√√ {symbol} 卖单提交成功 √√√  {order['id']}")
                                    logger.debug(f"{symbol} 交易所的卖单回执: {order}")
                                    orderIdsSell.append(order["id"])
                                    break

                            except Exception as e:
                                logger.error(f"提交卖单报错{symbol} {priceThisTime} {amountThisTime}: {e}")
                                # logger.exception(e)
                                if i == TRY_TIMES - 1: raise RuntimeError(f"下卖单失败次数过多，退出。")
                                time.sleep(0.002)
                                continue

                    # 查询卖出挂单状态
                    for sellOrderId in orderIdsSell:
                        time.sleep(SLEEP_LONG)

                        r = ex.fetchOrder(sellOrderId, symbol)
                        logger.info(f"查询卖单状态: symbol={r['symbol']} status={r['status']} price={r['price']} amount={r['amount']} "
                                    f"fees={r['fees']} orderType={r['type']} side={r['side']}")


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
            # logger.exception(e)
            time.sleep(SLEEP_MEDIUM)
            continue
        except RuntimeError as e:
            if str(e) == "余额不足，停止": exit()
            if str(e) == "买单最终未成交": exit()
        except Exception as e:
            logger.error(f"主程序报错: {e}")
            logger.exception(e)
            continue
