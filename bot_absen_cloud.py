import os
import time
import requests
from datetime import datetime, timezone # Modern datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys

def notify_discord(title, message, status="info"):
    """Sends a professional notification to Discord."""
    webhook_url = os.environ.get('DISCORD_WEBHOOK')
    if not webhook_url: return
    colors = {"success": 3066993, "error": 15158332, "info": 3447003}
    payload = {
        "embeds": [{
            "title": title,
            "description": message,
            "color": colors.get(status, 3447003),
            "footer": {"text": "STIKOM Poltek Cirebon Automation"},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }]
    }
    try: requests.post(webhook_url, json=payload)
    except: pass

def setup_driver():
    """Initializes headless Chrome for Cloud environment."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_experimental_option("prefs", {"profile.default_content_setting_values.geolocation": 2})
    return webdriver.Chrome(options=chrome_options)

def perform_login(driver, nim, password):
    """Handles login with double-login bug retry."""
    print("[1] Mengakses halaman login...")
    driver.get("https://siakad.stikompoltekcirebon.ac.id/index.php")
    time.sleep(5)
    def submit():
        driver.find_element(By.NAME, "username").clear()
        driver.find_element(By.NAME, "username").send_keys(nim)
        pw = driver.find_element(By.NAME, "password")
        pw.clear()
        pw.send_keys(password)
        pw.send_keys(Keys.ENTER)
        time.sleep(10)
    submit()
    if "dashboard" not in driver.current_url.lower():
        print("[!] Mencoba login ulang...")
        submit()

def main():
    NIM = os.environ.get('NIM_KAMPUS')
    PW = os.environ.get('PW_KAMPUS')
    
    # Use modern timezone-aware datetime to avoid warnings
    utc_now = datetime.now(timezone.utc)
    utc_hour = utc_now.hour
    
    # Monitoring starts at UTC 1 (08:00), 3 (10:30), 6 (13:00)
    is_patient_mode = utc_hour in [1, 3, 6]
    
    TIMEOUT = 30 * 60 if is_patient_mode else 1
    INTERVAL = 5 * 60 if is_patient_mode else 0
    
    mode_text = "SABAR (30m)" if is_patient_mode else "INSTAN (1x Cek)"
    print(f"[*] Menjalankan Mode: {mode_text}")
    
    start_time = time.time()
    driver = setup_driver()
    
    try:
        perform_login(driver, NIM, PW)
        
        if "dashboard" not in driver.current_url.lower():
            notify_discord("❌ Login Gagal", "Bot tidak bisa masuk ke Dashboard.", "error")
            return

        # NOTIFIKASI BARU: Biar kamu tahu bot sudah standby di Dashboard
        print("✅ Berhasil masuk ke Dashboard.")
        notify_discord("📡 Bot Standby", f"Berhasil Login. Memulai pemeriksaan dalam **{mode_text}**.", "info")
        
        while True:
            try:
                # Find green ABSEN button
                btn = driver.find_element(By.XPATH, "//a[contains(text(), 'ABSEN') and contains(@class, 'btn-success')]")
                if btn:
                    try: matkul = driver.find_element(By.XPATH, "//h3[contains(@class, 'card-category')]").text
                    except: matkul = "Mata Kuliah Aktif"
                    
                    driver.execute_script("arguments[0].scrollIntoView();", btn)
                    time.sleep(2)
                    btn.click()
                    time.sleep(5)
                    
                    now_wib = time.strftime('%H:%M:%S WIB')
                    notify_discord("✅ Absen Berhasil", f"**Matkul:** {matkul}\n**Jam:** {now_wib}\nStatus: Berhasil diklik otomatis.", "success")
                    return 
            except:
                print(f"[-] Tombol belum ada.")
            
            if not is_patient_mode or (time.time() - start_time) > TIMEOUT:
                if not is_patient_mode:
                    print("[*] Mode Instan selesai.")
                break
            
            time.sleep(INTERVAL)
            driver.refresh()
            time.sleep(5)

    except Exception as e:
        print(f"Error: {e}")
        notify_discord("⚠️ Error Sistem", f"Terjadi kesalahan: ```{str(e)}```", "error")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
