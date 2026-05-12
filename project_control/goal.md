# goal.md (Owner-owned)

> 依据：`project_control/.ggs/idea.md`（v0.1 需求定义稿）。实现前须按 GAEH 征得 Owner 同意（`APPROVE` 或 `approval.json`）。

## 1) Intent / 原始意图

交付 `voice-atom`：**本地 whisper.cpp 优先的语音转文字原子能力**，以统一 `service` 层支撑 **CLI + Python SDK + Local HTTP API** 三种调用方式，使外部系统可稳定复用「音频 → 文本/标准 JSON」，而不承担意图、模式、命令执行或上层应用集成。

## 2) Target Outcome / 目标交付物

在仓库内实现 **Python 可安装包**（建议 `pyproject.toml` + `voice_atom/`），结构对齐 idea 第 6 节，至少包含：

- **核心**：`service.py`（唯一转写编排入口）、`recorder.py`、`config.py`、`models.py`、`errors.py`、`asr/base.py`、`asr/whisper_cpp.py`、`asr/doubao.py`、`utils/`（音频与路径等）。
- **三入口**：`cli.py`（Typer/Click）、包级 SDK 导出（`transcribe_from_mic`、`transcribe_file`、`get_providers`、`check_config`）、`server.py`（FastAPI + Uvicorn）。
- **配置与文档**：根目录 `README.md` 更新（安装、依赖 whisper.cpp、环境变量、三入口用法）；`.env.example`（无真实密钥）。
- **测试**：`tests/` 覆盖 idea 第 19 节所列（service / CLI / HTTP / provider 行为，含 mock）。

第一批 **不交付** 浏览器 Web Speech 适配器进 Python core（见 Scope）。

## 3) Success Criteria / 成功标准（可验证）

1. **测试**：在项目根执行 `pytest`（或 `python -m pytest`）全部通过；包含 service 层 mock、CLI/HTTP 关键路径、Provider 错误码（如 `WHISPER_CPP_NOT_FOUND`、`WHISPER_MODEL_NOT_FOUND`、`API_KEY_MISSING`、`INVALID_AUDIO_FILE`）的断言。
2. **CLI（与 idea §20.1 一致）**：安装/editable 安装后，`voice-atom config check`、`voice-atom providers list`、`voice-atom transcribe-file <wav> --json`、`voice-atom server --host 127.0.0.1 --port 17860` 可执行；`voice-atom record --seconds N --json` 在具备麦克风与 whisper 配置的环境中可完成一次录音转写（CI 可对 record 做 skip 或 mock，但代码路径须存在且单测覆盖）。
3. **HTTP**：默认监听 `127.0.0.1:17860`；`GET /healthz`、`GET /providers`、`GET /config/check`、`POST /record`、`POST /transcribe-file` 行为与 idea §15 一致；`GET /config/check` 不泄露完整 API Key（可 masked）。
4. **默认 Provider**：未配置 `VOICE_ATOM_PROVIDER` 时行为等价于 `whisper_cpp`；`providers` 列表中 `whisper_cpp` 为 priority=1 且 local=true；**不得**默认或未配置即上传云端；**不得**默认自动 fallback 到 `doubao`。
5. **返回结构**：成功/失败 JSON 符合 idea §8；禁止在输出中加入 `mode` / `intent` / `command` / `target_app` / `task_type` 等语义决策字段；所有入口须经 `service`，禁止 CLI/HTTP 绕过 `service` 直调 Provider。

## 4) Scope / 范围

### In Scope

- 固定秒数麦克风录音转写、**WAV 文件**转写（第一批格式）；输出落盘路径约定 `runs/YYYY-MM-DD/NNN.wav`（可配置 `VOICE_ATOM_OUTPUT_DIR`）。
- `whisper_cpp`：第一版通过 `subprocess` 调用可配置 CLI；配置项见 idea §11。
- `doubao`：**仅**在 `VOICE_ATOM_PROVIDER=doubao` 时启用；**上传模式**（HTTPS 客户端直连上传音频，不依赖公网音频 URL）；缺 key 返回 `API_KEY_MISSING`。
- 稳定错误码集合（idea §9）、`config check` / `providers list`、结构化日志且不打印 API Key。

