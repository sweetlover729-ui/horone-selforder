import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useCustomerStore = defineStore('customer', () => {
  const token = ref(localStorage.getItem('client_token') || '')
  const customerInfo = ref(JSON.parse(localStorage.getItem('client_info') || '{}'))

  // 微信登录有 openid，手机登录无 openid 但有 name/phone
  const isLoggedIn = computed(() => !!token.value && (
    !!customerInfo.value.openid || !!customerInfo.value.name || !!customerInfo.value.phone
  ))
  const nickname = computed(() => customerInfo.value.nickname || customerInfo.value.openid?.slice(-6) || '')

  function loginAction(data) {
    // data: 来自API响应，格式为 { id, openid, nickname, token, ... }
    const info = { ...data }
    delete info.token  // token单独存储
    token.value = data.token || data.openid || data.id
    customerInfo.value = info
    localStorage.setItem('client_token', token.value)
    localStorage.setItem('client_info', JSON.stringify(info))
  }

  function logoutAction() {
    token.value = ''
    customerInfo.value = {}
    localStorage.removeItem('client_token')
    localStorage.removeItem('client_info')
  }

  function updateInfo(data) {
    customerInfo.value = { ...customerInfo.value, ...data }
    localStorage.setItem('client_info', JSON.stringify(customerInfo.value))
  }

  return {
    token,
    customerInfo,
    isLoggedIn,
    nickname,
    loginAction,
    logoutAction,
    updateInfo,
  }
})
