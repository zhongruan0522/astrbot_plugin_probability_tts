# 概率语音插件

基于AstrBot的概率语音转换插件，支持TTS语音合成、智能分段和内容过滤。

## 功能特性

1. **语音合成**: 使用OpenAI兼容的TTS API生成语音
2. **概率发送**: 根据设置的概率发送语音或文本消息
3. **智能分段**: 自动按句子分割内容，括号内容保持为文本
4. **思考过滤**: 自动过滤大模型的思考链内容
5. **灵活配置**: 支持动态切换音色和开关功能
6. **自定义分段**: 可配置分段正则表达式
7. **关键词管理**: 可管理需要过滤的思考链关键词

## 安装方法

1. 将 `probability_voice` 文件夹复制到 AstrBot 的插件目录
2. 在WebUI中启用插件
3. 配置插件参数

## 配置说明

### 基础配置
- **model_name**: TTS模型名称（默认: tts-1）
- **api_key**: TTS服务的API密钥
- **voice_id**: 音色ID（默认: alloy）
- **probability_percentage**: 语音发送概率（0-100，默认: 90）
- **probability_total**: 概率总数（默认: 10）
- **tts_enabled**: TTS总开关（默认: 开启）
- **segment_pattern**: 分段正则表达式（默认: [。！？.!?]）
- **thinking_keywords**: 思考链关键词列表（默认: ["<thinking>", "</thinking>", "<思考>", "</思考>"]）

### 概率计算说明
当设置概率百分比为90%，概率总数为10时：
- 每连续10条消息中，前9条会发送语音
- 第10条会发送纯文本
- 然后循环往复

## 使用指令

### 切换音色
```
/ttsid <音色ID>
```
示例：`/ttsid nova`

### 开关TTS功能
```
/ttsswitch on/off
```
或使用中文：
```
/ttsswitch 开启/关闭
```

### 设置分段正则表达式
```
/segmentpattern <正则表达式>
```
示例：`/segmentpattern [。！？.!?;；]`  （添加分号作为分隔符）

### 管理思考链关键词
```
/thinkingkeywords add <关键词>    # 添加关键词
/thinkingkeywords remove <关键词> # 删除关键词
/thinkingkeywords list           # 查看所有关键词
```

示例：
```
/thinkingkeywords add <思考链>
/thinkingkeywords remove </思考链>
/thinkingkeywords list
```

## 处理流程

1. 接收消息
2. 过滤思考链标签内的内容（支持自定义关键词）
3. 根据概率决定是否发送语音
4. 智能分段处理（使用配置的正则表达式）：
   - 按配置的分段符分割
   - 括号内容保持为文本
5. 按顺序发送语音或文本消息

## 示例

输入文本：
```
你好呀~你今天过的怎么样（探头）要抱抱
```

处理结果：
- 语音消息：你好呀~
- 语音消息：你今天过的怎么样
- 文本消息：（探头）
- 语音消息：要抱抱

## 注意事项

1. 请确保正确配置API密钥
2. 语音文件会保存在 `data/probability_voice` 目录
3. 插件会自动处理消息计数，无需手动干预
4. 支持中英文混合内容处理
5. 分段正则表达式需要是有效的正则表达式格式

## 项目地址
https://github.com/zhongruan0522/astrbot_plugin_probability_tts