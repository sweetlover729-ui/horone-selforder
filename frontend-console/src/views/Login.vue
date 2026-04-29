<template>
  <div class="login-page">
    <div class="login-box">
      <div class="login-header">
        <h1 class="login-title">皓壹维修服务平台控制台</h1>
        <p class="login-sub">Horone Maintenance Console</p>
      </div>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        @submit.prevent="handleLogin"
        class="login-form"
      >
        <el-form-item prop="username">
          <el-input
            v-model="form.username"
            placeholder="账号"
            size="large"
            prefix-icon="User"
            @keyup.enter="handleLogin"
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="密码"
            size="large"
            prefix-icon="Lock"
            show-password
            @keyup.enter="handleLogin"
          />
        </el-form-item>

        <el-button
          type="primary"
          size="large"
          :loading="loading"
          class="login-btn"
          @click="handleLogin"
        >
          登录
        </el-button>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'
import { useStaffStore } from '@/stores/staff'

const router = useRouter()
const staffStore = useStaffStore()

const formRef = ref(null)
const loading = ref(false)

const form = reactive({
  username: '',
  password: ''
})

const rules = {
  username: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const handleLogin = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    loading.value = true
    try {
      const data = await request.post('/auth/login', {
        username: form.username,
        password: form.password
      })

      staffStore.setAuth(data.token, data.staff)
      ElMessage.success('登录成功')
      // 根据角色跳转
      router.push(data.staff.role === 'admin' ? '/admin' : '/tech')
    } catch (error) {
      ElMessage.error(error.response?.data?.message || "请求失败"); console.error("Login failed:", error)
    } finally {
      loading.value = false
    }
  })
}
</script>

<style scoped>
.login-page {
  width: 100%;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f0f7ff 0%, #e6f0ff 100%);
}

.login-box {
  width: 400px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 24px rgba(22, 119, 255, 0.08);
  padding: 48px 40px;
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.login-title {
  font-size: 22px;
  font-weight: 600;
  color: #1677ff;
  margin-bottom: 8px;
}

.login-sub {
  font-size: 13px;
  color: #bfbfbf;
  letter-spacing: 1px;
}

.login-form {
  margin-top: 0;
}

.login-form :deep(.el-form-item) {
  margin-bottom: 20px;
}

.login-form :deep(.el-input__wrapper) {
  padding: 12px 16px;
}

.login-btn {
  width: 100%;
  height: 44px;
  font-size: 15px;
  margin-top: 8px;
}
</style>
