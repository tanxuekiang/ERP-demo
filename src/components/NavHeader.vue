<template>
  <header class="nav-header">
    <!-- Logo+用户信息区域（左上角） -->
    <div class="logo-user-container">
      <div class="logo-container">
        <span class="logo-icon">📊</span>
        <div class="logo-text-wrapper">
          <span class="logo-text">企业ERP系统</span>
          <!-- 用户信息移至Logo文字下方 -->
          <div class="user-info">
            <span class="user-role" v-if="isAdmin">管理员</span>
            <span class="user-name">{{ currentUser || '未登录' }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 主导航 -->
    <ul class="main-nav">
      <li
        v-for="(item, key) in mainNavMap"
        :key="key"
        class="nav-item"
        @click="handleMainNavClick(key)"
        :class="{ 'active': currentKey === key }"
      >
        <span class="nav-icon">{{ getNavIcon(key) }}</span>
        <span class="nav-text">{{ item }}</span>
      </li>
    </ul>

    <!-- 右侧超小功能图标区 -->
    <div class="tiny-icons">
      <!-- 权限管理：仅admin显示 -->
      <div
        v-if="isAdmin"
        class="tiny-icon-item"
        @click="handlePermissionManagement"
        title="权限管理"
      >
        <span class="tiny-icon">🔐</span>
      </div>

      <!-- 个人中心：仅admin显示 -->
      <div
        v-if="isAdmin"
        class="tiny-icon-item"
        @click="handleAdminUserManagement"
        title="用户管理"
      >
        <span class="tiny-icon">👤</span>
      </div>
      <!-- 非admin用户可保留普通个人中心（可选） -->
      <div
        v-else
        class="tiny-icon-item"
        @click="handleNormalPersonalCenter"
        title="个人中心"
      >
        <span class="tiny-icon">👤</span>
      </div>
      <div class="tiny-icon-item" @click="handlePendingTasks" title="待处理">
        <span class="tiny-icon">📋</span>
        <span class="tiny-badge" v-if="pendingCount > 0">{{ pendingCount }}</span>
      </div>
      <div class="tiny-icon-item" @click="handleLogout" title="退出登录">
        <span class="tiny-icon">🚪</span>
      </div>
    </div>
  </header>
</template>

<script setup>
import { ref, watchEffect, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';

const emit = defineEmits(['main-key-change', 'personal-center', 'pending-tasks', 'permission-management']);
const route = useRoute();
const router = useRouter();

// 主导航映射
const mainNavMap = {
  basicinfoman:'基础资料',
  ProjectInitiation:'立项管理',
  BudgetManage:'预算管理',
  procurement: '采购管理',
  contract: '合同管理',
  inventory: '库存管理',
  PrducMagem:'生产管理',
  FinancialManagement:'财务管理',
  DocManagement:'图纸管理',
  AccountBookManagement:'台账管理'
};

// 待处理数量
const pendingCount = ref(5);

// 从本地缓存获取当前登录用户（实际项目建议用pinia/vuex管理）
const currentUser = ref(localStorage.getItem('erp_username') || '');

// 计算属性：判断是否为admin账户
const isAdmin = computed(() => {
  return currentUser.value === 'admin'; // 可扩展为权限码判断，如包含'admin'角色
});

// 图标映射
const getNavIcon = (key) => {
  const iconMap = {
    basicinfoman: '📋',
    ProjectInitiation: '📌',
    BudgetManage: '💰',
    procurement: '🛒',
    contract: '📜',
    inventory: '📦',
    PrducMagem: '🏭',
    FinancialManagement: '💹',
    DocManagement: '📄',
    AccountBookManagement: '📓'
  };
  return iconMap[key] || '🔹';
};

// 默认选中基础资料
const currentKey = ref('basicinfoman');

// 监听路由同步选中状态
watchEffect(() => {
  const path = route.path;
  // 适配ERP用户管理/权限管理页面的选中状态
  if (path.includes('system/erp-user') || path.includes('system/role')) {
    currentKey.value = 'basicinfoman'; // 跳转到权限/用户管理时仍选中基础资料
    return;
  }
  const mainKey = path.split('/')[2] || 'basicinfoman'; // 修正：layout下的路径层级
  if (mainNavMap[mainKey]) {
    currentKey.value = mainKey;
  }
});

// 主导航点击
const handleMainNavClick = (key) => {
  currentKey.value = key;
  emit('main-key-change', key);
};

// 新增：权限管理跳转逻辑（仅Admin可见）
const handlePermissionManagement = () => {
  try {
    // 跳转到layout下的角色权限管理页面（与路由配置一致）
    router.push('/layout/system/role');
    // 可选：触发父组件事件
    emit('permission-management', { path: '/layout/system/role' });
  } catch (err) {
    console.error('跳转到权限管理页面失败：', err);
    alert('权限管理页面未配置，请检查路由！');
  }
};

// 核心修改：Admin用户跳转到ERP用户管理页面（适配路由配置）
const handleAdminUserManagement = () => {
  try {
    // 跳转到layout下的ERP用户管理页面（与路由配置一致）
    router.push('/layout/system/erp-user');
    // 可选：触发父组件事件
    emit('personal-center', { type: 'admin', path: '/layout/system/erp-user' });
  } catch (err) {
    console.error('跳转到ERP用户管理页面失败：', err);
    alert('ERP用户管理页面未配置，请检查路由！');
  }
};

// 非Admin用户：普通个人中心（可根据需求自定义）
const handleNormalPersonalCenter = () => {
  emit('personal-center');
  // 示例：跳转到普通个人中心（需自行创建组件）
  router.push('/layout/personal-center').catch(err => {
    console.error('跳转到个人中心失败：', err);
    alert('普通个人中心页面尚未开发！');
  });
};

// 待处理点击
const handlePendingTasks = () => {
  emit('pending-tasks');
};

// 退出登录逻辑
const handleLogout = () => {
  if (confirm('确定要退出登录吗？')) {
    // 1. 清除所有登录相关缓存
    localStorage.removeItem('erp_is_login');
    localStorage.removeItem('erp_username');
    localStorage.removeItem('erp_user_id');
    localStorage.removeItem('erp_session_id');

    // 2. 强制跳转到登录页并刷新
    router.push('/login').then(() => {
      window.location.reload();
    }).catch(err => {
      console.error('退出跳转失败：', err);
      window.location.href = '/login';
    });
  }
};
</script>

<style scoped>
.nav-header {
  height: 64px;
  display: flex;
  align-items: center;
  padding: 0 24px;
  background: linear-gradient(90deg, #81c7fe 0%, #4fc3f7 100%);
  border-bottom: 1px solid #29b6f6;
  box-shadow: 0 2px 8px rgba(129, 199, 254, 0.25);
  position: relative;
  z-index: 100;
}

/* 新增：Logo+用户信息容器 */
.logo-user-container {
  display: flex;
  align-items: center;
  margin-right: 50px;
}

.logo-container {
  display: flex;
  align-items: center;
  gap: 10px;
}

.logo-text-wrapper {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 2px;
}

.logo-icon {
  font-size: 22px;
}

.logo-text {
  font-size: 19px;
  font-weight: 600;
  color: #0c4a6e;
  letter-spacing: 0.5px;
}

.main-nav {
  display: flex;
  list-style: none;
  gap: 36px;
  margin: 0;
  padding: 0;
  flex: 1;
  overflow: hidden;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #075985;
  cursor: pointer;
  font-size: 15px;
  font-weight: 500;
  padding: 8px 12px;
  border-radius: 8px;
  transition: all 0.3s ease;
  position: relative;
  white-space: nowrap;
}

.nav-icon {
  font-size: 16px;
}

.nav-item.active {
  color: #0284c7;
  background-color: #bae6fd;
  box-shadow: 0 2px 0 #0ea5e9;
}

.nav-item:hover {
  color: #0284c7;
  background-color: #d1e7dd;
  transform: translateY(-1px);
}

.tiny-icons {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-left: auto;
}

/* 用户信息样式（Logo文字下方） */
.user-info {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #075985;
  font-size: 12px;
  font-weight: 500;
  padding: 2px 6px;
  border-radius: 6px;
  background-color: rgba(255, 255, 255, 0.2);
  white-space: nowrap;
}

.user-role {
  font-size: 11px;
  color: #0c4a6e;
  background-color: #bae6fd;
  padding: 1px 4px;
  border-radius: 4px;
  font-weight: 600;
}

.user-name {
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.tiny-icon-item {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  color: #075985;
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.2s ease;
  position: relative;
}

.tiny-icon {
  font-size: 14px;
  line-height: 1;
}

.tiny-icon-item:hover {
  color: #0284c7;
  background-color: #bae6fd;
  transform: scale(1.05);
}

.tiny-badge {
  position: absolute;
  top: -2px;
  right: -2px;
  min-width: 12px;
  height: 12px;
  line-height: 12px;
  text-align: center;
  font-size: 10px;
  font-weight: 600;
  color: white;
  background-color: #ef4444;
  border-radius: 6px;
  padding: 0 2px;
}

/* 权限管理图标hover增强（可选） */
.tiny-icon-item[title="权限管理"]:hover .tiny-icon {
  transform: rotate(5deg);
  transition: transform 0.2s ease;
}

/* 响应式适配 */
@media (max-width: 1200px) {
  .logo-user-container {
    margin-right: 30px;
  }
  .main-nav {
    gap: 24px;
  }
  .tiny-icons {
    gap: 12px;
  }
  .user-info {
    font-size: 11px;
    padding: 2px 5px;
  }
  .user-role {
    font-size: 10px;
  }
  .tiny-icon-item {
    width: 22px;
    height: 22px;
  }
  .tiny-icon {
    font-size: 13px;
  }
  .logo-text {
    font-size: 17px;
  }
}

/* 更小屏幕适配 */
@media (max-width: 992px) {
  .user-name {
    max-width: 100px;
  }
  .logo-text {
    font-size: 16px;
  }
}

/* 超小屏幕适配（可选） */
@media (max-width: 768px) {
  .logo-text {
    font-size: 15px;
  }
  .user-info {
    font-size: 10px;
    padding: 1px 4px;
  }
}
</style>