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

# ��������˵����
# buyParas = [
#     [0.1, 200],
#     [0.2, 100],
#
#     # [price, amountCoins]
#     # ������������ԣ����ĸ��۸�ҵ�������ٸ��ң�
#     # ����Ҷ൥
#     # [0.1, 200], ��0.1U�ĵ�������200���ң����͹ҵ�
#     # [0.2, 100], ��0.2U�ĵ�������100���ң����͹ҵ�
# ]
#
# sellParas = [
#     [2, 0.7],
#     [4, 0.3],
#
#     # [times, amountU]
#     # �������������ԣ��Գɽ��۵Ķ��ٱ������ɽ��������ٱ����ı�
#     # ����Ҷ൥
#     # [2, 0.7], �������2���������ɽ�����70%�ıң����͹ҵ�
#     # [4, 0.3], �������4���������ɽ�����30%�ıң����͹ҵ�
# ]

