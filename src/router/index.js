import { createRouter, createWebHistory } from 'vue-router';
// 基础组件导入（核心：MaterialDetail 为共用组件）
import Login from '../components/Login.vue';
import Layout from '../components/Layout.vue';
import MaterialTable from '../components/MaterialTable.vue';
import MaterialDetail from '../components/MaterialDetail.vue'; // 新增/编辑/详情共用组件
import MainContent from '../components/MainContent.vue';
import ApprovalFlowEditor from '../components/ApprovalFlowEditor.vue'; // 审批流编辑组件
// 修复：RoleManager 组件导入路径
import ERPUserManagement from '../components/ERPUserManagement.vue';
import RoleManager from '../components/RoleManager.vue';

// 补充缺失组件（临时占位）
const SupplyPage = { template: '<div>供应商管理页面（待开发）</div>' };
const SpotPage = { template: '<div>现货采购页面（待开发）</div>' };
const PlanPage = { template: '<div>采购计划页面（待开发）</div>' };
const ContractPage = { template: '<div>合同草稿页面（待开发）</div>' };

// 路由规则配置
const routes = [
  // 登录页
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { requiresAuth: false, title: 'ERP登录' }
  },
  // Layout布局（系统页面容器）
  {
    path: '/layout',
    name: 'Layout',
    component: Layout,
    meta: { requiresAuth: true, title: 'ERP系统首页' },
    children: [
      // 默认子路由
      { path: '', redirect: '/layout/basicinfoman/proc-material' },
      // 物料管理核心路由
      {
        path: 'basicinfoman/proc-material',
        name: 'MaterialTable',
        component: MaterialTable,
        meta: { title: '物料库', requiresAuth: true }
      },
      // 核心修复：合并新增/编辑为单个路由（带可选ID参数）
      {
        path: 'material/add-edit/:id?', // :id? 表示ID是可选参数（新增无ID，编辑有ID）
        name: 'MaterialAddEdit', // 统一路由名称
        component: MaterialDetail, // 直接使用已导入的组件（路径正确）
        meta: { title: '新增物料', requiresAuth: true }
      },
      // 旧路由重定向（保留，兼容历史跳转）
      {
        path: 'material/add',
        redirect: '/layout/material/add-edit'
      },
      {
        path: 'material/edit/:id',
        redirect: to => `/layout/material/add-edit/${to.params.id}`
      },
      {
        path: 'material/detail/:id',
        redirect: to => `/layout/material/add-edit/${to.params.id}`
      },
      // ERP用户管理路由
      {
        path: 'system/erp-user',
        name: 'ERPUserManagement',
        component: ERPUserManagement,
        meta: {
          title: 'ERP用户管理',
          requiresAuth: true,
          requiresAdmin: true
        }

      },
      // 角色权限管理路由
      {
        path: 'system/role',
        name: 'RoleManager',
        component: RoleManager,
        meta: {
          title: '角色权限管理',
          requiresAuth: true,
          requiresAdmin: true
        }
      },
      // 其他侧边栏路由
      {
        path: 'basicinfoman/proc-supply',
        component: SupplyPage,
        meta: { title: '供应商管理', requiresAuth: true }
      },
      {
        path: 'procurement/proc-spot',
        component: SpotPage,
        meta: { title: '现货采购', requiresAuth: true }
      },
      {
        path: 'procurement/proc-plan',
        component: PlanPage,
        meta: { title: '采购计划', requiresAuth: true }
      },
      {
        path: 'contract/contract-draft',
        component: ContractPage,
        meta: { title: '合同草稿', requiresAuth: true }
      },
        {
        path: 'approval-flow/edit/:processId?', // 可选processId，支持新建/编辑
        name: 'ApprovalFlowEditor',
        component: ApprovalFlowEditor,
        meta: { title: '审批流编辑' }
      }
    ]
  },
  // 全局旧路径兼容重定向
  { path: '/basicinfoman/proc-material', redirect: '/layout/basicinfoman/proc-material' },
  { path: '/material/add', redirect: '/layout/material/add-edit' },
  { path: '/material/edit/:id', redirect: to => `/layout/material/add-edit/${to.params.id}` },
  { path: '/material/detail/:id', redirect: to => `/layout/material/add-edit/${to.params.id}` },
  { path: '/material-table', redirect: '/layout/basicinfoman/proc-material' },
  { path: '/material-form', redirect: '/layout/material/add-edit' },
  { path: '/user-management', redirect: '/layout/system/erp-user' },
  { path: '/erp-user', redirect: '/layout/system/erp-user' },
  { path: '/role-manager', redirect: '/layout/system/role' },
  // 根路径重定向
  {
    path: '/',
    redirect: () => {
      const isLogin = localStorage.getItem('erp_is_login') === 'true';
      return isLogin ? '/layout/basicinfoman/proc-material' : '/login';
    }
  },
  // 404路由
  {
    path: '/:pathMatch(.*)*',
    redirect: (to) => {
      const isLogin = localStorage.getItem('erp_is_login') === 'true';
      return isLogin ? { name: 'MaterialTable' } : { name: 'Login' };
    }
  }
];

