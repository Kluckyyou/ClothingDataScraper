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

    all_info = []
    try:
        # 2. Identify all color swatch inputs
        color_swatch_inputs = driver.find_elements(By.CSS_SELECTOR, 'input[name="swatch"]')

        # 3. Iterate over each swatch, click it, grab updated info
        for swatch_input in color_swatch_inputs:
            try:
                product_id = swatch_input.get_attribute("value")
                if not product_id:
                    product_id = swatch_input.get_attribute("checked value")
                print(product_id)

                # Scroll into view, then try clicking
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", swatch_input)
                swatch_input.click()

                # Wait for the page update (this is just a naive wait;
                # ideally, wait for a specific condition or new element to appear)
                time.sleep(5)  # Wait for new items to load

                # Optionally parse the page HTML with BeautifulSoup
                soup = BeautifulSoup(driver.page_source, 'html.parser')

                h3_element = soup.find("h3", class_="shown_in__h3-mfe")
                span_element = h3_element.find("span", class_="h3__span")
                color_text = span_element.get_text()
                print(color_text)

                # Example: grab the updated price
                price_screen_reader_span = soup.find("span", class_="screen-reader-text")
                if price_screen_reader_span:
                    price_text = price_screen_reader_span.get_text(strip=True)
                    print(price_text)
                else:
                    price_text = ""
                    print("No 'screen-reader-text' span found.")

                meta_tag = driver.find_element(By.CSS_SELECTOR, 'meta[property="og:title"]')
                # Extract the "content" attribute
                product_title = meta_tag.get_attribute("content")
                print("product_title:", product_title)

                meta_tag = driver.find_element(By.CSS_SELECTOR, 'meta[property="og:title"]')
                # Extract the "content" attribute
                product_title = meta_tag.get_attribute("content")
                print("product_title:", product_title)

                meta_tag = driver.find_element(By.CSS_SELECTOR, 'meta[property="og:description"]')
                # Extract the "content" attribute
                description_content = meta_tag.get_attribute("content")
                print("Description content:", description_content)

                meta_tag = driver.find_element(By.CSS_SELECTOR, 'meta[name="keywords"]')
                # Extract the "content" attribute
                keywords = meta_tag.get_attribute("content")
                print("keywords:", keywords)

                # Or record the updated URL if it changes
                current_url = driver.current_url
                print(current_url)

                # Approach A: Grab all <img> tags from the container by its class name
                container = driver.find_elements(By.CSS_SELECTOR, 'div.product-page-gallery-mfe-container')
                srcs = []
                for c in container:
                    img = c.find_element(By.TAG_NAME, "img")
                    src = img.get_attribute("src")
                    srcs.append(src)
                    print(src)

                all_info.append({
                    "url": current_url,
                    "description": description_content,
                    "product_name": product_title,
                    "price": price_text,
                    "color": color_text,
                    "category": category,
                    "brand": "A&F",
                    "images": srcs,
                    "keywords": keywords,
                    "productid": product_id,
                    "currency": "CAD"
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
        "E:/Downloads/chromedriver-win64/chromedriver.exe")  # Replace with the path to your ChromeDriver

    # Initialize the driver
    driver = webdriver.Chrome(service=service)
    driver.set_window_size(1200, 800)
    driver.get(url)
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

    # Find all product links on the main page
    product_links = soup.find_all("div", class_="catalog-productCard-module__product-image-section")
    res = set()
    # Iterate over each product link
    for product in product_links:
        product_href = product.find("a").get("href")
        if product_href:
            print("https://www.abercrombie.com" + product_href)
            res.add("https://www.abercrombie.com" + product_href)
    driver.quit()
    return list(res)

# Specify the URL of the main website page
category_links = ["https://www.abercrombie.com/shop/ca/womens-coats-and-jackets", "https://www.abercrombie.com/shop/ca/womens-tops--1", "https://www.abercrombie.com/shop/ca/womens-bottoms--1", "https://www.abercrombie.com/shop/ca/womens-dresses-and-jumpsuits"]
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
# with open("af_data.json", "w") as json_file:
#     json.dump(all_category_links, json_file, indent=4)
#     print("Data has been saved to af_data.json")

# Open the JSON file
with open('af_data.json', 'r') as file:
    all_category_links = json.load(file)

everything = []
categories = ["coats-and-jackets", "tops", "bottoms", "dresses-and-jumpsuits"]
for ind, link in enumerate(category_links):
    all_links = all_category_links[link]
    for l in all_links:
        cate = categories[ind]
        infos = get_product_info(l, cate)
        everything.append(infos)
with open("af_full_data.json", "w") as json_file:
    json.dump(everything, json_file, indent=4)
    print("Data has been saved to af_full_data.json")