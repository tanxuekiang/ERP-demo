<!-- src/App.vue -->
<template>
  <!-- 路由出口：所有路由页面都会渲染到这里 -->
  <router-view />
</template>

<script setup>
// 空的script标签也满足规范（也可添加全局逻辑）
// 若需要全局引入样式/插件，可在这里添加
// 示例：import './assets/css/global.css'
</script>

<style scoped>
/* 可选：添加全局基础样式 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}
body {
  font-family: "Microsoft YaHei", sans-serif;
}
</style>