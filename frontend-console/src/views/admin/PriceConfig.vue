<template>
  <div class="price-config">
    <div class="page-header">
      <h2>价格配置</h2>
    </div>

    <div class="card">
      <div class="card-toolbar">
        <el-select v-model="filter.productTypeId" placeholder="产品类别" clearable @change="fetchList" style="width: 160px;">
          <el-option v-for="pt in productTypes" :key="pt.id" :label="pt.name" :value="pt.id" />
        </el-select>
        <el-select v-model="filter.brandId" placeholder="品牌" clearable @change="fetchList" style="width: 160px;">
          <el-option v-for="b in filteredFilterBrands" :key="b.id" :label="b.name" :value="b.id" />
        </el-select>
        <el-button type="primary" @click="showDialog('add')">新增价格</el-button>
      </div>

      <el-table :data="list" v-loading="loading">
        <el-table-column prop="product_type_name" label="产品类别" width="120" />
        <el-table-column prop="brand_name" label="品牌" width="150" />
        <el-table-column prop="category" label="类别" width="120">
          <template #default="{ row }">{{ row.category || '-' }}</template>
        </el-table-column>
        <el-table-column prop="model_name" label="型号" width="150">
          <template #default="{ row }">{{ row.model_name || '-' }}</template>
        </el-table-column>
        <el-table-column prop="service_type_name" label="服务类型" width="120" />
        <el-table-column prop="price" label="价格" width="100">
          <template #default="{ row }">
            <span class="price-text">¥{{ row.price }}</span>
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

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="550px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="产品类别" prop="productTypeId">
          <el-select v-model="form.productTypeId" placeholder="请选择" style="width: 100%;" @change="onProductTypeChange">
            <el-option v-for="pt in productTypes" :key="pt.id" :label="pt.name" :value="pt.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="品牌" prop="brandId">
          <el-select v-model="form.brandId" placeholder="请选择" style="width: 100%;" @change="onBrandChange">
            <el-option v-for="b in dialogBrands" :key="b.id" :label="b.name" :value="b.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="类别">
          <el-select v-model="form.category" placeholder="请选择" style="width: 100%;">
            <el-option v-for="c in categories" :key="c" :label="c" :value="c" />
          </el-select>
        </el-form-item>
        <el-form-item label="型号">
          <el-select v-model="form.modelId" placeholder="可选（不选则为品牌+类别级别）" style="width: 100%;" clearable>
            <el-option v-for="m in filteredModels" :key="m.id" :label="m.name" :value="m.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="服务类型" prop="serviceTypeId">
          <el-select v-model="form.serviceTypeId" placeholder="请选择" style="width: 100%;">
            <el-option v-for="st in serviceTypes" :key="st.id" :label="st.name" :value="st.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="价格" prop="price">
          <el-input-number v-model="form.price" :min="0" :precision="2" :step="10" />
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
const brands = ref([])
const models = ref([])
const serviceTypes = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const submitLoading = ref(false)
const formRef = ref(null)
const isEdit = ref(false)

const filter = reactive({
  productTypeId: '',
  brandId: ''
})

const form = reactive({
  id: '',
  productTypeId: '',
  brandId: '',
  category: '',
  modelId: '',
  serviceTypeId: '',
  price: 0
})

const rules = {
  productTypeId: [{ required: true, message: '请选择产品类别', trigger: 'change' }],
  brandId: [{ required: true, message: '请选择品牌', trigger: 'change' }],
  serviceTypeId: [{ required: true, message: '请选择服务类型', trigger: 'change' }],
  price: [{ required: true, message: '请输入价格', trigger: 'blur' }]
}

const dialogTitle = computed(() => isEdit.value ? '编辑价格' : '新增价格')

// 筛选区的品牌过滤
const filteredFilterBrands = computed(() => {
  if (!filter.productTypeId) return brands.value
  return brands.value.filter(b => b.product_type_id === filter.productTypeId)
})

