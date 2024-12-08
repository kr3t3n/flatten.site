document.addEventListener('DOMContentLoaded', function() {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const uploadForm = document.getElementById('uploadForm');
    const fileInfo = document.getElementById('fileInfo');
    const progressContainer = document.getElementById('progressContainer');
    const progressBar = document.getElementById('progressBar');
    const alertContainer = document.getElementById('alertContainer');

    // Drag and drop handlers
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => {
            dropZone.classList.add('drop-zone-active');
        });
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => {
            dropZone.classList.remove('drop-zone-active');
        });
    });

    dropZone.addEventListener('drop', handleDrop);
    dropZone.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', handleFileSelect);

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFiles(files);
    }

    function handleFileSelect(e) {
        const files = e.target.files;
        handleFiles(files);
    }

    function handleFiles(files) {
        if (files.length > 0) {
            const file = files[0];
            if (file.type !== 'application/zip' && !file.name.endsWith('.zip')) {
                showAlert('Please select a ZIP file', 'danger');
                return;
            }
            if (file.size > 50 * 1024 * 1024) { // 50MB
                showAlert('File size exceeds 50MB limit', 'danger');
                return;
            }
            fileInfo.querySelector('.selected-file-name').textContent = file.name;
            fileInfo.style.display = 'block';
        }
    }

    uploadForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        const file = fileInput.files[0];
        if (!file) {
            showAlert('Please select a file', 'danger');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        progressContainer.style.display = 'block';
        progressBar.style.width = '0%';

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                progressBar.style.width = '100%';
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'flattened.zip';
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                showAlert('File processed successfully!', 'success');
            } else {
                const data = await response.json();
                showAlert(data.error || 'Error processing file', 'danger');
            }
        } catch (error) {
            showAlert('Error uploading file', 'danger');
        } finally {
            progressContainer.style.display = 'none';
            fileInfo.style.display = 'none';
            fileInput.value = '';
        }
    });

    function showAlert(message, type) {
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show`;
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        alertContainer.innerHTML = '';
        alertContainer.appendChild(alert);

        setTimeout(() => {
            alert.remove();
        }, 5000);
    }
});
