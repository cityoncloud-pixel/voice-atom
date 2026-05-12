# GAEH (Goal-Driven AI Engineering Harness)

这套模板用于把任意工程项目变成“可被 AI 按统一流程推进”的落地骨架：Owner 只负责目标/边界/验收与同意门禁；AI 负责工程拆解、实现、验证、报告与修复。

## Quick Start (Owner)
1) 填写/生成目标：
- 简单写：`project_control/goal.md`
- 或使用 GGS：编辑 `project_control/.ggs/idea.md`，再把 `project_control/.ggs/templates/runner.prompt.md` 粘贴给 Codex/Cursor 执行一次

2) 发起执行（先澄清，后同意门禁）：
把下面这句话发给 Codex/Cursor（或运行 `gaeh start` 复制输出）：
> 按 GAEH 流程开始：先检查 goal 是否清晰（尤其边界与 UI 交互），再给出最小问题清单；目标清晰后必须先征得我同意（等待我回复 APPROVE）再开始连续实现到验收完成，并把过程落盘到 plans/reviews/reports 与 project_control/*.md。

3) 同意执行：
- 对话中回复：`APPROVE`
- 或修改：`project_control/approval.json` / 使用 `gaeh approve`

## Governance
- Tiny Fix 允许不写 spec/plan，但必须：最小验证 + report + decision_log + task_queue 同步。
- 发现问题（已完成但不对）：把复现写到 `project_control/issues.md`，AI 先给“可能原因 + 证据收集计划”，定位根因后修复并回归验证。
- 新要求/变更：追加到 `project_control/change_requests.md`，必要时更新 `project_control/goal.md`，并再次征得同意后继续。

---

## voice-atom（本仓库 Python 包）

语音转文字原子能力：**CLI + Python SDK + 本机 HTTP API**，默认本地 `whisper.cpp`。需求与边界见 `project_control/.ggs/idea.md`，验收目标见 `project_control/goal.md`。

### 安装（开发）

```powershell
python -m pip install -e ".[dev]"
```

### whisper.cpp

请自备可执行文件与模型，并在环境变量或 `.env` 中配置 `VOICE_ATOM_WHISPER_CPP_BIN`、`VOICE_ATOM_WHISPER_MODEL`。模板见 `.env.example`。

- **Windows 预编译包**：可从 [whisper.cpp Releases](https://github.com/ggml-org/whisper.cpp/releases) 下载 `whisper-bin-x64.zip`，解压后将 `Release` 目录中的 `whisper-cli.exe` 与全部 `*.dll` 放到仓库 `bin/`。
- **中文/多语言模型（约 200MB 量级）**：推荐 `ggml-small-q5_1.bin`（约 190MB，多语言含中文），下载地址示例：  
  `https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small-q5_1.bin`  
  保存到 `models/` 后在 `.env` 中指向该文件即可。

### 常用命令

```powershell
voice-atom config check --json
voice-atom providers list --json
voice-atom transcribe-file .\audio.wav --json
voice-atom record --seconds 10 --json
voice-atom server --host 127.0.0.1 --port 17860
```

`record` 默认 **先倒计时 3 秒再开麦**（`--countdown N`，`0` 关闭）；提示与数字在 **stderr**，JSON 在 **stdout**。

### 网页按住说话（测试 UI）

1. 启动：`voice-atom server`  
2. 浏览器打开：**`http://127.0.0.1:17860/ui/`**  
3. 按住「按住说话」录音，松开后自动调用 **`POST /transcribe-upload`** 转写，结果追加到文本框。  
4. 本机需已安装 **`ffmpeg`**（用于把浏览器 WebM 转成 16kHz WAV 再送 whisper）。

### 豆包 ASR（上传模式）

设置 `VOICE_ATOM_PROVIDER=doubao`，并配置 `DOUBAO_API_KEY`、`DOUBAO_ASR_MODEL`、`DOUBAO_ASR_UPLOAD_URL`（HTTPS 上传端点与字段以火山引擎文档为准；本实现为通用 multipart 上传占位，可按文档调整）。

### 测试

```powershell
python -m pytest
```

