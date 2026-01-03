from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from functools import wraps
from .models import ERPUser, Role, PermissionConfig
import json
import logging
from django.contrib.auth.models import User
from django.http import JsonResponse

# ===================== 日志配置 =====================
logger = logging.getLogger(__name__)

# ===================== 公共装饰器 =====================
def add_cors_headers(view_func):
    """跨域响应头装饰器 - 修复OPTIONS请求处理"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # 单独处理OPTIONS预检请求
        if request.method == 'OPTIONS':
            response = JsonResponse({'code': 200, 'msg': '预检成功', 'data': {}})
            response['Access-Control-Allow-Origin'] = 'http://localhost:5173'  # 前端地址
            response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response['Access-Control-Allow-Headers'] = 'Content-Type, X-CSRFToken, X-Requested-With'
            response['Access-Control-Allow-Credentials'] = 'true'
            response['Access-Control-Max-Age'] = '86400'
            return response

        # 处理正常请求
        response = view_func(request, *args, **kwargs)
        response['Access-Control-Allow-Origin'] = 'http://localhost:5173'
        response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, X-CSRFToken, X-Requested-With'
        response['Access-Control-Allow-Credentials'] = 'true'
        response['Access-Control-Max-Age'] = '86400'
        return response

    return wrapper

def erp_login_required(view_func):
    """登录校验装饰器"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # 检查session登录状态
        if not request.session.get('erp_user_id'):
            logger.warning(f"未登录访问ERP用户接口：{request.path}，IP：{request.META.get('REMOTE_ADDR')}")
            response = JsonResponse({
                'code': 401,
                'msg': '请先登录ERP系统！',
                'data': {}
            }, status=200, json_dumps_params={'ensure_ascii': False})
            response['Access-Control-Allow-Origin'] = 'http://localhost:5173'
            response['Access-Control-Allow-Credentials'] = 'true'
            return response

        # 验证用户是否存在
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

# ===================== 1. 查询：获取ERP用户列表 =====================
@csrf_exempt
@require_http_methods(["GET", "OPTIONS"])
#@erp_login_required  # 暂时注释，方便测试
@add_cors_headers
def get_erp_users(request):
    """
    获取ERP用户列表（含角色信息）
    GET参数：page(页码)、page_size(每页条数)、keyword(搜索关键词)
    """
    if request.method == 'OPTIONS':
        return JsonResponse({'code': 200, 'msg': '预检成功', 'data': {}})

    try:
        # 1. 解析参数
        page = request.GET.get('page', 1)
        page_size = request.GET.get('page_size', 10)
        keyword = request.GET.get('keyword', '').strip()

        # 2. 参数校验
        try:
            page = int(page) if page else 1
            page_size = int(page_size) if page_size else 10
            page = 1 if page < 1 else page
            page_size = 10 if page_size < 1 or page_size > 100 else page_size
        except (ValueError, TypeError):
            page = 1
            page_size = 10

        # 3. 数据查询
        queryset = ERPUser.objects.all().order_by('id')
        if keyword:
            queryset = queryset.filter(username__icontains=keyword)

        # 4. 分页处理
        paginator = Paginator(queryset, page_size)
        try:
            page_obj = paginator.page(page)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        # 5. 序列化
        user_list = [{
            'id': user.id,
            'username': user.username,
            'role_id': user.role.id if user.role else '',
            'role_name': user.role.role_name if user.role else '未分配角色',
            'is_active': user.is_active
        } for user in page_obj.object_list]

        # 6. 返回结果
        return JsonResponse({
            'code': 200,
            'msg': 'success',
            'data': {
                'list': user_list,
                'total': paginator.count,
                'page': page_obj.number,
                'page_size': page_size,
                'total_pages': paginator.num_pages
            }
        }, json_dumps_params={'ensure_ascii': False})

    except Exception as e:
        logger.error(f"查询ERP用户失败：{str(e)}", exc_info=True)
        return JsonResponse({
            'code': 500,
            'msg': '获取用户列表失败，请稍后重试',
            'data': {}
        }, status=200, json_dumps_params={'ensure_ascii': False})

