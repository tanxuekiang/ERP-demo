from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from functools import wraps
from .models import Material, ERPUser  # 导入自定义模型
import json
import logging
from django.contrib.auth.models import User
from django.http import JsonResponse

# ===================== 关键修复：初始化 logger =====================
# 全局 logger 初始化（解决 NameError: name 'logger' is not defined）
logger = logging.getLogger(__name__)


# ===================== 跨域响应头装饰器（修复：支持Cookie跨域） =====================
def add_cors_headers(view_func):
    """
    修复：添加跨域响应头，支持Cookie跨域传递
    """

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # 先执行原视图函数
        response = view_func(request, *args, **kwargs)

        # 核心修复：指定前端实际域名（替换为你的前端地址，如http://localhost:5173）
        response['Access-Control-Allow-Origin'] = 'http://localhost:5173'
        response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        # 允许跨域携带Cookie（关键）
        response['Access-Control-Allow-Credentials'] = 'true'

        return response

    return wrapper


# ===================== 核心：登录校验装饰器（增强版+统一提示） =====================
def erp_login_required(view_func):
    """
    自定义装饰器：校验ERP用户登录状态
    - 未登录返回统一提示：请先登录ERP系统！
    - 记录未登录访问日志
    """

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # 检查session中的登录标识
        if not request.session.get('erp_user_id'):
            logger.warning(f"未登录访问受保护接口：{request.path}，IP：{request.META.get('REMOTE_ADDR')}")
            response = JsonResponse({
                'code': 401,
                'msg': '请先登录ERP系统！',  # 统一提示文案
                'data': {}
            }, status=200, json_dumps_params={'ensure_ascii': False})  # 统一200状态码
            # 跨域头（修复：指定前端域名）
            response['Access-Control-Allow-Origin'] = 'http://localhost:5173'
            response['Access-Control-Allow-Credentials'] = 'true'
            return response

        # 验证用户是否存在（防止session篡改）
        try:
            ERPUser.objects.get(id=request.session['erp_user_id'])
        except ERPUser.DoesNotExist:
            request.session.flush()  # 清空无效session
            response = JsonResponse({
                'code': 401,
                'msg': '请先登录ERP系统！',  # 统一提示文案
                'data': {}
            }, status=200, json_dumps_params={'ensure_ascii': False})
            # 跨域头（修复：指定前端域名）
            response['Access-Control-Allow-Origin'] = 'http://localhost:5173'
            response['Access-Control-Allow-Credentials'] = 'true'
            return response

        return view_func(request, *args, **kwargs)

    return wrapper


# ===================== 辅助函数：初始化默认管理员（明文版） =====================
def init_default_admin():
    """
    初始化默认管理员账号：admin/123456（密码明文存储）
    - 仅首次运行创建
    - 生产环境建议删除此函数
    """
    try:
        if not ERPUser.objects.filter(username='admin').exists():
            ERPUser.objects.create(
                username='admin',
                password='123456'  # 明文存储
            )
            # 同步创建Django User
            if not User.objects.filter(username='admin').exists():
                User.objects.create_user(username='admin', password='123456')
            logger.info("✅ 默认管理员账号已创建：admin/123456（明文密码）")
    except Exception as e:
        logger.error(f"初始化默认管理员失败：{str(e)}")


