function openAssignModal(teacherId) {
    document.getElementById('teacherId').value = teacherId;
    document.getElementById('assignCourseModal').style.display = 'block';
}

function closeModal() {
    document.getElementById('assignCourseModal').style.display = 'none';
}

// Закрытие модального окна при клике вне его
window.onclick = function(event) {
    const modal = document.getElementById('assignCourseModal');
    if (event.target === modal) {
        closeModal();
    }
}

// Закрытие модального окна по клавише ESC
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        closeModal();
    }
});

// Обработка закрытия по крестику
document.querySelector('.close').addEventListener('click', closeModal);