<template>
  <template v-if="!stepSubmitted">
    <div class="section-title">质检通过</div>
    <p class="sub-desc">全面功能测试，记录测试结果，系统自动生成PDF维修报告</p>
    <div v-if="photos.length" class="existing-photos-section">
      <label>已上传的质检照片</label>
      <div class="photo-grid">
        <div v-for="(p, i) in photos" :key="'ex-qc-'+i" class="photo-item" @click="previewUrl = p.url">
          <img :src="p.url" />
        </div>
      </div>
    </div>
    <div class="field-group">
      <label>质检结果</label>
      <textarea v-model="note" class="textarea-input" rows="4" placeholder="如：气密性测试通过（9Bar/5min无泄漏），呼吸阻力12-15cmH2O达标"></textarea>
    </div>
    <div class="field-group">
      <label>{{ photos.length ? '添加更多质检照片' : '质检照片（可多张）' }}</label>
      <div class="upload-area multi" @click="triggerUploadMulti('qc')">
        <div v-for="(p, i) in localMultiPhotos.qc" :key="i" class="multi-preview">
          <img :src="p" />
          <button class="remove-btn" @click.stop="localMultiPhotos.qc.splice(i, 1)">x</button>
        </div>
        <div class="upload-placeholder mini">
          <span class="upload-icon">[+]</span>
          <span>添加照片</span>
        </div>
      </div>
    </div>
    <div class="page-nav">
      <button class="back-link" @click="goBack">返回上一步</button>
      <button class="primary-btn" @click="submitGeneric('qc')" :disabled="submitting">
        {{ submitting ? '提交中...' : '提交质检' }}
      </button>
    </div>
  </template>

  <template v-if="stepSubmitted">
    <div class="done-info" v-if="nodeData">
      <div v-if="nodeData.operate_note" class="info-row"><span>质检结果：</span>{{ nodeData.operate_note }}</div>
    </div>
    <div class="photo-section">
      <label>已上传照片</label>
      <div class="photo-grid">
        <div v-for="(p, i) in photos" :key="i" class="photo-item">
          <img :src="p.url" @click="previewUrl = p.url" />
          <button class="delete-btn" @click="deletePhoto(i)">x</button>
        </div>
      </div>
      <div class="page-nav">
        <button class="back-link" @click="goBack">返回上一步</button>
        <button v-if="!isLastStep" class="primary-btn" @click="nextStep">下一步</button>
      </div>
    </div>
  </template>
</template>

<script setup>
import { useWorkflow } from '@/composables/useTechWorkflow'
const { stepSubmitted, photos, note, previewUrl, nodeData, localMultiPhotos, submitting, isLastStep,
  triggerUploadMulti, goBack, nextStep, submitGeneric, deletePhoto } = useWorkflow()
</script>
