import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'
import { useStaffStore } from '@/stores/staff'

const request = axios.create({
  baseURL: '/selforder-api/console',
  timeout: 30000
})

request.interceptors.request.use(
  (config) => {
    try {
      const staffStore = useStaffStore()
      if (staffStore.token) {
        config.headers['X-Staff-Token'] = staffStore.token
      }
    } catch (e) {
      // store not ready yet, skip
    }
    return config
  },
  (error) => Promise.reject(error)
)

request.interceptors.response.use(
  (response) => {
    // blob 响应直接返回（用于文件下载）
    if (response.config.responseType === 'blob') {
      return response
    }
    const res = response.data
    // 如果后端返回 {success: false}，显示错误并reject
    if (res && res.success === false) {
      if (res.message) ElMessage.error(res.message)
      return Promise.reject(res)
    }
    return res
  },
  (error) => {
    if (error.response) {
      if (error.response.status === 401) {
        try {
          const staffStore = useStaffStore()
          staffStore.clearAuth()
        } catch (e) {}
        router.push('/login')
        ElMessage.error('登录已过期，请重新登录')
      } else if (error.response.status === 403) {
        ElMessage.error('没有权限访问')
      } else if (error.response.status === 404) {
        // 404 由后端返回了 message，不重复弹
      } else {
        ElMessage.error(error.response.data?.message || '请求失败')
      }
    } else {
      ElMessage.error('网络错误，请检查网络连接')
    }
    return Promise.reject(error)
  }
)

export default request
