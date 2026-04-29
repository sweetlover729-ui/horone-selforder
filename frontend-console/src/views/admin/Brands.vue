<template>
  <div class="brands-page">
    <div class="page-header">
      <h2>品牌管理</h2>
      <p class="tip">管理所有品牌，每个品牌必须归属一个产品类别（调节器/浮力补偿装置/电脑表）</p>
    </div>

    <div class="card">
      <div class="card-toolbar">
        <el-select v-model="filterType" placeholder="筛选产品类别" clearable style="width:180px;margin-right:12px">
          <el-option v-for="t in productTypes" :key="t.id" :label="t.name" :value="t.id" />
        </el-select>
        <el-button type="primary" @click="showDialog('add')">新增品牌</el-button>
      </div>

      <el-table :data="filteredList" v-loading="loading" stripe>
        <el-table-column prop="name" label="品牌名称" min-width="120" />
        <el-table-column prop="product_type_name" label="归属类型" width="140" align="center" />
        <el-table-column label="型号数" width="90" align="center">
          <template #default="{ row }">
            <el-tag type="info" size="small">{{ row.model_count || 0 }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100" align="center">
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
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="500px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="品牌名称" prop="name">
          <el-input v-model="form.name" placeholder="如：Scubapro、Apeks、Suunto" />
        </el-form-item>
        <el-form-item label="归属类型" prop="product_type_id">
          <el-select v-model="form.product_type_id" placeholder="请选择归属的产品类别" style="width:100%">
            <el-option v-for="t in productTypes" :key="t.id" :label="t.name" :value="t.id" />
          </el-select>
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
  is_active: 1
})

const rules = {
  name: [{ required: true, message: '请输入品牌名称', trigger: 'blur' }],
  product_type_id: [{ required: true, message: '请选择归属类型', trigger: 'change' }]
}

const filteredList = computed(() => {
  if (!filterType.value) return list.value
  return list.value.filter(b => b.product_type_id === filterType.value)
})

const dialogTitle = computed(() => isEdit.value ? '编辑品牌' : '新增品牌')

const fetchList = async () => {
  loading.value = true
  try {
    const res = await request.get('/admin/brands')
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
    Object.assign(form, { id: '', name: '', product_type_id: '', is_active: 1 })
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
      await request.put(`/admin/brands/${form.id}`, {
        name: form.name,
        product_type_id: form.product_type_id,
        is_active: form.is_active
      })
      ElMessage.success('更新成功')
    } else {
      await request.post('/admin/brands', {
        name: form.name,
        product_type_id: form.product_type_id,
        is_active: form.is_active
      })
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
    await request.delete(`/admin/brands/${row.id}`)
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
