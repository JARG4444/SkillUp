// Мобильное меню
const burger = document.getElementById('burger');
const nav = document.querySelector('.nav');
const headerAuth = document.querySelector('.header__auth');

burger.addEventListener('click', () => {
    burger.classList.toggle('active');
    nav.classList.toggle('active');
    headerAuth.classList.toggle('active');
});

// Плавный скролл для якорей
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        document.querySelector(this.getAttribute('href')).scrollIntoView({
            behavior: 'smooth'
        });
    });
});

// Слайдер отзывов (простая реализация)
let currentReview = 0;
const reviews = document.querySelectorAll('.review__card');

function showReview(index) {
    reviews.forEach((review, i) => {
        review.style.display = i === index ? 'flex' : 'none';
    });
}

// Автопрокрутка отзывов (опционально)
setInterval(() => {
    currentReview = (currentReview + 1) % reviews.length;
    showReview(currentReview);
}, 5000);

showReview(0);