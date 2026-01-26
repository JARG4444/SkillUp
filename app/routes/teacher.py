from flask import Blueprint, render_template, request, redirect, url_for, current_app, flash
from ..models.teacher import Teacher
from ..extensions import db
import os
from werkzeug.utils import secure_filename
from flask_login import login_required, current_user

teacher = Blueprint('teacher', __name__)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

@teacher.route('/teachers', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        try:
            name = request.form.get('teacher-name')
            exp = request.form.get('teacher-exp')
            subject = request.form.get('teacher-subject')
            bio = request.form.get('teacher-bio')
            
            photo = request.files['teacher-photo']
            filename = None
            
            if photo and allowed_file(photo.filename):
                upload_folder = os.path.join(current_app.static_folder, 'uploads', 'teachers')
                os.makedirs(upload_folder, exist_ok=True)
                
                filename = secure_filename(f"teacher_{name}_{photo.filename}")
                photo_path = os.path.join(upload_folder, filename)
                photo.save(photo_path)
                filename = f"uploads/teachers/{filename}"  
            
            new_teacher = Teacher(
                name=name,
                exp=exp,
                subject=subject,
                bio=bio,
                photo=filename if filename else 'img/default-teacher.jpg'
            )
            
            db.session.add(new_teacher)
            db.session.commit()
            
            flash('Преподователь успешно добавлен!', 'success')
            return redirect(url_for('teacher.create'))
            
        except Exception as e:
            print(f"Ошибка: {e}")
            db.session.rollback()
            return str(e), 500
            flash(f'Ошибка при добавлении преподователя: {str(e)}', 'error')
    
    teachers = Teacher.query.all()
    return render_template('main/teachers.html', teachers=teachers)

@teacher.route('/teachers/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    teacher = Teacher.query.get(id)

    request.method == 'POST'
    try:
        db.session.delete(teacher)
        db.session.commit()
        return redirect(url_for('teacher.create'))

    except Exception as e:
        print(f"Ошибка: {e}")
        db.session.rollback()
        return str(e), 500

@teacher.route('/teachers/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    if current_user.status != 'admin':
        flash('Доступ запрещен', 'error')
        return redirect(url_for('teacher.create'))
    teacher = Teacher.query.get(id)
    
    if request.method == 'POST':

        teacher.name = request.form.get('teacher-name')
        teacher.exp = request.form.get('teacher-exp')
        teacher.subject = request.form.get('teacher-subject')
        teacher.bio = request.form.get('teacher-bio')
        
        try:
            db.session.commit()
            flash('Преподаватель успешно обновлен!', 'success')
            return redirect(url_for('teacher.create'))

        except Exception as e:
            print(f"Ошибка: {e}")
            db.session.rollback()
            return str(e), 500
    else:
        return render_template('main/edit_teacher.html', teacher=teacher)