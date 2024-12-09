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
            
            // Create file tree structure
            const createFileTree = (files) => {
                const tree = {};
                
                files.forEach(file => {
                    const parts = file.name.split('/');
                    let current = tree;
                    
                    parts.forEach((part, index) => {
                        if (index === parts.length - 1) {
                            // It's a file
                            current[part] = {
                                type: 'file',
                                ...file
                            };
                        } else {
                            // It's a directory
                            current[part] = current[part] || {
                                type: 'directory',
                                children: {}
                            };
                            current = current[part].children;
                        }
                    });
                });
                
                return tree;
            };
            
            // Render file tree HTML
            const renderFileTree = (tree, level = 0) => {
                const items = Object.entries(tree).map(([name, node]) => {
                    if (node.type === 'file') {
                        const tooltipContent = `
                            Original: ${node.name}
                            Flattened: ${node.flattened_name}
                            Size: ${formatFileSize(node.size)}
                        `.replace(/\n\s+/g, '\n');
                        
                        return `
                            <li class="file-tree-item" data-bs-toggle="tooltip" data-bs-html="true" 
                                title="${tooltipContent}">
                                <span class="file-tree-toggle" style="visibility: hidden;">
                                    <i class="bi bi-file-text"></i>
                                </span>
                                <label class="file-tree-content">
                                    <input class="form-check-input" type="checkbox" value="${node.name}" checked>
                                    <span class="file-name">${name}</span>
                                </label>
                            </li>
                        `;
                    } else {
                        return `
                            <li>
                                <div class="file-tree-item">
                                    <span class="file-tree-toggle">
                                        <i class="bi bi-chevron-right"></i>
                                    </span>
                                    <label class="file-tree-content">
                                        <input class="form-check-input folder-checkbox" type="checkbox" checked>
                                        <i class="bi bi-folder me-1"></i>
                                        <span class="file-name">${name}</span>
                                    </label>
                                </div>
                                <ul class="collapse">
                                    ${renderFileTree(node.children, level + 1)}
                                </ul>
                            </li>
                        `;
                    }
                }).join('');
                
                return items;
            };
            
            // Create and show file selection list
            const fileList = document.createElement('div');
            fileList.className = 'mt-3';
            
            const fileTree = createFileTree(data.files);
            
            fileList.innerHTML = `
                <button type="button" class="btn btn-primary mb-2 process-files-btn">
                    <i class="bi bi-gear me-2"></i>Process Selected Files
                </button>
                <div class="progress mb-3 d-none">
                    <div class="progress-bar progress-bar-striped progress-bar-animated" role="progressbar" style="width: 0%"></div>
                </div>
                
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <h5 class="mb-0">Select Files to Include</h5>
                    <div class="btn-group" role="group">
                        <button type="button" class="btn btn-sm btn-outline-secondary" id="selectAll">Select All</button>
                        <button type="button" class="btn btn-sm btn-outline-secondary" id="deselectAll">Deselect All</button>
                    </div>
                </div>
                
                <ul class="file-tree mb-3">
                    ${renderFileTree(fileTree)}
                </ul>
                
                <button type="button" class="btn btn-primary process-files-btn">
                    <i class="bi bi-gear me-2"></i>Process Selected Files
                </button>
            `;
            
            // Replace the file info content with the new file list
            const fileInfoContainer = document.getElementById('fileInfo');
            if (fileInfoContainer) {
                // Clear existing content
                fileInfoContainer.innerHTML = '';
                // Add the new file list
                fileInfoContainer.appendChild(fileList);
            }
            
            // Initialize tooltips
            const tooltips = [].slice.call(fileList.querySelectorAll('[data-bs-toggle="tooltip"]'))
            tooltips.forEach(function (tooltip) {
                new bootstrap.Tooltip(tooltip, {
                    html: true,
                    placement: 'right'
                });
            });

            // Add event listeners after inserting the file list
            const processButtons = fileList.querySelectorAll('.process-files-btn');
            processButtons.forEach(button => {
                button.addEventListener('click', processFile);
            });

            // Handle folder toggles
            fileList.querySelectorAll('.file-tree-toggle').forEach(toggle => {
                if (!toggle.style.visibility || toggle.style.visibility !== 'hidden') {
                    toggle.addEventListener('click', (e) => {
                        const item = e.currentTarget.closest('.file-tree-item');
                        const icon = item.querySelector('.bi-chevron-right, .bi-chevron-down');
                        const ul = item.nextElementSibling;
                        
                        if (icon.classList.contains('bi-chevron-right')) {
                            icon.classList.replace('bi-chevron-right', 'bi-chevron-down');
                            ul.classList.add('show');
                        } else {
                            icon.classList.replace('bi-chevron-down', 'bi-chevron-right');
                            ul.classList.remove('show');
                        }
                    });
                }
            });

            // Handle folder checkboxes
            fileList.querySelectorAll('.folder-checkbox').forEach(checkbox => {
                checkbox.addEventListener('change', (e) => {
                    const folder = e.target.closest('li');
                    const childCheckboxes = folder.querySelectorAll('input[type="checkbox"]');
                    childCheckboxes.forEach(cb => cb.checked = e.target.checked);
                });
            });

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

        // Show progress bar
        const progressBar = document.querySelector('.progress');
        const progressBarInner = progressBar.querySelector('.progress-bar');
        progressBar.classList.remove('d-none');
        progressBarInner.style.width = '0%';
        
        // Simulate progress (actual progress not available for small files)
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += 5;
            if (progress <= 90) {
                progressBarInner.style.width = progress + '%';
            }
        }, 100);

        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            clearInterval(progressInterval);
            const progressBarInner = document.querySelector('.progress-bar');
            if (progressBarInner) {
                progressBarInner.style.width = '100%';
            }
            
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
                const progressBar = document.querySelector('.progress');
                if (progressBar) {
                    progressBar.classList.add('d-none');
                }
                fileInfo.classList.add('d-none');
                fileInput.value = '';
            }, 1000);
        })
        .catch(error => {
            clearInterval(progressInterval);
            const progressBar = document.querySelector('.progress');
            if (progressBar) {
                progressBar.classList.add('d-none');
            }
            showError(error.message);
        });
    }

    function showError(message) {
        errorMessage.textContent = message;
        errorContainer.classList.remove('d-none');
    }
});
