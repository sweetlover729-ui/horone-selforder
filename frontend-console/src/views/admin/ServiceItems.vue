<template>
  <div class="service-items">
    <div class="page-header">
      <h2>维修检项管理</h2>
      <p class="tip">维修工在维修过程中勾选的检查项目，按产品类别分组</p>
    </div>

    <div class="card">
      <div class="card-toolbar">
        <el-select v-model="filterType" placeholder="筛选产品类别" clearable style="width:180px;margin-right:12px">
          <el-option v-for="t in productTypes" :key="t.id" :label="t.name" :value="t.id" />
        </el-select>
        <el-button type="primary" @click="showDialog('add')">新增检项</el-button>
      </div>

      <el-table :data="filteredList" v-loading="loading" stripe>
        <el-table-column prop="product_type_name" label="产品类别" width="130" align="center" />
        <el-table-column prop="name" label="检项名称" min-width="180" />
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column label="类型" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_required === 1 ? 'danger' : 'default'" size="small">
              {{ row.is_required === 1 ? '必检' : '可检' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="sort_order" label="排序" width="80" align="center" />
        <el-table-column label="操作" width="180" align="center" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="showDialog('edit', row)">编辑</el-button>
            <el-button type="danger" link @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="600px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="产品类别" prop="product_type_id">
          <el-select v-model="form.product_type_id" placeholder="选择产品类别" style="width:100%">
            <el-option v-for="t in productTypes" :key="t.id" :label="t.name" :value="t.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="检项名称" prop="name">
          <el-input v-model="form.name" placeholder="如：一级头O型圈检查更换、屏幕检查" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="form.description" type="textarea" :rows="2" placeholder="简要描述检项内容" />
        </el-form-item>
        <el-form-item label="检项类型" prop="is_required">
          <el-radio-group v-model="form.is_required">
            <el-radio :label="1">必检项（保养/维修必须完成）</el-radio>
            <el-radio :label="0">可检项（根据需要勾选）</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="排序" prop="sort_order">
          <el-input-number v-model="form.sort_order" :min="0" />
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
const productTypes = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const submitLoading = ref(false)
const formRef = ref(null)
const isEdit = ref(false)
const filterType = ref('')

const form = reactive({
  id: '',
  product_type_id: '',
  name: '',
  description: '',
  is_required: 1,
  sort_order: 0
})

const rules = {
  product_type_id: [{ required: true, message: '请选择产品类别', trigger: 'change' }],
  name: [{ required: true, message: '请输入检项名称', trigger: 'blur' }]
}

const filteredList = computed(() => {
  if (!filterType.value) return list.value
  return list.value.filter(i => i.product_type_id === filterType.value)
})

const dialogTitle = computed(() => isEdit.value ? '编辑检项' : '新增检项')

const fetchList = async () => {
  loading.value = true
  try {
    const res = await request.get('/admin/service-items')
    list.value = Array.isArray(res) ? res : (res?.data || [])
  } catch (error) {
    console.error('Failed to fetch:', error)
  } finally {
    loading.value = false
  }
}

const fetchProductTypes = async () => {
  try {
    const res = await request.get('/admin/product-types')
    productTypes.value = Array.isArray(res) ? res : (res?.data || [])
  } catch (error) {
    console.error('Failed to fetch types:', error)
  }
}

const showDialog = (type, row = null) => {
  if (type === 'add') {
    isEdit.value = false
    Object.assign(form, { id: '', product_type_id: '', name: '', description: '', is_required: 1, sort_order: 0 })
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
    const payload = {
      product_type_id: form.product_type_id,
      name: form.name,
      description: form.description,
      is_required: form.is_required,
      sort_order: form.sort_order
    }
    if (isEdit.value) {
      await request.put(`/admin/service-items/${form.id}`, payload)
      ElMessage.success('更新成功')
    } else {
      await request.post('/admin/service-items', payload)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    fetchList()
  } catch (error) {
    ElMessage.error(error.message || '操作失败')
  } finally {
    submitLoading.value = false
  }
}

const handleDelete = async (row) => {
  await ElMessageBox.confirm(`确认删除「${row.name}」？`, '提示', { type: 'warning' })
  try {
    await request.delete(`/admin/service-items/${row.id}`)
    ElMessage.success('删除成功')
    fetchList()
  } catch (error) {
    ElMessage.error(error.message || '删除失败')
  }
}

onMounted(() => {
  fetchList()
  fetchProductTypes()
})
</script>

<style scoped>
.page-header { margin-bottom: 20px; }
.page-header h2 { margin: 0 0 4px; }
.tip { margin: 0; color: #999; font-size: 13px; }
.card-toolbar { margin-bottom: 16px; display: flex; align-items: center; }
</style>
