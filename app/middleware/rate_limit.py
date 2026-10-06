"""
Front-line per-IP rate limiter (before_request).

Blocks a client IP that fires two requests less than `MIN_INTERVAL` seconds apart,
returning 429. Registered on the app factory via `register_rate_limiter(app)`.

Exemptions (Option B):
  - CORS preflight (`OPTIONS`) requests are always allowed.
  - Disabled entirely when `app.config["TESTING"]` is true (so pytest isn't throttled).
  - Can be toggled off at runtime via env `RATE_LIMIT_ENABLED=false`.
"""
import time
import logging
import threading
from flask import request, jsonify

# Memori internal untuk mencatat IP dan waktu request terakhir
LAST_REQUEST_TIMES = {}

# Minimum jeda antar-request per IP (detik).
MIN_INTERVAL = 1

# 🆕 2. LETAKKAN FUNGSI PEMBERSIH DI SINI (Di luar Factory Function)
def start_ram_cleanup_worker():
    """Menjalankan background thread untuk menyapu IP sampah dari RAM setiap 10 menit."""
    def cleanup_logic():
        while True:
            time.sleep(600)  # Berjalan setiap 10 menit (600 detik)
            current_time = time.time()
            
            # Cari IP yang sudah tidak aktif/mengirim request lebih dari 5 menit (300 detik)
            expired_ips = [
                ip for ip, last_time in LAST_REQUEST_TIMES.items()
                if current_time - last_time > 300
            ]
            
            # Hapus IP tersebut dari Dictionary memori global
            for ip in expired_ips:
                if ip in LAST_REQUEST_TIMES:
                    del LAST_REQUEST_TIMES[ip]
            
            if expired_ips:
                logging.info(f"🧹 [RAM Cleanup] Berhasil menghapus {len(expired_ips)} IP tidak aktif dari memori.")

    # Jalankan sebagai Daemon Thread agar otomatis mati saat aplikasi Flask dihentikan
    cleanup_thread = threading.Thread(target=cleanup_logic, daemon=True)
    cleanup_thread.start()

def register_rate_limiter(app):
    """Attach the before_request rate limiter to the Flask app."""
    
    # do the cleanup variable in ram so it doens't get bloated
    start_ram_cleanup_worker()
    
    # 🛡️ MIDDLEWARE PERTAHANAN TERDEPAN
    @app.before_request
    def rate_limiter_middleware():
        # (B) Disabled under tests, or when turned off via env flag.
        if app.config.get("TESTING"):
            return None
        if not app.config.get("RATE_LIMIT_ENABLED", True):
            return None

        # (B) CORS preflight must never be blocked.
        if request.method == "OPTIONS":
            return None

        client_ip = request.remote_addr
        current_time = time.time()

        # 1. Cek jeda waktu di pintu masuk utama
        if client_ip in LAST_REQUEST_TIMES:
            last_request_time = LAST_REQUEST_TIMES[client_ip]
            time_elapsed = current_time - last_request_time

            # 🚫 Jika si orang iseng menembak terlalu cepat (< 500ms), LANGSUNG DEPAK DI SINI!
            if time_elapsed < MIN_INTERVAL:
                logging.warning(f"Rate limit hit for IP {client_ip} ({time_elapsed:.3f}s < {MIN_INTERVAL}s)")
                return jsonify({
                    "success": False,
                    "message": "Aktivitas terlalu cepat. Request Anda diblokir demi keamanan server."
                }), 429  # Request terhenti di sini, tidak akan pernah sampai ke fungsi route di bawah.

        # 2. Jika lolos, perbarui catatan waktu untuk IP tersebut
        LAST_REQUEST_TIMES[client_ip] = current_time

        # 3. Berikan return None agar Flask melanjutkan request ke route yang dituju
        return None

    return app
