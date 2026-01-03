from django.db import models
from django.apps import apps
from django.utils.translation import gettext_lazy as _
import os
import uuid
from datetime import datetime
from django.contrib.auth.models import User

# ========== 全局枚举 ==========
FORM_CHOICES = [
    ('material', '物料表单'),
    ('order', '订单表单'),
    ('erp_user', 'ERP用户表单'),
    ('product', '产品表单'),
    ('role', '角色表单'),
    ('contract', '合同表单')
]

ACTION_CHOICES = [
    ('view', '查看'),
    ('add', '新增'),
    ('edit', '修改'),
    ('delete', '删除'),
    ('export', '导出')
]

# ========== 工具函数 ==========
def material_file_path(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    unique_filename = f"{uuid.uuid4()}{ext}"
    date_path = datetime.now().strftime('%Y/%m/%d')
    return f"materials/{date_path}/{unique_filename}"

# ========== 基础模型（保留原有逻辑） ==========
class Role(models.Model):
    """角色模型"""
    role_name = models.CharField(max_length=50, unique=True, verbose_name=_("角色名称"))
    role_code = models.CharField(max_length=20, unique=True, verbose_name=_("角色编码"))
    desc = models.TextField(blank=True, verbose_name=_("角色描述"))
    create_time = models.DateTimeField(auto_now_add=True, verbose_name=_("创建时间"))

    class Meta:
        db_table = "erp_role"
        verbose_name = _("角色")
        verbose_name_plural = _("角色")

    def __str__(self):
        return self.role_name

    def has_permission(self, form_name, action):
        if self.role_code == 'admin':
            return True
        return self.permissions.filter(
            form_name=form_name,
            action=action
        ).exists()

class ERPUser(models.Model):
    """ERP用户模型"""
    username = models.CharField(max_length=50, unique=True, verbose_name=_('用户名'))
    password = models.CharField(max_length=128, verbose_name=_('密码'))
    email = models.EmailField(blank=True, null=True, verbose_name=_('邮箱'))
    role = models.ForeignKey(
        Role,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('所属角色')
    )
    create_time = models.DateTimeField(auto_now_add=True, verbose_name=_('创建时间'))
    is_active = models.BooleanField(default=True, verbose_name=_('是否激活'))

    class Meta:
        verbose_name = _('ERP用户')
        verbose_name_plural = _('ERP用户')

    def __str__(self):
        return self.username

    def has_permission(self, form_name, action):
        if not self.role:
            return False
        return self.role.has_permission(form_name, action)

class Material(models.Model):
    name = models.CharField(max_length=100, verbose_name="物料名称")
    code = models.CharField(max_length=50, unique=True, verbose_name="物料编码")
    category = models.CharField(max_length=50, default='', verbose_name="物料分类")
    unit = models.CharField(max_length=20, default='', verbose_name="单位")
    supplier = models.CharField(max_length=100, default='', verbose_name="供应商")
    quantity = models.IntegerField(default=0, verbose_name="数量")
    desc = models.TextField(default='', verbose_name="特征描述")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    update_time = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = "myerpapp_material"
        verbose_name = "物料"
        verbose_name_plural = "物料"

    def __str__(self):
        return f"{self.name}({self.code})"

class MaterialFile(models.Model):
    material = models.ForeignKey(Material, on_delete=models.CASCADE, verbose_name="关联物料")
    file_path = models.CharField(max_length=500, verbose_name="文件路径")
    name = models.CharField(
        max_length=255,
        verbose_name="文件原始名称",
        default="",
        blank=True
    )
    size = models.BigIntegerField(
        verbose_name="文件大小（字节）",
        default=0,
        blank=True
    )
    upload_time = models.DateTimeField(auto_now_add=True, verbose_name="上传时间")

    class Meta:
        verbose_name = "物料附件"
        verbose_name_plural = "物料附件"
        db_table = "myerpapp_materialfile"

    def __str__(self):
        return self.name

class PermissionConfig(models.Model):
    """权限配置模型"""
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        verbose_name=_("关联角色"),
        related_name="permissions"
    )
    form_name = models.CharField(max_length=20, choices=FORM_CHOICES, verbose_name=_("表单名称"))
    action = models.CharField(max_length=10, choices=ACTION_CHOICES, verbose_name=_("操作权限"))
    name = models.CharField(max_length=100, verbose_name=_("权限名称"), blank=True, editable=False)
    code = models.CharField(max_length=50, unique=True, verbose_name=_("权限编码"), blank=True, editable=False)
    desc = models.TextField(blank=True, null=True, verbose_name=_("权限描述"))
    create_time = models.DateTimeField(auto_now_add=True, verbose_name=_("创建时间"))

    class Meta:
        verbose_name = _("权限配置")
        verbose_name_plural = _("权限配置")
        unique_together = ('role', 'form_name', 'action')
        db_table = "erp_permission_config"

    def save(self, *args, **kwargs):
        form_name_cn = dict(FORM_CHOICES).get(self.form_name, self.form_name)
        action_cn = dict(ACTION_CHOICES).get(self.action, self.action)
        self.name = f"{self.role.role_name}-{form_name_cn}-{action_cn}"
        self.code = f"{self.role.role_code}_{self.form_name}_{self.action}".lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

