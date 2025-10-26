import io
from sqlalchemy.exc import IntegrityError
from flask import render_template, redirect, request, send_file, session, url_for, flash
from flask_login import current_user, login_required, login_user, logout_user

import pandas as pd
from sqlalchemy import func
from app import app, db
from app.auth import admin_required
from app.forms import EditStudentForm, EditTeacherForm, ImportStudentsForm, ImportTeachersForm, ImportUsersForm, LoginForm, SearchStudentForm, SearchTeacherForm, NewStudentForm
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
        elif request.form.get('action') == 'delete_grade_students':
            grade_name = request.form.get('grade_name')
            students = Student.query.filter_by(grade_name=grade_name).all()
            for student in students:
                db.session.delete(student)
            db.session.commit()
            flash(f'已删除 {grade_name} 的所有学生', 'success')
        elif request.form.get('action') == 'delete_grade_teachers':
            grade_name = request.form.get('grade_name')
            teachers = Teacher.query.filter_by(teaching_grade=grade_name).all()
            for teacher in teachers:
                db.session.delete(teacher)
            db.session.commit()
            flash(f'已删除 {grade_name} 的所有教师', 'success')

    users = User.query.filter_by(is_admin=False).order_by(User.school_name).all()
    
    # 获取所有学届
    grades = db.session.query(User.grade_name).filter_by(is_admin=False).distinct().all()
    grades = [grade[0] for grade in grades if grade[0]]  # 移除空值
    
    # 获取每个学届的学生和教师数量
    grade_stats = []
    for grade in grades:
        student_count = Student.query.filter_by(grade_name=grade).count()
        teacher_count = Teacher.query.filter_by(teaching_grade=grade).count()
        grade_stats.append({
            'grade_name': grade,
            'student_count': student_count,
            'teacher_count': teacher_count
        })
    
    return render_template('admin_panel.html', 
                         users=users, 
                         grade_stats=grade_stats)

