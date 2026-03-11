import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys

def notify_discord(message, status="info"):
    """Sends an embedded notification to Discord.
    Status 'success' = Green, 'error' = Red, 'info' = Blue.
    """
    webhook_url = os.environ.get('DISCORD_WEBHOOK')
    if not webhook_url:
        return

    # Color mapping: Green (3066993), Red (15158332), Blue (3447003)
    colors = {"success": 3066993, "error": 15158332, "info": 3447003}
    color = colors.get(status, 3447003)
    
    payload = {
        "embeds": [{
            "title": "Sistem Absensi SIAKAD",
            "description": message,
            "color": color,
            "footer": {"text": "Otomatisasi GitHub Actions • STIKOM Poltek Cirebon"},
            "timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        }]
    }
    try:
        requests.post(webhook_url, json=payload)
    except Exception as e:
        print(f"Gagal mengirim notif Discord: {e}")

def setup_driver():
    """Initializes Chrome in headless mode for cloud environments."""
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
    """Handles authentication and retries for the double-login bug."""
    print("[1] Membuka halaman login SIAKAD...")
    driver.get("https://siakad.stikompoltekcirebon.ac.id/index.php")
    time.sleep(5)
    
    def fill_form():
        print(f"[*] Memasukkan NIM: {nim}...")
        driver.find_element(By.NAME, "username").clear()
        driver.find_element(By.NAME, "username").send_keys(nim)
        pw_field = driver.find_element(By.NAME, "password")
        pw_field.clear()
        pw_field.send_keys(password)
        pw_field.send_keys(Keys.ENTER)
        time.sleep(10)

    fill_form()
    # Check if still on index (campus web bug)
    if "dashboard" not in driver.current_url.lower():
        print("[!] Bug terdeteksi: Sesi tidak dibuat. Mencoba login ulang...")
        fill_form()

def main():
    NIM = os.environ.get('NIM_KAMPUS')
    PW = os.environ.get('PW_KAMPUS')
    
    # Send 'Started' notification to Discord
    notify_discord(f"🤖 **Bot Mulai Bekerja**\nNIM: `{NIM}`\nStatus: Mencoba Login...", "info")
    
    # 2.5 hours monitoring window, refresh every 30 minutes
    TIMEOUT = 2.5 * 3600 
    REFRESH_INTERVAL = 30 * 60 
    start_time = time.time()
    
    driver = setup_driver()
    
    try:
        perform_login(driver, NIM, PW)
        
        if "dashboard" not in driver.current_url.lower():
            print("❌ Login Gagal.")
            notify_discord(f"❌ **Login Gagal!**\nNIM: `{NIM}`\nBot berhenti karena tidak bisa masuk dashboard.", "error")
            return

        print("✅ Login Berhasil.")

        # Main Monitoring Loop
        while (time.time() - start_time) < TIMEOUT:
            current_time = time.strftime('%H:%M:%S')
            print(f"[*] Mencari tombol absen pada pukul {current_time}...")
            
            try:
                # Find button using professional XPath
                attendance_btn = driver.find_element(By.XPATH, "//a[contains(text(), 'ABSEN') and contains(@class, 'btn-success')]")
                
                if attendance_btn:
                    print("🚀 Tombol ABSEN ditemukan! Sedang mengklik...")
                    driver.execute_script("arguments[0].scrollIntoView();", attendance_btn)
                    time.sleep(2)
                    attendance_btn.click()
                    time.sleep(10)
                    
                    # Send 'Success' notification
                    success_msg = f"✅ **Absen Berhasil!**\nNIM: `{NIM}`\nStatus: Sudah diklik otomatis oleh Bot."
                    notify_discord(success_msg, "success")
                    print(success_msg)
                    return 
            except:
                print("[-] Tombol belum muncul.")
            
            # Wait for 30 minutes before next check
            print(f"Menunggu {REFRESH_INTERVAL/60} menit sebelum refresh halaman...")
            time.sleep(REFRESH_INTERVAL)
            driver.refresh()
            time.sleep(5)

        # If timeout reached
        timeout_msg = f"⌛ **Sesi Berakhir (Timeout)**\nNIM: `{NIM}`\nTombol absen tidak ditemukan sampai batas waktu berakhir."
        notify_discord(timeout_msg, "info")
        print(timeout_msg)

    except Exception as e:
        err_msg = f"⚠️ **Kesalahan Fatal Sistem:**\n```{str(e)}```"
        notify_discord(err_msg, "error")
        print(err_msg)
    finally:
        print("Menutup browser dan mengakhiri script.")
        driver.quit()

if __name__ == "__main__":
    main()
