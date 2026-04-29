<template>
  <div class="models-page">
    <div class="page-header">
      <h2>型号管理</h2>
      <p class="tip">管理各品牌的具体型号。调节器需区分一级头/二级头/备用二级头；浮力补偿装置填"背飞"；电脑表填"电脑表"</p>
    </div>

    <div class="card">
      <div class="card-toolbar">
        <el-select v-model="filterType" placeholder="筛选类型" clearable style="width:160px;margin-right:8px" @change="onTypeChange">
          <el-option v-for="t in productTypes" :key="t.id" :label="t.name" :value="t.id" />
        </el-select>
        <el-select v-model="filterBrand" placeholder="筛选品牌" clearable style="width:160px;margin-right:12px">
          <el-option v-for="b in filteredBrands" :key="b.id" :label="b.name" :value="b.id" />
        </el-select>
        <el-button type="primary" @click="showDialog('add')">新增型号</el-button>
      </div>

      <el-table :data="filteredList" v-loading="loading" stripe>
        <el-table-column prop="brand_name" label="品牌" width="130" align="center" />
        <el-table-column prop="name" label="型号名称" min-width="150" />
        <el-table-column label="产品类型" width="180" align="center">
          <template #default="{ row }">
            <div v-if="row.categories && row.categories.length" class="category-tags">
              <el-tag v-for="cat in row.categories" :key="cat" size="small" type="info" style="margin: 2px">
                {{ cat }}
              </el-tag>
            </div>
            <span v-else-if="row.category" class="text-muted">{{ row.category }}</span>
            <span v-else class="text-muted">—</span>
          </template>
        </el-table-column>
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
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="500px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="品牌" prop="brand_id">
          <el-select v-model="form.brand_id" placeholder="先选产品类别，再选品牌" style="width:100%">
            <el-option v-for="b in filteredBrands" :key="b.id" :label="b.name" :value="b.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="型号名称" prop="name">
          <el-input v-model="form.name" placeholder="如：MK25 EVO、Perdix、Hydros Pro" />
        </el-form-item>
        <el-form-item label="产品类型" prop="category_ids">
          <p class="form-tip">勾选该型号所属的所有产品类型（可多选）</p>
          <el-checkbox-group v-model="form.category_ids">
            <el-checkbox v-for="cat in allCategories" :key="cat.id" :label="cat.id">
              {{ cat.name }}
            </el-checkbox>
          </el-checkbox-group>
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
const brands = ref([])
const productTypes = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const submitLoading = ref(false)
const formRef = ref(null)
const isEdit = ref(false)
const filterType = ref('')
const filterBrand = ref('')

const form = reactive({
  id: '',
  brand_id: '',
  name: '',
  category: '',
  category_ids: [],
  is_active: 1
})

const allCategories = ref([])

const rules = {
  brand_id: [{ required: true, message: '请选择品牌', trigger: 'change' }],
  name: [{ required: true, message: '请输入型号名称', trigger: 'blur' }]
}

const filteredBrands = computed(() => {
  if (!filterType.value) return brands.value
  return brands.value.filter(b => b.product_type_id === filterType.value)
})

const filteredList = computed(() => {
  let result = list.value
  if (filterBrand.value) result = result.filter(m => m.brand_id === filterBrand.value)
  if (filterType.value) result = result.filter(m => {
    const b = brands.value.find(bb => bb.id === m.brand_id)
    return b && b.product_type_id === filterType.value
  })
  return result
})

const dialogTitle = computed(() => isEdit.value ? '编辑型号' : '新增型号')

const fetchList = async () => {
  loading.value = true
  try {
    const res = await request.get('/admin/models')
    list.value = Array.isArray(res) ? res : (res?.data || [])
  } catch (error) {
    console.error('Failed to fetch:', error)
  } finally {
    loading.value = false
  }
}

const fetchBrands = async () => {
  try {
    const res = await request.get('/admin/brands')
    brands.value = Array.isArray(res) ? res : (res?.data || [])
  } catch (error) {
    console.error('Failed to fetch brands:', error)
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

const fetchCategories = async () => {
  try {
    const res = await request.get('/admin/categories')
    allCategories.value = Array.isArray(res) ? res : (res?.data || [])
  } catch (error) {
    console.error('Failed to fetch categories:', error)
  }
}

const onTypeChange = () => {
  filterBrand.value = ''
  form.brand_id = ''
}

const showDialog = (type, row = null) => {
  if (type === 'add') {
    isEdit.value = false
    Object.assign(form, { id: '', brand_id: '', name: '', category: '', category_ids: [], is_active: 1 })
  } else {
    isEdit.value = true
    Object.assign(form, {
      ...row,
      category_ids: row.category_ids || []
    })
  }
  dialogVisible.value = true
}

const handleSubmit = async () => {
  await formRef.value.validate()
  submitLoading.value = true
  try {
    const payload = {
      brand_id: form.brand_id,
      name: form.name,
      category_ids: form.category_ids,
      is_active: form.is_active
    }
    if (isEdit.value) {
      await request.put(`/admin/models/${form.id}`, payload)
      ElMessage.success('更新成功')
    } else {
      await request.post('/admin/models', payload)
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
    await request.delete(`/admin/models/${row.id}`)
    ElMessage.success('删除成功')
    fetchList()
  } catch (error) {
    ElMessage.error(error.message || '删除失败')
  }
}

onMounted(() => {
  fetchList()
  fetchBrands()
  fetchTypes()
  fetchCategories()
})
</script>

<style scoped>
.page-header { margin-bottom: 20px; }
.page-header h2 { margin: 0 0 4px; }
.tip { margin: 0; color: #999; font-size: 13px; }
.card-toolbar { margin-bottom: 16px; display: flex; align-items: center; }
.text-muted { color: #bbb; }
.form-tip { margin: 0 0 8px; color: #999; font-size: 12px; line-height: 1.4; }
</style>
