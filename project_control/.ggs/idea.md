# Idea

# voice-atom 需求说明书

> 版本：v0.1
> 状态：需求定义稿
> 目标：作为 GAEH / Cursor / Codex 的项目输入文档

---

## 1. 项目定位

`voice-atom` 是一个 **语音转文字原子智能体**。

它封装一项明确、可复用、可被外部系统调用的底层能力：

```text
Audio Input → ASR Provider → Text Result
```

这里的“原子智能体”不是指具备任务规划、意图理解、工具调用决策的完整 Agent，而是指一个 **atomic callable capability**：

- 它是独立能力单元；
- 它有稳定输入；
- 它有标准输出；
- 它可以被 CLI、Python SDK、HTTP API、其他智能体、桌面软件或本地工作流调用；
- 它只完成“语音/音频 → 文字/JSON”的能力闭环。

`voice-atom` 不是完整语音助手，不负责意图理解、模式判断、命令执行、内容整理、Obsidian 写入、LLM 改写或长期 Agent 规划。

---

## 2. 核心边界

### 2.1 负责什么

`voice-atom` 负责：

1. 从麦克风录音；
2. 接收音频文件；
3. 调用 ASR Provider；
4. 返回转写文本；
5. 返回标准 JSON 结构；
6. 提供 CLI 调用；
7. 提供 Python SDK 调用；
8. 提供 Local HTTP API 调用；
9. 管理 Provider 配置；
10. 提供配置检查；
11. 提供稳定错误码；
12. 默认使用本地 `whisper.cpp`。

### 2.2 不负责什么

`voice-atom` 不做以下事情：

- 不判断文本是命令还是内容；
- 不提供模式选择；


### 2.3 硬边界

`voice-atom` 只输出文本与结构化转写结果。

它的输出中不得包含以下语义决策字段：

```json
{
  "mode": "...",
  "intent": "...",
  "command": "...",
  "target_app": "...",
  "task_type": "..."
}
```

允许包含 Provider、模型、音频路径、时长、语言、错误码等工程信息。

---

## 3. 第一批交付目标

第一批必须同时完成三种调用形态：

1. CLI 调用；
2. Python SDK 调用；
3. Local HTTP API 调用。

HTTP API 不后移，必须和 CLI / SDK 同批设计、同批实现基础能力。

### 3.1 第一批必须支持的输入

第一批必须支持：

1. 麦克风固定秒数录音；
2. 音频文件转写。

第一批不要求：

- 按键开始/停止录音；
- VAD 静音检测；
- 自动停止；
- 热键监听；
- 桌面悬浮窗；
- 浏览器端完整产品。

这些可以作为后续增强能力。

---

## 4. Provider 顺位

Provider 顺位固定如下：

```text
1. local whisper.cpp
2. doubao ASR
3. browser speech adapter
```

### 4.1 默认 Provider

默认 Provider 必须是：

```text
whisper_cpp
```

也就是说，在没有显式指定 Provider 时，系统应优先尝试本地 `whisper.cpp`。

### 4.2 doubao ASR 定位

`doubao ASR` 是第二顺位可选云端 Provider。

**集成形态（已定）**：采用 **上传模式**——由 `voice-atom` 在本机读取音频后，通过 HTTPS 将音频数据 **直接上传** 至豆包 ASR 接口完成识别；**不依赖**「公网可访问的音频 URL」或本机反向隧道。因此 **一般情况下不需要** ngrok 等代理；若后续官方 API 变更为「仅支持 URL 拉取」等形态，再单独评估，不在 v0.1 默认假设内。

要求：

- 不得作为默认 Provider；
- 不得在用户未显式配置时上传音频；
- 只有当用户显式设置 `VOICE_ATOM_PROVIDER=doubao` 时才使用；
- 可作为高质量中文云端转写选项；
- 未来是否作为 fallback 必须由显式配置决定。

默认不允许自动 fallback 到 doubao。

### 4.3 browser speech adapter 定位

`browser speech adapter` 指浏览器端语音识别方案，例如 Web Speech API。

注意：

- 这里不是 TTS；
- TTS = Text To Speech，文字转语音；
- ASR = Automatic Speech Recognition，语音转文字；
- `voice-atom` 是 ASR 项目，不是 TTS 项目。