# ===================== 注册接口（修复版：跨域+关联ERPUser+完整校验） =====================
@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])  # 新增OPTIONS支持
@add_cors_headers  # 新增跨域装饰器
def user_register(request):
    """
    ERP用户注册接口
    - 支持跨域
    - 同步创建Django User和ERPUser
    - 完整参数校验
    """
    # 处理OPTIONS预检请求
    if request.method == 'OPTIONS':
        response = JsonResponse({
            'code': 200,
            'msg': '预检成功',
            'data': {}
        }, status=200)
        response['Access-Control-Allow-Origin'] = 'http://localhost:5173'
        response['Access-Control-Allow-Credentials'] = 'true'
        return response

    try:
        # 1. 解析请求数据
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST.dict()

        username = data.get('username', '').strip()
        password = data.get('password', '').strip()

        # 2. 完整参数校验
        if not username:
            return JsonResponse({
                'code': 400,
                'msg': '请设置注册账号',
                'data': {}
            }, json_dumps_params={'ensure_ascii': False})

        if not password:
            return JsonResponse({
                'code': 400,
                'msg': '请设置登录密码',
                'data': {}
            }, json_dumps_params={'ensure_ascii': False})

        # 检查用户名是否已存在（双重检查）
        if User.objects.filter(username=username).exists():
            return JsonResponse({
                'code': 400,
                'msg': '用户名已存在',
                'data': {}
            }, json_dumps_params={'ensure_ascii': False})

        if ERPUser.objects.filter(username=username).exists():
            return JsonResponse({
                'code': 400,
                'msg': '账号已存在，请更换账号注册',
                'data': {}
            }, json_dumps_params={'ensure_ascii': False})

        # 检查密码长度
        if len(password) < 6:
            return JsonResponse({
                'code': 400,
                'msg': '密码长度不能少于6位',
                'data': {}
            }, json_dumps_params={'ensure_ascii': False})

        # 账号格式校验（字母/数字/下划线，4-20位）
        import re
        username_reg = re.compile(r'^[a-zA-Z0-9_]{4,20}$')
        if not username_reg.match(username):
            return JsonResponse({
                'code': 400,
                'msg': '账号格式错误：仅支持字母、数字、下划线，长度4-20位',
                'data': {}
            }, json_dumps_params={'ensure_ascii': False})

        # 3. 创建用户（同步Django User和ERPUser）
        # 创建Django User（密码加密存储）
        django_user = User.objects.create_user(username=username, password=password)
        # 创建ERPUser（明文存储，兼容登录逻辑）
        erp_user = ERPUser.objects.create(
            username=username,
            password=password
        )

        logger.info(f"ERP用户注册成功：{username}")
        return JsonResponse({
            'code': 200,
            'msg': '注册成功',
            'data': {
                'username': username,
                'user_id': erp_user.id
            }
        }, json_dumps_params={'ensure_ascii': False})

    except json.JSONDecodeError:
        return JsonResponse({
            'code': 400,
            'msg': '请求数据格式错误（需为合法JSON）',
            'data': {}
        }, json_dumps_params={'ensure_ascii': False})
    except Exception as e:
        logger.error(f"注册失败：{str(e)}", exc_info=True)
        return JsonResponse({
            'code': 500,
            'msg': f'注册失败：{str(e)}',
            'data': {}
        }, json_dumps_params={'ensure_ascii': False})