@app.route('/import_users', methods=['GET', 'POST'])
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
        
        expected_columns = ['用户名', '密码', '学届', '学校简称', '学校代码']
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
            # 验证学校代码
            try:
                school_code = int(str(row['学校代码']).strip())
                if school_code < 1 or school_code > 999:
                    flash('学校代码必须是1-3位的正整数', 'error')
                    return redirect(url_for('import_users'))
            except ValueError:
                flash('学校代码必须是数字', 'error')
                return redirect(url_for('import_users'))

            user = User(
                username=row['用户名'].strip(), 
                grade_name=row['学届'].strip(), 
                school_name=row['学校简称'].strip(),
                school_code=school_code
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
        try:
            df = pd.read_excel(file)
        except Exception as e:
            flash(f'读取Excel文件失败: {str(e)}', 'error')
            return redirect(url_for('import_students'))

        # 根据是否分科确定必需列
        required_columns = ['姓名', '考号', '学校名称', '学届']
        if not form.not_divided.data:  # 如果已分科，则需要考生类型列
            required_columns.append('考生类型')

        # 检查必需列是否存在
        missing_columns = set(required_columns) - set(df.columns)
        if missing_columns:
            flash(f"缺少必需列: {', '.join(missing_columns)}。文件包含的列: {', '.join(df.columns.tolist())}", 'error')
            return redirect(url_for('import_students'))
        
        # 检查是否存在考号重复学生
        if not df["考号"].is_unique:
            # 找出重复的考号
            duplicated_exam_nos = df[df["考号"].duplicated(keep=False)]["考号"].unique().tolist()
            duplicated_exam_nos = [str(no) for no in duplicated_exam_nos]
            flash(f"学生考号不唯一，重复的考号: {', '.join(duplicated_exam_nos[:10])}{'...' if len(duplicated_exam_nos) > 10 else ''}", 'error')
            return redirect(url_for('import_students'))

        if form.replace.data:
            # 清理本校本学届现有学生
            existing_students = Student.query.filter_by(
                school_name=current_user.school_name, 
                grade_name=current_user.grade_name
            ).all()
            for student in existing_students:
                db.session.delete(student)
            db.session.commit()

        valid_exam_types = ["物化生", "物化政", "物化地", "物生地", "物生政", "物政地", 
                          "历化政", "历化生", "历化地", "历生政", "历生地", "历政地"]

        # 导入学生
        error_records = []
        for index, row in df.iterrows():
            row_num = index + 2  # Excel行号（加2是因为索引从0开始，且有标题行）
            student_name = str(row['姓名']).strip()
            
            # 检查学校名称
            school_name = str(row['学校名称']).strip()
            if school_name != current_user.school_name:
                error_records.append(f"第{row_num}行: 学生 '{student_name}' 的学校名称 '{school_name}' 与当前账号学校 '{current_user.school_name}' 不匹配")
                continue

            # 检查学届
            grade_name = str(row['学届']).strip()
            if grade_name != current_user.grade_name:
                error_records.append(f"第{row_num}行: 学生 '{student_name}' 的学届 '{grade_name}' 与当前账号学届 '{current_user.grade_name}' 不匹配")
                continue

            # 检查考号位数
            exam_no = str(row['考号']).strip()
            if len(exam_no) != 10:
                error_records.append(f"第{row_num}行: 学生 '{student_name}' 的考号 '{exam_no}' 不是10位数")
                continue

            # 生成班级代码（学校代码 + 考号第3-4位）
            try:
                class_code = str(current_user.school_code).zfill(1) + exam_no[2:4]
                if len(class_code) != 3:
                    error_records.append(f"第{row_num}行: 学生 '{student_name}' 生成的班级代码 '{class_code}' 不是3位数")
                    continue
            except Exception as e:
                error_records.append(f"第{row_num}行: 学生 '{student_name}' 生成班级代码时出错: {str(e)}")
                continue

            # 处理考生类型和科类属性
            exam_type = ''
            subject_type = ''
            if not form.not_divided.data:  # 如果已分科
<<<<<<< HEAD
                try:
                    exam_type1 = str(row['考生类型']).strip()
                    if exam_type1 not in valid_exam_types:
                        error_records.append(f"第{row_num}行: 学生 '{student_name}' 的考生类型 '{exam_type1}' 不在有效类型列表中")
                        continue
                    # 根据考生类型判断科类属性
                    subject_type = "物理类" if exam_type1.startswith('物') else "历史类"
                except Exception as e:
                    error_records.append(f"第{row_num}行: 学生 '{student_name}' 处理考生类型时出错: {str(e)}")
                    continue
=======
                exam_type = str(row['考生类型']).strip()
                if exam_type not in valid_exam_types:
                    flash(f"存在考生类型不正确,请修正后重新导入", 'error')
                    return redirect(url_for('import_students'))
                # 根据考生类型判断科类属性
                subject_type = "物理类" if exam_type.startswith('物') else "历史类"
>>>>>>> origin/main

            # 创建学生记录
            student = Student(
                school_code=current_user.school_code,
                school_name=current_user.school_name,
                grade_name=current_user.grade_name,
                class_name=class_code,
<<<<<<< HEAD
                name=student_name,
                student_id='',  # 学籍号可为空
                exam_type=exam_type1,  # 考生类型1
                exam_type1='',  # 考生类型2可为空
=======
                name=str(row['姓名']).strip(),
                exam_type=exam_type,
>>>>>>> origin/main
                exam_no=exam_no,
                subject_type=subject_type
            )
            db.session.add(student)

        # 如果有错误记录，回滚并显示错误
        if error_records:
            db.session.rollback()
            # 只显示前10条错误，避免消息过长
            error_display = '\n'.join(error_records[:10])
            if len(error_records) > 10:
                error_display += f"\n...还有 {len(error_records) - 10} 条错误未显示"
            flash(f'导入失败，以下数据有问题:\n{error_display}', 'error')
            return redirect(url_for('import_students'))

        try:
            db.session.commit()
            flash('考生导入成功', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'导入失败: {str(e)}', 'error')
            
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

        # 检查必需列
        required_columns = ['姓名', '身份证号', '任教学科', '学校名称', '任教学届']
        missing_columns = set(required_columns) - set(df.columns)
        if missing_columns:
            flash(f"缺少必需列: {', '.join(missing_columns)}", 'error')
            return redirect(url_for('import_teachers'))

        if form.replace.data:
            # 清理现有教师
            existing_teachers = Teacher.query.filter_by(school_name=current_user.school_name).all()
            for teacher in existing_teachers:
                db.session.delete(teacher)
            db.session.commit()

        valid_subjects = ['语文', '数学', '英语', '物理', '化学', '生物', '政治', '历史', '地理']

        # 检查身份证号是否有重复
        if not df["身份证号"].is_unique:
            flash(f"存在重复的身份证号，请检查后重新导入", 'error')
            return redirect(url_for('import_teachers'))

        # 导入教师
        for index, row in df.iterrows():
            # 检查学校名称
            if str(row['学校名称']).strip() != current_user.school_name:
                flash(f"存在非本校教师或学校名称缺失或不匹配,请修正后重新导入", 'error')
                return redirect(url_for('import_teachers'))

            # 检查身份证号格式
            id_number = str(row['身份证号']).strip()
            if not is_valid_id_number(id_number):
                flash(f"存在无效的身份证号，请检查后重新导入", 'error')
                return redirect(url_for('import_teachers'))

            # 检查任教学科
            subject = str(row['任教学科']).strip()
            if subject not in valid_subjects:
                flash(f"存在教师任教学科不正确,请修正后重新导入", 'error')
                return redirect(url_for('import_teachers'))

            # 从身份证号获取性别
            gender = '男' if int(id_number[-2]) % 2 == 1 else '女'

            teacher = Teacher(
                code=id_number,  # 使用身份证号作为编码
                name=str(row['姓名']).strip(),
                school_name=str(row['学校名称']).strip(),
                teaching_grade=str(row['任教学届']).strip(),
                password=id_number[-6:],  # 使用身份证号后6位作为密码
                subjects=subject,
                role='任课教师',  # 默认角色
                gender=gender,  # 根据身份证号判断性别
                enabled=True  # 默认启用
            )
            db.session.add(teacher)

        try:
            db.session.commit()
            flash('教师信息导入成功', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'导入失败: {str(e)}', 'error')
            
        return redirect(url_for('import_teachers'))
        
    return render_template('import_teachers.html', form=form)

def is_valid_id_number(id_number):
    """验证身份证号是否合法"""
    if len(id_number) != 18:
        return False
    
    # 检查前17位是否都是数字
    if not id_number[:-1].isdigit():
        return False
    
    # 检查最后一位是否是数字或X
    if not (id_number[-1].isdigit() or id_number[-1].upper() == 'X'):
        return False
    
    # 检查出生日期是否合法
    try:
        year = int(id_number[6:10])
        month = int(id_number[10:12])
        day = int(id_number[12:14])
        
        # 简单的日期验证
        if year < 1900 or year > 2100:
            return False
        if month < 1 or month > 12:
            return False
        if day < 1 or day > 31:
            return False
    except:
        return False
    
    return True

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
        student.exam_type = form.exam_type.data
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
        form.exam_type.data = student.exam_type
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

@app.route('/new_student', methods=['GET', 'POST'])
@login_required
def new_student():
    # 如果是管理员，重定向到学生列表页面
    if not current_user.grade_name:
        flash('管理员不能直接添加考生，请使用导入功能。', 'warning')
        return redirect(url_for('student_list'))

    form = NewStudentForm()
    if form.validate_on_submit():
        # 如果是确认提交
        if request.form.get('confirm'):
            # 从隐藏字段获取数据
            name = request.form.get('name')
            exam_no = request.form.get('exam_no')
            exam_type = request.form.get('exam_type')
            
            # 从考号获取班级代码
            class_name = str(current_user.school_code) + exam_no[2:4]
            
            # 根据考生类型判断科类属性
            subject_type = "物理类" if exam_type.startswith('物') else "历史类" if exam_type else ""

            # 创建新考生
            student = Student(
                name=name,
                exam_no=exam_no,
                exam_type=exam_type,
                school_code=current_user.school_code,
                school_name=current_user.school_name,
                grade_name=current_user.grade_name,
                class_name=class_name,
                subject_type=subject_type
            )

            try:
                db.session.add(student)
                db.session.commit()
                flash('考生添加成功！', 'success')
                return redirect(url_for('student_list'))
            except Exception as e:
                db.session.rollback()
                flash('添加失败：' + str(e), 'danger')
                return redirect(url_for('new_student'))
        
        # 如果是首次提交，显示预览
        else:
            # 检查考号是否已存在
            if Student.query.filter_by(exam_no=form.exam_no.data).first():
                flash('考号已存在！', 'danger')
                return redirect(url_for('new_student'))

            # 检查考号格式
            exam_no = form.exam_no.data
            if not exam_no.isdigit() or len(exam_no) != 10:
                flash('考号必须是10位数字！', 'danger')
                return redirect(url_for('new_student'))

            # 从考号获取班级代码
            class_name = str(current_user.school_code) + exam_no[2:4]
            
            # 根据考生类型判断科类属性
            exam_type = form.exam_type.data
            subject_type = "物理类" if exam_type.startswith('物') else "历史类" if exam_type else ""

            # 创建预览对象
            student = Student(
                name=form.name.data,
                exam_no=exam_no,
                exam_type=exam_type,
                school_code=current_user.school_code,
                school_name=current_user.school_name,
                grade_name=current_user.grade_name,
                class_name=class_name,
                subject_type=subject_type
            )

            return render_template('new_student.html', 
                                title='新增考生', 
                                form=form, 
                                preview=True, 
                                student=student)

    return render_template('new_student.html', 
                         title='新增考生', 
                         form=form, 
                         preview=False)

@app.route('/export_students', methods=['GET'])
@login_required
def export_students():
    # 管理员导出所有学生，非管理员只导出本学届学生
    if current_user.grade_name:
        students = Student.query.filter_by(grade_name=current_user.grade_name)
        sample_student = students.first()
        has_exam_type = sample_student and sample_student.exam_type
    else:
        students = Student.query.all()
        has_exam_type = False

    # 基础数据
    data = [{
        '学校代码': student.school_code,
        '学校名称': student.school_name,
        '班级代码': student.class_name,
        '学届': student.grade_name,
        '姓名': student.name,
        '考生类型': student.exam_type,
        '考号': student.exam_no,
        '科类属性': student.subject_type
    } for student in students]

    df = pd.DataFrame(data)
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='全部学生', index=False)

        # 如果已分科，则按科目分类导出
        if has_exam_type:
            # 创建各科目工作表
            physics_df = df[df['考生类型'].str.contains('物', na=False)]
            chemistry_df = df[df['考生类型'].str.contains('化', na=False)]
            biology_df = df[df['考生类型'].str.contains('生', na=False)]
            history_df = df[df['考生类型'].str.contains('历', na=False)]
            politics_df = df[df['考生类型'].str.contains('政', na=False)]
            geography_df = df[df['考生类型'].str.contains('地', na=False)]

            # 导出各科目工作表
            physics_df.to_excel(writer, sheet_name='物理', index=False)
            chemistry_df.to_excel(writer, sheet_name='化学', index=False)
            biology_df.to_excel(writer, sheet_name='生物', index=False)
            history_df.to_excel(writer, sheet_name='历史', index=False)
            politics_df.to_excel(writer, sheet_name='政治', index=False)
            geography_df.to_excel(writer, sheet_name='地理', index=False)

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

    # 检查当前学届是否已分科
    if current_user.grade_name:
        sample_student = Student.query.filter_by(grade_name=current_user.grade_name).first()
        has_exam_type = sample_student and sample_student.exam_type
    else:
        has_exam_type = False

    # 计算每个学校的学生统计信息
    student_stats = []
    total_stats = {
        'total': 0,
        'physics': 0,
        'chemistry': 0,
        'biology': 0,
        'history': 0,
        'politics': 0,
        'geography': 0
    }

    for school_name in school_names:
        if current_user.grade_name:
            students = Student.query.filter_by(school_name=school_name, grade_name=current_user.grade_name)
        else:
            students = Student.query.filter_by(school_name=school_name)

        student_count = students.count()
        school_stat = {
            'school_name': school_name,
            'student_count': student_count,
            'physics_count': 0,
            'chemistry_count': 0,
            'biology_count': 0,
            'history_count': 0,
            'politics_count': 0,
            'geography_count': 0
        }

        if has_exam_type:
            # 统计各科目人数
            for student in students:
                if student.exam_type:
                    if '物' in student.exam_type:
                        school_stat['physics_count'] += 1
                        total_stats['physics'] += 1
                    if '化' in student.exam_type:
                        school_stat['chemistry_count'] += 1
                        total_stats['chemistry'] += 1
                    if '生' in student.exam_type:
                        school_stat['biology_count'] += 1
                        total_stats['biology'] += 1
                    if '历' in student.exam_type:
                        school_stat['history_count'] += 1
                        total_stats['history'] += 1
                    if '政' in student.exam_type:
                        school_stat['politics_count'] += 1
                        total_stats['politics'] += 1
                    if '地' in student.exam_type:
                        school_stat['geography_count'] += 1
                        total_stats['geography'] += 1

        student_stats.append(school_stat)
        total_stats['total'] += student_count

    return render_template('student_stats.html', 
                         student_stats=student_stats, 
                         total_stats=total_stats,
                         has_exam_type=has_exam_type)

