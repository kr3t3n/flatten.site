import os
import zipfile
from tempfile import mkdtemp
import shutil
import logging

def list_zip_contents(input_zip_path):
    """
    Lists all files in the ZIP archive.
    
    Args:
        input_zip_path (str): Path to input zip file
    
    Returns:
        list: List of dictionaries containing file information
    """
    try:
        with zipfile.ZipFile(input_zip_path, 'r') as zip_ref:
            files = []
            for info in zip_ref.infolist():
                if not info.filename.endswith('/'):  # Skip directories
                    files.append({
                        'name': info.filename,
                        'size': info.file_size,
                        'flattened_name': info.filename.replace('/', '^')
                    })
            return files
    except Exception as e:
        logging.error(f"Error reading zip file: {str(e)}")
        raise

def _generate_filetree(path_list):
    """
    Generate a filetree representation from a list of file paths.
    
    Args:
        path_list (list): List of file paths
    
    Returns:
        str: ASCII filetree representation
    """
    if not path_list:
        return "File Tree: (empty)"
    
    # Sort paths for consistent display
    sorted_paths = sorted(path_list)
    
    # Step 1: Build directory tree structure
    dir_tree = {}
    for path in sorted_paths:
        parts = path.split('/')
        
        # Navigate through directory structure
        current = dir_tree
        for i, part in enumerate(parts):
            if i == len(parts) - 1:  # File
                if '__files__' not in current:
                    current['__files__'] = []
                current['__files__'].append(part)
            else:  # Directory
                if part not in current:
                    current[part] = {}
                current = current[part]
    
    # Step 2: Generate ASCII representation
    filetree = ["File Tree:"]
    
    def render_tree(node, prefix="", is_last=True, dir_name=None):
        lines = []
        
        # Process the current directory node
        if dir_name is not None:
            connector = "└── " if is_last else "├── "
            lines.append(f"{prefix}{connector}{dir_name}/")
            next_prefix = prefix + ("    " if is_last else "│   ")
        else:
            next_prefix = prefix
        
        # Process subdirectories first (alphabetically)
        dirs = sorted([d for d in node.keys() if d != '__files__'])
        for i, d in enumerate(dirs):
            is_last_dir = (i == len(dirs) - 1 and '__files__' not in node)
            lines.extend(render_tree(node[d], next_prefix, is_last_dir, d))
        
        # Then process files (alphabetically)
        if '__files__' in node:
            files = sorted(node['__files__'])
            for i, f in enumerate(files):
                is_last_file = (i == len(files) - 1)
                file_connector = "└── " if is_last_file else "├── "
                lines.append(f"{next_prefix}{file_connector}{f}")
        
        return lines
    
    # Generate tree starting from root
    filetree.extend(render_tree(dir_tree))
    
    return '\n'.join(filetree)

def flatten_zip_hierarchy(input_zip_path, selected_files=None, output_format='zip', delimiter='^^'):
    """
    Flattens a zip file hierarchy by converting nested paths to flat paths with ^ separator.
    
    Args:
        input_zip_path (str): Path to input zip file
        selected_files (list): List of filenames to include in the output
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
                            # Skip if not in selected files
                            if selected_files and rel_path not in selected_files:
                                continue
                                
                            flattened_name = rel_path.replace(os.sep, '^')
                            
                            # Add file to new zip
                            new_zip.write(file_path, flattened_name)
                return output_zip_path
            else:
                # Create text output
                with open(output_txt_path, 'w', encoding='utf-8') as txt_file:
                    # Collect all selected files to build the filetree
                    selected_paths = []
                    for root, _, files in os.walk(temp_dir):
                        for file in files:
                            rel_path = os.path.relpath(os.path.join(root, file), temp_dir)
                            if not selected_files or rel_path in selected_files:
                                selected_paths.append(rel_path)
                    
                    # Add filetree at the top
                    filetree = _generate_filetree(selected_paths)
                    txt_file.write(f"{filetree}\n\n{'='*60}\n\n")
                    
                    # Add individual file contents
                    for root, _, files in os.walk(temp_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            rel_path = os.path.relpath(file_path, temp_dir)
                            
                            # Skip if not in selected files
                            if selected_files and rel_path not in selected_files:
                                continue
                                
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