# ===================== 登录接口（明文密码版+跨域支持+返回Session ID） =====================
@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])  # 新增OPTIONS方法支持
@add_cors_headers  # 新增跨域装饰器
def user_login(request):
    """
    登录接口
    - 支持JSON格式请求
    - 密码明文验证
    - 默认账号：admin/123456
    - 新增：返回Session ID供前端同步
    """
    # 处理OPTIONS预检请求（新增核心逻辑）
    if request.method == 'OPTIONS':
        response = JsonResponse({
            'code': 200,
            'msg': '预检成功',
            'data': {}
        }, status=200)
        response['Access-Control-Allow-Origin'] = 'http://localhost:5173'
        response['Access-Control-Allow-Credentials'] = 'true'
        return response

    # 首次访问自动创建默认管理员
    init_default_admin()

    try:
        # 1. 解析请求数据（兼容form-data和json）
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST.dict()

        username = data.get('username', '').strip()
        password = data.get('password', '').strip()

        # 2. 基础校验
        if not username or not password:
            return JsonResponse({
                'code': 400,
                'msg': '账号和密码不能为空',
                'data': {}
            }, status=200, json_dumps_params={'ensure_ascii': False})

        # 3. 验证用户（明文密码校验）
        try:
            user = ERPUser.objects.get(username=username)
            # 明文对比密码
            if password != user.password:
                logger.warning(f"用户{username}密码错误")
                raise ValueError("密码错误")
        except ERPUser.DoesNotExist:
            logger.warning(f"不存在的用户登录：{username}")
            return JsonResponse({
                'code': 401,
                'msg': '账号不存在',
                'data': {}
            }, status=200, json_dumps_params={'ensure_ascii': False})
        except ValueError:
            return JsonResponse({
                'code': 401,
                'msg': '账号或密码错误（默认：admin/123456）',
                'data': {}
            }, status=200, json_dumps_params={'ensure_ascii': False})

        # 4. 创建登录会话（增强：确保Session立即生效）
        request.session['erp_user_id'] = user.id
        request.session['erp_username'] = user.username
        request.session.set_expiry(3600 * 24)  # 24小时过期
        request.session.modified = True  # 强制更新Session

        logger.info(f"用户{username}登录成功，IP：{request.META.get('REMOTE_ADDR')}")
        return JsonResponse({
            'code': 200,
            'msg': '登录成功',
            'data': {
                'username': user.username,
                'user_id': user.id,
                'session_id': request.session.session_key  # 新增：返回Session ID
            }
        }, status=200, json_dumps_params={'ensure_ascii': False})

    except json.JSONDecodeError:
        logger.error("登录请求JSON格式错误")
        return JsonResponse({
            'code': 400,
            'msg': '请求数据格式错误（需为合法JSON）',
            'data': {}
        }, status=200, json_dumps_params={'ensure_ascii': False})
    except Exception as e:
        logger.error(f"登录接口异常：{str(e)}", exc_info=True)
        return JsonResponse({
            'code': 500,
            'msg': '服务器内部错误，请稍后重试',
            'data': {}
        }, status=200, json_dumps_params={'ensure_ascii': False})


# ===================== 退出登录接口（增强版+跨域支持） =====================
@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])  # 新增OPTIONS支持
@erp_login_required
@add_cors_headers  # 新增跨域装饰器
def user_logout(request):
    """退出登录接口：安全清空session"""
    # 处理OPTIONS预检请求
    if request.method == 'OPTIONS':
        response = JsonResponse({
            'code': 200,
            'msg': '预检成功',
            'data': {}
        }, status=200)
        response['Access-Control-Allow-Origin'] = 'http://localhost:5173'
        response['Access-Control-Allow-Credentials'] = 'true'
        return response

    try:
        username = request.session.get('erp_username', '未知用户')
        request.session.flush()
        logger.info(f"用户{username}退出登录")

        return JsonResponse({
            'code': 200,
            'msg': '退出成功',
            'data': {}
        }, json_dumps_params={'ensure_ascii': False})
    except Exception as e:
        logger.error(f"退出登录异常：{str(e)}", exc_info=True)
        return JsonResponse({
            'code': 500,
            'msg': '退出失败，请稍后重试',
            'data': {}
        }, status=200, json_dumps_params={'ensure_ascii': False})


