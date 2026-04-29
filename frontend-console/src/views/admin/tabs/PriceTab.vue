<template>
  <div class="full-panel">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
      <h4 style="margin: 0; font-size: 15px;">价格配置</h4>
      <button class="primary-btn" style="padding: 4px 12px; font-size: 12px;" @click="openPriceDialog()">+ 价格</button>
    </div>
    <el-table :data="filteredPrices" style="width:100%;" size="small">
      <el-table-column label="服务类型">
        <template #default="{ row }">{{ getServiceName(row.service_type_id) }}</template>
      </el-table-column>
      <el-table-column label="产品大类">
        <template #default="{ row }">{{ getTypeName(row.product_type_id) }}</template>
      </el-table-column>
      <el-table-column label="品牌">
        <template #default="{ row }">{{ getBrandName(row.brand_id) }}</template>
      </el-table-column>
      <el-table-column label="型号">
        <template #default="{ row }">{{ getModelName(row.model_id) }}</template>
      </el-table-column>
      <el-table-column prop="price" label="价格" />
      <el-table-column label="操作" width="160">
        <template #default="{ row }">
          <div style="display: flex; gap: 6px;">
            <button class="text-btn" @click="openPriceDialog(row)">编辑</button>
            <button class="text-btn danger" @click="deletePrice(row)">删除</button>
          </div>
        </template>
      </el-table-column>
    </el-table>
    <div style="color:#ccc; text-align:center; padding: 20px;" v-if="!filteredPrices.length">暂无价格配置</div>
  </div>
</template>

<script setup>
import { useDC } from '@/composables/useDataCenter'
const { filteredPrices, getServiceName, getTypeName, getBrandName, getModelName,
  openPriceDialog, deletePrice } = useDC()
</script>
