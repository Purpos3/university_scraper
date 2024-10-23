import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

# Set up logging
logging.basicConfig(
    filename='scraper.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Setup Chrome options
chrome_options = Options()
chrome_options.add_argument("--headless")

# Automatically install the driver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# Step 1: Navigate to the WHED results page
driver.get("https://www.whed.net/results_institutions.php")
logging.info("Navigated to the WHED results page.")

# Step 2: Select "Germany" in the dropdown
wait = WebDriverWait(driver, 10)
select_element = wait.until(EC.presence_of_element_located((By.ID, "Chp1")))
select = Select(select_element)
select.select_by_value("Germany")
logging.info("Selected Germany in the dropdown.")

# Step 3: Trigger the JavaScript function to simulate the button click
driver.execute_script("return Valide();")
logging.info("Executed JavaScript function Valide() to submit the form.")

# Function to safely retrieve text from a soup element
def get_text_or_default(soup_element, default="Not found"):
    return soup_element.text.strip() if soup_element else default

# Step 4: Prepare a list to hold university data
university_data = []

def process_universities_on_page():
    """Function to extract university data from the current page."""
    # Wait for the university list to appear
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'fancybox'))
        )
        logging.info("University list is loaded.")
    except Exception as e:
        logging.warning("University list did not load.")
        return False

    # Step 5: Parse the page content
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'html.parser')

    # Step 6: Extract university names and links to detailed pages
    universities = soup.find_all('a', class_='fancybox fancybox.iframe')

    if not universities:
        logging.warning("No universities found on this page. Check the HTML structure.")
        return False

    logging.info(f"Found {len(universities)} universities on this page.")

    # Step 7: Visit each university's detail page and extract more data (city, website)
    for uni in universities:
        uni_name = uni.text.strip()
        uni_link = uni['href']  # Extract the link to the detailed page
        logging.info(f"Processing university: {uni_name}")

        # Step 7.1: Open the detailed page in a new tab
        driver.get(f"https://www.whed.net/{uni_link}")
        logging.info(f"Opened details page for {uni_name}")

        # Step 7.2: Wait for the detailed page to load
        time.sleep(3)  # Adjust sleep time depending on the page load

        # Step 7.3: Parse the detailed page content
        detail_page_source = driver.page_source
        detail_soup = BeautifulSoup(detail_page_source, 'html.parser')

        # Step 7.4: Find the <span class="libelle">City:</span> and extract the following sibling text
        city_label = detail_soup.find('span', class_='libelle', string='City:')
        if city_label:
            # The city is likely in the next sibling after the "City:" label
            city = city_label.find_next_sibling('span').text.strip()
        else:
            city = "City not found"

        # Extract the website link from the <a class="lien"> element
        website_link = detail_soup.find('a', class_='lien', href=True)
        website = website_link['href'] if website_link else "Website not found"

        # Step 7.5: Store the university data
        university_data.append({
            "English Name": uni_name,
            "City": city,
            "Website": website
        })

    return True

# Step 8: Iterate through all numbered pages and process universities on each
current_page = 1
has_next_page = True

while has_next_page:
    logging.info(f"Processing page {current_page}")

    # Process universities on the current page
    processed = process_universities_on_page()

    # Ensure universities are processed before moving to the next page
    if not processed:
        break

    # Step 9: Look for the numbered page link (e.g., 2, 3, etc.) and click it
    try:
        next_page_number = current_page + 1
        next_page_link = driver.find_element(By.XPATH, f'//a[@title="Page n°{next_page_number}"]')
        next_page_link.click()  # Click to go to the next numbered page
        logging.info(f"Clicked on page {next_page_number}")

        # Wait for the next page to load
        time.sleep(5)
        current_page += 1
    except Exception as e:
        logging.info(f"No more pages found or error occurred: {str(e)}")
        has_next_page = False

# Step 10: Output all the university data in the desired format
logging.info("Outputting all university data...")
for data in university_data:
    print(f"English Name: {data['English Name']}, City: {data['City']}, Website: {data['Website']}")
    logging.info(f"English Name: {data['English Name']}, City: {data['City']}, Website: {data['Website']}")

# Step 11: Close the driver
driver.quit()
logging.info("Closed the browser and finished the script.")
