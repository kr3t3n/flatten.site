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
        if 'temp_dir' in locals():
            shutil.rmtree(temp_dir, ignore_errors=True)
        raise

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
