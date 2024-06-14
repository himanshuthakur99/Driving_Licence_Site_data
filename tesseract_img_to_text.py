from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import pytesseract
import json
import time


pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Set the Tesseract command path
 
driver = webdriver.Chrome() #ChromeDriver

def preprocess_captcha(image_path):
    captcha_image = Image.open(image_path)
    captcha_image = captcha_image.convert('L')  # Convert to grayscale
    captcha_image = captcha_image.filter(ImageFilter.MedianFilter())  # Apply median filter

    enhancer = ImageEnhance.Contrast(captcha_image) # Enhance the image contrast
    captcha_image = enhancer.enhance(2)

    captcha_image = ImageOps.invert(captcha_image)  # Invert colors if the text is light on dark background
    captcha_image = captcha_image.point(lambda p: p > 128 and 255)

    captcha_image = captcha_image.filter(ImageFilter.MaxFilter(3))  # Dilation

    captcha_image = captcha_image.filter(ImageFilter.MinFilter(3))  # Apply erosion to remove noise

    return captcha_image

def solve_captcha(image_path, attempts=5):
    for attempt in range(attempts):
        captcha_image = preprocess_captcha(image_path)
        captcha_text = pytesseract.image_to_string(captcha_image, config='--psm 8').strip()
        if captcha_text:  # If captcha_text is not empty
            return captcha_text
    return ""

try:
   
    driver.get("https://parivahan.gov.in/rcdlstatus/?pur_cd=101")  # Main URL

    dl_no_field = WebDriverWait(driver, 20).until(
        EC.visibility_of_element_located((By.ID, "form_rcdl:tf_dlNO")) # for DL No field to be visible and fill 
    )
    dl_no_field.send_keys("MP3720221000183") # DL Number

    dob_field = WebDriverWait(driver, 20).until(
        EC.visibility_of_element_located((By.ID, "form_rcdl:tf_dob_input"))
    )
    dob = "10-10-2002"  # Date of b Same format required
    driver.execute_script("arguments[0].value = arguments[1];", dob_field, dob)

    captcha_img = WebDriverWait(driver, 20).until(
        EC.visibility_of_element_located((By.ID, "form_rcdl:j_idt34:j_idt39"))  # Captcha image visible and capture screenshot
    )
    captcha_img.screenshot("captcha.png")

    captcha_text = solve_captcha("captcha.png")  # OCR to read the captcha

    if not captcha_text:
        raise Exception("Failed to solve CAPTCHA")

    captcha_field = WebDriverWait(driver, 20).until(
        EC.visibility_of_element_located((By.ID, "form_rcdl:j_idt34:CaptchaID")) # This for Fill Captcha
    )
    captcha_field.send_keys(captcha_text)

    check_status_button = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.ID, "form_rcdl:j_idt44"))
    )
    check_status_button.click()

    result_element = WebDriverWait(driver, 20).until(
        EC.visibility_of_element_located((By.ID, "form_rcdl:pnl_show"))
    )

    
    result_text = result_element.text # Get the text from the result element

    try:
        result_json = json.loads(result_text)
        print(json.dumps(result_json, indent=4))
    except json.JSONDecodeError:
        print(result_text)

except Exception as e:
    print(f"Exception occurred: {str(e)}")

finally:
    
    driver.quit() # Close the browser
