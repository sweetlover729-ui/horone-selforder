<template>
  <div class="index-page">
    <!-- 顶部导航 -->
    <header class="app-header">
      <div class="app-header-inner">
        <div class="app-logo">
          <div class="app-logo-mark">皓壹</div>
          <div>
            <div class="app-logo-text">皓壹维修服务平台</div>
            <div class="app-logo-sub">潜水装备维修保养自助下单</div>
          </div>
        </div>
        <div class="header-actions">
          <template v-if="customerStore.isLoggedIn">
            <el-button text size="small" @click="router.push('/orders')">
              我的订单
            </el-button>
            <el-button text size="small" @click="handleLogout">
              退出
            </el-button>
          </template>
          <template v-else>
            <el-button type="primary" size="small" @click="router.push('/login')">
              登录
            </el-button>
          </template>
        </div>
      </div>
    </header>

    <!-- 主体内容 -->
    <div class="page-container">
      <!-- 欢迎横幅 -->
      <div class="hero-banner">
        <div class="hero-title">专业潜水装备维修保养</div>
        <div class="hero-sub">全程透明可追踪，让您的装备焕然一新</div>
        <div class="hero-tags">
          <span class="hero-tag">原厂配件</span>
          <span class="hero-tag">专业技师</span>
          <span class="hero-tag">进度可查</span>
          <span class="hero-tag">质量保障</span>
        </div>
      </div>

      <!-- 已登录用户信息 -->
      <div v-if="customerStore.isLoggedIn" class="user-bar">
        <el-icon color="#1677ff"><User /></el-icon>
        <span class="user-bar-name">{{ customerStore.customerInfo.name || customerStore.nickname }}</span>
        <el-button
          type="primary"
          plain
          size="small"
          style="margin-left: auto"
          @click="router.push('/orders')"
        >
          我的订单
        </el-button>
      </div>

      <!-- 产品类型选择 -->
      <div class="section-title">选择设备类别</div>
      <div class="product-grid">
        <div
          v-for="product in productTypes"
          :key="product.key"
          class="product-card"
          @click="handleSelectProduct(product)"
        >
          <div class="product-icon" :style="{ background: product.color }">
            {{ product.abbr }}
          </div>
          <div class="product-name">{{ product.name }}</div>
          <div class="product-desc">{{ product.desc }}</div>
          <div class="product-arrow">
            <el-icon color="#c9cdd4"><ArrowRight /></el-icon>
          </div>
        </div>
      </div>

      <!-- 服务说明 -->
      <div class="section-title" style="margin-top: 32px">服务说明</div>
      <el-card class="info-card">
        <div class="info-list">
          <div class="info-item">
            <div class="info-item-label">服务流程</div>
            <div class="info-item-value">在线下单 → 寄送设备 → 专业检修 → 保养维修 → 回寄设备</div>
          </div>
          <div class="info-item">
            <div class="info-item-label">快递方式</div>
            <div class="info-item-value">贵重物品建议使用顺丰，来回运费自行承担</div>
          </div>
          <div class="info-item">
            <div class="info-item-label">服务周期</div>
            <div class="info-item-value">收到设备后 3-7 个工作日完成（视设备状况而定）</div>
          </div>
          <div class="info-item">
            <div class="info-item-label">质量保障</div>
            <div class="info-item-value">保养完成后提供详细检测报告，保修 90 天</div>
          </div>
        </div>
      </el-card>

      <!-- 联系方式 -->
      <div class="contact-bar">
        <span>如有疑问，请联系客服</span>
        <el-button text type="primary" size="small" @click="showQrDialog = true">微信客服</el-button>
        <span style="color:#1677ff;font-size:13px;margin-left:4px">电话咨询：18502006220</span>
      </div>

      <!-- 微信客服二维码弹窗 -->
      <el-dialog v-model="showQrDialog" title="扫码添加客服微信" width="320px" align-center>
        <div style="text-align:center">
          <img src="/assets/wechat-qr.jpg" alt="客服二维码" style="width:260px;height:260px;border-radius:8px;" />
          <div style="margin-top:12px;font-size:13px;color:#86909c">请使用微信扫描上方二维码</div>
        </div>
      </el-dialog>

      <!-- 管理入口 - 隐蔽在底部 -->
      <div class="admin-entry">
        <a href="/admin/login" class="admin-link">管理入口</a>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useCustomerStore } from '@/stores/customer'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ref } from 'vue'

