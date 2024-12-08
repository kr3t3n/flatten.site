import os
import logging
from flask import Flask, render_template, request, send_file, jsonify
from werkzeug.utils import secure_filename
from utils import process_zip_file

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "a secret key"

# Configure upload settings
UPLOAD_FOLDER = '/tmp'
ALLOWED_EXTENSIONS = {'zip'}
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB limit

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Please upload a ZIP file'}), 400

    try:
        filename = secure_filename(file.filename)
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(upload_path)
        
        # Process the zip file
        output_path = process_zip_file(upload_path)
        
        # Clean up the original upload
        os.remove(upload_path)
        
        return send_file(
            output_path,
            as_attachment=True,
            download_name='flattened.zip',
            mimetype='application/zip'
        )
    
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        return jsonify({'error': 'Error processing file'}), 500

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({'error': 'File too large'}), 413
