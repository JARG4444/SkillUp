import os
from typing import List
from datetime import datetime

from flask import (
    Blueprint, render_template, request, redirect, url_for,
    flash, jsonify
)
from flask_login import login_required, current_user

from ..extensions import db
from ..models.post import Post, user_course  
from ..models.course import (
    CourseModule, CourseLesson, LessonType,
    CourseTest, TestQuestion, TestOption, TestAttempt,
    StudentProgress, LabAttempt, LabDefinition
)
from sqlalchemy import func
from ..models.user import User

course_bp = Blueprint("course", __name__)


SANDBOX_BASE_URL = os.getenv("SANDBOX_BASE_URL", "http://127.0.0.1:8000")
SANDBOX_API_KEY  = os.getenv("SANDBOX_API_KEY", "dev-secret-change-me")



UPLOAD_DIR = os.path.join("app", "static", "uploads", "courses")
os.makedirs(UPLOAD_DIR, exist_ok=True)





def is_teacher_or_admin(course: Post) -> bool:
    """Проверка: текущий пользователь — админ или преподаватель этого курса."""
    if not current_user.is_authenticated:
        return False

    # Глобальный админ
    if getattr(current_user, "status", None) == "admin":
        return True

    # Преподаватель, привязанный к курсу
    if getattr(current_user, "status", None) == "teacher":
        return current_user in course.teachers

    return False


def require_teacher_or_admin(course: Post):
    """Если нет прав – редирект с флешкой, иначе вернуть None."""
    if not is_teacher_or_admin(course):
        flash("Доступ запрещен", "error")
        return redirect(url_for("course.course_detail", course_id=course.id))
    return None


def is_student_enrolled(course: Post) -> bool:
    if current_user.status != "student":
        return False
    q = db.session.execute(
        user_course.select().where(
            (user_course.c.user_id == current_user.id) &
            (user_course.c.course_id == course.id)
        )
    ).first()
    return q is not None

def compute_course_stats_for_student(course: Post, student: User):
    # все уроки курса
    lessons_q = CourseLesson.query.join(CourseModule).filter(
        CourseModule.course_id == course.id
    )

    lecture_ids = [l.id for l in lessons_q.filter(CourseLesson.lesson_type == LessonType.lecture).all()]
    test_ids    = [l.id for l in lessons_q.filter(CourseLesson.lesson_type == LessonType.test).all()]
    lab_ids     = [l.id for l in lessons_q.filter(CourseLesson.lesson_type == LessonType.lab).all()]


    from ..models.course import StudentProgress 

    lectures_total = len(lecture_ids)
    lectures_done = 0
    if lecture_ids:
        lectures_done = StudentProgress.query.filter(
            StudentProgress.student_id == student.id,
            StudentProgress.course_id == course.id,
            StudentProgress.completed.is_(True),
            StudentProgress.lesson_id.in_(lecture_ids)
        ).count()


    tests_total = len(test_ids)
    tests_with_attempts = 0
    test_quality_ratio = 1.0  

    if tests_total > 0:
        best_ratios = []
        for lid in test_ids:
            attempts = TestAttempt.query.filter_by(
                student_id=student.id,
                lesson_id=lid
            ).all()
            if not attempts:
                best_ratios.append(0.0)
                continue
            best = max(a.score / a.total if a.total else 0.0 for a in attempts)
            if best > 0:
                tests_with_attempts += 1
            best_ratios.append(best)
        test_quality_ratio = sum(best_ratios) / len(best_ratios) if best_ratios else 0.0


    labs_total = len(lab_ids)
    labs_solved = 0
    lab_attempts_total = 0

    if lab_ids:

        for lid in lab_ids:
            attempts_q = LabAttempt.query.filter_by(
                student_id=student.id,
                lesson_id=lid
            )
            lab_attempts_total += attempts_q.count()
            solved = attempts_q.filter_by(is_correct=True).first() is not None
            if solved:
                labs_solved += 1


    lectures_ratio = lectures_done / lectures_total if lectures_total else 1.0
    tests_ratio    = test_quality_ratio
    labs_ratio     = labs_solved / labs_total if labs_total else 1.0


    final_score = round((lectures_ratio + tests_ratio + labs_ratio) / 3 * 10, 1)

    return {
        "lectures_done": lectures_done,
        "lectures_total": lectures_total,
        "tests_total": tests_total,
        "tests_ratio": tests_ratio,
        "labs_total": labs_total,
        "labs_solved": labs_solved,
        "lab_attempts_total": lab_attempts_total,
        "final_score": final_score,
    }



