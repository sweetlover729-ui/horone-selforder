<template>
  <div class="inventory-tab">
    <!-- 操作栏 -->
    <div class="inv-toolbar">
      <div class="inv-left">
        <el-input v-model="searchText" placeholder="搜索配件名称/编号" clearable style="width:260px" @keyup.enter="fetchParts">
          <template #prefix><span style="color:#999">🔍</span></template>
        </el-input>
        <el-select v-model="filterCategory" clearable placeholder="全部类别" style="width:160px;margin-left:8px" @change="fetchParts">
          <el-option v-for="c in categories" :key="c" :label="c" :value="c" />
        </el-select>
        <el-button v-if="lowStockOnly" type="warning" size="small" plain style="margin-left:8px" @click="lowStockOnly=false;fetchParts()">
          低库存预警 {{ lowStockCount > 0 ? `(${lowStockCount})` : '' }}
        </el-button>
        <el-button v-else size="small" style="margin-left:8px" @click="lowStockOnly=true;fetchParts()">
          低库存预警 {{ lowStockCount > 0 ? `(${lowStockCount})` : '' }}
        </el-button>
      </div>
      <el-button type="primary" @click="openAdd">+ 新增配件</el-button>
    </div>

    <!-- 列表 -->
    <div class="inv-table-wrap">
      <el-table :data="parts" stripe highlight-current-row @row-click="selectPart" style="width:100%" max-height="calc(100vh - 320px)">
        <el-table-column prop="part_code" label="编号" width="130" />
        <el-table-column prop="name" label="名称" min-width="160">
          <template #default="{row}"><span style="font-weight:500">{{ row.name }}</span></template>
        </el-table-column>
        <el-table-column prop="category" label="类别" width="110" />
        <el-table-column label="库存" width="150" align="center">
          <template #default="{row}">
            <span :style="{color: row.stock <= row.min_stock ? '#f56c6c' : (row.stock <= row.min_stock*2 ? '#e6a23c' : '#67c23a')}">
              <strong>{{ row.stock }}</strong>
            </span>
            / <span style="font-size:12px;color:#999">最低{{ row.min_stock }}</span>
            <el-tag v-if="row.stock <= row.min_stock" type="danger" size="small" effect="dark" style="margin-left:6px">缺货</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="cost_price" label="成本价" width="100" align="right">
          <template #default="{row}">¥{{ row.cost_price || 0 }}</template>
        </el-table-column>
        <el-table-column prop="selling_price" label="售价" width="100" align="right">
          <template #default="{row}">¥{{ row.selling_price || 0 }}</template>
        </el-table-column>
        <el-table-column prop="unit" label="单位" width="60" align="center" />
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{row}">
            <el-button size="small" @click.stop="openStockIn(row)">入库</el-button>
            <el-button size="small" type="warning" @click.stop="openStockOut(row)" :disabled="row.stock <= 0">出库</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 选中行的库存日志面板 -->
    <div v-if="selectedPart" class="inv-detail">
      <div class="detail-header">
        <span>📋 {{ selectedPart.name }} — 库存日志</span>
        <el-button size="small" text @click="selectedPart=null">✕</el-button>
      </div>
      <div class="detail-list">
        <div v-for="log in stockLogs" :key="log.id" class="log-item">
          <span :class="['log-badge', log.change_type]">{{ log.change_type === 'in' ? '入库' : log.change_type === 'out' ? '出库' : '调整' }}</span>
          <span class="log-qty">{{ log.change_qty > 0 ? '+' : '' }}{{ log.change_qty }}</span>
          <span class="log-ts">{{ formatTime(log.created_at) }}</span>
          <span class="log-op">{{ log.operator || '' }}</span>
          <span class="log-note">{{ log.notes || '' }}</span>
        </div>
        <div v-if="!stockLogs.length" class="log-empty">暂无记录</div>
      </div>
    </div>

    <!-- 新增/编辑弹窗 -->
    <el-dialog v-model="formVisible" :title="isEdit ? '编辑配件' : '新增配件'" width="520px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="编号"><el-input v-model="form.part_code" placeholder="可选" /></el-form-item>
        <el-form-item label="类别"><el-input v-model="form.category" placeholder="如：密封件、滤芯" /></el-form-item>
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="初始库存"><el-input-number v-model="form.stock" :min="0" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="最低库存"><el-input-number v-model="form.min_stock" :min="1" /></el-form-item></el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="成本价"><el-input-number v-model="form.cost_price" :min="0" :precision="2" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="售价"><el-input-number v-model="form.selling_price" :min="0" :precision="2" /></el-form-item></el-col>
        </el-row>
        <el-form-item label="单位"><el-input v-model="form.unit" /></el-form-item>
        <el-form-item label="描述"><el-input v-model="form.description" type="textarea" rows="2" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="form.notes" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="formVisible=false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitting">{{ isEdit ? '保存' : '创建' }}</el-button>
      </template>
    </el-dialog>

    <!-- 入库弹窗 -->
    <el-dialog v-model="stockInVisible" title="入库" width="380px">
      <div class="stock-op-info"><strong>{{ stockOpPart?.name }}</strong> | 当前库存：{{ stockOpPart?.stock }}</div>
      <el-form :model="stockInForm" label-width="80px" style="margin-top:12px">
        <el-form-item label="入库数量"><el-input-number v-model="stockInForm.quantity" :min="1" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="stockInForm.notes" placeholder="采购来源等" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="stockInVisible=false">取消</el-button>
        <el-button type="primary" @click="doStockIn" :loading="submitting">确认入库</el-button>
      </template>
    </el-dialog>

    <!-- 出库弹窗 -->
    <el-dialog v-model="stockOutVisible" title="出库" width="380px">
      <div class="stock-op-info"><strong>{{ stockOpPart?.name }}</strong> | 当前库存：{{ stockOpPart?.stock }}</div>
      <el-form :model="stockOutForm" label-width="80px" style="margin-top:12px">
        <el-form-item label="出库数量"><el-input-number v-model="stockOutForm.quantity" :min="1" :max="stockOpPart?.stock||1" /></el-form-item>
        <el-form-item label="关联订单"><el-input v-model="stockOutForm.order_id" placeholder="可选，订单ID" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="stockOutForm.notes" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="stockOutVisible=false">取消</el-button>
        <el-button type="primary" @click="doStockOut" :loading="submitting">确认出库</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'

