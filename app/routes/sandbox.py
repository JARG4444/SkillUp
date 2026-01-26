from flask import Blueprint, current_app, render_template, request, redirect, url_for, flash
from flask_login import current_user
import requests
from ..models.post import Post  
from ..extensions import db

sandbox_bp = Blueprint("sandbox", __name__, url_prefix="/sandbox")

# Старт лабы для конкретного урока
@sandbox_bp.route("/run/<int:course_id>/<int:lesson_id>", methods=["GET"])
def run_lab(course_id, lesson_id):
    from ..models.course import CourseLesson, LessonType

    lesson = CourseLesson.query.get_or_404(lesson_id)
    if lesson.lesson_type != LessonType.lab:
        flash("Этот урок не является лабораторной", "warning")
        return redirect(url_for("course.course_detail", course_id=course_id))

    lab_slug = lesson.sandbox_slug or "fakebank"

    base = current_app.config["SANDBOX_BASE"]
    api_key = current_app.config["SANDBOX_API_KEY"]

    try:
        r = requests.post(
            f"{base}/api/v1/sessions",
            json={"lab_slug": lab_slug, "user_id": getattr(current_user, "id", None)},
            headers={"X-Api-Key": api_key},
            timeout=10,
        )
        r.raise_for_status()
    except Exception as e:
        current_app.logger.exception("sandbox create session failed")
        flash(f"Не удалось запустить песочницу: {e}", "danger")
        return redirect(url_for("course.course_detail", course_id=course_id))

    data = r.json()
    iframe_src = data["client_url"]

    return render_template(
        "course/lab_run.html",
        course_id=course_id,
        lesson=lesson,
        iframe_src=iframe_src,
    )


# Отправка флага из курса 
@sandbox_bp.route("/verify/<int:course_id>/<int:lesson_id>", methods=["POST"])
def verify_flag(course_id, lesson_id):
    from ..models.course import CourseLesson
    lesson = CourseLesson.query.get_or_404(lesson_id)
    lab_slug = lesson.sandbox_slug or "fakebank"

    flag = request.form.get("flag", "").strip()
    if not flag:
        flash("Введите флаг", "warning")
        return redirect(url_for("sandbox.run_lab", course_id=course_id, lesson_id=lesson_id))

    base = current_app.config["SANDBOX_BASE"]
    api_key = current_app.config["SANDBOX_API_KEY"]

    try:
        r = requests.post(
            f"{base}/api/v1/verify",
            json={"lab_slug": lab_slug, "flag": flag, "user_id": getattr(getattr(request, 'user', None), 'id', None)},
            headers={"X-Api-Key": api_key},
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        current_app.logger.exception("sandbox verify failed")
        flash(f"Проверка не удалась: {e}", "danger")
        return redirect(url_for("sandbox.run_lab", course_id=course_id, lesson_id=lesson_id))

    if data.get("ok"):
        flash("Флаг принят. Задание зачтено.", "success")
    else:
        flash(data.get("message", "Флаг неверный"), "danger")

    return redirect(url_for("sandbox.run_lab", course_id=course_id, lesson_id=lesson_id))
