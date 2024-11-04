from bs4 import BeautifulSoup
import json
import requests

def parse_html(html, country, code):
    soup = BeautifulSoup(html, 'html.parser')
    data_list = []

    # Find all 'li' elements, each representing a single university
    for li in soup.find_all('li', class_='even clearfix plus'):
        try:
            # Extract 'whed_id' from <span> with class 'gui'
            whed_id = li.find_previous_sibling('span', class_='gui').get_text(strip=True)

            # Extract the English name (which was previously labeled as 'original_name')
            english_name = li.find('h3').find('a').get_text(strip=True)

            # Construct sub_link using whed_id
            sub_link = "https://www.whed.net/institutions/" + whed_id

            # Extract the original (local) name, previously labeled as 'english_name'
            original_name = li.find('p', class_='i_name').get_text(strip=True)

            # Check if there is an <img> with class "logo" and extract its src attribute
            logo_tag = li.find('img', class_='logo')
            logo_url = logo_tag['src'] if logo_tag else ""

            # Store the extracted data in a dictionary
            data_dict = {
                'whed_id': whed_id.strip(),
                'original_name': original_name,  # Local name
                'sub_link': sub_link,
                'english_name': english_name,  # English name
                'logo_url': logo_url,
                'country': country,
                'country_code': code
            }

            data_list.append(data_dict)
        except Exception as e:
            print(f"Error parsing university entry: {e}")

    return data_list

def parse_country_whed_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    # Find the form element with name="grille"
    form = soup.find('form', attrs={'name': 'grille'})

    if form:
        # Inside the form, find the input element with the specified attributes
        hidden_input = form.find('input', attrs={'type': 'hidden', 'class': 'envoi', 'name': 'where'})

        if hidden_input and 'value' in hidden_input.attrs:
            # Return the value attribute of the input element
            return hidden_input['value']
    return None


def get_where_id(country):
    url = 'https://www.whed.net/results_institutions.php'
    data = {'Chp1': country, 'Chp0': '', 'Chp2': '', 'Chp4': ''}
    
    response = requests.post(url, data=data)
    print(f"Response for {country}: {response.status_code}")  # Debug status code
    
    where_id = parse_country_whed_html(response.text)
    print(f"Where ID for {country}: {where_id}")  # Debug where_id
    return where_id


def get_unis_by_country(country, code):
    url = 'https://www.whed.net/results_institutions.php'
    where_id = get_where_id(country)

    if where_id is None:
        print(f"Failed to retrieve where_id for {country}")
        return []

    data = {
        'where': where_id,
        'requete': f'(Country={country})',
        'total': 500,
        'ret': 'home.php',
        'Chp0': '',
        'Chp1': country,
        'Chp2': '',
        'Chp3': '',
        'Chp4': '',
        'Chp5': '',
        'debut': '0',
        'use': '',
        'afftri': 'yes',
        'stat': 'Country',
        'sort': 'IAUMember DESC,Country,InstNameEnglish,iBranchName',
        'nbr_ref_pge': 500
    }

    response = requests.post(url, data=data)
    print(f"HTML response for {country} retrieval: {response.status_code}")  # Debug response status
    
    return parse_html(response.text, country, code)

def main():
    european_countries = {
       "Albania": "AL",
       "Armenia": "AM",
       "Austria": "AT",
       "Azerbaijan": "AZ",
       "Belarus": "BY",
       "Belgium": "BE",
       "Bosnia and Herzegovina": "BA",
       "Bulgaria": "BG",
       "Croatia": "HR",
       "Cyprus": "CY",
       "Czechia": "CZ",
       "Denmark": "DK",
       "Estonia": "EE",
       "Finland": "FI",
       "France": "FR",
       "Georgia": "GE",
       "Germany": "DE",
       "Greece": "GR",
       "Hungary": "HU",
       "Iceland": "IS",
       "Ireland": "IE",
       "Italy": "IT",
       "Kazakhstan": "KZ",
       "Latvia": "LV",
       "Liechtenstein": "LI",
       "Lithuania": "LT",
       "Malta": "MT",
       "Moldova": "MD",
       "Monaco": "MC",
       "Montenegro": "ME",
       "Netherlands": "NL",
       "North Macedonia (Republic of)": "MK",
       "Norway": "NO",
       "Poland": "PL",
       "Portugal": "PT",
       "Romania": "RO",
       "Russian Federation": "RU",
       "Serbia": "RS",
       "Slovak Republic": "SK",
       "Slovenia": "SI",
       "Spain": "ES",
       "Sweden": "SE",
       "Switzerland": "CH",
       "Türkiye": "TR",
       "Ukraine": "UA",
       "United Kingdom": "GB"
    }

    all_data = []
    for country, code in european_countries.items():
        try:
            print(f"Processing country: {country}")  # Progress log
            det_unis = get_unis_by_country(country, code)
            print(f"Data for {country}: {det_unis}")  # Output university data
            all_data.extend(det_unis)
        except Exception as e:
            print(f"Error processing {country}: {e}")

    # Optional: Save data to a JSON file if needed
    with open("universities_data.json", "w", encoding="utf-8") as file:
        json.dump(all_data, file, ensure_ascii=False, indent=4)
    print("Data saved to universities_data.json")


if __name__ == "__main__":
    main()
