<template>
  <!-- 子页0: 设备信息录入 -->
  <template v-if="!stepSubmitted && subPageIndex === 0">
    <div class="section-title">设备信息录入</div>
    <p class="sub-desc">请先填写每台设备的序列号及保养前检测参数（拆件前测量原始值）</p>
    <div v-for="(item, idx) in equipmentData" :key="item.order_item_id" class="equipment-item">
      <div class="equipment-header">
        <span class="equipment-name">{{ item.brand_name }} {{ item.model_name }}</span>
        <span class="equipment-type">{{ item.product_type_name }}</span>
      </div>
      <div class="field-group">
        <label>一级头数量</label>
        <input type="number" v-model.number="item.inspection_data.first_stage_count" class="text-input" min="0" max="10" @change="updateFirstStageArrays(item)" />
      </div>
      <div v-for="i in item.inspection_data.first_stage_count" :key="'fs'+i" class="sub-field-group">
        <div class="field-row">
          <div class="field-col">
            <label>一级头 #{{ i }} 序列号</label>
            <input type="text" v-model="item.inspection_data.first_stage_serials[i-1]" class="text-input" placeholder="序列号" />
          </div>
        </div>
        <div class="field-row">
          <div class="field-col">
            <label class="multi-line-label">保养前气瓶压力为10-150Bar时<br/>中压范围(Bar)</label>
            <input type="text" v-model="item.inspection_data.first_stage_pre_pressure[i-1]" class="text-input" placeholder="如：8.2-10.9" />
          </div>
          <div class="field-col">
            <label class="multi-line-label">保养后气瓶压力为10-150Bar时<br/>中压范围(Bar)</label>
            <input type="text" v-model="item.inspection_data.first_stage_post_pressure[i-1]" class="text-input" placeholder="如：8.5-10.2" />
          </div>
        </div>
      </div>
      <div class="field-group">
        <label>二级头数量</label>
        <input type="number" v-model.number="item.inspection_data.second_stage_count" class="text-input" min="0" max="10" @change="updateSecondStageArrays(item)" />
      </div>
      <div v-for="i in item.inspection_data.second_stage_count" :key="'ss'+i" class="sub-field-group">
        <div class="field-row">
          <div class="field-col">
            <label>二级头 #{{ i }} 序列号</label>
            <input type="text" v-model="item.inspection_data.second_stage_serials[i-1]" class="text-input" placeholder="序列号" />
          </div>
        </div>
        <div class="field-row">
          <div class="field-col">
            <label>保养前抗阻 (cmH2O)</label>
            <input type="text" v-model="item.inspection_data.second_stage_pre_resistance[i-1]" class="text-input" placeholder="如：12" />
          </div>
          <div class="field-col">
            <label>保养后抗阻 (cmH2O)</label>
            <input type="text" v-model="item.inspection_data.second_stage_post_resistance[i-1]" class="text-input" placeholder="如：12" />
          </div>
        </div>
      </div>
    </div>
    <div class="page-nav">
      <button class="back-link" @click="goBack">返回上一步</button>
      <button class="primary-btn" @click="saveEquipmentData" :disabled="submitting">
        {{ submitting ? '保存中...' : '保存并继续' }}
      </button>
    </div>
  </template>

  <!-- 子页1: 拆件检验照片 -->
  <template v-if="!stepSubmitted && subPageIndex === 1">
    <div class="section-title">设备拆解记录</div>
    <p class="sub-desc">请拆解设备各组件，拍摄拆解后的状态照片，记录磨损/损坏情况</p>
    <div v-if="photos.length" class="existing-photos-section">
      <label>已上传的检验照片</label>
      <div class="photo-grid">
        <div v-for="(p, i) in photos" :key="'ex-inspect-'+i" class="photo-item" @click="previewUrl = p.url">
          <img :src="p.url" />
        </div>
      </div>
    </div>
    <div class="field-group">
      <label>{{ photos.length ? '添加更多检验照片' : '拆解后状态照片（可多张）' }}</label>
      <div class="upload-area multi" @click="triggerUploadMulti('inspect')">
        <div v-for="(p, i) in localMultiPhotos.inspect" :key="i" class="multi-preview">
          <img :src="p" />
          <button class="remove-btn" @click.stop="localMultiPhotos.inspect.splice(i, 1)">x</button>
        </div>
        <div class="upload-placeholder mini">
          <span class="upload-icon">[+]</span>
          <span>添加照片</span>
        </div>
      </div>
    </div>
    <div class="field-group">
      <label>检验说明</label>
      <textarea v-model="note" class="textarea-input" rows="4" placeholder="如：O型圈老化需更换，一级头内部有盐渍结晶，二级头咬嘴磨损"></textarea>
    </div>
    <div class="page-nav">
      <button class="back-link" @click="goBack()">返回上一步</button>
      <button class="primary-btn" @click="submitGeneric('inspect')" :disabled="submitting">
        {{ submitting ? '提交中...' : '提交检验记录' }}
      </button>
    </div>
  </template>

  <!-- 已提交状态 -->
  <template v-if="stepSubmitted">
    <div class="done-info" v-if="nodeData">
      <div v-if="nodeData.operate_note" class="info-row"><span>检验说明：</span>{{ nodeData.operate_note }}</div>
    </div>
    <div class="photo-section">
      <label>已上传照片</label>
      <div class="photo-grid">
        <div v-for="(p, i) in photos" :key="i" class="photo-item">
          <img :src="p.url" @click="previewUrl = p.url" />
          <button class="delete-btn" @click="deletePhoto(i)">x</button>
        </div>
      </div>
    </div>
    <div v-if="equipmentData.length > 0" class="equipment-summary">
      <div class="section-title">已录入设备信息</div>
      <div v-for="item in equipmentData" :key="item.order_item_id" class="equipment-summary-item">
        <div class="summary-header">{{ item.brand_name }} {{ item.model_name }}</div>
        <div v-if="item.inspection_data">
          <template v-if="item.inspection_data.first_stage_count > 0">
            <div class="summary-row">一级头: {{ item.inspection_data.first_stage_count }}个</div>
            <div v-for="(sn, i) in item.inspection_data.first_stage_serials" :key="i" class="summary-detail">#{{ i+1 }} SN:{{ sn || '未填' }} 前压:{{ item.inspection_data.first_stage_pre_pressure[i] || '-' }} 后压:{{ item.inspection_data.first_stage_post_pressure[i] || '-' }}</div>
          </template>
          <template v-if="item.inspection_data.second_stage_count > 0">
            <div class="summary-row">二级头: {{ item.inspection_data.second_stage_count }}个</div>
            <div v-for="(sn, i) in item.inspection_data.second_stage_serials" :key="i" class="summary-detail">#{{ i+1 }} SN:{{ sn || '未填' }} 前阻:{{ item.inspection_data.second_stage_pre_resistance[i] || '-' }} 后阻:{{ item.inspection_data.second_stage_post_resistance[i] || '-' }}</div>
          </template>
        </div>
      </div>
    </div>
    <div class="page-nav">
      <button class="back-link" @click="goBack">返回上一步</button>
      <button v-if="!isLastStep" class="primary-btn" @click="nextStep">下一步</button>
    </div>
  </template>
</template>

<script setup>
import { useWorkflow } from '@/composables/useTechWorkflow'
const { stepSubmitted, subPageIndex, equipmentData, photos, note, previewUrl,
  nodeData, localMultiPhotos, submitting, isLastStep,
  updateFirstStageArrays, updateSecondStageArrays, saveEquipmentData,
  triggerUploadMulti, goBack, nextStep, submitGeneric, deletePhoto } = useWorkflow()
</script>
