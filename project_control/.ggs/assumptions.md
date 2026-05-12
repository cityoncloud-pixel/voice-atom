# Assumptions (LLM Best-Effort)

当你回答不了、或信息缺失时，GGS 允许 LLM 给出“最优可执行假设”，但必须全部记录在这里，便于审计与回滚。

格式建议（每条一段）：

## A-0001
- Assumption:
- Rationale:
- Risk Level: low|medium|high
- If wrong, fallback:

## A-0002（豆包 ASR 上传实现）
- Assumption: 火山引擎/豆包 ASR 在 v0.1 实现阶段可采用 **HTTPS 客户端上传音频**（如 multipart 或官方示例中的二进制体），与 `idea.md` §4.2 / §12.1.1 一致；具体 URL、Header、字段名以官方最新文档为准。
- Rationale: `goal.md` 需在无完整账号与文档副本的情况下仍可启动工程；避免在 goal 中写死未经验证的端点字符串。
- Risk Level: medium
- If wrong, fallback: 按官方变更为「流式/WebSocket/仅 URL」等形态时，仅改 `asr/doubao.py` 与相关配置项，保持 `service` 与对外 JSON 契约不变。

