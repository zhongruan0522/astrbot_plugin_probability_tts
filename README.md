# TTS概率语音插件

这是一个基于OpenAI TTS API规范的AstrBot插件，实现概率性的文本转语音回复功能。

## 功能特性

### 🎯 核心功能
- **概率语音回复**: 按设定概率将文本消息转换为语音回复
- **智能分段**: 支持正则表达式分段处理长文本
- **区域排除**: 指定区域（如括号内容）保持文本不转语音
- **命令控制**: 支持 `/ttson` 和 `/ttsoff` 命令开关功能

### 🔧 技术特点
- **OpenAI TTS API规范**: 使用标准的OpenAI TTS接口格式
- **固定API地址**: 预置API服务地址，用户无需配置
- **多音色支持**: 支持多种音色选择（alloy, echo, fable, onyx, nova, shimmer）
- **异步处理**: 完全异步实现，不阻塞机器人响应

## 配置说明

### 必填配置
- **API密钥 (api_key)**: TTS服务的API密钥
- **模型ID (model_id)**: TTS模型，默认 `tts-1`
- **音色ID (voice_id)**: 语音音色，默认 `nova`

### 行为配置
- **概率 (probability)**: 语音回复触发概率（0.0-1.0），默认 0.3
- **周期长度 (cycle_length)**: 随机周期消息数量，默认 100
- **分段正则 (segmentation_regex)**: 文本分段规则，默认 `[。？！]`
- **排除正则 (exclude_regex)**: 不转语音的内容规则，默认 `\\(.*?\\)|\\（.*?\\）`

## 使用方法

### 安装插件
1. 将插件文件夹放入 AstrBot 的 `data/plugins/` 目录
2. 在 AstrBot WebUI 中启用插件
3. 配置 API 密钥等必要参数

### 命令使用
- `/ttson` - 开启概率语音功能
- `/ttsoff` - 关闭概率语音功能
- `/ttsreload` - 重新加载配置（修改配置后使用）
- `/ttsstatus` - 显示插件详细状态信息

### 工作原理
1. 插件监听所有消息回复
2. 按概率决定是否触发语音转换
3. 提取排除区域内容（如括号内文字）
4. 将剩余文本按规则分段
5. 调用TTS API生成语音文件
6. 组合文本和语音消息发送

## 配置示例

```json
{
  "api_key": "your-api-key-here",
  "model_id": "tts-1",
  "voice_id": "nova", 
  "probability": 0.3,
  "cycle_length": 100,
  "segmentation_regex": "[。？！]",
  "exclude_regex": "\\(.*?\\)|\\（.*?\\）",
  "enabled": true
}
```

## 注意事项

⚠️ **重要提醒**
- 需要有效的TTS API密钥才能正常工作
- 生成的音频文件会暂存在系统临时目录
- 插件会自动跳过以 `/` 开头的命令消息
- 概率触发基于消息计数和随机算法

## 兼容性

- **AstrBot版本**: >= 3.4.0
- **Python版本**: >= 3.8
- **支持平台**: QQ (主要测试平台)

## 依赖库

- `httpx >= 0.24.0` - HTTP客户端
- `aiofiles >= 22.1.0` - 异步文件操作

## 开发者

- 作者: TTS Plugin Developer
- 版本: 1.0.0