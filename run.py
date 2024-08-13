import telebot
import aiohttp
import asyncio
import re
import random
import string
import time
import os 
import requests
import socket

API_TOKEN = '6324930447:AAEK_w2_6XELCbkpVLwPN0_Sm4pfaZYv1G0'
bot = telebot.TeleBot(API_TOKEN)

def get_progress_bar(percent):
    bar_length = 40
    filled_length = int(bar_length * percent // 100)
    bar = '█' * filled_length + '-' * (bar_length - filled_length)
    return f"[{bar}] {percent:.2f}%"

def format_size(size):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"

class Doodstream:
    def __init__(self, doodstream_url):
        self.doodstream_url = doodstream_url
        self.url = f"https://d0000d.com/e/{doodstream_url.split('/e/')[1]}"
        self.my_ip = self.get_my_ip()

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

    def generate_random_string(self, length):
        characters = string.ascii_letters + string.digits
        return ''.join(random.choice(characters) for _ in range(length))

    def get_my_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0)
        try:
            s.connect(('10.254.254.254', 1))
            ip = s.getsockname()[0]
        except Exception:
            ip = '127.0.0.1'
        finally:
            s.close()
        return ip

    async def solve_captcha(self):
        endpoint = "https://turn.seized.live/solve"
        headers = {"Content-Type": "application/json"}
        data = {"sitekey": "0x4AAAAAAALn0BYsCrtFUbm_", "invisible": True, "url": self.url}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(endpoint, json=data, headers=headers) as response:
                    if response.status == 200:
                        print(f"captcha solved: {await response.json()}")
                        verify = await self.validate_captcha((await response.json())["token"])
                        return await response.json()
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

    async def download_video(self, url, bot, chat_id):
        filename = self.generate_random_string(10) + ".mp4"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.base_headers) as response:
                    total_size = int(response.headers.get('Content-Length', 0))
                    downloaded_size = 0

                    msg = bot.send_message(chat_id, f"⬇️ Mengunduh video...\n{get_progress_bar(0)} 0.00%")

                    with open(filename, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            if not chunk:
                                break
                            f.write(chunk)
                            downloaded_size += len(chunk)
                            percent = (downloaded_size / total_size) * 100
                            bot.edit_message_text(
                                f"⬇️ Mengunduh video...\n{get_progress_bar(percent)} {percent:.2f}%\n"
                                f"Ukuran: {format_size(downloaded_size)}/{format_size(total_size)}",
                                chat_id, msg.message_id
                            )

            bot.edit_message_text("✅ Video berhasil diunduh.", chat_id, msg.message_id)
            return filename
        except Exception as e:
            bot.edit_message_text(f"❌ Gagal mengunduh video: {str(e)}", chat_id, msg.message_id)
            return None

    async def upload_video(self, filename, bot, chat_id):
        try:
            file_size = os.path.getsize(filename)
            uploaded_size = 0
            msg = bot.send_message(chat_id, f"⬆️ Mengunggah video...\n{get_progress_bar(0)} 0.00%")

            with open(filename, 'rb') as video:
                while True:
                    chunk = video.read(1024 * 1024)
                    if not chunk:
                        break
                    bot.send_video(chat_id, chunk)
                    uploaded_size += len(chunk)
                    percent = (uploaded_size / file_size) * 100
                    bot.edit_message_text(
                        f"⬆️ Mengunggah video...\n{get_progress_bar(percent)} {percent:.2f}%\n"
                        f"Ukuran: {format_size(uploaded_size)}/{format_size(file_size)}",
                        chat_id, msg.message_id
                    )

            bot.edit_message_text("✅ Video berhasil diunggah.", chat_id, msg.message_id)
            os.remove(filename)
            bot.send_message(chat_id, f"🗑️ File {filename} telah dihapus setelah diunggah.")
        except Exception as e:
            bot.send_message(chat_id, f"❌ Gagal mengunggah video: {str(e)}")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Selamat datang di Doodstream Bot! Kirimkan link Doodstream untuk mengunduh videonya.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if "dood.pm" in message.text:
        doodstream_url = message.text
        doodstream = Doodstream(doodstream_url)
        
        async def process_video():
            chat_id = message.chat.id
            video_url = await doodstream.download_video(doodstream_url, bot, chat_id)
            if video_url:
                await doodstream.upload_video(video_url, bot, chat_id)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(process_video())
    else:
        bot.reply_to(message, "Link tidak valid. Pastikan Anda mengirimkan link Doodstream yang benar.")

if __name__ == '__main__':
    bot.polling(none_stop=True)