@course_bp.route("/<int:course_id>/lesson/<int:lesson_id>/start_lab", methods=["POST"])
@login_required
def start_lab(course_id: int, lesson_id: int):
    """Старт лабораторной: редирект на sandbox.run_lab с проверкой прав."""

    course = Post.query.get_or_404(course_id)
    lesson = CourseLesson.query.get_or_404(lesson_id)

    # проверяем, что урок принадлежит курсу
    if lesson.module.course_id != course.id:
        flash("Неверный урок", "error")
        return redirect(url_for("user.account"))

    if current_user.status == "student":
        if not is_student_enrolled(course):
            flash("У вас нет доступа к этой лабораторной", "error")
            return redirect(url_for("user.account"))
    elif not is_teacher_or_admin(course):
        flash("Вы не ведёте этот курс", "error")
        return redirect(url_for("user.account"))

    # это вообще лаба?
    if lesson.lesson_type != LessonType.lab:
        flash("Этот урок не является лабораторной", "error")
        return redirect(url_for("course.lesson_detail",
                                course_id=course.id,
                                lesson_id=lesson.id))

    # задан ли slug
    if not lesson.sandbox_slug:
        flash("Для этой лабораторной не настроен sandbox slug", "error")
        return redirect(url_for("course.lesson_detail",
                                course_id=course.id,
                                lesson_id=lesson.id))

    # передаём управление блюпринту sandbox, который уже ходит в sandbox-manager
    return redirect(url_for("sandbox.run_lab",
                            course_id=course.id,
                            lesson_id=lesson.id))

@course_bp.route("/courses")
@login_required
def course_list():
    if current_user.status in ("teacher", "admin"):
        courses = Post.query.order_by(Post.created_at.desc()).all()
    else:
        courses = current_user.courses.order_by(Post.created_at.desc()).all()
    return render_template("course/course_list.html", courses=courses)


@course_bp.route("/course/<int:course_id>")
@login_required
def course_detail(course_id: int):
    course = Post.query.get_or_404(course_id)

    if current_user.status == "student" and not is_student_enrolled(course):
        flash("У вас нет доступа к этому курсу", "error")
        return redirect(url_for("user.account"))

    modules = course.modules

    progress_percentage = 0
    completed_lessons = []
    total_lectures = 0
    total_tests = 0


    return render_template(
        "course/course_detail.html",
        course=course,
        modules=modules,
        user=current_user,
        progress_percentage=progress_percentage,
        completed_lessons=completed_lessons,
        total_lectures=total_lectures,
        total_tests=total_tests,
    )

@course_bp.route("/lesson/<int:lesson_id>/progress", methods=["POST"])
@login_required
def mark_lesson_completed(lesson_id):
    """Отметить урок как завершённый (Только для ЛЕКЦИЙ)."""
    lesson = CourseLesson.query.get_or_404(lesson_id)
    course = lesson.module.course

    if current_user.status != "student" or course not in current_user.courses:
        return jsonify({"error": "Нет доступа"}), 403

    progress = StudentProgress.query.filter_by(
        student_id=current_user.id,
        lesson_id=lesson_id
    ).first()

    if not progress:
        progress = StudentProgress(
            student_id=current_user.id,
            course_id=course.id,
            lesson_id=lesson_id,
            completed=True,
            completed_at=datetime.utcnow(),
        )
        db.session.add(progress)
    else:
        progress.completed = True
        progress.completed_at = datetime.utcnow()

    db.session.commit()

    return jsonify({"success": True, "message": "Лекция отмечена как просмотренная"})


@course_bp.route("/course/<int:course_id>/lesson/<int:lesson_id>")
@login_required
def lesson_detail(course_id: int, lesson_id: int):
    course = Post.query.get_or_404(course_id)
    lesson = CourseLesson.query.get_or_404(lesson_id)

    if current_user.status == "student":
        if not is_student_enrolled(course):
            flash("У вас нет доступа к этому уроку", "error")
            return redirect(url_for("user.account"))
    elif not is_teacher_or_admin(course):
        flash("Вы не ведете этот курс", "error")
        return redirect(url_for("user.account"))

    attempts = None
    if current_user.status == "student" and lesson.lesson_type == LessonType.test:
        attempts = TestAttempt.query.filter_by(
            student_id=current_user.id,
            lesson_id=lesson.id
        ).order_by(TestAttempt.created_at.desc()).all()

    return render_template(
        "course/lesson_detail.html",
        course=course,
        lesson=lesson,
        attempts=attempts,
        user=current_user,
    )



