"""智能门铃 Chime Base 声音设置页 PO — jingle_sound。

入口：jingle 设置页列表点击「声音设置」。
Activity：SoundSettingActivity（com.ppstrong.weeye.view.activity.setting）。
识别点：标题「声音设置」+ Activity 关键字（2026-10-10 真机 dump 验证）。

页面结构（2026-10-11 真机 dump + 行为验证）：
- layout_sound_speaker + switch_sound_speaker：扬声器开关
- layout_speaker_volume + sb_volume：音量滑条（扬声器开启时可见）
- tv_volume：音量数值（1-100）
- tv_2：'双向音频，录制声音和声音报警也将被禁用'

行为要点（2026-10-11 真机验证）：
- 扬声器状态判断：sb_volume 可见 = 开，不可见 = 关
  （关闭后音量条整体隐藏；switch 的 checked 属性恒 False 不可靠）
- 音量拖动：使用 airtest 底层触摸事件序列
  （Down → 密集 Move → Up）从当前 thumb 位置拖到目标位置；
  poco.swipe / adb input swipe 均无法稳定生效
- tv_volume 文本不实时刷新：拖动后需退出重进页面才能读到新值
  （PO 提供 set_volume 拖动 + 由用例重进后 get_volume 验证）
- 精度误差约 ±2（目标 60 实际 62）
"""

from __future__ import annotations

from pages.android.jingle_sub_page_base import JingleSubPageBase, RID
from pages.base_page import OperationFailedError
from utils.log_utils import get_logger

logger = get_logger()

# 触摸事件序列（airtest 底层，绕过 poco.swipe 对滑条不生效的问题）
from airtest.core.android.touch_methods.base_touch import (  # noqa: E402
    DownEvent,
    MoveEvent,
    SleepEvent,
    UpEvent,
)

VOLUME_MIN = 1
VOLUME_MAX = 100


class JingleSoundPage(JingleSubPageBase):
    """声音设置页（SoundSettingActivity，标题='声音设置'）。"""

    TITLE_TEXT = "声音设置"
    ACTIVITY_KEYWORD = "SoundSettingActivity"

    # ==================== 定位器 ====================
    LAYOUT_SPEAKER = {"name": RID + "layout_sound_speaker"}   # 扬声器行
    SWITCH_SPEAKER = {"name": RID + "switch_sound_speaker"}   # 扬声器开关
    LAYOUT_VOLUME = {"name": RID + "layout_speaker_volume"}   # 音量行
    SB_VOLUME = {"name": RID + "sb_volume"}                   # 音量滑条
    TV_VOLUME = {"name": RID + "tv_volume"}                   # 音量数值（1-100）
    TV_DES = {"name": RID + "tv_2"}                           # 禁用说明文案

    def __init__(self, poco, udid: str = "") -> None:
        super().__init__(poco, udid)

    # ==================== 扬声器开关 ====================

    def is_speaker_on(self) -> bool:
        """判定扬声器是否开启（音量滑条可见 = 开）。

        真机验证（2026-10-11）：switch 的 checked 属性恒 False 不可靠，
        以 sb_volume 可见性作为状态依据（关闭后音量条整体隐藏）。
        """
        return self.exists(self.SB_VOLUME)

    def toggle_speaker(self) -> "JingleSoundPage":
        """点击扬声器开关（切换当前状态）。

        :return: self（支持链式调用）
        :raises OperationFailedError: 开关不在屏
        """
        if not self.exists(self.SWITCH_SPEAKER):
            raise OperationFailedError("扬声器开关不在屏")
        self.click(self.SWITCH_SPEAKER)
        logger.info("声音设置页：已点击扬声器开关")
        return self

    def turn_on_speaker(self) -> "JingleSoundPage":
        """开启扬声器（已开启则不动作）。"""
        if not self.is_speaker_on():
            self.toggle_speaker()
            import time

            deadline = time.time() + 5
            while time.time() < deadline and not self.is_speaker_on():
                time.sleep(0.5)
            logger.info("声音设置页：扬声器已开启")
        return self

    def turn_off_speaker(self) -> "JingleSoundPage":
        """关闭扬声器（已关闭则不动作）。

        关闭后音量条隐藏（双向音频与声音报警同时禁用）。
        """
        if self.is_speaker_on():
            self.toggle_speaker()
            import time

            deadline = time.time() + 5
            while time.time() < deadline and self.is_speaker_on():
                time.sleep(0.5)
            logger.info("声音设置页：扬声器已关闭")
        return self

    # ==================== 音量 ====================

    def get_volume(self) -> int:
        """读取音量数值（tv_volume 文本，1-100）。

        ⚠️ 拖动后 tv_volume 不实时刷新，需退出重进页面后读取
        才能拿到新值（2026-10-11 真机验证）。
        """
        text = self.get_text(self.TV_VOLUME)
        digits = "".join(c for c in text if c.isdigit())
        if not digits:
            raise OperationFailedError(f"音量文本无法解析：{text!r}")
        return int(digits)

    def _bar_geometry(self):
        """读取音量滑条几何（归一化）。"""
        node = self.poco(RID + "sb_volume")
        pos, size = node.attr("pos"), node.attr("size")
        return pos[0] - size[0] / 2, pos[0] + size[0] / 2, pos[1], size[0]

    def set_volume(self, value: int, steps: int = 15) -> "JingleSoundPage":
        """拖动音量滑条设置音量（1-100）。

        实现要点（2026-10-11 真机验证）：
        - 使用 airtest 底层触摸事件序列（Down → 密集 Move → Up），
          poco.swipe / adb input swipe 对该滑条无法稳定生效
        - 从当前音量对应 thumb 位置起拖
        - 精度误差约 ±2（目标 60 实际 62）
        - tv_volume 不实时刷新，验证需重进页面后 get_volume

        :param value: 目标音量（1-100，越界报错）
        :param steps: 拖动步数（默认 15，越大越平滑）
        :return: self（支持链式调用）
        :raises OperationFailedError: 音量越界 / 扬声器未开启
        """
        if not VOLUME_MIN <= value <= VOLUME_MAX:
            raise OperationFailedError(
                f"音量需在 [{VOLUME_MIN}, {VOLUME_MAX}] 内，当前 {value}"
            )
        if not self.exists(self.SB_VOLUME):
            raise OperationFailedError("扬声器未开启，音量滑条不可见")

        current = self.get_volume()
        left, _right, y_n, width_n = self._bar_geometry()
        device = self.poco.device
        screen_w, screen_h = device.get_current_resolution()
        y_px = int(y_n * screen_h)

        def x_px(v: float) -> int:
            return int((left + width_n * v / 100) * screen_w)

        # 事件序列：Down 在 thumb → 密集 Move → 停顿 → Up 在目标
        events = [DownEvent((x_px(current), y_px)), SleepEvent(0.4)]
        for i in range(1, steps + 1):
            v = current + (value - current) * i / steps
            events.append(MoveEvent((x_px(v), y_px)))
            events.append(SleepEvent(0.04))
        events.append(SleepEvent(0.4))
        events.append(UpEvent())
        device.minitouch.perform(events)
        logger.info(
            f"声音设置页：音量已拖动 {current} → {value}"
            "（tv_volume 不实时刷新，验证需重进页面）"
        )
        return self