### Out of Scope

- 意图识别、模式选择、命令解析、Obsidian/日记/Cursor/GAEH 执行、LLM 改写、完整语音助手。
- 按键起停录音、VAD、自动停止、热键、系统托盘、桌面悬浮窗、浏览器端完整产品。
- **browser speech adapter** 进入 Python core MVP（仅允许在文档中标记为后续 experimental）。
- 非 WAV 的多种音频格式（mp3/m4a 等）可作为后续增强，第一批不强制。

## 5) Constraints / 约束

- **语言与运行时**：Python 3.10+；依赖选型对齐 idea §5（Typer 或 Click、FastAPI、Uvicorn、pydantic、python-dotenv、httpx、pytest；录音 sounddevice 或 pyaudio）。
- **安全与隐私**：默认 Provider `whisper_cpp`；HTTP 默认 `127.0.0.1`，禁止默认 `0.0.0.0`；外网监听须显式配置；密钥仅来自环境变量或 `.env`，不得硬编码。
- **架构**：`whisper_cpp` 命令拼接与解析仅在 `asr/whisper_cpp.py`；`service.py` 不拼接 whisper 命令；CLI/server 不直接调用 whisper 二进制。
- **平台**：开发以当前仓库主环境为准（Windows 10+）；录音依赖在 Windows 上须可文档化说明（端口音频库等）。

## 6) Inputs / 输入材料与上下文

- `project_control/.ggs/idea.md`（v0.1，含上传模式豆包与边界）。
- 现有 GAEH 骨架与 GitHub 仓库；实现阶段需查阅 **whisper.cpp** 官方 CLI 用法及 **火山引擎/豆包 ASR** 当前「上传类」HTTP API 文档（端点、鉴权、请求体格式以官方为准）。

## 7) UI / Interaction Requirements（如涉及 UI）

不涉及图形界面产品。交互形态为：**终端 CLI**、**本机 HTTP 调用**、**Python import 调用**；无额外 UI 需求。

## 8) Boundary & Edge Cases / 边界与模糊点（重要）

- **`POST /transcribe-file` 的 `audio_path`**：语义为 **HTTP 服务进程所在机器上的路径**（本机 Local API）；非浏览器客户端本地路径。若未来支持远程上传文件，需新接口（multipart），不在本 goal 内。
- **失败响应**：失败体须符合 idea §8.2；成功体须含 `meta`（允许 `{}`）；`text` 在失败时的取舍实现前与 spec 对齐（建议失败时不返回有效转写 `text` 或固定为空字符串，二选一并写死测试）。
- **whisper.cpp**：二进制与模型文件由用户自备路径；项目负责检测缺失并返回对应错误码。
- **doubao**：具体端点、鉴权头、multipart 字段名以官方文档为准；若与假设不符，更新 `assumptions.md` 并调整实现。

## 9) Output Format / 输出格式

- 可运行包：`pyproject.toml`，控制台脚本入口 `voice-atom`。
- 源码树：`voice_atom/`、`tests/`、`runs/`（目录可空或 `.gitkeep`）、`.env.example`。
- 验证命令：`pytest`；人工可选验收 idea §20 所列 CLI/HTTP/SDK 命令。

## 10) Risks / 风险与未知

- **豆包 ASR**：具体 API 版本与请求体格式以火山文档为准，实现期可能微调 `doubao.py` 与配置项命名（风险：中；缓解：先抽象接口 + 契约测试 + 记录假设）。
- **Windows 音频栈**：`sounddevice`/`pyaudio` 安装与权限问题可能导致 CI 与本地差异（风险：中；缓解：录音逻辑抽象 + mock 测试）。
- **whisper.cpp CLI 名称/参数**：不同构建产物可能不同（风险：低；缓解：可配置 `VOICE_ATOM_WHISPER_CPP_BIN`）。

## 11) Approval Policy / 同意门禁（Owner 决策）

目标清晰后，AI **不得**在未获 Owner 同意前开始连续大规模实现。Owner 可：

- 在对话回复：`APPROVE`（或 `APPROVE <task_id>`）
- 或更新：`project_control/approval.json`
