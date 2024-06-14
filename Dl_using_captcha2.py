import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
import json
import requests
import base64
import time


API_KEY = '8a52c95ffc7017d98707e271d83160ff' # Set your 2Captcha API key


def solve_captcha(image_path, api_key): # Function to solve captcha using 2Captcha
    with open(image_path, "rb") as captcha_file:
        base64_captcha = base64.b64encode(captcha_file.read()).decode('utf-8')

    response = requests.post("http://2captcha.com/in.php", data={
        'method': 'base64',
        'key': api_key,
        'body': base64_captcha,
        'json': 1
    })
    
    if response.json()["status"] == 1:
        captcha_id = response.json()["request"]
        print("Captcha ID:", captcha_id)
        while True:
            fetch_response = requests.get(f"http://2captcha.com/res.php?key={api_key}&action=get&id={captcha_id}&json=1")
            if fetch_response.json()["status"] == 1:
                return fetch_response.json()["request"]
            time.sleep(5)  # Wait for 5 seconds before retrying
    else:
        raise Exception("Failed to send captcha to 2Captcha")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

driver = webdriver.Chrome() #ChromeDriver

try:
    driver.get("https://parivahan.gov.in/rcdlstatus/?pur_cd=101")  # main the URL
    logging.info("Opened the URL")

    dl_no_field = WebDriverWait(driver, 20).until(
        EC.visibility_of_element_located((By.ID, "form_rcdl:tf_dlNO"))
    )
    dl_no_field.send_keys("MP3720221000183") # Add Driving License Number here
    logging.info("Entered Driving License Number")

    dob_field = WebDriverWait(driver, 20).until(
        EC.visibility_of_element_located((By.ID, "form_rcdl:tf_dob_input"))
    )
    dob = "10-10-2002"  # DOB field required
    driver.execute_script("arguments[0].value = arguments[1];", dob_field, dob)
    logging.info("Entered Date of Birth")

    while True:
        captcha_img = WebDriverWait(driver, 20).until( 
            EC.visibility_of_element_located((By.ID, "form_rcdl:j_idt34:j_idt39")) # Captcha image visible and capture screenshot
        )
        captcha_img.screenshot("captcha.png")
        logging.info("Captured Captcha Image")

        captcha_text = solve_captcha("captcha.png", API_KEY) # Solve captcha using 2Captcha
        print(f"Solved Captcha: {captcha_text}")

        captcha_field = WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.ID, "form_rcdl:j_idt34:CaptchaID")) # Fill in the Captcha
        )
        captcha_field.send_keys(captcha_text)
        logging.info("Entered Captcha")

        check_status_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, "form_rcdl:j_idt44"))
        )
        check_status_button.click()
        logging.info("Clicked Check Status")

        try:
            result_element = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.ID, "form_rcdl:pnl_show"))
            )
            break  # Exit the loop if captcha was correct
        except:
            logging.warning("Captcha was incorrect, retrying...")
            continue  # Retry if captcha was incorrect

     
    result_text = result_element.text   # Get the text from the result element

    try:
        result_json = json.loads(result_text)
        print(json.dumps(result_json, indent=4))
    except json.JSONDecodeError:
        print(result_text)

except Exception as e:
    logging.error(f"Exception occurred: {str(e)}")

finally:
    
    driver.quit() # Close the browser
    logging.info("Closed the browser")
