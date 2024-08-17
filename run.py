import telebot
import aiohttp
import asyncio
import re
import random
import string
import time
import os
import socket

API_TOKEN = '5037870628:AAGHVEZoD1U5S5gzJjo1TzNcQQyv22EMaYQ'  # Ganti dengan API Token bot Telegram Anda

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
            "Accept-Language": "en-US,en;q=0.9",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
            "X-Requested-With": "XMLHttpRequest",
            "X-Forwarded-For": self.my_ip
        }

    def get_ip_address(self):
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        return local_ip

    def generate_random_string(self, length):
        characters = string.ascii_letters + string.digits
        return ''.join(random.choice(characters) for _ in range(length))

    async def solve_captcha(self):
        endpoint = "https://turn.seized.live/solve"
        headers = {"Content-Type": "application/json"}
        data = {"sitekey": "0x4AAAAAAALn0BYsCrtFUbm_", "invisible": True, "url": self.url}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(endpoint, json=data, headers=headers) as response:
                    if response.status == 200:
                        response_json = await response.json()
                        token = response_json.get("token")
                        if token:
                            return await self.validate_captcha(token)
                    else:
                        print(f"Error: {response.status}, {await response.text()}")
        except Exception as e:
            print(f"Error: {e}")
        return None

    async def validate_captcha(self, token):
        headers = self.base_headers.copy()
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://d0000d.com/dood?op=validate&gc_response={token}", headers=headers) as response:
                return await response.text()

    def extract_md5_url(self, html_response):
        match = re.search(r"\$\.get\('\/pass_md5([^']+)", html_response)
        return match.group().replace("$.get('", "") if match else None

    def get_data_for_later(self, html_response):
        data_for_later = re.search(r'\?token=([^&]+)&expiry=', html_response)
        return data_for_later.group(1) if data_for_later else None

    async def main(self, bot, chat_id):
        try:
            msg = bot.send_message(chat_id, "🔄 Memulai proses pengambilan video...")
            async with aiohttp.ClientSession() as session:
                async with session.get(self.url, headers=self.base_headers) as response:
                    html_response = await response.text()
                
                bot.edit_message_text("📥 Ekstraksi URL MD5...", chat_id, msg.message_id)
                md5_url = self.extract_md5_url(html_response)
    
                if md5_url is None:
                    bot.edit_message_text("🔍 Captcha terdeteksi, mencoba untuk memecahkan...", chat_id, msg.message_id)
                    captcha_response = await self.solve_captcha()
                    async with session.get(self.url, headers=self.base_headers) as response:
                        html_response = await response.text()
                    md5_url = self.extract_md5_url(html_response)

                    if md5_url is None:
                        bot.edit_message_text("❌ Gagal mengekstrak URL MD5. Proses dihentikan.", chat_id, msg.message_id)
                        return None
              
                bot.edit_message_text("✅ URL MD5 berhasil diekstrak", chat_id, msg.message_id)
                data_for_later = self.get_data_for_later(html_response)
    
                md5_url = f"https://d0000d.com{md5_url}"
    
                async with session.get(md5_url, headers=self.base_headers) as response:
                    response_text = await response.text()
                    constructed_url = f"{response_text}{self.generate_random_string(10)}?token={data_for_later}&expiry={int(time.time() * 1000)}#.mp4"
                
                bot.edit_message_text("🔗 URL video berhasil dibangun dan siap diunduh...", chat_id, msg.message_id)
                return constructed_url
        except Exception as e:
            bot.edit_message_text(f"❌ Terjadi kesalahan: {str(e)}", chat_id, msg.message_id)
            return None

    async def download_video(self, url, bot, chat_id):
        filename = self.generate_random_string(10) + ".mp4"
        try:
            msg = bot.send_message(chat_id, "⬇️ Mengunduh video...")
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=3600)) as session:
                async with session.get(url, headers=self.base_headers) as response:
                    response.raise_for_status()
                    with open(filename, 'wb') as f:
                        while True:
                            chunk = await response.content.read(1024 * 1024)  # 1MB per chunk
                            if not chunk:
                                break
                            f.write(chunk)

            bot.edit_message_text("✅ Video berhasil diunduh.", chat_id, msg.message_id)
            return filename
        except Exception as e:
            bot.edit_message_text(f"❌ Gagal mengunduh video: {str(e)}", chat_id, msg.message_id)
            return None

    async def upload_video(self, filename, bot, chat_id):
        try:
            with open(filename, 'rb') as video:
                bot.send_video(chat_id, video)  # Telegram mendukung unggahan hingga 2GB
            os.remove(filename)
            bot.send_message(chat_id, f"🗑️ File {filename} telah dihapus setelah diunggah.")
        except Exception as e:
            bot.send_message(chat_id, f"❌ Gagal mengunggah video: {str(e)}")

async def handle_message(message):
    doodstream_url = message.text
    if not doodstream_url.startswith("https://doodstream.com/e/"):
        bot.send_message(message.chat.id, "❌ Harap kirimkan link Doodstream yang valid.")
        return

    doodstream = Doodstream(doodstream_url)
    constructed_url = await doodstream.main(bot, message.chat.id)
    
    if constructed_url:
        video_filename = await doodstream.download_video(constructed_url, bot, message.chat.id)
        
        if video_filename:
            await doodstream.upload_video(video_filename, bot, message.chat.id)
        else:
            bot.send_message(message.chat.id, "❌ Tidak dapat mengunduh video.")
    else:
        bot.send_message(message.chat.id, "❌ Tidak dapat membangun URL video.")

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Halo! Kirimkan perintah /dood diikuti dengan link Doodstream untuk mengunduh video.")

@bot.message_handler(commands=['dood'])
def handle_dood_command(message):
    url = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None
    if url:
        asyncio.run(handle_message(message))
    else:
        bot.reply_to(message, "❌ Harap kirimkan link Doodstream setelah perintah /dood.")

# Memulai bot
print("Bot sedang berjalan...")
bot.polling()
