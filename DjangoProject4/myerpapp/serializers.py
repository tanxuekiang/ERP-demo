
from rest_framework import serializers
from .models import Material, MaterialFile,ApprovalFlow, ApprovalNode, ApprovalInstance, ApprovalRecord
from rest_framework import serializers

class ApprovalNodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApprovalNode
        fields = ["id", "flow", "name", "node_type", "approver_config", "next_nodes", "sort", "x", "y"]  # 包含x、y字段

class ApprovalFlowSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApprovalFlow
        fields = ["id", "name", "code", "is_active", "create_time", "update_time"]

class ApprovalRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApprovalRecord
        fields = ["id", "instance", "node", "approver", "action", "comment", "operate_time"]

class ApprovalInstanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApprovalInstance
        fields = ["id", "flow", "create_user", "current_node", "status", "create_time", "update_time"]

class MaterialFileSerializer(serializers.ModelSerializer):
    """物料附件序列化器"""

    class Meta:
        model = MaterialFile
        fields = ["id", "file", "file_name", "file_size", "create_time"]


class MaterialSerializer(serializers.ModelSerializer):
    """物料信息序列化器"""
    # 嵌套返回附件信息
    material_files = MaterialFileSerializer(many=True, read_only=True)

    class Meta:
        model = Material
        fields = [
            "id", "name", "code", "category", "unit",
            "supplier", "quantity", "desc", "files",
            "material_files", "create_time", "update_time"
        ]
        read_only_fields = ["id", "create_time", "update_time"]