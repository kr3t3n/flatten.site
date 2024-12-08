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
    
    // New elements for text output
    const delimiterSection = document.getElementById('delimiterSection');
    const delimiterInput = document.getElementById('delimiter');
    const outputFormatRadios = document.getElementsByName('outputFormat');

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

        // First, list the files in the ZIP
        const formData = new FormData();
        formData.append('file', file);

        fetch('/list-files', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            
            // Show file selection interface
            fileName.textContent = file.name;
            fileInfo.classList.remove('d-none');
            errorContainer.classList.add('d-none');
            
            // Create and show file selection list
            const fileList = document.createElement('div');
            fileList.className = 'mt-3';
            fileList.innerHTML = `
                <button type="button" class="btn btn-primary mb-3" onclick="processFile()">
                    <i class="bi bi-gear me-2"></i>Process Selected Files
                </button>
                
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <h5 class="mb-0">Select Files to Include</h5>
                    <div class="btn-group" role="group">
                        <button type="button" class="btn btn-sm btn-outline-secondary" id="selectAll">Select All</button>
                        <button type="button" class="btn btn-sm btn-outline-secondary" id="deselectAll">Deselect All</button>
                    </div>
                </div>
                
                <div class="list-group mb-3">
                    ${data.files.map(file => `
                        <label class="list-group-item">
                            <input class="form-check-input me-2" type="checkbox" value="${file.name}" checked>
                            <small class="text-muted d-block">Original: ${file.name}</small>
                            <small class="text-muted d-block">Flattened: ${file.flattened_name}</small>
                            <small class="text-muted d-block">Size: ${formatFileSize(file.size)}</small>
                        </label>
                    `).join('')}
                </div>
                
                <button type="button" class="btn btn-primary" onclick="processFile()">
                    <i class="bi bi-gear me-2"></i>Process Selected Files
                </button>
            `;
            
            // Insert file list before process button
            const processButtonContainer = document.getElementById('fileInfo');
            const processButton = document.getElementById('processButton');
            if (processButtonContainer && processButton) {
                processButtonContainer.insertBefore(fileList, processButton);
            }
            
            // Add select/deselect all functionality
            document.getElementById('selectAll').addEventListener('click', () => {
                fileList.querySelectorAll('input[type="checkbox"]').forEach(cb => cb.checked = true);
            });
            
            document.getElementById('deselectAll').addEventListener('click', () => {
                fileList.querySelectorAll('input[type="checkbox"]').forEach(cb => cb.checked = false);
            });
        })
        .catch(error => {
            showError(error.message);
        });
    }

    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    // Handle output format change
    if (outputFormatRadios && delimiterSection) {
        outputFormatRadios.forEach(radio => {
            radio.addEventListener('change', function() {
                delimiterSection.classList.toggle('d-none', this.value === 'zip');
            });
        });
    }

    // Handle delimiter suggestions
    if (delimiterInput) {
        document.querySelectorAll('[data-delimiter]').forEach(item => {
            item.addEventListener('click', function(e) {
                e.preventDefault();
                delimiterInput.value = this.dataset.delimiter;
            });
        });
    }

    function processFile() {
        const file = fileInput.files[0];
        if (!file) return;

        // Get selected files
        const selectedFiles = Array.from(document.querySelectorAll('.list-group-item input[type="checkbox"]:checked'))
            .map(cb => cb.value);
        
        if (selectedFiles.length === 0) {
            showError('Please select at least one file to process');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);
        
        // Add output format and delimiter if text output is selected
        const outputFormat = document.querySelector('input[name="outputFormat"]:checked').value;
        formData.append('output_format', outputFormat);
        if (outputFormat === 'text') {
            formData.append('delimiter', delimiterInput.value || '^^');
        }
        
        // Add selected files
        selectedFiles.forEach(filename => {
            formData.append('selected_files[]', filename);
        });

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
            
            return outputFormat === 'zip' ? response.blob() : response.text();
        })
        .then(content => {
            // Create download link
            const a = document.createElement('a');
            const outputFormat = document.querySelector('input[name="outputFormat"]:checked').value;
            
            if (outputFormat === 'zip') {
                const url = window.URL.createObjectURL(content);
                a.href = url;
                a.download = 'flattened.zip';
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
            } else {
                const blob = new Blob([content], { type: 'text/plain' });
                const url = window.URL.createObjectURL(blob);
                a.href = url;
                a.download = 'flattened.txt';
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
            }
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
