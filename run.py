from pyrogram import Client, filters
import requests
import re
import random
import string
import time
import os
import socket

API_ID = 961780  # Gantilah dengan API ID Anda
API_HASH = "bbbfa43f067e1e8e2fb41f334d32a6a7"  # Gantilah dengan API Hash Anda
BOT_TOKEN = "6324930447:AAEcHZLONpDPT5vg1Wmf1X9_C6OJJZc2L6Y"  # Gantilah dengan token bot Telegram Anda

app = Client("doodstream_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

class Doodstream:
    def __init__(self, doodstream_url):
        self.doodstream_url = doodstream_url
        self.url = f"https://d0000d.com/e/{doodstream_url.split('/e/')[1]}"
        self.my_ip = self.get_ip_address()

        self.base_headers = {
            "Host": "d0000d.com",
            "Connection": "keep-alive",
            "sec-ch-ua": "\"Not_A Brand\";v=\"8\", \"Chromium\";v=\"120\", \"Google Chrome\";v=\"120\"",
            "DNT": "1",
            "sec-ch-ua-mobile": "?0",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "sec-ch-ua-platform": "\"macOS\"",
            "Accept": "*/*",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Fetch-Mode": "no-cors",
            "Sec-Fetch-Dest": "video",
            "Referer": self.url,
            "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
            "X-Requested-With": "XMLHttpRequest",
            "X-Forwarded-For": self.my_ip
        }

        self.md5_headers = {
            'Accept': '*/*',
            'Accept-Language': 'en-GB,en;q=0.6',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Cookie': 'lang=1',
            'Host': 'd0000d.com',
            'Pragma': 'no-cache',
            'Referer': self.url,
            'sec-ch-ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Brave";v="122"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-GPC': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest',
            "X-Forwarded-For": self.my_ip,
        }

    def get_ip_address(self):
        # Mendapatkan alamat IP lokal
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        return local_ip

    def generate_random_string(self, length):
        characters = string.ascii_letters + string.digits
        return ''.join(random.choice(characters) for _ in range(length))

    def extract_md5_url(self, html_response):
        match = re.search(r"\$\.get\('\/pass_md5([^']+)", html_response)
        return match.group().replace("$.get('", "") if match else None

    def get_data_for_later(self, html_response):
        data_for_later = re.search(r'\?token=([^&]+)&expiry=', html_response)
        return data_for_later.group(1) if data_for_later else None

    def main(self, chat_id):
        app.send_message(chat_id, "🔄 Memulai proses pengambilan video...")
        response = requests.get(f"{self.url}", headers=self.base_headers)
        html_response = response.text
        app.send_message(chat_id, "📥 Ekstraksi URL MD5...")
        md5_url = self.extract_md5_url(html_response)
  
        if md5_url is None:
            app.send_message(chat_id, "❌ Gagal mengekstrak URL MD5. Proses dihentikan.")
            return None
              
        app.send_message(chat_id, "✅ URL MD5 berhasil diekstrak")
        data_for_later = self.get_data_for_later(html_response)

        md5_url = f"https://d0000d.com{md5_url}"

        response = requests.get(f"{md5_url}", headers=self.md5_headers)
        expiry_timestamp = int(time.time() * 1000)

        constructed_url = f"{response.text}{self.generate_random_string(10)}?token={data_for_later}&expiry={expiry_timestamp}#.mp4"
        app.send_message(chat_id, "🔗 URL video berhasil dibangun dan siap diunduh...")
        return constructed_url

    def download_video(self, url, chat_id):
        filename = self.generate_random_string(10) + ".mp4"
        app.send_message(chat_id, "⬇️ Mengunduh video...")
        with requests.get(url, stream=True, headers=self.base_headers) as r:
            r.raise_for_status()
            with open(filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        app.send_message(chat_id, "✅ Video berhasil diunduh.")
        return filename

@app.on_message(filters.command(['start']))
def send_welcome(client, message):
    message.reply_text("Halo! Kirimkan link Doodstream untuk mengunduh video.")

@app.on_message(filters.text)
def handle_message(client, message):
    doodstream_url = message.text

    doodstream = Doodstream(doodstream_url)
    constructed_url = doodstream.main(message.chat.id)
    if constructed_url:
        video_filename = doodstream.download_video(constructed_url, message.chat.id)

        with open(video_filename, 'rb') as video:
            client.send_video(message.chat.id, video)

        # Menghapus file setelah diunggah
        os.remove(video_filename)
        client.send_message(message.chat.id, f"🗑️ File {video_filename} telah dihapus setelah diunggah.")

# Memulai bot
print("Bot sedang berjalan...")
app.run()