@course_bp.route("/course/<int:course_id>/lesson/<int:lesson_id>/edit", methods=["GET", "POST"])
@login_required
def edit_lesson(course_id: int, lesson_id: int):
    course = Post.query.get_or_404(course_id)
    lesson = CourseLesson.query.get_or_404(lesson_id)

    guard = require_teacher_or_admin(course)
    if guard:
        return guard

    if lesson.module.course_id != course.id:
        flash("Неверный урок", "error")
        return redirect(url_for("course.course_detail", course_id=course.id))

    if request.method == "POST":

        title = (request.form.get("title") or "").strip() or lesson.title
        html_content = request.form.get("html_content") or ""
        video_url = request.form.get("video_url") or ""
        sandbox_slug = (request.form.get("sandbox_slug") or "").strip()

        lesson.title = title

        if lesson.lesson_type == LessonType.lecture:
            lesson.html_content = html_content
            lesson.video_url = video_url

        elif lesson.lesson_type == LessonType.lab:
            lesson.html_content = html_content
            lesson.sandbox_slug = sandbox_slug

        if lesson.lesson_type == LessonType.test and lesson.test:
            test_title = (request.form.get("test_title") or "").strip() or title
            test_desc = request.form.get("test_description") or ""
            lesson.test.title = test_title
            lesson.test.description = test_desc

            lesson.title = test_title

        db.session.commit()
        flash("Урок обновлён", "success")
        return redirect(url_for("course.course_detail", course_id=course.id))

    return render_template(
        "course/lesson_edit.html",
        course=course,
        lesson=lesson,
        LessonType=LessonType,
        user=current_user,
    )



