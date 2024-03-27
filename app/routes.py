import io
from flask import render_template, redirect, request, send_file, session, url_for, flash
from flask_login import current_user, login_required, login_user, logout_user

import pandas as pd
from sqlalchemy import func
from app import app, db
from app.auth import admin_required
from app.forms import EditStudentForm, ImportStudentsForm, ImportUsersForm, LoginForm
from app.models import Student, User

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

@app.route('/admin')
@login_required
@admin_required
def admin_panel():
    non_admin_users = User.query.outerjoin(Student, User.nickname == Student.school_name) \
                                .add_columns(func.count(Student.id).label('student_count')) \
                                .filter(User.is_admin == False) \
                                .group_by(User.id) \
                                .all()
    return render_template('admin_panel.html', users=non_admin_users)


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
        
        expected_columns = ['用户名', '密码', '学校简称']
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

        if form.replace.data:
            # 清除非管理员用户
            non_admin_users = User.query.filter_by(is_admin=False).all()
            for user in non_admin_users:
                db.session.delete(user)
            db.session.commit()
            
        # 导入新用户
        for _, row in df.iterrows():
            user = User(username=row['用户名'], nickname=row['学校简称'])
            user.set_password(str(row['密码']))
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

        expected_columns = ['学校代码', '学校名称', '班级代码', '姓名', '学籍号', '考生类型', '考号', '科类属性']
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
            return redirect(url_for('import_students'))
        
        if form.replace.data:
            # 清理现有学生
            existing_students = Student.query.filter_by(school_name=current_user.nickname).all()
            for student in existing_students:
                db.session.delete(student)
            db.session.commit()

        valid_exam_types = ["物化生", "物化政", "物化地", "物生地", "物生政", "物地政", "历化政", "历化生", "历化地", "历生政", "历生地", "历政地"]
        valid_subject_types = ["物理类", "历史类"]        

        # 导入学生
        for _, row in df.iterrows():
            # 检查学校名称
            if row['学校名称'] != current_user.nickname:
                    flash(f"第{_+2}行数据为非本校学生或学校名称不匹配,请修正后重新导入", 'error')
                    return redirect(url_for('import_students'))

            # 检查考生类型
            if row['考生类型'] not in valid_exam_types:
                flash(f"第{_+2}行数据考生类型不正确,请修正后重新导入", 'error')
                return redirect(url_for('import_students'))

            # 检查考号位数
            if len(str(row['考号'])) != 10:
                flash(f"第{_+2}行数据考号位数不正确,请修正后重新导入", 'error')
                return redirect(url_for('import_students'))

            # 检查班级代码
            if len(str(row['班级代码'])) != 3:
                flash(f"第{_+2}行数据班级代码位数不正确,请修正后重新导入", 'error')
                return redirect(url_for('import_students'))

            # 检查科类属性
            if row['科类属性'] not in valid_subject_types:
                flash(f"第{_+2}行数据科类属性不正确,请修正后重新导入", 'error')
                return redirect(url_for('import_students'))
            
            student = Student(
                school_code=row['学校代码'], 
                school_name=row['学校名称'],
                class_name=row['班级代码'],
                name=row['姓名'],
                student_id=row['学籍号'],
                exam_type=row['考生类型'],
                exam_no=row['考号'],
                subject_type=row['科类属性']
            )
            db.session.add(student)
        db.session.commit()
        flash('本校考生信息导入成功', 'info')
        return redirect(url_for('import_students'))
        
    return render_template('import_students.html', form=form)

@app.route('/user', methods=['GET', 'POST'])
@login_required
def user_panel():
    page = request.args.get('page', 1, type=int)
    sort_by = request.args.get('sort_by', 'name', type=str)

    query = Student.query.filter_by(school_name=current_user.nickname)

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

    return render_template('user_panel.html', students=students, pagination=pagination, sort_by=sort_by)

@app.route('/student/<int:student_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_student(student_id):
    student = Student.query.get_or_404(student_id)
    if student.school_name != current_user.nickname:
        flash('您无权编辑其他学校的学生信息', 'error')
        return redirect(url_for('user_panel'))

    form = EditStudentForm()
    if form.validate_on_submit():
        student.name = form.name.data
        student.student_id = form.student_id.data
        student.exam_type = form.exam_type.data
        student.subject_type = form.subject_type.data
        student.school_code = form.school_code.data
        student.school_name = form.school_name.data
        student.class_name = form.class_name.data
        student.exam_no = form.exam_no.data
        db.session.commit()
        flash('学生信息已更新', 'info')
        return redirect(url_for('user_panel'))
    elif request.method == 'GET':
        form.name.data = student.name
        form.student_id.data = student.student_id
        form.exam_type.data = student.exam_type
        form.subject_type.data = student.subject_type
        form.school_code.data = student.school_code
        form.school_name.data = student.school_name
        form.class_name.data = student.class_name
        form.exam_no.data = student.exam_no

    return render_template('edit_student.html', form=form, student=student)

@app.route('/student/<int:student_id>/delete', methods=['POST'])
@login_required
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    if student.school_name != current_user.nickname:
        flash('您无权删除其他学校的学生信息', 'error')
        return redirect(url_for('user_panel'))

    db.session.delete(student)
    db.session.commit()
    flash('学生信息已删除')
    return redirect(url_for('user_panel'))

@app.route('/student/new', methods=['GET', 'POST'])
@login_required
def new_student():
    form = EditStudentForm()
    if form.validate_on_submit():
        student = Student(
            name=form.name.data,
            student_id=form.student_id.data,
            exam_type=form.exam_type.data,
            subject_type=form.subject_type.data,
            school_code=form.school_code.data,
            class_name=form.class_name.data,
            exam_no=form.exam_no.data,
            school_name=form.school_name.data
        )
        db.session.add(student)
        db.session.commit()
        flash('新学生信息已添加', 'info')
        return redirect(url_for('user_panel'))
    return render_template('new_student.html', form=form)

@app.route('/export_students', methods=['GET'])
@login_required
def export_students():
    students = Student.query.all()
    data = [{
        '学校代码': student.school_code,
        '学校名称': student.school_name,
        '班级代码': student.class_name,
        '姓名': student.name,
        '学籍号': student.student_id,
        '考生类型': student.exam_type,
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

    flash('所有学生信息已删除', 'info')
    return redirect(url_for('admin_panel'))