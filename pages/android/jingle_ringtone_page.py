"""智能门铃 Chime Base 铃声设置页 PO — jingle_ringtone。

入口：jingle 设置页宫格点击「铃声设置」。
Activity：SoundLightAlarmDingActivity（com.ppstrong.weeye.view.activity.setting）。
识别点：标题「铃声设置」+ Activity 关键字（2026-10-10 真机 dump 验证）。

页面结构（2026-10-11 真机 dump + 行为验证）：
- rv_sound_list：默认音频列表（音频1/音频2/音频3），每项
  iv_play（播放）+ tv_sound_title（名称）+ iv_check（选中图标）
- tv_setting_des：说明文案（'*所选音效用于Chime Base声音播放'）
- ll_record / iv_center：底部录制按钮（tv_record_tips='按住按钮录制铃声'）
- 录制完成弹框（长按 ≥1s 松手后弹出）：
  title='提示' / message_tip='设置报警铃声的名称' / message（名称输入区）/
  negativeButton='取消' / positiveButton='确定'

行为要点（2026-10-11 真机验证）：
- 长按录制：同点 swipe 模拟（duration 即录制时长，上限 6s）
- 短按（<1s）：提示「录音时间短，请重新录制」——系统 Toast 对
  poco accessibility 树不可见，无法自动断言
- 选中态：iv_check 无属性差异，选中验证依赖音频播放行为或人工
"""

from __future__ import annotations

import time
from typing import List

from pages.android.jingle_sub_page_base import JingleSubPageBase, RID
from pages.base_page import OperationFailedError
from utils.log_utils import get_logger

logger = get_logger()


