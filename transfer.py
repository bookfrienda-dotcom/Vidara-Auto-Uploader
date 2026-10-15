import os
import requests
import yt_dlp
import re
import time
import glob

def clean_title(title):
    if not title:
        return "Unknown_Video"
    clean = re.sub(r'[\\/*?:"<>|#]', "", title)
    return clean.strip()[:100]

# --- دوال التعامل مع API الخاص بـ Vidara ---
def rename_video(api_key, filecode, custom_title, index):
    rename_endpoint = "https://api.vidara.so/v1/video/rename"
    params = {'api_key': api_key, 'filecode': filecode, 'title': custom_title}
    try:
        requests.get(rename_endpoint, params=params)
    except:
        pass

def move_video(api_key, filecode, folder_id, index):
    if not folder_id: return
    move_endpoint = "https://api.vidara.so/v1/video/move"
    params = {'api_key': api_key, 'filecode': filecode, 'fld_id': folder_id}
    try:
        requests.get(move_endpoint, params=params)
    except:
        pass

def get_upload_server(api_key):
    try:
        server_url = f"https://api.vidara.so/v1/upload/server?key={api_key}"
        res = requests.get(server_url).json()
        if res.get("status") == 200: return res["result"]
        
        server_url = f"https://api.vidara.so/v1/upload/server?api_key={api_key}"
        res = requests.get(server_url).json()
        if res.get("status") == 200: return res["result"]
    except:
        pass
    return None

# --- الطريقة الأولى: السحب السحابي السريع (مخصصة لتيك توك) ---
def get_tiktok_data(url, index):
    api_url = f"https://www.tikwm.com/api/?url={url}"
    try:
        res = requests.get(api_url).json()
        if res.get('code') == 0:
            return res['data']['play'], clean_title(res['data'].get('title', f'TikTok_{index}'))
    except:
        pass
    return None, None

def remote_upload_to_vidara(direct_url, final_title, folder_id, index):
    api_key = os.environ.get('VIDARA_API_KEY')
    api_endpoint = "https://api.vidara.so/v1/upload/url"
    print(f"[{index}] جاري أمر Vidara بسحب الفيديو سحابياً...")
    try:
        params = {'api_key': api_key, 'url': direct_url}
        response = requests.get(api_endpoint, params=params).json()
        if response.get("status") == 200:
             filecode = response.get('data', {}).get('filecode')
             print(f"[{index}] تم السحب السحابي بنجاح! (Filecode: {filecode})")
             if filecode:
                 time.sleep(1)
                 rename_video(api_key, filecode, final_title, index)
                 if folder_id:
                     time.sleep(1)
                     move_video(api_key, filecode, folder_id, index)
             return True
        else:
             return False
    except:
        return False

# --- الطريقة الثانية: التحميل لجيت هب ثم الرفع (لتليجرام ويوتيوب وباقي المواقع) ---
def download_local_fallback(video_url, index):
    print(f"[{index}] جاري التحميل محلياً إلى سيرفر جيت هب...")
    out_tmpl = f'downloaded_video_{index}.%(ext)s'
    ydl_opts = {
        'format': 'best',
        'outtmpl': out_tmpl,
        'quiet': True,
        'no_warnings': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # هنا قمنا بإصلاح الخطأ الذي ظهر لك: لو لم يجد فيديو لن ينهار
            info = ydl.extract_info(video_url, download=True)
            if not info:
                return None, None
            title = info.get('title', f'Video_{index}')
            
        downloaded_files = glob.glob(f"downloaded_video_{index}.*")
        if downloaded_files:
            return downloaded_files[0], clean_title(title)
        return None, None
    except Exception as e:
        print(f"[{index}] فشل التحميل: تأكد أن الرابط يحتوي على فيديو مدعوم.")
        return None, None

def local_upload_to_vidara(file_path, final_title, folder_id, index):
    api_key = os.environ.get('VIDARA_API_KEY')
    server_data = get_upload_server(api_key)
    if not server_data:
        print(f"[{index}] فشل الحصول على سيرفر الرفع من Vidara.")
        return False

    upload_api_url = server_data.get("upload_server") or server_data.get("url")
    print(f"[{index}] جاري رفع الملف من جيت هب إلى Vidara...")
    try:
        with open(file_path, 'rb') as f:
            files = {'file': f}
            data = {'api_key': api_key, 'key': api_key}
            response = requests.post(upload_api_url, files=files, data=data).json()
            
            filecode = response.get('filecode')
            if filecode:
                print(f"[{index}] تم الرفع والتخزين بنجاح! (Filecode: {filecode})")
                time.sleep(1)
                rename_video(api_key, filecode, final_title, index)
                if folder_id:
                    time.sleep(1)
                    move_video(api_key, filecode, folder_id, index)
                return True
            else:
                print(f"[{index}] خطأ في استجابة الرفع: {response}")
                return False
    except Exception as e:
        print(f"[{index}] حدث خطأ أثناء الرفع المحلي: {e}")
        return False

# --- المحرك الأساسي للسكريبت ---
if __name__ == "__main__":
    urls_input = os.environ.get('VIDEO_URLS', '')
    prefix_input = os.environ.get('TITLE_PREFIX', '').strip()
    folder_id_input = os.environ.get('FOLDER_ID', '').strip()
    
    urls = re.findall(r'(https?://[^\s,]+)', urls_input)
    urls = list(dict.fromkeys(urls))
    
    if not urls:
        print("لم يتم التعرف على أي روابط صالحة!")
        exit(1)
        
    print(f"تم العثور على ({len(urls)}) روابط للعمل عليها.\n" + "="*40)
    
    for idx, target_url in enumerate(urls, start=1):
        print(f"\n[{idx}] معالجة الرابط: {target_url}")
        
        final_title = ""
        is_telegram = 't.me' in target_url.lower()
        success = False
        
        # 1. محاولة السحب السحابي أولاً (نتخطاها لو كان تليجرام لأنها تفشل معه)
        if not is_telegram:
            direct_url, title = None, None
            if 'tiktok.com' in target_url.lower():
                direct_url, title = get_tiktok_data(target_url, idx)
            
            if direct_url and title:
                final_title = f"{prefix_input} {title}" if prefix_input else title
                final_title = final_title[:100]
                success = remote_upload_to_vidara(direct_url, final_title, folder_id_input, idx)
        
        # 2. الخطة البديلة: التحميل لجيت هب والرفع (لتليجرام ولأي رابط يفشل سحابياً)
        if not success:
            print(f"[{idx}] استخدام طريقة (التحميل والرفع المباشر)...")
            local_file, title = download_local_fallback(target_url, idx)
            
            if local_file and title:
                final_title = f"{prefix_input} {title}" if prefix_input else title
                final_title = final_title[:100]
                
                local_upload_to_vidara(local_file, final_title, folder_id_input, idx)
                os.remove(local_file) # تنظيف السيرفر
                print(f"[{idx}] تم حذف الملف المؤقت من سيرفر جيت هب.")
            else:
                print(f"[{idx}] تم تخطي الرابط بالكامل. (الرابط قد لا يحتوي على فيديو مدعوم)")
                
        print("="*40)
        
    print("اكتملت المهمة بالكامل!")
