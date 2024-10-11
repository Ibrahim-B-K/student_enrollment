document.addEventListener("DOMContentLoaded", function() {
    const formContainers = document.querySelectorAll('.form-animation');
    formContainers.forEach((form) => {
        form.style.opacity = 1;  // Ensure form is visible after page load
    });

    // Example of simple validation on forms
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            let valid = true;
            const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
            inputs.forEach(input => {
                if (!input.value) {
                    valid = false;
                    input.style.borderColor = 'red';
                    input.addEventListener('input', () => {
                        input.style.borderColor = '#3498db';
                    });
                }
            });
            if (!valid) {
                e.preventDefault(); // Prevent form submission if invalid
                alert("Please fill out all required fields.");
            }
        });
    });
});
