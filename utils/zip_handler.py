import os
import zipfile
from tempfile import mkdtemp
import shutil
import logging

def flatten_zip_hierarchy(input_zip_path, output_format='zip', delimiter='^^'):
    """
    Flattens a zip file hierarchy by converting nested paths to flat paths with ^ separator.
    
    Args:
        input_zip_path (str): Path to input zip file
        output_format (str): 'zip' or 'text'
        delimiter (str): Delimiter for text output format
    
    Returns:
        str: Path to output file (zip or txt)
    """
    temp_dir = mkdtemp()
    output_zip_path = os.path.join('/tmp', 'flattened_output.zip')
    output_txt_path = os.path.join('/tmp', 'flattened_output.txt')
    
    try:
        with zipfile.ZipFile(input_zip_path, 'r') as zip_ref:
            # Extract all files to temporary directory
            zip_ref.extractall(temp_dir)
            
        if output_format == 'zip':
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
            return output_zip_path
        else:
            # Create text output
            with open(output_txt_path, 'w', encoding='utf-8') as txt_file:
                for root, _, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, temp_dir)
                        flattened_name = rel_path.replace(os.sep, '^')
                        
                        # Write file path and contents with delimiter
                        txt_file.write(f"File: {flattened_name}\n")
                        txt_file.write(f"Original path: {rel_path}\n")
                        txt_file.write(f"{delimiter} Begin Content {delimiter}\n")
                        try:
                            with open(file_path, 'r', encoding='utf-8') as content_file:
                                txt_file.write(content_file.read())
                        except UnicodeDecodeError:
                            txt_file.write("[Binary file content not shown]")
                        txt_file.write(f"\n{delimiter} End Content {delimiter}\n\n")
            return output_txt_path
    
    except Exception as e:
        logging.error(f"Error processing zip file: {str(e)}")
        raise
    finally:
        # Cleanup temporary directory
        shutil.rmtree(temp_dir, ignore_errors=True)
