import requests
from bs4 import BeautifulSoup

# URL of the webpage you want to scrape
url = 'https://www.coolblue.be/en/mobile-phones/smartphones/apple-iphone/filter'

# Send a GET request to the URL
response = requests.get(url)

# Check if the request was successful
if response.status_code == 200:
    # Parse the HTML content of the page
    soup = BeautifulSoup(response.content, 'html.parser')

    # # Extract product name
    # product_name = soup.find('h1', class_='product-title').text.strip()
    # print(f'Product Name: {product_name}')

    # # Extract product price
    # product_price = soup.find('span', class_='sales-price__current').text.strip()
    # print(f'Product Price: {product_price}')

    # # Extract product attributes
    # attributes_section = soup.find('section', class_='product-specifications')
    # attributes = attributes_section.find_all('li')

    # print('Product Attributes:')
    # for attribute in attributes:
    #     attribute_name = attribute.find('span', class_='product-specifications__label').text.strip()
    #     attribute_value = attribute.find('span', class_='product-specifications__value').text.strip()
    #     print(f'{attribute_name}: {attribute_value}')
else:
    print('Failed to retrieve the webpage')