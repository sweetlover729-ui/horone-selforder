<template>
  <div class="service-types-page">
    <div class="page-header">
      <h2>服务类型管理</h2>
      <p class="tip">管理各产品类别的维修保养服务类型（保养/维修/清洗/换件等），按套装或故障类型命名</p>
    </div>

    <div class="card">
      <div class="card-toolbar">
        <el-select v-model="filterType" placeholder="筛选产品类别" clearable style="width:180px;margin-right:12px">
          <el-option v-for="t in productTypes" :key="t.id" :label="t.name" :value="t.id" />
        </el-select>
        <el-button type="primary" @click="showDialog('add')">新增服务类型</el-button>
      </div>

      <el-table :data="filteredList" v-loading="loading" stripe>
        <el-table-column prop="name" label="服务名称" min-width="180" />
        <el-table-column prop="product_type_name" label="归属类型" width="140" align="center" />
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column prop="base_price" label="价格" width="90" align="center">
          <template #default="{ row }">
            <span style="color:#e6a23c;font-weight:600">¥{{ row.base_price }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="sort_order" label="排序" width="80" align="center" />
        <el-table-column label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_active === 1 ? 'success' : 'info'" size="small">
              {{ row.is_active === 1 ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" align="center" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="showDialog('edit', row)">编辑</el-button>
            <el-button type="danger" link @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 弹窗 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="600px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="服务名称" prop="name">
          <el-input v-model="form.name" placeholder="如：标准套装保养、屏幕更换维修、传感器问题" />
        </el-form-item>
        <el-form-item label="归属类型" prop="product_type_id">
          <el-select v-model="form.product_type_id" placeholder="选择归属的产品类别" style="width:100%">
            <el-option v-for="t in productTypes" :key="t.id" :label="t.name" :value="t.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="form.description" type="textarea" :rows="2" placeholder="简要描述服务内容" />
        </el-form-item>
        <el-form-item label="价格" prop="base_price">
          <el-input-number v-model="form.base_price" :min="0" :precision="0" :step="10" />
          <span style="margin-left:8px;color:#999">元</span>
        </el-form-item>
        <el-form-item label="排序" prop="sort_order">
          <el-input-number v-model="form.sort_order" :min="0" :max="999" />
        </el-form-item>
        <el-form-item label="状态" prop="is_active">
          <el-radio-group v-model="form.is_active">
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
const productTypes = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const submitLoading = ref(false)
const formRef = ref(null)
const isEdit = ref(false)
const filterType = ref('')

const form = reactive({
  id: '',
  name: '',
  product_type_id: '',
  description: '',
  base_price: 0,
  sort_order: 0,
  is_active: 1
})

const rules = {
  name: [{ required: true, message: '请输入服务名称', trigger: 'blur' }],
  product_type_id: [{ required: true, message: '请选择归属类型', trigger: 'change' }],
  base_price: [{ required: true, message: '请输入价格', trigger: 'blur' }]
}

const filteredList = computed(() => {
  if (!filterType.value) return list.value
  return list.value.filter(s => s.product_type_id === filterType.value)
})

const dialogTitle = computed(() => isEdit.value ? '编辑服务类型' : '新增服务类型')

const fetchList = async () => {
  loading.value = true
  try {
    const res = await request.get('/admin/service-types')
    list.value = Array.isArray(res) ? res : (res?.data || [])
  } catch (error) {
    console.error('Failed to fetch:', error)
  } finally {
    loading.value = false
  }
}

const fetchTypes = async () => {
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
    Object.assign(form, { id: '', name: '', product_type_id: '', description: '', base_price: 0, sort_order: 0, is_active: 1 })
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
      name: form.name,
      product_type_id: form.product_type_id,
      description: form.description,
      base_price: form.base_price,
      sort_order: form.sort_order,
      is_active: form.is_active
    }
    if (isEdit.value) {
      await request.put(`/admin/service-types/${form.id}`, payload)
      ElMessage.success('更新成功')
    } else {
      await request.post('/admin/service-types', payload)
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
    await request.delete(`/admin/service-types/${row.id}`)
    ElMessage.success('删除成功')
    fetchList()
  } catch (error) {
    ElMessage.error(error.message || '删除失败')
  }
}

onMounted(() => {
  fetchList()
  fetchTypes()
})
</script>

<style scoped>
.page-header { margin-bottom: 20px; }
.page-header h2 { margin: 0 0 4px; }
.tip { margin: 0; color: #999; font-size: 13px; }
.card-toolbar { margin-bottom: 16px; display: flex; align-items: center; }
</style>