# ===================== 物料列表分页接口（优化版+跨域支持） =====================
@csrf_exempt
@require_http_methods(["GET", "OPTIONS"])  # 新增OPTIONS支持
@erp_login_required
@add_cors_headers  # 新增跨域装饰器
def get_materials(request):
    """
    物料列表分页接口
    - 支持页码/页大小参数
    - 处理页码越界/非法参数
    - 优化数据序列化
    """
    # 处理OPTIONS预检请求
    if request.method == 'OPTIONS':
        response = JsonResponse({
            'code': 200,
            'msg': '预检成功',
            'data': {}
        }, status=200)
        response['Access-Control-Allow-Origin'] = 'http://localhost:5173'
        response['Access-Control-Allow-Credentials'] = 'true'
        return response

    try:
        # 1. 获取分页参数（处理非法值）
        page = request.GET.get('page', 1)
        page_size = request.GET.get('page_size', 10)

        # 类型转换+合法性校验
        try:
            page = int(page) if page else 1
            page_size = int(page_size) if page_size else 10
            page = 1 if page < 1 else page
            page_size = 10 if page_size < 1 or page_size > 100 else page_size
        except (ValueError, TypeError):
            page = 1
            page_size = 10

        # 2. 查询物料
        materials = Material.objects.all().order_by('-create_time')
        paginator = Paginator(materials, page_size)

        # 3. 处理页码异常
        try:
            page_obj = paginator.page(page)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        # 4. 序列化数据
        material_list = []
        for item in page_obj.object_list:
            material_list.append({
                'id': item.id,
                'name': item.name,
                'code': item.code,
                'category': item.category,
                'unit': item.unit,
                'supplier': item.supplier,
                'quantity': item.quantity,
                'desc': item.desc or '',
                'create_time': item.create_time.strftime('%Y-%m-%d %H:%M:%S') if item.create_time else ''
            })

        # 5. 返回分页数据
        return JsonResponse({
            'code': 200,
            'msg': 'success',
            'data': {
                'list': material_list,
                'total': paginator.count,
                'page': page_obj.number,
                'page_size': page_size,
                'total_pages': paginator.num_pages
            }
        }, json_dumps_params={'ensure_ascii': False})

    except Exception as e:
        logger.error(f"获取物料列表异常：{str(e)}", exc_info=True)
        return JsonResponse({
            'code': 500,
            'msg': '获取物料列表失败，请稍后重试',
            'data': {}
        }, status=200, json_dumps_params={'ensure_ascii': False})


# ===================== 新增物料接口（优化版+跨域支持） =====================
@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])  # 新增OPTIONS支持
@erp_login_required
@add_cors_headers  # 新增跨域装饰器
def save_material(request):
    """新增物料接口：增强参数校验+防重复编码"""
    # 处理OPTIONS预检请求
    if request.method == 'OPTIONS':
        response = JsonResponse({
            'code': 200,
            'msg': '预检成功',
            'data': {}
        }, status=200)
        response['Access-Control-Allow-Origin'] = 'http://localhost:5173'
        response['Access-Control-Allow-Credentials'] = 'true'
        return response

    try:
        # 1. 解析请求数据
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST.dict()

        # 2. 核心参数校验
        name = data.get('name', '').strip()
        code = data.get('code', '').strip()

        if not name:
            return JsonResponse({
                'code': 400,
                'msg': '物料名称不能为空',
                'data': {}
            }, status=200, json_dumps_params={'ensure_ascii': False})

        if not code:
            return JsonResponse({
                'code': 400,
                'msg': '物料编码不能为空',
                'data': {}
            }, status=200, json_dumps_params={'ensure_ascii': False})

        # 3. 防重复编码
        if Material.objects.filter(code=code).exists():
            return JsonResponse({
                'code': 400,
                'msg': f'物料编码{code}已存在，请更换编码',
                'data': {}
            }, status=200, json_dumps_params={'ensure_ascii': False})

        # 4. 处理可选参数
        try:
            quantity = int(data.get('quantity', 0))
            quantity = quantity if quantity >= 0 else 0
        except (ValueError, TypeError):
            quantity = 0

        # 5. 创建物料
        material = Material.objects.create(
            name=name,
            code=code,
            category=data.get('category', '').strip(),
            unit=data.get('unit', '').strip(),
            supplier=data.get('supplier', '').strip(),
            quantity=quantity,
            desc=data.get('desc', '').strip()
        )

        logger.info(f"用户{request.session['erp_username']}新增物料：{code}-{name}")
        return JsonResponse({
            'code': 200,
            'msg': '新增物料成功',
            'data': {'id': material.id, 'code': material.code}
        }, json_dumps_params={'ensure_ascii': False})

    except json.JSONDecodeError:
        return JsonResponse({
            'code': 400,
            'msg': '请求数据格式错误（需为合法JSON）',
            'data': {}
        }, status=200, json_dumps_params={'ensure_ascii': False})
    except Exception as e:
        logger.error(f"新增物料异常：{str(e)}", exc_info=True)
        return JsonResponse({
            'code': 500,
            'msg': '新增物料失败，请稍后重试',
            'data': {}
        }, status=200, json_dumps_params={'ensure_ascii': False})


