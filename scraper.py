import os
import requests
from bs4 import BeautifulSoup
from time import sleep
import base64

# Define a user agent for scraping
USER_AGENT = "MyUniversityScraper/1.0 (https://example.com; info@example.com)"
LOGO_FOLDER = "uni_logos"
SVG_FOLDER = os.path.join(LOGO_FOLDER, "svgs")
URI_FOLDER = os.path.join(LOGO_FOLDER, "uris")

# Create the folders if they don't exist
os.makedirs(SVG_FOLDER, exist_ok=True)
os.makedirs(URI_FOLDER, exist_ok=True)

# Function to search Wikipedia and return the first relevant page URL (German Wikipedia)
def get_wikipedia_page(title):
    search_url = f"https://de.wikipedia.org/wiki/{title.replace(' ', '_')}"
    headers = {'User-Agent': USER_AGENT}
    
    # Make a request to the German Wikipedia page
    response = requests.get(search_url, headers=headers)
    
    if response.status_code == 200:
        return search_url
    else:
        print(f"❌ Could not find a Wikipedia page for {title} (Status: {response.status_code})")
        return None

# Function to download SVG with retry and error handling
def download_svg(url, filename):
    headers = {
        'User-Agent': USER_AGENT
    }
    retries = 3  # Number of retry attempts
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                svg_path = os.path.join(SVG_FOLDER, filename)
                with open(svg_path, 'wb') as file:
                    file.write(response.content)
                print(f"✅ Downloaded: {filename}")
                return svg_path
            else:
                print(f"❌ Failed to download {url}: Status code {response.status_code}")
        except Exception as e:
            print(f"❌ Error downloading {url}: {e}")
        sleep(2)  # Wait 2 seconds before retrying
    print(f"❌ Failed to download {filename} after {retries} attempts.")
    return None

# Function to convert an SVG file to a URI format suitable for Kotlin and save it in the uri folder
def convert_svg_to_uri(svg_path, filename):
    try:
        with open(svg_path, 'rb') as svg_file:
            svg_data = svg_file.read()
            svg_base64 = base64.b64encode(svg_data).decode('utf-8')
            svg_uri = f"data:image/svg+xml;base64,{svg_base64}"
            
            # Format the URI for Kotlin constant storage
            kotlin_formatted_uri = f'val {filename.replace(".svg", "")}Uri = "{svg_uri}"'
            
            # Save it in a .kt file in the uris folder
            uri_filename = filename.replace('.svg', '_uri.kt')
            uri_path = os.path.join(URI_FOLDER, uri_filename)
            with open(uri_path, 'w') as uri_file:
                uri_file.write(kotlin_formatted_uri)
            print(f"✅ Converted {filename} to URI and saved in {uri_filename}")
            return True
    except Exception as e:
        print(f"❌ Failed to convert {filename} to URI: {e}")
        return False

# Function to extract the SVG file URL from the file description page
def get_svg_from_description_page(description_url):
    headers = {'User-Agent': USER_AGENT}
    response = requests.get(description_url, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        # The actual image URL is usually within a full media URL link with class 'internal'
        svg_link = soup.find('a', class_='internal')
        if svg_link and svg_link['href'].endswith('.svg'):
            return 'https:' + svg_link['href']
    return None

# Function to find the logo SVG in the Wikipedia page content
def find_svg_in_wikipedia_page(page_url):
    headers = {'User-Agent': USER_AGENT}
    try:
        response = requests.get(page_url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Search for the link to the file description page (in German Wikipedia, it will still be "Datei")
            file_page_link = soup.find('a', href=lambda x: x and 'Datei:' in x)
            if file_page_link:
                description_url = 'https://de.wikipedia.org' + file_page_link['href']
                return get_svg_from_description_page(description_url)
        print(f"❌ Failed to find SVG in the page {page_url}")
    except Exception as e:
        print(f"❌ Error accessing {page_url}: {e}")
    return None

# List of universities to search and scrape SVG logos (in German)
universities = [
"Friedrich-Alexander-Universität Erlangen-Nürnberg",
    "Technische Universität München",
    "Ludwig-Maximilians-Universität München",
    "Rheinische Friedrich-Wilhelms-Universität Bonn",
    "Freie Universität Berlin",
    "Humboldt-Universität zu Berlin",
    "Universität Hamburg",
    "Georg-August-Universität Göttingen",
    "Karlsruher Institut für Technologie",
    "Johannes Gutenberg-Universität Mainz",
    "Eberhard Karls Universität Tübingen",
    "Heinrich-Heine-Universität Düsseldorf",
    "Universität Stuttgart",
    "Leibniz Universität Hannover",
    "Ruhr-Universität Bochum",
    "Universität zu Köln",
    "Universität Leipzig",
    "Christian-Albrechts-Universität zu Kiel",
    "Universität Mannheim",
    "Universität Passau",
    "Universität Augsburg",
    "Technische Universität Dresden",
    "Technische Universität Dortmund",
    "Technische Universität Berlin",
    "Technische Universität Braunschweig",
    "Bauhaus-Universität Weimar",
    "Universität Potsdam",
    "Universität Konstanz",
    "Universität Ulm",
    "Universität Bielefeld",
    "Universität Bremen",
    "Universität Regensburg",
    "Universität Trier",
    "Universität Hohenheim",
    "Universität Oldenburg",
    "Universität Paderborn",
    "Universität Wuppertal",
    "Universität Bayreuth",
    "Europa-Universität Viadrina",
    "Frankfurt School of Finance & Management",
    "Universität der Bundeswehr München",
    "Jacobs University Bremen",
    "Universität des Saarlandes",
    "Hertie School of Governance",
    "Technische Universität Kaiserslautern",
    "Universität Erfurt",
    "Helmut-Schmidt-Universität Hamburg",
    "Universität Siegen",
    "Universität Koblenz-Landau",
    "Universität Flensburg"
]

# Main loop to search, find, and download SVG logos for universities
success_count = 0
failure_count = 0

for university in universities:
    print(f"🔍 Searching for {university} German Wikipedia page...")
    page_url = get_wikipedia_page(university)
    
    if page_url:
        print(f"🔗 Found Wikipedia page: {page_url}")
        svg_url = find_svg_in_wikipedia_page(page_url)
        if svg_url:
            print(f"🔗 Found SVG URL: {svg_url}")
            filename = university.replace(" ", "_").replace("ä", "ae").replace("ü", "ue").replace("ö", "oe").replace("ß", "ss") + ".svg"
            svg_path = download_svg(svg_url, filename)
            if svg_path:
                success_count += 1
                # Convert to URI format and save in the uris folder
                convert_svg_to_uri(svg_path, filename)
            else:
                print(f"❌ Failed to download SVG for {university}")
                failure_count += 1
        else:
            print(f"❌ No SVG found for {university}")
            failure_count += 1
    else:
        print(f"❌ Could not find Wikipedia page for {university}")
        failure_count += 1

# Final Summary
print("\n🎉 Download Summary:")
print(f"✅ Successful downloads: {success_count}")
print(f"❌ Failed downloads: {failure_count}")
