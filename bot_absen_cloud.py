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
    """Sends a professional notification with optional screenshot."""
    webhook_url = os.environ.get('DISCORD_WEBHOOK')
    if not webhook_url: return
    colors = {"success": 3066993, "error": 15158332, "info": 3447003}
    payload = {
        "embeds": [{
            "title": title,
            "description": message,
            "color": colors.get(status, 3447003),
            "footer": {"text": "STIKOM Poltek Cirebon • Evidence Report"},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }]
    }
    try:
        if file_path and os.path.exists(file_path):
            files = {"file": (file_path, open(file_path, 'rb'))}
            requests.post(webhook_url, data={"payload_json": json.dumps(payload)}, files=files)
        else:
            requests.post(webhook_url, json=payload)
    except Exception as e:
        print(f"Failed to send Discord notification: {e}")

def setup_driver():
    """Initializes headless Chrome with high resolution."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_experimental_option("prefs", {"profile.default_content_setting_values.geolocation": 2})
    return webdriver.Chrome(options=chrome_options)

def perform_login(driver, nim, password):
    """Handles authentication with session retry logic."""
    print("[1] Mengakses halaman login SIAKAD...")
    driver.get("https://siakad.stikompoltekcirebon.ac.id/index.php")
    time.sleep(5)
    def submit_credentials():
        driver.find_element(By.NAME, "username").clear()
        driver.find_element(By.NAME, "username").send_keys(nim)
        pw_field = driver.find_element(By.NAME, "password")
        pw_field.clear()
        pw_field.send_keys(password)
        pw_field.send_keys(Keys.ENTER)
        time.sleep(10)
    submit_credentials()
    if "dashboard" not in driver.current_url.lower():
        submit_credentials()

def main():
    NIM = os.environ.get('NIM_KAMPUS')
    PW = os.environ.get('PW_KAMPUS')
    utc_hour = datetime.now(timezone.utc).hour
    is_patient_mode = utc_hour in [1, 3, 6]
    TIMEOUT = 30 * 60 if is_patient_mode else 1
    INTERVAL = 5 * 60 if is_patient_mode else 0
    start_time = time.time()
    driver = setup_driver()
    
    try:
        perform_login(driver, NIM, PW)
        if "dashboard" not in driver.current_url.lower():
            notify_discord("❌ Login Gagal", "Bot tidak bisa masuk ke Dashboard.", "error")
            return

        # --- TEST SNAPSHOT ---
        # Ambil screenshot dashboard segera setelah login sukses
        print("✅ Dashboard accessed. Taking initial snapshot...")
        time.sleep(3) # Tunggu grafik dashboard muncul
        initial_ss = "dashboard_status.png"
        driver.save_screenshot(initial_ss)
        
        mode_text = "SABAR (30m)" if is_patient_mode else "INSTAN (1x Cek)"
        notify_discord("📡 Bot Standby", f"Login Berhasil. Mode: **{mode_text}**.\nTerlampir foto kondisi dashboard saat ini.", "info", initial_ss)
        # ---------------------
        
        while True:
            try:
                btn = driver.find_element(By.XPATH, "//a[contains(text(), 'ABSEN') and contains(@class, 'btn-success')]")
                if btn:
                    try: matkul = driver.find_element(By.XPATH, "//h3[contains(@class, 'card-category')]").text
                    except: matkul = "Mata Kuliah Aktif"
                    driver.execute_script("arguments[0].scrollIntoView();", btn)
                    time.sleep(2)
                    btn.click()
                    time.sleep(10)
                    
                    success_ss = "attendance_success.png"
                    driver.save_screenshot(success_ss)
                    msg = f"**Matkul:** {matkul}\n**Jam:** {time.strftime('%H:%M:%S WIB')}\n**Status:** Berhasil Absen!"
                    notify_discord("✅ Absen Berhasil", msg, "success", success_ss)
                    return 
            except:
                print(f"[-] Tombol belum ditemukan.")
            
            if not is_patient_mode or (time.time() - start_time) > TIMEOUT:
                print("[*] Sesi monitoring berakhir.")
                break
            time.sleep(INTERVAL); driver.refresh(); time.sleep(5)

    except Exception as e:
        err_ss = "error_log.png"
        driver.save_screenshot(err_ss)
        notify_discord("⚠️ Error Sistem", f"Kesalahan: ```{str(e)}```", "error", err_ss)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()