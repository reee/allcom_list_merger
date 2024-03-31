# 简要部署流程：
1. 导入源码到指定目录
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
5. 初始化数据库：
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```
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