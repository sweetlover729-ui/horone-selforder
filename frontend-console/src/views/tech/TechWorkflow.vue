<template>
  <div class="tech-workflow">
    <!-- 步骤进度条 -->
    <div class="step-progress">
      <div v-for="(s, i) in STEPS" :key="i" :class="['step-item', { done: isStepDone(i), active: stepIndex === i }]">
        <div class="step-circle">
          <span v-if="isStepDone(i)">OK</span>
          <span v-else>{{ i + 1 }}</span>
        </div>
        <div class="step-label">{{ s.shortLabel }}</div>
      </div>
    </div>

    <!-- 订单信息栏 -->
    <div v-if="orderData" class="order-info-bar">
      <div class="order-info-left">
        <span class="order-no">订单号：{{ orderData.order_no }}</span>
        <span class="customer-name">客户：{{ orderData.customer_name }}</span>
      </div>
      <div class="order-info-right">
        <span v-if="orderData.urgent_service" class="urgent-badge">加急订单</span>
      </div>
    </div>

    <!-- 步骤卡片 -->
    <div class="step-card">
      <div class="step-header">
        <div>
          <h3 class="step-title">{{ currentStep.label }}</h3>
          <p class="step-desc">{{ currentStep.desc }}</p>
        </div>
        <span v-if="stepSubmitted" class="status-tag done">已完成</span>
        <span v-else class="status-tag pending">待操作</span>
      </div>

      <!-- 按 stepIndex 渲染对应步骤组件 -->
      <Step0Receive v-if="stepIndex === 0" />
      <Step1Inspect v-if="stepIndex === 1" />
      <Step2Repair v-if="stepIndex === 2" />
      <Step3QC v-if="stepIndex === 3" />
      <Step4Ship v-if="stepIndex === 4" />
      <Step5Complete v-if="stepIndex === 5" />
    </div>

    <!-- 照片预览弹窗 -->
    <div v-if="previewUrl" class="preview-modal" @click="previewUrl = ''">
      <img :src="previewUrl" />
    </div>
  </div>
</template>

<script setup>
import { watch } from 'vue'
import { useTechWorkflow } from '@/composables/useTechWorkflow'
import Step0Receive from './steps/Step0Receive.vue'
import Step1Inspect from './steps/Step1Inspect.vue'
import Step2Repair from './steps/Step2Repair.vue'
import Step3QC from './steps/Step3QC.vue'
import Step4Ship from './steps/Step4Ship.vue'
import Step5Complete from './steps/Step5Complete.vue'

const {
  STEPS, stepIndex, stepSubmitted, orderData, currentStep, previewUrl,
  isStepDone
} = useTechWorkflow()

// 监听路由参数变化（Vue router 复用组件时重置所有状态）
// route/loadOrder 在 composable 内通过 onMounted 调用
</script>

<style>
.tech-workflow { padding: 12px; max-width: 500px; margin: 0 auto; padding-bottom: 80px; }

