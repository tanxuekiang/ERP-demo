<template>
  <div class="flow-editor-container">
    <!-- 流程基础信息配置 -->
    <div class="flow-form">
      <el-form :model="flow" inline @submit.prevent>
        <el-form-item label="流程名称：">
          <el-input
            v-model="flow.name"
            placeholder="请输入流程名称"
            required
            style="width: 200px;"
          />
        </el-form-item>
        <el-form-item label="流程编码：">
          <el-input
            v-model="flow.code"
            placeholder="自动生成（可选）"
            style="width: 200px;"
            :disabled="!!flow.id"
          />
        </el-form-item>
        <el-form-item>
          <!-- 新增节点按钮 -->
          <el-button @click="addNode('start')">+ 开始节点</el-button>
          <el-button @click="addNode('approver')">+ 审批节点</el-button>
          <el-button @click="addNode('end')">+ 结束节点</el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 画布容器 -->
    <div class="canvas-wrapper">
      <div ref="canvas" class="canvas"></div>
    </div>

    <!-- 节点配置抽屉 -->
    <el-drawer
      v-model="nodeDrawerVisible"
      title="节点配置"
      size="500px"
      :destroy-on-close="true"
    >
      <el-form
        :model="currentNode"
        label-width="100px"
        :rules="{
          name: [{ required: true, message: '节点名称不能为空', trigger: 'blur' }],
          node_type: [{ required: true, message: '节点类型不能为空' }]
        }"
        ref="nodeFormRef"
      >
        <el-form-item label="节点名称" prop="name">
          <el-input v-model="currentNode.name" placeholder="请输入节点名称" />
        </el-form-item>
        <el-form-item label="节点类型" prop="node_type">
          <el-select v-model="currentNode.node_type" disabled>
            <el-option label="开始节点" value="start"></el-option>
            <el-option label="审批节点" value="approver"></el-option>
            <el-option label="结束节点" value="end"></el-option>
          </el-select>
        </el-form-item>

        <!-- 审批节点专属配置 -->
        <el-collapse v-if="currentNode.node_type === 'approver'">
          <el-collapse-item title="审批人配置">
            <el-form-item label="审批人类型">
              <el-select v-model="currentNode.approver_config.type" placeholder="选择审批人类型">
                <el-option label="指定用户" value="user"></el-option>
                <el-option label="部门主管" value="dept_manager"></el-option>
                <el-option label="角色审批" value="role"></el-option>
              </el-select>
            </el-form-item>
            <el-form-item label="指定用户" v-if="currentNode.approver_config.type === 'user'">
              <el-select v-model="currentNode.approver_config.user_ids" multiple placeholder="选择审批用户">
                <el-option label="管理员" value="1"></el-option>
                <el-option label="采购专员" value="2"></el-option>
                <!-- 实际项目中对接后端用户列表接口 -->
              </el-select>
            </el-form-item>
          </el-collapse-item>
        </el-collapse>

        <!-- 下一个节点配置 -->
        <el-form-item label="下一个节点">
          <el-select
            v-model="currentNode.next_nodes.next"
            multiple
            placeholder="请选择后续节点"
            @change="handleNextNodeChange"
          >
            <el-option
              v-for="node in nodeList"
              :key="node.id"
              :label="node.name"
              :value="node.id"
              :disabled="node.id === currentNode.id"
            ></el-option>
          </el-select>
        </el-form-item>
      </el-form>

      <div class="drawer-footer">
        <el-button @click="nodeDrawerVisible = false">取消</el-button>
        <el-button type="primary" @click="saveNode">保存节点</el-button>
      </div>
    </el-drawer>

    <!-- 保存按钮 -->
    <div class="flow-actions">
      <el-button type="primary" @click="saveFlow">保存流程</el-button>
      <el-button @click="() => $router.push('/approval/flow/list')">返回列表</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, getCurrentInstance } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Graph } from '@antv/x6'
import { ElMessage } from 'element-plus'

// 获取路由实例
const route = useRoute()
const router = useRouter()
// 获取当前组件实例
const instance = getCurrentInstance()
// 获取全局axios
const axios = instance ? instance.appContext.config.globalProperties.$axios : null

// 响应式数据
const flow = ref({ id: null, name: '', code: '' })
const graph = ref(null)
const nodeList = ref([])
const currentNode = ref({
  id: '',
  name: '',
  node_type: 'approver',
  approver_config: { type: 'user', user_ids: [] },
  next_nodes: { next: [] },
  sort: 0,
  x: 100,
  y: 100
})
const nodeDrawerVisible = ref(false)
const nodeFormRef = ref(null)

