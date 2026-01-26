from ..extensions import db, login_manager, bcrypt
from flask_login import UserMixin
from ..models.post import user_course, teacher_course

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(100), default='student')
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True, index=True)
    login = db.Column(db.String(50), unique=True, index=True)
    password = db.Column(db.String(500))  


    def set_password(self, raw_password: str) -> None:
        self.password = bcrypt.generate_password_hash(raw_password).decode('utf-8')

    def check_password(self, raw_password: str) -> bool:
        return bcrypt.check_password_hash(self.password, raw_password)


    def enroll_in_course(self, course):
        if course not in self.courses:
            self.courses.append(course)
            db.session.commit()
    
    def add_free_lesson(self, course):
        from sqlalchemy import update
        stmt = user_course.update().where(
            (user_course.c.user_id == self.id) & 
            (user_course.c.course_id == course.id)
        ).values(has_free_lesson=True)
        db.session.execute(stmt)
        db.session.commit()
    
    def is_enrolled(self, course):
        return course in self.courses
    
    def has_free_lesson(self, course):
        from sqlalchemy import select
        stmt = select(user_course.c.has_free_lesson).where(
            (user_course.c.user_id == self.id) & 
            (user_course.c.course_id == course.id)
        )
        result = db.session.execute(stmt).scalar()
        return result or False

    def assign_to_course(self, course):
        if course not in self.teaching_courses:
            self.teaching_courses.append(course)
            db.session.commit()
            return True
        return False
    
    def remove_from_course(self, course):
        if course in self.teaching_courses:
            self.teaching_courses.remove(course)
            db.session.commit()
            return True
        return False
