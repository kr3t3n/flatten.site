import os
import logging
import zipfile
from flask import Flask, render_template, request, send_file, jsonify, flash, redirect, url_for
from werkzeug.utils import secure_filename
from utils import flatten_zip_hierarchy, list_zip_contents

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "a secret key"

# Configure upload settings
UPLOAD_FOLDER = '/tmp'
ALLOWED_EXTENSIONS = {'zip'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB per file limit
MAX_TOTAL_SIZE = 200 * 1024 * 1024  # 200MB total limit
MAX_FILES = 5  # Maximum number of files that can be processed at once

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_TOTAL_SIZE
app.config['MAX_FILE_SIZE'] = MAX_FILE_SIZE
app.config['MAX_FILES'] = MAX_FILES

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/list-files', methods=['POST'])
def list_zip_files():
    if 'files[]' not in request.files:
        return jsonify({'error': 'No files provided'}), 400
    
    files = request.files.getlist('files[]')
    if not files or all(file.filename == '' for file in files):
        return jsonify({'error': 'No files selected'}), 400

    result = {}
    temp_paths = []
    
    try:
        for file in files:
            if not allowed_file(file.filename):
                return jsonify({'error': f'Invalid file type for {file.filename}. Only ZIP files are allowed'}), 400

            filename = secure_filename(file.filename)
            temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(temp_path)
            temp_paths.append(temp_path)
            
            # List files in each ZIP
            files_in_zip = list_zip_contents(temp_path)
            result[filename] = files_in_zip
            
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error listing zip contents: {str(e)}")
        return jsonify({'error': 'Error reading ZIP files'}), 500
    finally:
        for path in temp_paths:
            if os.path.exists(path):
                os.remove(path)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'files[]' not in request.files:
        return jsonify({'error': 'No files provided'}), 400
    
    files = request.files.getlist('files[]')
    if not files or all(file.filename == '' for file in files):
        return jsonify({'error': 'No files selected'}), 400

    if len(files) > app.config['MAX_FILES']:
        return jsonify({'error': f'Maximum {app.config["MAX_FILES"]} files can be processed at once'}), 400

    # Validate total size
    total_size = sum(file.seek(0, 2) or file.seek(0) or file.tell() for file in files)
    if total_size > app.config['MAX_TOTAL_SIZE']:
        return jsonify({'error': f'Total file size exceeds {app.config["MAX_TOTAL_SIZE"] // (1024*1024)}MB limit'}), 400

    # Validate individual files
    for file in files:
        if not allowed_file(file.filename):
            return jsonify({'error': f'Invalid file type for {file.filename}. Only ZIP files are allowed'}), 400
        if file.seek(0, 2) or file.seek(0) or file.tell() > app.config['MAX_FILE_SIZE']:
            return jsonify({'error': f'File {file.filename} exceeds {app.config["MAX_FILE_SIZE"] // (1024*1024)}MB limit'}), 400

    try:
        temp_paths = []
        processed_files = []
        
        # Get output format and delimiter from form data
        output_format = request.form.get('output_format', 'zip')
        delimiter = request.form.get('delimiter', '^^')
        
        # Process each file
        for file in files:
            filename = secure_filename(file.filename)
            temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(temp_path)
            temp_paths.append(temp_path)
            
            # Get selected files for this zip
            selected_files = request.form.getlist(f'selected_files[{filename}][]')
            
            # Process the zip file
            output_path = flatten_zip_hierarchy(temp_path, selected_files, output_format, delimiter)
            processed_files.append((output_path, filename))

        # If only one file, return it directly
        if len(processed_files) == 1:
            output_path, original_name = processed_files[0]
            base_name = os.path.splitext(original_name)[0]
            return send_file(
                output_path,
                as_attachment=True,
                download_name=f'{base_name}_flattened.{"zip" if output_format == "zip" else "txt"}',
                mimetype='application/zip' if output_format == 'zip' else 'text/plain'
            )
        
        # For multiple files, create a combined zip
        combined_zip_path = os.path.join(app.config['UPLOAD_FOLDER'], 'combined_flattened.zip')
        with zipfile.ZipFile(combined_zip_path, 'w', zipfile.ZIP_DEFLATED) as combined_zip:
            for output_path, original_name in processed_files:
                base_name = os.path.splitext(original_name)[0]
                arcname = f'{base_name}_flattened.{"zip" if output_format == "zip" else "txt"}'
                combined_zip.write(output_path, arcname)
        
        return send_file(
            combined_zip_path,
            as_attachment=True,
            download_name='flattened_files.zip',
            mimetype='application/zip'
        )
        
    except Exception as e:
        logging.error(f"Error processing files: {str(e)}")
        return jsonify({'error': 'Error processing files'}), 500
    finally:
        # Cleanup temporary files
        for path in temp_paths:
            if os.path.exists(path):
                os.remove(path)
        for output_path, _ in processed_files:
            if os.path.exists(output_path):
                os.remove(output_path)
        if 'combined_zip_path' in locals() and os.path.exists(combined_zip_path):
            os.remove(combined_zip_path)

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({'error': 'File too large. Maximum size is 50MB'}), 413

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        
        # Here you would typically send an email or store the contact request
        # For now, we'll just log it
        logging.info(f"Contact form submission from {name} ({email}): {message}")
        
        flash('Thank you for your message. We will get back to you soon!', 'success')
        return redirect(url_for('contact'))
    
    return render_template('contact.html')
