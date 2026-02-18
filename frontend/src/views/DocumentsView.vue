<script setup lang="ts">
import type { UploadCustomRequestOptions } from 'naive-ui'
import { NButton, NCard, NDataTable, NSpace, NTag, NUpload, useMessage } from 'naive-ui'
import { computed, h, onMounted, ref } from 'vue'

import { http } from '../api/http'

type DocumentItem = {
  id: string
  title: string
  filename: string
  status: 'queued' | 'processing' | 'completed' | 'failed'
  created_at: string
}

const message = useMessage()
const loading = ref(false)
const documents = ref<DocumentItem[]>([])

async function refresh() {
  loading.value = true
  try {
    const { data } = await http.get<{ items: DocumentItem[] }>('/documents')
    documents.value = data.items
  } finally {
    loading.value = false
  }
}

async function handleDelete(id: string) {
  await http.delete(`/documents/${id}`)
  message.success('已删除')
  await refresh()
}

async function handleReindex(id: string) {
  await http.post(`/documents/${id}/reindex`)
  message.success('已触发重建索引')
  await refresh()
}

async function customRequest(options: UploadCustomRequestOptions) {
  const file = options.file.file
  if (!file) {
    options.onError?.()
    return
  }

  const form = new FormData()
  form.append('file', file)
  form.append('title', file.name)

  try {
    const { data } = await http.post('/documents', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (evt) => {
        if (!evt.total) return
        options.onProgress?.({ percent: (evt.loaded / evt.total) * 100 })
      },
    })
    options.onFinish?.()
    message.success('上传成功，正在解析入库')
    await refresh()
    return data
  } catch (e) {
    options.onError?.()
    throw e
  }
}

const columns = computed(() => [
  { title: '标题', key: 'title' },
  { title: '文件名', key: 'filename' },
  {
    title: '状态',
    key: 'status',
    render: (row: DocumentItem) => {
      const type =
        row.status === 'completed'
          ? 'success'
          : row.status === 'failed'
            ? 'error'
            : row.status === 'processing'
              ? 'warning'
              : 'default'
      return h(NTag, { type }, { default: () => row.status })
    },
  },
  { title: '创建时间', key: 'created_at' },
  {
    title: '操作',
    key: 'actions',
    render: (row: DocumentItem) =>
      h(
        NSpace,
        {},
        {
          default: () => [
            h(
              NButton,
              { size: 'small', onClick: () => handleReindex(row.id) },
              { default: () => '重建索引' },
            ),
            h(
              NButton,
              { size: 'small', type: 'error', onClick: () => handleDelete(row.id) },
              { default: () => '删除' },
            ),
          ],
        },
      ),
  },
])

onMounted(refresh)
</script>

<template>
  <div style="padding: 10px 0 6px">
    <div class="hero-title" style="font-size: 22px">文档管理</div>
    <div class="hero-subtitle">上传教材 PDF 并入库索引</div>
  </div>
  <NSpace vertical size="large" style="margin-top: 14px">
    <NCard title="上传 PDF">
      <NUpload accept=".pdf" :custom-request="customRequest" :max="1">
        <NButton>选择文件</NButton>
      </NUpload>
    </NCard>
    <NCard title="文档列表">
      <NDataTable :loading="loading" :columns="columns" :data="documents" :row-key="(r) => r.id" />
    </NCard>
  </NSpace>
</template>
