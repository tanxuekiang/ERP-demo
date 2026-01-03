<template>
  <div>
    <!-- 发起审批按钮 -->
    <el-button v-if="!approvalInstance" type="primary" @click="createInstance">发起审批</el-button>

    <!-- 审批操作区 -->
    <div v-if="approvalInstance">
      <el-tag>当前节点：{{ approvalInstance.current_node.name }}</el-tag>
      <el-tag>审批状态：{{ approvalInstance.status }}</el-tag>
      <el-form :model="approvalForm" inline>
        <el-form-item label="审批意见">
          <el-input v-model="approvalForm.comment" type="textarea"></el-input>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="operateApproval('approve')">同意</el-button>
          <el-button type="danger" @click="operateApproval('reject')">驳回</el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ApprovalOperate',
  props: {
    businessId: { type: String, required: true },
    businessType: { type: String, required: true },
    flowId: { type: Number, required: true }
  },
  data() {
    return {
      approvalInstance: null,
      approvalForm: { comment: '' }
    }
  },
  mounted() {
    // 查询是否已有审批实例
    this.checkInstance()
  },
  methods: {
    async checkInstance() {
      const res = await this.$axios.get('/approval/instance/detail/', {
        params: { business_id: this.businessId, business_type: this.businessType }
      })
      this.approvalInstance = res.data
    },
    async createInstance() {
      // 发起审批：创建审批实例
      await this.$axios.post('/approval/instance/create/', {
        flow_id: this.flowId,
        business_id: this.businessId,
        business_type: this.businessType
      })
      this.$message.success('审批已发起')
      this.checkInstance()
    },
    async operateApproval(action) {
      // 执行同意/驳回操作
      await this.$axios.post('/approval/instance/operate/', {
        instance_id: this.approvalInstance.id,
        action,
        comment: this.approvalForm.comment
      })
      this.$message.success('操作成功')
      this.checkInstance()
      this.approvalForm.comment = ''
    }
  }
}
</script>