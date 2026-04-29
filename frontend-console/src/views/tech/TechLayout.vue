<template>
  <div class="tech-layout">
    <div class="tech-header">
      <span class="tech-title">皓壹维修</span>
      <span class="tech-user">{{ userInfo.full_name || userInfo.username }}</span>
      <button class="tech-logout" @click="logout">退出</button>
    </div>
    <div class="tech-content">
      <router-view />
    </div>
    <div class="tech-footer">
      <div class="tech-nav" :class="{ active: route.path === '/tech' }" @click="router.push('/tech')">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/></svg>
        <span>订单</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useStaffStore } from '@/stores/staff'

const router = useRouter()
const route = useRoute()
const staffStore = useStaffStore()
const userInfo = computed(() => staffStore.userInfo)

function logout() {
  staffStore.clearAuth()
  router.push('/login')
}
</script>

<style scoped>
.tech-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  max-width: 480px;
  margin: 0 auto;
  background: #f5f7fa;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}
.tech-header {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  background: #1a3a6c;
  color: white;
  gap: 12px;
}
.tech-title {
  font-weight: 700;
  font-size: 16px;
  flex: 1;
}
.tech-user {
  font-size: 13px;
  opacity: 0.8;
}
.tech-logout {
  background: rgba(255,255,255,0.15);
  border: none;
  color: white;
  padding: 4px 12px;
  border-radius: 14px;
  font-size: 12px;
  cursor: pointer;
}
.tech-content {
  flex: 1;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
}
.tech-footer {
  display: flex;
  border-top: 1px solid #e5e7eb;
  background: white;
  padding: 6px 0 env(safe-area-inset-bottom, 8px);
}
.tech-nav {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 6px;
  color: #9ca3af;
  font-size: 11px;
  cursor: pointer;
}
.tech-nav.active {
  color: #1a3a6c;
}
.tech-nav svg {
  width: 22px;
  height: 22px;
}
</style>
