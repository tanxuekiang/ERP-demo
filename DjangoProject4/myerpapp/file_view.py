# file_view.py（完整修复版）
import os
import time
import logging
from django.http import JsonResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.conf import settings
from django.core.files.storage import default_storage
from django.db import transaction
from functools import wraps
from .models import Material, MaterialFile

# 初始化日志（增强：打印到控制台+文件）
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]  # 控制台输出
)

# 复用跨域装饰器
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

# 复用登录校验装饰器
def erp_login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('erp_user_id'):
            response = JsonResponse({
                'code': 401,
                'msg': '请先登录ERP系统！',
                'data': {}
            }, status=200)
            response['Access-Control-Allow-Origin'] = 'http://localhost:5173'
            response['Access-Control-Allow-Credentials'] = 'true'
            return response
        return view_func(request, *args, **kwargs)
    return wrapper


# 1. 上传物料附件（核心修复版：补全登录校验）
@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
@erp_login_required  # 新增：补全登录校验，和其他接口保持一致
@add_cors_headers
def upload_material_files(request, material_id):
    """上传物料附件，支持多文件（修复文件名重复+增强日志+补全登录校验）"""
    # 处理OPTIONS预检
    if request.method == 'OPTIONS':
        logger.info("收到OPTIONS预检请求")
        return JsonResponse({'code': 200, 'msg': '预检成功', 'data': {}})

    try:
        # ========== 新增：打印登录用户信息（调试） ==========
        logger.info(f"登录用户ID：{request.session.get('erp_user_id')}，用户名：{request.session.get('erp_username')}")

        # ========== 1. 打印请求基本信息（调试关键） ==========
        logger.info(f"开始处理物料{material_id}的文件上传请求")
        logger.info(f"请求方法：{request.method}")
        logger.info(f"请求Content-Type：{request.content_type}")
        logger.info(f"是否为multipart/form-data：{request.content_type.startswith('multipart/form-data')}")
        logger.info(f"收到的文件数量：{len(request.FILES.getlist('files')) if 'files' in request.FILES else 0}")

        # ========== 2. 校验物料是否存在 ==========
        try:
            material = Material.objects.get(id=material_id)
            logger.info(f"找到物料：ID={material_id}，名称={material.name}")
        except Material.DoesNotExist:
            logger.error(f"物料{material_id}不存在，无法上传附件")
            return JsonResponse({
                'code': 404,
                'msg': '物料不存在，无法上传附件',
                'data': {}
            }, status=200)

        # ========== 3. 校验文件是否存在 ==========
        if 'files' not in request.FILES:
            logger.error("请求中未包含files字段")
            return JsonResponse({
                'code': 400,
                'msg': '请选择要上传的文件',
                'data': {}
            }, status=200)

        # ========== 4. 批量处理文件（修复文件名重复） ==========
        files = request.FILES.getlist('files')
        saved_files = []
        media_root = settings.MEDIA_ROOT
        # 新增：确保material_files目录存在
        material_files_dir = os.path.join(media_root, "material_files")
        if not os.path.exists(material_files_dir):
            os.makedirs(material_files_dir, exist_ok=True)
            logger.info(f"创建物料文件目录：{material_files_dir}")

        logger.info(f"媒体文件根目录：{media_root}，是否存在：{os.path.exists(media_root)}")
        logger.info(f"物料文件目录：{material_files_dir}，是否存在：{os.path.exists(material_files_dir)}")

        with transaction.atomic():  # 事务保证
            for file in files:
                # 限制文件大小（1GB）
                max_size = 1 * 1024 * 1024 * 1024
                if file.size > max_size:
                    logger.error(f"文件{file.name}超过1GB大小限制（实际大小：{file.size}字节）")
                    return JsonResponse({
                        'code': 400,
                        'msg': f'文件{file.name}超过1GB大小限制',
                        'data': {}
                    }, status=200)

                # 修复：文件名去重（添加时间戳）
                file_name = file.name
                file_ext = os.path.splitext(file_name)[1]  # 获取文件扩展名
                file_name_no_ext = os.path.splitext(file_name)[0]
                # 生成唯一文件名：原名称_时间戳.扩展名
                unique_file_name = f"{file_name_no_ext}_{int(time.time())}{file_ext}"
                file_path = os.path.join("material_files", unique_file_name)
                full_file_path = os.path.join(media_root, file_path)

                logger.info(f"准备保存文件：{unique_file_name}，路径：{full_file_path}")

                # 保存文件到服务器（改用手动保存，更稳定）
                try:
                    with open(full_file_path, 'wb+') as destination:
                        for chunk in file.chunks():
                            destination.write(chunk)
                    logger.info(f"文件手动保存成功，路径：{full_file_path}")
                    logger.info(f"文件是否存在：{os.path.exists(full_file_path)}")

                    # 创建文件记录
                    material_file = MaterialFile.objects.create(
                        material=material,
                        name=file.name,  # 保存原始文件名
                        file_path=file_path,  # 保存相对路径
                        size=file.size
                    )
                    saved_files.append({
                        'id': material_file.id,
                        'name': material_file.name,
                        'size': material_file.size,
                        'upload_time': material_file.upload_time.strftime('%Y-%m-%d %H:%M:%S')
                    })
                    logger.info(f"文件记录已写入数据库：ID={material_file.id}")

                except Exception as save_err:
                    logger.error(f"保存文件{file.name}失败：{str(save_err)}", exc_info=True)
                    raise save_err

        # ========== 5. 返回结果 ==========
        logger.info(f"用户{request.session['erp_username']}为物料{material_id}上传{len(saved_files)}个附件，全部成功")
        return JsonResponse({
            'code': 200,
            'msg': '文件上传成功',
            'data': saved_files
        }, status=200)

    except Exception as e:
        logger.error(f"文件上传失败：{str(e)}", exc_info=True)
        return JsonResponse({
            'code': 500,
            'msg': f'文件上传失败：{str(e)}',
            'data': {}
        }, status=200)

