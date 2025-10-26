from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms.validators import DataRequired, Length

class LoginForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired()])
    password = PasswordField('密码', validators=[DataRequired()])
    submit = SubmitField('登录')

class ImportUsersForm(FlaskForm):
    upload = FileField('请选择对应名单并上传导入', validators=[
        FileRequired(),
        FileAllowed(['xlsx'], '只允许上传xlsx文件!')
    ])
    replace = BooleanField('清空现有用户')
    submit = SubmitField('上传')

class ImportStudentsForm(FlaskForm):
    upload = FileField('请选择对应名单上传导入', validators=[
        FileRequired(),
        FileAllowed(['xlsx'], '只允许上传xlsx文件!')
    ])
    replace = BooleanField('清除本校本学届现有考生后再导入')
    not_divided = BooleanField('本次考试学生尚未分科')
    submit = SubmitField('上传')

class EditStudentForm(FlaskForm):
    name = StringField('姓名', validators=[DataRequired()])
    exam_no = StringField('考号', validators=[DataRequired(), Length(min=10, max=10)])
    school_code = StringField('学校代码', validators=[DataRequired()])
    school_name = StringField('学校名称', validators=[DataRequired()])
    grade_name = StringField('学届', validators=[DataRequired()])
    class_name = StringField('班级代码', validators=[DataRequired(), Length(min=3, max=3)])
    exam_type = SelectField('考生类型', choices=[
        ('', '高一上留空，其他年级请下拉选择'),  # 添加空选项
        ('物化生', '物化生'), 
        ('物化政', '物化政'), 
        ('物化地', '物化地'), 
        ('物生地', '物生地'), 
        ('物生政', '物生政'), 
        ('物地政', '物地政'), 
        ('历生政', '历生政'), 
        ('历生地', '历生地'), 
        ('历政地', '历政地'), 
        ('历化政', '历化政'), 
        ('历化生', '历化生'), 
        ('历化地', '历化地')
    ])  # 移除 DataRequired()
    subject_type = SelectField('科类属性', choices=[
        ('', '高一上留空，其他年级请下拉选择'),  # 添加空选项
        ('物理类', '物理类'), 
        ('历史类', '历史类')
    ])  # 移除 DataRequired()
    submit = SubmitField('提交')

class NewStudentForm(FlaskForm):
    name = StringField('姓名', validators=[DataRequired()])
    exam_no = StringField('考号', validators=[DataRequired(), Length(min=10, max=10)])
    exam_type = SelectField('考生类型', choices=[
        ('', '高一上留空，其他年级请下拉选择'),  # 添加空选项
        ('物化生', '物化生'), 
        ('物化政', '物化政'), 
        ('物化地', '物化地'), 
        ('物生地', '物生地'), 
        ('物生政', '物生政'), 
        ('物地政', '物地政'), 
        ('历化政', '历化政'), 
        ('历化生', '历化生'), 
        ('历化地', '历化地'), 
        ('历生政', '历生政'), 
        ('历生地', '历生地'), 
        ('历政地', '历政地')
    ])
    submit = SubmitField('提交')

class SearchStudentForm(FlaskForm):
    name = StringField('学生姓名', validators=[DataRequired()])
    submit = SubmitField('搜索')

class SearchTeacherForm(FlaskForm):
    name = StringField('教师姓名', validators=[DataRequired()])
    submit = SubmitField('搜索')

class EditTeacherForm(FlaskForm):
    code = StringField('编码', validators=[DataRequired()])
    name = StringField('姓名', validators=[DataRequired()]) 
    school_name = StringField('单位', validators=[DataRequired()])
    teaching_grade = StringField('任教学届')
    password = PasswordField('密码', validators=[DataRequired()])
    subjects = StringField('任教学科')
    role = SelectField('角色', choices=[('任课教师', '任课教师'), ('科组长', '科组长')], validators=[DataRequired()])
    gender = SelectField('性别', choices=[('男', '男'), ('女', '女')])
    enabled = BooleanField('是否启用')
    submit = SubmitField('提交')

class ImportTeachersForm(FlaskForm):
    upload = FileField('请选择对应名单上传导入', validators=[
        FileRequired(),
        FileAllowed(['xlsx'], '只允许上传xlsx文件!')
    ])
    replace = BooleanField('清除本校现有教师后再导入')
    submit = SubmitField('上传')