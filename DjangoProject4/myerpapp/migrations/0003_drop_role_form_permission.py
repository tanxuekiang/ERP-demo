from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('myerpapp', '0002_init_default_data'),  # 替换为你的上一个迁移文件名
    ]

    operations = [
        # 删除旧版权限表
        migrations.DeleteModel('RoleFormPermission'),
        # 可选：删除旧表的数据库记录（如果有）
        migrations.RunSQL("DROP TABLE IF EXISTS erp_role_form_permission;")
    ]