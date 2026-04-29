<template>
  <div class="data-center">
    <!-- Tab 栏 -->
    <div class="tab-bar">
      <div v-for="tab in ['product','service','price','inventory']" :key="tab"
        :class="['tab-item', { active: activeTab === tab }]"
        @click="activeTab = tab">
        {{ tab === 'product' ? '产品体系' : tab === 'service' ? '服务体系' : tab === 'price' ? '价格体系' : '配件库存' }}
      </div>
    </div>

    <!-- 标签页 -->
    <ProductTab v-if="activeTab === 'product'" />
    <ServiceTab v-if="activeTab === 'service'" />
    <PriceTab v-if="activeTab === 'price'" />
    <InventoryTab v-if="activeTab === 'inventory'" />

    <!-- ====== 弹窗 ====== -->
    <!-- 产品大类 -->
    <el-dialog v-model="typeDialogVisible" :title="isEditType ? '编辑产品大类' : '新增产品大类'" width="500px">
      <el-form :model="typeForm" label-width="80px">
        <el-form-item label="名称"><el-input v-model="typeForm.name" /></el-form-item>
        <el-form-item label="归属类别"><el-input v-model="typeForm.categories" placeholder="逗号分隔" /></el-form-item>
        <el-form-item label="排序"><el-input-number v-model="typeForm.sort_order" :min="0" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="typeDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitType" :loading="submitLoading">保存</el-button>
      </template>
    </el-dialog>

    <!-- 产品类型 -->
    <el-dialog v-model="categoryDialogVisible" :title="isEditCategory ? '编辑产品类型' : '新增产品类型'" width="500px">
      <el-form :model="categoryForm" label-width="80px">
        <el-form-item label="名称"><el-input v-model="categoryForm.name" /></el-form-item>
        <el-form-item label="产品大类">
          <el-select v-model="categoryForm.product_type_id" style="width:100%">
            <el-option v-for="t in productTypes" :key="t.id" :label="t.name" :value="t.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="排序"><el-input-number v-model="categoryForm.sort_order" :min="0" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="categoryDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitCategory" :loading="submitLoading">保存</el-button>
      </template>
    </el-dialog>

    <!-- 品牌 -->
    <el-dialog v-model="brandDialogVisible" :title="isEditBrand ? '编辑品牌' : '新增品牌'" width="500px">
      <el-form :model="brandForm" label-width="80px">
        <el-form-item label="名称"><el-input v-model="brandForm.name" /></el-form-item>
        <el-form-item label="产品大类">
          <el-select v-model="brandForm.product_type_id" style="width:100%">
            <el-option v-for="t in productTypes" :key="t.id" :label="t.name" :value="t.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="brandDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitBrand" :loading="submitLoading">保存</el-button>
      </template>
    </el-dialog>

    <!-- 型号 -->
    <el-dialog v-model="modelDialogVisible" :title="isEditModel ? '编辑型号' : '新增型号'" width="550px">
      <el-form :model="modelForm" label-width="80px">
        <el-form-item label="名称"><el-input v-model="modelForm.name" /></el-form-item>
        <el-form-item label="品牌">
          <el-select v-model="modelForm.brand_id" style="width:100%">
            <el-option v-for="b in brands" :key="b.id" :label="b.name" :value="b.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="产品类型">
          <el-select v-model="modelForm.category_ids" multiple style="width:100%">
            <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="modelDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitModel" :loading="submitLoading">保存</el-button>
      </template>
    </el-dialog>

    <!-- 服务类型 -->
    <el-dialog v-model="serviceTypeDialogVisible" :title="isEditServiceType ? '编辑服务类型' : '新增服务类型'" width="500px">
      <el-form :model="serviceTypeForm" label-width="80px">
        <el-form-item label="名称"><el-input v-model="serviceTypeForm.name" /></el-form-item>
        <el-form-item label="产品大类">
          <el-select v-model="serviceTypeForm.product_type_id" style="width:100%">
            <el-option v-for="t in productTypes" :key="t.id" :label="t.name" :value="t.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="产品类型">
          <el-select v-model="serviceTypeForm.category_id" clearable style="width:100%">
            <el-option v-for="c in serviceTypeCategories" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="基准价"><el-input-number v-model="serviceTypeForm.base_price" :min="0" /></el-form-item>
        <el-form-item label="描述"><el-input v-model="serviceTypeForm.description" type="textarea" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="serviceTypeDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitServiceType" :loading="submitLoading">保存</el-button>
      </template>
    </el-dialog>

    <!-- 检项 -->
    <el-dialog v-model="serviceItemDialogVisible" :title="isEditServiceItem ? '编辑检项' : '新增检项'" width="500px">
      <el-form :model="serviceItemForm" label-width="80px">
        <el-form-item label="名称"><el-input v-model="serviceItemForm.name" /></el-form-item>
        <el-form-item label="产品大类">
          <el-select v-model="serviceItemForm.product_type_id" style="width:100%">
            <el-option v-for="t in productTypes" :key="t.id" :label="t.name" :value="t.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="serviceItemDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitServiceItem" :loading="submitLoading">保存</el-button>
      </template>
    </el-dialog>

    <!-- 价格 -->
    <el-dialog v-model="priceDialogVisible" :title="isEditPrice ? '编辑价格' : '新增价格'" width="500px">
      <el-form :model="priceForm" label-width="80px">
        <el-form-item label="产品大类">
          <el-select v-model="priceForm.product_type_id" style="width:100%" @change="onPriceTypeChange">
            <el-option v-for="t in productTypes" :key="t.id" :label="t.name" :value="t.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="产品类型">
          <el-select v-model="priceForm.category_id" clearable style="width:100%">
            <el-option v-for="c in priceCategories" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="品牌">
          <el-select v-model="priceForm.brand_id" clearable style="width:100%">
            <el-option v-for="b in priceBrands" :key="b.id" :label="b.name" :value="b.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="型号">
          <el-select v-model="priceForm.model_id" clearable style="width:100%">
            <el-option v-for="m in priceModels" :key="m.id" :label="m.name" :value="m.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="服务类型">
          <el-select v-model="priceForm.service_type_id" style="width:100%">
            <el-option v-for="s in priceServiceTypes" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="价格"><el-input-number v-model="priceForm.price" :min="0" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="priceDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitPrice" :loading="submitLoading">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useDataCenter } from '@/composables/useDataCenter'
