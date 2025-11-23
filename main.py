# 文件名: main.py
# 鸣潮随机语音插件（修复版）

import random
from pathlib import Path
from typing import List, Dict

from astrbot.api import logger
from astrbot.api.all import *
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Star, Context

role_dict = {
    "ktxy": "卡提西娅",
    "fll": "弗洛洛",
    "sar": "守岸人",
    "fb": "菲比",
    "klt": "柯莱塔",
    "jx": "今汐",
    "cl": "长离",
    "c": "椿",
    "ktll": "坎特蕾拉",
    "zn": "赞妮"
 }


@register("astrbot_plugin_mingchao_voice", "yijin840", "鸣潮随机语音（一键即播）", "1.0.0")
class MingchaoVoicePlugin(Star):

    def __init__(self, context: Context, config):
        super().__init__(context)

        logger.info("[鸣潮语音] ========== 开始初始化 ==========")

        # 方案1：从插件目录读取（推荐）
        # 插件目录结构：/AstrBot/data/plugins/astrbot_plugin_mingchao_voice/
        plugin_dir = Path(__file__).parent
        self.voices_dir = plugin_dir / "voices"

        logger.info(f"[鸣潮语音] 插件根目录: {plugin_dir}")
        logger.info(f"[鸣潮语音] 语音文件目录: {self.voices_dir}")

        try:
            self.voices_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"[鸣潮语音] ✅ 语音目录创建成功")
        except Exception as e:
            logger.error(f"[鸣潮语音] ❌ 创建语音目录失败: {e}")

        self.scanned_files: Dict[str, List[Path]] = {}

        logger.info("[鸣潮语音] ========== 初始化完成 ==========")

    def _get_voice_files(self, sub_dir_name: str) -> List[Path]:
        """根据子目录名称获取语音文件列表，并进行缓存。"""
        if sub_dir_name in self.scanned_files:
            return self.scanned_files[sub_dir_name]

        target_dir = self.voices_dir / sub_dir_name

        # 显示相对路径
        try:
            relative_path = target_dir.relative_to(Path.cwd())
            logger.info(f"[鸣潮语音] 检查目录（相对路径）: {relative_path}")
        except ValueError:
            logger.info(f"[鸣潮语音] 检查目录（绝对路径）: {target_dir}")

        # ✨ 关键改进：如果目录不存在，自动创建（像战双一样）
        if not target_dir.exists():
            try:
                target_dir.mkdir(parents=True, exist_ok=True)
                logger.info(f"[鸣潮语音] ✅ 自动创建目录: {target_dir}")
            except Exception as e:
                logger.error(f"[鸣潮语音] ❌ 创建目录失败: {e}")
                return []

        if not target_dir.is_dir():
            logger.warning(f"[鸣潮语音] ❌ 路径存在但不是目录: {target_dir}")
            return []

        files = list(target_dir.glob("*.wav")) + list(target_dir.glob("*.mp3"))

        self.scanned_files[sub_dir_name] = files

        if len(files) == 0:
            logger.warning(f"[鸣潮语音] ⚠️ 目录 [{sub_dir_name}] 存在但为空，请添加 .mp3 或 .wav 文件")
        else:
            logger.info(f"[鸣潮语音] 成功扫描目录 [{sub_dir_name}]，发现 {len(files)} 个文件。")

        return files

    async def send_local_voice(self, sub_dir_name, event, voice_path: Path):
        """发送本地语音文件"""

        file_name = voice_path.name
        title = voice_path.stem

        logger.info(f"[鸣潮语音] ---------- 开始处理语音 ----------")
        logger.info(f"[鸣潮语音] 随机选中文件: {file_name}")

        if not voice_path.exists():
            logger.error(f"[鸣潮语音] ❌ 文件路径不存在: {voice_path}")
            yield event.plain_result(f"文件 {file_name} 不存在，无法播放。")
            return

        yield event.plain_result(f"来，听听{role_dict[sub_dir_name]}怎么说~")

        try:
            yield event.chain_result([Record.fromFileSystem(str(voice_path))])
            logger.info(f"[鸣潮语音] ✅ 语音发送成功")
        except Exception as send_error:
            logger.error(f"[鸣潮语音] ❌ 语音发送失败: {send_error}")
            yield event.plain_result(f"发送语音失败: {send_error}")

        logger.info(f"[鸣潮语音] ---------- 处理完成 ----------")

    @filter.command("mc", alias=["鸣潮语音", "mcvoice", "ww"])
    async def random_play(self, event: AstrMessageEvent):
        logger.info(f"[鸣潮语音] 收到命令，触发随机播放")

        # 方法1：尝试使用 get_message_text()
        try:
            full_message = event.get_message_text()
            logger.info(f"[鸣潮语音] 从 get_message_text() 获取消息: {full_message}")
        except AttributeError:
            # 方法2：尝试从 event.message_str 获取
            try:
                full_message = event.message_str
                logger.info(f"[鸣潮语音] 从 message_str 获取消息: {full_message}")
            except AttributeError:
                # 方法3：从 event_data 获取
                try:
                    full_message = str(event.event_data.get('message', ''))
                    logger.info(f"[鸣潮语音] 从 event_data 获取消息: {full_message}")
                except Exception as e:
                    logger.error(f"[鸣潮语音] ❌ 无法获取消息文本: {e}")
                    yield event.plain_result("错误：无法解析消息内容")
                    return

        if not full_message:
            logger.error("[鸣潮语音] 获取到的消息文本为空")
            yield event.plain_result("请在命令后指定要播放的语音类型（例如：/mc ktxy）")
            return

        # 移除命令前缀
        text_without_command = full_message.strip()
        command_list = ["mc", "/mc", "鸣潮语音", "ww", "/ww", "mcvoice"]

        for cmd in command_list:
            if text_without_command.lower().startswith(cmd.lower()):
                text_without_command = text_without_command[len(cmd):].strip()
                break

        logger.info(f"[鸣潮语音] 去除命令后的文本: '{text_without_command}'")

        if not text_without_command:
            yield event.plain_result("请在命令后指定要播放的语音类型（例如：/mc ktxy）")
            return

        # 获取第一个词作为目录名
        sub_dir_name = text_without_command.split()[0].lower()
        logger.info(f"[鸣潮语音] 确定的子目录名称: {sub_dir_name}")

        # 获取该目录下的所有语音文件
        available_files = self._get_voice_files(sub_dir_name)

        if not available_files:
            # 计算相对路径用于显示
            target_path = self.voices_dir / sub_dir_name
            try:
                relative_path = target_path.relative_to(Path.cwd())
                path_display = str(relative_path)
            except ValueError:
                path_display = str(target_path)

            yield event.plain_result(
                f"目录 '{sub_dir_name}' 已创建，但里面还没有语音文件！\n"
                f"请将 .mp3 或 .wav 文件放入：\n{path_display}"
            )
            return

        # 随机选择一个文件
        selected_file: Path = random.choice(available_files)
        logger.info(f"[鸣潮语音] 随机选择文件: {selected_file.name}")

        # 发送语音
        async for result in self.send_local_voice(sub_dir_name, event, selected_file):
            yield result
