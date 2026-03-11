import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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

def perform_attendance(driver):
    """Navigates to the attendance page and clicks the attendance button."""
    try:
        print("\n[2] Navigating to Attendance (Absen) page...")
        absen_url = "https://siakad.stikompoltekcirebon.ac.id/index.php?module=absen"
        driver.get(absen_url)

        wait = WebDriverWait(driver, 15)
        # Wait until the page body is present before searching for buttons
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        # Find all available "Absen" / attendance buttons on the page
        # translate() maps both upper and lower case letters to lowercase for case-insensitive match
        absen_buttons = driver.find_elements(By.XPATH,
            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'absen')] | "
            "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'absen') and contains(@href, 'absen')]"
        )

        if not absen_buttons:
            # Fallback: look for any submit/action button inside attendance rows
            absen_buttons = driver.find_elements(By.XPATH,
                "//input[@type='submit' and contains(translate(@value, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'absen')] | "
                "//button[contains(@class, 'absen') or contains(@id, 'absen')]"
            )

        if absen_buttons:
            clicked = 0
            for btn in absen_buttons:
                try:
                    driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                    btn.click()
                    time.sleep(2)
                    clicked += 1
                    print(f"  ✅ Clicked attendance button #{clicked}: {btn.text or btn.get_attribute('value')}")
                except Exception as e:
                    print(f"  [!] Could not click button: {e}")
            if clicked > 0:
                print(f"\n✅ SUCCESS: Marked attendance for {clicked} session(s).")
            else:
                print("\n⚠️ WARNING: Found attendance buttons but could not click any.")
        else:
            print("\n⚠️ WARNING: No attendance buttons found. The attendance window may be closed,")
            print("  or the page structure has changed. Please verify manually.")
            print(f"  Current URL: {driver.current_url}")

    except Exception as e:
        print(f"\n⚠️ ERROR during attendance: {e}")

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

        # Step 3: Verify Login Success
        if "dashboard" in driver.current_url.lower():
            print("\n✅ SUCCESS: Bot successfully reached the Dashboard!")
            print(f"Current URL: {driver.current_url}")

            # Step 4: Perform Attendance (Auto-Click)
            perform_attendance(driver)

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