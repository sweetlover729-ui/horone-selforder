import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useStaffStore = defineStore('staff', () => {
  const token = ref(localStorage.getItem('console_token') || '')
  const userInfo = ref(JSON.parse(localStorage.getItem('console_user') || '{}'))

  const setAuth = (tokenVal, userVal) => {
    token.value = tokenVal
    userInfo.value = userVal
    localStorage.setItem('console_token', tokenVal)
    localStorage.setItem('console_user', JSON.stringify(userVal))
  }

  const clearAuth = () => {
    token.value = ''
    userInfo.value = {}
    localStorage.removeItem('console_token')
    localStorage.removeItem('console_user')
  }

  const isLoggedIn = () => !!token.value

  const isAdmin = () => userInfo.value?.role === 'admin'

  return {
    token,
    userInfo,
    setAuth,
    clearAuth,
    isLoggedIn,
    isAdmin
  }
})
