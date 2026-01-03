from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from .models import ApprovalFlow, ApprovalNode, ApprovalInstance, ApprovalRecord
from .serializers import (
    ApprovalFlowSerializer, ApprovalNodeSerializer,
    ApprovalInstanceSerializer, ApprovalRecordSerializer
)
import uuid

# ========== 全局跨域装饰器（优化） ==========
def drf_cors_decorator(func):
    def wrapper(request, *args, **kwargs):
        response = func(request, *args, **kwargs)
        response['Access-Control-Allow-Origin'] = 'http://localhost:5173'
        response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, X-CSRFToken, X-Requested-With, Authorization'
        response['Access-Control-Allow-Credentials'] = 'true'
        return response
    return wrapper

# ========== 登录态校验装饰器（新增：适配DRF） ==========
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

# 简化登录校验：使用DRF内置权限类 + JWT认证
def login_required(view_func):
    """DRF视图登录校验装饰器"""
    @authentication_classes([JWTAuthentication])
    @permission_classes([IsAuthenticated])
    def wrapper(request, *args, **kwargs):
        return view_func(request, *args, **kwargs)
    return wrapper

# ========== 审批流程CRUD视图（修复版） ==========
@method_decorator(csrf_exempt, name='dispatch')
class ApprovalFlowListView(APIView):
    """审批流程列表接口"""
    @drf_cors_decorator
    def get(self, request):
        try:
            flows = ApprovalFlow.objects.filter(is_active=True).order_by('-create_time')
            serializer = ApprovalFlowSerializer(flows, many=True)
            return Response({
                'code': 200,
                'msg': 'success',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'code': 500,
                'msg': f'获取流程列表失败：{str(e)}',
                'data': []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @drf_cors_decorator
    def options(self, request):
        return Response({}, status=status.HTTP_200_OK)

@method_decorator(csrf_exempt, name='dispatch')
class ApprovalFlowDetailView(APIView):
    """审批流程详情接口（含节点）"""
    @drf_cors_decorator
    def get(self, request, pk):
        try:
            flow = ApprovalFlow.objects.get(id=pk)
            nodes = ApprovalNode.objects.filter(flow=flow).order_by('sort')
            return Response({
                'code': 200,
                'msg': 'success',
                'data': {
                    'info': ApprovalFlowSerializer(flow).data,
                    'nodes': ApprovalNodeSerializer(nodes, many=True).data
                }
            }, status=status.HTTP_200_OK)
        except ApprovalFlow.DoesNotExist:
            return Response({
                'code': 404,
                'msg': '流程不存在',
                'data': {}
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'code': 500,
                'msg': f'获取流程详情失败：{str(e)}',
                'data': {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @drf_cors_decorator
    def options(self, request, pk):
        return Response({}, status=status.HTTP_200_OK)

@method_decorator(csrf_exempt, name='dispatch')
class ApprovalFlowCreateView(APIView):
    """创建审批流程接口"""
    @drf_cors_decorator
    def post(self, request):
        try:
            # 1. 构造流程数据（自动生成唯一编码）
            flow_data = request.data.get('info', {})
            if not flow_data.get('code'):
                flow_data['code'] = f"FLOW_{uuid.uuid4().hex[:8].upper()}"
            flow_data.setdefault('is_active', True)

            # 2. 验证并保存流程
            serializer = ApprovalFlowSerializer(data=flow_data)
            if serializer.is_valid():
                flow = serializer.save()

                # 3. 批量保存节点（兼容前端空ID节点）
                nodes = request.data.get('nodes', [])
                node_list = []
                for idx, item in enumerate(nodes):
                    # 兼容approver_config格式（前端可能传数组）
                    approver_config = item.get('approver_config', {})
                    if isinstance(approver_config, list):
                        approver_config = {}

                    # 不强制要求ID，由数据库自增生成
                    node_list.append(ApprovalNode(
                        flow=flow,
                        name=item.get('name', ''),
                        node_type=item.get('node_type', 'approver'),
                        approver_config=approver_config,
                        next_nodes=item.get('next_nodes', {}),
                        sort=item.get('sort', idx),
                        x=item.get('x', 100),
                        y=item.get('y', 100)
                    ))
                ApprovalNode.objects.bulk_create(node_list)

                return Response({
                    'code': 200,
                    'msg': '流程创建成功',
                    'data': {'id': flow.id, 'code': flow.code}
                }, status=status.HTTP_200_OK)
            else:
                # 返回详细的验证错误信息
                return Response({
                    'code': 400,
                    'msg': '参数验证失败',
                    'data': {
                        'errors': serializer.errors,
                        'request_data': request.data
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'code': 500,
                'msg': f'创建流程失败：{str(e)}',
                'data': {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @drf_cors_decorator
    def options(self, request):
        return Response({}, status=status.HTTP_200_OK)

@method_decorator(csrf_exempt, name='dispatch')
class ApprovalFlowUpdateView(APIView):
    """更新审批流程接口"""
    @drf_cors_decorator
    def put(self, request, pk):
        try:
            flow = ApprovalFlow.objects.get(id=pk)
            flow_data = request.data.get('info', {})
            flow_data.pop('code', None)  # 禁止修改流程编码

            # 验证并更新流程
            serializer = ApprovalFlowSerializer(flow, data=flow_data, partial=True)
            if serializer.is_valid():
                serializer.save()

                # 重置节点（先删后加）
                ApprovalNode.objects.filter(flow=flow).delete()
                nodes = request.data.get('nodes', [])
                node_list = []
                for idx, item in enumerate(nodes):
                    # 兼容approver_config格式
                    approver_config = item.get('approver_config', {})
                    if isinstance(approver_config, list):
                        approver_config = {}

                    # 兼容前端空ID节点
                    node_list.append(ApprovalNode(
                        flow=flow,
                        name=item.get('name', ''),
                        node_type=item.get('node_type', 'approver'),
                        approver_config=approver_config,
                        next_nodes=item.get('next_nodes', {}),
                        sort=item.get('sort', idx),
                        x=item.get('x', 100),
                        y=item.get('y', 100)
                    ))
                ApprovalNode.objects.bulk_create(node_list)

                return Response({
                    'code': 200,
                    'msg': '流程更新成功',
                    'data': {'id': flow.id}
                }, status=status.HTTP_200_OK)
            else:
                # 返回详细的验证错误信息
                return Response({
                    'code': 400,
                    'msg': '参数验证失败',
                    'data': {
                        'errors': serializer.errors,
                        'request_data': request.data
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
        except ApprovalFlow.DoesNotExist:
            return Response({
                'code': 404,
                'msg': '流程不存在',
                'data': {}
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'code': 500,
                'msg': f'更新流程失败：{str(e)}',
                'data': {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @drf_cors_decorator
    def options(self, request, pk):
        return Response({}, status=status.HTTP_200_OK)

# ========== 审批节点视图 ==========
@method_decorator(csrf_exempt, name='dispatch')
class ApprovalNodeListView(APIView):
    """获取流程节点列表"""
    @drf_cors_decorator
    def get(self, request, flow_id):
        try:
            nodes = ApprovalNode.objects.filter(flow_id=flow_id).order_by('sort')
            serializer = ApprovalNodeSerializer(nodes, many=True)
            return Response({
                'code': 200,
                'msg': 'success',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'code': 500,
                'msg': f'获取节点列表失败：{str(e)}',
                'data': []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @drf_cors_decorator
    def options(self, request, flow_id):
        return Response({}, status=status.HTTP_200_OK)

@method_decorator(csrf_exempt, name='dispatch')
class ApprovalNodeSaveView(APIView):
    """批量保存节点"""
    @drf_cors_decorator
    def post(self, request):
        flow_id = request.data.get("flow_id")
        nodes = request.data.get("nodes", [])
        try:
            flow = ApprovalFlow.objects.get(id=flow_id)
            # 先删除旧节点
            ApprovalNode.objects.filter(flow=flow).delete()
            # 批量创建新节点
            node_list = [
                ApprovalNode(
                    flow=flow,
                    name=item["name"],
                    node_type=item["node_type"],
                    approver_config=item.get("approver_config", {}),
                    next_nodes=item.get("next_nodes", {}),
                    sort=item["sort"],
                    x=item.get("x", 100),
                    y=item.get("y", 100)
                ) for item in nodes
            ]
            ApprovalNode.objects.bulk_create(node_list)
            return Response({
                'code': 200,
                'msg': "节点保存成功",
                'data': {}
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'code': 500,
                'msg': str(e),
                'data': {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @drf_cors_decorator
    def options(self, request):
        return Response({}, status=status.HTTP_200_OK)

# ========== 审批实例视图（修复登录态校验） ==========
@method_decorator(csrf_exempt, name='dispatch')
class ApprovalInstanceCreateView(APIView):
    """创建审批实例（适配DRF登录校验）"""
    # 使用JWT认证 + 登录权限校验
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @drf_cors_decorator
    def post(self, request):
        try:
            request.data['create_user'] = request.user.id
            serializer = ApprovalInstanceSerializer(data=request.data)
            if serializer.is_valid():
                instance = serializer.save()
                return Response({
                    'code': 200,
                    'msg': '实例创建成功',
                    'data': {'id': instance.id}
                }, status=status.HTTP_200_OK)
            return Response({
                'code': 400,
                'msg': '参数验证失败',
                'data': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'code': 500,
                'msg': f'创建实例失败：{str(e)}',
                'data': {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @drf_cors_decorator
    def options(self, request):
        return Response({}, status=status.HTTP_200_OK)

@method_decorator(csrf_exempt, name='dispatch')
class ApprovalInstanceOperateView(APIView):
    """审批操作（同意/驳回）"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @drf_cors_decorator
    def post(self, request):
        instance_id = request.data.get("instance_id")
        action = request.data.get("action")
        comment = request.data.get("comment", "")
        approver = request.user

        try:
            instance = ApprovalInstance.objects.get(id=instance_id)
            # 验证审批实例状态
            if instance.status != 'running':
                return Response({
                    'code': 400,
                    'msg': '审批已结束，无法操作',
                    'data': {}
                }, status=status.HTTP_400_BAD_REQUEST)

            current_node = instance.current_node
            # 记录审批操作
            ApprovalRecord.objects.create(
                instance=instance,
                node=current_node,
                approver=approver,
                action=action,
                comment=comment
            )

            # 处理流转逻辑
            if action == "approve":
                next_node_ids = current_node.next_nodes.get("next", [])
                if next_node_ids:
                    next_node = ApprovalNode.objects.get(id=next_node_ids[0])
                    instance.current_node = next_node
                    # 如果是结束节点，更新状态为已通过
                    if next_node.node_type == "end":
                        instance.status = "approved"
                instance.save()
            elif action == "reject":
                instance.status = "rejected"
                instance.save()

            return Response({
                'code': 200,
                'msg': "操作成功",
                'data': {"status": instance.status}
            }, status=status.HTTP_200_OK)
        except ApprovalInstance.DoesNotExist:
            return Response({
                'code': 404,
                'msg': '审批实例不存在',
                'data': {}
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'code': 500,
                'msg': str(e),
                'data': {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @drf_cors_decorator
    def options(self, request):
        return Response({}, status=status.HTTP_200_OK)

@method_decorator(csrf_exempt, name='dispatch')
class ApprovalInstanceDetailView(APIView):
    """审批实例详情（含审批记录）"""
    @drf_cors_decorator
    def get(self, request, pk):
        try:
            instance = ApprovalInstance.objects.get(id=pk)
            # 获取审批记录（按操作时间倒序）
            records = ApprovalRecord.objects.filter(instance=instance).order_by('-operate_time')
            return Response({
                'code': 200,
                'msg': 'success',
                'data': {
                    'instance': ApprovalInstanceSerializer(instance).data,
                    'records': ApprovalRecordSerializer(records, many=True).data
                }
            }, status=status.HTTP_200_OK)
        except ApprovalInstance.DoesNotExist:
            return Response({
                'code': 404,
                'msg': '审批实例不存在',
                'data': {}
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'code': 500,
                'msg': f'获取实例详情失败：{str(e)}',
                'data': {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @drf_cors_decorator
    def options(self, request, pk):
        return Response({}, status=status.HTTP_200_OK)