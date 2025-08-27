from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger, AstrBotConfig
from astrbot.api.message_components import Record, Plain
import random
import asyncio
import re
import httpx
import aiofiles
import os
import tempfile
from typing import List, Tuple, Optional
import json

@register("tts_probability_plugin", "TTS Plugin Developer", "TTS概率语音插件", "1.0.0", "https://github.com/example/astrbot_plugin_tts")
class TTSProbabilityPlugin(Star):
    
    # TTS API配置（用户不可见）
    TTS_API_BASE_URL = "http://154.201.91.65:3000/v1"
    
    # 排除指令列表
    EXCLUDED_COMMANDS = {
        "/help", "/new", "/plugin", "/t2i", "/tts", "/sid", "/op", "/wl",
        "/dashboard_update", "/alter_cmd", "/llm", "/provider", "/model",
        "/ls", "/groupnew", "/switch", "/rename", "/del", "/reset",
        "/history", "/persona", "/tool", "/key", "/websearch", "/ttson", "/ttsoff"
    }

    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        
        # 用户配置参数
        self.api_key = str(self.config.get("api_key", ""))
        self.model_id = str(self.config.get("model_id", "tts-1"))
        self.voice_id = str(self.config.get("voice_id", "nova"))
        self.probability = float(self.config.get("probability", 0.3))
        self.cycle_length = int(self.config.get("cycle_length", 100))
        self.segmentation_regex = str(self.config.get("segmentation_regex", "[。？！]"))
        self.exclude_regex = str(self.config.get("exclude_regex", "\\(.*?\\)|\\（.*?\\）"))
        self.enabled = bool(self.config.get("enabled", True))
        
        # 概率触发状态
        self.current_message_count = 0
        self.voice_trigger_numbers = set()
        self._generate_voice_trigger_numbers()
        
        logger.info(f"TTS概率语音插件已初始化 - 概率: {self.probability}, 周期长度: {self.cycle_length}, 状态: {'启用' if self.enabled else '禁用'}")

    def _generate_voice_trigger_numbers(self):
        """生成语音触发点"""
        self.voice_trigger_numbers.clear()
        if self.probability <= 0:
            return
            
        num_to_trigger = int(self.cycle_length * self.probability)
        num_to_trigger = min(num_to_trigger, self.cycle_length)
        
        if num_to_trigger > 0:
            self.voice_trigger_numbers = set(random.sample(range(1, self.cycle_length + 1), num_to_trigger))
        
        logger.info(f"生成新的语音触发点: {sorted(list(self.voice_trigger_numbers))}")

    async def _call_tts_api(self, text: str) -> Optional[str]:
        """调用TTS API生成语音"""
        if not self.api_key:
            logger.warning("TTS API密钥未配置")
            return None
        
        url = f"{self.TTS_API_BASE_URL}/audio/speech"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model_id,
            "input": text,
            "voice": self.voice_id
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=headers, json=data)
                response.raise_for_status()
                
                # 保存音频文件到临时目录
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
                temp_path = temp_file.name
                temp_file.close()
                
                async with aiofiles.open(temp_path, "wb") as f:
                    await f.write(response.content)
                
                logger.info(f"TTS音频文件生成成功: {temp_path}")
                return temp_path
                
        except Exception as e:
            logger.error(f"TTS API调用失败: {e}")
            return None

    def _extract_excluded_content(self, text: str) -> Tuple[str, List[str]]:
        """提取需要排除的内容"""
        if not self.exclude_regex:
            return text, []
        
        try:
            excluded_matches = re.findall(self.exclude_regex, text)
            remaining_text = re.sub(self.exclude_regex, "", text).strip()
            return remaining_text, excluded_matches
        except Exception as e:
            logger.error(f"正则表达式处理失败: {e}")
            return text, []

    def _segment_text(self, text: str) -> List[str]:
        """按正则表达式分段文本"""
        if not text or not self.segmentation_regex:
            return [text] if text else []
        
        try:
            segments = re.split(self.segmentation_regex, text)
            segments = [seg.strip() for seg in segments if seg.strip()]
            return segments
        except Exception as e:
            logger.error(f"文本分段失败: {e}")
            return [text] if text else []

    @filter.command("ttson")
    async def enable_tts(self, event: AstrMessageEvent):
        """开启概率语音功能"""
        self.enabled = True
        self.config["enabled"] = True
        self.config.save_config()
        yield event.plain_result("✅ TTS概率语音功能已开启")

    @filter.command("ttsoff") 
    async def disable_tts(self, event: AstrMessageEvent):
        """关闭概率语音功能"""
        self.enabled = False
        self.config["enabled"] = False
        self.config.save_config()
        yield event.plain_result("❌ TTS概率语音功能已关闭")

    @filter.on_decorating_result()
    async def on_decorating_result(self, event: AstrMessageEvent):
        """拦截消息并处理TTS转换"""
        if not self.enabled:
            return
        
        # 检查是否为命令消息
        is_command = False
        if event.get_messages() and isinstance(event.get_messages()[0], Plain):
            first_message_text = event.get_messages()[0].text
            if first_message_text.startswith('/') or first_message_text.lower() in self.EXCLUDED_COMMANDS:
                is_command = True
        
        if is_command:
            logger.debug(f"跳过命令消息的语音转换: {event.message_str}")
            return
        
        result = event.get_result()
        if not result or not result.chain:
            return
        
        # 提取纯文本内容
        text_to_speak = ""
        is_plain_text_response = False
        
        for component in result.chain:
            if isinstance(component, Plain):
                is_plain_text_response = True
                text_to_speak += component.text
        
        if not is_plain_text_response or not text_to_speak.strip():
            return
        
        # 消息计数
        self.current_message_count += 1
        logger.debug(f"当前消息计数: {self.current_message_count}")
        
        # 检查是否触发语音
        if self.current_message_count in self.voice_trigger_numbers:
            logger.info(f"消息 #{self.current_message_count} 触发语音转换")
            
            # 处理文本
            remaining_text, excluded_content = self._extract_excluded_content(text_to_speak)
            
            new_chain = []
            
            # 添加排除的内容作为文本消息
            for excluded in excluded_content:
                if excluded.strip():
                    new_chain.append(Plain(excluded))
            
            # 处理剩余文本进行语音转换
            if remaining_text.strip():
                segments = self._segment_text(remaining_text)
                
                for segment in segments:
                    if segment.strip():
                        audio_path = await self._call_tts_api(segment)
                        if audio_path:
                            new_chain.append(Record(file=audio_path, url=audio_path))
                        else:
                            # TTS失败时发送原文本
                            new_chain.append(Plain(segment))
            
            # 如果成功生成了语音，替换消息链
            if new_chain:
                result.chain = new_chain
                logger.info(f"成功转换为语音消息，包含 {len(new_chain)} 个组件")
        else:
            logger.debug(f"消息 #{self.current_message_count} 未触发语音转换")
        
        # 重置周期
        if self.current_message_count >= self.cycle_length:
            logger.info(f"周期结束，重置消息计数并生成新的触发点")
            self.current_message_count = 0
            self._generate_voice_trigger_numbers()

    async def terminate(self):
        """插件卸载时的清理工作"""
        logger.info("TTS概率语音插件已卸载")