# 2. 获取物料附件列表（保持不变）
@csrf_exempt
@require_http_methods(["GET", "OPTIONS"])
@erp_login_required
@add_cors_headers
def get_material_files(request, material_id):
    if request.method == 'OPTIONS':
        return JsonResponse({'code':200, 'msg':'预检成功', 'data':{}})

    try:
        try:
            material = Material.objects.get(id=material_id)
        except Material.DoesNotExist:
            return JsonResponse({
                'code':404,
                'msg':'物料不存在',
                'data':[]
            }, status=200)

        files = MaterialFile.objects.filter(material=material).order_by('-upload_time')
        file_list = []
        for f in files:
            file_list.append({
                'id': f.id,
                'name': f.name,
                'size': f.size,
                'upload_time': f.upload_time.strftime('%Y-%m-%d %H:%M:%S')
            })

        return JsonResponse({
            'code':200,
            'msg':'success',
            'data': file_list
        }, status=200)

    except Exception as e:
        logger.error(f"获取物料附件失败：{str(e)}", exc_info=True)
        return JsonResponse({
            'code':500,
            'msg':'获取附件失败',
            'data':[]
        }, status=200)

# 3. 下载物料附件（保持不变）
@csrf_exempt
@require_http_methods(["GET", "OPTIONS"])
@erp_login_required
@add_cors_headers
def download_material_file(request, material_id, file_id):
    if request.method == 'OPTIONS':
        response = JsonResponse({'code':200, 'msg':'预检成功', 'data':{}})
        return response

    try:
        try:
            material_file = MaterialFile.objects.get(id=file_id, material_id=material_id)
        except MaterialFile.DoesNotExist:
            return JsonResponse({
                'code':404,
                'msg':'文件不存在',
                'data':{}
            }, status=200)

        file_path = material_file.file_path
        if not default_storage.exists(file_path):
            return JsonResponse({
                'code':404,
                'msg':'文件已被删除',
                'data':{}
            }, status=200)

        file = default_storage.open(file_path, 'rb')
        response = FileResponse(file)
        response['Content-Type'] = 'application/octet-stream'
        response['Content-Disposition'] = f'attachment; filename="{material_file.name}"'
        response['Access-Control-Allow-Origin'] = 'http://localhost:5173'
        response['Access-Control-Allow-Credentials'] = 'true'

        logger.info(f"用户{request.session['erp_username']}下载物料{material_id}的附件{file_id}")
        return response

    except Exception as e:
        logger.error(f"文件下载失败：{str(e)}", exc_info=True)
        response = JsonResponse({
            'code':500,
            'msg':f'下载失败：{str(e)}',
            'data':{}
        }, status=200)
        response['Access-Control-Allow-Origin'] = 'http://localhost:5173'
        response['Access-Control-Allow-Credentials'] = 'true'
        return response

# 4. 删除物料附件（保持不变）
@csrf_exempt
@require_http_methods(["DELETE", "OPTIONS"])
@erp_login_required
@add_cors_headers
def delete_material_file(request, material_id, file_id):
    if request.method == 'OPTIONS':
        return JsonResponse({'code':200, 'msg':'预检成功', 'data':{}})

    try:
        try:
            material_file = MaterialFile.objects.get(id=file_id, material_id=material_id)
        except MaterialFile.DoesNotExist:
            return JsonResponse({
                'code':404,
                'msg':'文件不存在',
                'data':{}
            }, status=200)

        file_path = material_file.file_path
        if default_storage.exists(file_path):
            default_storage.delete(file_path)
            logger.info(f"已删除文件：{file_path}")
        material_file.delete()

        logger.info(f"用户{request.session['erp_username']}删除物料{material_id}的附件{file_id}")
        return JsonResponse({
            'code':200,
            'msg':'文件删除成功',
            'data':{}
        }, status=200)

    except Exception as e:
        logger.error(f"文件删除失败：{str(e)}", exc_info=True)
        return JsonResponse({
            'code':500,
            'msg':f'删除失败：{str(e)}',
            'data':{}
        }, status=200)