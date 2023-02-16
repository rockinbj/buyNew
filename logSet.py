import logging, logging.handlers
import os
import requests
from buySetting import LOG_FILE, LOG_CONSOLE, LOG_MIXIN

logPath = "log"
logName = "test.log"
logFile = os.path.join(logPath, logName)

logger = logging.getLogger("app.logSet")
logger.setLevel(logging.DEBUG)

fmt = '%(asctime)s|%(name)s:%(lineno)4d|%(threadName)s|%(levelname)-8s %(message)s'
fmt = logging.Formatter(fmt)

hdlConsole = logging.StreamHandler()
hdlConsole.setLevel(getattr(logging, LOG_CONSOLE.upper()))
hdlConsole.setFormatter(fmt)

hdlFile = logging.handlers.TimedRotatingFileHandler(logFile, when="midnight", backupCount=30)
hdlFile.setLevel(getattr(logging, LOG_FILE.upper()))
hdlFile.setFormatter(fmt)

# 自定义handler用于发送webhook消息
class MixinHandler(logging.Handler):
    def __init__(self,
                token="mrbXSz6rSoQjtrVnDlOH9ogK8UubLdNKClUgx1kGjGoq39usdEzbHlwtFIvHHO3C",
                msgType="PLAIN_TEXT"):
        logging.Handler.__init__(self)
        self.token = token
        self.msgType = msgType
    

    def sendMixin(self, msg, token, _type):
        
        url = f"https://webhook.exinwork.com/api/send?access_token={token}"
        value = {
            'category': _type,
            'data': msg,
            }
        
        r = requests.post(url, data=value, timeout=2).json()
        if r["success"] is False:
            logger.warning(f"Mixin failure: {r.text}")


    def emit(self, msg):
        try:
            msg = self.format(msg)
            self.sendMixin(msg, self.token, self.msgType)
        except Exception as e:
            logger.exception(e)
            raise e


hdlMixin = MixinHandler()
hdlMixin.setLevel(getattr(logging, LOG_MIXIN.upper()))
hdlMixin.setFormatter(fmt)

logger.addHandler(hdlConsole)
logger.addHandler(hdlFile)
# logger.addHandler(hdlMixin)

