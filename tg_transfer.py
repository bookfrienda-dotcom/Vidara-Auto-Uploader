import os
import requests
import re
import time
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession

# تنظيف العنوان
def clean_title(title):
    if not title: return "Telegram_Video"
    clean = re.sub(r'[\\/*?:"<>|#\n\r]', " ", title)
    return clean.strip()[:100]

# --- دوال Vidara للرفع المحلي ---
def rename_video(api_key, filecode, custom_title, index):
    try:
        requests.get("https://api.vidara.so/v1/video/rename", params={'api_key': api_key, 'filecode': filecode, 'title': custom_title})
    except: pass

def move_video(api_key, filecode, folder_id, index):
    if not folder_id: return
    try:
        requests.get("https://api.vidara.so/v1/video/move", params={'api_key': api_key, 'filecode': filecode, 'fld_id': folder_id})
    except: pass

def local_upload_to_vidara(file_path, final_title, folder_id, index):
    api_key = os.environ.get('VIDARA_API_KEY')
    print(f"[{index}] جاري طلب سيرفر الرفع من Vidara...")
    try:
        # الإصلاح: استخدام api_key بشكل صحيح والتحقق من الاستجابة
        res = requests.get(f"https://api.vidara.so/v1/upload/server?api_key={api_key}").json()
        
        if res.get("status") != 200 or res.get("result") is None:
            print(f"[{index}] خطأ في الاستجابة من سيرفر Vidara: {res}")
            return False
            
        upload_api_url = res["result"].get("upload_server") or res["result"].get("url")
        
        if not upload_api_url:
            print(f"[{index}] لم يتم إرجاع رابط رفع صحيح.")
            return False
        
        print(f"[{index}] جاري رفع الفيديو إلى Vidara...")
        with open(file_path, 'rb') as f:
            # الإصلاح: التأكد من إرسال المتغير api_key في الـ data لربطه بحسابك
            response = requests.post(upload_api_url, files={'file': f}, data={'api_key': api_key}).json()
            filecode = response.get('filecode')
            if filecode:
                print(f"[{index}] تم الرفع بنجاح! (Filecode: {filecode})")
                time.sleep(1)
                rename_video(api_key, filecode, final_title, index)
                if folder_id:
                    time.sleep(1)
                    move_video(api_key, filecode, folder_id, index)
                return True
            else:
                print(f"[{index}] لم نتمكن من الحصول على Filecode: {response}")
    except Exception as e:
        print(f"[{index}] خطأ أثناء الرفع لـ Vidara: {e}")
    return False

# --- المحرك الأساسي لـ Telethon ---
async def main():
    api_id = int(os.environ.get('TG_API_ID', 0))
    api_hash = os.environ.get('TG_API_HASH', '')
    session_str = os.environ.get('TG_SESSION', '')
    
    urls_input = os.environ.get('VIDEO_URLS', '')
    prefix_input = os.environ.get('TITLE_PREFIX', '').strip()
    folder_id_input = os.environ.get('FOLDER_ID', '').strip()

    urls = re.findall(r'(https?://t\.me/[^\s,]+)', urls_input)
    urls = list(dict.fromkeys(urls))
    
    if not urls:
        print("لم يتم إدخال روابط تليجرام صالحة!")
        return

    print(f"تم العثور على ({len(urls)}) روابط تليجرام.\n" + "="*40)
    
    client = TelegramClient(StringSession(session_str), api_id, api_hash)
    await client.start()
    
    for idx, url in enumerate(urls, start=1):
        print(f"\n[{idx}] معالجة الرابط: {url}")
        
        match = re.search(r't\.me/(?:c/)?([^/]+)/(\d+)', url)
        if not match:
            print(f"[{idx}] صيغة الرابط غير مدعومة.")
            continue
            
        chat_id_or_username = match.group(1)
        msg_id = int(match.group(2))
        
        if chat_id_or_username.isdigit():
            chat_id_or_username = int('-100' + chat_id_or_username)
            
        try:
            print(f"[{idx}] جاري جلب المنشور من تليجرام...")
            message = await client.get_messages(chat_id_or_username, ids=msg_id)
            
            if not message or not message.media:
                print(f"[{idx}] تم التخطي: لا يوجد فيديو في هذا الرابط.")
                continue
                
            caption = message.text[:50] if message.text else f"TG_Video_{msg_id}"
            title = f"{prefix_input} {caption}".strip() if prefix_input else caption
            final_title = clean_title(title)
            
            print(f"[{idx}] جاري تحميل الفيديو إلى سيرفر جيت هب (قد يستغرق بعض الوقت حسب حجم الفيديو)...")
            local_file = f"tg_video_{idx}.mp4"
            await client.download_media(message, file=local_file)
            
            if os.path.exists(local_file):
                print(f"[{idx}] اكتمل التحميل المحلي.")
                local_upload_to_vidara(local_file, final_title, folder_id_input, idx)
                os.remove(local_file)
                print(f"[{idx}] تم مسح الملف المؤقت.")
            else:
                print(f"[{idx}] فشل في حفظ الملف.")
                
        except Exception as e:
            print(f"[{idx}] حدث خطأ في تليجرام: {e}")
            
        print("="*40)

if __name__ == "__main__":
    asyncio.run(main())