@app.route('/teacher_stats', methods=['GET'])
@login_required
def teacher_stats():
    # 获取所有学校名称并去重
    school_names = set([user.school_name for user in User.query.filter(User.school_name != '').all()])

    # 初始化总计数据
    total_stats = {
        'total': 0,
        'chinese': 0,
        'math': 0,
        'english': 0,
        'physics': 0,
        'chemistry': 0,
        'biology': 0,
        'history': 0,
        'politics': 0,
        'geography': 0
    }

    # 计算每个学校的教师统计信息
    teacher_stats = []
    for school_name in school_names:
        # 根据当前用户的学届筛选教师
        if current_user.grade_name:
            teachers = Teacher.query.filter_by(school_name=school_name, teaching_grade=current_user.grade_name)
        else:
            teachers = Teacher.query.filter_by(school_name=school_name)

        # 初始化学校统计数据
        school_stat = {
            'school_name': school_name,
            'teacher_count': 0,
            'chinese_count': 0,
            'math_count': 0,
            'english_count': 0,
            'physics_count': 0,
            'chemistry_count': 0,
            'biology_count': 0,
            'history_count': 0,
            'politics_count': 0,
            'geography_count': 0
        }

        # 统计各学科教师人数
        for teacher in teachers:
            school_stat['teacher_count'] += 1
            if teacher.subjects == '语文':
                school_stat['chinese_count'] += 1
                total_stats['chinese'] += 1
            elif teacher.subjects == '数学':
                school_stat['math_count'] += 1
                total_stats['math'] += 1
            elif teacher.subjects == '英语':
                school_stat['english_count'] += 1
                total_stats['english'] += 1
            elif teacher.subjects == '物理':
                school_stat['physics_count'] += 1
                total_stats['physics'] += 1
            elif teacher.subjects == '化学':
                school_stat['chemistry_count'] += 1
                total_stats['chemistry'] += 1
            elif teacher.subjects == '生物':
                school_stat['biology_count'] += 1
                total_stats['biology'] += 1
            elif teacher.subjects == '历史':
                school_stat['history_count'] += 1
                total_stats['history'] += 1
            elif teacher.subjects == '政治':
                school_stat['politics_count'] += 1
                total_stats['politics'] += 1
            elif teacher.subjects == '地理':
                school_stat['geography_count'] += 1
                total_stats['geography'] += 1

        teacher_stats.append(school_stat)
        total_stats['total'] += school_stat['teacher_count']

    return render_template('teacher_stats.html', 
                         teacher_stats=teacher_stats, 
                         total_stats=total_stats)

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
    # 管理员导出所有教师，非管理员只导出本学届教师
    if current_user.grade_name:
        teachers = Teacher.query.filter_by(teaching_grade=current_user.grade_name)
    else:
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
        '是否启用': '是' if teacher.enabled else '否'
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

@app.route('/search_student', methods=['GET', 'POST'])
@login_required
def search_student():
    form = SearchStudentForm()
    students = []
    
    if form.validate_on_submit():
        search_term = form.name.data
        students = Student.query.filter(
            Student.name.like(f'%{search_term}%'),
            Student.school_name == current_user.school_name,
            Student.grade_name == current_user.grade_name
        ).all()
        
        if not students:
            flash('未找到匹配的学生', 'info')
    
    return render_template('search_student.html', form=form, students=students)

@app.route('/search_teacher', methods=['GET', 'POST'])
@login_required
def search_teacher():
    form = SearchTeacherForm()
    teachers = []
    
    if form.validate_on_submit():
        search_term = form.name.data
        teachers = Teacher.query.filter(
            Teacher.name.like(f'%{search_term}%'),
            Teacher.school_name == current_user.school_name
        ).all()
        
        if not teachers:
            flash('未找到匹配的教师', 'info')
    
    return render_template('search_teacher.html', form=form, teachers=teachers)