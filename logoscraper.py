import os
import requests
from bs4 import BeautifulSoup
import json
import base64
import cairosvg
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image
import time
import logging
import sys

# Configuration for folders and log file
USER_AGENT = "UniLogoScraperBot/1.0 (+https://purpose.hr; g.kobilarov@purpose.hr)"
LOGO_FOLDER = "uni_logos"
SVG_FOLDER = os.path.join(LOGO_FOLDER, "svgs")
URI_FOLDER = os.path.join(LOGO_FOLDER, "uris")
LOG_FILE = "scraper_log.txt"

# Set up logging to capture any issues immediately
logging.basicConfig(filename=LOG_FILE, level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logging.info("Starting logoscraper...")

# Ensure folders exist
os.makedirs(SVG_FOLDER, exist_ok=True)
os.makedirs(URI_FOLDER, exist_ok=True)

# Placeholder patterns and dimensions
PLACEHOLDER_PATTERNS = ["Wikimedia-logo", "earth", "commons-logo"]
PLACEHOLDER_DIMENSIONS = [(320, 320), (1, 1), (200, 200), (150, 150)]

def sanitize_filename(name):
    return "".join(c if c.isalnum() or c in (' ', '_') else "_" for c in name)

def is_placeholder_image(url, image_size):
    if any(placeholder in url for placeholder in PLACEHOLDER_PATTERNS):
        return True
    if image_size in PLACEHOLDER_DIMENSIONS:
        return True
    return False

def get_logo_from_open_graph(website_url):
    """Attempt to find a logo using Open Graph metadata from the university's website."""
    try:
        headers = {'User-Agent': USER_AGENT}
        response = requests.get(website_url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            og_image = soup.find('meta', property='og:image')
            if og_image and og_image['content']:
                return og_image['content']
    except Exception as e:
        logging.error(f"Error fetching Open Graph logo for {website_url}: {e}")
    return None

def get_wikipedia_page_via_api(title, lang_code="en"):
    search_url = f"https://{lang_code}.wikipedia.org/w/api.php"
    headers = {'User-Agent': USER_AGENT}
    params = {'action': 'query', 'list': 'search', 'srsearch': title, 'format': 'json'}
    
    response = requests.get(search_url, headers=headers, params=params)
    if response.status_code == 200:
        search_results = response.json().get('query', {}).get('search', [])
        if search_results:
            page_title = search_results[0]['title']
            page_url = f"https://{lang_code}.wikipedia.org/wiki/{page_title.replace(' ', '_')}"
            return page_url, True
    return None, False

def find_logo_image(soup):
    svg_link = soup.find('a', class_='internal', href=lambda href: href and href.endswith('.svg'))
    if svg_link:
        return 'https:' + svg_link['href']
    
    img_tags = soup.find_all('img')
    for img in img_tags:
        img_src = img.get('src', '').lower()
        if 'logo' in img_src and not is_placeholder_image(img_src, None):
            return 'https:' + img['src']
    return None

def download_image(url, filename):
    headers = {'User-Agent': USER_AGENT}
    retries = 3
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                file_path = os.path.join(SVG_FOLDER, filename)
                with open(file_path, 'wb') as file:
                    file.write(response.content)
                
                # Verify if the image is not a placeholder
                with Image.open(file_path) as img:
                    if is_placeholder_image(url, img.size):
                        logging.info(f"Placeholder image detected for {filename}, skipping.")
                        os.remove(file_path)
                        return None
                logging.info(f"Successfully downloaded image for {filename}")
                return file_path
        except requests.RequestException as e:
            logging.warning(f"Attempt {attempt + 1} - Error downloading image from {url}: {e}")
            time.sleep(2 ** attempt)
    logging.error(f"Failed to download image from {url} after {retries} attempts.")
    return None

def convert_image_to_svg(filepath):
    svg_path = filepath.rsplit(".", 1)[0] + ".svg"
    try:
        if not filepath.endswith(".svg"):
            cairosvg.png2svg(url=filepath, write_to=svg_path)
            logging.info(f"Converted {filepath} to SVG at {svg_path}")
        return svg_path
    except Exception as e:
        logging.error(f"Error converting {filepath} to SVG: {e}")
    return None

def convert_image_to_uri(filepath, filename):
    try:
        with open(filepath, 'rb') as file:
            encoded_string = base64.b64encode(file.read()).decode('utf-8')
            uri_content = f'data:image/{filename.split(".")[-1]};base64,{encoded_string}'
            uri_filename = filename.replace(".", "_") + ".uri"
            uri_path = os.path.join(URI_FOLDER, uri_filename)
            with open(uri_path, 'w') as uri_file:
                uri_file.write(uri_content)
            logging.info(f"Converted {filename} to URI and saved in {uri_path}")
            return True
    except Exception as e:
        logging.error(f"Failed to convert {filename} to URI: {e}")
    return False

def process_university(university):
    uni_name = university.get("original_name", "")
    lang_code = university.get("country_code", "en")
    
    try:
        page_url, success = get_wikipedia_page_via_api(uni_name, lang_code)
        if success:
            response = requests.get(page_url, headers={'User-Agent': USER_AGENT})
            soup = BeautifulSoup(response.text, 'html.parser')
            
            img_url = find_logo_image(soup) or get_logo_from_open_graph(university.get("sub_link"))
            if img_url:
                filename = sanitize_filename(uni_name) + os.path.splitext(img_url)[1]
                file_path = download_image(img_url, filename)
                if file_path:
                    if not file_path.endswith(".svg"):
                        file_path = convert_image_to_svg(file_path) or file_path
                    
                    if convert_image_to_uri(file_path, filename):
                        logging.info(f"Successfully processed logo for {uni_name}")
                        return True
        logging.warning(f"Failed to process logo for {uni_name}")
    except Exception as e:
        logging.error(f"Error processing {uni_name}: {e}")
    return False

# Main execution block with error handling
try:
    print("Script started", flush=True)
    logging.info("Logoscraper main execution started.")

    # Load university data
    with open("universities_data.json", "r", encoding="utf-8") as file:
        universities_data = json.load(file)

    # Process universities in parallel
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(process_university, uni) for uni in universities_data]
        for future in as_completed(futures):
            result = future.result()

    logging.info("Logoscraper finished successfully.")
    print("Script completed", flush=True)

except Exception as e:
    logging.error(f"An unexpected error occurred: {e}")
    print(f"An error occurred: {e}", flush=True)
    sys.exit(1)
