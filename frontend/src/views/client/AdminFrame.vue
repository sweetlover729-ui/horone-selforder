<template>
  <div class="admin-frame">
    <div v-if="!isAuthenticated" class="auth-prompt">
      <p>请先 <el-button type="primary" @click="router.push('/admin/login')">登录管理后台</el-button></p>
    </div>
    <iframe 
      v-else
      :src="consoleUrl" 
      class="console-iframe"
      @load="onIframeLoad"
      @error="onIframeError"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const isAuthenticated = ref(false)
const consoleUrl = ref('')

onMounted(() => {
  const token = localStorage.getItem('admin_token')
  if (token) {
    isAuthenticated.value = true
    // console 使用 /console/ 路由
    consoleUrl.value = '/admin/'
  } else {
    router.push('/admin/login')
  }
})

function onIframeLoad() {
  console.log('Console iframe loaded')
}

function onIframeError() {
  console.error('Console iframe error')
}
</script>

<style scoped>
.admin-frame {
  width: 100vw;
  height: 100vh;
  overflow: hidden;
}

.console-iframe {
  width: 100%;
  height: 100%;
  border: none;
}

.auth-prompt {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100vh;
  font-size: 16px;
}
</style>
