symbol = "KING/USDT"
tradingTime = 1676627999
IS_TEST = True

buyParas = [
    [0.1, 200],
]

sellParas = [
    [2, 0.7],
    [4, 0.3],
]

testSymbol = "DOGE/USDT"
testStartWaitingSeconds = 7

if IS_TEST:
    import time
    symbol = testSymbol
    tradingTime = int(time.time()) + testStartWaitingSeconds

# 买卖参数说明：
# buyParas = [
#     [0.1, 200],
#     [0.2, 100],
#
#     # [price, amountCoins]
#     # 定义多个买入策略，在哪个价格挂单买入多少个币，
#     # 多组挂多单
#     # [0.1, 200], 以0.1U的单价买入200个币，发送挂单
#     # [0.2, 100], 以0.2U的单价买入100个币，发送挂单
# ]
#
# sellParas = [
#     [2, 0.7],
#     [4, 0.3],
#
#     # [times, amountU]
#     # 定义多个卖出策略，以成交价的多少倍卖出成交数量多少比例的币
#     # 多组挂多单
#     # [2, 0.7], 以买入价2倍，卖出成交数量70%的币，发送挂单
#     # [4, 0.3], 以买入价4倍，卖出成交数量30%的币，发送挂单
# ]