`browser speech adapter` 的定位：

- 只作为后续浏览器客户端或 Web Demo 的实验性输入方案；
- 不进入 Python core MVP；
- 不作为默认 Provider；
- 不替代 `whisper.cpp`。

如果未来实现，必须明确标记：

```text
experimental
browser-only
not default provider
```

---

## 5. 推荐技术栈

第一版建议使用 Python。

推荐技术：

- Python 3.10+
- Typer 或 Click：CLI 框架
- FastAPI + Uvicorn：Local HTTP API
- sounddevice 或 pyaudio：麦克风录音
- pydantic：结构化模型
- python-dotenv：环境变量管理
- subprocess：第一版调用 whisper.cpp CLI
- httpx：后续调用 doubao ASR
- pytest：测试

---

## 6. 项目结构

建议项目结构：

```text
voice-atom/
├── README.md
├── pyproject.toml
├── .env.example
├── voice_atom/
│   ├── __init__.py
│   ├── cli.py
│   ├── server.py
│   ├── recorder.py
│   ├── service.py
│   ├── models.py
│   ├── config.py
│   ├── errors.py
│   ├── asr/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── whisper_cpp.py
│   │   └── doubao.py
│   └── utils/
│       ├── audio.py
│       └── paths.py
├── tests/
│   ├── test_service.py
│   ├── test_cli.py
│   ├── test_server.py
│   └── test_providers.py
└── runs/
```

---

## 7. 核心数据流

### 7.1 麦克风录音转写

```text
CLI / SDK / HTTP
↓
service.transcribe_from_mic(seconds)
↓
recorder.record(seconds)
↓
audio.wav
↓
provider.transcribe(audio_path)
↓
TranscriptionResult
```

### 7.2 音频文件转写

```text
CLI / SDK / HTTP
↓
service.transcribe_file(audio_path)
↓
validate audio file
↓
provider.transcribe(audio_path)
↓
TranscriptionResult
```

所有入口必须经过 `service.py`。

禁止：

- CLI 直接调用 Provider；
- HTTP API 直接调用 Provider；
- SDK 绕过 service；
- 多入口重复实现转写逻辑。

---

## 8. 标准返回模型

### 8.1 成功返回

所有入口必须返回同一结构。

```json
{
  "ok": true,
  "text": "今天我想记录一下 voice atom 的设计。",
  "language": "zh",
  "provider": "whisper_cpp",
  "audio_path": "runs/2026-05-12/001.wav",
  "duration_seconds": 8.0,
  "created_at": "2026-05-12T10:30:00-07:00",
  "meta": {
    "model": "ggml-small.bin",
    "source": "mic"
  }
}
```

字段说明：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| ok | boolean | 是 | 是否成功 |
| text | string | 是 | 转写文本 |
| language | string | 否 | 语言，例如 zh、en |
| provider | string | 是 | 当前 ASR Provider |
| audio_path | string | 否 | 本地音频路径 |
| duration_seconds | number | 否 | 音频时长 |
| created_at | string | 是 | 创建时间，ISO 格式 |
| meta | object | 是 | Provider 或模型相关元信息 |

### 8.2 失败返回

```json
{
  "ok": false,
  "error": {
    "code": "ASR_FAILED",
    "message": "ASR provider failed",
    "recoverable": true,
    "details": {}
  }
}
```

字段说明：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| ok | boolean | 是 | 固定为 false |
| error.code | string | 是 | 稳定错误码 |
| error.message | string | 是 | 人类可读错误信息 |
| error.recoverable | boolean | 是 | 是否可恢复 |
| error.details | object | 是 | 调试信息，不得包含密钥 |

---

## 9. 错误码

必须定义稳定错误码：

```text
MIC_NOT_FOUND
RECORDING_FAILED
AUDIO_SAVE_FAILED
WHISPER_CPP_NOT_FOUND
WHISPER_MODEL_NOT_FOUND
WHISPER_TRANSCRIBE_FAILED
API_KEY_MISSING
ASR_FAILED
PROVIDER_TIMEOUT
INVALID_AUDIO_FILE
CONFIG_INVALID
UNKNOWN_ERROR
```

### 9.1 错误码说明

