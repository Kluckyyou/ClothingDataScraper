import os
import re

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json
import csv
from pathlib import Path

# Define the storage file
STORAGE_FILE = Path("zara_storage.csv")


def get_product_info(url):

    # Headers to mimic a browser request
    headers = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/58.0.3029.110 Safari/537.3")
    }

    # Send a request to the main page with headers
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        # Parse the content of the main page
        soup = BeautifulSoup(response.content, "html.parser")
        # Locate the script by a unique attribute
        script_tag = soup.find('script', attrs={'data-compress': 'true'})
        if script_tag and script_tag.string:
            script_text = script_tag.string

            # 3. Regex to isolate the JSON part after "zara.analyticsData ="
            pattern = re.compile(r'zara\.analyticsData\s*=\s*(\{.*?\});', re.DOTALL)
            match = pattern.search(script_text)
            if match:
                json_string = match.group(1)  # The {...} part
                # 4. Load into a Python dict
                data_dict = json.loads(json_string)
                print(data_dict)
                try:
                    category_id = data_dict['catentryId']
                    product_id = data_dict['productId']
                    product_name = data_dict['productName']
                    discounted_price = data_dict['mainPrice']
                    color_code = data_dict['colorCode']
                    product_family = data_dict['family']
                    product_subfamily = data_dict['subfamily']
                    section = data_dict['section']
                    low_on_stock = data_dict['lowOnStockProduct']
                    currency = data_dict['page']['currency']
                except:
                    print("something does not exist")
            else:
                print("Could not find zara.analyticsData in the script.")
        else:
            print("Script tag not found or empty.")
        # Find the <p> tag
        p_tag = soup.find('p', class_='product-color-extended-name')
        text_all = p_tag.get_text(strip=True)
        color_name = text_all.split('|')[0].strip()
        print(color_name)

        div_tag = soup.find("div", class_="expandable-text__inner-content")
        if div_tag:
            p_tag = div_tag.find("p")
            if p_tag:
                # separator=" " ensures <br> is turned into a space.
                # strip=True removes leading/trailing whitespace.
                description = p_tag.get_text(strip=True)
                print(description)

        # Find all <picture> tags
        pictures = soup.find_all('picture', class_='media-image')
        all_image_urls = set()  # We'll collect them here

        for pic in pictures:
            # 2) Grab each <source> srcset
            source_tags = pic.find_all('source')
            # print(source_tags)
            for source in source_tags:
                srcset_value = source.get('srcset')
                # srcset often looks like: "url1 375w, url2 750w, url3 1500w"
                # We can split by commas to get each "urlN wN" chunk
                chunk = srcset_value.split(',')[0]
                # print(chunk)
                # chunk might look like "https://static.zara.net/example-2.jpg?w=375 375w"
                # split again by space to separate the URL from width (e.g., "375w")
                parts = chunk.strip().split('?')
                if parts:
                    # The first part is the URL
                    img_url = parts[0]
                    all_image_urls.add(img_url)
        print(list(all_image_urls))
    print(url)
    save_result(category_id, product_id, product_name, discounted_price, color_code, color_name, description, product_family, product_subfamily, section, low_on_stock, url, currency, list(all_image_urls))


def get_product_urls(url, category_id):
    # Headers to mimic a browser request
    headers = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/58.0.3029.110 Safari/537.3")
    }

    # Send a request to the main page with headers
    response = requests.get(url, headers=headers)
    res = []
    if response.status_code == 200:
        # Parse the content of the main page
        soup = BeautifulSoup(response.content, "html.parser")

        # Find all product links on the main page
        product_links = soup.find_all("li", class_="product-grid-product")

        # Iterate over each product link
        for product in product_links:
            product_id = product.get("data-productid")
            product_href = product.find("a", class_="product-link product-grid-product__link link")
            if product_href:
                # Append the full URL, including any query parameters (e.g., v1, v2)
                product_url = urljoin(url, product_href.get("href"))
                product_url += "?v1=" + product_id + "&v2=" + category_id
                print(product_url)
                res.append(product_url)
                # get_product_info(product_url)

    else:
        print(f"Failed to retrieve the main page: {response.status_code}")
    return res


def save_result(category_id, product_id, product_name, price, colour_code, colour, description, product_family, product_subfamily, section, low_on_stock, url, currency, pictures):
    # Check if the file exists and has a header
    file_exists = STORAGE_FILE.exists()

    with open(STORAGE_FILE, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        # Write the header if the file is new
        if not file_exists:
            writer.writerow(["categoryId", "productId", "productName", "price", "colourCode", "colour", "description", "productFamily","productSubfamily", "section", "lowOnStock", "url", "currency", "image"])
        # Write the function header, instruction, and docstring
        writer.writerow([category_id, product_id, product_name, price, colour_code, colour, description, product_family, product_subfamily, section, low_on_stock, url, currency, pictures])


# Specify the URL of the main website page
category_links = ["https://www.zara.com/us/en/woman-shoes-l1251.html?v1=2419285", "https://www.zara.com/us/en/woman-bags-l1024.html?v1=2419364"]
category_ids = ["2419285", "2419364"]

all_category_links = {}


for idx, category_link in enumerate(category_links):
    page_num = 1
    final = []
    while True:
        try:
            attempt_url = category_link + "&page=" + str(page_num)
            print(attempt_url)
            all_products_under = get_product_urls(attempt_url, category_ids[idx])
            final.extend(all_products_under)
            page_num += 1
            if not all_products_under:
                break
        except:
            break

    all_category_links[category_link] = final

for link in category_links:
    all_links = all_category_links[link]
    for l in all_links:
        get_product_info(l)
