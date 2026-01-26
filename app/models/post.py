from ..extensions import db
from datetime import datetime

user_course = db.Table('user_course',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('course_id', db.Integer, db.ForeignKey('post.id'), primary_key=True),
    db.Column('enrolled_at', db.DateTime, default=datetime.utcnow),
    db.Column('has_free_lesson', db.Boolean, default=False)
)

teacher_course = db.Table('teacher_course',
    db.Column('teacher_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('course_id', db.Integer, db.ForeignKey('post.id'), primary_key=True),
    db.Column('assigned_at', db.DateTime, default=datetime.utcnow)
)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False) 
    bio = db.Column(db.String(300), nullable=False)   
    exp = db.Column(db.String(50), nullable=False)    
    level = db.Column(db.String(50), nullable=False)  
    photo = db.Column(db.String(300))                 
    tag = db.Column(db.String(50))                    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    students = db.relationship('User', secondary=user_course, backref=db.backref('courses', lazy='dynamic'))

    teachers = db.relationship('User', secondary=teacher_course, backref=db.backref('teaching_courses', lazy='dynamic'))

    modules = db.relationship('CourseModule', backref='course', lazy=True, order_by='CourseModule.order')
    
    def __repr__(self):
        return f'<Course {self.name}>'

    