// 弹窗的品牌过滤
const dialogBrands = computed(() => {
  if (!form.productTypeId) return brands.value
  return brands.value.filter(b => b.product_type_id === form.productTypeId)
})

// 类别选项
const categories = computed(() => {
  if (!form.productTypeId) return []
  const pt = productTypes.value.find(p => p.id === form.productTypeId)
  if (!pt || !pt.categories) return []
  try {
    return JSON.parse(pt.categories)
  } catch {
    return []
  }
})

// 型号过滤
const filteredModels = computed(() => {
  if (!form.brandId) return []
  return models.value.filter(m => m.brand_id === form.brandId && m.category === form.category)
})

const onProductTypeChange = () => {
  form.brandId = ''
  form.category = ''
  form.modelId = ''
}

const onBrandChange = () => {
  form.modelId = ''
}

const showDialog = (type, row = null) => {
  if (type === 'add') {
    isEdit.value = false
    Object.assign(form, {
      id: '',
      productTypeId: filter.productTypeId,
      brandId: filter.brandId,
      category: '',
      modelId: '',
      serviceTypeId: '',
      price: 0
    })
  } else {
    isEdit.value = true
    Object.assign(form, {
      id: row.id,
      productTypeId: row.productTypeId || '',
      brandId: row.brandId || '',
      category: row.category || '',
      modelId: row.modelId || '',
      serviceTypeId: row.serviceTypeId || '',
      price: row.price || 0
    })
  }
  dialogVisible.value = true
}

const handleSubmit = async () => {
  await formRef.value.validate()
  submitLoading.value = true
  try {
    const submitData = {
      product_type_id: form.productTypeId,
      brand_id: form.brandId,
      category: form.category,
      service_type_id: form.serviceTypeId,
      price: form.price
    }
    if (form.modelId) submitData.model_id = form.modelId
    
    if (isEdit.value) {
      await request.put(`/admin/prices/${form.id}`, submitData)
      ElMessage.success('更新成功')
    } else {
      await request.post('/admin/prices', submitData)
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
  await ElMessageBox.confirm('确认删除此价格配置?', '提示', { type: 'warning' })
  try {
    await request.delete(`/admin/prices/${row.id}`)
    ElMessage.success('删除成功')
    fetchList()
  } catch (error) {
    console.error('Delete failed:', error)
  }
}

const fetchList = async () => {
  loading.value = true
  try {
    const params = {}
    if (filter.productTypeId) params.productTypeId = filter.productTypeId
    if (filter.brandId) params.brandId = filter.brandId
    const data = await request.get('/admin/prices', { params })
    list.value = Array.isArray(data) ? data : (data?.data || data?.list || [])
  } catch (error) {
    console.error('Failed to fetch:', error)
  } finally {
    loading.value = false
  }
}

const fetchProductTypes = async () => {
  try {
    const data = await request.get('/admin/product-types')
    productTypes.value = Array.isArray(data) ? data : (data?.data || data?.list || [])
  } catch (error) {
    console.error('Failed to fetch product types:', error)
  }
}

const fetchBrands = async () => {
  try {
    const data = await request.get('/admin/brands')
    brands.value = Array.isArray(data) ? data : (data?.data || data?.list || [])
  } catch (error) {
    console.error('Failed to fetch brands:', error)
  }
}

const fetchModels = async () => {
  try {
    const data = await request.get('/admin/models')
    models.value = Array.isArray(data) ? data : (data?.data || data?.list || [])
  } catch (error) {
    console.error('Failed to fetch models:', error)
  }
}

const fetchServiceTypes = async () => {
  try {
    const data = await request.get('/admin/service-types')
    serviceTypes.value = Array.isArray(data) ? data : (data?.data || data?.list || [])
  } catch (error) {
    console.error('Failed to fetch service types:', error)
  }
}

onMounted(() => {
  fetchList()
  fetchProductTypes()
  fetchBrands()
  fetchModels()
  fetchServiceTypes()
})
</script>

<style scoped>
.card-toolbar {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 16px;
}
.price-text {
  color: #f56c6c;
  font-weight: bold;
}
</style>
