from datetime import datetime
import logging
import os
from pathlib import Path

def get_logger():
    """
    1、输入在控制台和保存在文件中
    2、按照时间分割/文件大小分割
    3、文件统一保存在项目的operate_logs文件夹中
    4、每行文件包含时间（精确到秒）、执行的py文件名、方法名，信息
    """
    #首先判断是否有文件夹operate_logs
    # 在operate_logs文件夹中创建日志文件
    project_root= Path(__file__).resolve().parents[1]    # 获取当前项目目录/Users/fangxiaoc/Desktop/汇总-fjc/PO_PythonProject
    log_dir = os.path.join(project_root,"operater_logs") #拼接操作日志完整保存路径，组成完成的保存路径
    os.makedirs(log_dir,exist_ok=True) #创建文件路径
    current_date = datetime.now().strftime("%Y-%m-%d")  #2026_09_12
    log_path = f"{log_dir}/{current_date}.log"
    size = Path(log_path).stat().st_size
    n = 1
    if size >= 10*1024*1024:
        log_path = f"{log_dir}/{current_date}-{n}.log"
        n = n+1
    #创建logger实例
    logger = logging.getLogger("") #日志开头
    logger.setLevel(logging.DEBUG) #设置日志的默认级别
    #日志打印格式
    formatter = logging.Formatter("%(asctime)s- %(filename)s|%(funcName)s-%(name)s-%(levelname)s-%(message)s")
    #设置流处理器，输出在控制台的日志
    ch = logging.StreamHandler() #创建流处理器的实例
    ch.setLevel(logging.INFO) #设置流处理展示的日志级别
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    #设置文件处理器，输出在文件中
    file_handle = logging.FileHandler(log_path)
    file_handle.setLevel(logging.DEBUG)
    file_handle.setFormatter(formatter)
    logger.addHandler(file_handle)
    return logger