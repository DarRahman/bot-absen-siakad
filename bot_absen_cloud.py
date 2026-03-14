import os
import time
import json
import requests
from datetime import datetime, timezone
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys

def notify_discord(title, message, status="info", file_path=None):
    """
    Sends a professional Embed notification to Discord.
    Comments are in English, but the actual notification content is in Indonesian.
    """
    webhook_url = os.environ.get('DISCORD_WEBHOOK')
    if not webhook_url:
        return

    # Decimal color codes for Discord Embeds
    colors = {"success": 3066993, "error": 15158332, "info": 3447003}
    
    payload = {
        "embeds": [{
            "title": title,
            "description": message,
            "color": colors.get(status, 3447003),
            "footer": {"text": "Sistem Otomatis • STIKOM Poltek Cirebon"},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }]
    }

    try:
        if file_path and os.path.exists(file_path):
            # Send notification with an attached screenshot file
            files = {"file": (file_path, open(file_path, 'rb'))}
            requests.post(webhook_url, data={"payload_json": json.dumps(payload)}, files=files)
        else:
            # Send text-only notification
            requests.post(webhook_url, json=payload)
    except Exception as e:
        print(f"Gagal mengirim notifikasi Discord: {e}")

def setup_driver():
    """Initializes a headless Chrome driver with production-ready settings."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    # Disable location popups to prevent execution blocking
    chrome_options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.geolocation": 2
    })
    return webdriver.Chrome(options=chrome_options)

def perform_login(driver, nim, password):
    """Handles the login process and addresses the specific portal session bug."""
    print("[1] Mengakses halaman login SIAKAD...")
    driver.get("https://siakad.stikompoltekcirebon.ac.id/index.php")
    time.sleep(5)
    
    def submit_data():
        print(f"[*] Memasukkan kredensial login...")
        driver.find_element(By.NAME, "username").clear()
        driver.find_element(By.NAME, "username").send_keys(nim)
        pw_field = driver.find_element(By.NAME, "password")
        pw_field.clear()
        pw_field.send_keys(password)
        pw_field.send_keys(Keys.ENTER)
        time.sleep(10)

    submit_data()
    # Campus portal often requires two login attempts to establish a session
    if "dashboard" not in driver.current_url.lower():
        print("[!] Bug sesi terdeteksi. Melakukan login ulang (Retry)...")
        submit_data()

def main():
    # Fetch credentials from environment variables
    NIM = os.environ.get('NIM_KAMPUS')
    PW = os.environ.get('PW_KAMPUS')
    
    # Calculate current hour in UTC for mode selection
    utc_now = datetime.now(timezone.utc)
    utc_hour = utc_now.hour
    
    # Define Patient Mode for start hours (08:00, 10:30, 13:00 WIB)
    is_patient_mode = utc_hour in [1, 3, 6]
    
    # Set monitoring duration and refresh frequency
    TIMEOUT = 30 * 60 if is_patient_mode else 1
    INTERVAL = 5 * 60 if is_patient_mode else 0
    
    mode_desc = "SABAR (30m)" if is_patient_mode else "INSTAN (1x Cek)"
    print(f"[*] Menjalankan dalam Mode: {mode_desc}")
    
    start_time = time.time()
    driver = setup_driver()
    
    try:
        perform_login(driver, NIM, PW)
        
        if "dashboard" not in driver.current_url.lower():
            notify_discord("❌ Login Gagal", "Bot tidak dapat mengakses Dashboard.", "error")
            return

        print("✅ Berhasil masuk ke Dashboard.")
        # Send initial standby notification (Text only)
        notify_discord("📡 Bot Standby", f"Login sukses. Memulai pemeriksaan dalam **{mode_desc}**.", "info")
        
        while True:
            try:
                # Find the 'ABSEN' button based on class and text
                btn = driver.find_element(By.XPATH, "//a[contains(text(), 'ABSEN') and contains(@class, 'btn-success')]")
                
                if btn:
                    # Attempt to scrape the course name
                    try:
                        matkul = driver.find_element(By.XPATH, "//h3[contains(@class, 'card-category')]").text
                    except:
                        matkul = "Mata Kuliah Aktif"
                    
                    # Scroll to the element and perform the click action
                    driver.execute_script("arguments[0].scrollIntoView();", btn)
                    time.sleep(2)
                    btn.click()
                    
                    print("🚀 Tombol ditemukan dan diklik. Menunggu pembaruan sistem...")
                    time.sleep(12) 
                    
                    # Capture screenshot ONLY upon successful attendance
                    success_ss = "bukti_absen.png"
                    driver.save_screenshot(success_ss)
                    
                    waktu_skrg = datetime.now().strftime('%H:%M:%S WIB')
                    msg = f"**Matkul:** {matkul}\n**Waktu:** {waktu_skrg}\n**Status:** Berhasil Absen Otomatis!"
                    notify_discord("✅ Absen Berhasil", msg, "success", success_ss)
                    return 
            except:
                print(f"[-] Tombol belum muncul pada {datetime.now().strftime('%H:%M:%S')}")
            
            # Logic to break the loop for Instant Mode or Timeout
            if not is_patient_mode or (time.time() - start_time) > TIMEOUT:
                print("[*] Sesi monitoring selesai.")
                break
            
            # Sleep and refresh page for Patient Mode
            time.sleep(INTERVAL)
            driver.refresh()
            time.sleep(5)

    except Exception as e:
        print(f"⚠️ Kesalahan Sistem: {str(e)}")
        # Capture screenshot for debugging purposes on error
        err_ss = "log_kesalahan.png"
        driver.save_screenshot(err_ss)
        notify_discord("⚠️ Error Sistem", f"Terjadi kesalahan teknis: ```{str(e)}```", "error", err_ss)
    finally:
        # Gracefully shut down the driver
        driver.quit()

if __name__ == "__main__":
    main()