document.addEventListener('DOMContentLoaded', function() {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const browseButton = document.getElementById('browseButton');
    const fileInfo = document.getElementById('fileInfo');
    const fileName = document.getElementById('fileName');
    const processButton = document.getElementById('processButton');
    const progressContainer = document.getElementById('progressContainer');
    const progressBar = progressContainer.querySelector('.progress-bar');
    const errorContainer = document.getElementById('errorContainer');
    const errorMessage = document.getElementById('errorMessage');

    // File selection via browse button
    browseButton.addEventListener('click', () => fileInput.click());

    // File selection handler
    fileInput.addEventListener('change', handleFileSelect);

    // Drag and drop handlers
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        handleFiles(e.dataTransfer.files);
    });

    // Process button handler
    processButton.addEventListener('click', processFile);

    function handleFileSelect(e) {
        handleFiles(e.target.files);
    }

    function handleFiles(files) {
        const file = files[0];
        if (!file) return;

        if (!file.name.toLowerCase().endsWith('.zip')) {
            showError('Please select a ZIP file');
            return;
        }

        if (file.size > 50 * 1024 * 1024) {
            showError('File size exceeds 50MB limit');
            return;
        }

        fileName.textContent = file.name;
        fileInfo.classList.remove('d-none');
        errorContainer.classList.add('d-none');
    }

    function processFile() {
        const file = fileInput.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append('file', file);

        // Show progress
        progressContainer.classList.remove('d-none');
        progressBar.style.width = '0%';
        
        // Simulate progress (actual progress not available for small files)
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += 5;
            if (progress <= 90) {
                progressBar.style.width = progress + '%';
            }
        }, 100);

        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            clearInterval(progressInterval);
            progressBar.style.width = '100%';
            
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.error || 'Processing failed');
                });
            }
            
            return response.blob();
        })
        .then(blob => {
            // Create download link
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'flattened.zip';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

            // Reset form
            setTimeout(() => {
                progressContainer.classList.add('d-none');
                fileInfo.classList.add('d-none');
                fileInput.value = '';
            }, 1000);
        })
        .catch(error => {
            clearInterval(progressInterval);
            progressContainer.classList.add('d-none');
            showError(error.message);
        });
    }

    function showError(message) {
        errorMessage.textContent = message;
        errorContainer.classList.remove('d-none');
    }
});
