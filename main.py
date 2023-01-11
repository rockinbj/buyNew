import time
import math
import ccxt
from functions import *
from exchangeConfig import *
from logSet import *


symbol = "AMKT/USDT"
tradingTime = 1673532000
# symbol = "SHIB/USDT"
# tradingTime = int(time.time()) + 10

buyParas = [
    # [price, amountCoins]
    # 定义多个买入策略，在哪个价格挂单买入多少个币
    [70, 0.7],
    # [0.01, 2000],
]

sellParas = [
    # [times, amountU]
    # 定义多个卖出策略，在成交价多少倍数挂单卖出多少U
    # [2, 0.7],
    [2, 0.7],
]

def main():
    ex = getattr(ccxt, EXCHANGE)(EXCHANGE_CONFIG)

    mkts = ex.loadMarkets()
    tks = ex.fetchTicker(symbol)
    mkt = mkts[symbol]

    symbolId = mkt["id"]
    precisionAmount = mkt["precision"]["amount"]
    minAmount = mkt["limits"]["amount"]["min"]
    minCost = mkt["limits"]["cost"]["min"]
    logger.debug(f"{symbolId} precisionAmount:{precisionAmount} minAmount:{minAmount} minPrice:{minCost}")
    
    orderIdsBuy = []
    orderIdsSell = []

    logger.info("准备就绪，等待开始……")
    while True:
        if time.time() >= tradingTime:
            logger.info("时间到！开始下单！")

            for bp in buyParas:
                price = bp[0]
                amount = bp[1]

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
                        if i==TRY_TIMES-1: raise RuntimeError(f"下买单失败次数过多，退出。")
                        continue
            
            logger.debug(f"orderBuyList: {orderIdsBuy}")
            time.sleep(SLEEP_MEDIUM)
            for id in orderIdsBuy:
                if id:
                    orderInfo = ex.fetchOrder(id, symbol)
                    if orderInfo["status"] == "closed":
                        price = orderInfo["average"]
                        amount = orderInfo["filled"]
                        logger.info(f"买入成功！！！{symbol} price:{price} amount:{amount}")
                    else:
                        logger.info(f"买入订单状态未成交{symbol} price:{price} amount:{amount} : {orderInfo['status']}") 
                        continue
                    
                    for sp in sellParas:
                        tk = ex.fetchTicker(symbol)
                        priceBuy1 = tk["bid"]
                        price *= sp[0]
                        # amount *= priceBuy1
                        # price = ex.priceToPrecision(symbol, price)
                        # amount = max(amount, minAmount)
                        if amount*price < minCost:
                            amount = math.ceil(minCost / price)

                        for i in range(TRY_TIMES):
                            try:
                                order = ex.createOrder(symbol, type="limit", side="sell", price=price, amount=amount)
                                logger.debug(f"{symbol}卖出订单已提交，orderId: {orderId} price:{price} amount:{amount}")
                                orderIdsSell.append(order["id"])
                                break
                            except Exception as e:
                                logger.error(f"提交卖单报错{symbol} {price} {amount}: {e}")
                                logger.exception(e)
                                if i==TRY_TIMES-1: raise RuntimeError(f"下卖单失败次数过多，退出。")
                                continue

            break
        time.sleep(0.005)

    logger.info("任务结束")

if __name__ == "__main__":
    start = time.time()
    main()
    logger.info(f"用时{round(time.time()-start,2)}s")
