import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys

def setup_driver():
    """Initializes the Chrome driver for cloud environment (Headless)."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    # Disable geolocation popups automatically
    chrome_options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.geolocation": 2
    })
    return webdriver.Chrome(options=chrome_options)

def perform_login(driver, nim, password):
    """Handles the login process with retry logic for the double-login bug."""
    driver.get("https://siakad.stikompoltekcirebon.ac.id/index.php")
    time.sleep(3)
    
    def fill_and_submit():
        driver.find_element(By.NAME, "username").clear()
        driver.find_element(By.NAME, "username").send_keys(nim)
        pw_field = driver.find_element(By.NAME, "password")
        pw_field.clear()
        pw_field.send_keys(password)
        pw_field.send_keys(Keys.ENTER)
        time.sleep(7)

    fill_and_submit()
    # Retry if session bug occurs (redirected back to index)
    if "dashboard" not in driver.current_url.lower():
        print("[!] Bug detected: Session not created. Retrying login...")
        fill_and_submit()

def main():
    # Load credentials from GitHub Secrets
    NIM = os.environ.get('NIM_KAMPUS')
    PW = os.environ.get('PW_KAMPUS')
    
    # Configuration: Try for 2.5 hours, refresh every 30 minutes
    TIMEOUT = 2.5 * 3600 # 2.5 hours in seconds
    REFRESH_INTERVAL = 30 * 60 # 30 minutes in seconds
    start_time = time.time()
    
    driver = setup_driver()
    
    try:
        perform_login(driver, NIM, PW)
        
        if "dashboard" not in driver.current_url.lower():
            print("❌ Critical: Login failed after retries.")
            return

        print("✅ Login Successful. Entering monitoring mode...")

        # Monitoring Loop
        while (time.time() - start_time) < TIMEOUT:
            print(f"[*] Checking for attendance button at {time.strftime('%H:%M:%S')}...")
            
            try:
                # Find the link that contains 'aksi absen masuk.php' in the href
                # Based on the inspected HTML element
                attendance_btn = driver.find_element(By.XPATH, "//a[contains(@href, 'aksi absen masuk.php')]")
                
                if attendance_btn:
                    print("🚀 Attendance button FOUND! Clicking now...")
                    attendance_btn.click()
                    time.sleep(5) # Wait for processing
                    print("✅ SUCCESS: Attendance has been recorded automatically!")
                    return # Exit script after success
            
            except:
                print(f"[-] Button not found. Waiting 30 minutes before next refresh...")
            
            time.sleep(REFRESH_INTERVAL)
            driver.refresh()
            time.sleep(5)

        print("⌛ Timeout reached: The attendance button never appeared.")

    except Exception as e:
        print(f"⚠️ Error: {str(e)}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
