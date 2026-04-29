<template>
  <div class="customers-page">
    <div class="page-header">
      <h2>客户管理</h2>
    </div>

    <div class="card">
      <div class="card-toolbar">
        <el-input v-model="searchText" placeholder="搜索姓名/手机号/昵称" clearable style="width: 240px" @clear="loadList" @keyup.enter="loadList">
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
      </div>

      <el-table :data="list" v-loading="loading" @row-click="showDetail" style="cursor: pointer">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="name" label="姓名" width="120">
          <template #default="{ row }">{{ row.name || '-' }}</template>
        </el-table-column>
        <el-table-column prop="phone" label="手机号" width="140">
          <template #default="{ row }">{{ row.phone || '-' }}</template>
        </el-table-column>
        <el-table-column prop="nickname" label="昵称" width="120">
          <template #default="{ row }">{{ row.nickname || '-' }}</template>
        </el-table-column>
        <el-table-column prop="order_count" label="订单数" width="90" />
        <el-table-column label="经销商" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.is_dealer" type="success" size="small">经销商</el-tag>
            <span v-else class="text-gray">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="address" label="地址" min-width="200" show-overflow-tooltip />
        <el-table-column prop="created_at" label="注册时间" width="160">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
      </el-table>

      <div class="pagination-bar" v-if="total > perPage">
        <el-pagination
          v-model:current-page="page"
          :page-size="perPage"
          :total="total"
          layout="total, prev, pager, next"
          @current-change="loadList"
        />
      </div>
    </div>

    <!-- 详情抽屉 -->
    <el-drawer v-model="drawerVisible" :title="'客户详情 - ' + (detail.name || detail.nickname || '未命名')" size="480px">
      <div class="detail-section">
        <h4>基本信息</h4>
        <el-descriptions :column="1" border size="small">
          <el-descriptions-item label="ID">{{ detail.id }}</el-descriptions-item>
          <el-descriptions-item label="姓名">{{ detail.name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="手机号">{{ detail.phone || '-' }}</el-descriptions-item>
          <el-descriptions-item label="昵称">{{ detail.nickname || '-' }}</el-descriptions-item>
          <el-descriptions-item label="地址">{{ detail.address || '-' }}</el-descriptions-item>
          <el-descriptions-item label="注册时间">{{ formatTime(detail.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="经销商">
            <el-tag v-if="detail.is_dealer" type="success">是 ({{ detail.discount_rate }}折)</el-tag>
            <span v-else>否</span>
          </el-descriptions-item>
        </el-descriptions>
        <div style="margin-top: 12px; display: flex; gap: 8px;">
          <el-button type="primary" size="small" @click="showEditDialog">编辑</el-button>
          <el-button type="danger" size="small" @click="handleDelete">删除客户</el-button>
        </div>
      </div>

      <div class="detail-section" v-if="detail.addresses?.length">
        <h4>地址历史 ({{ detail.addresses.length }})</h4>
        <div v-for="addr in detail.addresses" :key="addr.id" class="address-item">
          <div class="addr-name">{{ addr.receiver_name }} {{ addr.receiver_phone }}</div>
          <div class="addr-detail">{{ addr.receiver_address }}</div>
          <el-button type="danger" link size="small" @click="deleteAddress(addr.id)">删除</el-button>
        </div>
      </div>

      <div class="detail-section" v-if="detail.orders?.length">
        <h4>订单历史 ({{ detail.orders.length }})</h4>
        <div v-for="ord in detail.orders" :key="ord.id" class="order-item" @click="goOrder(ord.id)">
          <div class="order-no">{{ ord.order_no }}</div>
          <div class="order-meta">
            <span class="order-status">{{ statusLabel(ord.status) }}</span>
            <span class="order-amount">¥{{ Number(ord.total_amount || 0).toLocaleString() }}</span>
          </div>
          <div class="order-time">{{ formatTime(ord.created_at) }}</div>
        </div>
      </div>
    </el-drawer>

    <!-- 编辑弹窗 -->
    <el-dialog v-model="editVisible" title="编辑客户" width="440px">
      <el-form :model="editForm" label-width="100px">
        <el-form-item label="姓名">
          <el-input v-model="editForm.name" placeholder="客户姓名" />
        </el-form-item>
        <el-form-item label="手机号">
          <el-input v-model="editForm.phone" placeholder="手机号码" />
        </el-form-item>
        <el-form-item label="地址">
          <el-input v-model="editForm.address" type="textarea" :rows="2" placeholder="地址" />
        </el-form-item>
        <el-form-item label="经销商">
          <el-switch v-model="editForm.is_dealer" active-text="是" inactive-text="否" />
        </el-form-item>
        <el-form-item label="折扣比例" v-if="editForm.is_dealer">
          <el-input-number v-model="editForm.discount_rate" :min="1" :max="100" :step="5" />
          <span class="input-tip">% (如85表示85折)</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave" :loading="saveLoading">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import request from '@/utils/request'

const router = useRouter()
const loading = ref(false)
const list = ref([])
const page = ref(1)
const perPage = 20
const total = ref(0)
const searchText = ref('')

// 详情
const drawerVisible = ref(false)
const detail = ref({})
const editVisible = ref(false)
const saveLoading = ref(false)
const editForm = ref({ name: '', phone: '', address: '' })

const formatTime = (t) => {
  if (!t) return '-'
  return t.replace('T', ' ').slice(0, 19)
}

const statusLabel = (s) => ({
  pending: '待处理', paid: '待收货', receiving: '收货中', inspecting: '验货中',
  repairing: '维修中', qc: '质检中', ready: '待回寄', shipping: '回寄中',
  completed: '已完成', cancelled: '已取消', deleted: '已删除'
}[s] || s)

const loadList = async () => {
  loading.value = true
  try {
    const params = { page: page.value, per_page: perPage }
    if (searchText.value) params.search = searchText.value
    const res = await request.get('/admin/customers', { params })
    if (res?.data) {
      list.value = res.data.customers || []
      total.value = res.data.total || 0
    }
  } catch (e) { console.error('loadList', e) }
  finally { loading.value = false }
}

const showDetail = async (row) => {
  try {
    const res = await request.get(`/admin/customers/${row.id}`)
    if (res?.data) {
      detail.value = res.data
      drawerVisible.value = true
    }
  } catch (e) { console.error('showDetail', e) }
}

const showEditDialog = () => {
  editForm.value = {
    name: detail.value.name || '',
    phone: detail.value.phone || '',
    address: detail.value.address || '',
    is_dealer: detail.value.is_dealer || false,
    discount_rate: detail.value.discount_rate || 100
  }
  editVisible.value = true
}

const handleSave = async () => {
  saveLoading.value = true
  try {
    await request.put(`/admin/customers/${detail.value.id}`, editForm.value)
    ElMessage.success('保存成功')
    editVisible.value = false
    showDetail({ id: detail.value.id })
    loadList()
  } catch (e) { console.error('handleSave', e); ElMessage.error('保存失败') }
  finally { saveLoading.value = false }
}

const handleDelete = async () => {
  try {
    await ElMessageBox.confirm('确定删除该客户？关联订单将保留。', '确认删除', { type: 'warning' })
    const res = await request.delete(`/admin/customers/${detail.value.id}`)
    if (res?.success) {
      ElMessage.success('删除成功')
      drawerVisible.value = false
      loadList()
    } else {
      ElMessage.error(res?.message || '删除失败')
    }
  } catch (e) { if (e !== 'cancel') console.error('handleDelete', e) }
}

const deleteAddress = async (addrId) => {
  try {
    await request.delete(`/admin/customers/${detail.value.id}/addresses/${addrId}`)
    ElMessage.success('地址已删除')
    showDetail({ id: detail.value.id })
  } catch (e) { console.error('deleteAddress', e) }
}

const goOrder = (id) => {
  router.push(`/admin/orders/${id}`)
}

onMounted(() => loadList())
</script>

<style scoped>
.customers-page { max-width: 1100px; }
.card { background: #fff; border-radius: 12px; padding: 16px 20px; box-shadow: 0 1px 3px rgba(0,0,0,.08); }
.card-toolbar { display: flex; gap: 12px; align-items: center; margin-bottom: 16px; }
.pagination-bar { margin-top: 16px; display: flex; justify-content: flex-end; }
.detail-section { margin-bottom: 24px; }
.detail-section h4 { font-size: 14px; font-weight: 700; color: #1e293b; margin-bottom: 10px; padding-bottom: 6px; border-bottom: 1px solid #f0f0f0; }
.address-item { padding: 8px 0; border-bottom: 1px solid #f8fafc; }
.addr-name { font-weight: 600; font-size: 13px; color: #334155; }
.addr-detail { font-size: 12px; color: #64748b; margin-top: 2px; }
.order-item { padding: 10px 0; border-bottom: 1px solid #f8fafc; cursor: pointer; }
.order-item:hover { background: #f8fafc; }
.order-no { font-weight: 600; font-size: 13px; color: #3b82f6; }
.order-meta { display: flex; gap: 12px; margin-top: 4px; font-size: 12px; }
.order-status { color: #64748b; }
.order-amount { color: #f59e0b; font-weight: 600; }
.order-time { font-size: 11px; color: #94a3b8; margin-top: 2px; }
</style>
