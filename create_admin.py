from app import app, db
from app.models import User

def create_admin():
    admin_username = app.config['ADMIN_USERNAME']
    admin_password = app.config['ADMIN_PASSWORD']

    # 查询是否已经存在管理员用户
    admin_user = User.query.filter_by(is_admin=True).first()

    if admin_user:
        # 如果存在,更新密码和管理员标志
        admin_user.username = admin_username
        admin_user.set_password(admin_password)
        db.session.commit()
        print(f"管理员用户 {admin_username} 已更新")
    else:
        # 如果不存在,创建新的管理员用户
        admin_user = User(username=admin_username, is_admin=True)
        admin_user.set_password(admin_password)
        db.session.add(admin_user)
        db.session.commit()
        print(f"管理员用户 {admin_username} 已创建")

if __name__ == '__main__':
    with app.app_context():
        create_admin()