// 初始化画布
onMounted(() => {
  // 校验axios是否存在
  if (!axios) {
    ElMessage.error('全局axios未配置，请检查！')
    return
  }

  // 获取画布DOM（修复ref获取方式）
  const canvasDom = instance.refs?.canvas
  if (!canvasDom) {
    ElMessage.error('画布容器不存在')
    return
  }

  // 创建X6画布实例
  graph.value = new Graph({
    container: canvasDom,
    width: canvasDom.clientWidth,
    height: canvasDom.clientHeight,
    grid: { size: 10, visible: true },
    connecting: {
      router: 'manhattan',
      connector: 'rounded',
      anchor: 'center',
      connectionPoint: 'anchor',
      allowBlank: false,
      snap: { radius: 20 }
    },
    interacting: {
      nodeMove: true,
      magnetConnect: true
    }
  })

  // 监听节点点击事件
  graph.value.on('node:click', ({ node }) => {
    currentNode.value = JSON.parse(JSON.stringify(node.getData()))
    nodeDrawerVisible.value = true
  })

  // 加载已有流程（编辑模式）
  const flowId = route.params.processId || route.query.flowId
  if (flowId) {
    loadFlow(flowId)
  }
})

// 加载流程详情
const loadFlow = async (flowId) => {
  try {
    const res = await axios.get(`/approval/flow/detail/${flowId}/`)
    if (res.data.code !== 200) throw new Error(res.data.msg || '加载失败')

    // 赋值流程信息
    flow.value = res.data.data.info
    nodeList.value = res.data.data.nodes

    // 渲染节点和连线
    renderNodesAndEdges(res.data.data.nodes)
  } catch (err) {
    ElMessage.error(`加载流程失败：${err.message}`)
    console.error('加载流程失败：', err)
  }
}

// 渲染节点和连线
const renderNodesAndEdges = (nodes) => {
  if (!graph.value) return

  // 清空画布
  graph.value.clearCells()

  // 定义节点样式
  const nodeStyleMap = {
    start: { fill: '#10b981', stroke: '#059669' },
    approver: { fill: '#3b82f6', stroke: '#2563eb' },
    end: { fill: '#ef4444', stroke: '#dc2626' }
  }

  // 添加节点
  nodes.forEach(node => {
    const style = nodeStyleMap[node.node_type] || nodeStyleMap.approver
    graph.value.addNode({
      id: node.id || `node_${Date.now()}`,
      x: node.x || 100,
      y: node.y || 100,
      width: 120,
      height: 60,
      label: node.name || '未命名节点',
      attrs: {
        body: { fill: style.fill, stroke: style.stroke, rx: 8, ry: 8 },
        text: { fill: '#fff', fontSize: 14 }
      },
      data: node
    })
  })

  // 添加连线
  nodes.forEach(node => {
    if (node.next_nodes?.next?.length) {
      node.next_nodes.next.forEach(targetId => {
        // 避免重复连线
        const existingEdge = graph.value.getEdges().find(edge =>
          edge.getSourceCellId() === node.id && edge.getTargetCellId() === targetId
        )
        if (!existingEdge) {
          graph.value.addEdge({
            source: node.id,
            target: targetId,
            attrs: {
              line: { stroke: '#94a3b8', strokeWidth: 2, targetMarker: { name: 'block', size: 8 } }
            }
          })
        }
      })
    }
  })
}

// 添加新节点
const addNode = (type) => {
  const nodeId = `node_${Date.now()}`
  const baseX = type === 'start' ? 100 : type === 'end' ? 600 : 300
  const baseY = 200 + nodeList.value.length * 80

  const newNode = {
    id: nodeId,
    name: type === 'start' ? '开始节点' : type === 'end' ? '结束节点' : '审批节点',
    node_type: type,
    approver_config: type === 'approver' ? { type: 'user', user_ids: [] } : {},
    next_nodes: { next: [] },
    x: baseX,
    y: baseY,
    sort: nodeList.value.length
  }

  nodeList.value.push(newNode)
  renderNodesAndEdges(nodeList.value)
}

// 下一个节点变更处理
const handleNextNodeChange = () => {
  if (!currentNode.value.id) return
  updateNodeEdges(currentNode.value)
}

