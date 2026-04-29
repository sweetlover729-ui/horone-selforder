<template>
  <div class="product-types">
    <div class="page-header">
      <h2>产品大类管理</h2>
      <p class="tip">管理设备大类（调节器/浮力补偿装置/电脑表），以及各类型的套装分类</p>
    </div>

    <div class="card">
      <div class="card-toolbar">
        <el-button type="primary" @click="showDialog('add')">新增产品大类</el-button>
      </div>

      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column prop="name" label="名称" width="120" align="center" />
        <el-table-column prop="categories" label="套装分类" min-width="200">
          <template #default="{ row }">
            <template v-if="row.categories">
              <div class="category-tags">
                <el-tag v-for="cat in JSON.parse(row.categories)" :key="cat" size="small">
                  {{ cat }}
                </el-tag>
              </div>
            </template>
            <span v-else class="text-muted">— 无</span>
          </template>
        </el-table-column>
        <el-table-column prop="sort_order" label="排序" width="80" align="center" />
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
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="600px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="如：调节器、浮力补偿装置、电脑表" />
        </el-form-item>
        <el-form-item label="套装分类" prop="categories">
          <p class="form-tip">输入后回车添加，调节器必填套装类型（标准套装/侧挂套装/背挂双瓶套装/减压适氧套装）</p>
          <el-select
            v-model="form.categoriesInput"
            multiple
            filterable
            allow-create
            default-first-option
            placeholder="输入套装名称后回车（如：标准套装）"
            style="width:100%"
          />
        </el-form-item>
        <el-form-item label="排序" prop="sort_order">
          <el-input-number v-model="form.sort_order" :min="0" :max="9999" />
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
const loading = ref(false)
const dialogVisible = ref(false)
const submitLoading = ref(false)
const formRef = ref(null)
const isEdit = ref(false)

const form = reactive({
  id: '',
  name: '',
  categoriesInput: [],
  sort_order: 0,
  is_active: 1
})

const rules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }]
}

const dialogTitle = computed(() => isEdit.value ? '编辑产品大类' : '新增产品大类')

const fetchList = async () => {
  loading.value = true
  try {
    const res = await request.get('/admin/product-types')
    list.value = Array.isArray(res) ? res : (res?.data || [])
  } catch (error) {
    console.error('Failed to fetch:', error)
  } finally {
    loading.value = false
  }
}

const showDialog = (type, row = null) => {
  if (type === 'add') {
    isEdit.value = false
    Object.assign(form, { id: '', name: '', categoriesInput: [], sort_order: 0, is_active: 1 })
  } else {
    isEdit.value = true
    const cats = row.categories ? JSON.parse(row.categories) : []
    Object.assign(form, { ...row, categoriesInput: cats })
  }
  dialogVisible.value = true
}

const handleSubmit = async () => {
  await formRef.value.validate()
  submitLoading.value = true
  try {
    const payload = {
      name: form.name,
      categories: JSON.stringify(form.categoriesInput),
      sort_order: form.sort_order,
      is_active: form.is_active
    }
    if (isEdit.value) {
      await request.put(`/admin/product-types/${form.id}`, payload)
      ElMessage.success('更新成功')
    } else {
      await request.post('/admin/product-types', payload)
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
    await request.delete(`/admin/product-types/${row.id}`)
    ElMessage.success('删除成功')
    fetchList()
  } catch (error) {
    ElMessage.error(error.message || '删除失败')
  }
}

onMounted(() => {
  fetchList()
})
</script>

<style scoped>
.page-header { margin-bottom: 20px; }
.page-header h2 { margin: 0 0 4px; }
.tip { margin: 0; color: #999; font-size: 13px; }
.card-toolbar { margin-bottom: 16px; }
.text-muted { color: #bbb; }
.form-tip { margin: 0 0 8px; color: #999; font-size: 12px; line-height: 1.4; }
.category-tags { display: flex; flex-wrap: wrap; gap: 4px; justify-content: center; }
</style>
