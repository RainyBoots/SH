
function initializeFavoriteButtons(container) {
    const favoriteContainers = container.querySelectorAll('.favorite-container');

    favoriteContainers.forEach(container => {
        const favoriteBtn = container.querySelector('.favorite-btn');
        const scoreId = container.dataset.scoreId;

        function animateHeartPulse() {
            favoriteBtn.classList.add('favorite-animate');
            setTimeout(() => {
                favoriteBtn.classList.remove('favorite-animate');
            }, 300);
        }

        favoriteBtn.addEventListener('click', async function() {
            try {
                const response = await fetch(`/scores/${scoreId}/toggle-favorite/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': '{{ csrf_token }}',
                        'Content-Type': 'application/json',
                    }
                });

                if (!response.ok) {
                    throw new Error('Ошибка сети');
                }

                const data = await response.json();
                const icon = favoriteBtn.querySelector('i');
                const statusText = container.querySelector('.favorite-status');

                icon.className = data.is_favorite ? 'fas fa-heart text-danger' : 'far fa-heart';
                statusText.textContent = data.is_favorite ? 'В избранном' : 'Добавить в избранное';


                animateHeartPulse();


                showNotification(data.message);

            } catch (error) {
                console.error('Ошибка:', error);
                showNotification('Произошла ошибка. Попробуйте позже.', 'error');
            }
        });
    });
}


function showNotification(message, type = 'success') {
    console.log(message);
}