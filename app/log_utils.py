import logging
from logging.handlers import RotatingFileHandler
import os

basedir = os.path.abspath(os.path.dirname(__file__))
logs_dir = os.path.join(basedir, 'logs')
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

# 创建一个日志实例
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# 创建一个处理器,写入日志文件
file_handler = RotatingFileHandler(os.path.join(logs_dir, 'app.log'), maxBytes=10240, backupCount=10)
file_formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
file_handler.setFormatter(file_formatter)
file_handler.setLevel(logging.INFO)

# 创建一个处理器,输出到控制台
stream_handler = logging.StreamHandler()
stream_formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
stream_handler.setFormatter(stream_formatter)
stream_handler.setLevel(logging.DEBUG)

# 将处理器添加到日志实例
logger.addHandler(file_handler)
logger.addHandler(stream_handler)