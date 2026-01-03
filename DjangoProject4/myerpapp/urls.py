from django.urls import path
from . import views, erp_user_views, role_views, file_view, process_view

urlpatterns = [
    # 审批流程管理 - 修复前端调用的路径
    path('approval/flows/', process_view.ApprovalFlowListView.as_view(), name='approval_flow_list'),
    # 新增：适配前端 /approval/flow/detail/{id}/ 路径
    path('approval/flow/detail/<int:pk>/', process_view.ApprovalFlowDetailView.as_view(), name='approval_flow_detail'),
    # 新增：适配前端 /approval/flow/create/ 路径（原flows/create/保留兼容）
    path('approval/flow/create/', process_view.ApprovalFlowCreateView.as_view(), name='approval_flow_create_v2'),
    path('approval/flows/create/', process_view.ApprovalFlowCreateView.as_view(), name='approval_flow_create'),
    # 新增：适配前端 /approval/flow/update/{id}/ 路径
    path('approval/flow/update/<int:pk>/', process_view.ApprovalFlowUpdateView.as_view(),
         name='approval_flow_update_v2'),
    path('approval/flows/<int:pk>/update/', process_view.ApprovalFlowUpdateView.as_view(), name='approval_flow_update'),

    # 原有审批节点/实例接口（无需修改）
    path('approval/nodes/<int:flow_id>/', process_view.ApprovalNodeListView.as_view(), name='approval_node_list'),
    path('approval/nodes/save/', process_view.ApprovalNodeSaveView.as_view(), name='approval_node_save'),
    path('approval/instances/create/', process_view.ApprovalInstanceCreateView.as_view(),
         name='approval_instance_create'),
    path('approval/instances/operate/', process_view.ApprovalInstanceOperateView.as_view(),
         name='approval_instance_operate'),
    path('approval/instances/<int:pk>/', process_view.ApprovalInstanceDetailView.as_view(),
         name='approval_instance_detail'),

    # ========== 原有基础接口 ==========
    path('login/', views.user_login, name='user-login'),
    path('register/', views.user_register, name='user-register'),
    path('logout/', views.user_logout, name='user-logout'),
    path('get-materials/', views.get_materials, name='get-materials'),
    path('save-material/', views.save_material, name='save-material'),
    path('get-material/<int:material_id>/', views.get_material, name='get-material'),
    path('update-material/<int:material_id>/', views.update_material, name='update-material'),
    path('delete-material/<int:material_id>/', views.delete_material, name='delete-material'),
    path('erp-users/', erp_user_views.get_erp_users, name='get-erp-users'),
    path('erp-users/add/', erp_user_views.add_erp_user, name='add-erp-user'),
    path('erp-users/update/<int:user_id>/', erp_user_views.update_erp_user_password, name='update-erp-user-password'),
    path('erp-users/delete/<int:user_id>/', erp_user_views.delete_erp_user, name='delete-erp-user'),
    path('roles/', role_views.get_roles, name='get-roles'),
    path('roles/add/', role_views.add_role, name='add-role'),
    path('roles/update/<int:role_id>/', role_views.update_role, name='update-role'),
    path('roles/delete/<int:role_id>/', role_views.delete_role, name='delete-role'),
    path('roles/batch_delete/', role_views.batch_delete_roles, name='batch-delete-roles'),
    path('get-user-permissions/', erp_user_views.get_user_permissions, name='get-user-permissions'),
    path('upload-material-files/<int:material_id>/', file_view.upload_material_files, name='upload-material-files'),
    path('get-material-files/<int:material_id>/', file_view.get_material_files, name='get-material-files'),
    path('download-material-file/<int:material_id>/<int:file_id>/', file_view.download_material_file,
         name='download-material-file'),
    path('delete-material-file/<int:material_id>/<int:file_id>/', file_view.delete_material_file,
         name='delete-material-file'),
]