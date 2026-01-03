from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from functools import wraps
from django.http import JsonResponse
import json
import logging
from .models import Role, PermissionConfig, ERPUser
# role_views.py 顶部添加
FORM_CHOICES = [
    ('material', '物料管理'),
    ('erp_user', 'ERP用户管理'),
    ('role', '角色管理'),
    ('order', '订单管理'),
    ('product', '产品管理'),
    ('contract', '合同管理'),
]

ACTION_CHOICES = [
    ('view', '查看'),
    ('add', '新增'),
    ('edit', '编辑'),
    ('delete', '删除'),
    ('export', '导出'),
]
# 日志配置
logger = logging.getLogger(__name__)


# 复用你已有的跨域装饰器
def add_cors_headers(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        response = view_func(request, *args, **kwargs)
        response['Access-Control-Allow-Origin'] = 'http://localhost:5173'
        response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response['Access-Control-Allow-Credentials'] = 'true'
        return response

    return wrapper


# 复用你已有的登录校验装饰器
def erp_login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('erp_user_id'):
            response = JsonResponse({
                'code': 401,
                'msg': '请先登录ERP系统！',
                'data': {}
            }, status=200, json_dumps_params={'ensure_ascii': False})
            response['Access-Control-Allow-Origin'] = 'http://localhost:5173'
            response['Access-Control-Allow-Credentials'] = 'true'
            return response

        try:
            ERPUser.objects.get(id=request.session['erp_user_id'])
        except ERPUser.DoesNotExist:
            request.session.flush()
            response = JsonResponse({
                'code': 401,
                'msg': '请先登录ERP系统！',
                'data': {}
            }, status=200, json_dumps_params={'ensure_ascii': False})
            response['Access-Control-Allow-Origin'] = 'http://localhost:5173'
            response['Access-Control-Allow-Credentials'] = 'true'
            return response

        return view_func(request, *args, **kwargs)

    return wrapper


# ===================== 角色列表接口 =====================
@csrf_exempt
@require_http_methods(["GET", "OPTIONS"])
@erp_login_required
@add_cors_headers
def get_roles(request):
    """角色列表分页接口（适配前端）"""
    if request.method == 'OPTIONS':
        return JsonResponse({'code': 200, 'msg': '预检成功', 'data': {}})

    try:
        # 分页参数
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
        page = 1 if page < 1 else page
        page_size = 10 if page_size < 1 or page_size > 100 else page_size

        # 查询角色
        roles = Role.objects.all().order_by('-create_time')
        paginator = Paginator(roles, page_size)

        try:
            page_obj = paginator.page(page)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        # 序列化（包含权限配置）
        role_list = []
        for role in page_obj.object_list:
            # 获取角色的所有权限
            permissions = []
            for perm in role.permissions.all():
                permissions.append({
                    'form_name': perm.form_name,
                    'form_name_text': dict(FORM_CHOICES).get(perm.form_name, perm.form_name),
                    'action': perm.action,
                    'action_text': dict(ACTION_CHOICES).get(perm.action, perm.action)
                })

            role_list.append({
                'id': role.id,
                'role_name': role.role_name,
                'role_code': role.role_code,
                'desc': role.desc or '',
                'permissions': permissions,
                'create_time': role.create_time.strftime('%Y-%m-%d %H:%M:%S')
            })

        return JsonResponse({
            'code': 200,
            'msg': 'success',
            'data': {
                'list': role_list,
                'total': paginator.count,
                'page': page_obj.number,
                'page_size': page_size,
                'total_pages': paginator.num_pages
            }
        }, json_dumps_params={'ensure_ascii': False})

    except Exception as e:
        logger.error(f"获取角色列表失败：{str(e)}", exc_info=True)
        return JsonResponse({
            'code': 500,
            'msg': f'获取角色列表失败：{str(e)}',
            'data': {}
        }, json_dumps_params={'ensure_ascii': False})


# ===================== 新增角色接口 =====================
@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
@erp_login_required
@add_cors_headers
# ===================== 新增角色接口 =====================
@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
@erp_login_required
@add_cors_headers
def add_role(request):
    """新增角色（包含权限配置）"""
    if request.method == 'OPTIONS':
        return JsonResponse({'code': 200, 'msg': '预检成功', 'data': {}})

    try:
        # 解析请求数据
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST.dict()

        # 参数校验
        role_name = data.get('role_name', '').strip()
        role_code = data.get('role_code', '').strip()
        # 🔥 兼容空权限配置
        permission_config = data.get('permission_config', {}) or {}

        if not role_name:
            return JsonResponse({'code': 400, 'msg': '角色名称不能为空', 'data': {}},
                                json_dumps_params={'ensure_ascii': False})
        if not role_code:
            return JsonResponse({'code': 400, 'msg': '角色编码不能为空', 'data': {}},
                                json_dumps_params={'ensure_ascii': False})
        if Role.objects.filter(role_name=role_name).exists():
            return JsonResponse({'code': 400, 'msg': '角色名称已存在', 'data': {}},
                                json_dumps_params={'ensure_ascii': False})
        if Role.objects.filter(role_code=role_code).exists():
            return JsonResponse({'code': 400, 'msg': '角色编码已存在', 'data': {}},
                                json_dumps_params={'ensure_ascii': False})
        # 角色编码格式校验
        import re
        if not re.match(r'^[a-zA-Z0-9_]{2,30}$', role_code):
            return JsonResponse({'code': 400, 'msg': '角色编码仅支持字母、数字、下划线，长度2-30位', 'data': {}},
                                json_dumps_params={'ensure_ascii': False})

        # 创建角色
        role = Role.objects.create(
            role_name=role_name,
            role_code=role_code,
            desc=data.get('desc', '').strip()
        )

        # 🔥 优化权限配置逻辑：兼容空数组
        form_choices = [f[0] for f in FORM_CHOICES]
        action_choices = [a[0] for a in ACTION_CHOICES]

        for form_name, actions in permission_config.items():
            # 跳过无效表单类型
            if form_name not in form_choices:
                continue
            # 确保 actions 是数组（兼容前端异常传值）
            if not isinstance(actions, list):
                continue
            # 遍历权限并创建
            for action in actions:
                if action in action_choices:
                    PermissionConfig.objects.create(
                        role=role,
                        form_name=form_name,
                        action=action
                    )

        logger.info(f"新增角色成功：{role_name}({role_code})")
        return JsonResponse({
            'code': 200,
            'msg': '新增角色成功',
            'data': {'id': role.id, 'role_code': role_code}
        }, json_dumps_params={'ensure_ascii': False})

    except Exception as e:
        logger.error(f"新增角色失败：{str(e)}", exc_info=True)
        return JsonResponse({
            'code': 500,
            'msg': f'新增角色失败：{str(e)}',
            'data': {}
        }, json_dumps_params={'ensure_ascii': False})


@csrf_exempt
@require_http_methods(["PUT", "OPTIONS"])
@erp_login_required
@add_cors_headers
def update_role(request, role_id):
    """编辑角色（更新名称、描述、权限）"""
    if request.method == 'OPTIONS':
        return JsonResponse({'code': 200, 'msg': '预检成功', 'data': {}})

    try:
        # 校验角色ID
        try:
            role_id = int(role_id)
            role = Role.objects.get(id=role_id)
        except (ValueError, Role.DoesNotExist):
            return JsonResponse({'code': 404, 'msg': '角色不存在', 'data': {}},
                                json_dumps_params={'ensure_ascii': False})

        # 禁止修改admin角色
        if role.role_code == 'admin':
            return JsonResponse({'code': 403, 'msg': '禁止修改系统管理员角色', 'data': {}},
                                json_dumps_params={'ensure_ascii': False})

        # 解析请求数据
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST.dict()

        # 更新基本信息
        role_name = data.get('role_name', '').strip()
        if role_name and role_name != role.role_name:
            if Role.objects.filter(role_name=role_name).exists():
                return JsonResponse({'code': 400, 'msg': '角色名称已存在', 'data': {}},
                                    json_dumps_params={'ensure_ascii': False})
            role.role_name = role_name
        role.desc = data.get('desc', '').strip()
        role.save()

        # 🔥 优化权限更新逻辑：兼容空权限
        # 先删除原有权限
        PermissionConfig.objects.filter(role=role).delete()
        # 兼容空权限配置
        permission_config = data.get('permission_config', {}) or {}
        form_choices = [f[0] for f in FORM_CHOICES]
        action_choices = [a[0] for a in ACTION_CHOICES]

        for form_name, actions in permission_config.items():
            if form_name not in form_choices:
                continue
            if not isinstance(actions, list):
                continue
            for action in actions:
                if action in action_choices:
                    PermissionConfig.objects.create(
                        role=role,
                        form_name=form_name,
                        action=action
                    )

        logger.info(f"更新角色成功：{role.role_name}({role.id})")
        return JsonResponse({
            'code': 200,
            'msg': '更新角色成功',
            'data': {'id': role.id}
        }, json_dumps_params={'ensure_ascii': False})

    except Exception as e:
        logger.error(f"更新角色失败：{str(e)}", exc_info=True)
        return JsonResponse({
            'code': 500,
            'msg': f'更新角色失败：{str(e)}',
            'data': {}
        }, json_dumps_params={'ensure_ascii': False})
# ===================== 删除角色接口 =====================
@csrf_exempt
@require_http_methods(["DELETE", "OPTIONS"])
@erp_login_required
@add_cors_headers
def delete_role(request, role_id):
    """删除角色（单个）"""
    if request.method == 'OPTIONS':
        return JsonResponse({'code': 200, 'msg': '预检成功', 'data': {}})

    try:
        # 校验角色ID
        try:
            role_id = int(role_id)
            role = Role.objects.get(id=role_id)
        except (ValueError, Role.DoesNotExist):
            return JsonResponse({'code': 404, 'msg': '角色不存在', 'data': {}},
                                json_dumps_params={'ensure_ascii': False})

        # 禁止删除admin角色
        if role.role_code == 'admin':
            return JsonResponse({'code': 403, 'msg': '禁止删除系统管理员角色', 'data': {}},
                                json_dumps_params={'ensure_ascii': False})

        # 检查是否有用户关联该角色
        if ERPUser.objects.filter(role=role).exists():
            return JsonResponse({'code': 400, 'msg': '该角色已关联用户，无法删除', 'data': {}},
                                json_dumps_params={'ensure_ascii': False})

        # 删除角色（级联删除权限配置）
        role_name = role.role_name
        role.delete()

        logger.info(f"删除角色成功：{role_name}({role_id})")
        return JsonResponse({
            'code': 200,
            'msg': '删除角色成功',
            'data': {}
        }, json_dumps_params={'ensure_ascii': False})

    except Exception as e:
        logger.error(f"删除角色失败：{str(e)}", exc_info=True)
        return JsonResponse({
            'code': 500,
            'msg': f'删除角色失败：{str(e)}',
            'data': {}
        }, json_dumps_params={'ensure_ascii': False})


# ===================== 批量删除角色接口 =====================
@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
@erp_login_required
@add_cors_headers
def batch_delete_roles(request):
    """批量删除角色"""
    if request.method == 'OPTIONS':
        return JsonResponse({'code': 200, 'msg': '预检成功', 'data': {}})

    try:
        # 解析请求数据
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST.dict()

        role_ids = data.get('ids', [])
        if not isinstance(role_ids, list) or len(role_ids) == 0:
            return JsonResponse({'code': 400, 'msg': '请选择要删除的角色', 'data': {}},
                                json_dumps_params={'ensure_ascii': False})

        success_ids = []
        fail_ids = []
        for role_id in role_ids:
            try:
                role = Role.objects.get(id=role_id)
                # 禁止删除admin
                if role.role_code == 'admin':
                    fail_ids.append({'id': role_id, 'msg': '禁止删除系统管理员角色'})
                    continue
                # 检查用户关联
                if ERPUser.objects.filter(role=role).exists():
                    fail_ids.append({'id': role_id, 'msg': '该角色已关联用户，无法删除'})
                    continue
                # 删除角色
                role.delete()
                success_ids.append(role_id)
            except Role.DoesNotExist:
                fail_ids.append({'id': role_id, 'msg': '角色不存在'})
            except Exception as e:
                fail_ids.append({'id': role_id, 'msg': str(e)})

        return JsonResponse({
            'code': 200,
            'msg': f'批量删除完成：成功{len(success_ids)}条，失败{len(fail_ids)}条',
            'data': {
                'success_ids': success_ids,
                'fail_ids': fail_ids
            }
        }, json_dumps_params={'ensure_ascii': False})

    except Exception as e:
        logger.error(f"批量删除角色失败：{str(e)}", exc_info=True)
        return JsonResponse({
            'code': 500,
            'msg': f'批量删除角色失败：{str(e)}',
            'data': {}
        }, json_dumps_params={'ensure_ascii': False})


# ===================== 权限校验装饰器（业务接口用） =====================
def permission_required(form_name, action):
    """
    权限校验装饰器：校验用户是否有某模块的某操作权限
    使用示例：@permission_required('material', 'edit')
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # 先校验登录
            if not request.session.get('erp_user_id'):
                response = JsonResponse({
                    'code': 401,
                    'msg': '请先登录ERP系统！',
                    'data': {}
                }, status=200, json_dumps_params={'ensure_ascii': False})
                response['Access-Control-Allow-Origin'] = 'http://localhost:5173'
                response['Access-Control-Allow-Credentials'] = 'true'
                return response

            # 获取用户
            try:
                user = ERPUser.objects.get(id=request.session['erp_user_id'])
            except ERPUser.DoesNotExist:
                request.session.flush()
                response = JsonResponse({
                    'code': 401,
                    'msg': '请先登录ERP系统！',
                    'data': {}
                }, status=200, json_dumps_params={'ensure_ascii': False})
                response['Access-Control-Allow-Origin'] = 'http://localhost:5173'
                response['Access-Control-Allow-Credentials'] = 'true'
                return response

            # 校验权限（admin角色默认拥有所有权限）
            if not user.has_permission(form_name, action):
                return JsonResponse({
                    'code': 403,
                    'msg': f'您没有{dict(FORM_CHOICES).get(form_name, form_name)}的{dict(ACTION_CHOICES).get(action, action)}权限',
                    'data': {}
                }, json_dumps_params={'ensure_ascii': False})

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator