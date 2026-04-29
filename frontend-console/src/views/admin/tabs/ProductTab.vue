<template>
  <div class="main-layout">
    <!-- 左栏：产品大类 -->
    <div class="sidebar-panel" style="width: 220px;">
      <div class="panel-title">
        产品大类
        <button class="primary-btn" style="padding: 4px 12px; font-size: 12px;" @click="openTypeDialog()">+ 新增</button>
      </div>
      <div class="type-list">
        <div v-for="t in productTypes" :key="t.id"
          :class="['type-item', { active: selectedType?.id === t.id }]"
          @click="selectType(t)">
          <div class="type-name">{{ t.name }}</div>
          <div class="type-stats">{{ getTypeStats(t.id) }}</div>
        </div>
        <div style="padding: 12px; color: #ccc; font-size: 13px; text-align: center;" v-if="!productTypes.length">暂无数据</div>
      </div>
    </div>

    <!-- 中栏：产品类型 + 品牌 -->
    <div class="content-panel" style="flex: 1; display: flex; flex-direction: column; overflow: hidden;">
      <!-- 产品类型标签 -->
      <div class="category-tags" style="display: flex; flex-wrap: wrap; gap: 6px; padding-bottom: 12px;" v-if="selectedType">
        <div v-for="c in typeCategories" :key="c.id"
          :class="['category-tag', { active: selectedCategory?.id === c.id }]"
          @click="selectCategory(c)" style="cursor: pointer; padding: 4px 12px; border-radius: 16px; background: #f5f7fa; font-size: 13px; border: 1px solid transparent; transition: all 0.2s;">
          {{ c.name }} ({{ getCategoryModelCount(c.id) }})
        </div>
        <button class="text-btn" style="font-size: 12px;" @click="openCategoryDialog()">+ 类型</button>
      </div>
      <div style="color: #ccc; font-size: 13px; padding: 0 0 12px;" v-else>请选择产品大类</div>

      <!-- 品牌列表 -->
      <div class="brand-section" style="flex: 1; overflow-y: auto; min-height: 150px;">
        <div v-if="selectedType" class="panel-title" style="position: sticky; top: 0; z-index: 1; background: #fff;">
          品牌
          <button class="primary-btn" style="padding: 4px 12px; font-size: 12px;" @click="openBrandDialog()">+ 品牌</button>
        </div>
        <div v-for="b in typeBrands" :key="b.id"
          :class="['brand-card', { active: selectedBrand?.id === b.id }]"
          @click="selectBrand(b)" style="padding: 10px 12px; margin: 4px 0; border-radius: 6px; cursor: pointer; display: flex; justify-content: space-between; align-items: center; background: #fafafa; border: 1px solid transparent; transition: all 0.2s;">
          <span style="font-weight: 500; font-size: 14px;">{{ b.name }}</span>
          <span style="color: #999; font-size: 12px;">{{ getBrandModelCount(b.id) }}型号</span>
        </div>
        <div style="color: #ccc; font-size: 13px; text-align: center; padding: 20px;" v-if="selectedType && !typeBrands.length">暂无品牌</div>
      </div>
    </div>

    <!-- 右栏：型号 -->
    <div class="detail-panel" style="width: 280px; flex-shrink: 0; background: #fff; border-radius: 8px; border: 1px solid #e4e7ed; display: flex; flex-direction: column; min-height: 200px;">
      <div class="panel-title" v-if="selectedBrand">
        {{ selectedBrand.name }} - 型号
        <button class="primary-btn" style="padding: 4px 12px; font-size: 12px;" @click="openModelDialog()">+ 型号</button>
      </div>
      <div style="flex: 1; overflow-y: auto;">
        <el-table :data="brandModels" size="small" style="width: 100%;" v-if="selectedBrand">
          <el-table-column prop="name" label="型号名称" />
          <el-table-column label="产品类型">
            <template #default="{ row }">
              <span v-for="(cid, i) in (row.category_ids || [])" :key="cid">
                {{ getCategoryName(cid) }}<span v-if="i < (row.category_ids?.length || 0) - 1">, </span>
              </span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="160">
            <template #default="{ row }">
              <div style="display: flex; gap: 6px;">
                <button class="text-btn" @click="openModelDialog(row)">编辑</button>
                <button class="text-btn danger" @click="deleteModel(row)">删除</button>
              </div>
            </template>
          </el-table-column>
        </el-table>
        <div style="color: #ccc; font-size: 13px; text-align: center; padding: 20px;" v-else>请选择品牌</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useDC } from '@/composables/useDataCenter'
const { productTypes, selectedType, selectedCategory, selectedBrand, typeCategories, typeBrands, brandModels,
  selectType, selectCategory, selectBrand, getTypeStats, getCategoryModelCount, getBrandModelCount,
  getCategoryName, deleteModel, openModelDialog, openCategoryDialog, openBrandDialog, openTypeDialog } = useDC()
</script>
