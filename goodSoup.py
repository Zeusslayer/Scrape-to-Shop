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

        # Find the div with class 'main-information-18077go' to get the product name from h1 element
        product_name = None
        product_page_div = soup.find('div', class_='main-information-18077go')
        if product_page_div:
            h1_element = product_page_div.find('h1')
            if h1_element:
                product_name = h1_element.get_text(strip=True)

        # Find the div with class 'main-information-4qdsve' to get score and reviews
        score = None
        reviews = None
        review_rating_div = soup.find('div', class_='main-information-4qdsve')
        if review_rating_div:
            spans = review_rating_div.find_all('span', class_='main-information-ecoufm')
            if spans:
                # First span = score
                score = spans[0].get_text(strip=True)

                # Last span = reviews (extract number inside parentheses)
                reviews_text = spans[-1].get_text(strip=True)
                if '(' in reviews_text:
                    reviews = reviews_text.split('(')[1].split()[0]

        # Extract price from <div class="main-information-1ug6m03">
        price = None
        price_div = soup.find('div', class_='main-information-1ug6m03')
        if price_div:
            span_price = price_div.find('span', class_='main-information-2nej4b')
            if span_price:
                price_text = span_price.get_text(strip=True)  # "1.029 ,-"
                # Extract only the numeric part before the ,-
                price_match = re.search(r'[\d.]+', price_text)
                if price_match:
                    # Keep as string "1.029"
                    price = price_match.group(0)

                    # Keep as integer 1029, remove dot:
                    price = price.replace('.', '')

        # Get second chance price based on the text search
        second_chance_price = None
        second_chance_div = soup.find('a', string=lambda text: text and "Affordable Second Chance" in text)
        if second_chance_div:
            # Look for the next span that contains the price
            second_chance_price_tag = second_chance_div.find_next('span', class_='main-information-2nej4b')
            if second_chance_price_tag:
                second_chance_price_text = second_chance_price_tag.get_text(strip=True)  # e.g. "940 ,-"
                # Extract numeric part
                price_match = re.search(r'[\d.]+', second_chance_price_text)
                if price_match:
                    # Normalize: remove dots so "1.029" → "1029"
                    second_chance_price = price_match.group(0).replace('.', '')

        # Store extracted data until here
        product_info = {
            "Link": f"https://www.coolblue.be{link}",
            "Name": product_name,
            "Price": price,
            "2nd Hand Price": second_chance_price,
            "Reviews": reviews,
            "Score": score
        }

        # Find the section with class 'product-specifications'
        section = soup.find('section', id='product-specifications')

        if section:
            # Find ALL tables inside the section
            tables = section.find_all('table')

            # Loop through each specifications table
            for table in tables:
                rows = table.find_all('tr')

                for row in rows:
                    # Name is always inside <th scope="row">
                    name_cell = row.find('th', scope='row')
                    # The specification value is inside a <td>
                    # with class "css-7wsoqo" (value column)
                    value_cell = row.find('td', class_='css-7wsoqo')

                    # If either the name or the value is missing,
                    # skip this row to avoid errors
                    if not name_cell or not value_cell:
                        continue

                    # Extract and clean the text of the specification name
                    # strip=True removes extra spaces and line breaks
                    name = name_cell.get_text(strip=True)

                    # Handle SVG Yes / No
                    svg = value_cell.find('svg', attrs={'aria-label': True})
                    if svg:
                        value = svg['aria-label']
                    else:
                        value = value_cell.get_text(strip=True)

                    # Only store the data if both name and value are valid
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
