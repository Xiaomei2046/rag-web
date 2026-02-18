import { createRouter, createWebHistory } from 'vue-router'

import ChatView from './views/ChatView.vue'
import DocumentsView from './views/DocumentsView.vue'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/chat' },
    { path: '/documents', component: DocumentsView },
    { path: '/chat', component: ChatView },
  ],
})
