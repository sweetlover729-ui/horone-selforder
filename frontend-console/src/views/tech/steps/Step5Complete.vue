<template>
  <template v-if="!stepSubmitted">
    <div class="section-title">订单完成</div>
    <div class="alert-box warning">
      <p>确认后订单将标记为<strong>已完成</strong>，系统自动推送微信通知给客户，客户即可查看和下载PDF维修报告。</p>
    </div>
    <div class="field-group">
      <label>完成备注（可选）</label>
      <textarea v-model="note" class="textarea-input" rows="2" placeholder="如：客户确认收货"></textarea>
    </div>
    <div class="page-nav">
      <button class="back-link" @click="goBack()">返回上一步</button>
      <div class="btn-group">
        <button class="secondary-btn" @click="previewPdf" :disabled="pdfLoading">
          {{ pdfLoading ? '生成中...' : '预览报告' }}
        </button>
        <button class="primary-btn success" @click="submitGeneric('complete')" :disabled="submitting">
          {{ submitting ? '提交中...' : '确认完成' }}
        </button>
      </div>
    </div>
  </template>
  <template v-if="stepSubmitted">
    <div class="alert-box success">
      <p>订单已完成！PDF维修报告已生成，客户微信端已收到通知。</p>
    </div>
    <div class="completed-summary" v-if="allNodes.length">
      <div class="summary-title">维修记录摘要</div>
      <div v-for="node in allNodes" :key="node.id" class="summary-item">
        <div class="summary-node-name">{{ node.node_name }}</div>
        <div class="summary-node-time">{{ node.operate_time?.substring(0, 16) }}</div>
        <div v-if="node.operate_note" class="summary-node-note">{{ node.operate_note }}</div>
      </div>
    </div>
    <div class="page-nav">
      <button class="back-link" @click="goBack()">返回上一步</button>
      <button class="primary-btn" @click="downloadPdf" :disabled="pdfLoading">
        {{ pdfLoading ? '生成中...' : '下载PDF报告' }}
      </button>
    </div>
  </template>
</template>

<script setup>
import { useWorkflow } from '@/composables/useTechWorkflow'
const { stepSubmitted, note, allNodes, submitting, pdfLoading,
  goBack, previewPdf, downloadPdf, submitGeneric } = useWorkflow()
</script>
