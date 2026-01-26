// Валидация формы входа
document.querySelector('.auth__form').addEventListener('submit', function(e) {
    const login = document.getElementById('login').value;
    const password = document.getElementById('password').value;
    
    if (!login || !password) {
        e.preventDefault();
        alert('Пожалуйста, заполните все поля!');
        return;
    }
    
    // Здесь можно добавить AJAX-отправку формы
});