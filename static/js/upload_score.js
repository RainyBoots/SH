// static/js/upload_score.js

function initScoreUpload(uploadUrl) {
    const form = document.getElementById('scoreUploadForm');
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('scoreUpload');
    const previewSection = document.getElementById('previewSection');
    const errorMessages = document.getElementById('errorMessages'); // Элемент для ошибок

    // Drag and drop функционал
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('border-primary');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('border-primary');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('border-primary');
        if (e.dataTransfer.files.length) {
            fileInput.files = e.dataTransfer.files;
            handleFileSelection();
        }
    });

    fileInput.addEventListener('change', handleFileSelection);

    form.addEventListener('submit', function (e) {
        e.preventDefault(); // Предотвращаем стандартное поведение формы
        handleFileSelection(); // Обрабатываем файл
    });

    function handleFileSelection() {
        if (fileInput.files.length) {
            const file = fileInput.files[0];
            const allowedExtensions = /(\.musicxml|\.xml)$/i; // Допустимые расширения

            // Проверяем формат файла
            if (!allowedExtensions.exec(file.name)) {
                errorMessages.textContent = 'Недопустимый формат файла. Пожалуйста, загружайте файлы .musicxml или .xml.';
                errorMessages.style.display = 'block';
                return;
            } else {
                errorMessages.style.display = 'none'; // Скрываем ошибки
            }

            const formData = new FormData(form); // Создание FormData

            fetch(uploadUrl, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                }
            })
            .then(response => {
                return response.json(); // Параметры ответа в формате JSON
            })
            .then(data => {
                if (data.error) {
                    errorMessages.textContent = data.error; // Отображаем ошибку
                    errorMessages.style.display = 'block';
                } else {
                    // Заполняем поля предпросмотра
                    document.querySelector('[name=envelope_title]').value = data.envelope_title;
                    document.querySelector('[name=key]').value = data.key;
                    document.querySelector('[name=part_count]').value = data.part_count;
                    document.querySelector('[name=page_count]').value = data.page_count;
                    document.querySelector('[name=measures]').value = data.measures;
                    
                    previewSection.style.display = 'block'; // Показать предпросмотр
                }
            })
            .catch(error => {
                errorMessages.textContent = 'Произошла ошибка при загрузке файла.';
                errorMessages.style.display = 'block';
            });
        }
    }
}