# ===================== 2. 新增：创建ERP用户 =====================
@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
@erp_login_required
@add_cors_headers
def add_erp_user(request):
    """新增ERP用户"""
    if request.method == 'OPTIONS':
        return JsonResponse({'code': 200, 'msg': '预检成功', 'data': {}})

    try:
        # 1. 解析数据
        data = json.loads(request.body) if request.content_type == 'application/json' else request.POST.dict()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        role_id = data.get('role_id')

        # 2. 校验规则
        if not username:
            return JsonResponse({'code': 400, 'msg': '请输入用户名！', 'data': {}},
                                json_dumps_params={'ensure_ascii': False})
        if not password:
            return JsonResponse({'code': 400, 'msg': '请输入密码！', 'data': {}},
                                json_dumps_params={'ensure_ascii': False})
        if len(password) < 6:
            return JsonResponse({'code': 400, 'msg': '密码长度不少于6位！', 'data': {}},
                                json_dumps_params={'ensure_ascii': False})
        if not username.strip() or not username.replace('_', '').isalnum():
            return JsonResponse({'code': 400, 'msg': '用户名仅支持字母、数字、下划线！', 'data': {}},
                                json_dumps_params={'ensure_ascii': False})
        if ERPUser.objects.filter(username=username).exists():
            return JsonResponse({'code': 400, 'msg': '用户名已存在！', 'data': {}},
                                json_dumps_params={'ensure_ascii': False})

        # 角色ID校验
        role = None
        if role_id:
            try:
                role = Role.objects.get(id=role_id)
            except Role.DoesNotExist:
                return JsonResponse({'code': 400, 'msg': '角色不存在！', 'data': {}},
                                    json_dumps_params={'ensure_ascii': False})

        # 3. 创建用户
        new_user = ERPUser.objects.create(
            username=username,
            password=password,
            role=role,
            is_active=True
        )
        # 同步创建Django User
        if not User.objects.filter(username=username).exists():
            User.objects.create_user(username=username, password=password)

        logger.info(f"管理员{request.session.get('erp_username', '未知')}新增用户：{username}")
        return JsonResponse({
            'code': 200,
            'msg': '用户新增成功！',
            'data': {
                'id': new_user.id,
                'username': new_user.username,
                'role_id': role_id or '',
                'role_name': role.role_name if role else '未分配角色'
            }
        }, json_dumps_params={'ensure_ascii': False})

    except json.JSONDecodeError:
        return JsonResponse({'code': 400, 'msg': '请求数据格式错误！', 'data': {}},
                            json_dumps_params={'ensure_ascii': False})
    except Exception as e:
        logger.error(f"新增ERP用户失败：{str(e)}", exc_info=True)
        return JsonResponse({
            'code': 500,
            'msg': '新增失败，请重试！',
            'data': {}
        }, json_dumps_params={'ensure_ascii': False})

# ===================== 3. 修改：更新用户密码 =====================
@csrf_exempt
@require_http_methods(["PUT", "OPTIONS"])
@erp_login_required
@add_cors_headers
def update_erp_user_password(request, user_id):
    """修改ERP用户密码"""
    if request.method == 'OPTIONS':
        return JsonResponse({'code': 200, 'msg': '预检成功', 'data': {}})

    try:
        data = json.loads(request.body) if request.content_type == 'application/json' else request.POST.dict()
        new_password = data.get('password', '').strip()

        if not new_password:
            return JsonResponse({'code': 400, 'msg': '密码为空，未做修改！', 'data': {}},
                                json_dumps_params={'ensure_ascii': False})
        if len(new_password) < 6:
            return JsonResponse({'code': 400, 'msg': '密码长度不少于6位！', 'data': {}},
                                json_dumps_params={'ensure_ascii': False})

        try:
            user = ERPUser.objects.get(id=user_id)
            if user.username == 'admin':
                return JsonResponse({'code': 403, 'msg': '禁止修改管理员密码！', 'data': {}},
                                    json_dumps_params={'ensure_ascii': False})

            user.password = new_password
            user.save()
            # 同步更新Django User
            try:
                django_user = User.objects.get(username=user.username)
                django_user.set_password(new_password)
                django_user.save()
            except User.DoesNotExist:
                pass

            logger.info(f"管理员修改用户{user.username}密码")
            return JsonResponse({'code': 200, 'msg': '密码修改成功！', 'data': {}},
                                json_dumps_params={'ensure_ascii': False})

        except ERPUser.DoesNotExist:
            return JsonResponse({'code': 404, 'msg': '用户不存在！', 'data': {}},
                                json_dumps_params={'ensure_ascii': False})

    except json.JSONDecodeError:
        return JsonResponse({'code': 400, 'msg': '请求数据格式错误！', 'data': {}},
                            json_dumps_params={'ensure_ascii': False})
    except Exception as e:
        logger.error(f"修改ERP用户密码失败：{str(e)}", exc_info=True)
        return JsonResponse({
            'code': 500,
            'msg': '修改失败，请重试！',
            'data': {}
        }, json_dumps_params={'ensure_ascii': False})

