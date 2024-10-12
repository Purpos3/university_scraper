<<<<<<< HEAD
# european_universities
A curated list of European universities available in multiple formats: json, yaml.
Data includes:
 - name
 - city
 - country
 - website
 - logo_url
 - whed_id - unique WHED ID number 

Credits for Github action: 
https://github.com/marketplace/actions/json-yaml-validate
=======
# University Logo Scraper and URI Converter

This Python-based tool scrapes SVG logos of German universities from **Wikipedia** and converts them into **Base64-encoded URIs** for easy embedding in Kotlin frontends or any other web projects.

## Features

- Scrapes SVG logos from German Wikipedia pages for a list of universities.
- Downloads the SVGs and stores them in a specified folder.
- Converts the downloaded SVGs to **Base64 URI format** for embedding in web or mobile applications.
- Stores both the original SVG files and URI-encoded versions in separate folders.
- Supports approximately 50 universities and is easily extendable.

## Prerequisites

- Python 3.x
- `beautifulsoup4` library for HTML parsing
- `requests` library for HTTP requests

### Install the required dependencies:

```bash
pip install beautifulsoup4 requests
>>>>>>> f5a4641 (Update README.md)