// 创建路由实例
const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 };
  }
});

// 登录权限守卫
router.beforeEach((to, from, next) => {
  // 严格登录态判断（与组件内保持一致）
  const isLogin = localStorage.getItem('erp_is_login') === 'true';
  const hasUserId = !!localStorage.getItem('erp_user_id');
  const finalIsLogin = isLogin && hasUserId; // 必须同时满足
  const isAdmin = localStorage.getItem('erp_username') === 'admin';

  const needAuth = to.meta.requiresAuth === true;
  const needAdmin = to.meta.requiresAdmin === true;

  // 已登录访问登录页 → 跳首页
  if (to.name === 'Login' && finalIsLogin) {
    next({ path: '/layout/basicinfoman/proc-material' });
    return;
  }

  // 未登录访问需授权页面 → 跳登录页（带回调）
  if (needAuth && !finalIsLogin) {
    alert('登录状态已失效，请重新登录！');
    next({
      name: 'Login',
      query: { redirect: to.fullPath } // 登录后返回原页面
    });
    return;
  }

  // 非管理员访问管理员页面 → 跳物料库
  if (needAdmin && finalIsLogin && !isAdmin) {
    console.warn('仅管理员可访问该页面！');
    alert('抱歉，仅管理员账户可访问此功能！');
    next({ path: '/layout/basicinfoman/proc-material' });
    return;
  }

  // 修复：动态设置 MaterialAddEdit 页面标题（新增/编辑区分）
  if (to.name === 'MaterialAddEdit') {
    to.meta.title = to.params.id ? '物料详情/编辑' : '新增物料';
  }

  // 正常放行
  next();
});

// 路由后置守卫：动态标题 + 数据刷新
router.afterEach((to) => {
  document.title = to.meta.title || 'ERP管理系统';

  // 物料列表刷新
  const materialTablePaths = ['/layout/basicinfoman/proc-material'];
  if (to.name === 'MaterialTable' || materialTablePaths.includes(to.path)) {
    console.log('全局守卫：触发表格数据刷新');
    if (typeof window.__forceFetchMaterials === 'function') {
      window.__forceFetchMaterials();
    }
  }

  // ERP用户列表刷新
  if (to.name === 'ERPUserManagement') {
    console.log('全局守卫：触发ERP用户列表数据刷新');
    if (typeof window.__forceFetchERPUsers === 'function') {
      window.__forceFetchERPUsers();
    }
  }

  // 角色管理列表刷新
  if (to.name === 'RoleManager') {
    console.log('全局守卫：触发角色列表数据刷新');
    if (typeof window.__forceFetchRoles === 'function') {
      window.__forceFetchRoles();
    }
  }

  // 从 MaterialAddEdit 返回列表时强制刷新
  if (from.name === 'MaterialAddEdit' && to.name === 'MaterialTable') {
    console.log('从物料编辑页返回，强制刷新列表数据');
    if (typeof window.__forceFetchMaterials === 'function') {
      window.__forceFetchMaterials(true); // 强制刷新缓存
    }
  }
});

// 暴露路由调试方法（保留）
window.__routerDebug = {
  listAllRoutes: () => router.getRoutes().map(r => ({ name: r.name, path: r.path, meta: r.meta })),
  checkRouteExists: (name) => !!router.getRoutes().find(r => r.name === name),
  goToAddMaterial: () => router.push({ name: 'MaterialAddEdit' })
};

export default router;