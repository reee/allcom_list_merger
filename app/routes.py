import io
from sqlalchemy.exc import IntegrityError
from flask import render_template, redirect, request, send_file, session, url_for, flash
from flask_login import current_user, login_required, login_user, logout_user

import pandas as pd
from sqlalchemy import func
from app import app, db
from app.auth import admin_required
from app.forms import EditStudentForm, EditTeacherForm, ImportStudentsForm, ImportTeachersForm, ImportUsersForm, LoginForm
from app.models import Student, Teacher, User

from app.log_utils import logger

@app.route('/', methods=['GET', 'POST'])
def index():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin_panel'))
        else:
            return redirect(url_for('user_panel'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('无效的用户名或密码', 'error')
            return redirect(url_for('index'))
        login_user(user)
        if user.is_admin:
            return redirect(url_for('admin_panel'))
        else:
            return redirect(url_for('user_panel'))
    return render_template('index.html', title='登录', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/admin', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_panel():
    if request.method == 'POST':
        if request.form.get('action') == 'edit':
            user_id = request.form.get('user_id')
            user = User.query.get(user_id)
            user.username = request.form.get('username')
            user.set_password(request.form.get('password'))
            user.school_name = request.form.get('school_name')
            db.session.commit()
            flash('用户信息已更新', 'success')
        elif request.form.get('action') == 'delete':
            user_id = request.form.get('user_id')
            user = User.query.get(user_id)
            db.session.delete(user)
            db.session.commit()
            flash('用户已删除', 'success')

    users = User.query.filter_by(is_admin=False).order_by(User.school_name).all()
    return render_template('admin_panel.html', users=users)


@app.route('/admin/import_users', methods=['GET', 'POST'])
@login_required
@admin_required
def import_users():
    form = ImportUsersForm()
    if form.validate_on_submit():
        file = request.files['upload']
        if file.filename == '':
            flash('未选择文件', 'error')
            return redirect(url_for('import_users'))
        
        # 读取Excel数据
        df = pd.read_excel(file)
        
        expected_columns = ['用户名', '密码', '学届', '学校简称']
        columns = df.columns.tolist()
        if columns != expected_columns:
            missing_columns = set(expected_columns) - set(columns)
            extra_columns = set(columns) - set(expected_columns)
            error_message = ''
            if missing_columns:
                error_message += f"缺少列: {', '.join(missing_columns)}\n"
            if extra_columns:
                error_message += f"多余列: {', '.join(extra_columns)}\n"
            flash(error_message, 'error')
            return redirect(url_for('import_users'))

        # 检查是否存在重复用户
        if not df["用户名"].is_unique:
            flash(f"用户名不唯一，请修正后重新导入", 'error')
            return redirect(url_for('import_users'))

        if form.replace.data:
            # 清除非管理员用户
            non_admin_users = User.query.filter_by(is_admin=False).all()
            for user in non_admin_users:
                db.session.delete(user)
            db.session.commit()

        # 导入新用户
        for _, row in df.iterrows():
            user = User(
                username=row['用户名'].strip(), 
                grade_name=row['学届'].strip(), 
                school_name=row['学校简称'].strip()
                )
            user.set_password(str(row['密码']).strip())
            db.session.add(user)
        db.session.commit()
        flash('用户导入成功', 'info')
        return redirect(url_for('import_users'))
        
    return render_template('import_users.html', form=form)

@app.route('/import_students', methods=['GET', 'POST'])
@login_required
def import_students():
    form = ImportStudentsForm()
    if form.validate_on_submit():
        file = request.files['upload']
        if file.filename == '':
            flash('未选择文件', 'error')
            return redirect(url_for('import_students'))
        
        # 读取Excel数据
        df = pd.read_excel(file)

        expected_columns = ['学校代码', '学校名称', '学届', '班级代码', '姓名', '学籍号', '考生类型1', '考生类型2', '考号', '科类属性']
        columns = df.columns.tolist()
        if sorted(columns) != sorted(expected_columns):
            missing_columns = set(expected_columns) - set(columns)
            extra_columns = set(columns) - set(expected_columns)
            error_message = ''
            if missing_columns:
                error_message += f"缺少列: {', '.join(missing_columns)}\n"
            if extra_columns:
                error_message += f"多余列: {', '.join(extra_columns)}\n"
            flash(error_message, 'error')
            return redirect(url_for('import_students'))
        
        # 检查是否存在考号重复学生
        if not df["考号"].is_unique:
            flash(f"学生考号不唯一，请修正后重新导入", 'error')
            return redirect(url_for('import_students'))

        if form.replace.data:
            # 清理本校本学届现有学生
            existing_students = Student.query.filter_by(school_name=current_user.school_name, grade_name=current_user.grade_name).all()
            for student in existing_students:
                db.session.delete(student)
            db.session.commit()

        valid_exam_types = ["物化生", "物化政", "物化地", "物生地", "物生政", "物地政", "历化政", "历化生", "历化地", "历生政", "历生地", "历政地"]
        valid_subject_types = ["物理类", "历史类"]        

        # 导入学生
        for index, row in df.iterrows():
            # 检查学校名称
            if row['学校名称'] != current_user.school_name:
                flash(f"存在非本校学生或学校名称缺失或学校名称不匹配,请修正后重新导入", 'error')
                return redirect(url_for('import_students'))

            # 检查考生类型
            if row['考生类型1'] not in valid_exam_types:
                flash(f"存在考生“考生类型1”缺失或不正确,请修正后重新导入", 'error')
                return redirect(url_for('import_students'))

            if row['学届'] != current_user.grade_name:
                flash(f"存在考生学届与当前账号不匹配,请修正后重新导入", 'error')
                return redirect(url_for('import_students'))

            # 检查考号位数
            if len(str(row['考号'])) != 10:
                flash(f"存在考生考号缺失或位数不正确,请修正后重新导入", 'error')
                return redirect(url_for('import_students'))

            # 检查班级代码
            if len(str(row['班级代码'])) != 3:
                flash(f"存在考生班级代码缺失或位数不正确,请修正后重新导入", 'error')
                return redirect(url_for('import_students'))

            # 检查科类属性
            if row['科类属性'] not in valid_subject_types:
                flash(f"存在考生科类属性缺失或不正确,请修正后重新导入", 'error')
                return redirect(url_for('import_students'))
            
            student = Student(
                school_code=str(row['学校代码']).strip(), 
                school_name=str(row['学校名称']).strip(),
                grade_name=str(row['学届']).strip(),
                class_name=str(row['班级代码']).strip(),
                name=str(row['姓名']).strip(),
                student_id=row['学籍号'],
                exam_type=str(row['考生类型1']).strip(),
                exam_type1=row['考生类型2'],
                exam_no=str(row['考号']).strip(),
                subject_type=str(row['科类属性']).strip()
            )
            db.session.add(student)
        
        try:
            db.session.commit()
            flash('本校考生信息导入成功', 'info')
        except IntegrityError as e:
            error_info = str(e.orig)
            if 'UNIQUE constraint failed' in error_info:
                flash('导入学生考号与数据库已有考号重复，请检查相关数据', 'error')
            else:
                flash('发生未知错误，请联系管理员！', 'error')
        return redirect(url_for('import_students'))
        
    return render_template('import_students.html', form=form)

@app.route('/import_teachers', methods=['GET', 'POST'])
@login_required
def import_teachers():
    form = ImportTeachersForm()
    if form.validate_on_submit():
        file = request.files['upload']
        if file.filename == '':
            flash('未选择文件', 'error')
            return redirect(url_for('import_teachers'))
        
        # 读取Excel数据
        df = pd.read_excel(file)

        expected_columns = ['编码', '姓名', '单位', '任教学届', '密码', '任教学科', '角色', '性别', '是否启用']
        columns = df.columns.tolist()
        if columns.sort() != expected_columns.sort():
            missing_columns = set(expected_columns) - set(columns)
            extra_columns = set(columns) - set(expected_columns)
            error_message = ''
            if missing_columns:
                error_message += f"缺少列: {', '.join(missing_columns)}\n"
            if extra_columns:
                error_message += f"多余列: {', '.join(extra_columns)}\n"
            flash(error_message, 'error')
            return redirect(url_for('import_students'))
        
        if form.replace.data:
            # 清理现有学生
            existing_teachers = Teacher.query.filter_by(school_name=current_user.school_name).all()
            for teacher in existing_teachers:
                db.session.delete(teacher)
            db.session.commit()

        valid_subjects = ['语文', '数学', '英语', '物理', '化学', '生物', '政治', '历史', '地理']
        valid_roles = ["任课教师", "科组长"]

        # 检查编码字段是否有重复，一般这里重复是因为存在跨年级的情况
        if not df["编码"].is_unique:
            flash(f"教师编码存在重复值，请删除重复的教师后重新导入", 'error')
            return redirect(url_for('import_teachers'))

        # 导入教师
        for index, row in df.iterrows():
            # 检查学校名称
            if row['单位'] != current_user.school_name:
                flash(f"存在非本校教师或学校名称缺失或不匹配,请修正后重新导入", 'error')
                return redirect(url_for('import_teachers'))

            # 检查任教学科
            if row['任教学科'] and row['任教学科'] not in valid_subjects:
                flash(f"存在教师任教学科不正确,请修正后重新导入", 'error')
                return redirect(url_for('import_teachers'))
            
            # 检查角色
            if row['角色'] and row['角色'] not in valid_roles:
                flash(f"存在教师角色不正确,请修正后重新导入", 'error')
                return redirect(url_for('import_teachers'))

            teacher = Teacher(
                code=row['编码'], 
                name=row['姓名'], 
                school_name=row['单位'],
                teaching_grade=row['任教学届'],
                password=row['密码'],
                subjects=row['任教学科'],
                role=row['角色'],
                gender=row['性别'],
                enabled=True if row['是否启用'] == '是' else False
            )
            db.session.add(teacher)
        db.session.commit()
        flash('本校阅卷教师信息导入成功', 'info')
        return redirect(url_for('import_teachers'))
        
    return render_template('import_teachers.html', form=form)

@app.route('/user', methods=['GET', 'POST'])
@login_required
def user_panel():
    return render_template('user_panel.html')

@app.route('/student/<int:student_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_student(student_id):
    student = Student.query.get_or_404(student_id)
    if student.school_name != current_user.school_name:
        flash('您无权编辑其他学校的学生信息', 'error')
        return redirect(url_for('student_list'))
    
    if student.grade_name != current_user.grade_name:
        flash('您无权编辑其他学届的学生信息', 'error')
        return redirect(url_for('student_list'))

    form = EditStudentForm()
    if form.validate_on_submit():
        student.name = form.name.data
        student.student_id = form.student_id.data
        student.exam_type = form.exam_type.data
        student.exam_type1 = form.exam_type1.data
        student.subject_type = form.subject_type.data
        student.school_code = form.school_code.data
        student.school_name = form.school_name.data
        student.class_name = form.class_name.data
        student.grade_name = form.grade_name.data
        student.exam_no = form.exam_no.data
        db.session.commit()
        flash('学生信息已更新', 'info')
        return redirect(url_for('student_list'))
    
    elif request.method == 'GET':
        form.name.data = student.name
        form.student_id.data = student.student_id
        form.exam_type.data = student.exam_type
        form.exam_type1.data = student.exam_type1
        form.subject_type.data = student.subject_type
        form.school_code.data = student.school_code
        form.school_name.data = student.school_name
        form.class_name.data = student.class_name
        form.grade_name.data = student.grade_name
        form.exam_no.data = student.exam_no

    return render_template('edit_student.html', form=form, student=student)

@app.route('/student/<int:student_id>/delete', methods=['POST'])
@login_required
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    if student.school_name != current_user.school_name:
        flash('您无权删除其他学校的学生信息', 'error')
        return redirect(url_for('student_list'))
    
    if student.grade_name != current_user.grade_name:
        flash('您无权删除其他学届的学生信息', 'error')
        return redirect(url_for('student_list'))

    db.session.delete(student)
    db.session.commit()
    flash('学生信息已删除')
    return redirect(url_for('student_list'))

@app.route('/student/new', methods=['GET', 'POST'])
@login_required
def new_student():
    form = EditStudentForm()
    if form.validate_on_submit():

        if form.school_name.data != current_user.school_name:
            flash('您无权新增其他学校的学生信息', 'error')
            return redirect(url_for('new_student'))
        
        if form.grade_name.data != current_user.grade_name:
            flash('您无权新增其他年级的学生信息', 'error')
            return redirect(url_for('new_student'))    

        student = Student(
            name=form.name.data,
            student_id=form.student_id.data,
            exam_type=form.exam_type.data,
            exam_type1=form.exam_type1.data,
            subject_type=form.subject_type.data,
            school_code=form.school_code.data,
            class_name=form.class_name.data,
            grade_name=form.grade_name.data,
            exam_no=form.exam_no.data,
            school_name=form.school_name.data
        )
        db.session.add(student)
        db.session.commit()
        flash('新考生信息已添加', 'info')
        return redirect(url_for('student_list'))
    return render_template('new_student.html', form=form)

@app.route('/export_students', methods=['GET'])
@login_required
def export_students():
    # 管理员导出所有学生，非管理员只导出本学届学生
    if current_user.grade_name:
        students = Student.query.filter_by(grade_name=current_user.grade_name)
    else:
        students = Student.query.all()
    data = [{
        '学校代码': student.school_code,
        '学校名称': student.school_name,
        '班级代码': student.class_name,
        '学届': student.grade_name,
        '姓名': student.name,
        '学籍号': student.student_id,
        '考生类型1': student.exam_type,
        '考生类型2': student.exam_type1,
        '考号': student.exam_no,
        '科类属性': student.subject_type
    } for student in students]

    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Students', index=False)

    output.seek(0)

    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='stu-list.xlsx'
    )

@app.route('/delete_all_students', methods=['POST'])
@login_required
@admin_required
def delete_all_students():
    students = Student.query.all()
    for student in students:
        db.session.delete(student)
    db.session.commit()

    flash('所有考生信息已删除', 'info')
    return redirect(url_for('admin_panel'))

@app.route('/delete_all_teachers', methods=['POST'])
@login_required
@admin_required
def delete_all_teachers():
    teachers = Teacher.query.all()
    for teacher in teachers:
        db.session.delete(teacher)
    db.session.commit()

    flash('所有教师信息已删除', 'info')
    return redirect(url_for('admin_panel'))

@app.route('/student_stats', methods=['GET'])
@login_required
def student_stats():
    # 获取所有学校名称并去重
    school_names = set([user.school_name for user in User.query.filter(User.school_name != '').all()])

    # 计算每个学校的学生人数
    student_stats = []
    for school_name in school_names:
        if current_user.grade_name:
            student_count = Student.query.filter_by(school_name=school_name, grade_name=current_user.grade_name).count()
        else:
            student_count = Student.query.filter_by(school_name=school_name).count()

        student_stats.append({
            'school_name': school_name,
            'student_count': student_count
        })

    return render_template('student_stats.html', student_stats=student_stats)

@app.route('/teacher_stats', methods=['GET'])
@login_required
def teacher_stats():
    # 获取所有学校名称并去重
    school_names = set([user.school_name for user in User.query.filter(User.school_name != '').all()])

    # 计算每个学校的学生人数
    teacher_stats = []
    for school_name in school_names:
        teacher_count = Teacher.query.filter_by(school_name=school_name).count()
        teacher_stats.append({
            'school_name': school_name,
            'teacher_count': teacher_count
        })

    return render_template('teacher_stats.html', teacher_stats=teacher_stats)

@app.route('/teacher_list')
def teacher_list():
    page = request.args.get('page', 1, type=int)
    sort_by = request.args.get('sort_by', 'name', type=str)

    query = Teacher.query.filter_by(school_name=current_user.school_name)

    if sort_by == 'name':
        query = query.order_by(Teacher.name)
    elif sort_by == 'teaching_grade':
        query = query.order_by(Teacher.teaching_grade)
    elif sort_by == 'subjects':
        query = query.order_by(Teacher.subjects)

    pagination = query.paginate(page=page, per_page=20, error_out=False)
    teachers = pagination.items
    return render_template('teacher_list.html', teachers=teachers, pagination=pagination, sort_by=sort_by)

@app.route('/student_list')
def student_list():
    page = request.args.get('page', 1, type=int)
    sort_by = request.args.get('sort_by', 'name', type=str)

    query = Student.query.filter_by(school_name=current_user.school_name, grade_name=current_user.grade_name)

    if sort_by == 'name':
        query = query.order_by(Student.name)
    elif sort_by == 'exam_type':
        query = query.order_by(Student.exam_type)
    elif sort_by == 'subject_type':
        query = query.order_by(Student.subject_type)
    elif sort_by == 'exam_no':
        query = query.order_by(Student.exam_no)

    pagination = query.paginate(page=page, per_page=20, error_out=False)
    students = pagination.items
    return render_template('student_list.html', students=students, pagination=pagination, sort_by=sort_by)

@app.route('/export_teachers', methods=['GET'])
@login_required
def export_teachers():
    teachers = Teacher.query.all()
    data = [{
        '编码': teacher.code,
        '姓名': teacher.name,
        '单位': teacher.school_name,
        '任教学届': teacher.teaching_grade,
        '密码': teacher.password,
        '任教学科': teacher.subjects,
        '角色': teacher.role,
        '性别': teacher.gender,
        '是否启用': teacher.enabled
    } for teacher in teachers]

    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='教师列表', index=False)

    output.seek(0)

    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='teacher-list.xlsx'
    )

@app.route('/teacher/<int:teacher_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_teacher(teacher_id):
    teacher = Teacher.query.get_or_404(teacher_id)
    if teacher.school_name != current_user.school_name:
        flash('您无权编辑其他学校的教师信息', 'error')
        return redirect(url_for('teacher_list'))

    form = EditTeacherForm()
    if form.validate_on_submit():
        teacher.code = form.code.data
        teacher.name = form.name.data
        teacher.school_name = form.school_name.data
        teacher.teaching_grade = form.teaching_grade.data
        teacher.password = form.password.data
        teacher.subjects = form.subjects.data
        teacher.role = form.role.data
        teacher.gender = form.gender.data
        teacher.enabled = form.enabled.data
        db.session.commit()
        flash('教师信息已更新', 'info')
        return redirect(url_for('teacher_list'))
    
    elif request.method == 'GET':
        form.code.data = teacher.code
        form.name.data = teacher.name
        form.school_name.data = teacher.school_name
        form.teaching_grade.data = teacher.teaching_grade
        form.password.data = teacher.password
        form.subjects.data = teacher.subjects
        form.role.data = teacher.role
        form.gender.data = teacher.gender
        form.enabled.data = teacher.enabled

    return render_template('edit_teacher.html', form=form, teacher=teacher)

@app.route('/teacher/<int:teacher_id>/delete', methods=['POST'])
@login_required
def delete_teacher(teacher_id):
    teacher = Teacher.query.get_or_404(teacher_id)
    if teacher.school_name != current_user.school_name:
        flash('您无权删除其他学校的教师信息', 'error')
        return redirect(url_for('teacher_list'))

    db.session.delete(teacher)
    db.session.commit()
    flash('学生信息已删除')
    return redirect(url_for('teacher_list'))