document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('updateScoreForm');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const errorMessages = document.getElementById('errorMessages');

    function validateFile(file) {
        const allowedExtensions = /(\.musicxml|\.xml)$/i; 
        return allowedExtensions.exec(file.name) !== null; 
    }

    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const fileInput = form.querySelector('input[type="file"]'); 
        const file = fileInput.files[0]; 

    
        if (file && !validateFile(file)) {
            errorMessages.textContent = 'Недопустимый формат файла. Пожалуйста, загружайте файлы .musicxml или .xml.';
            errorMessages.style.display = 'block';
            return; 
        }

        const formData = new FormData(form); 
        

        loadingIndicator.style.display = 'block';
        errorMessages.style.display = 'none';

        fetch(form.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                window.location.href = data.redirect_url; 
            } else {
                throw new Error(data.message);
            }
        })
        .catch(error => {
            errorMessages.textContent = error.message;
            errorMessages.style.display = 'block';
        })
        .finally(() => {
            loadingIndicator.style.display = 'none'; 
        });
    });
});