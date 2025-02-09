import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

# Constants
BASE_URL = "https://www.coolblue.be/en/mobile-phones/smartphones/apple-iphone/filter?page="

# Function to fetch and parse HTML content
def get_soup(url):
    """Fetch HTML content and parse it with BeautifulSoup."""
    response = requests.get(url)
    if response.status_code == 200:
        return BeautifulSoup(response.content, 'html.parser')
    print(f"Failed to retrieve {url}")
    return None

# Function to extract product links from a page
def get_product_links():
    """Scrape product links from pagination pages."""
    all_links = set()
    page = 1

    while True:
        soup = get_soup(f"{BASE_URL}{page}")
        if not soup:
            break

        # Extract product links
        links_on_page = {
            link.get('href') for link in soup.find_all('a', href=True) if "/en/product/" in link.get('href')
        }

        if not links_on_page:
            print("No more product links found. Stopping pagination.")
            break

        all_links.update(links_on_page)
        print(f"Page {page}: Found {len(links_on_page)} links.")
        page += 1

    return all_links

# Function to extract text safely
def get_text(element):
    """Return stripped text of an element or None if missing."""
    return element.get_text(strip=True) if element else None

# Function to extract price (before ',' or '-')
def extract_price(price_text):
    """Extract numeric part of the price before ',' or '-'."""
    if price_text:
        match = re.search(r'(\d+[\d.]*)', price_text)
        return match.group(1).replace('.', '') if match else None
    return None

# Function to scrape product details
def scrape_product(link):
    """Extract all required details from a product page."""
    soup = get_soup(f"https://www.coolblue.be{link}")
    if not soup:
        return None

    product_info = {"Link": f"https://www.coolblue.be{link}"}

    # Extract product name
    product_name = get_text(soup.find('div', class_='product-page')?.find('h1'))
    product_info["Name"] = product_name

    # Extract review score and reviews count
    review_section = soup.find('div', class_='review-rating')
    if review_section:
        rating_text = get_text(review_section.find('span'))
        if rating_text and '/' in rating_text:
            product_info["Score"] = rating_text.split('/')[0].strip()
        if '(' in rating_text and ')' in rating_text:
            product_info["Reviews"] = rating_text.split('(')[1].split()[0].strip()

    # Extract price
    price_tag = soup.find('div', class_='js-threshold-toggle-sticky-bar')?.find('span', class_='sales-price')?.find('strong')
    product_info["Price"] = extract_price(get_text(price_tag))

    # Extract second-hand price
    second_chance_tag = soup.find('a', string=lambda text: text and "Affordable Second Chance" in text)
    if second_chance_tag:
        second_chance_price_tag = second_chance_tag.find_next('strong')
        product_info["2nd Hand Price"] = extract_price(get_text(second_chance_price_tag))

    # Extract specifications
    specifications_div = soup.find('div', class_='js-specifications-content')
    if specifications_div:
        for dl in specifications_div.find_all('dl'):
            name = dl.get('data-property-name')
            value = dl.get('data-property-value')

            if not value or value == "1":  # Handle empty values
                title = dl.find('title')
                value = get_text(title) if title else value

            if name and value:
                product_info[name] = value

    return product_info

# Main execution
if __name__ == "__main__":
    product_links = get_product_links()
    products_data = [scrape_product(link) for link in product_links if scrape_product(link) is not None]

    if products_data:
        df = pd.DataFrame(products_data)
        df.to_excel('product_specifications.xlsx', index=False)
        print("Data saved to product_specifications.xlsx")
    else:
        print("No products found.")
