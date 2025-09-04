import os
import re
import json
import random
import aiohttp
import asyncio
from pathlib import Path

from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import astrbot.api.message_components as Comp


@register("probability_voice", "zhongruan", "基于概率的语音转换插件", "1.0.0")
class ProbabilityVoicePlugin(Star):
    def __init__(self, context: Context, config):
        super().__init__(context)
        self.config = config
        
        # 创建数据目录
        self.data_dir = os.path.join("data", "probability_voice")
        os.makedirs(self.data_dir, exist_ok=True)
        
        # TTS API配置
        self.tts_url = "http://154.201.91.65:3000/v1/audio/speech"
        
        # 初始化消息计数
        self.message_count = self.config.get("message_count", 0)
        
        logger.info("ProbabilityVoice插件初始化完成")

    async def terminate(self):
        """插件卸载时调用"""
        # 保存消息计数
        self.config["message_count"] = self.message_count
        logger.info("ProbabilityVoice插件已卸载")

    @filter.command("ttsid")
    async def set_voice_id(self, event: AstrMessageEvent, voice_id: str):
        """切换音色ID"""
        self.config["voice_id"] = voice_id
        yield event.plain_result(f"音色ID已切换为: {voice_id}")

    @filter.command("ttsswitch")
    async def toggle_tts(self, event: AstrMessageEvent, switch: str):
        """开启/关闭TTS功能"""
        if switch.lower() in ["on", "开启", "启用"]:
            self.config["tts_enabled"] = True
            yield event.plain_result("TTS功能已开启")
        elif switch.lower() in ["off", "关闭", "禁用"]:
            self.config["tts_enabled"] = False
            yield event.plain_result("TTS功能已关闭")
        else:
            yield event.plain_result("参数错误，请使用 on/off 或 开启/关闭")

    @filter.event_message_type(filter.EventMessageType.ALL)
    async def on_message(self, event: AstrMessageEvent):
        """处理所有消息"""
        try:
            # 检查TTS是否启用
            if not self.config.get("tts_enabled", True):
                return
            
            # 获取消息内容
            message_str = event.message_str
            if not message_str:
                return
            
            # 过滤思考内容
            filtered_content = self._filter_thinking_content(message_str)
            if not filtered_content:
                return
            
            # 概率判断
            should_send_voice = self._check_probability()
            
            # 分段处理
            segments = self._segment_content(filtered_content)
            
            # 发送消息
            if should_send_voice:
                await self._send_voice_messages(event, segments)
            else:
                await self._send_text_messages(event, segments)
            
        except Exception as e:
            logger.error(f"处理消息时出错: {e}")

    def _filter_thinking_content(self, content: str) -> str:
        """过滤思考内容"""
        # 移除 <thinking> 和 </thinking> 标签及其内容
        pattern = r'<thinking>.*?</thinking>'
        filtered = re.sub(pattern, '', content, flags=re.DOTALL)
        
        # 移除可能的空行和多余空格
        filtered = '\n'.join(line.strip() for line in filtered.split('\n') if line.strip())
        
        return filtered.strip()

    def _check_probability(self) -> bool:
        """检查是否应该发送语音"""
        # 更新消息计数
        self.message_count += 1
        self.config["message_count"] = self.message_count
        
        # 获取概率配置
        percentage = self.config.get("probability_percentage", 90)
        total = self.config.get("probability_total", 10)
        
        # 计算当前消息在概率总数中的位置
        current_position = self.message_count % total
        
        # 计算应该发送语音的消息数量
        voice_count = int(total * percentage / 100)
        
        # 如果当前消息位置在应该发送语音的范围内
        return current_position < voice_count

    def _segment_content(self, content: str) -> list:
        """分段处理内容"""
        segments = []
        
        # 使用正则表达式匹配句子结束符
        # 句号、感叹号、问号（包括中文和英文）
        sentence_pattern = r'[^。！？.!?]*[。！？.!?]'
        
        # 查找所有匹配的句子
        sentences = re.findall(sentence_pattern, content)
        
        # 处理括号内容
        bracket_pattern = r'（[^）]*）|\([^)]*\)'
        bracket_contents = re.findall(bracket_pattern, content)
        
        # 按原始顺序组合
        segments = []
        sentence_index = 0
        bracket_index = 0
        pos = 0
        
        while pos < len(content):
            # 检查是否是括号内容
            bracket_match = re.search(bracket_pattern, content[pos:])
            sentence_match = re.search(sentence_pattern, content[pos:])
            
            if bracket_match and (not sentence_match or bracket_match.start() < sentence_match.start()):
                # 处理括号内容
                segments.append({
                    'content': bracket_match.group(),
                    'type': 'text',
                    'position': pos + bracket_match.start()
                })
                pos += bracket_match.end()
            elif sentence_match:
                # 处理句子
                segments.append({
                    'content': sentence_match.group().strip(),
                    'type': 'voice',
                    'position': pos + sentence_match.start()
                })
                pos += sentence_match.end()
            else:
                # 处理剩余内容
                remaining = content[pos:].strip()
                if remaining:
                    segments.append({
                        'content': remaining,
                        'type': 'text',
                        'position': pos
                    })
                break
        
        # 按位置排序
        segments.sort(key=lambda x: x['position'])
        
        return segments

    async def _send_voice_messages(self, event: AstrMessageEvent, segments: list):
        """发送语音消息"""
        for segment in segments:
            if segment['type'] == 'voice':
                # 生成语音
                audio_path = await self._generate_tts(segment['content'])
                if audio_path:
                    # 发送语音
                    yield event.chain_result([Comp.Record(file=audio_path)])
            else:
                # 发送文本
                yield event.plain_result(segment['content'])
            
            # 添加延迟，避免发送过快
            await asyncio.sleep(0.5)

    async def _send_text_messages(self, event: AstrMessageEvent, segments: list):
        """发送文本消息"""
        for segment in segments:
            yield event.plain_result(segment['content'])
            await asyncio.sleep(0.3)

    async def _generate_tts(self, text: str) -> str:
        """生成TTS语音"""
        try:
            # 准备请求数据
            headers = {
                "Authorization": f"Bearer {self.config.get('api_key', '')}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.config.get("model_name", "tts-1"),
                "input": text,
                "voice": self.config.get("voice_id", "alloy"),
                "response_format": "mp3"
            }
            
            # 发送请求
            async with aiohttp.ClientSession() as session:
                async with session.post(self.tts_url, headers=headers, json=data) as response:
                    if response.status == 200:
                        # 保存音频文件
                        audio_path = os.path.join(self.data_dir, f"tts_{self.message_count}_{random.randint(1000, 9999)}.mp3")
                        
                        with open(audio_path, 'wb') as f:
                            async for chunk in response.content.iter_chunked(8192):
                                f.write(chunk)
                        
                        logger.info(f"TTS生成成功: {audio_path}")
                        return audio_path
                    else:
                        error_text = await response.text()
                        logger.error(f"TTS请求失败: {response.status} - {error_text}")
                        return None
                        
        except Exception as e:
            logger.error(f"生成TTS时出错: {e}")
            return None