@course_bp.route("/course/<int:course_id>/admin", methods=["GET", "POST"])
@login_required
def course_admin(course_id: int):
    course = Post.query.get_or_404(course_id)

    guard = require_teacher_or_admin(course)
    if guard:
        return guard

    if request.method == "POST":
        action = request.form.get("action") or ""


        if action == "add_module":
            title = (request.form.get("title") or "").strip() or "Новый модуль"
            description = (request.form.get("description") or "").strip()
            next_order = (course.modules[-1].order + 1) if course.modules else 1

            m = CourseModule(course_id=course.id, title=title, description=description, order=next_order)
            db.session.add(m)
            db.session.commit()
            flash("Модуль добавлен", "success")
            return redirect(url_for("course.course_admin", course_id=course.id))

        if action == "add_lecture":
            module_id = int(request.form.get("module_id"))
            module = CourseModule.query.get_or_404(module_id)
            if module.course_id != course.id:
                flash("Неверный модуль", "error")
                return redirect(url_for("course.course_admin", course_id=course.id))

            title = (request.form.get("title") or "").strip() or "Новая лекция"
            html_content = request.form.get("html_content") or ""
            video_url = request.form.get("video_url") or ""
            next_order = module.lessons.count() + 1

            lesson = CourseLesson(
                module_id=module.id,
                title=title,
                order=next_order,
                lesson_type=LessonType.lecture,
                html_content=html_content,
                video_url=video_url,
            )
            db.session.add(lesson)
            db.session.commit()
            flash("Лекция добавлена", "success")
            return redirect(url_for("course.course_admin", course_id=course.id))


        if action == "add_test":
            module_id = int(request.form.get("module_id"))
            module = CourseModule.query.get_or_404(module_id)
            if module.course_id != course.id:
                flash("Неверный модуль", "error")
                return redirect(url_for("course.course_admin", course_id=course.id))

            title = (request.form.get("title") or "").strip() or "Новый тест"
            next_order = module.lessons.count() + 1

            lesson = CourseLesson(
                module_id=module.id,
                title=title,
                order=next_order,
                lesson_type=LessonType.test,
            )
            test = CourseTest(lesson=lesson, title=title, description="Тест по материалам урока")
            db.session.add_all([lesson, test])
            db.session.commit()
            flash("Тест добавлен", "success")
            return redirect(url_for("course.course_admin", course_id=course.id))


        if action == "add_lab":
            module_id = int(request.form.get("module_id"))
            module = CourseModule.query.get_or_404(module_id)
            if module.course_id != course.id:
                flash("Неверный модуль", "error")
                return redirect(url_for("course.course_admin", course_id=course.id))

            title = (request.form.get("title") or "").strip() or "Новая лабораторная"
            sandbox_slug = (request.form.get("sandbox_slug") or "").strip()
            next_order = module.lessons.count() + 1

            lesson = CourseLesson(
                module_id=module.id,
                title=title,
                order=next_order,
                lesson_type=LessonType.lab,
                sandbox_slug=sandbox_slug,
            )
            db.session.add(lesson)
            db.session.commit()
            flash("Лабораторная добавлена", "success")
            return redirect(url_for("course.course_admin", course_id=course.id))


        if action == "delete_module":
            module_id = int(request.form.get("module_id"))
            module = CourseModule.query.get_or_404(module_id)
            if module.course_id != course.id:
                flash("Неверный модуль", "error")
                return redirect(url_for("course.course_admin", course_id=course.id))
            db.session.delete(module)
            db.session.commit()
            flash("Модуль удалён", "success")
            return redirect(url_for("course.course_admin", course_id=course.id))


        if action == "delete_lesson":
            lesson_id = int(request.form.get("lesson_id"))
            lesson = CourseLesson.query.get_or_404(lesson_id)
            if lesson.module.course_id != course.id:
                flash("Неверный урок", "error")
                return redirect(url_for("course.course_admin", course_id=course.id))
            db.session.delete(lesson)
            db.session.commit()
            flash("Урок удалён", "success")
            return redirect(url_for("course.course_admin", course_id=course.id))


        if action == "add_question":
            test_id = int(request.form.get("test_id"))
            question_text = (request.form.get("question") or "").strip()
            options: List[str] = request.form.getlist("options[]")
            correct_idx = int(request.form.get("correct_option") or "-1")

            test = CourseTest.query.get_or_404(test_id)
            lesson = test.lesson
            if lesson.module.course_id != course.id:
                flash("Неверный тест", "error")
                return redirect(url_for("course.course_admin", course_id=course.id))

            q_order = len(test.questions) + 1
            q = TestQuestion(test_id=test.id, order=q_order, question=question_text)
            db.session.add(q)
            db.session.flush()

            for i, opt_text in enumerate(options):
                text = (opt_text or "").strip()
                if not text:
                    continue
                o = TestOption(
                    question_id=q.id,
                    order=i + 1,
                    option_text=text,
                    is_correct=(i == correct_idx)
                )
                db.session.add(o)

            db.session.commit()
            flash("Вопрос добавлен", "success")
            return redirect(url_for("course.course_detail", course_id=course.id))

    modules = course.modules
    return render_template("course/course_detail.html", course=course, modules=modules)




@course_bp.route("/course/<int:course_id>/lesson/<int:lesson_id>/start_test", methods=["POST"])
@login_required
def start_test(course_id: int, lesson_id: int):
    course = Post.query.get_or_404(course_id)
    lesson = CourseLesson.query.get_or_404(lesson_id)

    if lesson.lesson_type != LessonType.test or lesson.module.course_id != course.id:
        flash("Неверный тест", "error")
        return redirect(url_for("course.lesson_detail", course_id=course.id, lesson_id=lesson.id))

    if current_user.status != "student" or not is_student_enrolled(course):
        flash("Нет доступа", "error")
        return redirect(url_for("course.lesson_detail", course_id=course.id, lesson_id=lesson.id))

    return redirect(url_for("course.lesson_detail", course_id=course.id, lesson_id=lesson.id))


@course_bp.route("/course/<int:course_id>/lesson/<int:lesson_id>/submit_test", methods=["POST"])
@login_required
def submit_test(course_id: int, lesson_id: int):
    course = Post.query.get_or_404(course_id)
    lesson = CourseLesson.query.get_or_404(lesson_id)

    if lesson.lesson_type != LessonType.test or lesson.module.course_id != course.id:
        flash("Неверный тест", "error")
        return redirect(url_for("course.lesson_detail", course_id=course.id, lesson_id=lesson.id))

    if current_user.status != "student" or not is_student_enrolled(course):
        flash("Нет доступа", "error")
        return redirect(url_for("course.lesson_detail", course_id=course.id, lesson_id=lesson.id))

    test = lesson.test
    if not test:
        flash("Тест не настроен", "error")
        return redirect(url_for("course.lesson_detail", course_id=course.id, lesson_id=lesson.id))

    correct = 0
    total = len(test.questions)
    for q in test.questions:
        field = f"q_{q.id}"
        opt_id = request.form.get(field)
        if not opt_id:
            continue
        try:
            opt_id = int(opt_id)
        except ValueError:
            continue
        opt = TestOption.query.get(opt_id)
        if opt and opt.question_id == q.id and opt.is_correct:
            correct += 1

    attempt = TestAttempt(student_id=current_user.id, lesson_id=lesson.id, score=correct, total=total)
    db.session.add(attempt)
    db.session.commit()

    flash(f"Тест отправлен. Результат: {correct}/{total}", "success")
    return redirect(url_for("course.lesson_detail", course_id=course.id, lesson_id=lesson.id))