const parts = ref([])
const categories = ref([])
const lowStockCount = ref(0)
const lowStockOnly = ref(false)
const searchText = ref('')
const filterCategory = ref('')
const selectedPart = ref(null)
const stockLogs = ref([])
const submitting = ref(false)

// Part form
const formVisible = ref(false)
const isEdit = ref(false)
const form = ref({ name:'', part_code:'', category:'', stock:0, min_stock:5, cost_price:0, selling_price:0, unit:'个', description:'', notes:'' })

// Stock dialogs
const stockInVisible = ref(false)
const stockOutVisible = ref(false)
const stockOpPart = ref(null)
const stockInForm = ref({ quantity:1, notes:'' })
const stockOutForm = ref({ quantity:1, order_id:'', notes:'' })

const formatTime = (ts) => ts ? new Date(ts).toLocaleString('zh-CN') : ''

const fetchParts = async () => {
  const params = {}
  if (searchText.value) params.search = searchText.value
  if (filterCategory.value) params.category = filterCategory.value
  if (lowStockOnly.value) params.low_stock = '1'
  try {
    const res = await request.get('/admin/parts', { params })
    parts.value = res?.data || []
    categories.value = res?.categories || []
  } catch { ElMessage.error('加载配件列表失败') }
}

const fetchLowStockCount = async () => {
  try {
    const res = await request.get('/admin/parts/low-stock')
    lowStockCount.value = res?.total || 0
  } catch { /* silent */ }
}

const openAdd = () => {
  isEdit.value = false; form.value = { name:'', part_code:'', category:'', stock:0, min_stock:5, cost_price:0, selling_price:0, unit:'个', description:'', notes:'' }
  formVisible.value = true
}

const selectPart = async (row) => {
  selectedPart.value = row
  try {
    const res = await request.get(`/admin/parts/${row.id}/stock-log`)
    stockLogs.value = res?.data || []
  } catch { stockLogs.value = [] }
}

const submitForm = async () => {
  if (!form.value.name.trim()) { ElMessage.warning('请输入名称'); return }
  submitting.value = true
  try {
    const payload = { ...form.value, brand_id: null, model_id: null }
    if (isEdit.value) {
      await request.put(`/admin/parts/${payload.id}`, payload)
      ElMessage.success('已更新')
    } else {
      await request.post('/admin/parts', payload)
      ElMessage.success('已创建')
    }
    formVisible.value = false; await fetchParts()
  } catch { ElMessage.error('操作失败') }
  finally { submitting.value = false }
}

const openStockIn = (row) => { stockOpPart.value = row; stockInForm.value = { quantity:1, notes:'' }; stockInVisible.value = true }
const openStockOut = (row) => { stockOpPart.value = row; stockOutForm.value = { quantity:1, order_id:'', notes:'' }; stockOutVisible.value = true }

const doStockIn = async () => {
  submitting.value = true
  try { await request.post(`/admin/parts/${stockOpPart.value.id}/stock-in`, stockInForm.value); stockInVisible.value = false; ElMessage.success('入库成功'); await fetchParts() }
  catch(e) { ElMessage.error(e?.response?.data?.message || '操作失败') }
  finally { submitting.value = false }
}

const doStockOut = async () => {
  submitting.value = true
  const payload = { ...stockOutForm.value }
  if (payload.order_id) payload.order_id = parseInt(payload.order_id) || null
  try { await request.post(`/admin/parts/${stockOpPart.value.id}/stock-out`, payload); stockOutVisible.value = false; ElMessage.success('出库成功'); await fetchParts() }
  catch(e) { ElMessage.error(e?.response?.data?.message || '操作失败') }
  finally { submitting.value = false }
}

onMounted(() => { fetchParts(); fetchLowStockCount() })
</script>

<style scoped>
.inv-toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.inv-left { display: flex; align-items: center; }
.inv-table-wrap { background: #fff; border-radius: 8px; border: 1px solid #e4e7ed; }
.inv-detail { margin-top: 12px; background: #fff; border-radius: 8px; border: 1px solid #e4e7ed; }
.detail-header { padding: 14px 16px; border-bottom: 1px solid #e4e7ed; display: flex; justify-content: space-between; align-items: center; font-weight: 600; }
.detail-list { max-height: 200px; overflow-y: auto; padding: 8px; }
.log-item { display: flex; align-items: center; gap: 10px; padding: 8px; border-radius: 6px; font-size: 13px; }
.log-item:nth-child(odd) { background: #fafafa; }
.log-badge { padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: 600; min-width: 42px; text-align: center; }
.log-badge.in { background: #e6f7e6; color: #389e0d; }
.log-badge.out { background: #fff2e8; color: #d46b08; }
.log-badge.adjust { background: #e6f0ff; color: #1677ff; }
.log-qty { font-weight: 600; min-width: 40px; text-align: right; }
.log-ts { color: #999; font-size: 12px; }
.log-op { color: #666; }
.log-note { color: #999; flex: 1; }
.log-empty { text-align: center; color: #ccc; padding: 20px; }
.stock-op-info { padding: 8px 12px; background: #f5f7fa; border-radius: 6px; color: #666; }
</style>
