import os
import re
import time

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs
import json
import csv
from pathlib import Path

from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC  # Corrected EC import
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver import ActionChains

# Define the storage file
STORAGE_FILE = Path("zara_storage.csv")


def get_product_info(url, category):
    service = Service(
        "E:/Downloads/chromedriver-win64/chromedriver.exe")  # Replace with the path to your ChromeDriver

    options = webdriver.ChromeOptions()
    options.add_argument("--disable-popup-blocking")  # Disables all popup blocking
    options.add_argument("--disable-notifications")  # Disables notifications

    # Initialize the driver
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_window_size(1200, 800)
    driver.get(url)

    # Wait for the location prompt to appear and click "Yes, continue on Turkey"
    try:
        # Wait until the "Yes, continue on Turkey" button is clickable
        continue_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH,
                                        "//button[@class='sitewide-9pwq9q']"))
        )
        continue_button.click()
        print("Clicked to close that")

        cookie_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH,
                                        "//button[@class='onetrust-close-btn-handler']"))
        )
        cookie_button.click()
        print("Clicked to close that")

    except Exception as e:
        print("email overlay did not appear or could not be clicked:", e)

    last_url = driver.current_url
    all_info = []
    try:
        # 2. Identify all color swatch inputs
        color_swatch_inputs = driver.find_elements(By.CSS_SELECTOR, 'input[name="color-radio"]')

        # 3. Iterate over each swatch, click it, grab updated info
        for swatch_input in color_swatch_inputs:
            try:
                color_name = swatch_input.get_attribute("aria-label")  # or aria-label, etc.
                print(color_name)

                # Scroll into view, then try clicking
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", swatch_input)
                try:
                    promo_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH,
                                                    "//div[@class='promoDrawer__handlebar__icon']"))
                    )
                    driver.execute_script("arguments[0].click();", promo_button)
                    print("Clicked to close that")
                except Exception as e:
                    print("promo did not appear or could not be clicked:", e)
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", swatch_input)
                swatch_input.click()



                # Wait for the page update (this is just a naive wait;
                # ideally, wait for a specific condition or new element to appear)
                WebDriverWait(driver, 10).until(EC.url_changes(last_url))

                # Optionally parse the page HTML with BeautifulSoup
                soup = BeautifulSoup(driver.page_source, 'html.parser')

                # Example: grab the updated price
                price_element = soup.select_one(".product-price__highlight .amount-price")
                price = price_element.get_text(strip=True) if price_element else None
                print(price)

                product_element = soup.select_one(".buy-box h1")
                product_name = product_element.get_text(strip=True) if product_element else None
                print(product_name)

                meta_tag = driver.find_element(By.CSS_SELECTOR, 'meta[name="description"]')

                # Extract the "content" attribute
                description_content = meta_tag.get_attribute("content")
                print("Description content:", description_content)

                # Or record the updated URL if it changes
                current_url = driver.current_url
                last_url = current_url
                print(current_url)

                # Approach A: Grab all <img> tags from the container by its class name
                container = driver.find_elements(By.CSS_SELECTOR, 'div.brick__product-image-wrapper')
                srcs = []
                for c in container:
                    img = c.find_element(By.TAG_NAME, "img")
                    src = img.get_attribute("src")
                    srcs.append(src)
                    print(src)

                all_info.append({
                    "url": current_url,
                    "description": description_content,
                    "product_name": product_name,
                    "price": price,
                    "color": color_name,
                    "category": category,
                    "brand": "Gap",
                    "images": srcs
                })
            except:
                continue
    except:
        print("Something went wrong")
    # 5. Close the browser
    driver.quit()
    return all_info




def get_product_urls(url):
    service = Service(
        "C:/Users/Lenovo/Downloads/chromedriver-win64/chromedriver.exe")  # Replace with the path to your ChromeDriver

    # Initialize the driver
    driver = webdriver.Chrome(service=service)
    driver.get(url)
    # Wait for the location prompt to appear and click "Yes, continue on Turkey"
    try:
        # Wait until the "Yes, continue on Turkey" button is clickable
        continue_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH,
                                        "//button[@class='sitewide-9pwq9q']"))
        )
        continue_button.click()
        print("Clicked to close that")
    except Exception as e:
        print("email overlay did not appear or could not be clicked:", e)
    # Scroll to the bottom of the page to load all products
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)  # Wait for new items to load
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    # Parse the loaded page with BeautifulSoup
    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()
    # Find all product links on the main page
    product_links = soup.find_all("div", class_="product-card")
    res = set()
    # Iterate over each product link
    for product in product_links:
        product_href = product.find("a").get("href")
        if product_href:
            print(product_href)
            res.add(product_href)

    return list(res)


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
category_links = ["https://www.gap.com/browse/women/jeans?cid=5664#pageId=0&department=136&mlink=5643,DP_VCN_2_W_CTA", "https://www.gap.com/browse/women/outerwear-and-jackets?cid=5736#pageId=0&department=136&mlink=5643,DP_VCN_3_W_CTA", "https://www.gap.com/browse/women/dresses?cid=13658#pageId=0&department=136&mlink=5643,DP_VCN_4_W_CTA", "https://www.gap.com/browse/women/pants?cid=1011761#pageId=0&department=136&mlink=5643,DP_VCN_5_W_CTA", "https://www.gap.com/browse/women/sweaters?cid=5745#pageId=0&department=136&mlink=5643,DP_VCN_6_W_CTA"]
category_ids = ["5664", "5736", "13658", "1011761", "5745"]

# all_category_links = {}


# for category_link in category_links:
#     final = []
#     print(category_link)
#     all_products_under = get_product_urls(category_link)
#     final.extend(all_products_under)
#
#     all_category_links[category_link] = final
#
# # Save the all_category_links to a JSON file
# with open("gap_data.json", "w") as json_file:
#     json.dump(all_category_links, json_file, indent=4)
#     print("Data has been saved to gap_data.json.json")

# Open the JSON file
# with open('gap_data.json', 'r') as file:
#     all_category_links = json.load(file)
#
# everything = []
# categories = ["Jeans", "Outerwear", "Dresses", "Pants", "Sweaters"]
# for ind, link in enumerate(category_links):
#     all_links = all_category_links[link]
#     for l in all_links:
#         cate = categories[ind]
#         infos = get_product_info(l, cate)
#         everything.append(infos)
# with open("gap_url_data.json", "w") as json_file:
#     json.dump(everything, json_file, indent=4)
#     print("Data has been saved to gap_url_data.json.json")

def extract_pids(nested_data):
    """Return a list of all pid values in a nested data structure."""
    pids = []
    for sub_list in nested_data:
        for item in sub_list:
            url = item["url"]
            parsed_url = urlparse(url)               # Parse the URL
            query_dict = parse_qs(parsed_url.query)  # Parse the query string into a dict
            pid_list = query_dict.get("pid")         # pid_list will be None or a list of strings
            if pid_list:
                pids.append(pid_list[0])            # Grab the first item (usually there's only one)
            item["pid"] = pid_list[0]
    with open("gap_full_data.json", "w") as json_file:
        json.dump(nested_data, json_file, indent=4)
        print("Data has been saved to gap_full_data.json")
    return pids

with open('gap_url_data.json', 'r') as file:
    data = json.load(file)

all_pids = extract_pids(data)
