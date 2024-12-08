import os
import logging
from flask import Flask, render_template, request, send_file, jsonify
from werkzeug.utils import secure_filename
from utils.zip_handler import flatten_zip_hierarchy

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "a secret key"

# Configure upload settings
UPLOAD_FOLDER = '/tmp'
ALLOWED_EXTENSIONS = {'zip'}
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB limit

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Only ZIP files are allowed'}), 400

    try:
        filename = secure_filename(file.filename)
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(temp_path)
        
        # Process the zip file
        output_path = flatten_zip_hierarchy(temp_path)
        
        # Send the processed file
        return send_file(
            output_path,
            as_attachment=True,
            download_name='flattened.zip'
        )
    except Exception as e:
        logging.error(f"Error processing file: {str(e)}")
        return jsonify({'error': 'Error processing file'}), 500
    finally:
        # Cleanup temporary files
        if os.path.exists(temp_path):
            os.remove(temp_path)
        if 'output_path' in locals() and os.path.exists(output_path):
            os.remove(output_path)

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({'error': 'File too large. Maximum size is 50MB'}), 413
