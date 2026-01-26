// Валидация формы регистрации
document.querySelector('.auth__form').addEventListener('submit', function(e) {
    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirm_password').value;
    const terms = document.getElementById('terms').checked;
    
    if (password !== confirmPassword) {
        e.preventDefault();
        alert('Пароли не совпадают!');
        return;
    }
    
    if (!terms) {
        e.preventDefault();
        alert('Необходимо согласиться с условиями!');
        return;
    }
    
    // Здесь можно добавить AJAX-отправку формы
});