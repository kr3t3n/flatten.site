import os
import re
import logging
from urllib.parse import urljoin, urlparse
from tempfile import mkdtemp
import zipfile
import shutil
import requests
from bs4 import BeautifulSoup

def is_same_domain(url, base_domain):
    """Check if URL belongs to the same domain/subdomain"""
    url_domain = urlparse(url).netloc
    return url_domain == base_domain or url_domain.endswith('.' + base_domain)

def url_to_path(url, base_url):
    """Convert URL to filesystem path"""
    parsed_url = urlparse(url)
    base_parsed = urlparse(base_url)
    
    # Remove base domain from path
    path = parsed_url.path
    if path == '' or path == '/':
        path = '/index.html'
    elif not path.endswith('.html'):
        path = path.rstrip('/') + '/index.html'
    
    # Convert URL path to safe filename
    safe_path = re.sub(r'[<>:"/\\|?*]', '_', path)
    return safe_path.lstrip('/')

def crawl_website(base_url, max_pages=100):
    """
    Crawl website and create a flattened hierarchy
    
    Args:
        base_url: Starting URL to crawl
        max_pages: Maximum number of pages to crawl
    
    Returns:
        tuple: (temp_dir_path, list of crawled pages)
    """
    temp_dir = None
    try:
        # Normalize base URL
        if not base_url.startswith(('http://', 'https://')):
            base_url = 'https://' + base_url
        
        base_domain = urlparse(base_url).netloc
        visited_urls = set()
        to_visit = {base_url}
        crawled_pages = []
        temp_dir = mkdtemp()
        
        while to_visit and len(visited_urls) < max_pages:
            url = to_visit.pop()
            if url in visited_urls:
                continue
                
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                visited_urls.add(url)
                
                # Parse HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Save page content
                file_path = url_to_path(url, base_url)
                full_path = os.path.join(temp_dir, file_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                
                crawled_pages.append({
                    'url': url,
                    'path': file_path,
                    'size': len(response.text)
                })
                
                # Find links
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    absolute_url = urljoin(url, href)
                    
                    # Only follow links to same domain
                    if is_same_domain(absolute_url, base_domain) and absolute_url not in visited_urls:
                        to_visit.add(absolute_url)
                
            except Exception as e:
                logging.error(f"Error crawling {url}: {str(e)}")
                continue
        
        return temp_dir, crawled_pages
        
    except Exception as e:
        logging.error(f"Error during website crawling: {str(e)}")
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
        raise

def _generate_filetree(paths):
    """
    Generate a filetree representation from a list of file paths.
    
    Args:
        paths (list): List of file paths
    
    Returns:
        str: ASCII filetree representation
    """
    if not paths:
        return "File Tree: (empty)"
    
    # Sort paths for consistent display
    sorted_paths = sorted(paths)
    
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

def create_flattened_output(temp_dir, crawled_pages, output_format='zip', delimiter='^^'):
    """
    Create flattened output file from crawled pages
    
    Args:
        temp_dir: Temporary directory containing crawled pages
        crawled_pages: List of crawled page information
        output_format: 'zip' or 'text'
        delimiter: Delimiter for text output
    
    Returns:
        str: Path to output file
    """
    try:
        if output_format == 'zip':
            output_path = os.path.join('/tmp', 'flattened_website.zip')
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for page in crawled_pages:
                    file_path = os.path.join(temp_dir, page['path'])
                    flattened_name = page['path'].replace('/', '^')
                    zf.write(file_path, flattened_name)
            return output_path
            
        else:
            output_path = os.path.join('/tmp', 'flattened_website.txt')
            with open(output_path, 'w', encoding='utf-8') as f:
                # Generate and add filetree at the top of the file
                paths = [page['path'] for page in crawled_pages]
                filetree = _generate_filetree(paths)
                f.write(f"{filetree}\n\n{'='*60}\n\n")
                
                # Add individual files with content
                for page in crawled_pages:
                    file_path = os.path.join(temp_dir, page['path'])
                    flattened_name = page['path'].replace('/', '^')
                    
                    f.write(f"URL: {page['url']}\n")
                    f.write(f"Flattened path: {flattened_name}\n")
                    f.write(f"{delimiter} Begin Content {delimiter}\n")
                    
                    with open(file_path, 'r', encoding='utf-8') as content:
                        f.write(content.read())
                    
                    f.write(f"\n{delimiter} End Content {delimiter}\n\n")
            return output_path
            
    except Exception as e:
        logging.error(f"Error creating flattened output: {str(e)}")
        raise
    finally:
        # Cleanup temp directory
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
