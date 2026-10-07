"""配置管理模块。

统一管理 config.yaml 设备配置的读取与校验：
关键字检查、空值检查、类型检查、特定字段值检查、
平台依赖检查（iOS 多台需要 wda_port）、端口范围与重复性校验。
"""

from pathlib import Path

import yaml

from utils.log_utils import get_logger

logger = get_logger()


class ConfigError(Exception):
    """配置校验异常基类。"""


class ConfigManager:
    """统一管理配置。"""

    # 类属性——字典
    PLATFORM_DICTS = {"platform": ["android", "ios"]}

    # 唯一标志
    UNIQUE_ID = "udid"

    # 平台分类
    IOS_RECOGNIZE = "ios"
    ANDROID_RECOGNIZE = "android"
    PLATFORM = "platform"
    WDA_PORT = "wda_port"

    # 类属性——关键字段
    KEYWORDS_LISTS = ["platform", "udid", "app_package"]

    # 类属性——字段的数据类型
    COMMON_FIELD_TYPES = {
        "user_name": str,
        "phone_model": str,
        "platform": str,
        "udid": str,
        "app_package": str,
        "wda_port": int,
    }

    # 类属性——多台 iOS 特有字段
    ALLOWED_COMBINATIONS = {
        "ios": ["wda_port"],
        "android": [],
    }

    # 依赖关系
    DEPENDENCY_FIELD = "platform"
    DEPENDENT_FIELD = "wda_port"

    def __init__(self, config_dir, config_list_map):
        self.config_dir = config_dir  # 初始化文件路径
        self.config_list_map = config_list_map  # yaml 中的列表名称

    def _read_yaml_file(self):
        """读取文件。"""
        try:
            with open(self.config_dir, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except FileNotFoundError as exc:
            logger.error(f"文件不存在：{exc}")
            return None
        except PermissionError as exc:
            logger.error(f"文件权限问题：{exc}")
            return None
        except UnicodeError as exc:
            logger.error(f"文件编码错误：{exc}")
            return None
        except yaml.YAMLError as exc:
            logger.error(f"yaml文件内容不规范：{exc}")
            return None
        except Exception as exc:
            logger.error(f"其他错误：{exc}")
            return None

    @staticmethod
    def _keyword_check(existing_dic, allowed_key_list):
        """yaml 文件中的关键字段检查：platform、udid、app_package。"""
        existing_key_list = [k for k in existing_dic.keys()]
        missing_keyword = [
            k for k in allowed_key_list if k not in existing_key_list
        ]
        if missing_keyword:
            raise ConfigError(f"缺少如下关键字：{missing_keyword}")

    @staticmethod
    def _value_none_check(dic):
        """对 yaml 文件中的值是否为空进行校验，包含 None、空格、[]、{}。"""
        for k, v in dic.items():
            if not v:
                raise ConfigError(f"{k}的值为空")

    @staticmethod
    def _value_type_check(value, expect_type):
        """yaml 文件中的数据类型校验。"""
        if not isinstance(value, expect_type):
            raise ConfigError(
                f"值{value}不是预期的数据类型{expect_type}，"
                f"实际类型是{type(value)}"
            )

    @staticmethod
    def _key_value_check(value, expect_value):
        """yaml 文件中关键字段的值校验。"""
        if value.lower() not in expect_value:
            raise ConfigError(f"{value}不是预期的值{expect_value}")

    @staticmethod
    def _validate_dictvalue_dependency(
        existing_dict, dependency_field, dependent_field, allowed_combinations
    ):
        """校验字段间的依赖关系。

        :param existing_dict: 当前被校验的字典，如 {platform: ios, wda_port: 8001}
        :param dependency_field: 属性被依赖者，如 platform
        :param dependent_field: 属性依赖者，如 wda_port
        :param allowed_combinations: 平台与依赖字段的关系表
        """
        depd_value = existing_dict[dependency_field]  # 取出 platform 的值
        allowed_value = allowed_combinations[depd_value.lower()]
        if allowed_value is None or len(allowed_value) == 0:
            if dependent_field in existing_dict:
                raise ConfigError(f"不需要依赖{dependent_field}")
        else:
            if dependent_field not in existing_dict:
                raise ConfigError(
                    f"缺少{dependent_field}，请检查依赖关系表和源文件"
                )

    @staticmethod
    def _value_range_check(existing_value, expect_range):
        """对值的范围进行校验。"""
        if existing_value not in expect_range:
            raise ConfigError(
                f"{existing_value}不在设定的范围内，设定的范围是{expect_range}"
            )

    @staticmethod
    def _type_nums(map_lists, expect_key, expect_value, dependent_field, unique_id):
        """统计整个列表中指定平台值的数量，以唯一标志为键保存到字典中返回。"""
        dicts = {}
        expect_value_num = 0
        for map_list in map_lists:
            if map_list[expect_key].lower() == expect_value:
                dicts[map_list[unique_id]] = map_list[dependent_field]
                expect_value_num += 1
        return dicts, expect_value_num

    @staticmethod
    def _value_repeatability_check(existing_lists, dependent_field, dependency_field):
        """重复性校验。

        :param existing_lists: 列表嵌套字典形式
        :param dependent_field: 字典中的唯一关键字
        :param dependency_field: 需要检验的字段
        """
        exist_combinations = {}
        for existing_dic in existing_lists:
            if dependency_field not in existing_dic:
                continue
            exist_key = existing_dic.get(dependent_field)
            exist_value = existing_dic[dependency_field]
            if exist_value in exist_combinations:
                raise ConfigError(
                    f"{exist_key}中字段{dependency_field}的值重复"
                )
            exist_combinations[exist_value] = exist_key

    def validate_all(self):
        """初始化文件（校验文件）。

        单设备校验：关键字、空值、类型、特定字段值、平台依赖；
        列表级校验：wda_port 重复性。
        :return: 校验通过的设备列表
        """
        devices = self.get_all_devices()
        logger.info("文件初始化开始")
        for device in devices:
            logger.debug(f"开始检查{device[self.UNIQUE_ID]}")
            self._keyword_check(device, self.KEYWORDS_LISTS)
            self._value_none_check(device)
            for device_attribute, device_value in device.items():
                self._value_type_check(
                    device_value, self.COMMON_FIELD_TYPES[device_attribute]
                )
                if device_attribute in self.PLATFORM_DICTS:
                    self._key_value_check(
                        device_value, self.PLATFORM_DICTS[device_attribute]
                    )
                if device_attribute.lower() == self.WDA_PORT:
                    self._value_range_check(device_value, range(8100, 9100))
            self._validate_dictvalue_dependency(
                device,
                self.DEPENDENCY_FIELD,
                self.DEPENDENT_FIELD,
                self.ALLOWED_COMBINATIONS,
            )
            logger.debug(f"{device[self.UNIQUE_ID]}检查完成")
        self._value_repeatability_check(
            devices, self.UNIQUE_ID, self.WDA_PORT
        )
        logger.info("文件初始化完成")
        return devices

    def get_all_devices(self):
        """获取所有设备的配置信息。"""
        try:
            return self._read_yaml_file()[self.config_list_map]
        except Exception as exc:
            logger.error(f"读取config.yaml文件出现异常：{exc}")
            return None

    def get_mobile_platform(self):
        """按平台分类打印设备信息。

        :return: 设备总数
        """
        devices = self.get_all_devices()
        if not devices:
            logger.warning("配置文件中无设备信息")
            return 0
        for device in devices:
            platform = device.get("platform", "")
            if not platform:
                logger.warning("配置列表无手机型号")
                continue
            if platform.lower() == self.ANDROID_RECOGNIZE:
                logger.info(f"安卓机{device['phone_model']}")
            else:
                logger.info(f"iOS机{device['phone_model']}")
        return len(devices)


def load_config(config_dir=None, config_list_map="devices"):
    """加载并校验配置的便捷入口。

    :param config_dir: 配置文件路径，默认为项目 config/config.yaml
    :param config_list_map: yaml 中的列表名称
    :return: ConfigManager 实例
    """
    if config_dir is None:
        project_root = Path(__file__).resolve().parents[1]
        config_dir = project_root / "config" / "config.yaml"
    return ConfigManager(config_dir, config_list_map)


if __name__ == "__main__":
    manager = load_config()
    manager.validate_all()
    manager.get_mobile_platform()