import ProductTab from './tabs/ProductTab.vue'
import ServiceTab from './tabs/ServiceTab.vue'
import PriceTab from './tabs/PriceTab.vue'
import InventoryTab from './tabs/InventoryTab.vue'

const activeTab = ref('product')

const {
  typeDialogVisible, isEditType, typeForm, submitType, submitLoading,
  categoryDialogVisible, isEditCategory, categoryForm, productTypes, submitCategory,
  brandDialogVisible, isEditBrand, brandForm, brands, submitBrand,
  modelDialogVisible, isEditModel, modelForm, categories, submitModel,
  serviceTypeDialogVisible, isEditServiceType, serviceTypeForm, serviceTypeCategories, submitServiceType,
  serviceItemDialogVisible, isEditServiceItem, serviceItemForm, submitServiceItem,
  priceDialogVisible, isEditPrice, priceForm, priceCategories, priceBrands, priceModels, priceServiceTypes,
  onPriceTypeChange, submitPrice
} = useDataCenter()
</script>
<style scoped>
.data-center { padding: 20px 20px 12px; height: 100%; overflow: hidden; }
.tab-bar { display: flex; gap: 4px; margin-bottom: 16px; background: #f5f7fa; padding: 4px; border-radius: 8px; flex-shrink: 0; }
.tab-item { padding: 10px 24px; border-radius: 6px; cursor: pointer; transition: all 0.2s; display: flex; align-items: center; gap: 6px; font-size: 14px; color: #666; }
.tab-item:hover { background: #fff; }
.tab-item.active { background: #fff; color: #409eff; font-weight: 600; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }

/* ===== Shared: tab components ===== */
</style>

<style>
.main-layout { display: flex; gap: 16px; height: calc(100% - 80px); min-height: 500px; }
.full-panel { height: calc(100% - 80px); overflow-y: auto; }

.sidebar-panel { width: 240px; flex-shrink: 0; background: #fff; border-radius: 8px; border: 1px solid #e4e7ed; display: flex; flex-direction: column; overflow-y: auto; }
.panel-title { padding: 16px; border-bottom: 1px solid #e4e7ed; font-weight: 600; display: flex; justify-content: space-between; align-items: center; }

.type-list { padding: 8px; }
.type-item { padding: 12px; border-radius: 6px; cursor: pointer; transition: all 0.2s; }
.type-item:hover { background: #f5f7fa; }
.type-item.active { background: #ecf5ff; border-left: 3px solid #409eff; }
.type-name { font-weight: 600; font-size: 14px; }
.type-stats { color: #999; font-size: 12px; margin-top: 4px; }

.content-panel { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
.category-tag { padding: 4px 12px; border-radius: 16px; background: #f5f7fa; font-size: 13px; border: 1px solid transparent; cursor: pointer; transition: all 0.2s; }
.category-tag:hover { border-color: #409eff; }
.category-tag.active { background: #ecf5ff; border-color: #409eff; color: #409eff; }

.brand-section { flex: 1; overflow-y: auto; min-height: 100px; }
.brand-card { padding: 10px 12px; margin: 4px 0; border-radius: 6px; cursor: pointer; display: flex; justify-content: space-between; align-items: center; background: #fafafa; border: 1px solid transparent; transition: all 0.2s; }
.brand-card:hover { background: #f0f7ff; }
.brand-card.active { background: #ecf5ff; border-color: #409eff; }

.detail-panel { width: 280px; flex-shrink: 0; background: #fff; border-radius: 8px; border: 1px solid #e4e7ed; display: flex; flex-direction: column; min-height: 200px; }

.primary-btn { padding: 10px 20px; border-radius: 8px; font-size: 14px; cursor: pointer; border: none; font-weight: 500; background: #409eff; color: #fff; }
.primary-btn:disabled { background: #c0c4cc; cursor: not-allowed; }
.text-btn { background: none; border: none; color: #409eff; font-size: 12px; cursor: pointer; padding: 4px 0; }
.text-btn.danger { color: #f56c6c; }
</style>
