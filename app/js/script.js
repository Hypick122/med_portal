window.onload = function() {
    const login = document.getElementById('login');
    const password = document.getElementById('password');
    const submit = document.getElementById('submit');

    if(password) {
        password.oninput = function() {
            if(submit) {
                if(password.value.match(/^.*(?=.{8,})(?=.*[a-zA-Z])(?=.*\d)(?=.*[!#$%&? "]).*$/)) {
                    submit.setAttribute('disabled', '');
                } else {
                    submit.setAttribute('disabled', 'disabled');
                }
            }
        }
    }
}