@course_bp.route("/course/<int:course_id>/lesson/<int:lesson_id>/submit_flag", methods=["POST"])
@login_required
def submit_flag(course_id: int, lesson_id: int):
    course = Post.query.get_or_404(course_id)
    lesson = CourseLesson.query.get_or_404(lesson_id)

    if lesson.lesson_type != LessonType.lab:
        abort(400)

    raw_flag = request.form.get("flag", "")
    submitted_flag = raw_flag.strip()

    if not submitted_flag:
        flash("Флаг не может быть пустым", "error")
        return redirect(url_for("course.lesson_detail", course_id=course.id, lesson_id=lesson.id))


    lab_def = None
    if lesson.sandbox_slug:
        lab_def = LabDefinition.query.filter_by(slug=lesson.sandbox_slug).first()

    if not lab_def:
        flash("Для этой лабораторной не задан правильный флаг (обратитесь к преподавателю).", "error")
        return redirect(url_for("course.lesson_detail", course_id=course.id, lesson_id=lesson.id))

    expected_flag = (lab_def.correct_flag or "").strip()

    is_correct = submitted_flag == expected_flag

    attempt = LabAttempt(
        student_id=current_user.id,
        lesson_id=lesson.id,
        submitted_flag=submitted_flag,
        is_correct=is_correct,
        created_at=datetime.utcnow()
    )
    db.session.add(attempt)

    if is_correct:
  
        progress = StudentProgress.query.filter_by(
            student_id=current_user.id,
            course_id=course.id,
            lesson_id=lesson.id
        ).first()

        if not progress:
            progress = StudentProgress(
                student_id=current_user.id,
                course_id=course.id,
                lesson_id=lesson.id,
            )
            db.session.add(progress)

        progress.completed = True
        progress.completed_at = datetime.utcnow()
        progress.score = 1

        db.session.commit()
        flash("Флаг принят, лабораторная засчитана ✅", "success")

    else:
        db.session.commit()
        wrong_attempts = LabAttempt.query.filter_by(
            student_id=current_user.id,
            lesson_id=lesson.id,
            is_correct=False
        ).count()
        flash(f"Флаг неверный. Неверных попыток: {wrong_attempts}", "error")

    return redirect(url_for("course.lesson_detail", course_id=course.id, lesson_id=lesson.id))



@course_bp.route("/course/upload_image", methods=["POST"])
@login_required
def upload_image():
    if current_user.status not in ("teacher", "admin"):
        return jsonify({"error": "Нет прав"}), 403

    f = request.files.get("image")
    if not f or not f.filename:
        return jsonify({"error": "Файл не получен"}), 400

    filename = f.filename.strip().replace(" ", "_")
    save_path = os.path.join(UPLOAD_DIR, filename)
    base, ext = os.path.splitext(filename)
    i = 1
    while os.path.exists(save_path):
        filename = f"{base}_{i}{ext}"
        save_path = os.path.join(UPLOAD_DIR, filename)
        i += 1
    f.save(save_path)

    rel_url = url_for("static", filename=f"uploads/courses/{filename}")
    return jsonify({"url": rel_url})


@course_bp.route("/course/<int:course_id>/students")
@login_required
def course_students(course_id: int):
    course = Post.query.get_or_404(course_id)

    if not is_teacher_or_admin(course):
        flash("Доступ запрещён", "error")
        return redirect(url_for("user.account"))

  
    students = course.students  

    stats_rows = []
    for s in students:
        stats = compute_course_stats_for_student(course, s)
        stats_rows.append({
            "student": s,
            **stats
        })

    return render_template(
        "course/course_students.html",
        course=course,
        rows=stats_rows,
    )

