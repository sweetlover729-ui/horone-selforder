<template>
  <template v-if="!stepSubmitted">
    <div class="section-title">维修保养</div>
    <p class="sub-desc">按维修清单操作，更换磨损配件，填写维修记录，上传过程照片</p>
    <div v-if="photos.length" class="existing-photos-section">
      <label>已上传的维修照片</label>
      <div class="photo-grid">
        <div v-for="(p, i) in photos" :key="'ex-repair-'+i" class="photo-item" @click="previewUrl = p.url">
          <img :src="p.url" />
        </div>
      </div>
    </div>
    <div class="field-group" v-if="serviceItems.length">
      <label>维修检项（可多选）</label>
      <div class="checklist-grid">
        <label v-for="item in serviceItems" :key="item.id" class="checklist-item" :class="{ checked: selectedServiceItems.includes(item.id) }">
          <input type="checkbox" :value="item.id" v-model="selectedServiceItems" />
          <span class="checklist-name">{{ item.name }}</span>
        </label>
      </div>
    </div>
    <div v-if="serviceLoadFailed" class="field-group">
      <label style="color: #e6a23c;">⚠ 维修检项加载失败</label>
      <p style="color: #999; font-size: 13px; margin-top: 4px;">请检查网络或返回订单列表重新进入，如问题持续请确认数据管理中已配置该产品类别的维修检项。</p>
      <button class="retry-link" @click="loadServiceItems(orderData)">重新加载</button>
    </div>
    <div class="field-group">
      <label>维修内容</label>
      <textarea v-model="note" class="textarea-input" rows="4" placeholder="如：已更换O型圈全套，超声波清洗一级头，二级头校准呼吸阻力"></textarea>
    </div>
    <div class="field-group">
      <label>{{ photos.length ? '添加更多维修照片' : '维修过程照片（可多张）' }}</label>
      <div class="upload-area multi" @click="triggerUploadMulti('repair')">
        <div v-for="(p, i) in localMultiPhotos.repair" :key="i" class="multi-preview">
          <img :src="p" />
          <button class="remove-btn" @click.stop="localMultiPhotos.repair.splice(i, 1)">x</button>
        </div>
        <div class="upload-placeholder mini">
          <span class="upload-icon">[+]</span>
          <span>添加照片</span>
        </div>
      </div>
    </div>
    <div class="page-nav">
      <button class="back-link" @click="goBack">返回上一步</button>
      <button class="primary-btn" @click="submitGeneric('repair')" :disabled="submitting">
        {{ submitting ? '提交中...' : '提交维修记录' }}
      </button>
    </div>
  </template>

  <template v-if="stepSubmitted">
    <div class="done-info" v-if="nodeData">
      <div v-if="nodeData.description && nodeData.description.startsWith('维修检项：')" class="info-row">
        <span>维修检项：</span>{{ nodeData.description.replace('维修检项：', '') }}
      </div>
      <div v-if="nodeData.operate_note" class="info-row"><span>维修内容：</span>{{ nodeData.operate_note }}</div>
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
const { stepSubmitted, serviceItems, selectedServiceItems, serviceLoadFailed,
  photos, note, previewUrl, nodeData, orderData, localMultiPhotos, submitting, isLastStep,
  loadServiceItems, triggerUploadMulti, goBack, nextStep, submitGeneric, deletePhoto } = useWorkflow()
</script>
