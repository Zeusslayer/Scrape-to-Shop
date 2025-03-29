import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

# Base URL for pagination
base_url = "https://www.coolblue.be/en/mobile-phones/smartphones/apple-iphone"
page = 1  # Start from page 1
all_links = set()  # Use a set to store unique links

while True:
    # if page > 1:  # Stop after 1 iterations. (Testing purposes)
    #     break

    # Construct the URL for the current page (Pagination)
    url = f"{base_url}/filter?page={page}"
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code != 200:
        print(f"Failed to retrieve page {page}. Stopping.")
        break

    # Parse the HTML content of the page
    soup = BeautifulSoup(response.content, 'html.parser')

    # Saving the parsed HTML to a file
    # with open('output.html', 'w', encoding='utf-8') as file:
    #     file.write(soup.prettify())

    # Get product links in the page
    links_on_page = set()
    for link in soup.find_all('a'):
        href = link.get('href')
        if href and "/en/product/" in href:
            links_on_page.add(href)

    # If no new links are found, stop the loop
    if not links_on_page:
        print("No more product links found. Reached the last page.")
        break

    # Add new links to the global set
    all_links.update(links_on_page)

    print(f"Page {page}: Found {len(links_on_page)} new links.")
    page += 1  # Move to the next page

print(f"Total collected links before writing: {len(all_links)}")

# Save unique links to a file.
# with open('links.txt', 'w', encoding='utf-8') as file:
#     for link in all_links:
#         file.write(link + '\n')

# List to store all product data
products_data = []

# Retrieving data from products one by one
for index, link in enumerate(all_links, start=1):
    # if index > 1:  # Stop after 1 iterations. (Testing purposes)
    #     break
    
    response = requests.get(f"https://www.coolblue.be{link}")
    # Example link
    # response = requests.get(
    #     f"https://www.coolblue.be/en/product/953059/apple-iphone-16-pro-max-1tb-natural-titanium.html")

    if response.status_code == 200:
        # Parse the HTML content of the page
        soup = BeautifulSoup(response.content, 'html.parser')

        # Saving the parsed HTML to a file.
        # with open('outputProduct.html', 'w', encoding='utf-8') as file:
        #     file.write(soup.prettify())

        # Find the div with class 'product-page' to get the product name
        product_name = None
        product_page_div = soup.find('div', class_='product-page')
        if product_page_div:
            h1_element = product_page_div.find('h1')
            if h1_element:
                product_name = h1_element.get_text(strip=True)

        # Find the div with class 'review-rating' to get score and reviews
        score = None
        reviews = None
        review_rating_div = soup.find('div', class_='review-rating')
        if review_rating_div:
            span_element = review_rating_div.find('span')
            if span_element:
                rating_text = span_element.get_text(strip=True)
                if '/' in rating_text:
                    score = rating_text.split('/')[0].strip()
                if '(' in rating_text and ')' in rating_text:
                    reviews = rating_text.split('(')[1].split()[0].strip()

        # Extract price from <div class="js-threshold-toggle-sticky-bar">
        price = None
        price_div = soup.find('div', class_='js-threshold-toggle-sticky-bar')
        if price_div:
            sales_price_span = price_div.find('span', class_='sales-price')
            if sales_price_span:
                strong_element = sales_price_span.find('strong')
                if strong_element:
                    price_text = strong_element.get_text(strip=True)
                    price = price_text.split(',')[0].replace(
                        '.', '').strip() if ',' in price_text else price_text

        # Get second chance price based on the text search
        second_chance_price = None
        second_chance_div = soup.find(
            'a', string=lambda text: text and "Affordable Second Chance" in text)
        if second_chance_div:
            second_chance_price_tag = second_chance_div.find_next('strong')
            if second_chance_price_tag:
                second_chance_price_text = second_chance_price_tag.get_text(
                    strip=True)
                # Use regex to extract numbers from the price string
                price_match = re.search(
                    r'(\d[\d,.]*)', second_chance_price_text)
                if price_match:
                    # Clean up price (remove any commas and extract the numeric value)
                    second_chance_price = price_match.group(
                        1).replace(',', '').replace('.', '')

        # Store extracted data until here
        product_info = {
            "Link": f"https://www.coolblue.be{link}",
            "Name": product_name,
            "Price": price,
            "2nd Hand Price": second_chance_price,
            "Reviews": reviews,
            "Score": score
        }

        # Find the div with class 'js-specifications-content'
        specifications_div = soup.find(
            'div', class_='js-specifications-content')

        if specifications_div:
            # Extract all dl elements inside the div
            dl_elements = specifications_div.find_all('dl')

            # Loop through all dl elements and extract data
            for dl in dl_elements:
                name = dl.get('data-property-name')
                value = dl.get('data-property-value')

                # Check for empty string or "1" in value and handle exceptions
                if value == "" or value == "1":
                    # Check if there is a title element under the current dl
                    title_element = dl.find('title')
                    if title_element:
                        value = title_element.get_text(strip=True)
                    else:
                        value = value  # Keep original if no title element is found

                # Only append the data if both name and value exist
                if name and value:
                    product_info[name] = value

        # Add product data to list
        products_data.append(product_info)

        print(f"Stored {index}/{len(all_links)}")

# Create a pandas DataFrame
df = pd.DataFrame(products_data)

# Save the DataFrame to an Excel file
df.to_excel('product_specifications.xlsx', index=False)

print(f"End of scraping")
