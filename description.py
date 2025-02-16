from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import os
from flask import url_for, current_app
import openai
from openai import OpenAI
from config import API_KEY

# Configure OpenAI API
openai.api_key = API_KEY

def get_latest_image_url():
    """Retrieve the URL of the most recently uploaded image."""
    uploads_folder = current_app.config['UPLOAD_FOLDER']
    
    try:
        # List all files in the uploads directory with allowed image extensions
        files = [
            f for f in os.listdir(uploads_folder)
            if os.path.isfile(os.path.join(uploads_folder, f))
               and f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))
        ]
        
        if not files:
            return None  # No images uploaded yet
        
        # Sort files by modification time in descending order (newest first)
        files.sort(key=lambda x: os.path.getmtime(os.path.join(uploads_folder, x)), reverse=True)
        
        # The first file in the sorted list is the most recent
        latest_file = files[0]
        
        # Construct the URL for the latest image using the 'uploaded_file' route
        image_url = url_for('uploaded_file', filename=latest_file, _external=True)
        return image_url
    
    except Exception as e:
        print(f"Error retrieving the latest image: {e}")
        return None


def generate_description():
    #image_url = get_latest_image_url()
    image_url = "http://127.0.0.1:5000/uploads/jeans.jpg"
    image_url = "https://tarunchinta.github.io/uploads/jeans.jpg"

    # Define the path to your ChromeDriver executable
    chromedriver_path = "../chromedriver-win64/chromedriver.exe"
    service = Service(executable_path=chromedriver_path)

    # Initialize the WebDriver
    driver = webdriver.Chrome(service=service)

    try:
        # Open Google Image Search
        driver.get("https://images.google.com/")

        # Locate and click the camera icon
        camera_icon = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div[aria-label='Search by image']"))
        )
        camera_icon.click()

        # Wait for the input field to be interactable
        url_input = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "input.cB9M7"))
        )

        # Enter the image URL using JavaScript to avoid interaction issues
        driver.execute_script("arguments[0].value = arguments[1];", url_input, image_url)

        # Locate and click the "Search" button
        search_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div.Qwbd3"))
        )
        search_button.click()

        # Wait for results to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # Extract the HTML of the resulting page
        page_html = driver.page_source
        print("HTML of the resulting page has been extracted.")

        # Optionally, save the HTML to a file
        with open("resulting_page.html", "w", encoding="utf-8") as file:
            file.write(page_html)

    finally:
        # Close the browser
        driver.quit()

    from bs4 import BeautifulSoup


    # Parse the HTML using BeautifulSoup
    soup = BeautifulSoup(page_html, 'html.parser')

    # Find all elements with the 'aria-label' attribute
    aria_labels = [element['aria-label'] for element in soup.find_all(attrs={"aria-label": True})]

    # Print the extracted strings
    print("Strings following aria-label tags:", aria_labels)

    llm_input_text = str(aria_labels[23:28])
    llm_prompt = f'Take the following descriptions and summarize into one clothing description. Your description should be a similar length, use the same tone and style, and can\'t include brand or price. Here are the descriptions to summarize: {llm_input_text}'


    # Please install OpenAI SDK first: `pip3 install openai`

    from openai import OpenAI

    from config import API_KEY  # Import API_KEY from config
    client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": llm_prompt},
        ],
        stream=False
    )

    return response.choices[0].message.content