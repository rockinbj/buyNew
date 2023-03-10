import sys
from functions import *
from exchangeConfig import *

RULE = "USDT"

print("如果需要清仓, 请加入'--close'参数")
print("如果需要平仓指定币种, 请加入'--close=symbol'参数, 例如--close=ETH/USDT")
print("\n")

ex = getattr(ccxt, EXCHANGE)(EXCHANGE_CONFIG)
mkts = ex.loadMarkets()

pos = getOpenPosition(ex)
print(f"当前持仓情况:\n{pos}\n")
bal = getBalance(ex, asset=RULE)
print(f"当前余额:\n{bal}\n")
if not pos.empty:
    value = pos["cost"].sum() + bal
else:
    value = bal
print(f"账户权益:\n{value}")

if len(sys.argv) == 2:
    if "--close" == sys.argv[1]:
        print(f"\n\n\n正在执行清仓操作......")
        closePositionForce(ex, mkts, pos)
        # dushToBnb(ex)

        pos = getOpenPosition(ex)
        print(f"当前持仓情况:\n{pos}")
        bal = getBalance(ex, asset=RULE)
        print(f"当前余额:\n{bal}")
        if not pos.empty:
            value = pos["cost"].sum() + bal
        else:
            value = bal
        print(f"账户权益:\n{value}")

    elif "--close=" in sys.argv[1]:
        symbol = sys.argv[1].replace("--close=", "")
        print(f"\n\n\n正在执行{symbol}的平仓操作.....")
        closePositionForce(ex, mkts, pos, symbol)
        # dushToBnb(ex)

        pos = getOpenPosition(ex)
        print(f"当前持仓情况:\n{pos}")
        bal = getBalance(ex, asset=RULE)
        print(f"当前余额:\n{bal}")
        if not pos.empty:
            value = pos["cost"].sum() + bal
        else:
            value = bal
        print(f"账户权益:\n{value}")

