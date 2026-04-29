<template>
  <div class="data-hub">
    <!-- 页头 -->
    <div class="page-header-row">
      <div>
        <h1>数据中枢</h1>
        <p>统一管理产品、品牌、型号、服务类型、维修检项</p>
      </div>
      <div class="quick-actions">
        <div class="search-box">
          <span class="search-icon">Q</span>
          <input v-model="keyword" :placeholder="`搜索${activeTabLabel}…`" @input="onSearch" />
        </div>
        <button class="btn btn-outline btn-sm" @click="handleBackup" :disabled="backupLoading">
          {{ backupLoading ? '导出中…' : '📥 导出备份' }}
        </button>
        <button class="btn btn-outline btn-sm" @click="showRestoreDialog = true">
          📤 导入恢复
        </button>
      </div>
    </div>

    <!-- 标签切换 -->
    <div class="tabs">
      <div class="tab-item" :class="{ active: activeTab === 'types' }" @click="switchTab('types')">
        产品类别 <span class="tab-count">{{ productTypes.length }}</span>
      </div>
      <div class="tab-item" :class="{ active: activeTab === 'brands' }" @click="switchTab('brands')">
        品牌 <span class="tab-count">{{ brands.length }}</span>
      </div>
      <div class="tab-item" :class="{ active: activeTab === 'models' }" @click="switchTab('models')">
        型号 <span class="tab-count">{{ models.length }}</span>
      </div>
      <div class="tab-item" :class="{ active: activeTab === 'services' }" @click="switchTab('services')">
        服务类型 <span class="tab-count">{{ serviceTypes.length }}</span>
      </div>
      <div class="tab-item" :class="{ active: activeTab === 'items' }" @click="switchTab('items')">
        维修检项 <span class="tab-count">{{ serviceItems.length }}</span>
      </div>
    </div>

    <!-- ========== 产品类别 ========== -->
    <div v-show="activeTab === 'types'" class="card">
      <div class="card-header">
        <span class="card-title">产品类别</span>
        <button class="btn btn-primary btn-sm" @click="openTypeDialog()">+ 新增类型</button>
      </div>
      <table class="data-table">
        <thead>
          <tr>
            <th>排序</th>
            <th>类型名称</th>
            <th>套装类别</th>
            <th>关联品牌</th>
            <th>关联服务</th>
            <th>状态</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="t in filteredTypes" :key="t.id">
            <td style="width:60px"><input class="inline-input" v-model.number="t.sort_order" @change="updateType(t)" type="number" min="0" /></td>
            <td><span class="type-name">{{ t.name }}</span></td>
            <td>
              <div style="display:flex;flex-wrap:wrap;gap:4px">
                <span v-for="c in parseCats(t.categories)" :key="c" class="relation-badge">{{ c }}</span>
                <span v-if="!t.categories" class="text-muted f12">— 无</span>
              </div>
            </td>
            <td><span class="relation-badge green">{{ brandCountByType[t.id] || 0 }} 个</span></td>
            <td><span class="relation-badge">{{ serviceCountByType[t.id] || 0 }} 个</span></td>
            <td>
              <span class="tag" :class="t.is_active === 1 ? 'tag-success' : 'tag-gray'" @click="toggleType(t)" style="cursor:pointer">
                {{ t.is_active === 1 ? '启用' : '禁用' }}
              </span>
            </td>
            <td>
              <button class="btn btn-ghost btn-sm" @click="openTypeDialog(t)">编辑</button>
              <button class="btn btn-danger btn-sm" @click="deleteType(t)" style="margin-left:4px">删除</button>
            </td>
          </tr>
          <tr v-if="filteredTypes.length === 0">
            <td colspan="7"><div class="empty-state"><div class="empty-desc">暂无产品类别</div></div></td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- ========== 品牌管理 ========== -->
    <div v-show="activeTab === 'brands'" class="card">
      <div class="card-header">
        <span class="card-title">品牌</span>
        <div style="display:flex;gap:8px;align-items:center">
          <select v-model="brandFilterType" class="filter-select">
            <option value="">全部类型</option>
            <option v-for="t in productTypes" :key="t.id" :value="t.id">{{ t.name }}</option>
          </select>
          <button class="btn btn-primary btn-sm" @click="openBrandDialog()">+ 新增品牌</button>
        </div>
      </div>
      <table class="data-table">
        <thead>
          <tr>
            <th>品牌名称</th>
            <th>归属类型</th>
            <th>型号数量</th>
            <th>官网</th>
            <th>状态</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="b in filteredBrands" :key="b.id">
            <td><span style="font-weight:600">{{ b.name }}</span></td>
            <td><span class="relation-badge">{{ getTypeName(b.product_type_id) }}</span></td>
            <td><span class="tag tag-info">{{ modelCountByBrand[b.id] || 0 }} 个型号</span></td>
            <td><a v-if="b.website" :href="b.website" target="_blank" class="link">{{ b.website }}</a><span v-else class="text-muted f12">—</span></td>
            <td>
              <span class="tag" :class="b.is_active === 1 ? 'tag-success' : 'tag-gray'" @click="toggleBrand(b)" style="cursor:pointer">
                {{ b.is_active === 1 ? '启用' : '禁用' }}
              </span>
            </td>
            <td>
              <button class="btn btn-ghost btn-sm" @click="openBrandDialog(b)">编辑</button>
              <button class="btn btn-danger btn-sm" @click="deleteBrand(b)" style="margin-left:4px">删除</button>
            </td>
          </tr>
          <tr v-if="filteredBrands.length === 0">
            <td colspan="6"><div class="empty-state"><div class="empty-desc">暂无品牌</div></div></td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- ========== 型号管理 ========== -->
    <div v-show="activeTab === 'models'" class="card">
      <div class="card-header">
        <span class="card-title">型号</span>
        <div style="display:flex;gap:8px;align-items:center">
          <select v-model="modelFilterType" class="filter-select" @change="modelFilterBrand=''">
            <option value="">全部类型</option>
            <option v-for="t in productTypes" :key="t.id" :value="t.id">{{ t.name }}</option>
          </select>
          <select v-model="modelFilterBrand" class="filter-select">
            <option value="">全部品牌</option>
            <option v-for="b in filteredBrandsForModels" :key="b.id" :value="b.id">{{ b.name }}</option>
          </select>
          <button class="btn btn-primary btn-sm" @click="openModelDialog()">+ 新增型号</button>
        </div>
      </div>
      <table class="data-table">
        <thead>
          <tr>
            <th>品牌</th>
            <th>型号名称</th>
            <th>产品类别</th>
            <th>状态</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="m in filteredModels" :key="m.id">
            <td><span class="relation-badge">{{ getBrandName(m.brand_id) }}</span></td>
            <td><span style="font-weight:600">{{ m.name }}</span></td>
            <td><span class="tag tag-info">{{ m.category || '—' }}</span></td>
            <td>
              <span class="tag" :class="m.is_active === 1 ? 'tag-success' : 'tag-gray'" @click="toggleModel(m)" style="cursor:pointer">
                {{ m.is_active === 1 ? '启用' : '禁用' }}
              </span>
            </td>
            <td>
              <button class="btn btn-ghost btn-sm" @click="openModelDialog(m)">编辑</button>
              <button class="btn btn-danger btn-sm" @click="deleteModel(m)" style="margin-left:4px">删除</button>
            </td>
          </tr>
          <tr v-if="filteredModels.length === 0">
            <td colspan="5"><div class="empty-state"><div class="empty-desc">暂无型号</div></div></td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- ========== 服务类型 ========== -->
    <div v-show="activeTab === 'services'" class="card">
      <div class="card-header">
        <span class="card-title">服务类型</span>
        <div style="display:flex;gap:8px;align-items:center">
          <select v-model="serviceFilterType" class="filter-select">
            <option value="">全部类型</option>
            <option v-for="t in productTypes" :key="t.id" :value="t.id">{{ t.name }}</option>
          </select>
          <button class="btn btn-primary btn-sm" @click="openServiceDialog()">+ 新增服务</button>
        </div>
      </div>
      <table class="data-table">
        <thead>
          <tr>
            <th>服务名称</th>
            <th>归属类型</th>
            <th>描述</th>
            <th>基准价格</th>
            <th>品牌价格</th>
            <th>排序</th>
            <th>状态</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="s in filteredServices" :key="s.id">
            <td><span style="font-weight:600">{{ s.name }}</span></td>
            <td><span class="relation-badge">{{ getTypeName(s.product_type_id) }}</span></td>
            <td><span class="f12 text-muted" style="max-width:200px;display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{{ s.description }}</span></td>
            <td><span class="price-tag">¥{{ s.base_price }}</span></td>
            <td>
              <span v-if="overrideCountByService[s.id]" class="relation-badge green">{{ overrideCountByService[s.id] }} 个品牌有专属价</span>
              <span v-else class="f12 text-muted">使用基准价</span>
            </td>
            <td style="width:60px"><input class="inline-input" v-model.number="s.sort_order" @change="updateService(s)" type="number" min="0" /></td>
            <td>
              <span class="tag" :class="s.is_active === 1 ? 'tag-success' : 'tag-gray'" @click="toggleService(s)" style="cursor:pointer">
                {{ s.is_active === 1 ? '启用' : '禁用' }}
              </span>
            </td>
            <td>
              <button class="btn btn-ghost btn-sm" @click="openServiceDialog(s)">编辑</button>
              <button class="btn btn-ghost btn-sm" @click="openOverrides(s)" style="margin-left:4px;color:var(--primary)">品牌价</button>
              <button class="btn btn-danger btn-sm" @click="deleteService(s)" style="margin-left:4px">删除</button>
            </td>
          </tr>
          <tr v-if="filteredServices.length === 0">
            <td colspan="8"><div class="empty-state"><div class="empty-desc">暂无服务类型</div></div></td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- ========== 维修检项 ========== -->
    <div v-show="activeTab === 'items'" class="card">
      <div class="card-header">
        <span class="card-title">维修检项</span>
        <div style="display:flex;gap:8px;align-items:center">
          <select v-model="itemFilterType" class="filter-select">
            <option value="">全部类型</option>
            <option v-for="t in productTypes" :key="t.id" :value="t.id">{{ t.name }}</option>
          </select>
          <button class="btn btn-primary btn-sm" @click="openItemDialog()">+ 新增检项</button>
        </div>
      </div>
      <table class="data-table">
        <thead>
          <tr>
            <th>产品类别</th>
            <th>检项名称</th>
            <th>描述</th>
            <th>类型</th>
            <th>排序</th>
            <th>状态</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in filteredItems" :key="item.id">
            <td><span class="relation-badge">{{ getTypeName(item.product_type_id) }}</span></td>
            <td><span style="font-weight:600">{{ item.name }}</span></td>
            <td><span class="f12 text-muted">{{ item.description }}</span></td>
            <td><span class="tag" :class="item.is_required === 1 ? 'tag-danger' : 'tag-gray'">{{ item.is_required === 1 ? '必检' : '可检' }}</span></td>
            <td style="width:60px"><input class="inline-input" v-model.number="item.sort_order" @change="updateItem(item)" type="number" min="0" /></td>
            <td>
              <span class="tag" :class="item.is_active === 1 ? 'tag-success' : 'tag-gray'" @click="toggleItem(item)" style="cursor:pointer">
                {{ item.is_active === 1 ? '启用' : '禁用' }}
              </span>
            </td>
            <td>
              <button class="btn btn-ghost btn-sm" @click="openItemDialog(item)">编辑</button>
              <button class="btn btn-danger btn-sm" @click="deleteItem(item)" style="margin-left:4px">删除</button>
            </td>
          </tr>
          <tr v-if="filteredItems.length === 0">
            <td colspan="7"><div class="empty-state"><div class="empty-desc">暂无维修检项</div></div></td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- ========== 弹窗们 ========== -->

    <!-- 产品类别弹窗 -->
    <div class="dialog-overlay" v-if="typeDialog.show" @click.self="typeDialog.show = false">
      <div class="dialog">
        <div class="dialog-header">
          <span>{{ typeDialog.isEdit ? '编辑产品类别' : '新增产品类别' }}</span>
          <button class="dialog-close" @click="typeDialog.show = false">×</button>
        </div>
        <div class="dialog-body">
          <div class="form-row">
            <div class="form-field">
              <label class="form-label">类型名称 *</label>
              <input v-model="typeDialog.form.name" class="form-input" placeholder="如：调节器、BCD、电脑表" />
            </div>
            <div class="form-field">
              <label class="form-label">排序</label>
              <input v-model.number="typeDialog.form.sort_order" type="number" min="0" class="form-input" />
            </div>
          </div>
          <div class="form-field">
            <label class="form-label">套装类别 <span class="form-hint-inline">（用英文逗号分隔，如：标准套装,侧挂套装）</span></label>
            <input v-model="typeDialog.form.categories_input" class="form-input" placeholder="用英文逗号分隔，如：标准套装,侧挂套装,背挂双瓶套装" />
          </div>
          <div class="form-field">
            <label class="form-label">状态</label>
            <label style="display:flex;align-items:center;gap:8px;cursor:pointer">
              <input type="checkbox" v-model="typeDialog.form.is_active" :true-value="1" :false-value="0" />
              启用（禁用后客户端不可选）
            </label>
          </div>
        </div>
        <div class="dialog-footer">
          <button class="btn btn-ghost" @click="typeDialog.show = false">取消</button>
          <button class="btn btn-primary" @click="saveType" :disabled="saving">保存</button>
        </div>
      </div>
    </div>

    <!-- 品牌弹窗 -->
    <div class="dialog-overlay" v-if="brandDialog.show" @click.self="brandDialog.show = false">
      <div class="dialog">
        <div class="dialog-header">
          <span>{{ brandDialog.isEdit ? '编辑品牌' : '新增品牌' }}</span>
          <button class="dialog-close" @click="brandDialog.show = false">×</button>
        </div>
        <div class="dialog-body">
          <div class="form-row">
            <div class="form-field">
              <label class="form-label">品牌名称 *</label>
              <input v-model="brandDialog.form.name" class="form-input" placeholder="如：Scubapro、Apeks、Suunto" />
            </div>
            <div class="form-field">
              <label class="form-label">归属产品类别 *</label>
              <select v-model="brandDialog.form.product_type_id" class="form-input">
                <option value="">请选择</option>
                <option v-for="t in productTypes" :key="t.id" :value="t.id">{{ t.name }}</option>
              </select>
            </div>
          </div>
          <div class="form-row">
            <div class="form-field">
              <label class="form-label">官网</label>
              <input v-model="brandDialog.form.website" class="form-input" placeholder="https://..." />
            </div>
            <div class="form-field">
              <label class="form-label">国家</label>
              <input v-model="brandDialog.form.country" class="form-input" placeholder="如：中国、美国" />
            </div>
          </div>
          <div class="form-field">
            <label class="form-label">备注</label>
            <textarea v-model="brandDialog.form.notes" class="form-input" rows="2" placeholder=""></textarea>
          </div>
          <div class="form-field">
            <label class="form-label" style="display:flex;align-items:center;gap:8px;cursor:pointer">
              <input type="checkbox" v-model="brandDialog.form.is_active" :true-value="1" :false-value="0" />启用
            </label>
          </div>
        </div>
        <div class="dialog-footer">
          <button class="btn btn-ghost" @click="brandDialog.show = false">取消</button>
          <button class="btn btn-primary" @click="saveBrand" :disabled="saving">保存</button>
        </div>
      </div>
    </div>

    <!-- 型号弹窗 -->
    <div class="dialog-overlay" v-if="modelDialog.show" @click.self="modelDialog.show = false">
      <div class="dialog">
        <div class="dialog-header">
          <span>{{ modelDialog.isEdit ? '编辑型号' : '新增型号' }}</span>
          <button class="dialog-close" @click="modelDialog.show = false">×</button>
        </div>
        <div class="dialog-body">
          <div class="form-row">
            <div class="form-field">
              <label class="form-label">品牌 *</label>
              <select v-model="modelDialog.form.brand_id" class="form-input">
                <option value="">请选择品牌</option>
                <option v-for="b in filteredBrandsForModels" :key="b.id" :value="b.id">{{ b.name }} ({{ getTypeName(b.product_type_id) }})</option>
              </select>
            </div>
            <div class="form-field">
              <label class="form-label">型号名称 *</label>
              <input v-model="modelDialog.form.name" class="form-input" placeholder="如：MK25 EVO、Perdix、Hydros Pro" />
            </div>
          </div>
          <div class="form-field">
            <label class="form-label">产品类别</label>
            <select v-model="modelDialog.form.category" class="form-input">
              <option value="">无（通用）</option>
              <option value="一级头">一级头</option>
              <option value="二级头">二级头</option>
              <option value="备用二级头">备用二级头</option>
              <option value="背飞">背飞</option>
              <option value="电脑表">电脑表</option>
            </select>
            <div class="form-hint">调节器必填，BCD填"背飞"，电脑表可不填</div>
          </div>
          <div class="form-field">
            <label class="form-label" style="display:flex;align-items:center;gap:8px;cursor:pointer">
              <input type="checkbox" v-model="modelDialog.form.is_active" :true-value="1" :false-value="0" />启用
            </label>
          </div>
        </div>
        <div class="dialog-footer">
          <button class="btn btn-ghost" @click="modelDialog.show = false">取消</button>
          <button class="btn btn-primary" @click="saveModel" :disabled="saving">保存</button>
        </div>
      </div>
    </div>

    <!-- 服务类型弹窗 -->
    <div class="dialog-overlay" v-if="serviceDialog.show" @click.self="serviceDialog.show = false">
      <div class="dialog dialog-wide">
        <div class="dialog-header">
          <span>{{ serviceDialog.isEdit ? '编辑服务类型' : '新增服务类型' }}</span>
          <button class="dialog-close" @click="serviceDialog.show = false">×</button>
        </div>
        <div class="dialog-body">
          <div class="form-row">
            <div class="form-field">
              <label class="form-label">服务名称 *</label>
              <input v-model="serviceDialog.form.name" class="form-input" placeholder="如：标准套装保养、屏幕更换维修" />
            </div>
            <div class="form-field">
              <label class="form-label">归属产品类别 *</label>
              <select v-model="serviceDialog.form.product_type_id" class="form-input">
                <option value="">请选择</option>
                <option v-for="t in productTypes" :key="t.id" :value="t.id">{{ t.name }}</option>
              </select>
            </div>
          </div>
          <div class="form-row">
            <div class="form-field">
              <label class="form-label">基准价格（元）*</label>
              <input v-model.number="serviceDialog.form.base_price" type="number" min="0" class="form-input" />
              <div class="form-hint">此为默认价格，品牌专属价可在下方单独设置</div>
            </div>
            <div class="form-field">
              <label class="form-label">排序</label>
              <input v-model.number="serviceDialog.form.sort_order" type="number" min="0" class="form-input" />
            </div>
          </div>
          <div class="form-field">
            <label class="form-label">描述</label>
            <textarea v-model="serviceDialog.form.description" class="form-input" rows="2" placeholder="简要描述服务内容"></textarea>
          </div>
          <div class="form-field">
            <label class="form-label" style="display:flex;align-items:center;gap:8px;cursor:pointer">
              <input type="checkbox" v-model="serviceDialog.form.is_active" :true-value="1" :false-value="0" />启用
            </label>
          </div>
        </div>
        <div class="dialog-footer">
          <button class="btn btn-ghost" @click="serviceDialog.show = false">取消</button>
          <button class="btn btn-primary" @click="saveService" :disabled="saving">保存</button>
        </div>
      </div>
    </div>

    <!-- 维修检项弹窗 -->
    <div class="dialog-overlay" v-if="itemDialog.show" @click.self="itemDialog.show = false">
      <div class="dialog">
        <div class="dialog-header">
          <span>{{ itemDialog.isEdit ? '编辑检项' : '新增检项' }}</span>
          <button class="dialog-close" @click="itemDialog.show = false">×</button>
        </div>
        <div class="dialog-body">
          <div class="form-row">
            <div class="form-field">
              <label class="form-label">产品类别 *</label>
              <select v-model="itemDialog.form.product_type_id" class="form-input">
                <option value="">请选择</option>
                <option v-for="t in productTypes" :key="t.id" :value="t.id">{{ t.name }}</option>
              </select>
            </div>
            <div class="form-field">
              <label class="form-label">检项名称 *</label>
              <input v-model="itemDialog.form.name" class="form-input" placeholder="如：一级头O型圈检查、屏幕检查" />
            </div>
          </div>
          <div class="form-row">
            <div class="form-field">
              <label class="form-label">检项类型</label>
              <select v-model="itemDialog.form.is_required" class="form-input">
                <option :value="1">必检项（保养/维修必须完成）</option>
                <option :value="0">可检项（根据需要勾选）</option>
              </select>
            </div>
            <div class="form-field">
              <label class="form-label">排序</label>
              <input v-model.number="itemDialog.form.sort_order" type="number" min="0" class="form-input" />
            </div>
          </div>
          <div class="form-field">
            <label class="form-label">描述</label>
            <textarea v-model="itemDialog.form.description" class="form-input" rows="2" placeholder="简要描述检项内容"></textarea>
          </div>
          <div class="form-field">
            <label class="form-label" style="display:flex;align-items:center;gap:8px;cursor:pointer">
              <input type="checkbox" v-model="itemDialog.form.is_active" :true-value="1" :false-value="0" />启用
            </label>
          </div>
        </div>
        <div class="dialog-footer">
          <button class="btn btn-ghost" @click="itemDialog.show = false">取消</button>
          <button class="btn btn-primary" @click="saveItem" :disabled="saving">保存</button>
        </div>
      </div>
    </div>

    <!-- 品牌专属价弹窗 -->
    <div class="dialog-overlay" v-if="overrideDialog.show" @click.self="overrideDialog.show = false">
      <div class="dialog dialog-wide">
        <div class="dialog-header">
          <span>品牌专属价格 — {{ overrideDialog.service?.name }}</span>
          <div style="font-size:13px;color:var(--text-secondary);font-weight:400">
            基准价：<span style="color:var(--warning);font-weight:700">¥{{ overrideDialog.service?.base_price }}</span>
          </div>
          <button class="dialog-close" @click="overrideDialog.show = false">×</button>
        </div>
        <div class="dialog-body">
          <div class="override-grid">
            <div v-for="brand in overrideDialog.brands" :key="brand.id" class="override-item">
              <div class="override-brand">
                <span class="relation-badge">{{ brand.name }}</span>
                <span class="override-type">{{ getTypeName(brand.product_type_id) }}</span>
              </div>
              <div class="override-price">
                <span class="override-base">¥{{ overrideDialog.service?.base_price }}</span>
                <input
                  v-model.number="overrideDialog.overrides[brand.id]"
                  type="number" min="0"
                  class="override-input"
                  :placeholder="'='""
                  @change="saveOverride(brand.id)"
                />
                <span v-if="overrideDialog.overrides[brand.id]" class="override-diff">
                  {{ overrideDialog.overrides[brand.id] > overrideDialog.service.base_price ? '+' : '' }}{{ overrideDialog.overrides[brand.id] - overrideDialog.service.base_price }}
                </span>
              </div>
            </div>
          </div>
          <div v-if="overrideDialog.brands.length === 0" class="empty-state">
            <div class="empty-desc">该产品类别下暂无品牌</div>
          </div>
        </div>
        <div class="dialog-footer">
          <div class="override-legend">
            留空表示使用基准价；填写数字为该品牌的专属价格
          </div>
          <button class="btn btn-ghost" @click="overrideDialog.show = false">关闭</button>
        </div>
      </div>
    </div>

    <!-- 恢复确认对话框 -->
    <div v-if="showRestoreDialog" class="dialog-overlay" @click.self="showRestoreDialog = false">
      <div class="dialog" style="max-width:480px">
        <div class="dialog-header">
          <span>导入数据恢复</span>
          <button class="dialog-close" @click="showRestoreDialog = false; restorePreview = null; restoreError = ''">&times;</button>
        </div>
        <div class="dialog-body">
          <p style="color:#e6a23c;margin:0 0 12px;line-height:1.6">
            此操作将<strong>覆盖当前所有数据</strong>，请确认已导出最新备份。<br/>
            导入后不可撤销，建议先导出备份再操作。
          </p>
          <div class="field-group">
            <label>选择备份文件 (.json)</label>
            <input type="file" accept=".json" @change="onRestoreFile" ref="restoreFileInput" style="width:100%" />
          </div>
          <div v-if="restorePreview" style="margin:8px 0;padding:8px;background:#f5f7fa;border-radius:6px;font-size:12px;line-height:1.8">
            <div v-for="(info, tbl) in restorePreview" :key="tbl">{{ tbl }}: {{ info.count ?? 0 }} 条</div>
          </div>
          <div v-if="restoreError" style="color:#f56c6c;margin:8px 0;font-size:13px">{{ restoreError }}</div>
        </div>
        <div class="dialog-footer">
          <button class="btn btn-ghost" @click="showRestoreDialog = false; restorePreview = null; restoreError = ''">取消</button>
          <button class="btn btn-danger" @click="handleRestore" :disabled="restoreLoading || !restoreFileData">
            {{ restoreLoading ? '恢复中…' : '确认恢复' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/utils/request'

const activeTab = ref('types')
const keyword = ref('')
const saving = ref(false)
const loading = ref(false)

// 数据
const productTypes = ref([])
const brands = ref([])
const models = ref([])
const serviceTypes = ref([])
const serviceItems = ref([])
const priceOverrides = ref([])

// 筛选
const brandFilterType = ref('')
const modelFilterType = ref('')
const modelFilterBrand = ref('')
const serviceFilterType = ref('')
const itemFilterType = ref('')

// 计算属性
const activeTabLabel = computed(() => ({
  types: '产品类别', brands: '品牌', models: '型号',
  services: '服务类型', items: '维修检项'
}[activeTab.value] || ''))

const parseCats = (cats) => {
  if (!cats) return []
  try { return JSON.parse(cats) } catch { return [] }
}

const brandCountByType = computed(() => {
  const map = {}
  brands.value.forEach(b => { map[b.product_type_id] = (map[b.product_type_id] || 0) + 1 })
  return map
})
const serviceCountByType = computed(() => {
  const map = {}
  serviceTypes.value.forEach(s => { map[s.product_type_id] = (map[s.product_type_id] || 0) + 1 })
  return map
})
const modelCountByBrand = computed(() => {
  const map = {}
  models.value.forEach(m => { map[m.brand_id] = (map[m.brand_id] || 0) + 1 })
  return map
})
const overrideCountByService = computed(() => {
  const map = {}
  priceOverrides.value.forEach(o => { map[o.service_type_id] = (map[o.service_type_id] || 0) + 1 })
  return map
})

const filteredTypes = computed(() => {
  if (!keyword.value) return productTypes.value
  return productTypes.value.filter(t => t.name.includes(keyword.value))
})
const filteredBrands = computed(() => {
  let list = brands.value
  if (brandFilterType.value) list = list.filter(b => b.product_type_id == brandFilterType.value)
  if (keyword.value) list = list.filter(b => b.name.includes(keyword.value))
  return list
})
const filteredBrandsForModels = computed(() => {
  if (!modelFilterType.value) return brands.value
  return brands.value.filter(b => b.product_type_id == modelFilterType.value)
})
const filteredModels = computed(() => {
  let list = models.value
  if (modelFilterType.value) {
    const ids = brands.value.filter(b => b.product_type_id == modelFilterType.value).map(b => b.id)
    list = list.filter(m => ids.includes(m.brand_id))
  }
  if (modelFilterBrand.value) list = list.filter(m => m.brand_id == modelFilterBrand.value)
  if (keyword.value) list = list.filter(m => m.name.includes(keyword.value))
  return list
})
const filteredServices = computed(() => {
  let list = serviceTypes.value
  if (serviceFilterType.value) list = list.filter(s => s.product_type_id == serviceFilterType.value)
  if (keyword.value) list = list.filter(s => s.name.includes(keyword.value))
  return list
})
const filteredItems = computed(() => {
  let list = serviceItems.value
  if (itemFilterType.value) list = list.filter(i => i.product_type_id == itemFilterType.value)
  if (keyword.value) list = list.filter(i => i.name.includes(keyword.value))
  return list
})

const getTypeName = (id) => productTypes.value.find(t => t.id == id)?.name || '—'
const getBrandName = (id) => brands.value.find(b => b.id == id)?.name || '—'

const switchTab = (tab) => {
  activeTab.value = tab
  keyword.value = ''
}
const onSearch = () => {}

// ===== 加载数据 =====
const fetchAll = async () => {
  loading.value = true
  try {
    const [types, brandsData, modelsData, services, items, overrides] = await Promise.all([
      request.get('/admin/product-types'),
      request.get('/admin/brands'),
      request.get('/admin/models'),
      request.get('/admin/service-types'),
      request.get('/admin/service-items'),
      request.get('/admin/prices').catch(() => []),
    ])
    productTypes.value = Array.isArray(types) ? types : (types?.data || [])
    brands.value = Array.isArray(brandsData) ? brandsData : (brandsData?.data || [])
    models.value = Array.isArray(modelsData) ? modelsData : (modelsData?.data || [])
    serviceTypes.value = Array.isArray(services) ? services : (services?.data || [])
    serviceItems.value = Array.isArray(items) ? items : (items?.data || [])
    priceOverrides.value = Array.isArray(overrides) ? overrides : (overrides?.data || [])
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

// ===== 产品类别 =====
const typeDialog = reactive({ show: false, isEdit: false, form: {} })
const openTypeDialog = (row = null) => {
  if (row) {
    typeDialog.isEdit = true
    const cats = parseCats(row.categories)
    typeDialog.form = { ...row, categories_input: cats.join(',') }
  } else {
    typeDialog.isEdit = false
    typeDialog.form = { name: '', sort_order: 0, categories_input: '', is_active: 1 }
  }
  typeDialog.show = true
}
const saveType = async () => {
  if (!typeDialog.form.name?.trim()) { ElMessage.warning('请输入名称'); return }
  saving.value = true
  try {
    const cats = typeDialog.form.categories_input
      ? JSON.stringify(typeDialog.form.categories_input.split(',').map(s => s.trim()).filter(Boolean))
      : '[]'
    const payload = {
      name: typeDialog.form.name.trim(),
      sort_order: typeDialog.form.sort_order || 0,
      categories: cats,
      is_active: typeDialog.form.is_active
    }
    if (typeDialog.isEdit) {
      await request.put(`/admin/product-types/${typeDialog.form.id}`, payload)
    } else {
      await request.post('/admin/product-types', payload)
    }
    ElMessage.success('保存成功')
    typeDialog.show = false
    fetchAll()
  } catch (e) {
    ElMessage.error(e.message || '保存失败')
  } finally {
    saving.value = false
  }
}
const updateType = async (t) => {
  try {
    await request.put(`/admin/product-types/${t.id}`, {
      name: t.name, sort_order: t.sort_order,
      categories: t.categories || '[]', is_active: t.is_active
    })
  } catch (e) { ElMessage.error(e.message || '更新失败') }
}
const toggleType = async (t) => {
  try {
    await request.put(`/admin/product-types/${t.id}`, {
      name: t.name, sort_order: t.sort_order,
      categories: t.categories || '[]', is_active: t.is_active === 1 ? 0 : 1
    })
    t.is_active = t.is_active === 1 ? 0 : 1
    ElMessage.success(t.is_active === 1 ? '已启用' : '已禁用')
  } catch (e) { ElMessage.error(e.message || '操作失败') }
}
const deleteType = async (t) => {
  await ElMessageBox.confirm(`删除「${t.name}」？`, '提示', { type: 'warning' })
  try {
    await request.delete(`/admin/product-types/${t.id}`)
    ElMessage.success('已删除')
    fetchAll()
  } catch (e) { ElMessage.error(e.message || '删除失败') }
}

// ===== 品牌 =====
const brandDialog = reactive({ show: false, isEdit: false, form: {} })
const openBrandDialog = (row = null) => {
  if (row) {
    brandDialog.isEdit = true
    brandDialog.form = { ...row }
  } else {
    brandDialog.isEdit = false
    brandDialog.form = { name: '', product_type_id: '', website: '', country: '', notes: '', is_active: 1 }
  }
  brandDialog.show = true
}
const saveBrand = async () => {
  if (!brandDialog.form.name?.trim()) { ElMessage.warning('请输入品牌名称'); return }
  if (!brandDialog.form.product_type_id) { ElMessage.warning('请选择归属类型'); return }
  saving.value = true
  try {
    const payload = { ...brandDialog.form, name: brandDialog.form.name.trim() }
    if (brandDialog.isEdit) {
      await request.put(`/admin/brands/${brandDialog.form.id}`, payload)
    } else {
      await request.post('/admin/brands', payload)
    }
    ElMessage.success('保存成功')
    brandDialog.show = false
    fetchAll()
  } catch (e) {
    ElMessage.error(e.message || '保存失败')
  } finally {
    saving.value = false
  }
}
const toggleBrand = async (b) => {
  try {
    await request.put(`/admin/brands/${b.id}`, { ...b, is_active: b.is_active === 1 ? 0 : 1 })
    b.is_active = b.is_active === 1 ? 0 : 1
    ElMessage.success(b.is_active === 1 ? '已启用' : '已禁用')
  } catch (e) { ElMessage.error(e.message || '操作失败') }
}
const deleteBrand = async (b) => {
  await ElMessageBox.confirm(`删除「${b.name}」？`, '提示', { type: 'warning' })
  try {
    await request.delete(`/admin/brands/${b.id}`)
    ElMessage.success('已删除')
    fetchAll()
  } catch (e) { ElMessage.error(e.message || '删除失败') }
}

// ===== 型号 =====
const modelDialog = reactive({ show: false, isEdit: false, form: {} })
const openModelDialog = (row = null) => {
  if (row) {
    modelDialog.isEdit = true
    modelDialog.form = { ...row }
  } else {
    modelDialog.isEdit = false
    modelDialog.form = { brand_id: '', name: '', category: '', is_active: 1 }
  }
  modelDialog.show = true
}
const saveModel = async () => {
  if (!modelDialog.form.brand_id) { ElMessage.warning('请选择品牌'); return }
  if (!modelDialog.form.name?.trim()) { ElMessage.warning('请输入型号名称'); return }
  saving.value = true
  try {
    const payload = { ...modelDialog.form, name: modelDialog.form.name.trim() }
    if (modelDialog.isEdit) {
      await request.put(`/admin/models/${modelDialog.form.id}`, payload)
    } else {
      await request.post('/admin/models', payload)
    }
    ElMessage.success('保存成功')
    modelDialog.show = false
    fetchAll()
  } catch (e) {
    ElMessage.error(e.message || '保存失败')
  } finally {
    saving.value = false
  }
}
const toggleModel = async (m) => {
  try {
    await request.put(`/admin/models/${m.id}`, { ...m, is_active: m.is_active === 1 ? 0 : 1 })
    m.is_active = m.is_active === 1 ? 0 : 1
    ElMessage.success(m.is_active === 1 ? '已启用' : '已禁用')
  } catch (e) { ElMessage.error(e.message || '操作失败') }
}
const deleteModel = async (m) => {
  await ElMessageBox.confirm(`删除「${m.name}」？`, '提示', { type: 'warning' })
  try {
    await request.delete(`/admin/models/${m.id}`)
    ElMessage.success('已删除')
    fetchAll()
  } catch (e) { ElMessage.error(e.message || '删除失败') }
}

// ===== 服务类型 =====
const serviceDialog = reactive({ show: false, isEdit: false, form: {} })
const openServiceDialog = (row = null) => {
  if (row) {
    serviceDialog.isEdit = true
    serviceDialog.form = { ...row }
  } else {
    serviceDialog.isEdit = false
    serviceDialog.form = { name: '', product_type_id: '', description: '', base_price: 0, sort_order: 0, is_active: 1 }
  }
  serviceDialog.show = true
}
const saveService = async () => {
  if (!serviceDialog.form.name?.trim()) { ElMessage.warning('请输入服务名称'); return }
  if (!serviceDialog.form.product_type_id) { ElMessage.warning('请选择归属类型'); return }
  saving.value = true
  try {
    const payload = { ...serviceDialog.form, name: serviceDialog.form.name.trim() }
    if (serviceDialog.isEdit) {
      await request.put(`/admin/service-types/${serviceDialog.form.id}`, payload)
    } else {
      await request.post('/admin/service-types', payload)
    }
    ElMessage.success('保存成功')
    serviceDialog.show = false
    fetchAll()
  } catch (e) {
    ElMessage.error(e.message || '保存失败')
  } finally {
    saving.value = false
  }
}
const updateService = async (s) => {
  try {
    await request.put(`/admin/service-types/${s.id}`, {
      name: s.name, product_type_id: s.product_type_id,
      description: s.description, base_price: s.base_price,
      sort_order: s.sort_order, is_active: s.is_active
    })
  } catch (e) { ElMessage.error(e.message || '更新失败') }
}
const toggleService = async (s) => {
  try {
    await request.put(`/admin/service-types/${s.id}`, {
      name: s.name, product_type_id: s.product_type_id,
      description: s.description, base_price: s.base_price,
      sort_order: s.sort_order, is_active: s.is_active === 1 ? 0 : 1
    })
    s.is_active = s.is_active === 1 ? 0 : 1
    ElMessage.success(s.is_active === 1 ? '已启用' : '已禁用')
  } catch (e) { ElMessage.error(e.message || '操作失败') }
}
const deleteService = async (s) => {
  await ElMessageBox.confirm(`删除「${s.name}」？`, '提示', { type: 'warning' })
  try {
    await request.delete(`/admin/service-types/${s.id}`)
    ElMessage.success('已删除')
    fetchAll()
  } catch (e) { ElMessage.error(e.message || '删除失败') }
}

// ===== 维修检项 =====
const itemDialog = reactive({ show: false, isEdit: false, form: {} })
const openItemDialog = (row = null) => {
  if (row) {
    itemDialog.isEdit = true
    itemDialog.form = { ...row }
  } else {
    itemDialog.isEdit = false
    itemDialog.form = { product_type_id: '', name: '', description: '', is_required: 1, sort_order: 0, is_active: 1 }
  }
  itemDialog.show = true
}
const saveItem = async () => {
  if (!itemDialog.form.product_type_id) { ElMessage.warning('请选择产品类别'); return }
  if (!itemDialog.form.name?.trim()) { ElMessage.warning('请输入检项名称'); return }
  saving.value = true
  try {
    const payload = { ...itemDialog.form, name: itemDialog.form.name.trim() }
    if (itemDialog.isEdit) {
      await request.put(`/admin/service-items/${itemDialog.form.id}`, payload)
    } else {
      await request.post('/admin/service-items', payload)
    }
    ElMessage.success('保存成功')
    itemDialog.show = false
    fetchAll()
  } catch (e) {
    ElMessage.error(e.message || '保存失败')
  } finally {
    saving.value = false
  }
}
const updateItem = async (item) => {
  try {
    await request.put(`/admin/service-items/${item.id}`, {
      product_type_id: item.product_type_id, name: item.name,
      description: item.description, is_required: item.is_required,
      sort_order: item.sort_order, is_active: item.is_active
    })
  } catch (e) { ElMessage.error(e.message || '更新失败') }
}
const toggleItem = async (item) => {
  try {
    await request.put(`/admin/service-items/${item.id}`, {
      product_type_id: item.product_type_id, name: item.name,
      description: item.description, is_required: item.is_required,
      sort_order: item.sort_order, is_active: item.is_active === 1 ? 0 : 1
    })
    item.is_active = item.is_active === 1 ? 0 : 1
    ElMessage.success(item.is_active === 1 ? '已启用' : '已禁用')
  } catch (e) { ElMessage.error(e.message || '操作失败') }
}
const deleteItem = async (item) => {
  await ElMessageBox.confirm(`删除「${item.name}」？`, '提示', { type: 'warning' })
  try {
    await request.delete(`/admin/service-items/${item.id}`)
    ElMessage.success('已删除')
    fetchAll()
  } catch (e) { ElMessage.error(e.message || '删除失败') }
}

// ===== 品牌专属价 =====
const overrideDialog = reactive({ show: false, service: null, brands: [], overrides: {} })
const openOverrides = (service) => {
  overrideDialog.service = service
  overrideDialog.brands = brands.value.filter(b => b.product_type_id == service.product_type_id)
  overrideDialog.overrides = {}
  priceOverrides.value
    .filter(o => o.service_type_id == service.id)
    .forEach(o => { overrideDialog.overrides[o.brand_id] = o.price })
  overrideDialog.show = true
}
const saveOverride = async (brandId) => {
  const price = overrideDialog.overrides
  try {
    await request.post('/admin/prices', {
      product_type_id: overrideDialog.service.product_type_id,
      brand_id: brandId,
      service_type_id: overrideDialog.service.id,
      price: price || overrideDialog.service.base_price
    })
    // 更新本地缓存
    const exist = priceOverrides.value.find(o => o.service_type_id == overrideDialog.service.id && o.brand_id == brandId)
    if (exist) exist.price = price
    else priceOverrides.value.push({ service_type_id: overrideDialog.service.id, brand_id: brandId, price })
    ElMessage.success('价格已保存')
  } catch (e) { ElMessage.error(e.message || '保存失败') }
}

// ── 数据备份与恢复 ──
const backupLoading = ref(false)
const showRestoreDialog = ref(false)
const restoreLoading = ref(false)
const restoreFileData = ref(null)
const restorePreview = ref(null)
const restoreError = ref('')
const restoreFileInput = ref(null)

async function handleBackup() {
  backupLoading.value = true
  try {
    const response = await request.get('/admin/backup', { responseType: 'blob' })
    const blob = response.data instanceof Blob ? response.data : new Blob([response.data], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    // 尝试从 Content-Disposition 获取文件名
    const cd = response.headers?.['content-disposition'] || ''
    const match = cd.match(/filename="?(.+?)"?$/)
    a.download = match ? match[1] : `selforder_backup_${new Date().toISOString().slice(0,19).replace(/[:]/g,'-')}.json`
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('备份文件已下载')
  } catch (e) {
    ElMessage.error('导出失败: ' + (e.message || '未知错误'))
  } finally {
    backupLoading.value = false
  }
}

function onRestoreFile(e) {
  const file = e.target.files[0]
  if (!file) { restoreFileData.value = null; restorePreview.value = null; return }
  restoreError.value = ''
  const reader = new FileReader()
  reader.onload = (ev) => {
    try {
      const data = JSON.parse(ev.target.result)
      if (!data.tables) throw new Error('无效的备份文件格式')
      restoreFileData.value = data
      // 预览各表记录数
      const preview = {}
      for (const [tbl, rows] of Object.entries(data.tables)) {
        preview[tbl] = Array.isArray(rows) ? { count: rows.length } : { count: 0 }
      }
      restorePreview.value = preview
    } catch (err) {
      restoreError.value = '文件解析失败: ' + err.message
      restoreFileData.value = null
      restorePreview.value = null
    }
  }
  reader.readAsText(file)
}

async function handleRestore() {
  if (!restoreFileData.value) return
  try {
    await ElMessageBox.confirm(
      '确认要覆盖当前所有数据吗？此操作不可撤销！',
      '危险操作', { confirmButtonText: '确认恢复', cancelButtonText: '取消', type: 'warning' }
    )
  } catch { return }
  restoreLoading.value = true
  restoreError.value = ''
  try {
    const res = await request.post('/admin/backup/restore', {
      confirm: true,
      tables: restoreFileData.value.tables
    })
    if (res.success) {
      ElMessage.success('数据恢复完成')
      showRestoreDialog.value = false
      restorePreview.value = null
      restoreFileData.value = null
      await fetchAll()
    } else {
      restoreError.value = res.message || '恢复失败'
    }
  } catch (e) {
    restoreError.value = e.message || '恢复失败'
  } finally {
    restoreLoading.value = false
  }
}

onMounted(fetchAll)
</script>

<style scoped>
/* ===== 对话框 ===== */
.dialog-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,.45);
  display: flex; align-items: center; justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(2px);
}
.dialog {
  background: #fff;
  border-radius: 14px;
  width: 460px;
  max-width: 95vw;
  box-shadow: 0 20px 60px rgba(0,0,0,.2);
  overflow: hidden;
}
.dialog-wide { width: 640px; }
.dialog-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 18px 20px;
  border-bottom: 1px solid var(--border);
  font-size: 15px; font-weight: 700;
}
.dialog-close {
  background: none; border: none; cursor: pointer;
  font-size: 22px; color: #9ca3af;
  padding: 0 4px;
}
.dialog-close:hover { color: var(--text); }
.dialog-body { padding: 20px; max-height: 70vh; overflow-y: auto; }
.dialog-footer {
  padding: 14px 20px;
  border-top: 1px solid var(--border);
  display: flex; align-items: center; justify-content: flex-end; gap: 8px;
}

/* ===== 表单 ===== */
.form-field { display: flex; flex-direction: column; }
.form-input {
  width: 100%;
  padding: 9px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  font-size: 14px;
  outline: none;
  transition: all .15s;
  background: #fff;
}
.form-input:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(79,70,229,.1);
}
textarea.form-input { resize: vertical; }
.form-hint-inline { font-size: 11px; font-weight: 400; color: var(--text-secondary); }

/* ===== 内联输入 ===== */
.inline-input {
  width: 60px;
  padding: 4px 8px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-size: 13px;
  text-align: center;
  outline: none;
}
.inline-input:focus { border-color: var(--primary); }

/* ===== 价格标签 ===== */
.price-tag { font-weight: 700; color: #d97706; font-size: 14px; }

/* ===== 品牌专属价网格 ===== */
.override-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
.override-item {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 14px;
  background: #f9fafb;
  border-radius: 10px;
  border: 1px solid #f3f4f6;
}
.override-brand { display: flex; flex-direction: column; gap: 4px; }
.override-type { font-size: 11px; color: var(--text-secondary); }
.override-price { display: flex; align-items: center; gap: 6px; }
.override-base { font-size: 12px; color: #9ca3af; text-decoration: line-through; }
.override-input {
  width: 80px; padding: 5px 8px;
  border: 1px solid #e5e7eb; border-radius: 6px;
  font-size: 14px; text-align: center; outline: none;
}
.override-input:focus { border-color: var(--primary); }
.override-diff { font-size: 11px; font-weight: 700; color: #d97706; }
.override-legend { font-size: 12px; color: var(--text-secondary); flex: 1; }

/* ===== 辅助 ===== */
.text-muted { color: var(--text-secondary); }
.f12 { font-size: 12px; }
.type-name { font-weight: 700; }
.link { color: var(--primary); text-decoration: none; font-size: 13px; }
.link:hover { text-decoration: underline; }
.filter-select {
  padding: 6px 10px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  font-size: 13px;
  background: #fff;
  outline: none;
  cursor: pointer;
}
.filter-select:focus { border-color: var(--primary); }

@media (max-width: 768px) {
  .override-grid { grid-template-columns: 1fr; }
  .dialog { width: 95vw; }
}
</style>
