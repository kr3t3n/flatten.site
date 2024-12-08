import os
import zipfile
from tempfile import mkdtemp
import shutil
import logging

def flatten_zip_hierarchy(input_zip_path):
    """
    Flattens a zip file hierarchy by converting nested paths to flat paths with ^ separator.
    """
    temp_dir = mkdtemp()
    output_zip_path = os.path.join('/tmp', 'flattened_output.zip')
    
    try:
        with zipfile.ZipFile(input_zip_path, 'r') as zip_ref:
            # Extract all files to temporary directory
            zip_ref.extractall(temp_dir)
            
        # Create new zip file
        with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as new_zip:
            # Walk through the extracted directory
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    # Get full file path
                    file_path = os.path.join(root, file)
                    
                    # Create new flattened name
                    rel_path = os.path.relpath(file_path, temp_dir)
                    flattened_name = rel_path.replace(os.sep, '^')
                    
                    # Add file to new zip
                    new_zip.write(file_path, flattened_name)
    
    except Exception as e:
        logging.error(f"Error processing zip file: {str(e)}")
        raise
    finally:
        # Cleanup temporary directory
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    return output_zip_path
