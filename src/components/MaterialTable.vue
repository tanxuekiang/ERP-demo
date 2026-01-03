<template>
  <!-- 骨架屏加载状态（视觉提速） -->
  <div class="material-table-container" style="display: block !important; min-height: 500px; width: 100%;">
    <div class="table-header">
      <h4>物料信息列表</h4>
      <div class="header-actions">
        <!-- 🔴 新增：权限控制 - 新增物料按钮 -->
        <button
          class="add-btn"
          @click="navigateToAddMaterial"
          v-if="hasPermission('material_add')"
          :disabled="loading || !hasPermission('material_add')"
        >新增物料</button>
        <!-- 🔴 新增：权限控制 - 批量删除按钮 -->
        <button
          class="delete-btn"
          @click="handleBatchDelete"
          v-if="hasPermission('material_delete')"
          :disabled="loading || selectedIds.length === 0 || !hasPermission('material_delete')"
        >
          🗑️ 批量删除选中
        </button>
      </div>
    </div>

    <!-- 骨架屏加载状态 -->
    <div v-if="loading" class="skeleton-container">
      <div class="skeleton-row" v-for="i in 8" :key="i">
        <div class="skeleton-col col-checkbox"></div>
        <div class="skeleton-col col-id"></div>
        <div class="skeleton-col col-name"></div>
        <div class="skeleton-col col-code"></div>
        <div class="skeleton-col col-category"></div>
        <div class="skeleton-col col-unit"></div>
        <div class="skeleton-col col-supplier"></div>
        <div class="skeleton-col col-quantity"></div>
        <div class="skeleton-col col-desc"></div>
        <div class="skeleton-col col-time"></div>
      </div>
    </div>

    <!-- 空数据/异常提示 -->
    <div v-else-if="!hasData">
      {{ emptyMsg }}
    </div>

    <!-- 表格 + 分页 -->
    <div v-else>
      <div class="table-wrapper" style="max-height: 500px; overflow: auto;">
        <table class="material-table">
          <thead>
            <tr>
              <!-- 🔴 新增：权限控制 - 复选框列仅删除权限可见 -->
              <th class="col-checkbox" v-if="hasPermission('material_delete')">
                <input
                  type="checkbox"
                  v-model="allChecked"
                  @change="handleAllCheck"
                  :disabled="loading || materials.length === 0"
                  class="check-all"
                >
              </th>
              <th class="col-id">ID</th>
              <th class="col-name">物料名称</th>
              <th class="col-code">物料编码</th>
              <th class="col-category">物料分类</th>
              <th class="col-unit">单位</th>
              <th class="col-supplier">供应商</th>
              <th class="col-quantity">数量</th>
              <th class="col-desc">特征描述</th>
              <th class="col-time">创建时间</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in materials" :key="item.id" @click="handleRowClick(item.id, $event)" class="table-row">
              <!-- 🔴 新增：权限控制 - 行复选框仅删除权限可见 -->
              <td class="col-checkbox" v-if="hasPermission('material_delete')">
                <input
                  type="checkbox"
                  :value="item.id"
                  v-model="selectedIds"
                  @change="handleRowCheck"
                  :disabled="loading"
                  class="check-row"
                >
              </td>
              <td class="col-id">{{ item.id }}</td>
              <td class="col-name">{{ item.name }}</td>
              <td class="col-code">{{ item.code }}</td>
              <td class="col-category">{{ item.category }}</td>
              <td class="col-unit">{{ item.unit }}</td>
              <td class="col-supplier">{{ item.supplier }}</td>
              <td class="col-quantity">{{ item.quantity }}</td>
              <td class="col-desc">{{ item.desc }}</td>
              <td class="col-time">{{ item.create_time }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="pagination">
        <div class="pagination-info">
          共 {{ totalCount }} 条 | 第 {{ currentPage }} 页 / 共 {{ totalPages }} 页
          <!-- 🔴 新增：权限控制 - 选中数量仅删除权限可见 -->
          <span v-if="selectedIds.length > 0 && hasPermission('material_delete')" class="selected-count">
            已选中 {{ selectedIds.length }} 条
          </span>
        </div>
        <div class="pagination-btns">
          <button @click="changePage(1)" :disabled="currentPage === 1 || loading" class="page-btn">首页</button>
          <button @click="changePage(currentPage - 1)" :disabled="currentPage === 1 || loading" class="page-btn">上一页</button>
          <button @click="changePage(currentPage + 1)" :disabled="currentPage === totalPages || loading" class="page-btn">下一页</button>
          <button @click="changePage(totalPages)" :disabled="currentPage === totalPages || loading" class="page-btn">尾页</button>
          <div class="page-jump">
            <input type="number" v-model.number="jumpPage" min="1" :max="totalPages" placeholder="页码" @keyup.enter="jumpToPage">
            <button @click="jumpToPage" class="jump-btn" :disabled="!jumpPage || jumpPage < 1 || jumpPage > totalPages || loading">跳转</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 🔴 新增：权限控制 - 刷新按钮仅查看权限可见 -->
    <button
      class="refresh-btn"
      @click="handleRefresh"
      :disabled="loading"
      title="刷新物料数据"
      v-if="hasPermission('material_view')"
    >
      ♻️
    </button>
  </div>
</template>

<script setup>
// 完整导入所有需要的API
import { ref, onMounted, computed, watch, onErrorCaptured, onUnmounted, shallowRef } from 'vue';
import request from '@/utils/request'; // 导入配置好的axios实例（带withCredentials）
import { useRouter, useRoute } from 'vue-router';

// 防抖函数（前端环境兼容）
const debounce = (fn, delay = 300) => {
  let timer = null;
  return (...args) => {
    if (timer) clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
};

// 捕获所有渲染错误
onErrorCaptured((error, instance, info) => {
  console.error('组件错误：', error, '位置：', info);
  emptyMsg.value = '页面加载失败：' + error.message;
  loading.value = false;
  return true;
});

const router = useRouter();
const route = useRoute();

// 基础数据：浅响应式（减少响应式开销）
const materials = shallowRef([]);
const loading = ref(false);
const emptyMsg = ref('暂无物料数据，请先录入！');

// 选择相关状态
const allChecked = ref(false); // 全选状态
const selectedIds = ref([]);   // 选中的物料ID列表

// 🔴 新增：权限核心变量
const userPermissions = ref([]); // 当前用户权限列表
const permissionLoading = ref(true); // 权限加载状态（避免闪烁）

// 缓存配置（5秒内复用缓存，避免重复请求）
const cache = ref({ data: [], time: 0, page: 1 });
const CACHE_DURATION = 5000; // 缓存5秒

// 分页参数
const currentPage = ref(1);
const pageSize = ref(10);
const totalCount = ref(0);
const totalPages = ref(0);
const jumpPage = ref(1);

// 🔴 优化：判断是否有数据（需等待权限加载完成）
const hasData = computed(() => {
  return !permissionLoading.value && materials.value.length > 0 && !loading.value;
});

// 🔴 核心新增：权限判断方法（适配后端下划线编码）
const hasPermission = (permission) => {
  // 管理员特殊处理（兼容后端返回的role_code）
  const userRole = localStorage.getItem('erp_user_role_code') || '';
  if (userRole.toLowerCase() === 'admin') return true;

  // 普通用户校验权限列表
  return userPermissions.value.includes(permission);
};

// 🔴 核心新增：初始化用户权限（从后端接口获取）
const initPermissions = async () => {
  permissionLoading.value = true;
  try {
    // 调用后端权限接口（需确保request已配置withCredentials）
    const res = await request.get('/get-user-permissions/', {
      timeout: 5000,
      withCredentials: true // 携带登录态
    });

    if (res && res.code === 200) {
      userPermissions.value = res.data || [];
      console.log('✅ 权限加载成功：', userPermissions.value);
      // 缓存权限到本地（降级备用）
      localStorage.setItem('user_permissions', JSON.stringify(userPermissions.value));
    } else {
      // 降级：读取本地缓存
      const cachedPerms = localStorage.getItem('user_permissions');
      userPermissions.value = cachedPerms ? JSON.parse(cachedPerms) : [];
      console.warn('⚠️ 权限接口返回异常，使用本地缓存：', userPermissions.value);
    }
  } catch (err) {
    console.error('❌ 获取权限失败：', err);
    // 降级：读取本地缓存
    const cachedPerms = localStorage.getItem('user_permissions');
    userPermissions.value = cachedPerms ? JSON.parse(cachedPerms) : [];

    // 登录态失效处理
    if (err.response?.status === 401) {
      emptyMsg.value = '登录状态失效，请重新登录！';
      setTimeout(() => router.push('/login'), 2000);
    }
  } finally {
    permissionLoading.value = false;
  }
};

// 监听表格数据变化，重置选中状态（分页/刷新后清空选择）
watch([materials, currentPage], () => {
  allChecked.value = false;
  selectedIds.value = [];
}, { immediate: true });

// 全选/取消全选逻辑
const handleAllCheck = () => {
  if (loading.value) return;
  if (allChecked.value) {
    // 全选：选中当前页所有物料ID
    selectedIds.value = materials.value.map(item => item.id);
  } else {
    // 取消全选：清空选中
    selectedIds.value = [];
  }
};

// 行复选框变化，更新全选状态
const handleRowCheck = () => {
  // 所有行都选中时，全选框勾选；否则取消
  allChecked.value = materials.value.length > 0 &&
    selectedIds.value.length === materials.value.length;
};

// 行点击事件（区分点击复选框和行内容）
const handleRowClick = (materialId, event) => {
  // 增强兼容性：向上遍历DOM判断是否点击复选框
  let target = event.target;
  while (target) {
    if (target.type === 'checkbox' || target.classList.contains('check-row')) {
      return;
    }
    target = target.parentElement;
  }

  // 🔴 新增：权限控制 - 仅编辑权限可跳转（适配共用组件）
  if (!hasPermission('material_edit')) {
    alert('您暂无编辑物料的权限！');
    return;
  }
  navigateToMaterialEdit(materialId);
};

// 核心：修复接口路径+响应解析（适配后端返回格式）
const fetchMaterials = async (page = 1, forceRefresh = false) => {
  // 🔴 新增：权限校验 - 无查看权限直接返回
  if (!hasPermission('material_view')) {
    emptyMsg.value = '您暂无查看物料数据的权限，请联系管理员！';
    loading.value = false;
    return;
  }

  if (loading.value) return;

  const now = Date.now();
  // 登录状态变化时强制刷新缓存
  const isLogin = localStorage.getItem('erp_username');
  if (!isLogin || forceRefresh) {
    cache.value = { data: [], time: 0, page: 1 };
  }
  // 缓存逻辑：5秒内且页码相同，复用缓存
  if (!forceRefresh && cache.value.time + CACHE_DURATION > now && cache.value.page === page) {
    materials.value = cache.value.data;
    totalCount.value = cache.value.total;
    totalPages.value = cache.value.totalPages;
    currentPage.value = page;
    jumpPage.value = page;
    loading.value = false;
    console.log('复用缓存数据，跳过请求');
    return;
  }

  loading.value = true;
  materials.value = [];
  emptyMsg.value = '暂无物料数据，请先录入！';

  try {
    const reqPage = Number(page) || 1;
    const reqPageSize = Number(pageSize.value) || 10;

    // 核心修复：移除重复的/api前缀（request.js已配置baseURL: '/api'）
    const res = await request.get('/get-materials/', {
      params: {
        page: reqPage,
        page_size: reqPageSize,
        ...(forceRefresh ? { _t: now } : {})
      },
      timeout: 3000,
    });

    // 核心修复：适配后端直接返回的格式（无需解析response.data）
    if (res && res.code === 200) {
      materials.value = res.data.list || [];
      totalCount.value = res.data.total || 0;
      currentPage.value = reqPage;
      totalPages.value = Math.ceil(totalCount.value / reqPageSize) || 1;
      jumpPage.value = reqPage;
      // 更新缓存
      cache.value = {
        data: materials.value,
        time: now,
        page: reqPage,
        total: totalCount.value,
        totalPages: totalPages.value
      };
    } else {
      emptyMsg.value = `接口返回异常：${res.msg || '无返回信息'}`;
    }
  } catch (error) {
    console.error('请求失败：', error);
    // 细化错误提示，精准定位问题
    if (error.message.includes('Network Error')) {
      emptyMsg.value = '无法连接后端：请检查8000端口是否启动，或配置跨域！';
    } else if (error.code === 'ECONNABORTED') {
      emptyMsg.value = '请求超时：后端响应过慢，请检查服务！';
    } else if (error.response) {
      // 针对401未登录的特殊处理
      if (error.response.status === 401) {
        emptyMsg.value = '登录状态失效，请重新登录！';
        // 自动跳转到登录页
        setTimeout(() => router.push('/login'), 1500);
      } else if (error.response.status === 403) {
        emptyMsg.value = '您暂无访问物料列表的权限，请联系管理员！';
      } else if (error.response.status === 404) {
        emptyMsg.value = `接口不存在 [404]：请检查后端是否配置/api/get-materials/路由`;
      } else {
        emptyMsg.value = `后端错误 [${error.response.status}]：${error.response.data?.msg || '未知错误'}`;
      }
    } else {
      emptyMsg.value = '加载失败：' + (error.message || '未知错误');
    }
  } finally {
    loading.value = false;
    console.log('请求完成：', { loading: loading.value, dataLen: materials.value.length });
  }
};

// 批量删除逻辑（优化：并行请求+移除重复/api前缀）
const handleBatchDelete = async () => {
  // 🔴 新增：权限二次校验
  if (!hasPermission('material_delete')) {
    alert('您暂无批量删除物料的权限！');
    return;
  }

  if (selectedIds.value.length === 0) return;

  const confirmDelete = confirm(`🗑️ 确定删除选中的${selectedIds.value.length}条物料吗？删除后不可恢复！`);
  if (!confirmDelete) return;

  loading.value = true;
  let successCount = 0;
  let failCount = 0;
  const failIds = [];

  try {
    // 优化：并行请求（提升删除效率）
    const deletePromises = selectedIds.value.map(async (id) => {
      try {
        // 核心修复：移除重复的/api前缀
        await request.delete(`/delete-material/${id}/`, {
          timeout: 3000
        });
        return { id, success: true };
      } catch (err) {
        console.error(`删除ID${id}失败：`, err);
        return { id, success: false };
      }
    });

    // 等待所有删除请求完成
    const results = await Promise.all(deletePromises);

    // 统计结果
    results.forEach(result => {
      if (result.success) {
        successCount++;
      } else {
        failCount++;
        failIds.push(result.id);
      }
    });

    let tipMsg = '';
    if (successCount > 0 && failCount === 0) {
      tipMsg = `成功删除${successCount}条物料！页面即将刷新...`;
    } else if (successCount > 0 && failCount > 0) {
      tipMsg = `成功删除${successCount}条，失败${failCount}条（失败ID：${failIds.join(',')}）！页面即将刷新...`;
    } else {
      tipMsg = `删除失败：所有选中的${failCount}条物料都未能删除！`;
    }
    alert(tipMsg);

    if (successCount > 0) {
      // 优化：使用前端刷新而非页面重载（体验更好）
      fetchMaterials(currentPage.value, true);
      // 重置选中状态
      allChecked.value = false;
      selectedIds.value = [];
    }

  } catch (err) {
    alert(`批量删除异常：${err.message}`);
    console.error('批量删除失败：', err);
  } finally {
    loading.value = false;
  }
};

// 防抖刷新（避免重复点击）
const handleRefresh = debounce(() => {
  fetchMaterials(currentPage.value, true); // 强制刷新，跳过缓存
}, 200);

// 分页切换防抖
const changePage = debounce((page) => {
  if (page < 1 || page > totalPages.value || loading.value) return;
  fetchMaterials(page);
}, 100);

// 页码跳转防抖
const jumpToPage = debounce(() => {
  changePage(jumpPage.value);
}, 100);

// 🔴 核心修改：新增物料跳转（适配共用组件）
// 🔴 核心修改：新增物料跳转（适配Layout子路由）
const navigateToAddMaterial = () => {
  // 1. 主动触发路由调试（快速定位问题）
  window.__checkRouter?.();
  window.__checkPermissions?.();

  // 2. 简化登录态判断（复用路由守卫的逻辑）
  const isLogin = localStorage.getItem('erp_is_login') === 'true';
  const hasUserId = !!localStorage.getItem('erp_user_id');
  if (!isLogin || !hasUserId) {
    alert('请先登录系统！');
    router.push('/login').catch(err => console.error('跳转登录页失败：', err));
    return;
  }

  // 3. 修复权限加载异常处理（超时兜底）
  if (permissionLoading.value) {
    // 权限加载超过5秒则兜底
    const permissionTimeout = setTimeout(() => {
      alert('权限加载超时，使用本地缓存权限！');
      permissionLoading.value = false;
    }, 5000);

    // 等待权限加载完成
    const checkPermission = setInterval(() => {
      if (!permissionLoading.value) {
        clearInterval(checkPermission);
        clearTimeout(permissionTimeout);
        // 权限加载完成后重试
        navigateToAddMaterial();
      }
    }, 200);
    return;
  }

  // 4. 权限校验
  if (!hasPermission('material_add')) {
    alert('您暂无新增物料的权限！');
    return;
  }

  try {
    // 5. 关键修复：先确保在Layout路由下，再跳转子路由
    if (!route.fullPath.startsWith('/layout')) {
      console.log('当前不在Layout路由，先跳转到Layout首页');
      router.push('/layout').then(() => {
        // 延迟跳转子路由（确保父路由加载完成）
        setTimeout(() => {
          router.push({ name: 'MaterialAddEdit' }).catch(err => {
            console.error('Layout内名称跳转失败：', err);
            router.push('/layout/material/add-edit');
          });
        }, 100);
      }).catch(err => {
        console.error('跳转Layout失败：', err);
        // 终极兜底：直接跳转完整路径
        router.push('/layout/material/add-edit');
      });
    } else {
      // 已在Layout内，直接跳转
      router.push({ name: 'MaterialAddEdit' }).catch(err => {
        console.error('名称跳转失败，尝试路径跳转：', err);
        router.push('/layout/material/add-edit');
      });
    }
  } catch (err) {
    console.error('跳转异常（同步错误）：', err);
    alert(`跳转失败：${err.message}\n请检查路由配置！`);
  }
};

// 🔴 核心修改：物料编辑跳转（适配共用组件）
const navigateToMaterialEdit = (materialId) => {
  if (!materialId) {
    alert('物料ID为空，无法跳转编辑页！');
    return;
  }

  try {
    // 跳转到共用组件的编辑路径（带ID参数）
    router.push(`/layout/material/add-edit/${materialId}`).catch((err) => {
      console.error('跳转编辑页失败：', err);
      // 兜底：直接跳转路径
      router.push(`/layout/material/add-edit/${materialId}`);
    });
  } catch (err) {
    console.error('跳转物料编辑失败：', err);
    alert('跳转失败，请检查路由配置！');
  }
};

// 路由监听防抖
const routeWatchHandler = debounce(async (newPath) => {
  console.log('当前路由：', newPath);
  if (newPath.includes('/basicinfoman/proc-material') || newPath.includes('/material-table')) {
    // 🔴 新增：路由变化时重新加载权限
    await initPermissions();
    if (!permissionLoading.value) {
      fetchMaterials(currentPage.value);
    }
  }
}, 100);

watch(
  () => route.fullPath,
  routeWatchHandler,
  { immediate: true, deep: true }
);

// 组件挂载（新增登录态校验）
onMounted(async () => {
  console.log('组件挂载完成，开始加载数据');
  // 严格登录态校验（与路由守卫保持一致）
  const isLogin = localStorage.getItem('erp_is_login') === 'true';
  const hasUserId = !!localStorage.getItem('erp_user_id');
  if (!isLogin || !hasUserId) {
    alert('请先登录系统！');
    router.push('/login');
    return;
  }

  // 先加载权限，再加载数据
  await initPermissions();

  if (!permissionLoading.value) {
    fetchMaterials();
  }

  // 暴露调试方法（方便排查）
  window.__forceFetchMaterials = fetchMaterials;
  window.__checkRouter = () => {
    // 打印当前所有路由名称和路径
    const routes = router.getRoutes().map(r => ({ name: r.name, path: r.path }));
    console.log('当前注册的路由：', routes);
    // 检查目标路由是否存在
    const targetRoute = router.getRoutes().find(r => r.name === 'MaterialAddEdit');
    console.log('MaterialAddEdit 路由是否存在：', !!targetRoute, targetRoute);
  };
  window.__checkPermissions = () => console.log('当前权限列表：', userPermissions.value);
});

// 组件卸载：清理缓存和全局方法
onUnmounted(() => {
  delete window.__forceFetchMaterials;
  delete window.__checkPermissions;
  cache.value = { data: [], time: 0, page: 1 };
});
</script>

<style scoped>
/* 原有样式完全保留，无改动 */
.material-table-container {
  margin: 24px auto;
  padding: 24px 32px;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  max-width: 1600px;
  width: 98%;
  box-sizing: border-box;
  position: relative;
  min-height: 600px;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.table-header h4 {
  font-size: 18px;
  color: #0c4a6e;
  margin: 0;
}

.add-btn, .refresh-btn {
  padding: 8px 18px;
  border: none;
  border-radius: 4px;
  color: #fff;
  cursor: pointer;
  font-size: 14px;
}

.add-btn {
  background: #10b981;
  transition: background 0.2s ease;
}

.add-btn:hover {
  background: #059669;
}

.refresh-btn {
  background: #0ea5e9;
  position: absolute;
  bottom: 24px;
  right: 24px;
  z-index: 10;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  width: 44px;
  height: 44px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  padding: 0;
  transition: all 0.2s ease;
}

.refresh-btn:hover {
  background: #0284c7;
  transform: rotate(180deg);
}

.refresh-btn:disabled {
  background: #94a3b8;
  cursor: not-allowed;
  opacity: 0.7;
  transform: none;
}

.delete-btn {
  padding: 8px 18px;
  border: none;
  border-radius: 4px;
  color: #fff;
  cursor: pointer;
  background: #ef4444;
  margin-left: 12px;
  font-size: 14px;
  transition: background 0.2s ease;
}

.delete-btn:hover {
  background: #dc2626;
}

.delete-btn:disabled {
  background: #fca5a5;
  cursor: not-allowed;
}

.skeleton-container {
  width: 100%;
  padding: 12px 0;
}

.skeleton-row {
  display: flex;
  height: 44px;
  margin-bottom: 10px;
  align-items: center;
}

.skeleton-col {
  background: linear-gradient(90deg, #f0f9ff 25%, #e0f2fe 50%, #f0f9ff 75%);
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s infinite;
  border-radius: 4px;
  height: 28px;
}

.skeleton-col.col-checkbox { width: 6%; margin: 0 6px; }
.skeleton-col.col-id { width: 5%; margin: 0 6px; }
.skeleton-col.col-name { width: 14%; margin: 0 6px; }
.skeleton-col.col-code { width: 10%; margin: 0 6px; }
.skeleton-col.col-category { width: 9%; margin: 0 6px; }
.skeleton-col.col-unit { width: 7%; margin: 0 6px; }
.skeleton-col.col-supplier { width: 14%; margin: 0 6px; }
.skeleton-col.col-quantity { width: 7%; margin: 0 6px; }
.skeleton-col.col-desc { width: 22%; margin: 0 6px; }
.skeleton-col.col-time { width: 10%; margin: 0 6px; }

@keyframes skeleton-loading {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.col-checkbox {
  width: 6%;
  text-align: center;
  padding: 16px 10px;
}

.check-all, .check-row {
  width: 24px;
  height: 24px;
  cursor: pointer;
  margin: 0 auto;
  position: relative;
}

.check-all::after, .check-row::after {
  content: '';
  position: absolute;
  top: -6px;
  left: -6px;
  right: -6px;
  bottom: -6px;
}

.check-all:disabled, .check-row:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.selected-count {
  color: #ef4444;
  margin-left: 14px;
  font-weight: 600;
  font-size: 14px;
}

.loading, .empty {
  text-align: center;
  padding: 60px 0;
  color: #64748b;
  font-size: 16px;
}

.table-wrapper {
  width: 100%;
  overflow-x: auto;
  min-height: 300px;
  margin: 12px 0;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}

.material-table {
  width: 100%;
  border-collapse: collapse;
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
}

.material-table th {
  background: #f0f9ff;
  color: #0c4a6e;
  font-weight: 600;
  padding: 16px 10px;
  font-size: 15px;
  border-bottom: 2px solid #bae6fd;
  white-space: nowrap;
}

.material-table td {
  padding: 16px 10px;
  font-size: 14px;
  color: #334155;
  border-bottom: 1px solid #e2e8f0;
  white-space: nowrap;
}

.table-row {
  cursor: pointer;
  transition: background 0.2s ease;
}

.table-row:hover {
  background: #e0f2fe;
}

.col-id { width: 5%; text-align: center; }
.col-name { width: 14%; text-align: left; padding-left: 20px; }
.col-code { width: 10%; text-align: center; }
.col-category { width: 9%; text-align: center; }
.col-unit { width: 7%; text-align: center; }
.col-supplier { width: 14%; text-align: left; padding-left: 20px; }
.col-quantity { width: 7%; text-align: right; padding-right: 20px; }
.col-desc { width: 22%; text-align: left; padding-left: 20px; white-space: normal; word-wrap: break-word; line-height: 1.5; }
.col-time { width: 10%; text-align: center; }

.pagination {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid #e2e8f0;
  font-size: 15px;
  color: #64748b;
  padding-right: 70px;
  box-sizing: border-box;
}

.pagination-info {
  display: flex;
  align-items: center;
}

.pagination-btns {
  display: flex;
  gap: 10px;
  align-items: center;
}

.page-btn {
  padding: 6px 14px;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s ease;
}

.page-btn:hover:not(:disabled) {
  background: #e0f2fe;
  border-color: #0ea5e9;
}

.page-btn:disabled {
  background: #f8fafc;
  color: #94a3b8;
  cursor: not-allowed;
}

.page-jump input {
  width: 70px;
  padding: 6px 10px;
  border: 1px solid #e2e8f0;
  border-radius: 4px;
  text-align: center;
  font-size: 14px;
}

.jump-btn {
  padding: 6px 14px;
  background: #0ea5e9;
  color: #fff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.2s ease;
}

.jump-btn:hover:not(:disabled) {
  background: #0284c7;
}

.jump-btn:disabled {
  background: #94a3b8;
  cursor: not-allowed;
}

@media (min-width: 1920px) {
  .material-table-container {
    max-width: 1800px;
    padding: 32px 40px;
  }
  .material-table th, .material-table td {
    padding: 18px 12px;
    font-size: 15px;
  }
  .skeleton-row {
    height: 48px;
  }
  .skeleton-col {
    height: 32px;
  }
}

@media (max-width: 1440px) {
  .material-table-container {
    max-width: 1400px;
    width: 95%;
  }
}

@media (max-width: 768px) {
  .pagination {
    flex-direction: column;
    gap: 14px;
    align-items: flex-start;
    padding-right: 0;
  }
  .pagination-btns {
    width: 100%;
    justify-content: flex-start;
    flex-wrap: wrap;
  }
  .material-table th, .material-table td {
    padding: 12px 6px;
    font-size: 13px;
  }
  .col-checkbox { width: 10%; }
  .skeleton-col.col-checkbox { width: 10%; }
  .refresh-btn {
    bottom: 18px;
    right: 18px;
    width: 40px;
    height: 40px;
    font-size: 18px;
  }
  .material-table-container {
    max-width: 100%;
    padding: 16px;
    margin: 16px auto;
    width: calc(100% - 32px);
  }
}

@media (max-width: 480px) {
  .table-header {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }
  .header-actions {
    width: 100%;
    display: flex;
    gap: 10px;
  }
  .add-btn, .delete-btn {
    flex: 1;
    width: 100%;
    padding: 10px;
  }
  .pagination-btns {
    flex-direction: row;
    flex-wrap: wrap;
    gap: 6px;
  }
  .col-checkbox { width: 12%; }
  .skeleton-col.col-checkbox { width: 12%; }
  .material-table-container {
    padding: 12px;
    margin: 8px auto;
    width: calc(100% - 16px);
    min-height: 500px;
  }
}
</style>