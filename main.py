# 文件名: main.py
# 鸣潮通用随机语音插件 (动态目录版)

import random
import re
from pathlib import Path
from typing import List, Dict

from astrbot.api import logger
from astrbot.api.all import *
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import StarTools, Star


# 插件注册信息改为更通用的“随机语音”
@register("astrbot_plugin_mingchao_voice", "yijin840", "动态目录随机语音（一键即播）", "1.0.0")
class DynamicVoicePlugin(Star):
    # 允许用户输入 /ww 后面接的命令列表，例如 'ktxy', 'zspms'

    def __init__(self, context, config):
        super().__init__(context)

        logger.info("[随机语音] ========== 开始初始化 ==========")

        data_dir_raw = StarTools.get_data_dir("astrbot_plugin_random_voice")
        self.data_dir = Path(str(data_dir_raw))

        # 所有的语音文件都放在 self.voices_dir 下的不同子目录中
        self.voices_dir = self.data_dir / "voices"

        logger.info(f"[随机语音] 插件数据目录: {self.data_dir}")
        logger.info(f"[随机语音] 基础语音目录: {self.voices_dir}")

        try:
            self.voices_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"[随机语音] ✅ 基础语音目录创建成功")
        except Exception as e:
            logger.error(f"[随机语音] ❌ 创建基础语音目录失败: {e}")

        # 缓存已扫描的目录文件列表
        self.scanned_files: Dict[str, List[Path]] = {}

        logger.info("[随机语音] ========== 初始化完成 ==========")

    def _get_voice_files(self, sub_dir_name: str) -> List[Path]:
        """
        根据子目录名称获取语音文件列表，并进行缓存。
        """
        # 1. 检查缓存
        if sub_dir_name in self.scanned_files:
            return self.scanned_files[sub_dir_name]

        # 2. 构造完整路径
        target_dir = self.voices_dir / sub_dir_name

        if not target_dir.is_dir():
            logger.warning(f"[随机语音] ❌ 目标目录不存在: {target_dir}")
            return []

        # 3. 扫描文件
        # 兼容 .wav 和 .mp3 格式
        files = list(target_dir.glob("*.wav")) + list(target_dir.glob("*.mp3"))

        # 4. 写入缓存
        self.scanned_files[sub_dir_name] = files
        logger.info(f"[随机语音] 成功扫描目录 [{sub_dir_name}]，发现 {len(files)} 个文件。")

        return files

    async def send_local_voice(self, event, voice_path: Path):
        """发送本地语音文件"""

        file_name = voice_path.name
        # 尝试将文件名作为标题，例如 'zh_vo_Main_Linaxita_2_3_67_15'
        title = voice_path.stem

        logger.info(f"[随机语音] ---------- 开始处理语音 ----------")
        logger.info(f"[随机语音] 随机选中文件: {file_name}")
        logger.info(f"[随机语音] 标题: {title}")
        logger.info(f"[随机语音] 准备发送路径: {voice_path}")

        # 理论上这里的路径应该存在，但再次检查以防万一
        if not voice_path.exists():
            logger.error(f"[随机语音] ❌ 文件路径不存在: {voice_path}")
            yield event.plain_result(f"文件 {file_name} 不存在，无法播放。")
            return

        yield event.plain_result(f"来，听听这个「{title}」~")

        try:
            # 使用 Record.fromFileSystem 发送本地文件
            yield event.chain_result([Record.fromFileSystem(str(voice_path))])
            logger.info(f"[随机语音] ✅ 语音发送成功")
        except Exception as send_error:
            logger.error(f"[随机语音] ❌ 语音发送失败: {send_error}")
            yield event.plain_result(f"发送语音失败: {send_error}")

        logger.info(f"[随机语音] ---------- 处理完成 ----------")

    # 命令格式改为通用，例如 /ww ktxy
    @filter.command("ww", alias=["随机语音", "voice"])
    async def random_play(self, event: AstrMessageEvent):
        logger.info(f"[随机语音] 收到命令，触发随机播放")

        # 1. 解析用户输入的第一个参数作为子目录名
        # event.arg_list[0] 应该是命令后的第一个词，例如 'ktxy'
        if not event.arg_list:
            yield event.plain_result("请在命令后指定要播放的语音类型（例如：/ww ktxy 或 /ww zspms）。")
            return

        sub_dir_name = event.arg_list[0].lower()

        logger.info(f"[随机语音] 动态加载目录: {sub_dir_name}")

        # 2. 获取该目录下的所有语音文件
        available_files = self._get_voice_files(sub_dir_name)

        if not available_files:
            yield event.plain_result(
                f"目录 '{sub_dir_name}' 中没有找到语音文件！请检查文件是否已放置在 {self.voices_dir / sub_dir_name} 目录下。"
            )
            return

        # 3. 随机选择一个文件
        selected_file: Path = random.choice(available_files)

        # 4. 发送语音
        async for result in self.send_local_voice(event, selected_file):
            yield result