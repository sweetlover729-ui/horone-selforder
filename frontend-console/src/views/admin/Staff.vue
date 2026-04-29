<template>
  <div class="staff-page">
    <div class="page-header">
      <h2>员工管理</h2>
    </div>

    <div class="card">
      <div class="card-toolbar">
        <el-button type="primary" @click="showDialog('add')">新增员工</el-button>
      </div>

      <el-table :data="list" v-loading="loading">
        <el-table-column prop="username" label="用户名" />
        <el-table-column prop="fullName" label="姓名" />
        <el-table-column label="角色" width="120">
          <template #default="{ row }">
            <span class="role-tag">{{ getRoleLabel(row.role) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-switch
              :model-value="row.is_active === 1"
              @change="toggleStatus(row)"
              :loading="row._loading"
              :disabled="row.id === currentUserId"
            />
          </template>
        </el-table-column>
        <el-table-column prop="createdAt" label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatTime(row.createdAt) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button type="primary" link @click="showDialog('edit', row)">编辑</el-button>
            <el-button type="danger" link @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 弹窗 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="500px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" :disabled="isEdit" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="姓名" prop="fullName">
          <el-input v-model="form.fullName" placeholder="请输入姓名" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="form.role" placeholder="请选择角色" style="width: 100%;">
            <el-option label="管理员" value="admin" />
            <el-option label="维修技师" value="technician" />
            <el-option label="接待员" value="receptionist" />
          </el-select>
        </el-form-item>
        <el-form-item label="密码" :prop="isEdit ? '' : 'password'">
          <el-input
            v-model="form.password"
            type="password"
            show-password
            :placeholder="isEdit ? '不修改请留空' : '请输入密码'"
          />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="form.status">
            <el-radio :label="1">启用</el-radio>
            <el-radio :label="0">禁用</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitLoading">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/utils/request'

const list = ref([])
const loading = ref(false)
const currentUserId = computed(() => useStaffStore().userInfo?.id)
const dialogVisible = ref(false)
const submitLoading = ref(false)
const formRef = ref(null)
const isEdit = ref(false)

const form = reactive({
  id: '',
  username: '',
  fullName: '',
  role: 'receptionist',
  password: '',
  status: 1
})

const rules = computed(() => ({
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  fullName: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
  password: isEdit.value ? [] : [{ required: true, message: '请输入密码', trigger: 'blur' }]
}))

const dialogTitle = computed(() => isEdit.value ? '编辑员工' : '新增员工')

const getRoleLabel = (role) => {
  const map = { admin: '管理员', technician: '维修技师', receptionist: '接待员' }
  return map[role] || role
}

const formatTime = (time) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit'
  })
}

const fetchList = async () => {
  loading.value = true
  try {
    const res = await request.get('/admin/staff')
    list.value = Array.isArray(res) ? res : (res?.data || res?.list || [])
  } catch (error) {
    console.error('Failed to fetch:', error)
  } finally {
    loading.value = false
  }
}

const showDialog = (type, row = null) => {
  if (type === 'add') {
    isEdit.value = false
    Object.assign(form, { id: '', username: '', fullName: '', role: 'receptionist', password: '', status: 1 })
  } else {
    isEdit.value = true
    Object.assign(form, {
      id: row.id,
      username: row.username || '',
      fullName: row.fullName || row.full_name || '',
      role: row.role || 'receptionist',
      password: '',
      status: row.is_active ?? row.status ?? 1,
    })
  }
  dialogVisible.value = true
}

const handleSubmit = async () => {
  await formRef.value.validate()
  submitLoading.value = true
  try {
    const payload = {
      username: form.username,
      fullName: form.fullName,
      full_name: form.fullName,
      role: form.role,
      is_active: form.status,
    }
    if (form.password) payload.password = form.password

    if (isEdit.value) {
      await request.put(`/admin/staff/${form.id}`, payload)
      ElMessage.success('更新成功')
    } else {
      await request.post('/admin/staff', payload)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    fetchList()
  } catch (error) {
    console.error('Submit failed:', error)
  } finally {
    submitLoading.value = false
  }
}

const toggleStatus = async (row) => {
  row._loading = true
  try {
    await request.put(`/admin/staff/${row.id}`, { is_active: row.is_active === 1 ? 0 : 1 }).catch(e => { if (e.response?.status === 401) ElMessage.warning("禁用自己后将无法恢复，请重新登录后操作"); throw e })
    row.is_active = row.is_active === 1 ? 0 : 1
    ElMessage.success('状态已更新')
  } catch (error) {
    console.error('Toggle status failed:', error)
  } finally {
    row._loading = false
  }
}

const handleDelete = async (row) => {
  await ElMessageBox.confirm('确认删除此员工?', '提示', { type: 'warning' })
  try {
    await request.delete(`/admin/staff/${row.id}`)
    ElMessage.success('删除成功')
    fetchList()
  } catch (error) {
    console.error('Delete failed:', error)
  }
}

onMounted(() => {
  fetchList()
})
</script>

<style scoped>
.card-toolbar {
  margin-bottom: 16px;
  display: flex;
  justify-content: flex-end;
}

.role-tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  background: #e6f4ff;
  color: #1677ff;
}
</style>