| 错误码 | 含义 | recoverable |
|---|---|---:|
| MIC_NOT_FOUND | 未找到麦克风 | true |
| RECORDING_FAILED | 录音失败 | true |
| AUDIO_SAVE_FAILED | 音频保存失败 | true |
| WHISPER_CPP_NOT_FOUND | whisper.cpp 可执行文件不存在 | true |
| WHISPER_MODEL_NOT_FOUND | whisper.cpp 模型文件不存在 | true |
| WHISPER_TRANSCRIBE_FAILED | whisper.cpp 转写失败 | true |
| API_KEY_MISSING | 云端 Provider 缺少 API Key | true |
| ASR_FAILED | ASR Provider 失败 | true |
| PROVIDER_TIMEOUT | Provider 超时 | true |
| INVALID_AUDIO_FILE | 音频文件不存在或格式不支持 | true |
| CONFIG_INVALID | 配置不合法 | true |
| UNKNOWN_ERROR | 未知错误 | false |

---

## 10. ASR Provider 接口

### 10.1 Provider 基类

```python
class ASRProvider:
    name: str
    priority: int
    is_local: bool

    def check_available(self) -> ProviderStatus:
        ...

    def transcribe(self, audio_path: str) -> TranscriptionResult:
        ...
```

### 10.2 Provider 要求

所有 Provider 必须满足：

1. 实现统一接口；
2. 返回统一 `TranscriptionResult`；
3. 不向上层暴露 Provider 私有异常；
4. 失败时转换为稳定错误码；
5. 不在日志中输出敏感信息；
6. 不把业务含义写入返回结果；
7. 不返回 mode、intent、command 等语义字段。

### 10.3 Provider 选择规则

Provider 选择由配置决定：

```env
VOICE_ATOM_PROVIDER=whisper_cpp
```

规则：

- 未配置时，默认 `whisper_cpp`；
- 配置为 `whisper_cpp` 时，使用本地 whisper.cpp；
- 配置为 `doubao` 时，使用 doubao ASR；
- 不允许在未显式配置时自动上传音频到云端；
- fallback 默认关闭。

---

## 11. whisper.cpp Provider 要求

`whisper_cpp` 是第一顺位、默认 Provider。

### 11.1 配置项

```env
VOICE_ATOM_PROVIDER=whisper_cpp
VOICE_ATOM_WHISPER_CPP_BIN=./bin/whisper-cli
VOICE_ATOM_WHISPER_MODEL=./models/ggml-small.bin
VOICE_ATOM_LANGUAGE=zh
VOICE_ATOM_THREADS=4
```

### 11.2 第一版实现方式

第一版可以通过 `subprocess` 调用 whisper.cpp CLI。

示例逻辑：

```text
python service
↓
subprocess run whisper-cli
↓
parse output
↓
TranscriptionResult
```

### 11.3 约束

- `whisper_cpp.py` 负责 whisper.cpp 的命令构造、执行、输出解析；
- `service.py` 不允许拼接 whisper.cpp 命令；
- `cli.py` 不允许直接调用 whisper.cpp；
- `server.py` 不允许直接调用 whisper.cpp；
- whisper.cpp CLI 失败时必须返回 `WHISPER_TRANSCRIBE_FAILED` 或更具体错误；
- 找不到可执行文件时返回 `WHISPER_CPP_NOT_FOUND`；
- 找不到模型文件时返回 `WHISPER_MODEL_NOT_FOUND`。

### 11.4 后续演进

后续可以从 subprocess 改为：

- C API binding；
- Python binding；
- 后台常驻 whisper 服务；
- GPU 加速；
- 模型自动下载。

但不得破坏上层 service 接口。

---

## 12. doubao ASR Provider 要求

`doubao` 是第二顺位、可选云端 Provider。

### 12.1 配置项

```env
VOICE_ATOM_PROVIDER=doubao
DOUBAO_API_KEY=xxx
DOUBAO_ASR_MODEL=xxx
```

### 12.1.1 调用方式（与 idea 4.2 一致）

- 豆包侧采用 **上传模式**：客户端携带凭证向官方 ASR 端点发起请求，在请求中 **附带音频内容**（如 multipart / 二进制体，以火山/豆包当期 API 为准）。
- 不要求部署可被外网访问的音频文件服务；v0.1 不将「URL 拉取音频」作为默认实现路径。

