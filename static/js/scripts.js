// Funcionalidad para el textarea de publicaciones
document.addEventListener('DOMContentLoaded', function() {
    // Autoajustar altura del textarea al escribir
    const textareas = document.querySelectorAll('textarea');
    textareas.forEach(textarea => {
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });
    });
    
    // Confirmación antes de acciones importantes
    const actionButtons = document.querySelectorAll('[data-confirm]');
    actionButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm(this.dataset.confirm)) {
                e.preventDefault();
            }
        });
    });
    
    // Manejo de likes con AJAX (opcional)
    const likeButtons = document.querySelectorAll('.like-btn');
    likeButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const url = this.href;
            
            fetch(url, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const icon = this.querySelector('i');
                    const count = this.querySelector('.like-count');
                    
                    if (data.action === 'like') {
                        icon.classList.remove('bi-heart');
                        icon.classList.add('bi-heart-fill');
                        this.classList.remove('btn-outline-primary');
                        this.classList.add('btn-primary');
                    } else {
                        icon.classList.remove('bi-heart-fill');
                        icon.classList.add('bi-heart');
                        this.classList.remove('btn-primary');
                        this.classList.add('btn-outline-primary');
                    }
                    
                    count.textContent = data.likes;
                }
            })
            .catch(error => console.error('Error:', error));
        });
    });
});