# ===================== 4. 修改：更新用户角色 =====================
@csrf_exempt
@require_http_methods(["PUT", "OPTIONS"])
@erp_login_required
@add_cors_headers
def update_erp_user_role(request, user_id):
    """修改ERP用户角色"""
    if request.method == 'OPTIONS':
        return JsonResponse({'code': 200, 'msg': '预检成功', 'data': {}})

    try:
        data = json.loads(request.body) if request.content_type == 'application/json' else request.POST.dict()
        role_id = data.get('role_id')

        try:
            user = ERPUser.objects.get(id=user_id)
            if user.username == 'admin':
                return JsonResponse({'code': 403, 'msg': '禁止修改管理员角色！', 'data': {}},
                                    json_dumps_params={'ensure_ascii': False})

            # 角色校验
            role = None
            if role_id:
                try:
                    role = Role.objects.get(id=role_id)
                except Role.DoesNotExist:
                    return JsonResponse({'code': 400, 'msg': '角色不存在！', 'data': {}},
                                        json_dumps_params={'ensure_ascii': False})

            user.role = role
            user.save()

            logger.info(f"管理员修改用户{user.username}角色为：{role.role_name if role else '无'}")
            return JsonResponse({
                'code': 200,
                'msg': '角色修改成功！',
                'data': {
                    'role_id': role_id or '',
                    'role_name': role.role_name if role else '未分配角色'
                }
            }, json_dumps_params={'ensure_ascii': False})

        except ERPUser.DoesNotExist:
            return JsonResponse({'code': 404, 'msg': '用户不存在！', 'data': {}},
                                json_dumps_params={'ensure_ascii': False})

    except json.JSONDecodeError:
        return JsonResponse({'code': 400, 'msg': '请求数据格式错误！', 'data': {}},
                            json_dumps_params={'ensure_ascii': False})
    except Exception as e:
        logger.error(f"修改ERP用户角色失败：{str(e)}", exc_info=True)
        return JsonResponse({
            'code': 500,
            'msg': '修改失败，请重试！',
            'data': {}
        }, json_dumps_params={'ensure_ascii': False})

# ===================== 5. 删除：删除ERP用户 =====================
@csrf_exempt
@require_http_methods(["DELETE", "OPTIONS"])
@erp_login_required
@add_cors_headers
def delete_erp_user(request, user_id):
    """删除ERP用户"""
    if request.method == 'OPTIONS':
        return JsonResponse({'code': 200, 'msg': '预检成功', 'data': {}})

    try:
        try:
            user = ERPUser.objects.get(id=user_id)
            if user.username == 'admin':
                return JsonResponse({'code': 403, 'msg': '禁止删除管理员账号！', 'data': {}},
                                    json_dumps_params={'ensure_ascii': False})

            username = user.username
            user.delete()
            # 同步删除Django User
            try:
                django_user = User.objects.get(username=username)
                django_user.delete()
            except User.DoesNotExist:
                pass

            logger.info(f"管理员删除用户：{username}")
            return JsonResponse({'code': 200, 'msg': '用户删除成功！', 'data': {}},
                                json_dumps_params={'ensure_ascii': False})

        except ERPUser.DoesNotExist:
            return JsonResponse({'code': 404, 'msg': '用户不存在！', 'data': {}},
                                json_dumps_params={'ensure_ascii': False})

    except Exception as e:
        logger.error(f"删除ERP用户失败：{str(e)}", exc_info=True)
        return JsonResponse({
            'code': 500,
            'msg': '删除失败，请重试！',
            'data': {}
        }, json_dumps_params={'ensure_ascii': False})

# ===================== 6. 权限：获取当前用户的权限列表 =====================
@csrf_exempt
@require_http_methods(["GET", "OPTIONS"])
@erp_login_required
@add_cors_headers
def get_user_permissions(request):
    """获取当前登录用户的权限列表"""
    if request.method == 'OPTIONS':
        return JsonResponse({'code': 200, 'msg': '预检成功', 'data': {}})

    try:
        user = ERPUser.objects.get(id=request.session['erp_user_id'])

        # 管理员返回所有权限
        if user.role and user.role.role_code == 'admin':
            permissions = [
                'material_view', 'material_add', 'material_edit', 'material_delete',
                'material_export', 'erp_user_view', 'erp_user_add', 'erp_user_edit', 'erp_user_delete'
            ]
        else:
            permissions = []
            if user.role:
                permission_configs = PermissionConfig.objects.filter(role=user.role)
                for pc in permission_configs:
                    if '_' in pc.code:
                        parts = pc.code.split('_')
                        # 优化：防止索引越界
                        if len(parts) >= 3:
                            perm_code = f"{parts[-2]}_{parts[-1]}"
                            permissions.append(perm_code)

        permissions = list(set(permissions))  # 去重
        return JsonResponse({
            'code': 200,
            'msg': 'success',
            'data': permissions
        }, json_dumps_params={'ensure_ascii': False})  # 修复：拼写错误修正

    except ERPUser.DoesNotExist:
        return JsonResponse({
            'code': 401,
            'msg': '用户不存在',
            'data': []
        }, json_dumps_params={'ensure_ascii': False})
    except Exception as e:
        logger.error(f"获取用户权限失败：{str(e)}", exc_info=True)
        return JsonResponse({
            'code': 500,
            'msg': '获取权限失败，请稍后重试',
            'data': []
        }, json_dumps_params={'ensure_ascii': False})