### 12.2 使用规则

- 只有用户显式设置 `VOICE_ATOM_PROVIDER=doubao` 时才使用；
- 默认不得上传音频；
- 缺少 `DOUBAO_API_KEY` 时返回 `API_KEY_MISSING`；
- Provider 调用失败时返回 `ASR_FAILED` 或 `PROVIDER_TIMEOUT`；
- 日志不得打印 API Key；
- `config check` 不得返回完整 API Key。

### 12.3 定位

`doubao` 适合：

- 需要更高中文云端识别质量；
- 本地机器性能不足；
- 用户明确愿意上传音频。

`doubao` 不适合：

- 默认 Provider；
- 静默 fallback；
- 无提示上传音频；
- 替代本地 whisper.cpp 的核心地位。

---

## 13. CLI 需求

第一批必须支持以下命令。

### 13.1 麦克风录音转写

```powershell
voice-atom record --seconds 10
```

默认输出纯文本。默认录制 **10** 秒；可选 `--countdown N`（默认 **3**，`0` 关闭）：**倒计时结束后再开启麦克风**，倒计时提示输出到 stderr，避免与 stdout 纯文本混淆。

```powershell
voice-atom record --seconds 10 --json
```

输出标准 JSON（准备提示与倒计时同样走 stderr）。

### 13.2 音频文件转写

```powershell
voice-atom transcribe-file ./audio.wav
```

默认输出纯文本。

```powershell
voice-atom transcribe-file ./audio.wav --json
```

输出标准 JSON。

### 13.3 Provider 列表

```powershell
voice-atom providers list
```

返回当前可用 Provider 及状态。

### 13.4 配置检查

```powershell
voice-atom config check
```

检查：

- 当前 Provider；
- whisper.cpp 可执行文件；
- whisper.cpp 模型文件；
- 输出目录；
- doubao 配置是否完整；
- HTTP 服务默认 host/port。

不得输出完整 API Key。

### 13.5 启动 HTTP 服务

```powershell
voice-atom server --host 127.0.0.1 --port 17860
```

默认 host 必须是：

```text
127.0.0.1
```

默认 port：

```text
17860
```

---

## 14. Python SDK 需求

第一批必须提供以下函数：

```python
transcribe_from_mic(seconds: int) -> TranscriptionResult
transcribe_file(audio_path: str) -> TranscriptionResult
get_providers() -> ProviderList
check_config() -> ConfigCheckResult
```

### 14.1 示例

```python
from voice_atom import transcribe_from_mic, transcribe_file

result = transcribe_from_mic(seconds=8)
print(result.text)

result = transcribe_file("./test.wav")
print(result.text)
```

### 14.2 SDK 约束

- SDK 必须调用 service 层；
- SDK 不得直接依赖具体 Provider；
- SDK 返回结构化模型，不只返回字符串；
- SDK 不做模式判断；
- SDK 不做意图识别；
- SDK 不执行外部命令，除非是 Provider 内部必要调用，例如 whisper.cpp CLI。

---

## 15. Local HTTP API 需求

HTTP API 是第一批目标，不后移。

### 15.1 服务监听

默认监听：

```text
127.0.0.1:17860
```

不得默认监听 `0.0.0.0`。

如果允许外部访问，必须显式配置。

### 15.2 必须支持的接口

```http
GET /healthz
POST /record
POST /transcribe-file
GET /providers
GET /config/check
```

### 15.3 GET /healthz

返回：

```json
{
  "ok": true,
  "service": "voice-atom",
  "version": "0.1.0"
}
```

### 15.4 POST /record

请求：

```json
{
  "seconds": 8
}
```

返回标准 `TranscriptionResult`。

### 15.5 POST /transcribe-file

请求：

```json
{
  "audio_path": "./audio.wav"
}
```

返回标准 `TranscriptionResult`。

### 15.6 GET /providers

返回示例：

```json
{
  "ok": true,
  "default_provider": "whisper_cpp",
  "providers": [
    {
      "name": "whisper_cpp",
      "enabled": true,
      "priority": 1,
      "local": true
    },
    {
      "name": "doubao",
      "enabled": false,
      "priority": 2,
      "local": false
    }
  ]
}
```

### 15.7 GET /config/check

返回配置检查结果。

要求：

- 不得泄露 API Key；
- 不得返回完整密钥；
- 可返回 masked key，例如 `sk-***abcd`；
- 必须检查 whisper.cpp bin 和 model 是否存在；
- 必须检查输出目录是否可写。

---

## 16. 配置规则

### 16.1 .env 示例

```env
VOICE_ATOM_PROVIDER=whisper_cpp
VOICE_ATOM_OUTPUT_DIR=./runs
VOICE_ATOM_DEFAULT_SECONDS=10

VOICE_ATOM_WHISPER_CPP_BIN=./bin/whisper-cli
VOICE_ATOM_WHISPER_MODEL=./models/ggml-small.bin
VOICE_ATOM_LANGUAGE=zh
VOICE_ATOM_THREADS=4

VOICE_ATOM_HOST=127.0.0.1
VOICE_ATOM_PORT=17860

DOUBAO_API_KEY=
DOUBAO_ASR_MODEL=
```

### 16.2 配置原则

- API Key 只能从环境变量或 `.env` 读取；
- 不允许写死在代码中；
- 日志不得打印 API Key；
- 默认 Provider 是 `whisper_cpp`；
- 默认不上传音频；
- 默认保存音频到本地 `runs` 目录；
- HTTP 服务默认只监听 `127.0.0.1`。

---

## 17. 录音与音频要求

### 17.1 第一批录音能力

第一批只要求固定秒数录音：

```powershell
voice-atom record --seconds 10
```

录音结果保存为 wav 文件。

### 17.2 音频文件要求

第一批至少支持：

- wav

后续可增加：

- mp3
- m4a
- webm
- flac

若格式不支持，返回：

```text
INVALID_AUDIO_FILE
```

### 17.3 音频保存路径

默认保存到：

```text
runs/YYYY-MM-DD/NNN.wav
```

示例：

```text
runs/2026-05-12/001.wav
```

---

## 18. 安全与隐私要求

必须满足：

1. 默认使用本地 `whisper.cpp`；
2. 默认不上传音频；
3. doubao 只有显式配置时才使用；
4. HTTP API 默认只监听 `127.0.0.1`；
5. 日志不得打印 API Key；
6. 配置检查不得返回完整 API Key；
7. 默认保存音频到本地 `runs` 目录；
8. 后续允许配置是否保留音频；
9. 不采集与 ASR 无关的数据；
10. 不做长期记忆。

---

## 19. 测试要求

第一批至少包含以下测试：

### 19.1 service 测试

- `transcribe_file` 能调用 mock provider；
- `transcribe_from_mic` 能调用 mock recorder + mock provider；
- Provider 失败能转换为标准错误；
- 缺少音频文件返回 `INVALID_AUDIO_FILE`。

### 19.2 CLI 测试

- `voice-atom config check` 可运行；
- `voice-atom providers list` 可运行；
- `voice-atom transcribe-file ./test.wav --json` 返回标准结构；
- 缺少参数时显示合理错误。

### 19.3 HTTP API 测试

- `GET /healthz` 返回 ok；
- `GET /providers` 返回 Provider 列表；
- `GET /config/check` 不泄露 API Key；
- `POST /transcribe-file` 返回标准结构；
- 错误时返回标准错误结构。

### 19.4 Provider 测试

- whisper.cpp bin 不存在时返回 `WHISPER_CPP_NOT_FOUND`；
- whisper.cpp model 不存在时返回 `WHISPER_MODEL_NOT_FOUND`；
- doubao 缺少 API Key 时返回 `API_KEY_MISSING`。

---

## 20. 第一批验收标准

第一批完成后，以下命令必须可用。

### 20.1 CLI 验收

```powershell
voice-atom config check
voice-atom providers list
voice-atom record --seconds 10 --json
voice-atom transcribe-file ./test.wav --json
voice-atom server --host 127.0.0.1 --port 17860
```

### 20.2 HTTP API 验收

```http
GET /healthz
GET /providers
GET /config/check
POST /record
POST /transcribe-file
```

### 20.3 Python SDK 验收

