from flask import Blueprint, render_template, request, redirect, url_for, current_app, flash
from flask_login import login_user, logout_user, current_user, login_required
from ..models.user import User
from ..models.post import Post, teacher_course
from ..extensions import db, bcrypt, login_manager
import re 

user = Blueprint('user' , __name__)

def validate_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email)

def validate_password(password):
    return len(password) >= 8

@user.route('/', methods=['GET', 'POST'])
def index():
    return render_template('main/index.html')

@user.route('/contacts', methods=['GET', 'POST'])
def contacts():
    return render_template('main/contacts.html')


@user.route('/account')
@login_required
def account():
    return render_template('main/account.html')

@user.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = (request.form.get('name') or '').strip()
        login_value = (request.form.get('login') or '').strip()
        email = (request.form.get('email') or '').strip().lower()
        password = request.form.get('password') or ''
        confirm_password = request.form.get('confirm_password') or ''
        status = request.form.get('status')

        errors = []

        if not validate_email(email):
            errors.append('Некорректный email')

        if not validate_password(password):
            errors.append('Пароль должен содержать минимум 8 символов')

        if password != confirm_password:
            errors.append('Пароли не совпадают')

        if not status:
            errors.append('Укажите ваш статус')

        if User.query.filter_by(email=email).first():
            errors.append('Этот email уже зарегистрирован')
        if User.query.filter_by(login=login_value).first():
            errors.append('Этот логин уже занят')

        if errors:
            for error in errors:
                flash(error, 'error')
            return redirect(url_for('user.register'))

        new_user = User(
            name=name,
            login=login_value,
            email=email,
            status=status
        )

        new_user.set_password(password)

        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Вы успешно зарегистрировались', 'success')
            return redirect(url_for('user.login'))
        except Exception as e:
            current_app.logger.exception("Ошибка регистрации")
            db.session.rollback()
            flash('При регистрации произошла ошибка', 'error')
            return redirect(url_for('user.register'))

    return render_template('main/register.html')

@user.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        login_credential = (request.form.get('login') or '').strip()
        raw_password = request.form.get('password') or ''
        remember = True if request.form.get('remember') else False

        user_obj = User.query.filter(
            (User.email == login_credential) | (User.login == login_credential)
        ).first()

        if user_obj and user_obj.check_password(raw_password):
            login_user(user_obj, remember=remember)
            flash('Вы успешно вошли в систему', 'success')
            return redirect(url_for('user.index'))
        else:
            flash('Неверный логин/email или пароль', 'error')
            return redirect(url_for('user.login'))

    return render_template('main/login.html')

@user.route('/user/logout')
def logout():
    logout_user()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('user.index'))

@user.route('/admin/users')
@login_required
def admin_users():
    if current_user.status != 'admin':
        flash('Доступ запрещен', 'error')
        return redirect(url_for('user.account'))
    
    students = User.query.filter_by(status='student').all()
    teachers = User.query.filter_by(status='teacher').all()
    all_courses = Post.query.all()
    
    return render_template('main/adminform.html', 
                         students=students, 
                         teachers=teachers,
                         all_courses=all_courses)

@user.route('/admin/user/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.status != 'admin':
        flash('Доступ запрещен', 'error')
        return redirect(url_for('user.admin_users'))
    
    if current_user.id == user_id:
        flash('Нельзя удалить самого себя', 'error')
        return redirect(url_for('user.admin_users'))
    
    user_to_delete = User.query.get(user_id)
    if not user_to_delete:
        flash('Пользователь не найден', 'error')
        return redirect(url_for('user.admin_users'))
    
    try:
        db.session.delete(user_to_delete)
        db.session.commit()
        flash('Пользователь успешно удален', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении: {str(e)}', 'error')
    
    return redirect(url_for('user.admin_users'))


@user.route('/admin/assign-course', methods=['POST'])
@login_required
def assign_course():
    if current_user.status != 'admin':
        flash('Доступ запрещен', 'error')
        return redirect(url_for('user.admin_users'))
    
    teacher_id = request.form.get('teacher_id')
    course_id = request.form.get('course_id')
    
    teacher = User.query.get(teacher_id)
    course = Post.query.get(course_id)
    
    if not teacher or not course:
        flash('Пользователь или курс не найден', 'error')
        return redirect(url_for('user.admin_users'))
    
    if teacher.status != 'teacher':
        flash('Можно назначать курсы только преподавателям', 'error')
        return redirect(url_for('user.admin_users'))
    
    try:
        if teacher.assign_to_course(course):
            flash('Преподаватель успешно прикреплен к курсу', 'success')
        else:
            flash('Преподаватель уже прикреплен к этому курсу', 'info')
    except Exception as e:
        flash(f'Ошибка: {str(e)}', 'error')
    
    return redirect(url_for('user.admin_users'))

@user.route('/admin/teacher/<int:teacher_id>/course/<int:course_id>/remove', methods=['POST'])
@login_required
def remove_course(teacher_id, course_id):
    if current_user.status != 'admin':
        flash('Доступ запрещен', 'error')
        return redirect(url_for('user.admin_users'))
    
    teacher = User.query.get(teacher_id)
    course = Post.query.get(course_id)
    
    if not teacher or not course:
        flash('Пользователь или курс не найден', 'error')
        return redirect(url_for('user.admin_users'))
    
    try:
        if teacher.remove_from_course(course):
            flash('Преподаватель убран с курса', 'success')
        else:
            flash('Преподаватель не был прикреплен к этому курсу', 'info')
    except Exception as e:
        flash(f'Ошибка: {str(e)}', 'error')
    
    return redirect(url_for('user.admin_users'))

