document.querySelectorAll('.btn-delete').forEach(btn => {
    btn.addEventListener('click', function(e) {
        if (!confirm('Вы уверены, что хотите удалить этого преподавателя?')) {
            e.preventDefault();
        }
    });
});