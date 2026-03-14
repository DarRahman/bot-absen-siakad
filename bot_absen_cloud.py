import os
import time
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys

def notify_discord(title, message, status="info"):
    """
    Sends a professional Embed notification to Discord.
    Status colors: Green for success, Red for error, Blue for info.
    """
    webhook_url = os.environ.get('DISCORD_WEBHOOK')
    if not webhook_url:
        return

    # Discord color decimal codes
    colors = {"success": 3066993, "error": 15158332, "info": 3447003}
    
    payload = {
        "embeds": [{
            "title": title,
            "description": message,
            "color": colors.get(status, 3447003),
            "footer": {"text": "STIKOM Poltek Cirebon • Automated Service"},
            "timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        }]
    }
    try:
        requests.post(webhook_url, json=payload)
    except Exception as e:
        print(f"Failed to send Discord notification: {e}")

def setup_driver():
    """Initializes a headless Chrome instance optimized for Cloud environments."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    # Automatically block geolocation popups to prevent script hang
    chrome_options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.geolocation": 2
    })
    return webdriver.Chrome(options=chrome_options)

def perform_login(driver, nim, password):
    """Handles the authentication process with session retry logic."""
    print("[1] Mengakses halaman login SIAKAD...")
    driver.get("https://siakad.stikompoltekcirebon.ac.id/index.php")
    time.sleep(5)
    
    def submit_credentials():
        print(f"[*] Memasukkan kredensial...")
        driver.find_element(By.NAME, "username").clear()
        driver.find_element(By.NAME, "username").send_keys(nim)
        pw_field = driver.find_element(By.NAME, "password")
        pw_field.clear()
        pw_field.send_keys(password)
        pw_field.send_keys(Keys.ENTER)
        time.sleep(10)

    submit_credentials()
    
    # Check for the specific 'double login' bug of the campus portal
    if "dashboard" not in driver.current_url.lower():
        print("[!] Sesi gagal dibuat. Melakukan login ulang (Retry)...")
        submit_credentials()

def main():
    # Load secrets from environment variables
    NIM = os.environ.get('NIM_KAMPUS')
    PW = os.environ.get('PW_KAMPUS')
    
    # Determine Mode based on current UTC hour (WIB - 7)
    # Start windows (08:00, 10:30, 13:00) correspond to UTC (1, 3, 6)
    utc_hour = datetime.utcnow().hour
    is_patient_mode = utc_hour in [1, 3, 6]
    
    # Configuration: 30-min monitoring for starts, instant check for ends
    TIMEOUT = 30 * 60 if is_patient_mode else 1
    INTERVAL = 5 * 60 if is_patient_mode else 0
    
    print(f"[*] Mode: {'SABAR (30m)' if is_patient_mode else 'INSTAN (1x Cek)'}")
    start_time = time.time()
    driver = setup_driver()
    
    try:
        perform_login(driver, NIM, PW)
        
        if "dashboard" not in driver.current_url.lower():
            notify_discord("❌ Login Gagal", "Sistem tidak dapat mengakses Dashboard SIAKAD.", "error")
            return

        print("✅ Berhasil masuk ke Dashboard.")
        
        while True:
            try:
                # Search for the green 'ABSEN' button link
                btn = driver.find_element(By.XPATH, "//a[contains(text(), 'ABSEN') and contains(@class, 'btn-success')]")
                
                if btn:
                    # Scrape the course name from the card title
                    try:
                        matkul = driver.find_element(By.XPATH, "//h3[contains(@class, 'card-category')]").text
                    except:
                        matkul = "Tidak Terdeteksi"
                    
                    # Scroll and execute click
                    driver.execute_script("arguments[0].scrollIntoView();", btn)
                    time.sleep(2)
                    btn.click()
                    time.sleep(5)
                    
                    # Prepare and send success notification
                    waktu_absen = time.strftime('%H:%M:%S WIB')
                    msg = f"**Mata Kuliah:** {matkul}\n**Jam:** {waktu_absen}\n**Status:** Absen Berhasil Diklik"
                    notify_discord("✅ Absen Otomatis Berhasil", msg, "success")
                    print(f"[!] {msg}")
                    return 
            except:
                print(f"[-] Tombol belum ditemukan pada {time.strftime('%H:%M:%S')}")
            
            # Exit loop if instant mode or timeout reached
            if not is_patient_mode or (time.time() - start_time) > TIMEOUT:
                print("[*] Sesi monitoring berakhir.")
                break
            
            time.sleep(INTERVAL)
            driver.refresh()
            time.sleep(5)

    except Exception as e:
        print(f"⚠️ Error: {str(e)}")
        notify_discord("⚠️ Kesalahan Sistem", f"Terjadi error: ```{str(e)}```", "error")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
