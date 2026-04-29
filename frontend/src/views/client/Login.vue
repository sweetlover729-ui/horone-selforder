<template>
  <div class="login-page">
    <div class="login-container">
      <!-- Logo -->
      <div class="login-logo">
        <div class="login-logo-mark">皓壹</div>
        <div class="login-logo-text">皓壹维修服务平台</div>
      </div>

      <!-- 切换标签 -->
      <div class="login-tabs">
        <div
          class="login-tab"
          :class="{ active: activeTab === 'phone' }"
          @click="activeTab = 'phone'"
        >
          手机号登录
        </div>
        <div
          class="login-tab"
          :class="{ active: activeTab === 'wechat' }"
          @click="activeTab = 'wechat'"
        >
          微信扫码
        </div>
      </div>

      <!-- 手机号登录 -->
      <el-card v-show="activeTab === 'phone'" class="login-card">
        <el-form
          ref="phoneFormRef"
          :model="phoneForm"
          :rules="phoneRules"
          label-position="top"
          @submit.prevent="handlePhoneLogin"
        >
          <el-form-item label="姓名" prop="name">
            <el-input
              v-model="phoneForm.name"
              placeholder="请输入您的姓名"
              size="large"
              clearable
              :prefix-icon="User"
            />
          </el-form-item>

          <el-form-item label="手机号" prop="phone">
            <el-input
              v-model="phoneForm.phone"
              placeholder="请输入手机号码"
              size="large"
              clearable
              maxlength="11"
              :prefix-icon="Cellphone"
              @input="phoneForm.phone = phoneForm.phone.replace(/\D/g, '')"
            />
          </el-form-item>

          <el-form-item>
            <el-button
              type="primary"
              size="large"
              :loading="phoneLoading"
              native-type="submit"
              style="width: 100%; margin-top: 8px"
            >
              登录 / 注册
            </el-button>
          </el-form-item>
        </el-form>

        <div class="login-note">
          首次使用将自动注册，下次使用同一手机号即可直接登录
        </div>
      </el-card>

      <!-- 微信扫码 -->
      <el-card v-show="activeTab === 'wechat'" class="login-card">
        <div class="login-card-title">微信扫码登录</div>
        <div class="login-card-sub">使用微信扫码，快速登录</div>

        <div class="qrcode-area">
          <div class="qrcode-placeholder">
            <div class="qrcode-inner">
              <div class="qrcode-icon">
                <el-icon size="56" color="#52c41a"><Coin /></el-icon>
              </div>
              <div class="qrcode-wechat-icon">
                <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
                  <circle cx="16" cy="16" r="16" fill="#52c41a"/>
                  <path d="M10.5 14.5C10.5 14.5 11.5 18 16 18C20.5 18 21.5 14.5 21.5 14.5" stroke="white" stroke-width="1.5" stroke-linecap="round"/>
                  <path d="M13 12C13 12 14 13.5 16 13.5C18 13.5 19 12 19 12" stroke="white" stroke-width="1.5" stroke-linecap="round"/>
                </svg>
              </div>
              <div class="qrcode-tip">模拟二维码</div>
            </div>
          </div>
        </div>

        <div class="login-actions">
          <el-button
            type="success"
            size="large"
            :loading="wechatLoading"
            style="width: 100%"
            @click="handleMockWechatLogin"
          >
            模拟微信扫码登录
          </el-button>
        </div>

        <div class="login-note">
          正式环境将显示微信扫码二维码，扫码后自动完成登录
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useCustomerStore } from '@/stores/customer'
import { User, Cellphone, Coin } from '@element-plus/icons-vue'
import request from '@/utils/request'

const router = useRouter()
const route = useRoute()
const customerStore = useCustomerStore()

const activeTab = ref('phone') // 默认显示手机号登录
const phoneFormRef = ref()
const phoneLoading = ref(false)
const wechatLoading = ref(false)

const phoneForm = reactive({
  name: '',
  phone: '',
})

const phoneRules = {
  name: [
    { required: true, message: '请输入姓名', trigger: 'blur' },
    { min: 2, message: '姓名至少2个字符', trigger: 'blur' },
  ],
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '手机号格式不正确', trigger: 'blur' },
  ],
}

async function handlePhoneLogin() {
  const valid = await phoneFormRef.value?.validate().catch(() => false)
  if (!valid) return

  phoneLoading.value = true
  try {
    const res = await request.post('/client/auth/phone-login', {
      name: phoneForm.name.trim(),
      phone: phoneForm.phone.trim(),
    })
    if (res.success) {
      customerStore.loginAction(res.data)
      ElMessage.success(`欢迎 ${res.data.name}，登录成功`)
      const redirect = route.query.redirect || '/'
      router.push(redirect)
    }
  } catch (e) {
    ElMessage.error(e?.message || '登录失败，请重试')
  } finally {
    phoneLoading.value = false
  }
}

function generateOpenid() {
  return 'wx_' + Math.random().toString(36).slice(2, 12).toUpperCase()
}

async function handleMockWechatLogin() {
  wechatLoading.value = true
  try {
    const openid = generateOpenid()
    const nickname = '潜水用户_' + openid.slice(-4)
    const res = await request.post('/client/auth/wechat-login', {
      code: 'mock_login',
      openid,
      nickname,
    })
    if (res.success) {
      customerStore.loginAction(res.data)
      ElMessage.success('登录成功')
      const redirect = route.query.redirect || '/'
      router.push(redirect)
    }
  } catch (e) {
    ElMessage.error('登录失败')
  } finally {
    wechatLoading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #f0f5ff 0%, #f5f7fa 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px 16px;
}

.login-container {
  width: 100%;
  max-width: 400px;
}

.login-logo {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 24px;
  gap: 10px;
}

.login-logo-mark {
  width: 56px;
  height: 56px;
  background: #1677ff;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 16px;
  font-weight: 700;
  box-shadow: 0 4px 16px rgba(22, 119, 255, 0.3);
}

.login-logo-text {
  font-size: 18px;
  font-weight: 600;
  color: #1d2129;
}

.login-tabs {
  display: flex;
  background: #fff;
  border-radius: 12px 12px 0 0;
  border: 1px solid #e5e6eb;
  border-bottom: none;
  overflow: hidden;
}

.login-tab {
  flex: 1;
  padding: 14px;
  text-align: center;
  font-size: 15px;
  font-weight: 500;
  color: #86909c;
  cursor: pointer;
  transition: all 0.2s;
  user-select: none;
}

.login-tab.active {
  color: #1677ff;
  background: #f0f5ff;
  font-weight: 600;
  border-bottom: 2px solid #1677ff;
  margin-bottom: -1px;
}

.login-card {
  border-radius: 0 0 12px 12px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08);
  border-top: none;
}

.login-card-title {
  font-size: 18px;
  font-weight: 600;
  color: #1d2129;
  text-align: center;
  margin-bottom: 6px;
  margin-top: 8px;
}

.login-card-sub {
  font-size: 13px;
  color: #86909c;
  text-align: center;
  margin-bottom: 24px;
}

.qrcode-area {
  display: flex;
  justify-content: center;
  margin-bottom: 24px;
}

.qrcode-placeholder {
  width: 180px;
  height: 180px;
  border: 2px dashed #52c41a;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fafff0;
}

.qrcode-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.qrcode-wechat-icon {
  margin-top: 4px;
}

.qrcode-tip {
  font-size: 12px;
  color: #52c41a;
  font-weight: 500;
}

.login-actions {
  margin-bottom: 16px;
}

.login-note {
  font-size: 12px;
  color: #86909c;
  text-align: center;
  line-height: 1.6;
}
</style>
