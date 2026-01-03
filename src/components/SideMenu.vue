<template>
  <aside class="side-menu" :class="{ collapsed: isCollapsed }">
    <!-- 折叠按钮：优化视觉和交互 -->
    <button
      class="toggle-btn"
      @click="isCollapsed = !isCollapsed"
      title="折叠/展开菜单"
    >
      <span class="btn-icon">{{ isCollapsed ? '→' : '←' }}</span>
    </button>

    <!-- 菜单标题：优化排版 -->
    <h3 class="menu-title" v-if="!isCollapsed">
      <span class="title-icon">📋</span>
      {{ currentSideMenu.title }}
    </h3>

    <ul class="menu-list">
      <li v-for="(item, index) in currentSideMenu.subMenu" :key="item.id" class="menu-item">
        <a
          href="#"
          class="menu-link"
          @click.prevent="handleSubMenuClick(item)"
          :class="{ 'active': selectedSubMenuId === item.id }"
          :title="isCollapsed ? item.name : ''"
        >
          <!-- 菜单图标：增强视觉识别 -->
          <span class="menu-icon">
            {{ getMenuIcon(item.id) }}
          </span>
          <!-- 菜单文字：优化排版 -->
          <span v-if="!isCollapsed" class="menu-text">{{ item.name }}</span>
        </a>
      </li>
    </ul>

    <!-- 新增：审批流编辑图标按钮 -->
    <div class="approval-flow-btn-wrap">
      <button
        class="approval-flow-btn"
        @click="handleApprovalFlowClick"
        :title="isCollapsed ? '审批流编辑' : ''"
      >
        <span class="approval-flow-icon">📝</span>
        <span v-if="!isCollapsed" class="approval-flow-text">审批流编辑</span>
      </button>
    </div>
  </aside>
</template>

<script setup>
import { ref, computed, watchEffect } from 'vue';
import { useRouter, useRoute } from 'vue-router'; // 引入路由

const router = useRouter();
const route = useRoute();
const props = defineProps({ activeMainKey: { type: String, default: 'procurement' } });
const emit = defineEmits(['select-submenu', 'open-approval-flow']); // 新增事件

const isCollapsed = ref(false);
const selectedSubMenuId = ref('');

const menuMap = {
  basicinfoman: {
    title: '基础资料',
    subMenu: [
      { id: 'proc-material', name: '物料库' },
      { id: 'proc-supply', name: '供应商库' },
      { id: 'proc-organ', name: '组织信息' }
    ]
  },
  // 新增：立项管理菜单配置（关键）
  ProjectInitiation: {
    title: '立项管理',
    subMenu: [
      { id: 'project-apply', name: '立项申请' },
      { id: 'project-review', name: '立项审核' },
      { id: 'project-list', name: '立项列表' } // 可根据实际需求调整子菜单
    ]
  },
  procurement: {
    title: '采购管理',
    subMenu: [
      { id: 'proc-spot', name: '零星采购' },
      { id: 'proc-plan', name: '采购计划' },
      { id: 'proc-quote', name: '材料询比价单' }
    ]
  },
  contract: { title: '合同管理', subMenu: [{ id: 'contract-draft', name: '合同起草' }] },
  inventory: { title: '库存管理', subMenu: [] }
};

// 菜单图标映射：增强视觉识别
const getMenuIcon = (menuId) => {
  const iconMap = {
    'proc-material':'📦',
    'proc-supply':'🛒',
    'proc-spot': '🛒',
    'proc-plan': '📅',
    'proc-quote': '💵',
    'contract-draft': '📝',
    'contract-approve': '✅'
  };
  return iconMap[menuId] || '🔹';
};

const currentSideMenu = computed(() => {
  return menuMap[props.activeMainKey] || { title: '', subMenu: [] };
});

// 修复：监听路由变化，同步菜单高亮 + 父组件状态
watchEffect(() => {
  const path = route.path;
  let targetSubMenuId = '';

  // 1. 处理常规菜单路由（/mainKey/subMenuId）
  const pathParts = path.split('/');
  if (pathParts.length >= 3 && props.activeMainKey === pathParts[1]) {
    targetSubMenuId = pathParts[2]; // 修正：原代码取[3]是错误的，应该取[2]
  }

  // 2. 处理新增物料路由（/material/add）：保留物料库高亮
  if (path === '/material/add') {
    targetSubMenuId = 'proc-material'; // 强制高亮「物料库」
    // 同步通知父组件（Layout）选中状态
    emit('select-submenu', {
      mainKey: 'basicinfoman',
      subMenuId: 'proc-material',
      subMenuName: '物料库'
    });
  }

  // 3. 初始化选中第一个子菜单（无匹配时）
  if (!targetSubMenuId) {
    const subMenus = currentSideMenu.value.subMenu;
    targetSubMenuId = subMenus.length > 0 ? subMenus[0].id : '';
  }

  // 4. 更新选中状态
  selectedSubMenuId.value = targetSubMenuId;

  // 5. 同步通知父组件（Layout）选中状态（常规路由）
  if (targetSubMenuId && path !== '/material/add') {
    const targetSubMenu = currentSideMenu.value.subMenu.find(item => item.id === targetSubMenuId);
    if (targetSubMenu) {
      emit('select-submenu', {
        mainKey: props.activeMainKey,
        subMenuId: targetSubMenuId,
        subMenuName: targetSubMenu.name
      });
    }
  }
});

