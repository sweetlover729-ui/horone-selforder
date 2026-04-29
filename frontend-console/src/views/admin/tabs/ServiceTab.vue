<template>
  <div class="full-panel">
    <!-- 服务类型 -->
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
      <h4 style="margin: 0; font-size: 15px;">服务类型</h4>
      <button class="primary-btn" style="padding: 4px 12px; font-size: 12px;" @click="openServiceTypeDialog()">+ 服务类型</button>
    </div>
    <el-table :data="filteredServiceTypes" style="width:100%;" size="small">
      <el-table-column prop="name" label="服务名称" />
      <el-table-column label="产品大类">
        <template #default="{ row }">{{ getTypeName(row.product_type_id) }}</template>
      </el-table-column>
      <el-table-column label="产品类型">
        <template #default="{ row }">{{ getCategoryName(row.category_id) }}</template>
      </el-table-column>
      <el-table-column prop="base_price" label="基准价" />
      <el-table-column prop="description" label="描述" />
      <el-table-column label="操作" width="160">
        <template #default="{ row }">
          <div style="display: flex; gap: 6px;">
            <button class="text-btn" @click="openServiceTypeDialog(row)">编辑</button>
            <button class="text-btn danger" @click="deleteServiceType(row)">删除</button>
          </div>
        </template>
      </el-table-column>
    </el-table>
    <div style="color:#ccc; text-align:center; padding: 20px;" v-if="!filteredServiceTypes.length">暂无服务类型</div>

    <!-- 检项 -->
    <div style="display: flex; justify-content: space-between; align-items: center; margin: 24px 0 16px;">
      <h4 style="margin: 0; font-size: 15px;">维修检项</h4>
      <button class="primary-btn" style="padding: 4px 12px; font-size: 12px;" @click="openServiceItemDialog()">+ 检项</button>
    </div>
    <el-table :data="filteredServiceItems" style="width:100%;" size="small">
      <el-table-column prop="name" label="检项名称" />
      <el-table-column label="产品大类">
        <template #default="{ row }">{{ getTypeName(row.product_type_id) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="160">
        <template #default="{ row }">
          <div style="display: flex; gap: 6px;">
            <button class="text-btn" @click="openServiceItemDialog(row)">编辑</button>
            <button class="text-btn danger" @click="deleteServiceItem(row)">删除</button>
          </div>
        </template>
      </el-table-column>
    </el-table>
    <div style="color:#ccc; text-align:center; padding: 20px;" v-if="!filteredServiceItems.length">暂无检项</div>
  </div>
</template>

<script setup>
import { useDC } from '@/composables/useDataCenter'
const { filteredServiceTypes, filteredServiceItems,
  getTypeName, getCategoryName,
  openServiceTypeDialog, deleteServiceType,
  openServiceItemDialog, deleteServiceItem } = useDC()
</script>
