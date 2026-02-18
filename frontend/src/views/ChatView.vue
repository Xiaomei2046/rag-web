<script setup lang="ts">
import { NButton, NCard, NForm, NFormItem, NInput, NList, NListItem, NSelect, NSpace, useMessage } from 'naive-ui'
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { http } from '../api/http'

type ProviderItem = { provider: string; models: string[] }
type ProvidersResponse = { items: ProviderItem[] }
type DocumentItem = { id: string; title: string; status: string }

type Citation = { doc_title: string; page_start: number; page_end: number; snippet: string }
type Usage = { total_tokens?: number; latency_ms?: { retrieval?: number; llm?: number; total?: number } }
type ChatMessage = { role: 'user' | 'assistant'; content: string; citations?: Citation[]; usage?: Usage }

const message = useMessage()
const router = useRouter()
const input = ref('')
const messages = ref<ChatMessage[]>([])
const sessionId = ref<string | null>(null)

const providers = ref<ProviderItem[]>([])
const provider = ref('openai_compat')
const model = ref('')

const documents = ref<DocumentItem[]>([])
const selectedDocumentIds = ref<string[]>([])

const modelOptions = computed(() => {
  const p = providers.value.find((x) => x.provider === provider.value)
  return (p?.models ?? []).map((m) => ({ label: m, value: m }))
})

const hasMessages = computed(() => messages.value.length > 0)

const documentOptions = computed(() =>
  documents.value
    .filter((d) => d.status === 'completed')
    .map((d) => ({ label: d.title, value: d.id })),
)

async function loadProviders() {
  const { data } = await http.get<ProvidersResponse>('/llm/providers')
  providers.value = data.items
  if (!providers.value.find((p) => p.provider === provider.value)) {
    provider.value = providers.value[0]?.provider ?? 'openai_compat'
  }
  const models = providers.value.find((p) => p.provider === provider.value)?.models ?? []
  if (!models.includes(model.value)) {
    model.value = models[0] ?? ''
  }
}

async function loadDocuments() {
  const { data } = await http.get<{ items: DocumentItem[] }>('/documents')
  documents.value = data.items
}

async function send() {
  const content = input.value.trim()
  if (!content) return

  messages.value.push({ role: 'user', content })
  input.value = ''

  try {
    if (!sessionId.value) {
      const { data: s } = await http.post<{ id: string }>('/chat/sessions', { title: 'Demo' })
      sessionId.value = s.id
    }
    const { data } = await http.post(`/chat/sessions/${sessionId.value}/messages`, {
      content,
      document_ids: selectedDocumentIds.value,
      llm: { provider: provider.value, model: model.value, temperature: 0.2 },
      retrieval: { top_k: 5 },
    })
    messages.value.push({
      role: 'assistant',
      content: data.message?.content ?? '',
      citations: data.message?.citations ?? [],
      usage: data.message?.usage ?? {},
    })
  } catch {
    message.error('请求失败（请确认后端与数据库/LLM配置）')
  }
}

function quickFill(text: string) {
  input.value = text
}

onMounted(async () => {
  await Promise.all([loadProviders().catch(() => {}), loadDocuments().catch(() => {})])
})
</script>

<template>
  <div v-if="!hasMessages" class="hero">
    <div class="hero-title">下午好，有什么可以帮忙的？</div>
    <div class="hero-subtitle">上传教材、选择范围，然后开始提问（回答会带引用）</div>

    <NCard style="width: min(760px, 100%)">
      <NInput v-model:value="input" type="textarea" :autosize="{ minRows: 4, maxRows: 10 }" placeholder="请输入任务或问题…" />
      <div style="display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-top: 12px">
        <NSpace size="small">
          <NButton size="small" quaternary @click="router.push('/documents')">上传教材</NButton>
          <NButton size="small" quaternary @click="loadDocuments">刷新文档</NButton>
        </NSpace>
        <NButton type="primary" @click="send">发送</NButton>
      </div>
    </NCard>

    <div class="chip-row" style="margin-top: 4px">
      <NButton size="small" secondary @click="quickFill('请用教材原文解释：井眼稳定的基本机理与影响因素。')">解释概念</NButton>
      <NButton size="small" secondary @click="quickFill('请总结教材中关于钻井液密度设计的要点，并给出引用页码。')">总结要点</NButton>
      <NButton size="small" secondary @click="quickFill('请列出套管设计需要考虑的主要载荷工况，并引用原文。')">列出清单</NButton>
      <NButton size="small" secondary @click="quickFill('基于教材内容生成 5 道练习题（含答案与引用）。')">生成练习</NButton>
    </div>

    <NCard title="范围与模型" style="width: min(760px, 100%); margin-top: 8px">
      <NForm label-placement="left" label-width="110">
        <NFormItem label="LLM Provider">
          <NSelect
            v-model:value="provider"
            :options="providers.map((p) => ({ label: p.provider, value: p.provider }))"
            @update:value="loadProviders"
          />
        </NFormItem>
        <NFormItem label="模型">
          <NSelect v-model:value="model" :options="modelOptions" />
        </NFormItem>
        <NFormItem label="教材范围">
          <NSelect v-model:value="selectedDocumentIds" multiple :options="documentOptions" placeholder="默认：全部已完成文档" />
        </NFormItem>
      </NForm>
    </NCard>
  </div>

  <NSpace v-else vertical size="large">
    <NCard title="范围与模型">
      <NForm label-placement="left" label-width="110">
        <NFormItem label="LLM Provider">
          <NSelect
            v-model:value="provider"
            :options="providers.map((p) => ({ label: p.provider, value: p.provider }))"
            @update:value="loadProviders"
          />
        </NFormItem>
        <NFormItem label="模型">
          <NSelect v-model:value="model" :options="modelOptions" />
        </NFormItem>
        <NFormItem label="教材范围">
          <NSelect v-model:value="selectedDocumentIds" multiple :options="documentOptions" placeholder="默认：全部已完成文档" />
        </NFormItem>
      </NForm>
    </NCard>

    <NCard title="对话">
      <NList bordered>
        <NListItem v-for="(m, idx) in messages" :key="idx">
          <div style="white-space: pre-wrap">
            <strong>{{ m.role }}:</strong>
            {{ m.content }}
          </div>
          <div v-if="m.role === 'assistant' && m.citations && m.citations.length" style="margin-top: 8px">
            <strong>引用：</strong>
            <ul style="margin: 6px 0 0 18px">
              <li v-for="(c, cidx) in m.citations" :key="cidx" style="margin-bottom: 6px">
                <div>
                  {{ c.doc_title }}（p{{ c.page_start }}<span v-if="c.page_end !== c.page_start">-{{ c.page_end }}</span>）
                </div>
                <div style="opacity: 0.85; white-space: pre-wrap">{{ c.snippet }}</div>
              </li>
            </ul>
          </div>
          <div v-if="m.role === 'assistant' && m.usage" style="margin-top: 8px; opacity: 0.85">
            <span v-if="m.usage.total_tokens != null">tokens: {{ m.usage.total_tokens }}</span>
            <span v-if="m.usage.latency_ms?.total != null" style="margin-left: 12px">latency: {{ m.usage.latency_ms.total }}ms</span>
          </div>
        </NListItem>
      </NList>
      <NSpace style="margin-top: 12px" align="end">
        <NInput v-model:value="input" type="textarea" :autosize="{ minRows: 2, maxRows: 6 }" placeholder="输入你的问题" />
        <NButton type="primary" @click="send">发送</NButton>
      </NSpace>
    </NCard>
  </NSpace>
</template>