class JingleRingtonePage(JingleSubPageBase):
    """铃声设置页（SoundLightAlarmDingActivity，标题='铃声设置'）。"""

    TITLE_TEXT = "铃声设置"
    ACTIVITY_KEYWORD = "SoundLightAlarmDingActivity"

    # ==================== 音频列表 ====================
    RV_SOUND_LIST = {"name": RID + "rv_sound_list"}
    TV_SOUND_TITLE = {"name": RID + "tv_sound_title"}   # 音频名称
    IV_PLAY = {"name": RID + "iv_play"}                 # 播放按钮
    IV_CHECK = {"name": RID + "iv_check"}               # 选中图标
    IV_DELETE = {"name": RID + "iv_delete"}             # 删除按钮（仅自定义铃声项）
    TV_SETTING_DES = {"name": RID + "tv_setting_des"}   # 说明文案

    # ==================== 录制区 ====================
    LAYOUT_RECORD = {"name": RID + "ll_record"}
    IV_CENTER = {"name": RID + "iv_center"}             # 录制按钮
    TV_RECORD_TIPS = {"name": RID + "tv_record_tips"}   # '按住按钮录制铃声'

    # ==================== 录制完成弹框 ====================
    DIALOG_TITLE = {"name": RID + "title"}              # '提示'
    DIALOG_MESSAGE_TIP = {"name": RID + "message_tip"}  # '设置报警铃声的名称'
    DIALOG_INPUT = {"name": RID + "message"}            # 名称输入区
    DIALOG_BTN_CANCEL = {"name": RID + "negativeButton"}   # '取消'
    DIALOG_BTN_SAVE = {"name": RID + "positiveButton"}     # '确定'（保存）

    DIALOG_TITLE_TEXT = "提示"
    DIALOG_TIP_TEXT = "设置报警铃声的名称"
    RECORD_TIPS_TEXT = "按住按钮录制铃声"
    MAX_RECORD_SECONDS = 6.0

    def __init__(self, poco, udid: str = "") -> None:
        super().__init__(poco, udid)

    # ==================== 音频列表 ====================

    def get_ringtone_list(self) -> List[str]:
        """读取默认音频名称列表（如 ['音频1', '音频2', '音频3']）。"""
        proxy = self.poco(RID + "tv_sound_title")
        titles = [proxy[i].attr("text") for i in range(len(proxy))]
        logger.debug(f"铃声设置页：音频列表 {titles}")
        return titles

    def select_ringtone(self, name: str) -> "JingleRingtonePage":
        """点击指定音频名称选定铃声。

        :param name: 音频名称（如 '音频2'）
        :return: self（支持链式调用）
        :raises OperationFailedError: 音频不存在
        """
        if name not in self.get_ringtone_list():
            raise OperationFailedError(f"音频 {name!r} 不在铃声列表中")
        self.click({"text": name})
        logger.info(f"铃声设置页：已点击音频 {name!r}")
        return self

    def delete_ringtone(self, name: str) -> "JingleRingtonePage":
        """删除指定自定义铃声（点击该项的 iv_delete）。

        默认音频（音频1/2/3）无删除按钮，仅自定义铃声可删
        （2026-10-11 真机验证：保存自定义铃声后该项右侧出现 iv_delete，
        且 iv_delete 仅存在于自定义项，需按行 y 坐标与名称对齐定位）。

        :param name: 自定义铃声名称
        :return: self（支持链式调用）
        :raises OperationFailedError: 铃声不存在或该项无删除按钮
        """
        titles = self.get_ringtone_list()
        if name not in titles:
            raise OperationFailedError(f"音频 {name!r} 不在铃声列表中")
        index = titles.index(name)
        target_y = self.poco(RID + "tv_sound_title")[index].attr("pos")[1]
        deletes = self.poco(RID + "iv_delete")
        for i in range(len(deletes)):
            if abs(deletes[i].attr("pos")[1] - target_y) < 0.02:
                deletes[i].click()
                logger.info(f"铃声设置页：已删除自定义铃声 {name!r}")
                return self
        raise OperationFailedError(
            f"音频 {name!r} 项未找到同行删除按钮（默认音频不可删除）"
        )

    # ==================== 录制 ====================

    def _hold_record_button(self, seconds: float) -> None:
        """同点 swipe 模拟按住录制按钮。"""
        if not 0 < seconds <= self.MAX_RECORD_SECONDS:
            raise OperationFailedError(
                f"录制时长需在 (0, {self.MAX_RECORD_SECONDS}] 秒内，当前 {seconds}"
            )
        node = self.poco(RID + "iv_center")
        pos = node.attr("pos")
        self.poco.swipe([pos[0], pos[1]], [pos[0], pos[1]],
                        duration=seconds)

    def record_ringtone(self, seconds: float = 3.0, name: str = "",
                        save: bool = False) -> "JingleRingtonePage":
        """按住录制按钮录制自定义铃声并处理完成弹框。

        行为（2026-10-11 真机验证）：
        - seconds >= 1：松手后弹「设置报警铃声的名称」弹框
        - seconds < 1：提示「录音时间短，请重新录制」（系统 Toast，
          poco 不可见，无弹框），此时 name/save 参数不生效
        - save=True 点「确定」真实保存（验证后建议删除恢复）；
          save=False 点「取消」不保存

        :param seconds: 按住时长（录制时长，上限 6 秒）
        :param name: 弹框中输入的铃声名称（空则不输入）
        :param save: True 保存 / False 取消
        :return: self（支持链式调用）
        """
        self._hold_record_button(seconds)
        logger.info(f"铃声设置页：已按住录制 {seconds}s 后松手")

        if seconds < 1:
            # 短按：仅 Toast 提示，无弹框（poco 不可见，无法断言）
            logger.info(
                "录制时长 <1s，预期提示「录音时间短，请重新录制」"
                "（系统 Toast 对 poco 不可见）"
            )
            return self

        # 等待录制完成弹框
        if not self.wait_for_element(self.DIALOG_MESSAGE_TIP, timeout=10):
            raise OperationFailedError("录制完成后未弹出铃声命名弹框")
        if name:
            self.input_text(self.DIALOG_INPUT, name)
            logger.info(f"铃声弹框：已输入名称 {name!r}")
        btn = self.DIALOG_BTN_SAVE if save else self.DIALOG_BTN_CANCEL
        self.click(btn)
        self.wait_for_element_disappear(self.DIALOG_MESSAGE_TIP, timeout=10)
        logger.info(
            f"铃声弹框：已点击「{'确定' if save else '取消'}」"
        )
        return self

    def is_record_tip_shown(self) -> bool:
        """判定录制提示文案（'按住按钮录制铃声'）在屏。"""
        try:
            return self.get_text(self.TV_RECORD_TIPS) == self.RECORD_TIPS_TEXT
        except Exception:  # noqa: BLE001 弹框遮挡期按未就绪处理
            return False
