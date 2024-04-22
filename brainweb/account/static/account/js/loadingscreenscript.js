document.addEventListener("DOMContentLoaded", function() {
    const dynamicContent = document.getElementById("dynamic-content");
    const fileUpload = document.getElementById("file-upload");
    const fileName = document.getElementById("file-name");

    fileUpload.addEventListener("change", function() {
        const file = this.files[0];
        if (file) {
            fileName.textContent = file.name;

            // Burada dosya işleme işlemlerini gerçekleştirin
            // Örneğin, dosyayı yükleyebilir veya içeriğini görüntüleyebilirsiniz
        } else {
            fileName.textContent = "";
        }
    });

    document.querySelectorAll('.pipeline-button').forEach(button => {
        button.addEventListener('click', () => {
            // Tıklanan butonun data-pipeline attribute değerini al
            const pipeline = button.getAttribute('data-pipeline');
            // description elementini seç
            const description = document.getElementById('description');
            // pipeline'e göre description içeriğini güncelle
            switch (pipeline) {
                case 'brain':
                    description.innerText = 'Beyin ile ilgili açıklama metni buraya gelecek';
                    break;
                case 'cerebellum':
                    description.innerText = 'Beyincik ile ilgili açıklama metni buraya gelecek';
                    break;
                case 'hippocampus':
                    description.innerText = 'Hipokampus ile ilgili açıklama metni buraya gelecek';
                    break;
                case 'lesions':
                    description.innerText = 'Lezyonlar ile ilgili açıklama metni buraya gelecek';
                    break;
                case 'nuclei':
                    description.innerText = 'Çekirdekler ile ilgili açıklama metni buraya gelecek';
                    break;
                default:
                    description.innerText = 'Açıklama metni buraya gelecek';
                    break;
            }
            // Dinamik içeriği göster
            dynamicContent.classList.remove('hidden');
        });
    });
});