# ===================== 获取物料详情接口（优化版+跨域支持） =====================
@csrf_exempt
@require_http_methods(["GET", "OPTIONS"])  # 新增OPTIONS支持
@erp_login_required
@add_cors_headers  # 新增跨域装饰器
def get_material(request, material_id):
    """获取物料详情接口：增强ID校验"""
    # 处理OPTIONS预检请求
    if request.method == 'OPTIONS':
        response = JsonResponse({
            'code': 200,
            'msg': '预检成功',
            'data': {}
        }, status=200)
        response['Access-Control-Allow-Origin'] = 'http://localhost:5173'
        response['Access-Control-Allow-Credentials'] = 'true'
        return response

    # 1. 校验物料ID
    try:
        material_id = int(material_id)
        if material_id <= 0:
            raise ValueError("ID必须为正整数")
    except (ValueError, TypeError):
        return JsonResponse({
            'code': 400,
            'msg': '物料ID必须为有效正整数',
            'data': {}
        }, status=200, json_dumps_params={'ensure_ascii': False})

    # 2. 查询物料详情
    try:
        mat = Material.objects.get(id=material_id)
        data = {
            'id': mat.id,
            'name': mat.name,
            'code': mat.code,
            'category': mat.category,
            'unit': mat.unit,
            'supplier': mat.supplier,
            'quantity': mat.quantity,
            'desc': mat.desc or '',
            'create_time': mat.create_time.strftime('%Y-%m-%d %H:%M:%S') if mat.create_time else ''
        }
        return JsonResponse({
            'code': 200,
            'msg': 'success',
            'data': data
        }, json_dumps_params={'ensure_ascii': False})

    except Material.DoesNotExist:
        logger.warning(f"查询不存在的物料：ID={material_id}")
        return JsonResponse({
            'code': 404,
            'msg': '物料不存在',
            'data': {}
        }, status=200, json_dumps_params={'ensure_ascii': False})
    except Exception as e:
        logger.error(f"获取物料详情异常：ID={material_id}，错误：{str(e)}", exc_info=True)
        return JsonResponse({
            'code': 500,
            'msg': '获取物料详情失败，请稍后重试',
            'data': {}
        }, status=200, json_dumps_params={'ensure_ascii': False})


