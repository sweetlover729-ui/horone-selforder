<template>
  <div class="special-services">
    <div class="page-header">
      <h2>专项服务</h2>
    </div>

    <div class="card">
      <div class="card-toolbar">
        <el-button type="primary" @click="showDialog('add')">新增专项服务</el-button>
      </div>

      <el-table :data="list" v-loading="loading">
        <el-table-column prop="name" label="名称" />
        <el-table-column prop="price" label="预设价格" width="120">
          <template #default="{ row }">¥{{ row.preset_price }}</template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="300" show-overflow-tooltip />
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button type="primary" link @click="showDialog('edit', row)">编辑</el-button>
            <el-button type="danger" link @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="500px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入专项服务名称" />
        </el-form-item>
        <el-form-item label="预设价格" prop="price">
          <el-input-number v-model="form.price" :min="0" :precision="2" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="请输入描述" />
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
const dialogVisible = ref(false)
const submitLoading = ref(false)
const formRef = ref(null)
const isEdit = ref(false)

const form = reactive({
  id: '',
  name: '',
  price: 0,
  description: ''
})

const rules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  price: [{ required: true, message: '请输入价格', trigger: 'blur' }]
}

const dialogTitle = computed(() => isEdit.value ? '编辑专项服务' : '新增专项服务')

const fetchList = async () => {
  loading.value = true
  try {
    const res = await request.get('/admin/special-services')
    list.value = Array.isArray(data) ? data : (data?.list || [])
  } catch (error) {
    console.error('Failed to fetch:', error)
  } finally {
    loading.value = false
  }
}

const showDialog = (type, row = null) => {
  if (type === 'add') {
    isEdit.value = false
    Object.assign(form, { id: '', name: '', price: 0, description: '' })
  } else {
    isEdit.value = true
    Object.assign(form, { ...row })
  }
  dialogVisible.value = true
}

const handleSubmit = async () => {
  await formRef.value.validate()
  submitLoading.value = true
  try {
    if (isEdit.value) {
      await request.put(`/admin/special-services/${form.id}`, form)
      ElMessage.success('更新成功')
    } else {
      await request.post('/admin/special-services', form)
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

const handleDelete = async (row) => {
  await ElMessageBox.confirm('确认删除此专项服务?', '提示', { type: 'warning' })
  try {
    await request.delete(`/admin/special-services/${row.id}`)
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
</style>