from django.db import models

class ApprovalFlow(models.Model):
    """审批流程主表"""
    name = models.CharField(max_length=100, verbose_name="流程名称")
    code = models.CharField(max_length=50, unique=True, verbose_name="流程编码")
    is_active = models.BooleanField(default=True, verbose_name="是否启用")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    update_time = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "审批流程"
        verbose_name_plural = "审批流程"

class ApprovalNode(models.Model):
    """审批流程节点表"""
    flow = models.ForeignKey(ApprovalFlow, on_delete=models.CASCADE, related_name="nodes", verbose_name="所属流程")
    name = models.CharField(max_length=100, verbose_name="节点名称")
    node_type = models.CharField(
        max_length=20,
        choices=[("start", "开始节点"), ("approver", "审批节点"), ("end", "结束节点")],
        default="approver",
        verbose_name="节点类型"
    )
    approver_config = models.JSONField(default=dict, verbose_name="审批人配置")  # 存储审批人类型、用户ID等
    next_nodes = models.JSONField(default=dict, verbose_name="下一个节点配置")     # 存储后续节点ID列表
    sort = models.IntegerField(default=0, verbose_name="排序")
    # 新增画布坐标字段
    x = models.FloatField(default=100.0, verbose_name="节点X坐标")
    y = models.FloatField(default=100.0, verbose_name="节点Y坐标")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    update_time = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "审批节点"
        verbose_name_plural = "审批节点"

class ApprovalInstance(models.Model):
    """审批实例表"""
    flow = models.ForeignKey(ApprovalFlow, on_delete=models.CASCADE, verbose_name="所属流程")
    create_user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="创建人")
    current_node = models.ForeignKey(ApprovalNode, on_delete=models.SET_NULL, null=True, verbose_name="当前节点")
    status = models.CharField(
        max_length=20,
        choices=[("running", "审批中"), ("approved", "已通过"), ("rejected", "已驳回")],
        default="running",
        verbose_name="审批状态"
    )
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    update_time = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "审批实例"
        verbose_name_plural = "审批实例"

class ApprovalRecord(models.Model):
    """审批记录"""
    instance = models.ForeignKey(ApprovalInstance, on_delete=models.CASCADE, related_name="records", verbose_name="审批实例")
    node = models.ForeignKey(ApprovalNode, on_delete=models.CASCADE, verbose_name="审批节点")
    approver = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="审批人")
    action = models.CharField(max_length=20, choices=[("approve", "同意"), ("reject", "驳回")], verbose_name="审批操作")
    comment = models.TextField(blank=True, null=True, verbose_name="审批意见")
    operate_time = models.DateTimeField(auto_now_add=True, verbose_name="操作时间")

    class Meta:
        verbose_name = "审批记录"
        verbose_name_plural = "审批记录"

