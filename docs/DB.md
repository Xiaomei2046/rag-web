# 数据库模型草案（PostgreSQL + pgvector）

## 扩展
- `pgcrypto`：生成 UUID（可选）
- `vector`（pgvector）：向量类型与索引

## 表：documents
用途：教材文件元数据与处理状态。

字段（建议）：
- `id` uuid pk
- `title` text not null
- `filename` text not null
- `storage_path` text not null
- `status` text not null（queued|processing|completed|failed）
- `created_at` timestamptz not null
- `updated_at` timestamptz not null

索引：
- `status`
- `created_at`

## 表：ingestion_jobs
用途：异步入库任务与进度。

字段：
- `id` uuid pk
- `document_id` uuid fk -> documents.id
- `status` text not null（queued|processing|completed|failed）
- `stage` text null（extract|chunk|embed|store）
- `percent` int not null default 0
- `error_code` text null
- `error_message` text null
- `created_at` timestamptz not null
- `updated_at` timestamptz not null

索引：
- `document_id`
- `status`

## 表：document_pages
用途：按页保存抽取后的文本与页码元数据，便于溯源。

字段：
- `id` uuid pk
- `document_id` uuid fk -> documents.id
- `page_number` int not null
- `text` text not null
- `created_at` timestamptz not null

约束：
- unique(document_id, page_number)

## 表：chunks
用途：切分后的最小检索单元，保留引用信息。

字段：
- `id` uuid pk
- `document_id` uuid fk -> documents.id
- `page_start` int not null
- `page_end` int not null
- `content` text not null
- `metadata` jsonb not null default '{}'
- `embedding` vector(1536) null
- `embedding_model` text null
- `created_at` timestamptz not null

索引：
- `document_id`
- `page_start`
- `embedding`：ivfflat/hnsw（根据 pgvector 版本与数据量选择）

备注：
- embedding 维度取决于实际模型；MVP 可固定一种 embedding 模型，后续再做多维度兼容（不同表或增加维度字段）。

## 表：chat_sessions
用途：对话会话。

字段：
- `id` uuid pk
- `title` text not null
- `created_at` timestamptz not null

## 表：chat_messages
用途：对话消息与引用。

字段：
- `id` uuid pk
- `session_id` uuid fk -> chat_sessions.id
- `role` text not null（user|assistant|system）
- `content` text not null
- `citations` jsonb not null default '[]'
- `llm_provider` text null
- `llm_model` text null
- `usage` jsonb not null default '{}'
- `created_at` timestamptz not null

索引：
- `session_id`
- `created_at`

