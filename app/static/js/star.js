document.querySelectorAll('.rating-stars input').forEach(star => {
    star.addEventListener('change', function() {
        const ratingText = document.getElementById('rating-text');
        const texts = ['Ужасно', 'Плохо', 'Нормально', 'Хорошо', 'Отлично'];
        ratingText.textContent = texts[this.value - 1];
    });
});