/* 步骤进度 */
.step-progress { display: flex; gap: 0; margin-bottom: 16px; }
.step-item { flex: 1; display: flex; flex-direction: column; align-items: center; }
.step-circle {
  width: 26px; height: 26px; border-radius: 50%;
  background: #e8e8e8; color: #aaa;
  display: flex; align-items: center; justify-content: center;
  font-size: 11px; font-weight: 600;
}
.step-item.done .step-circle { background: #67c23a; color: #fff; }
.step-item.active .step-circle { background: #409eff; color: #fff; }
.step-label { font-size: 10px; margin-top: 4px; color: #999; white-space: nowrap; }
.step-item.active .step-label { color: #409eff; font-weight: 600; }
.step-item.done .step-label { color: #67c23a; }

/* 步骤卡片 */
.step-card {
  background: #fff; border-radius: 12px; padding: 16px;
  box-shadow: 0 1px 6px rgba(0,0,0,0.06);
}
.step-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px; }
.step-title { margin: 0; font-size: 16px; color: #303133; }
.step-desc { margin: 4px 0 0; color: #909399; font-size: 12px; }
.status-tag { font-size: 11px; padding: 2px 8px; border-radius: 10px; flex-shrink: 0; }
.status-tag.done { background: #e8f7e8; color: #67c23a; }
.status-tag.pending { background: #fdf6ec; color: #e6a23c; }

.section-title { font-size: 15px; font-weight: 600; color: #303133; margin-bottom: 12px; }
.sub-desc { color: #909399; font-size: 12px; margin-bottom: 12px; }

/* 表单 */
.field-group { margin-bottom: 14px; }
.field-group > label { display: block; font-size: 13px; color: #606266; margin-bottom: 6px; font-weight: 500; }
.text-input, .select-input, .textarea-input {
  width: 100%; padding: 10px 12px;
  border: 1px solid #dcdfe6; border-radius: 8px;
  font-size: 14px; box-sizing: border-box;
  -webkit-appearance: none; appearance: none;
}
.text-input:focus, .select-input:focus, .textarea-input:focus { border-color: #409eff; outline: none; }
.textarea-input { resize: vertical; font-family: inherit; }
.select-input { background: #fff; }

/* 外包装选择 */
.radio-group { display: flex; gap: 10px; }
.radio-item {
  flex: 1; padding: 12px; text-align: center;
  border: 2px solid #e8e8e8; border-radius: 10px; cursor: pointer;
  font-size: 13px; color: #606266; transition: all 0.2s;
}
.radio-item.active { border-color: #409eff; color: #409eff; background: #ecf5ff; }
.radio-icon { font-size: 14px; display: block; margin-bottom: 4px; color: #909399; }
.radio-item.active .radio-icon { color: #409eff; }

/* 照片上传 */
.upload-area {
  border: 2px dashed #dcdfe6; border-radius: 10px;
  padding: 8px; min-height: 120px; cursor: pointer;
  display: flex; flex-wrap: wrap; gap: 8px; align-items: center;
  justify-content: center;
}
.upload-area.multi { min-height: 100px; flex-wrap: wrap; }
.upload-placeholder {
  display: flex; flex-direction: column; align-items: center; gap: 4px;
  color: #c0c4cc; font-size: 13px; padding: 20px;
}
.upload-placeholder.mini { padding: 10px; width: 80px; height: 80px; }
.upload-icon { font-size: 20px; color: #c0c4cc; }
.preview-img { max-width: 100%; max-height: 200px; border-radius: 8px; object-fit: cover; }
.multi-preview {
  position: relative; width: 80px; height: 80px; border-radius: 6px; overflow: hidden;
}
.multi-preview img { width: 100%; height: 100%; object-fit: cover; }
.remove-btn {
  position: absolute; top: 2px; right: 2px;
  width: 20px; height: 20px; border-radius: 50%;
  background: rgba(245,108,108,0.9); color: #fff;
  border: none; font-size: 12px; line-height: 1; cursor: pointer; padding: 0;
}

.text-btn { background: none; border: none; color: #409eff; font-size: 12px; cursor: pointer; padding: 4px 0; }
.text-btn.danger { color: #f56c6c; }

/* 已提交状态 */
.done-info { background: #f8f9fa; border-radius: 8px; padding: 12px; margin-bottom: 12px; }
.info-row { font-size: 13px; color: #606266; margin-bottom: 4px; }
.info-row span { font-weight: 500; color: #303133; }
.photo-section > label { display: block; font-size: 13px; color: #606266; margin-bottom: 8px; font-weight: 500; }
.photo-grid { display: flex; flex-wrap: wrap; gap: 8px; }
.photo-item { position: relative; width: 80px; height: 80px; border-radius: 6px; overflow: hidden; }
.photo-item img { width: 100%; height: 100%; object-fit: cover; cursor: pointer; }
.delete-btn {
  position: absolute; top: 2px; right: 2px;
  width: 20px; height: 20px; border-radius: 50%;
  background: rgba(245,108,108,0.9); color: #fff;
  border: none; font-size: 12px; line-height: 1; cursor: pointer; padding: 0;
}

/* 提示框 */
.alert-box { padding: 12px; border-radius: 8px; margin-bottom: 14px; font-size: 13px; }
.alert-box.warning { background: #fdf6ec; color: #e6a23c; border-left: 3px solid #e6a23c; }
.alert-box.success { background: #f0f9eb; color: #67c23a; border-left: 3px solid #67c23a; }

/* 按钮 */
.page-nav { display: flex; justify-content: space-between; align-items: center; margin-top: 16px; padding-top: 12px; border-top: 1px solid #f0f0f0; }
.primary-btn {
  padding: 10px 20px; border-radius: 8px; font-size: 14px;
  cursor: pointer; border: none; font-weight: 500;
  background: #409eff; color: #fff;
}
.primary-btn:disabled { background: #c0c4cc; cursor: not-allowed; }
.primary-btn.success { background: #67c23a; }
.secondary-btn {
  padding: 10px 20px; border-radius: 8px; font-size: 14px;
  cursor: pointer; border: 1px solid #409eff; font-weight: 500;
  background: #fff; color: #409eff;
}
.secondary-btn:disabled { border-color: #c0c4cc; color: #c0c4cc; cursor: not-allowed; }
.secondary-btn:hover:not(:disabled) { background: #ecf5ff; }
.btn-group { display: flex; gap: 10px; }
.back-link { background: none; border: none; color: #909399; font-size: 13px; cursor: pointer; }
.back-link:hover { color: #409eff; }
.mt { margin-top: 12px; }

/* 照片预览弹窗 */
.preview-modal {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.85);
  display: flex; align-items: center; justify-content: center;
  z-index: 1000;
}
.preview-modal img { max-width: 95%; max-height: 90%; border-radius: 4px; }

/* 完成摘要 */
.completed-summary {
  background: #f8f9fa; border-radius: 12px; padding: 16px; margin: 16px 0;
}
.summary-title {
  font-size: 15px; font-weight: 600; color: #303133; margin-bottom: 12px;
  padding-bottom: 8px; border-bottom: 1px solid #e4e7ed;
}
.summary-item {
  padding: 10px 0; border-bottom: 1px solid #ebeef5;
}
.summary-item:last-child { border-bottom: none; }
.summary-node-name {
  font-size: 14px; font-weight: 500; color: #303133;
}
.summary-node-time {
  font-size: 12px; color: #909399; margin-top: 2px;
}
.summary-node-note {
  font-size: 13px; color: #606266; margin-top: 4px;
  background: #fff; padding: 8px; border-radius: 6px;
}

/* 子页面标签 */
.subpage-tabs {
  display: flex; gap: 0; margin-bottom: 16px;
  background: #f5f7fa; border-radius: 8px; overflow: hidden;
}
.tab-btn {
  flex: 1; padding: 10px 12px; font-size: 13px;
  border: none; background: transparent; color: #909399; cursor: pointer;
  transition: all 0.2s;
}
.tab-btn.active {
  background: #409eff; color: #fff; font-weight: 500;
}
.tab-btn:hover:not(.active) {
  background: #e8e8e8;
}

/* 空提示 */
.empty-hint {
  color: #c0c4cc; font-size: 13px; text-align: center; padding: 20px 0;
}

/* 已上传照片（编辑模式预填充） */
.existing-photos-section {
  margin-bottom: 14px;
  padding: 10px;
  background: #f0f9eb;
  border-radius: 8px;
  border: 1px solid #e1f3d8;
}
.existing-photos-section > label {
  display: block;
  font-size: 12px;
  color: #67c23a;
  margin-bottom: 8px;
  font-weight: 500;
}
.existing-photos-section .photo-item {
  cursor: pointer;
}

/* 设备信息录入样式 */
.equipment-item {
  background: #f8f9fa;
  border-radius: 10px;
  padding: 14px;
  margin-bottom: 14px;
}
.equipment-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e4e7ed;
}
.equipment-name {
  font-weight: 600;
  font-size: 14px;
  color: #303133;
}
.equipment-type {
  font-size: 12px;
  color: #909399;
  background: #ecf5ff;
  padding: 2px 8px;
  border-radius: 4px;
}
.sub-field-group {
  background: #fff;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 10px;
  border: 1px solid #e4e7ed;
}
.field-row {
  display: flex;
  gap: 10px;
  margin-bottom: 8px;
}
.field-col {
  flex: 1;
}
.field-col label {
  font-size: 12px;
  color: #606266;
  margin-bottom: 4px;
  display: block;
}

.multi-line-label {
  line-height: 1.4;
}

/* 设备信息摘要 */
.equipment-summary {
  background: #f8f9fa;
  border-radius: 10px;
  padding: 14px;
  margin-top: 14px;
}
.equipment-summary-item {
  background: #fff;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 10px;
  border: 1px solid #e4e7ed;
}
.equipment-summary-item:last-child {
  margin-bottom: 0;
}
.summary-header {
  font-weight: 600;
  font-size: 14px;
  color: #303133;
  margin-bottom: 8px;
  padding-bottom: 6px;
  border-bottom: 1px solid #f0f0f0;
}
.summary-row {
  font-size: 13px;
  color: #606266;
  margin: 6px 0;
  font-weight: 500;
}
.summary-detail {
  font-size: 12px;
  color: #909399;
  margin: 4px 0 4px 12px;
  font-family: monospace;
}

/* 订单信息栏 */
.order-info-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #fff;
  border-radius: 10px;
  padding: 12px 16px;
  margin: 0 0 12px 0;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.order-info-left {
  display: flex;
  gap: 16px;
  align-items: center;
}
.order-no {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}
.customer-name {
  font-size: 13px;
  color: #606266;
}
.urgent-badge {
  background: #fef0f0;
  color: #f56c6c;
  border: 1px solid #fde2e2;
  padding: 4px 12px;
  border-radius: 16px;
  font-size: 13px;
  font-weight: 600;
  animation: urgent-pulse 2s infinite;
}
@keyframes urgent-pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

/* 维修检项多选 */
.checklist-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.checklist-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 5px 12px;
  border: 1px solid #dcdfe6;
  border-radius: 16px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
  user-select: none;
}
.checklist-item:hover { border-color: #409eff; }
.checklist-item.checked {
  background: #ecf5ff;
  border-color: #409eff;
  color: #409eff;
}
.checklist-item input[type="checkbox"] { display: none; }
.checklist-name { pointer-events: none; }
</style>
