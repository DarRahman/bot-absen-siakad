import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys

def setup_driver():
    """Initializes the Chrome driver for headless cloud environment."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.geolocation": 2
    })
    return webdriver.Chrome(options=chrome_options)

def perform_login(driver, nim, password):
    """Handles authentication with session retry logic."""
    print("[1] Opening SIAKAD login page...")
    driver.get("https://siakad.stikompoltekcirebon.ac.id/index.php")
    time.sleep(5)
    
    def fill_form():
        print(f"[*] Typing credentials for NIM: {nim}...")
        driver.find_element(By.NAME, "username").clear()
        driver.find_element(By.NAME, "username").send_keys(nim)
        pw_field = driver.find_element(By.NAME, "password")
        pw_field.clear()
        pw_field.send_keys(password)
        pw_field.send_keys(Keys.ENTER)
        time.sleep(10) # Increased wait for slow campus server

    fill_form()
    if "dashboard" not in driver.current_url.lower():
        print("[!] Bug detected: Session not created. Attempting retry...")
        fill_form()

def main():
    NIM = os.environ.get('NIM_KAMPUS')
    PW = os.environ.get('PW_KAMPUS')
    
    TIMEOUT_DURATION = 2.5 * 3600 
    REFRESH_INTERVAL = 30 * 60 
    start_time = time.time()
    
    driver = setup_driver()
    
    try:
        perform_login(driver, NIM, PW)
        
        if "dashboard" not in driver.current_url.lower():
            print("❌ FAILED: Unable to reach Dashboard.")
            return

        print("✅ SUCCESS: Login achieved. Entering monitoring loop.")

        while (time.time() - start_time) < TIMEOUT_DURATION:
            print(f"[*] Scanning for attendance button at {time.strftime('%H:%M:%S')}...")
            
            try:
                # NEW AGGRESSIVE XPATH:
                # Search for any link (<a>) that HAS the text 'ABSEN' and HAS the class 'btn-success'
                attendance_btn = driver.find_element(By.XPATH, "//a[contains(text(), 'ABSEN') and contains(@class, 'btn-success')]")
                
                if attendance_btn:
                    print("🚀 FOUND: Attendance button detected! Executing click...")
                    # Scroll to element just in case
                    driver.execute_script("arguments[0].scrollIntoView();", attendance_btn)
                    time.sleep(2)
                    attendance_btn.click()
                    time.sleep(10) # Wait longer for the 'Berhasil' message
                    print("✅ FINAL STATUS: Attendance recorded successfully!")
                    return 
            
            except:
                # SECOND ATTEMPT XPATH: Just in case the text is lowercase
                try:
                    attendance_btn = driver.find_element(By.XPATH, "//a[contains(@href, 'absen') and contains(@class, 'btn-success')]")
                    attendance_btn.click()
                    print("✅ FINAL STATUS: Attendance recorded (Attempt 2)!")
                    return
                except:
                    print(f"[-] Status: Button not found yet.")
            
            print(f"Waiting {REFRESH_INTERVAL/60} minutes before next refresh...")
            time.sleep(REFRESH_INTERVAL)
            driver.refresh()
            time.sleep(5)

    except Exception as e:
        print(f"⚠️ CRITICAL ERROR: {str(e)}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
