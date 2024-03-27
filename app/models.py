from app import db, login, logger
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    nickname = db.Column(db.String(64))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<User {}>'.format(self.username)

@login.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    school_code = db.Column(db.String(64), index=True)
    school_name = db.Column(db.String(128))
    class_name = db.Column(db.String(64))
    name = db.Column(db.String(64))
    student_id = db.Column(db.String(20))
    exam_type = db.Column(db.String(64))
    exam_no = db.Column(db.String(64), unique=True)
    subject_type = db.Column(db.String(64))

    def __repr__(self):
        return '<Student {}>'.format(self.name)
    
