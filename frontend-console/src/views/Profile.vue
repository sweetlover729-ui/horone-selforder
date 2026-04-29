<template>
  <div class="profile-page">
    <div class="page-header">
      <h2>账号设置</h2>
    </div>

    <div class="profile-content">
      <!-- 账号信息 -->
      <div class="card">
        <div class="card-title">账号信息</div>
        <div class="info-grid">
          <div class="info-item">
            <span class="label">用户名:</span>
            <span class="value">{{ staffStore.userInfo?.username }}</span>
          </div>
          <div class="info-item">
            <span class="label">姓名:</span>
            <span class="value">{{ staffStore.userInfo?.fullName || '-' }}</span>
          </div>
          <div class="info-item">
            <span class="label">角色:</span>
            <span class="value">{{ roleLabel }}</span>
          </div>
          <div class="info-item">
            <span class="label">状态:</span>
            <span class="value">{{ staffStore.userInfo?.status === 1 ? '启用' : '禁用' }}</span>
          </div>
        </div>
      </div>

      <!-- 修改密码 -->
      <div class="card">
        <div class="card-title">修改密码</div>
        <el-form :model="pwdForm" :rules="pwdRules" ref="pwdFormRef" label-width="120px" style="max-width: 500px;">
          <el-form-item label="当前密码" prop="oldPassword">
            <el-input v-model="pwdForm.oldPassword" type="password" show-password placeholder="请输入当前密码" />
          </el-form-item>
          <el-form-item label="新密码" prop="newPassword">
            <el-input v-model="pwdForm.newPassword" type="password" show-password placeholder="请输入新密码" />
          </el-form-item>
          <el-form-item label="确认密码" prop="confirmPassword">
            <el-input v-model="pwdForm.confirmPassword" type="password" show-password placeholder="请再次输入新密码" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleChangePwd" :loading="pwdLoading">修改密码</el-button>
          </el-form-item>
        </el-form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'
import { useStaffStore } from '@/stores/staff'

const staffStore = useStaffStore()

const roleLabel = computed(() => {
  const map = {
    admin: '管理员',
    technician: '维修技师',
    receptionist: '接待员'
  }
  return map[staffStore.userInfo?.role] || '员工'
})

const pwdFormRef = ref(null)
const pwdLoading = ref(false)

const pwdForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const validateConfirm = (rule, value, callback) => {
  if (value !== pwdForm.newPassword) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const pwdRules = {
  oldPassword: [{ required: true, message: '请输入当前密码', trigger: 'blur' }],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    { validator: validateConfirm, trigger: 'blur' }
  ]
}

const handleChangePwd = async () => {
  await pwdFormRef.value.validate()
  pwdLoading.value = true
  try {
    await request.put('/auth/password', {
      old_password: pwdForm.oldPassword,
      new_password: pwdForm.newPassword
    })
    ElMessage.success('密码修改成功')
    pwdForm.oldPassword = ''
    pwdForm.newPassword = ''
    pwdForm.confirmPassword = ''
  } catch (error) {
    console.error('Change password failed:', error)
  } finally {
    pwdLoading.value = false
  }
}
</script>

<style scoped>
.profile-page {
  max-width: 800px;
}

.profile-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
</style>
