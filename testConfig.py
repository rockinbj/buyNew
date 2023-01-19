STRATEGY_NAME = "功能测试StrategyTest"

# 定义参与轮动币种
SYMBOLS = ["BTC", "ETH", "DOGE", "BNB", "DYDX", "ETC"]


# 测试区间
TEST_START = "2021-12-01"
TEST_END = "2022-12-02"


# 定义选币周期
LEVEL = "1h"
PERIOD = 20
HOLD_TIME = "4h"
OFFSET_LIST = [0,1,2,3]


# 定义选币算法
FACTOR = "signalMomentum"


# 定义交易手续费和滑点
FEE = 1 / 10000
SLIP = 1 / 1000


# 原始k线位置、格式
from os import path
DATA_PATH = path.join("data", "binance_spot_1m")
DATA_FORMAT = "csv"

# 输出目录
import datetime as dt
OUTPUT_PATH = "output"
TIME_PATH = dt.datetime.now().strftime("%Y-%m-%d_%H.%M.%S")



# 定义log级别
import logging
LOG_PATH = "log"
LOG_LEVEL_CONSOLE = logging.DEBUG
LOG_LEVEL_FILE = logging.DEBUG


SLEEP_SHORT = 0.003
SLEEP_MEDIUM = 0.05
SLEEP_LONG = 1

MIXIN_TOKEN = "mrbXSz6rSoQjtrVnDlOH9ogK8UubLdNKClUgx1kGjGoq39usdEzbHlwtFIvHHO3C"

TRY_TIMES = 15