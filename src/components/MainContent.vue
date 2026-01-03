<template>
  <div class="main-content" style="flex: 1; overflow-y: auto;">
    <!-- 动态标题 -->
    <h2>{{ currentTitle }}</h2>
    <!-- 主内容区的router-view（渲染物料库/采购计划等页面） -->
    <router-view></router-view>
  </div>
</template>

<script setup>
import { computed, watchEffect } from 'vue';
import { useRoute } from 'vue-router';

const route = useRoute();

// 静态路由标题配置
const staticTitleMap = {
  '/layout/basicinfoman/proc-material': '基础资料 - 物料库',
  '/layout/material/add': '基础资料 - 新增物料',
  '/layout/procurement/proc-spot': '采购管理 - 零星采购',
  '/layout/procurement/proc-plan': '采购管理 - 采购计划',
  '/layout/basicinfoman/proc-supply': '基础资料 - 供应商库'
};

// 动态计算标题
const currentTitle = computed(() => {
  const currentPath = route.path;
  if (staticTitleMap[currentPath]) return staticTitleMap[currentPath];
  return '企业ERP系统 - 首页';
});

// 监听路由变化
watchEffect(() => {
  console.log('路由变化：', route.path);
});
</script>

<style scoped>
.main-content {
  width: 100%;
  height: 100%;
  box-sizing: border-box;
  padding: 20px;
  background-color: #f5f7fa;
  overflow-y: auto;
}

h2 {
  font-size: 20px;
  color: #333;
  border-bottom: 1px solid #e0e0e0;
  padding-bottom: 10px;
  margin-bottom: 20px;
}
</style>