const router = useRouter()
const customerStore = useCustomerStore()
const showQrDialog = ref(false)

const productTypes = [
  {
    key: 'regulator',
    name: '调节器',
    abbr: '调',
    desc: '标准套装/侧挂套装/背挂双瓶套装',
    color: '#1677ff',
  },
  {
    key: 'bcd',
    name: 'BCD',
    abbr: 'BCD',
    desc: '马甲式/背飞/侧挂系统保养清洗维修',
    color: '#13c2c2',
  },
  {
    key: 'computer',
    name: '电脑表',
    abbr: '表',
    desc: '传感器/屏幕/按键/电池更换',
    color: '#fa8c16',
  },
]

function handleSelectProduct(product) { 
  if (!customerStore.isLoggedIn) {
    ElMessage.info('请先登录后再下单')
    router.push({ path: '/login', query: { redirect: `/order/create?type=${product.key}` } })
    return
  }
  router.push({ path: '/order/create', query: { type: product.key } })
}

function handleLogout() {
  customerStore.logoutAction()
  ElMessage.success('已退出登录')
}
</script>

<style scoped>
.index-page {
  min-height: 100vh;
  background: #f5f7fa;
}

.hero-banner {
  background: linear-gradient(135deg, #1677ff 0%, #4096ff 100%);
  border-radius: 12px;
  padding: 28px 24px;
  margin: 20px 0 24px;
  color: #fff;
}

.hero-title {
  font-size: 20px;
  font-weight: 700;
  margin-bottom: 8px;
}

.hero-sub {
  font-size: 13px;
  opacity: 0.85;
  margin-bottom: 16px;
}

.hero-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.hero-tag {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 4px;
  padding: 3px 10px;
  font-size: 12px;
}

.user-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #fff;
  border-radius: 8px;
  padding: 12px 16px;
  margin-bottom: 20px;
  border: 1px solid #e5e6eb;
  font-size: 14px;
  color: #4e5969;
}

.user-bar-name {
  font-weight: 500;
  color: #1d2129;
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: #1d2129;
  margin-bottom: 12px;
}

.product-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.product-card {
  background: #fff;
  border-radius: 10px;
  padding: 20px 16px;
  border: 1px solid #e5e6eb;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
  overflow: hidden;
}

.product-card:hover {
  border-color: #1677ff;
  box-shadow: 0 4px 16px rgba(22, 119, 255, 0.12);
  transform: translateY(-1px);
}

.product-card:active {
  transform: translateY(0);
}

.product-icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 14px;
  font-weight: 700;
  margin-bottom: 12px;
}

.product-name {
  font-size: 15px;
  font-weight: 600;
  color: #1d2129;
  margin-bottom: 4px;
}

.product-desc {
  font-size: 12px;
  color: #86909c;
  line-height: 1.5;
}

.product-arrow {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
}

.info-card {
  margin-bottom: 20px;
}

.info-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.info-item {
  display: flex;
  gap: 12px;
}

.info-item-label {
  font-size: 13px;
  color: #86909c;
  white-space: nowrap;
  min-width: 60px;
}

.info-item-value {
  font-size: 13px;
  color: #4e5969;
  line-height: 1.6;
}

.contact-bar {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: #86909c;
  padding: 16px 0;
  justify-content: center;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

.admin-entry {
  text-align: center;
  padding: 12px 0 24px;
  border-top: 1px dashed #e5e6eb;
  margin-top: 8px;
}

.admin-link {
  color: #86909c;
  font-size: 12px;
  text-decoration: none;
  transition: color 0.2s;
}

.admin-link:hover {
  color: #1677ff;
}
</style>
