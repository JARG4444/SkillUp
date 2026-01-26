
from datetime import datetime
from enum import Enum

from ..extensions import db


class CourseModule(db.Model):
    __tablename__ = "course_module"

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("post.id"), nullable=False)  
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    order = db.Column(db.Integer, nullable=False, default=1)


    lessons = db.relationship(
        "CourseLesson",
        backref="module",
        cascade="all, delete-orphan",
        order_by="CourseLesson.order",
        lazy="dynamic",
    )


class LessonType(str, Enum):
    lecture = "lecture"
    test = "test"
    lab = "lab"


class CourseLesson(db.Model):
    __tablename__ = "course_lesson"

    id = db.Column(db.Integer, primary_key=True)
    module_id = db.Column(db.Integer, db.ForeignKey("course_module.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    order = db.Column(db.Integer, nullable=False, default=1)

    # Тип урока
    lesson_type = db.Column(db.String(12), nullable=False, default="lecture")

    __table_args__ = (
        db.CheckConstraint(
            "lesson_type IN ('lecture','test','lab')",
            name="ck_course_lesson_type",
        ),
    )

    # Поля для лекции
    html_content = db.Column(db.Text, nullable=True)     
    video_url    = db.Column(db.String(500), nullable=True)

    # Поля для лабы
    sandbox_slug = db.Column(db.String(150), nullable=True)

    # Поле для теста 
    test = db.relationship(
        "CourseTest",
        backref="lesson",
        uselist=False,
        cascade="all, delete-orphan",
    )


class CourseTest(db.Model):
    __tablename__ = "course_test"

    id = db.Column(db.Integer, primary_key=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey("course_lesson.id"), nullable=False, unique=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)

    questions = db.relationship(
        "TestQuestion",
        backref="test",
        cascade="all, delete-orphan",
        order_by="TestQuestion.order",
    )


class TestQuestion(db.Model):
    __tablename__ = "test_question"

    id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(db.Integer, db.ForeignKey("course_test.id"), nullable=False)
    order = db.Column(db.Integer, nullable=False, default=1)

    question = db.Column(db.Text, nullable=False)  # текст вопроса

    options = db.relationship(
        "TestOption",
        backref="question",
        cascade="all, delete-orphan",
        order_by="TestOption.order",
    )


class TestOption(db.Model):
    __tablename__ = "test_option"

    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey("test_question.id"), nullable=False)
    order = db.Column(db.Integer, nullable=False, default=1)

    option_text = db.Column(db.Text, nullable=False)
    is_correct  = db.Column(db.Boolean, default=False)


class TestAttempt(db.Model):
    __tablename__ = "test_attempt"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    lesson_id  = db.Column(db.Integer, db.ForeignKey('course_lesson.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    score = db.Column(db.Integer, nullable=False, default=0)  # верных
    total = db.Column(db.Integer, nullable=False, default=0)  # всего

class LabAttempt(db.Model):
    __tablename__ = "lab_attempt"

    id = db.Column(db.Integer, primary_key=True)

    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey("course_lesson.id"), nullable=False)

    submitted_flag = db.Column(db.String(255), nullable=False)
    is_correct = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class StudentProgress(db.Model):
    __tablename__ = "student_progress"

    id = db.Column(db.Integer, primary_key=True)

    
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    
    course_id = db.Column(db.Integer, db.ForeignKey("post.id"), nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey("course_lesson.id"), nullable=False)

    
    completed = db.Column(db.Boolean, default=False, nullable=False)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)

   
    score = db.Column(db.Float, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<StudentProgress student={self.student_id} lesson={self.lesson_id} score={self.score}>"

class LabDefinition(db.Model):
    __tablename__ = "lab_definition"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=True)

    correct_flag = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f"<LabDefinition {self.slug}>"
