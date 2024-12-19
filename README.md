# 学生教师信息管理系统 (Student and Teacher Information Management System)

这是一个基于 Flask 和 Bootstrap 5 开发的学生和教师信息管理系统。系统提供了一个现代化的 Web 界面，用于管理学校的学生和教师信息。

This is a student and teacher information management system developed with Flask and Bootstrap 5. The system provides a modern web interface for managing school student and teacher information.

## 功能特点 (Features)

- 📚 学生信息管理
  - 批量导入学生信息
  - 搜索和编辑学生信息
  - 管理学生考试类型和科目属性
  - Student information management
    - Batch import student information
    - Search and edit student information
    - Manage student exam types and subject attributes

- 👨‍🏫 教师信息管理
  - 批量导入教师信息
  - 搜索和编辑教师信息
  - 管理教师角色和状态
  - Teacher information management
    - Batch import teacher information
    - Search and edit teacher information
    - Manage teacher roles and status

- 🔐 用户认证与授权
  - 安全的用户登录系统
  - 基于角色的访问控制
  - User authentication and authorization
    - Secure user login system
    - Role-based access control

## 部署指南 (Deployment Guide)

### 环境准备 (Environment Setup)

1. 导入源码到指定目录 (Import source code to the specified directory)
2. 在源码对应目录下新建venv的目录：
```bash
python3 -m venv venv
```
3. 激活venv:
```bash
source venv/bin/activate
```
4. 安装依赖：
```bash
pip install -r requirements.txt
```

### 数据库配置 (Database Configuration)

5. 初始化数据库：
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### 管理员设置 (Admin Setup)

6. 预定义管理员信息：
在源码目录下新建文件 .env，输入如下内容：
```bash
ADMIN_USERNAME=admin
ADMIN_PASSWORD=changme
```
其中用户名密码都可以随意设置。

7. 导入管理员信息：
```bash
python ./create_admin.py
```
注：若管理员信息有修改，可以再次运行脚本，会对之前的信息进行覆盖。

### 服务配置 (Service Configuration)

8. 建立用于守护的systemd service：
```bash
vim /etc/systemd/system/stu-list.service
```
输入如下内容：
```bash
[Unit]
Description=Gunicorn instance to serve stu-list
After=network.target

[Service]
User={$USERNAME}
Group={$GROUP}
WorkingDirectory={PATH}/stu-list
Environment="PATH={PATH}/stu-list/venv/bin"
ExecStart={PATH}/stu-list/venv/bin/gunicorn --workers 3 --bind unix:/tmp/stu-list.sock -m 007 wsgi:app

[Install]
WantedBy=multi-user.target
```
请自行根据情况修改 {$USERNAME}、{$GROUP}、{PATH}。

9. 运行并启用服务：
```bash
systemctl start stu-list && systemctl enable stu-list
```

### Nginx 配置 (Nginx Configuration)

10. 使用nginx进行反代：
```bash
vim /etc/nginx/conf.d/stu-list.conf
```
输入如下内容：
```bash
server {
   listen 443 ssl http2;
   server_name {$DOMAIN_NAME};
   ssl_certificate     /path/to/cert_file;
   ssl_certificate_key /path/to/key_file;

   location / {
        include proxy_params;
        proxy_pass http://unix:/tmp/stu-list.sock;
    }
}
```
请自行根据情况修改{$DOMAIN_NAME}、/path/to/cert_file、/path/to/key_file。

## 技术栈 (Tech Stack)

- Backend: Flask, SQLAlchemy, Flask-Login
- Frontend: Bootstrap 5, jQuery
- Database: SQLite
- Server: Nginx, Gunicorn

## 系统要求 (System Requirements)

- Python 3.6+
- Nginx
- Modern web browser