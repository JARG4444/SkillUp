from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename
from ..models.post import Post
from ..models.user import User
from ..extensions import db
import os
from flask_login import login_required, current_user

post = Blueprint('post', __name__)

UPLOAD_FOLDER = 'app/static/uploads/courses'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@post.route('/courses', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            bio = request.form.get('bio')
            exp = request.form.get('exp')
            level = request.form.get('level')
            tag = request.form.get('tag')
            
            photo = request.files['photo']
            filename = None
            
            if photo and allowed_file(photo.filename):
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                
                filename = secure_filename(f"course_{name}_{photo.filename}")
                photo_path = os.path.join(UPLOAD_FOLDER, filename)
                photo.save(photo_path)
                filename = f"uploads/courses/{filename}"
            
            new_course = Post(
                name=name,
                bio=bio,
                exp=exp,
                level=level,
                photo=filename,
                tag=tag
            )
            
            db.session.add(new_course)
            db.session.commit()
            
            flash('Курс успешно добавлен!', 'success')
            return redirect(url_for('post.create'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при добавлении курса: {str(e)}', 'error')
    
    courses = Post.query.order_by(Post.created_at.desc()).all()
    return render_template('main/courses.html', courses = courses)


@post.route('/courses/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    if current_user.status != 'admin':
        flash('Доступ запрещен', 'error')
        return redirect(url_for('post.create'))

    course = Post.query.get(id)
    
    if request.method == 'POST':

        course.name = request.form.get('name')
        course.bio = request.form.get('bio')
        course.exp = request.form.get('exp')
        course.level = request.form.get('level')
        course.tag = request.form.get('tag')
        
        try:
            db.session.commit()
            flash('Курс успешно обновлен!', 'success')
            return redirect(url_for('post.create'))

        except Exception as e:
            print(f"Ошибка: {e}")
            db.session.rollback()
            return str(e), 500
        
    else:
        return render_template('main/courses_edit.html', course = course)

@post.route('/courses/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    course = Post.query.get(id)
    
    try:        
        db.session.delete(course)
        db.session.commit()
        flash('Курс успешно удален!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении курса: {str(e)}', 'error')
    
    return redirect(url_for('post.create'))

@post.route('/courses/<int:id>/info', methods=['POST', 'GET'])
def detail(id):
    course = Post.query.get(id)
    return render_template('main/courses_detail.html', course = course)


@post.route('/courses/<int:id>/enroll', methods=['POST'])
@login_required
def enroll(id):
    course = Post.query.get(id)
    if not course:
        flash('Курс не найден', 'error')
        return redirect(url_for('post.create'))
    
    if current_user.is_enrolled(course):
        flash('Вы уже записаны на этот курс', 'info')
    else:
        current_user.enroll_in_course(course)
        flash('Вы успешно записались на курс!', 'success')
    
    return redirect(url_for('post.detail', id=id))

@post.route('/courses/<int:id>/free-lesson', methods=['POST'])
@login_required
def free_lesson(id):
    course = Post.query.get(id)
    if not course:
        flash('Курс не найден', 'error')
        return redirect(url_for('post.create'))
    
    if not current_user.is_enrolled(course):
        current_user.enroll_in_course(course)
    
    if current_user.has_free_lesson(course):
        flash('Вы уже получили бесплатный урок', 'info')
    else:
        current_user.add_free_lesson(course)
        flash('Бесплатный урок добавлен в ваш аккаунт!', 'success')
    
    return redirect(url_for('post.detail', id=id))