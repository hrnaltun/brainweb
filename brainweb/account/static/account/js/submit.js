document.addEventListener("DOMContentLoaded", function() {
    const dynamicContent = document.getElementById("dynamic-content");
    const descriptionText = document.getElementById("description");
    const fileUpload = document.getElementById("file-upload");
    const fileName = document.getElementById("file-name");
    const serviceForm = document.getElementById("service-form");

    // Servis ID'sini form input alanına ekleyen JavaScript fonksiyonu
    function setServiceId(servisId) {
        document.getElementById("servis_id").value = servisId;
    }

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
                    // Servis ID'sini form input alanına ekleyelim
                    setServiceId(servisId);
                    
                    // Açıklama metnini güncelleyelim
                    descriptionText.textContent = data.açıklama || 'Açıklama mevcut değil.';  

                    // Dynamic content panelini gösterelim
                    dynamicContent.classList.remove('hidden');
                })
                .catch(error => {
                    console.error('Error fetching service data:', error);
                    descriptionText.textContent = 'Servis bilgisi alınamadı.';
                });
        });
    });

    // Dosya seçildiğinde dosya adını göster
    fileUpload.addEventListener('change', function() {
        if (fileUpload.files.length > 0) {
            fileName.textContent = fileUpload.files[0].name;  // Seçilen dosyanın adını göster
        }
    });
});
