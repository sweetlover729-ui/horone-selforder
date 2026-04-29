<template>
  <template v-if="!stepSubmitted">
    <div class="section-title">设备发出</div>
    <p class="sub-desc">填写回寄快递信息，上传打包照片</p>
    <div class="section-title" style="margin-top: 0; margin-bottom: 16px;">
      <button class="secondary-btn" @click="previewPdf" :disabled="pdfLoading">
        {{ pdfLoading ? '生成中...' : '预览维修报告' }}
      </button>
    </div>
    <div class="field-group">
      <label>快递公司 <span style="color:#e6a23c;font-size:12px;">(公司规定：必须使用顺丰速运)</span></label>
      <select v-model="formData.shipCompany" class="select-input">
        <option value="">请选择</option>
        <option v-for="c in returnCourierList" :key="c" :value="c">{{ c }}</option>
      </select>
    </div>
    <div class="field-group">
      <label>快递单号 <span style="color:#909399;font-size:12px;">(顺丰取件后补填)</span></label>
      <input v-model="formData.shipNo" type="text" class="text-input" placeholder="待顺丰取件后填写" />
    </div>
    <div v-if="photos.length" class="existing-photos-section">
      <label>已上传的发货照片</label>
      <div class="photo-grid">
        <div v-for="(p, i) in photos" :key="'ex-ship-'+i" class="photo-item" @click="previewUrl = p.url">
          <img :src="p.url" />
        </div>
      </div>
    </div>
    <div class="field-group">
      <label>{{ photos.length ? '添加更多发货照片' : '打包发出照片（可选）' }}</label>
      <div class="upload-area" @click="triggerUpload('ship')">
        <img v-if="localPhotos.ship" :src="localPhotos.ship" class="preview-img" />
        <div v-else class="upload-placeholder">
          <span class="upload-icon">[+]</span>
          <span>点击拍照/选择照片</span>
        </div>
      </div>
      <button v-if="localPhotos.ship" class="text-btn danger" @click="localPhotos.ship = null">移除照片</button>
    </div>
    <div class="field-group">
      <label>备注（可选）</label>
      <textarea v-model="note" class="textarea-input" rows="2" placeholder="备注信息"></textarea>
    </div>
    <div class="page-nav">
      <button class="back-link" @click="goBack">返回上一步</button>
      <button class="primary-btn" @click="submitShip" :disabled="submitting">
        {{ submitting ? '提交中...' : '确认发出' }}
      </button>
    </div>
  </template>

  <template v-if="stepSubmitted">
    <div class="done-info" v-if="nodeData">
      <div v-if="nodeData.express_company" class="info-row"><span>快递：</span>{{ nodeData.express_company }} {{ nodeData.express_no }}</div>
      <div v-if="nodeData.operate_note" class="info-row"><span>备注：</span>{{ nodeData.operate_note }}</div>
    </div>
    <div class="section-title" style="margin-top: 16px;">
      <button class="secondary-btn" @click="previewPdf" :disabled="pdfLoading">
        {{ pdfLoading ? '生成中...' : '预览维修报告' }}
      </button>
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
const { stepSubmitted, formData, returnCourierList, photos, note, previewUrl,
  nodeData, localPhotos, submitting, isLastStep, pdfLoading,
  triggerUpload, goBack, nextStep, submitShip, previewPdf, deletePhoto } = useWorkflow()
</script>
