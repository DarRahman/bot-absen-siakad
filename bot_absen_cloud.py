import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys

def setup_driver():
    """Initializes the Chrome driver with headless options for cloud execution."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Runs Chrome in the background
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Disable geolocation popups
    chrome_options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.geolocation": 2
    })
    
    return webdriver.Chrome(options=chrome_options)

def perform_login(driver, nim, password):
    """Fills the login form and submits."""
    try:
        print(f"[*] Attempting to login with NIM: {nim}")
        
        # Locate and fill the username field
        username_field = driver.find_element(By.NAME, "username")
        username_field.clear()
        username_field.send_keys(nim)

        # Locate and fill the password field
        password_field = driver.find_element(By.NAME, "password")
        password_field.clear()
        password_field.send_keys(password)

        # Submit the form using ENTER key
        password_field.send_keys(Keys.ENTER)
        time.sleep(7)  # Wait for server response
    except Exception as e:
        print(f"[!] Error during form submission: {e}")

def main():
    # Retrieve credentials from GitHub Secrets
    NIM = os.environ.get('NIM_KAMPUS')
    PW = os.environ.get('PW_KAMPUS')
    TARGET_URL = "https://siakad.stikompoltekcirebon.ac.id/index.php"

    driver = setup_driver()

    try:
        # Step 1: Initial Login Attempt
        print("[1] Opening SIAKAD login page...")
        driver.get(TARGET_URL)
        perform_login(driver, NIM, PW)

        # Step 2: Handle "Double Login" Bug
        # If still on index page, retry login
        if "dashboard" not in driver.current_url.lower():
            print("[!] Bug detected: Redirected back to login. Retrying (Attempt 2)...")
            perform_login(driver, NIM, PW)

        # Step 3: Verify Success
        if "dashboard" in driver.current_url.lower():
            print("\n✅ SUCCESS: Bot successfully reached the Dashboard in the Cloud!")
            print(f"Current URL: {driver.current_url}")
            
            # This is where we will add Part 2 (Auto-Click Attendance) later
            # For now, we only test the cloud login capability
            
        else:
            print("\n❌ FAILED: Login failed. Please check credentials or server status.")
            print(f"Ending URL: {driver.current_url}")

    except Exception as e:
        print(f"\n⚠️ CRITICAL ERROR: {e}")
    finally:
        print("Closing browser and terminating process.")
        driver.quit()

if __name__ == "__main__":
    main()