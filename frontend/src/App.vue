<script setup lang="ts">
import { NButton, NConfigProvider, NLayout, NLayoutContent, NLayoutHeader, NLayoutSider, NMenu, NMessageProvider, NSpace } from 'naive-ui'
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const selectedKey = computed(() => route.path)
const collapsed = ref(false)

const menuOptions = [
  { label: '问答', key: '/chat' },
  { label: '文档管理', key: '/documents' },
]

const themeOverrides = {
  common: {
    primaryColor: '#8CB818',
    primaryColorHover: '#9ED22A',
    primaryColorPressed: '#7AA90F',
    successColor: '#8CB818',
    warningColor: '#FADF2E',
    warningColorHover: '#FFE95A',
    warningColorPressed: '#E2C919',
    textColorBase: '#004132',
    bodyColor: '#D0EBB7',
    borderColor: 'rgba(0, 65, 50, 0.12)',
  },
  Layout: {
    color: 'transparent',
    headerColor: 'rgba(255, 251, 226, 0.7)',
    siderColor: 'rgba(255, 251, 226, 0.85)',
  },
  Card: {
    color: 'rgba(255, 251, 226, 0.9)',
    borderRadius: '14px',
  },
  Menu: {
    itemTextColor: 'rgba(0, 65, 50, 0.78)',
    itemTextColorActive: '#004132',
    itemTextColorHover: '#004132',
    itemColorActive: 'rgba(208, 235, 183, 0.55)',
    itemColorHover: 'rgba(208, 235, 183, 0.35)',
    borderRadius: '12px',
  },
  Button: {
    borderRadiusSmall: '10px',
    borderRadiusMedium: '12px',
    borderRadiusLarge: '14px',
  },
} as const
</script>

<template>
  <NConfigProvider :theme-overrides="themeOverrides">
    <NMessageProvider>
      <NLayout class="app-shell" has-sider>
        <NLayoutSider
          bordered
          collapse-mode="width"
          :collapsed-width="72"
          :width="240"
          :collapsed="collapsed"
          show-trigger
          @collapse="collapsed = true"
          @expand="collapsed = false"
        >
          <div style="padding: 14px 12px 10px">
            <div style="display: flex; align-items: center; justify-content: space-between; gap: 12px">
              <div style="font-weight: 800; letter-spacing: -0.02em">RAG Web</div>
              <NButton size="small" tertiary @click="router.push('/chat')">新对话</NButton>
            </div>
          </div>
          <div style="padding: 0 8px 12px">
            <NMenu :value="selectedKey" :options="menuOptions" @update:value="(k) => router.push(String(k))" />
          </div>
        </NLayoutSider>

        <NLayout>
          <NLayoutHeader
            bordered
            style="height: 56px; padding: 0 14px; display: flex; align-items: center; justify-content: space-between"
          >
            <div style="font-weight: 650; opacity: 0.9">{{ selectedKey === '/documents' ? '文档管理' : '问答' }}</div>
            <NSpace size="small">
              <NButton size="small" quaternary>帮助</NButton>
              <NButton size="small" quaternary>下载</NButton>
            </NSpace>
          </NLayoutHeader>
          <NLayoutContent style="padding: 18px 0 28px">
            <div class="page-container">
              <RouterView />
            </div>
          </NLayoutContent>
        </NLayout>
      </NLayout>
    </NMessageProvider>
  </NConfigProvider>
</template>