// 侧边栏script中的handleSubMenuClick方法
const handleSubMenuClick = (item) => {
  selectedSubMenuId.value = item.id;
  const submenuInfo = {
    mainKey: props.activeMainKey,
    subMenuId: item.id,
    subMenuName: item.name
  };
  emit('select-submenu', submenuInfo);

  // 1. 新增日志，验证点击触发
  console.log('点击菜单：', props.activeMainKey, item.id, `/${props.activeMainKey}/${item.id}`);
  // 2. 跳转路由（保留）
  router.push(`/${props.activeMainKey}/${item.id}`);
};

// 新增：审批流编辑按钮点击事件
const handleApprovalFlowClick = () => {
  console.log('点击审批流编辑按钮');
  // 直接跳转到审批流编辑页面（新建模式）
  router.push({
    name: 'ApprovalFlowEditor',
    // 可传递当前主菜单key作为参数，便于后续关联业务
    query: { mainKey: props.activeMainKey }
  });

  // 如果需要支持编辑已有流程，可传递processId
  // router.push(`/approval-flow/edit/${processId}`);
};
</script>

<style scoped>
/* 原有样式完全保留，无需修改 */
.side-menu {
  width: 240px;
  height: 100%;
  padding: 28px 0;
  box-sizing: border-box;
  background: linear-gradient(180deg, #e0f2fe 0%, #f0f9ff 100%);
  border-right: 1px solid #bae6fd;
  box-shadow: 0 0 16px rgba(147, 205, 253, 0.15);
  flex-shrink: 0;
  overflow-y: auto;
  position: relative;
  transition: width 0.35s ease, padding 0.35s ease;
  /* 新增：为固定按钮预留空间 */
  display: flex;
  flex-direction: column;
}

.side-menu.collapsed {
  width: 50px;
  padding: 28px 0;
}

.toggle-btn {
  position: absolute;
  top: 50%;
  right: 12px;
  transform: translateY(-50%);
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, #38bdf8 0%, #0ea5e9 100%);
  color: #ffffff;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  box-shadow: 0 4px 12px rgba(56, 189, 248, 0.2);
  transition: all 0.3s ease;
  z-index: 10;
}

.side-menu.collapsed .toggle-btn {
  right: 8px;
}

.toggle-btn:hover {
  transform: translateY(-50%) scale(1.08);
  box-shadow: 0 6px 16px rgba(56, 189, 248, 0.3);
}

.toggle-btn .btn-icon {
  transition: transform 0.3s ease;
}

.toggle-btn:hover .btn-icon {
  transform: scale(1.1);
}

.menu-title {
  font-size: 19px;
  margin: 0 0 32px 28px;
  color: #0c4a6e;
  font-weight: 600;
  letter-spacing: 0.3px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.title-icon {
  font-size: 20px;
  color: #0284c7;
}

.side-menu.collapsed .menu-title {
  display: none;
}

.menu-list {
  list-style: none;
  padding: 0;
  margin: 0;
  /* 新增：让列表占满中间空间，按钮固定在底部 */
  flex: 1;
}

.menu-item {
  margin: 0 8px 6px 8px;
  border-radius: 8px;
  transition: all 0.2s ease;
}

.menu-link {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 15px 20px;
  color: #075985;
  text-decoration: none;
  font-size: 15px;
  font-weight: 500;
  border-radius: 8px;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.menu-icon {
  font-size: 18px;
  width: 20px;
  text-align: center;
  color: #0369a1;
  transition: color 0.3s ease;
}

.menu-text {
  letter-spacing: 0.2px;
  transition: opacity 0.3s ease;
}

.menu-link.active {
  background: linear-gradient(135deg, #bae6fd 0%, #93c5fd 100%);
  color: #0c4a6e;
  box-shadow: 0 2px 8px rgba(147, 205, 253, 0.25);
}

.menu-link.active .menu-icon {
  color: #0284c7;
}

.menu-link:hover {
  background: #bae6fd;
  color: #075985;
  transform: translateX(2px);
}

.menu-link:hover .menu-icon {
  color: #0284c7;
}

.side-menu.collapsed .menu-text {
  display: none;
}

.side-menu.collapsed .menu-link {
  justify-content: center;
  padding: 15px 0;
}

.side-menu::-webkit-scrollbar {
  width: 7px;
}

.side-menu::-webkit-scrollbar-track {
  background: #f0f9ff;
  border-radius: 10px;
  margin: 10px 0;
}

.side-menu::-webkit-scrollbar-thumb {
  background: #93c5fd;
  border-radius: 10px;
  transition: background 0.3s ease;
}

.side-menu::-webkit-scrollbar-thumb:hover {
  background: #60a5fa;
}

.menu-list:empty::before {
  content: '暂无菜单';
  display: block;
  padding: 20px;
  text-align: center;
  color: #075985;
  font-size: 14px;
}

/* 新增：审批流编辑按钮样式 */
.approval-flow-btn-wrap {
  padding: 16px 8px;
  margin-top: auto;
  border-top: 1px solid rgba(186, 230, 253, 0.5);
}

.approval-flow-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 12px;
  padding: 12px 20px;
  background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
  color: #ffffff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 15px;
  font-weight: 500;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(14, 165, 233, 0.2);
}

.side-menu.collapsed .approval-flow-btn {
  justify-content: center;
  padding: 12px 0;
}

.approval-flow-icon {
  font-size: 18px;
  width: 20px;
  text-align: center;
  transition: transform 0.3s ease;
}

.approval-flow-text {
  letter-spacing: 0.2px;
}

.approval-flow-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(14, 165, 233, 0.3);
  background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
}

.approval-flow-btn:hover .approval-flow-icon {
  transform: scale(1.1);
}

.side-menu.collapsed .approval-flow-text {
  display: none;
}
</style>