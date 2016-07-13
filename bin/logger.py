import logging
import logging.handlers
import multiprocessing
from config import config

class Logger:
    
    logger = None
    lock = None
    
    def __init__(self, filename):
        self.lock = multiprocessing.Lock()
        handler = logging.handlers.TimedRotatingFileHandler(filename = filename, when='D', interval = 1, backupCount = 72)
        fmt = logging.Formatter(fmt='%(asctime)s  %(filename)s [line:%(lineno)d] [%(levelname)s]  %(message)s', datefmt='%Y-%m-%d %H:%M:%S' )
        handler.setFormatter(fmt)
        self.logger = logging.getLogger()
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def info(self, content):
        self.lock.acquire()
        self.logger.info(content)
        self.lock.release()

filename = config.get("logger", "path") if config.has_option("logger", "path") else "../conf/dns_benchmark_default.log"
logger = Logger(filename)

if __name__ == "__main__":
    logger.info("It's just a test")

