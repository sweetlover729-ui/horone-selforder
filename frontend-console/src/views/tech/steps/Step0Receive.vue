<template>
  <!-- 子页1: 快递信息 + 未拆包装照片 -->
  <template v-if="!stepSubmitted && subPageIndex === 0">
    <div class="section-title">快递信息</div>
    <div class="field-group">
      <label>快递公司</label>
      <select v-model="formData.expressCompany" class="select-input">
        <option value="">请选择</option>
        <option v-for="c in courierList" :key="c" :value="c">{{ c }}</option>
      </select>
    </div>
    <div class="field-group">
      <label>快递单号</label>
      <input v-model="formData.expressNo" type="text" class="text-input" placeholder="输入快递单号" />
    </div>
    <div class="field-group">
      <label>外包装情况</label>
      <div class="radio-group">
        <label class="radio-item" :class="{ active: formData.packaging === '完好' }" @click="formData.packaging = '完好'">
          <span class="radio-icon">[完好]</span> 邮包完好
        </label>
        <label class="radio-item" :class="{ active: formData.packaging === '破损' }" @click="formData.packaging = '破损'">
          <span class="radio-icon">[破损]</span> 邮包破损
        </label>
      </div>
    </div>
    <div v-if="photos.filter(p => p.type === 'unbox').length" class="existing-photos-section">
      <label>已上传的未拆包照片</label>
      <div class="photo-grid">
        <div v-for="(p, i) in photos.filter(p => p.type === 'unbox')" :key="'ex-unbox-'+i" class="photo-item" @click="previewUrl = p.url">
          <img :src="p.url" />
        </div>
      </div>
    </div>
    <div class="field-group">
      <label>{{ photos.filter(p => p.type === 'unbox').length ? '替换未拆包照片' : '未拆邮包照片（外包装整体照片）' }}</label>
      <div class="upload-area" @click="triggerUpload('unbox')">
        <img v-if="localPhotos.unbox" :src="localPhotos.unbox" class="preview-img" />
        <div v-else class="upload-placeholder">
          <span class="upload-icon">[+]</span>
          <span>点击拍照/选择照片</span>
        </div>
      </div>
      <button v-if="localPhotos.unbox" class="text-btn danger" @click="localPhotos.unbox = null">移除照片</button>
    </div>
    <div class="page-nav">
      <button class="back-link" @click="goBack">返回订单列表</button>
      <button class="primary-btn" @click="goForwardSub(subPageIndex, 1)">下一步：拆邮包照片</button>
    </div>
  </template>

  <!-- 子页2: 拆邮包照片 -->
  <template v-if="!stepSubmitted && subPageIndex === 1">
    <div class="section-title">拆邮包照片</div>
    <p class="sub-desc">请拆开外包装后，拍摄设备在邮包内的状态照片</p>
    <div v-if="photos.filter(p => p.type === 'unbox_opened').length" class="existing-photos-section">
      <label>已上传的拆包照片</label>
      <div class="photo-grid">
        <div v-for="(p, i) in photos.filter(p => p.type === 'unbox_opened')" :key="'ex-open-'+i" class="photo-item" @click="previewUrl = p.url">
          <img :src="p.url" />
        </div>
      </div>
    </div>
    <div class="field-group">
      <label>{{ photos.filter(p => p.type === 'unbox_opened').length ? '替换拆包照片' : '拆邮包后的照片（设备在包装内的状态）' }}</label>
      <div class="upload-area" @click="triggerUpload('unbox_opened')">
        <img v-if="localPhotos.unbox_opened" :src="localPhotos.unbox_opened" class="preview-img" />
        <div v-else class="upload-placeholder">
          <span class="upload-icon">[+]</span>
          <span>点击拍照/选择照片</span>
        </div>
      </div>
      <button v-if="localPhotos.unbox_opened" class="text-btn danger" @click="localPhotos.unbox_opened = null">移除照片</button>
    </div>
    <div class="field-group">
      <label>备注（可选）</label>
      <textarea v-model="note" class="textarea-input" rows="3" placeholder="如：邮包内部有防震气泡，设备本体无明显外伤"></textarea>
    </div>
    <div class="page-nav">
      <button class="back-link" @click="goBack()">返回上一步</button>
      <button class="primary-btn" @click="submitReceive" :disabled="submitting">
        {{ submitting ? '提交中...' : '确认收货' }}
      </button>
    </div>
  </template>

  <!-- 已提交状态 - 显示两个子页面 -->
  <template v-if="stepSubmitted">
    <div class="subpage-tabs">
      <button :class="['tab-btn', { active: doneSubPageIndex === 0 }]" @click="doneSubPageIndex = 0">未拆邮包照片</button>
      <button :class="['tab-btn', { active: doneSubPageIndex === 1 }]" @click="doneSubPageIndex = 1">拆邮包照片</button>
    </div>

    <template v-if="doneSubPageIndex === 0">
      <div class="done-info" v-if="nodeData">
        <div v-if="nodeData.express_company" class="info-row"><span>快递：</span>{{ nodeData.express_company }} {{ nodeData.express_no }}</div>
        <div v-if="nodeData.packaging_condition" class="info-row"><span>包装：</span>{{ nodeData.packaging_condition }}</div>
      </div>
      <div class="photo-section">
        <label>未拆邮包照片</label>
        <div class="photo-grid">
          <div v-for="(p, i) in photos.filter(p => p.type === 'unbox')" :key="i" class="photo-item">
            <img :src="p.url" @click="previewUrl = p.url" />
            <button class="delete-btn" @click="deletePhotoByType('unbox', i)">x</button>
          </div>
        </div>
        <div v-if="!photos.filter(p => p.type === 'unbox').length" class="empty-hint">暂无照片</div>
      </div>
      <div class="page-nav">
        <button class="back-link" @click="goBack">返回上一步</button>
        <button class="primary-btn" @click="goForwardDone(doneSubPageIndex, 1)">下一步：拆邮包照片</button>
      </div>
    </template>

    <template v-if="doneSubPageIndex === 1">
      <div class="photo-section">
        <label>拆邮包后的照片</label>
        <div class="photo-grid">
          <div v-for="(p, i) in photos.filter(p => p.type === 'unbox_opened')" :key="i" class="photo-item">
            <img :src="p.url" @click="previewUrl = p.url" />
            <button class="delete-btn" @click="deletePhotoByType('unbox_opened', i)">x</button>
          </div>
        </div>
        <div v-if="!photos.filter(p => p.type === 'unbox_opened').length" class="empty-hint">暂无照片</div>
      </div>
      <div class="done-info" v-if="nodeData && nodeData.operate_note">
        <div class="info-row"><span>备注：</span>{{ nodeData.operate_note }}</div>
      </div>
      <div class="page-nav">
        <button class="back-link" @click="goBackDoneSub()">返回上一步</button>
        <button v-if="!isLastStep" class="primary-btn" @click="nextStep">下一步</button>
      </div>
    </template>
  </template>
</template>

<script setup>
import { useWorkflow } from '@/composables/useTechWorkflow'
const { stepSubmitted, subPageIndex, doneSubPageIndex, formData, courierList,
  photos, note, previewUrl, nodeData, localPhotos, submitting, isLastStep,
  triggerUpload, goBack, goForwardSub, goForwardDone, goBackDoneSub,
  submitReceive, nextStep, deletePhotoByType } = useWorkflow()
</script>
