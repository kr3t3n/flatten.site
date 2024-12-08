import os
import zipfile
import tempfile
from pathlib import Path

def process_zip_file(input_path):
    """
    Process a zip file by flattening its hierarchy and renaming files
    using ^ as a separator for directory levels.
    """
    # Create a temporary file for the output zip
    temp_fd, temp_path = tempfile.mkstemp(suffix='.zip')
    os.close(temp_fd)

    with zipfile.ZipFile(input_path, 'r') as zip_in:
        with zipfile.ZipFile(temp_path, 'w', zipfile.ZIP_DEFLATED) as zip_out:
            # Process each file in the zip
            for file_info in zip_in.filelist:
                if file_info.filename[-1] == '/':  # Skip directories
                    continue
                
                # Read the file content
                content = zip_in.read(file_info.filename)
                
                # Create the new filename
                path_parts = Path(file_info.filename).parts
                new_filename = '^'.join(path_parts)
                
                # Write to the new zip with the flattened filename
                zip_out.writestr(new_filename, content)
    
    return temp_path
