import { ref, computed, provide, inject, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/utils/request'

export const DC_INJECT_KEY = Symbol('dataCenter')

export function useDataCenter() {
  // ============ 搜索 ============
  const searchQuery = ref('')
  const handleSearch = () => {
    if (!searchQuery.value) {
      selectedType.value = null; selectedCategory.value = null; selectedBrand.value = null; return
    }
    const query = searchQuery.value.toLowerCase()
    const foundModel = models.value.find(m => m.name.toLowerCase().includes(query))
    if (foundModel) {
      const brand = brands.value.find(b => b.id === foundModel.brand_id)
      if (brand) {
        const type = productTypes.value.find(t => t.id === brand.product_type_id)
        if (type) { selectedType.value = type; selectedBrand.value = brand; return }
      }
    }
    const foundBrand = brands.value.find(b => b.name.toLowerCase().includes(query))
    if (foundBrand) {
      const type = productTypes.value.find(t => t.id === foundBrand.product_type_id)
      if (type) { selectedType.value = type; selectedBrand.value = foundBrand; return }
    }
  }

  // ============ 数据状态 ============
  const productTypes = ref([])
  const categories = ref([])
  const brands = ref([])
  const models = ref([])
  const serviceTypes = ref([])
  const serviceItems = ref([])
  const prices = ref([])

  const selectedType = ref(null)
  const selectedCategory = ref(null)
  const selectedBrand = ref(null)

  const loading = ref(false)
  const submitLoading = ref(false)

  // ============ 计算属性 ============
  const typeCategories = computed(() => {
    if (!selectedType.value) return []
    const typeBrandIds = new Set(brands.value.filter(b => b.product_type_id == selectedType.value.id).map(b => b.id))
    const categoryIds = new Set()
    models.value.forEach(m => { if (typeBrandIds.has(m.brand_id) && m.category_ids?.length) m.category_ids.forEach(cid => categoryIds.add(cid)) })
    return categories.value.filter(c => categoryIds.has(c.id))
  })
  const typeBrands = computed(() => {
    if (!selectedType.value) return []
    let result = brands.value.filter(b => b.product_type_id == selectedType.value.id)
    if (selectedCategory.value) {
      const brandsWithCategory = new Set()
      models.value.forEach(m => { if (m.category_ids?.includes(selectedCategory.value.id)) brandsWithCategory.add(m.brand_id) })
      result = result.filter(b => brandsWithCategory.has(b.id))
    }
    return result
  })
  const brandModels = computed(() => {
    if (!selectedBrand.value) return []
    let result = models.value.filter(m => m.brand_id == selectedBrand.value.id)
    if (selectedCategory.value) result = result.filter(m => m.category_ids?.includes(selectedCategory.value.id))
    return result
  })
  const filteredServiceTypes = computed(() => {
    if (!selectedType.value) return serviceTypes.value
    let result = serviceTypes.value.filter(s => s.product_type_id == selectedType.value.id)
    if (selectedCategory.value) result = result.filter(s => !s.category_id || s.category_id == selectedCategory.value.id)
    return result
  })
  const filteredServiceItems = computed(() => {
    if (!selectedType.value) return serviceItems.value
    return serviceItems.value.filter(i => i.product_type_id == selectedType.value.id)
  })
  const filteredPrices = computed(() => {
    let result = prices.value
    if (selectedType.value) result = result.filter(p => p.product_type_id == selectedType.value.id)
    if (selectedCategory.value) {
      const brandIds = new Set(typeBrands.value.map(b => b.id))
      result = result.filter(p => !p.brand_id || brandIds.has(p.brand_id))
    }
    if (selectedBrand.value) result = result.filter(p => p.brand_id == selectedBrand.value.id)
    return result
  })
  const priceCategories = computed(() => {
    if (!priceForm.value.product_type_id) return []
    const ptBrands = brands.value.filter(b => b.product_type_id == priceForm.value.product_type_id)
    const brandIds = new Set(ptBrands.map(b => b.id))
    const ptModels = models.value.filter(m => brandIds.has(m.brand_id))
    const catIds = new Set()
    ptModels.forEach(m => (m.category_ids || []).forEach(cid => catIds.add(cid)))
    return categories.value.filter(c => catIds.has(c.id))
  })
  const priceBrands = computed(() => {
    if (!priceForm.value.product_type_id) return []
    return brands.value.filter(b => b.product_type_id == priceForm.value.product_type_id)
  })
  const priceModels = computed(() => {
    if (!priceForm.value.brand_id) return []
    return models.value.filter(m => m.brand_id == priceForm.value.brand_id)
  })
  const serviceTypeCategories = computed(() => {
    if (!serviceTypeForm.value.product_type_id) return []
    const ptBrands = brands.value.filter(b => b.product_type_id == serviceTypeForm.value.product_type_id)
    const brandIds = new Set(ptBrands.map(b => b.id))
    const ptModels = models.value.filter(m => brandIds.has(m.brand_id))
    const catIds = new Set()
    ptModels.forEach(m => (m.category_ids || []).forEach(cid => catIds.add(cid)))
    return categories.value.filter(c => catIds.has(c.id))
  })
  const priceServiceTypes = computed(() => {
    let result = serviceTypes.value
    if (priceForm.value.product_type_id) result = result.filter(s => s.product_type_id == priceForm.value.product_type_id)
    if (priceForm.value.category_id) result = result.filter(s => !s.category_id || s.category_id == priceForm.value.category_id)
    return result
  })
  const onServiceTypeProductChange = () => { serviceTypeForm.value.category_id = '' }
  const onPriceTypeChange = () => { priceForm.value.category_id = ''; priceForm.value.brand_id = ''; priceForm.value.model_id = '' }

  // ============ 选择方法 ============
  const selectType = (type) => { selectedType.value = type; selectedCategory.value = null; selectedBrand.value = null }
  const selectCategory = (cat) => {
    if (selectedCategory.value?.id === cat.id) { selectedCategory.value = null }
    else {
      selectedCategory.value = cat
      if (selectedBrand.value) {
        const hasModels = models.value.some(m => m.brand_id == selectedBrand.value.id && m.category_ids?.includes(cat.id))
        if (!hasModels) selectedBrand.value = null
      }
    }
  }
  const selectBrand = (brand) => { selectedBrand.value = selectedBrand.value?.id === brand.id ? null : brand }
  const getTypeStats = (typeId) => {
    const tBrands = brands.value.filter(b => b.product_type_id == typeId)
    const brandIds = tBrands.map(b => b.id)
    const tModels = models.value.filter(m => brandIds.includes(m.brand_id))
    return `${tBrands.length}品牌 ${tModels.length}型号`
  }
  const getCategoryModelCount = (categoryId) => {
    let ms = models.value
    if (selectedType.value) { const typeBrandIds = new Set(brands.value.filter(b => b.product_type_id == selectedType.value.id).map(b => b.id)); ms = ms.filter(m => typeBrandIds.has(m.brand_id)) }
    return ms.filter(m => m.category_ids?.includes(categoryId)).length
  }
  const getBrandModelCount = (brandId) => {
    let result = models.value.filter(m => m.brand_id == brandId)
    if (selectedCategory.value) result = result.filter(m => m.category_ids?.includes(selectedCategory.value.id))
    return result.length
  }

  // ============ 数据加载 ============
  const fetchAllData = async () => {
    loading.value = true
    try {
      const [typesRes, catsRes, brandsRes, modelsRes, servicesRes, itemsRes, pricesRes] = await Promise.all([
        request.get('/admin/product-types'), request.get('/admin/categories'),
        request.get('/admin/brands'), request.get('/admin/models'),
        request.get('/admin/service-types'), request.get('/admin/service-items'),
        request.get('/admin/prices')
      ])
      productTypes.value = Array.isArray(typesRes) ? typesRes : (typesRes?.data || [])
      categories.value = Array.isArray(catsRes) ? catsRes : (catsRes?.data || [])
      brands.value = Array.isArray(brandsRes) ? brandsRes : (brandsRes?.data || [])
      models.value = Array.isArray(modelsRes) ? modelsRes : (modelsRes?.data || [])
      serviceTypes.value = Array.isArray(servicesRes) ? servicesRes : (servicesRes?.data || [])
      serviceItems.value = Array.isArray(itemsRes) ? itemsRes : (itemsRes?.data || [])
      prices.value = Array.isArray(pricesRes) ? pricesRes : (pricesRes?.data || [])
    } catch (error) {
      console.error('Failed to fetch data:', error)
      ElMessage.error('数据加载失败')
    } finally { loading.value = false }
  }

  // ============ 弹窗 & CRUD ============
  const typeDialogVisible = ref(false)
  const isEditType = ref(false)
  const openTypeDialog = (row = null) => {
    isEditType.value = !!row
    typeForm.value = row ? { ...row, categories: row.categories ? JSON.parse(row.categories) : [] } : { id: '', name: '', categories: [], sort_order: 0 }
    typeDialogVisible.value = true
  }
  const typeForm = ref({ id: '', name: '', categories: [], sort_order: 0 })
  const submitType = async () => {
    submitLoading.value = true
    try {
      const payload = { ...typeForm.value, categories: JSON.stringify(typeForm.value.categories) }
      if (typeForm.value.id) await request.put(`/admin/product-types/${typeForm.value.id}`, payload)
      else await request.post('/admin/product-types', payload)
      ElMessage.success('保存成功'); fetchAllData()
    } catch (error) { ElMessage.error(error.message || '保存失败') } finally { submitLoading.value = false }
  }
  const deleteProductType = async (row) => {
    try { await ElMessageBox.confirm('确定删除？关联的品牌和型号将失去分类。', '提示', { type: 'warning' }); await request.delete(`/admin/product-types/${row.id}`); ElMessage.success('删除成功'); if (selectedType.value?.id === row.id) { selectedType.value = null; selectedCategory.value = null; selectedBrand.value = null }; fetchAllData() } catch (error) { if (error !== 'cancel') ElMessage.error(error.message || '删除失败') }
  }

  const categoryDialogVisible = ref(false)
  const isEditCategory = ref(false)
  const openCategoryDialog = (row = null) => {
    isEditCategory.value = !!row
    categoryForm.value = row ? { ...row } : { id: '', name: '', product_type_id: selectedType.value?.id || '', description: '', sort_order: 0 }
    categoryDialogVisible.value = true
  }
  const categoryForm = ref({ id: '', name: '', product_type_id: '', description: '', sort_order: 0 })
  const submitCategory = async () => {
    submitLoading.value = true
    try {
      if (categoryForm.value.id) await request.put(`/admin/categories/${categoryForm.value.id}`, categoryForm.value)
      else await request.post('/admin/categories', categoryForm.value)
      ElMessage.success('保存成功'); fetchAllData()
    } catch (error) { ElMessage.error(error.message || '保存失败') } finally { submitLoading.value = false }
  }
  const deleteCategory = async (row) => {
    try { await ElMessageBox.confirm('确定删除？', '提示', { type: 'warning' }); await request.delete(`/admin/categories/${row.id}`); ElMessage.success('删除成功'); if (selectedCategory.value?.id === row.id) selectedCategory.value = null; fetchAllData() } catch (error) { if (error !== 'cancel') ElMessage.error(error.message || '删除失败') }
  }

  const brandDialogVisible = ref(false)
  const isEditBrand = ref(false)
  const openBrandDialog = (row = null) => {
    isEditBrand.value = !!row
    brandForm.value = row ? { ...row } : { id: '', name: '', product_type_id: selectedType.value?.id || '', sort_order: 0 }
    brandDialogVisible.value = true
  }
  const brandForm = ref({ id: '', name: '', product_type_id: '', sort_order: 0 })
  const submitBrand = async () => {
    submitLoading.value = true
    try {
      if (brandForm.value.id) await request.put(`/admin/brands/${brandForm.value.id}`, brandForm.value)
      else await request.post('/admin/brands', brandForm.value)
      ElMessage.success('保存成功'); fetchAllData()
    } catch (error) { ElMessage.error(error.message || '保存失败') } finally { submitLoading.value = false }
  }
  const deleteBrand = async (row) => {
    try { await ElMessageBox.confirm('确定删除？', '提示', { type: 'warning' }); await request.delete(`/admin/brands/${row.id}`); ElMessage.success('删除成功'); if (selectedBrand.value?.id === row.id) selectedBrand.value = null; fetchAllData() } catch (error) { if (error !== 'cancel') ElMessage.error(error.message || '删除失败') }
  }

  const modelDialogVisible = ref(false)
  const isEditModel = ref(false)
  const openModelDialog = (row = null, brandId = null) => {
    isEditModel.value = !!row
    modelForm.value = row ? { ...row, category_ids: row.category_ids || [] } : { id: '', name: '', brand_id: brandId || selectedBrand.value?.id || '', category_ids: [], is_active: 1 }
    modelDialogVisible.value = true
  }
  const modelForm = ref({ id: '', name: '', brand_id: '', category_ids: [], is_active: 1 })
  const submitModel = async () => {
    submitLoading.value = true
    try {
      if (modelForm.value.id) await request.put(`/admin/models/${modelForm.value.id}`, modelForm.value)
      else await request.post('/admin/models', modelForm.value)
      ElMessage.success('保存成功'); fetchAllData()
    } catch (error) { ElMessage.error(error.message || '保存失败') } finally { submitLoading.value = false }
  }
  const deleteModel = async (row) => {
    try { await ElMessageBox.confirm('确定删除？', '提示', { type: 'warning' }); await request.delete(`/admin/models/${row.id}`); ElMessage.success('删除成功'); fetchAllData() } catch (error) { if (error !== 'cancel') ElMessage.error(error.message || '删除失败') }
  }

  const serviceTypeDialogVisible = ref(false)
  const isEditServiceType = ref(false)
  const openServiceTypeDialog = (row = null) => {
    isEditServiceType.value = !!row
    serviceTypeForm.value = row ? { ...row } : { id: '', name: '', product_type_id: selectedType.value?.id || '', category_id: selectedCategory.value?.id || '', base_price: 0, description: '', is_active: 1 }
    serviceTypeDialogVisible.value = true
  }
  const serviceTypeForm = ref({ id: '', name: '', product_type_id: '', category_id: '', base_price: 0, description: '', is_active: 1 })
  const submitServiceType = async () => {
    submitLoading.value = true
    try {
      if (serviceTypeForm.value.id) await request.put(`/admin/service-types/${serviceTypeForm.value.id}`, serviceTypeForm.value)
      else await request.post('/admin/service-types', serviceTypeForm.value)
      ElMessage.success('保存成功'); fetchAllData()
    } catch (error) { ElMessage.error(error.message || '保存失败') } finally { submitLoading.value = false }
  }
  const deleteServiceType = async (row) => {
    try { await ElMessageBox.confirm('确定删除？', '提示', { type: 'warning' }); await request.delete(`/admin/service-types/${row.id}`); ElMessage.success('删除成功'); fetchAllData() } catch (error) { if (error !== 'cancel') ElMessage.error(error.message || '删除失败') }
  }

  const serviceItemDialogVisible = ref(false)
  const isEditServiceItem = ref(false)
  const openServiceItemDialog = (row = null) => {
    isEditServiceItem.value = !!row
    serviceItemForm.value = row ? { ...row } : { id: '', name: '', product_type_id: selectedType.value?.id || '', is_required: 0 }
    serviceItemDialogVisible.value = true
  }
  const serviceItemForm = ref({ id: '', name: '', product_type_id: '', is_required: 0 })
  const submitServiceItem = async () => {
    submitLoading.value = true
    try {
      if (serviceItemForm.value.id) await request.put(`/admin/service-items/${serviceItemForm.value.id}`, serviceItemForm.value)
      else await request.post('/admin/service-items', serviceItemForm.value)
      ElMessage.success('保存成功'); fetchAllData()
    } catch (error) { ElMessage.error(error.message || '保存失败') } finally { submitLoading.value = false }
  }
  const deleteServiceItem = async (row) => {
    try { await ElMessageBox.confirm('确定删除？', '提示', { type: 'warning' }); await request.delete(`/admin/service-items/${row.id}`); ElMessage.success('删除成功'); fetchAllData() } catch (error) { if (error !== 'cancel') ElMessage.error(error.message || '删除失败') }
  }

  const priceDialogVisible = ref(false)
  const isEditPrice = ref(false)
  const openPriceDialog = (row = null, defaults = null) => {
    isEditPrice.value = !!row
    if (row) priceForm.value = { ...row }
    else if (defaults) priceForm.value = { id: '', service_type_id: '', product_type_id: selectedType.value?.id || '', category_id: selectedCategory.value?.id || '', brand_id: selectedBrand.value?.id || '', model_id: '', price: 0, ...defaults }
    else priceForm.value = { id: '', service_type_id: '', product_type_id: selectedType.value?.id || '', category_id: selectedCategory.value?.id || '', brand_id: selectedBrand.value?.id || '', model_id: '', price: 0 }
    priceDialogVisible.value = true
  }
  const priceForm = ref({ id: '', service_type_id: '', product_type_id: '', category_id: '', brand_id: '', model_id: '', price: 0 })
  const submitPrice = async () => {
    submitLoading.value = true
    try {
      const payload = { ...priceForm.value }
      if (payload.category_id) { const cat = categories.value.find(c => c.id === payload.category_id); payload.category = cat ? cat.name : '' }
      else payload.category = ''
      delete payload.category_id
      if (payload.id) await request.put(`/admin/prices/${payload.id}`, payload)
      else await request.post('/admin/prices', payload)
      ElMessage.success('保存成功'); fetchAllData()
    } catch (error) { ElMessage.error(error.message || '保存失败') } finally { submitLoading.value = false }
  }
  const deletePrice = async (row) => {
    try { await ElMessageBox.confirm('确定删除？', '提示', { type: 'warning' }); await request.delete(`/admin/prices/${row.id}`); ElMessage.success('删除成功'); fetchAllData() } catch (error) { if (error !== 'cancel') ElMessage.error(error.message || '删除失败') }
  }

  // ============ 辅助函数 ============
  const getCategoryName = (id) => { if (!id) return '-'; const c = categories.value.find(x => x.id === id); return c ? c.name : '-' }
  const getTypeName = (id) => { if (!id) return '-'; const t = productTypes.value.find(x => x.id === id); return t ? t.name : '-' }
  const getServiceName = (id) => { if (!id) return '-'; const s = serviceTypes.value.find(x => x.id === id); return s ? s.name : '-' }
  const getBrandName = (id) => { if (!id) return '-'; const b = brands.value.find(x => x.id === id); return b ? b.name : '-' }
  const getModelName = (id) => { if (!id) return '-'; const m = models.value.find(x => x.id === id); return m ? m.name : '-' }

  // ============ 复合导出 ============
  const ctx = {
    searchQuery, handleSearch,
    productTypes, categories, brands, models, serviceTypes, serviceItems, prices,
    selectedType, selectedCategory, selectedBrand,
    loading, submitLoading,
    typeCategories, typeBrands, brandModels, filteredServiceTypes, filteredServiceItems, filteredPrices,
    priceCategories, priceBrands, priceModels, serviceTypeCategories, priceServiceTypes,
    onServiceTypeProductChange, onPriceTypeChange,
    selectType, selectCategory, selectBrand, getTypeStats, getCategoryModelCount, getBrandModelCount,
    fetchAllData,
    typeDialogVisible, isEditType, openTypeDialog, typeForm, submitType, deleteProductType,
    categoryDialogVisible, isEditCategory, openCategoryDialog, categoryForm, submitCategory, deleteCategory,
    brandDialogVisible, isEditBrand, openBrandDialog, brandForm, submitBrand, deleteBrand,
    modelDialogVisible, isEditModel, openModelDialog, modelForm, submitModel, deleteModel,
    serviceTypeDialogVisible, isEditServiceType, openServiceTypeDialog, serviceTypeForm, submitServiceType, deleteServiceType,
    serviceItemDialogVisible, isEditServiceItem, openServiceItemDialog, serviceItemForm, submitServiceItem, deleteServiceItem,
    priceDialogVisible, isEditPrice, openPriceDialog, priceForm, submitPrice, deletePrice,
    getCategoryName, getTypeName, getServiceName, getBrandName, getModelName
  }
  provide(DC_INJECT_KEY, ctx)
  onMounted(() => fetchAllData())
  return ctx
}

export function useDC() {
  return inject(DC_INJECT_KEY)
}
