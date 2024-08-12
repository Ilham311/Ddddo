import telebot
import requests
import re
import random
import string
import time
import os
import socket

# Gantilah dengan API Token bot Telegram Anda
API_TOKEN = '5037870628:AAGHVEZoD1U5S5gzJjo1TzNcQQyv22EMaYQ'

bot = telebot.TeleBot(API_TOKEN)

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

    def solve_captcha(self):
        endpoint = "https://turn.seized.live/solve"
        headers = {"Content-Type": "application/json"}
        data = {"sitekey": "0x4AAAAAAALn0BYsCrtFUbm_", "invisible": True, "url": self.url}

        try:
            response = requests.post(endpoint, json=data, headers=headers)

            if response.status_code == 200:
                print(f"Captcha berhasil dipecahkan: {response.json()}")
                verify = self.validate_captcha(response.json()["token"])
                return response.json()
            else:
                print(f"Error: {response.status_code}, {response.text}")
        except Exception as e:
            print(f"Error: {e}")

        return None

    def validate_captcha(self, token):
        headers = self.base_headers.copy()
        response = requests.get(f"https://d0000d.com/dood?op=validate&gc_response={token}", headers=headers)
        return response.text

    def extract_md5_url(self, html_response):
        match = re.search(r"\$\.get\('\/pass_md5([^']+)", html_response)
        return match.group().replace("$.get('", "") if match else None

    def get_data_for_later(self, html_response):
        data_for_later = re.search(r'\?token=([^&]+)&expiry=', html_response)
        return data_for_later.group(1) if data_for_later else None

    def main(self, bot, chat_id):
        bot.send_message(chat_id, "🔄 Memulai proses pengambilan video...")
        response = requests.get(f"{self.url}", headers=self.base_headers)
        html_response = response.text
        bot.send_message(chat_id, "📥 Ekstraksi URL MD5...")
        md5_url = self.extract_md5_url(html_response)
  
        if md5_url is None:
            bot.send_message(chat_id, "🔍 Captcha terdeteksi, mencoba untuk memecahkan...")
            html_response = self.solve_captcha()
            response = requests.get(f"{self.url}", headers=self.base_headers)
            html_response = response.text
            md5_url = self.extract_md5_url(html_response)

            if md5_url is None:
                bot.send_message(chat_id, "❌ Gagal mengekstrak URL MD5. Proses dihentikan.")
                exit()
              
        bot.send_message(chat_id, "✅ URL MD5 berhasil diekstrak")
        data_for_later = self.get_data_for_later(html_response)

        md5_url = f"https://d0000d.com{md5_url}"

        response = requests.get(f"{md5_url}", headers=self.md5_headers)
        expiry_timestamp = int(time.time() * 1000)

        constructed_url = f"{response.text}{self.generate_random_string(10)}?token={data_for_later}&expiry={expiry_timestamp}#.mp4"
        bot.send_message(chat_id, "🔗 URL video berhasil dibangun dan siap diunduh...")
        return constructed_url

    def download_video(self, url, bot, chat_id):
        filename = self.generate_random_string(10) + ".mp4"
        bot.send_message(chat_id, "⬇️ Mengunduh video...")
        with requests.get(url, stream=True, headers=self.base_headers) as r:
            r.raise_for_status()
            with open(filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        bot.send_message(chat_id, "✅ Video berhasil diunduh.")
        return filename

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Halo! Kirimkan link Doodstream untuk mengunduh video.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    doodstream_url = message.text

    doodstream = Doodstream(doodstream_url)
    constructed_url = doodstream.main(bot, message.chat.id)
    video_filename = doodstream.download_video(constructed_url, bot, message.chat.id)

    with open(video_filename, 'rb') as video:
        bot.send_video(message.chat.id, video)

    # Menghapus file setelah diunggah
    os.remove(video_filename)
    bot.send_message(message.chat.id, f"🗑️ File {video_filename} telah dihapus setelah diunggah.")

# Memulai bot
print("Bot sedang berjalan...")
bot.polling()