```python
from voice_atom import transcribe_from_mic, transcribe_file

transcribe_from_mic(seconds=8)
transcribe_file("./test.wav")
```

### 20.4 Provider 验收

默认 Provider 必须是：

```text
whisper_cpp
```

`providers list` 中必须显示：

```text
whisper_cpp priority=1 local=true
```

`doubao` 可以显示为 disabled，除非用户显式配置。

### 20.5 边界验收

第一批交付中不得出现：

- 模式选择 UI；
- command parser；
- intent router；
- Obsidian 写入；
- Markdown 日记整理；
- Cursor 控制；
- GAEH 执行；
- LLM 改写；
- 自动上传云端；
- 默认 doubao Provider。

---

## 21. 后续增强方向

后续可以增加，但不属于第一批硬性范围：

1. 手动停止录音；
2. VAD 静音检测；
3. 自动停止；
4. 热键触发；
5. 系统托盘；
6. 桌面小窗口；
7. browser speech adapter demo；
8. 模型自动下载；
9. whisper.cpp GPU 加速配置；
10. 音频质量检测；
11. 是否保留音频的配置；
12. 后台常驻服务。

注意：这些增强仍不得改变 `voice-atom` 的核心边界。

---

## 22. 开发原则

必须遵守：

- 本地优先；
- whisper.cpp 第一顺位；
- HTTP API 同批完成；
- CLI / SDK / HTTP 共用 service 层；
- Provider 可替换；
- 不做模式判断；
- 不做意图识别；
- 不做命令执行；
- 不绑定任何上层应用；
- 不做完整语音助手；
- 默认不上传音频；
- 默认监听 127.0.0.1；
- 输出结构稳定；
- 错误码稳定；
- 可测试。

---

## 23. 无歧义审查

### 23.1 项目是否是普通脚本？

不是。

`voice-atom` 是可被其他系统调用的语音转文字原子智能体，必须提供 CLI / SDK / Local HTTP API 三种调用形态。

### 23.2 项目是否是语音助手？

不是。

它不做意图理解、命令执行、Obsidian 写入、日记整理或 Agent 规划。

### 23.3 HTTP API 是否后续再做？

不是。

HTTP API 是第一批交付目标，必须与 CLI / SDK 同批完成基础能力。

### 23.4 默认 Provider 是什么？

默认 Provider 是：

```text
whisper_cpp
```

### 23.5 豆包 ASR 是默认吗？

不是。

豆包 ASR 是第二顺位可选云端 Provider。只有用户显式配置 `VOICE_ATOM_PROVIDER=doubao` 时才使用。

### 23.6 浏览器方案是什么？

浏览器方案是 `browser speech adapter`，不是 TTS，不进入 Python core MVP，只作为后续浏览器端实验方案。

### 23.7 是否允许 fallback？

默认不允许自动 fallback。

如果后续支持 fallback，必须由显式配置开启，并且不得静默上传音频。

### 23.8 是否有模式？

没有。

`voice-atom` 不提供模式选择，不做模式判断，不返回 mode 字段。

### 23.9 是否有 intent？

没有。

`voice-atom` 不做 intent detection，不返回 intent 字段。

### 23.10 是否执行命令？

不执行。

`voice-atom` 只返回文本和 JSON，不负责文本之后的动作。

---

## 24. 最终一句话定义

`voice-atom` 是一个 **本地 whisper.cpp 优先的语音转文字原子智能体**。

第一批必须提供：

```text
CLI + Python SDK + Local HTTP API
```

它只完成：

```text
Audio Input → ASR Provider → Text Result
```

它不做：

```text
模式判断 / 意图识别 / 命令执行 / 上层应用集成 / Agent 规划
```

---

## 25. 审查结论

```text
PASS
```

通过条件：

1. `whisper_cpp` 必须是默认第一 Provider；
2. HTTP API 必须与 CLI / SDK 同批交付；
3. 所有入口必须共用 service 层；
4. 不得引入模式判断、意图识别、命令执行；
5. doubao 不得作为默认 Provider；
6. 浏览器方案不得被误写为 TTS；
7. 输出结构不得包含 mode、intent、command、target_app 等语义字段。



## Context (Optional)

- Existing repo?:
- Target users?:
- Deadline?:

