<template>
  <div class="app-layout" style="display: flex; flex-direction: column; height: 100vh;">
    <!-- 导航栏：监听logout和main-key-change事件 -->
    <NavHeader
      @logout="handleLogout"
      @main-key-change="handleMainKeyChange"
    />
    <!-- 主体区域：侧边栏 + 主内容区 -->
    <div class="layout-body" style="display: flex; flex: 1;">
      <!-- 侧边栏 -->
      <SideMenu
        :activeMainKey="activeMainKey"
        @select-submenu="handleSelectSubmenu"
      />
      <!-- 主内容区：用闭合标签形式的router-view（避免自闭合标签解析问题） -->
      <div style="flex: 1; padding: 16px; width: 100%; overflow: auto; box-sizing: border-box;">
        <router-view></router-view>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import NavHeader from './NavHeader.vue';
import SideMenu from './SideMenu.vue';

const router = useRouter();
const activeMainKey = ref('basicinfoman');

// 处理顶部导航的key变化（同步到侧边栏）
const handleMainKeyChange = (key) => {
  activeMainKey.value = key;
  // 可选：点击顶部导航时自动跳转到对应菜单第一个子路由
  const firstSubMenuMap = {
    basicinfoman: 'proc-material',
    ProjectInitiation: 'project-apply',
    procurement: 'proc-spot',
    contract: 'contract-draft'
  };
  const firstSubMenuId = firstSubMenuMap[key];
  if (firstSubMenuId) {
    router.push(`/layout/${key}/${firstSubMenuId}`);
  }
};

// 接收侧边栏选中的子菜单
const handleSelectSubmenu = (submenuInfo) => {
  activeMainKey.value = submenuInfo.mainKey;
};

// 退出登录逻辑
const handleLogout = () => {
  localStorage.removeItem('erp_is_login');
  router.push('/login');
};
</script>

<style scoped>
.app-layout {
  height: 100vh;
  overflow: hidden;
}
.layout-body {
  flex: 1;
  overflow: hidden;
}
</style>