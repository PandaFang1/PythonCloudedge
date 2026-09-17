import yaml
from utils.log_utils import get_logger

logger = get_logger()


class ConfigError(Exception):
    """
    继承异常的基类
    """
    pass

class ConfigManager:
    """统一管理配置"""

    #类属性--字典
    PLATFORM_DICTS = {"platform":["android","ios"]}

    #唯一标志：
    UNIQUE_ID = "udid"

    #平台分类：
    IOS_RECOGNIZE= "ios"
    ANDROID_RECOGNIZE = "android"
    PLATFORM = "platform"
    WDA_PORT="wda_port"

    # 类属性--关键字段
    KEYWORDS_LISTS = ["platform", "udid", "app_package"]

    #类属性--字段的数据类型
    COMMON_FIELD_TYPES = {
        "user_name" : str,
        "phone_model" : str,
        "platform" : str,
        "udid": str,
        "app_package" : str,
        "wda_port":int
    }

    #类属性--多台IOS特有字段
    ALLOWED_COMBINATIONS = {
        "ios": ["wda_port"],
        "android": []
    }

    #依赖关系：
    DEPENDENCY_FIELD = "platform"
    DEPENDENT_FIELD = "wda_port"


    def __init__(self,config_dir,config_list_map):
        self.config_dir = config_dir #初始化文件路径
        self.config_list_map = config_list_map #yamle中的列表名称

    def _read_yaml_file(self):
        """
        读取文件
        """
        try:
            with open(self.config_dir,"r",encoding="utf-8") as f: #以只读的方式读取文件
                return yaml.safe_load(f) #返回读取的数据
        except FileNotFoundError as e:
            logger.error(f"文件不存在:{e}")
            return None
        except PermissionError as e:
            logger.error(f"文件权限问题：{e}")
            return None
        except UnicodeError as e:
            logger.error(f"文件编码错误：{e}")
            return None
        except yaml.YAMLError as e:
            logger.error(f"yaml文件内容不规范：{e}")
            return None
        except Exception as e:
            logger.error(f"其他错误:{e}")
            return None

    @staticmethod
    def _keyword_check(existing_dic,allowed_key_list):
        """
        yaml文件中的关键字段检查：platform,uuid,app_package:
        """
        existing_key_list =[k for k in existing_dic.keys()] # 获取原始文件中的键，转换为列表
        missing_keyword = [k for k in allowed_key_list if k not in existing_key_list]        # 检查是否缺少键，missing_keyword返回的是列表，即使没有返回的也是列表
        if missing_keyword:
            raise ConfigError(
                    f"缺少如下关键字：{missing_keyword}"
                )

    @staticmethod
    def _value_none_check_(dic):
        """
        对yaml文件中的值是否为空进行校验，包含None,空格,[],{},
        """
        for k,v in dic.items():
            if not v :
                raise ConfigError(
                    f"{k}的值为空"
                )



    @staticmethod
    def _value_type_check(value,except_type):
        """
        yaml文件中的数据类型校验
        """
        if not isinstance(value,except_type):#数据类型方法isinstance
            raise ConfigError(
                f"值{value}不是预期的数据类型{except_type}",
                f"实际类型是{type(value)}"
            )

    @staticmethod
    def _key_value_check(value,expect_value):
        """
        yaml文件中关键字段的值校验
        """
        if value.lower() not in expect_value:
            raise ConfigError(
                f"{value}不是预期的值{expect_value}"
            )

    @staticmethod
    def _validate_dictvalue_dependency(existing_dict,dependency_field,dependent_field,allowed_combinations):
        """
        exiting_dict:当前被校验的字典---{platform:ios/android,
                                        wda_port:8001}
        dependent_field：属性依赖者----wda_port
        dependency_field:属性被依赖者---platform
        allowed_combinations：属性值的关系{ios:[wda_port]
                                       android:[]     }
        """
        depd_value = existing_dict[dependency_field] #取出platform的值
        # 判断depd_value的具体的值
        allowed_value = allowed_combinations[depd_value.lower()]
        if allowed_value is None or len(allowed_value) == 0:
            if dependent_field  in existing_dict:
                raise ConfigError(
                    f"不需要依赖{dependent_field}"
                 )
        else:
            if dependent_field not in existing_dict:
                raise  ConfigError(
                    f"缺少{dependent_field}，请检查依赖关系表和源文件"
                )

    @staticmethod
    def _value_range_check(existing_value,expect_range):
        """
        对值的范围进行校验
        """
        if existing_value not in expect_range:
            raise ConfigError(
                f"{existing_value}不在设定的范围内，设定的范围是{expect_range}"
            )

    @staticmethod
    def _type_nums(map_lists,except_key,except_value,dependent_field,unique_id):
        """
        统计整个列表地图中的值的数量,并使用唯一标志位保存在字典中返回
        """
        dicts = {}
        except_value_num = 0
        for map_list in map_lists:
            if map_list[except_key].lower()==except_value:
              dicts[map_list[unique_id]] = map_list[dependent_field]
              except_value_num += 1
        return dicts,except_value_num


    @staticmethod
    def _value_repeatability_check(existing_lists,dependent_field,dependency_field):
        """
        重复性校验
        existing_lists：列表嵌套字典形式
        dependency_field:需要检验的字段
        dependent_field:字典中的唯一关键字
        """
        exist_combinations = {} #用于记录整个列表嵌套字典中的唯一值和需要检测重复的值
        for existing_dic in existing_lists: #遍历列表
            if dependency_field not in existing_dic: #判断是否有这个字段在字典中
                continue #如果不存在则结束此次循环
            #判断这个键的值是否在已存在的，值作为键，唯一标志作为值，存储在exist_combinations中
            exist_key = existing_dic.get(dependent_field)
            exist_value = existing_dic[dependency_field]
            if exist_value in exist_combinations:
                raise ConfigError(
                    f"{exist_key}中字段{dependency_field}的值重复"
                )
            exist_combinations[exist_value] = exist_key

    def validate_all(self):
        """
        初始化文件（校验文件）
        """
        devices = self.get_all_devices()#读取文件中的所有信息
        logger.info("文件初始化开始")
        for device in devices:
            """
            单设备通用校验
            1、关键字检查
            2、空值检查
            3、值的类型检查
            4、特定字段的值检查
            """
            logger.debug(f"开始检查{device[self.UNIQUE_ID]}")
            self._keyword_check(device,self.KEYWORDS_LISTS)#检查关键字
            self._value_none_check_(device)  # 空值检查
            for device_attribute,device_value in device.items():
                self._value_type_check(device_value,self.COMMON_FIELD_TYPES[device_attribute])#值的类型检查
                if device_attribute in self.PLATFORM_DICTS:
                    self._key_value_check(device_value,self.PLATFORM_DICTS[device_attribute])#特定字段的值检查
                self._validate_dictvalue_dependency(device, self.DEPENDENCY_FIELD, self.DEPENDENT_FIELD,self.ALLOWED_COMBINATIONS)#检查ios和安卓是否有wda_port参数
                if device_attribute.lower() == self.WDA_PORT:
                    self._value_range_check(device_value,range(8100,9100))
            logger.debug(f"{device[self.UNIQUE_ID]}检查完成")
            """处理端口逻辑：
            1、安卓不需要端口，ios单台不需要，ios多台需要配置wda_port
            2、ios端口范围校验
            3、ios端口重复校验
            """
        self._value_repeatability_check(devices,self.UNIQUE_ID,self.WDA_PORT)
        logger.info("文件初始化完成")
        return devices

    def get_all_devices(self):
        """
        获取手机的所有相关信息
        :return:
        """
        try:
            return self._read_yaml_file()[self.config_list_map]
        except Exception as e:
            logger.error(f"读取config.yaml文件出现异常：{e}")
            return None

    def get_mobile_platform(self):
        """
        获取设备列表长度以及
        :return:
        """
        if self.get_all_devices():
            devices_num = len(self.get_all_devices())
            for i in range(0,devices_num):
                mobile_platform = self.get_all_devices()[i]["platform"]
                if self.get_all_devices()[i]["platform"]:
                    if mobile_platform == "Android"or"android":
                        print(f'安卓机{self.get_all_devices()[i]["phone_model"]}')
                    else:
                        print(f'ios{self.get_all_devices()[i]["phone_model"]}')
                else:
                    print("配置列表无手机型号")


data =ConfigManager("./config.yaml","devices")
data.validate_all()