// 更新节点连线
const updateNodeEdges = (node) => {
  if (!graph.value) return

  // 删除该节点的所有旧连线
  graph.value.getEdges().forEach(edge => {
    if (edge.getSourceCellId() === node.id) {
      graph.value.removeCell(edge)
    }
  })

  // 添加新连线
  if (node.next_nodes?.next?.length) {
    node.next_nodes.next.forEach(targetId => {
      graph.value.addEdge({
        source: node.id,
        target: targetId,
        attrs: {
          line: { stroke: '#94a3b8', strokeWidth: 2, targetMarker: { name: 'block', size: 8 } }
        }
      })
    })
  }
}

// 保存节点配置
const saveNode = async () => {
  try {
    // 校验表单引用是否存在
    if (!nodeFormRef.value) {
      ElMessage.error('表单实例不存在')
      return
    }
    // 表单验证
    await nodeFormRef.value.validate()

    if (!currentNode.value.id) {
      ElMessage.warning('节点ID不存在')
      return
    }

    // 更新画布节点数据
    const node = graph.value.getCellById(currentNode.value.id)
    if (!node) throw new Error('节点不存在')

    node.setData(currentNode.value)
    node.attr('label', currentNode.value.name)

    // 更新本地节点列表
    const index = nodeList.value.findIndex(n => n.id === currentNode.value.id)
    if (index > -1) {
      nodeList.value.splice(index, 1, currentNode.value)
    }

    nodeDrawerVisible.value = false
    ElMessage.success('节点保存成功')
  } catch (err) {
    ElMessage.error(`保存节点失败：${err.message || '表单验证失败'}`)
    console.error('保存节点失败：', err)
  }
}

// 保存整个流程
const saveFlow = async () => {
  try {
    if (!flow.value.name) {
      ElMessage.warning('请输入流程名称')
      return
    }

    if (!graph.value) {
      ElMessage.error('画布实例不存在，无法保存')
      return
    }

    // 收集画布中所有节点数据（含坐标）
    const nodes = graph.value.getNodes().map((node, idx) => {
      const nodeData = node.getData()
      const position = node.position()
      return {
        id: nodeData.id || node.id, // 兼容新节点ID
        name: nodeData.name || '',
        node_type: nodeData.node_type || 'approver',
        // 确保approver_config是对象
        approver_config: nodeData.approver_config && typeof nodeData.approver_config === 'object'
          ? nodeData.approver_config
          : {},
        // 标准化next_nodes格式
        next_nodes: {
          next: Array.isArray(nodeData.next_nodes?.next) ? nodeData.next_nodes.next : []
        },
        x: position.x,
        y: position.y,
        sort: idx
      }
    })

    // 构建请求数据
    const requestData = {
      info: {
        name: flow.value.name.trim(),
        code: flow.value.code || '',
        is_active: true
      },
      nodes: nodes
    }

    let res
    if (flow.value.id) {
      // 编辑已有流程
      res = await axios.put(`/approval/flow/update/${flow.value.id}/`, requestData)
    } else {
      // 新增流程
      res = await axios.post('/approval/flow/create/', requestData)
    }

    if (res.data.code !== 200) throw new Error(res.data.msg || '保存失败')

    ElMessage.success(flow.value.id ? '流程更新成功' : '流程创建成功')

    // 新增流程后更新ID
    if (!flow.value.id) {
      flow.value.id = res.data.data.id
      flow.value.code = res.data.data.code
    }

  } catch (err) {
    // 详细错误信息
    console.error('保存流程错误详情：', err.response || err)
    const errorMsg = err.response?.data?.data?.errors
      ? JSON.stringify(err.response.data.data.errors)
      : err.message || '服务器错误'
    ElMessage.error(`保存流程失败：${errorMsg}`)
  }
}
</script>

<style scoped>
.flow-editor-container {
  padding: 20px;
  height: 100vh;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
}

.flow-form {
  margin-bottom: 20px;
  padding: 10px;
  background: #f8f9fa;
  border-radius: 8px;
}

.canvas-wrapper {
  flex: 1;
  border: 1px solid #e6e6e6;
  border-radius: 8px;
  overflow: hidden;
  min-height: 600px;
}

.canvas {
  width: 100%;
  height: 100%;
  background: #fff;
}

.flow-actions {
  margin-top: 20px;
  text-align: right;
}

.drawer-footer {
  margin-top: 20px;
  text-align: right;
}
</style>