# ===================== 更新物料接口（优化版+跨域支持） =====================
@csrf_exempt
@require_http_methods(["PUT", "POST", "OPTIONS"])  # 新增POST支持（兼容前端误传）
@erp_login_required
@add_cors_headers  # 新增跨域装饰器
def update_material(request, material_id):
    """更新物料接口：支持部分字段更新+防重复编码+兼容POST/PUT"""
    # 处理OPTIONS预检请求
    if request.method == 'OPTIONS':
        response = JsonResponse({
            'code': 200,
            'msg': '预检成功',
            'data': {}
        }, status=200)
        response['Access-Control-Allow-Origin'] = 'http://localhost:5173'
        response['Access-Control-Allow-Credentials'] = 'true'
        return response

    # 1. 校验物料ID
    try:
        material_id = int(material_id)
        if material_id <= 0:
            raise ValueError("ID必须为正整数")
    except (ValueError, TypeError):
        return JsonResponse({
            'code': 400,
            'msg': '物料ID必须为有效正整数',
            'data': {}
        }, status=200, json_dumps_params={'ensure_ascii': False})

    # 2. 解析更新数据
    try:
        update_data = json.loads(request.body) if request.content_type == 'application/json' else request.POST.dict()
    except json.JSONDecodeError:
        return JsonResponse({
            'code': 400,
            'msg': '请求数据格式错误（需为合法JSON）',
            'data': {}
        }, status=200, json_dumps_params={'ensure_ascii': False})

    # 3. 查询物料并更新
    try:
        material = Material.objects.get(id=material_id)

        # 4. 处理编码重复
        new_code = update_data.get('code', '').strip()
        if new_code and new_code != material.code:
            if Material.objects.filter(code=new_code).exclude(id=material_id).exists():
                return JsonResponse({
                    'code': 400,
                    'msg': f'物料编码{new_code}已存在，请更换编码',
                    'data': {}
                }, status=200, json_dumps_params={'ensure_ascii': False})

        # 5. 字段更新
        if 'name' in update_data:
            material.name = update_data['name'].strip() or material.name
        if 'code' in update_data:
            material.code = update_data['code'].strip() or material.code
        if 'category' in update_data:
            material.category = update_data['category'].strip()
        if 'unit' in update_data:
            material.unit = update_data['unit'].strip()
        if 'supplier' in update_data:
            material.supplier = update_data['supplier'].strip()
        if 'quantity' in update_data:
            try:
                quantity = int(update_data['quantity'])
                material.quantity = quantity if quantity >= 0 else 0
            except (ValueError, TypeError):
                pass
        if 'desc' in update_data:
            material.desc = update_data['desc'].strip()

        material.save()

        logger.info(f"用户{request.session['erp_username']}更新物料：ID={material_id}")
        return JsonResponse({
            'code': 200,
            'msg': '物料修改保存成功',
            'data': {'id': material.id, 'code': material.code}
        }, json_dumps_params={'ensure_ascii': False})

    except Material.DoesNotExist:
        logger.warning(f"更新不存在的物料：ID={material_id}")
        return JsonResponse({
            'code': 404,
            'msg': '待修改的物料不存在',
            'data': {}
        }, status=200, json_dumps_params={'ensure_ascii': False})
    except Exception as e:
        logger.error(f"更新物料异常：ID={material_id}，错误：{str(e)}", exc_info=True)
        return JsonResponse({
            'code': 500,
            'msg': '修改物料失败，请稍后重试',
            'data': {}
        }, status=200, json_dumps_params={'ensure_ascii': False})


# ===================== 删除物料接口（优化版+跨域支持） =====================
@csrf_exempt
@require_http_methods(["DELETE", "OPTIONS"])  # 新增OPTIONS支持
@erp_login_required
@add_cors_headers  # 新增跨域装饰器
def delete_material(request, material_id):
    """删除物料接口：增强日志+安全校验"""
    # 处理OPTIONS预检请求
    if request.method == 'OPTIONS':
        response = JsonResponse({
            'code': 200,
            'msg': '预检成功',
            'data': {}
        }, status=200)
        response['Access-Control-Allow-Origin'] = 'http://localhost:5173'
        response['Access-Control-Allow-Credentials'] = 'true'
        return response

    # 1. 校验物料ID
    try:
        material_id = int(material_id)
        if material_id <= 0:
            raise ValueError("物料ID必须为正整数")
    except (ValueError, TypeError):
        return JsonResponse({
            "code": 400,
            "msg": "物料ID格式错误（必须为正整数）",
            "data": {}
        }, status=200, json_dumps_params={'ensure_ascii': False})

    # 2. 执行删除
    try:
        material = Material.objects.get(id=material_id)
        material_name = material.name
        material_code = material.code
        material.delete()

        logger.info(f"用户{request.session['erp_username']}删除物料：{material_code}-{material_name}（ID={material_id}）")
        return JsonResponse({
            "code": 200,
            "msg": "物料删除成功",
            "data": {}
        }, json_dumps_params={'ensure_ascii': False})

    except Material.DoesNotExist:
        logger.warning(f"删除不存在的物料：ID={material_id}")
        return JsonResponse({
            "code": 404,
            "msg": "待删除的物料不存在",
            "data": {}
        }, status=200, json_dumps_params={'ensure_ascii': False})
    except Exception as e:
        logger.error(f"删除物料异常：ID={material_id}，错误：{str(e)}", exc_info=True)
        return JsonResponse({
            "code": 500,
            "msg": "删除物料失败，请稍后重试",
            "data": {}
        }, status=200, json_dumps_params={'ensure_ascii': False})


