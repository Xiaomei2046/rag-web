# API 契约（MVP）

Base URL：`/api`

## 约定
- 全部接口返回 `application/json`
- 统一错误格式：
  - `{"error": {"code": "string", "message": "string", "details": any}}`
- 时间字段为 ISO8601 UTC 字符串
- 文件上传采用 `multipart/form-data`

## 健康检查
### GET `/healthz`
返回：
```json
{"status":"ok"}
```

## 文档
### POST `/documents`
上传 PDF 并创建 ingestion 任务。

请求（multipart）：
- `file`: PDF 文件
- `title`(optional): 文档标题

返回：
```json
{
  "document": {
    "id": "uuid",
    "title": "string",
    "filename": "string",
    "status": "queued",
    "created_at": "2026-01-01T00:00:00Z"
  },
  "ingestion_job": {
    "id": "uuid",
    "status": "queued"
  }
}
```

### GET `/documents`
返回：
```json
{
  "items": [
    {
      "id": "uuid",
      "title": "string",
      "filename": "string",
      "status": "queued|processing|completed|failed",
      "created_at": "2026-01-01T00:00:00Z"
    }
  ]
}
```

### GET `/documents/{document_id}`
返回：
```json
{
  "id": "uuid",
  "title": "string",
  "filename": "string",
  "status": "queued|processing|completed|failed",
  "created_at": "2026-01-01T00:00:00Z"
}
```

### DELETE `/documents/{document_id}`
返回：
```json
{"deleted": true}
```

### POST `/documents/{document_id}/reindex`
触发重建索引（异步）。

返回：
```json
{
  "ingestion_job": {"id":"uuid","status":"queued"}
}
```

## Ingestion Jobs
### GET `/ingestion-jobs/{job_id}`
返回：
```json
{
  "id": "uuid",
  "document_id": "uuid",
  "status": "queued|processing|completed|failed",
  "progress": {
    "stage": "extract|chunk|embed|store",
    "percent": 0
  },
  "error": null,
  "created_at": "2026-01-01T00:00:00Z",
  "updated_at": "2026-01-01T00:00:00Z"
}
```

## Chat
### POST `/chat/sessions`
创建会话。

请求：
```json
{"title":"string"}
```

返回：
```json
{"id":"uuid","title":"string","created_at":"2026-01-01T00:00:00Z"}
```

### GET `/chat/sessions`
返回：
```json
{"items":[{"id":"uuid","title":"string","created_at":"2026-01-01T00:00:00Z"}]}
```

### GET `/chat/sessions/{session_id}`
返回（含最近消息，可分页后续扩展）：
```json
{
  "id":"uuid",
  "title":"string",
  "messages":[
    {"id":"uuid","role":"user","content":"...","created_at":"..."},
    {"id":"uuid","role":"assistant","content":"...","citations":[],"created_at":"..."}
  ]
}
```

### POST `/chat/sessions/{session_id}/messages`
发送问题并返回一次回答。

请求：
```json
{
  "content": "string",
  "document_ids": ["uuid"],
  "llm": {
    "provider": "openai_compat|ollama|anthropic",
    "model": "string",
    "temperature": 0.2
  },
  "retrieval": {
    "top_k": 5
  }
}
```

返回：
```json
{
  "message": {
    "id":"uuid",
    "role":"assistant",
    "content":"string",
    "citations":[
      {
        "chunk_id":"uuid",
        "document_id":"uuid",
        "doc_title":"string",
        "page_start": 1,
        "page_end": 1,
        "snippet":"string",
        "score": 0.0
      }
    ],
    "usage": {
      "prompt_tokens": 0,
      "completion_tokens": 0,
      "total_tokens": 0
    },
    "created_at":"2026-01-01T00:00:00Z"
  }
}
```

## LLM Providers
### GET `/llm/providers`
返回可用 provider 与默认模型（从配置读取）。
```json
{
  "items":[
    {"provider":"openai_compat","models":["gpt-4o-mini"]},
    {"provider":"ollama","models":["qwen2.5:7b-instruct"]}
  ]
}
```

