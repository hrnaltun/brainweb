document.addEventListener("DOMContentLoaded", function() {
    const dynamicContent = document.getElementById("dynamic-content");
    const descriptionText = document.getElementById("description");
    const fileUpload = document.getElementById("file-upload");
    const fileName = document.getElementById("file-name");

    document.querySelectorAll('.pipeline-button').forEach(button => {
        button.addEventListener('click', () => {
            const servisId = button.getAttribute('data-service-id');  // Düğmenin servis kimliği
            const url = `/service/${servisId}/`;  // URL

            // Servis detayını Fetch ile alın
            fetch(url)
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Servis bilgisi alınamadı.');
                    }
                    return response.json();
                })
                .then(data => {
                    dynamicContent.classList.remove('hidden');  // Paneli görünür yapın
                    descriptionText.textContent = data.açıklama || 'Açıklama mevcut değil.';  // Açıklamayı güncelleyin

                })
        });
    });
});

