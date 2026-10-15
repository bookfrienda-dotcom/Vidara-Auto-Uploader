import os
import requests
import yt_dlp
import glob
import re
import time

def download_tiktok_via_api(url, index):
    """دالة مخصصة لتنزيل تيك توك لتخطي الحظر وبدون علامة مائية"""
    print(f"[{index}] جاري استخراج رابط تيك توك المباشر لتخطي الحظر...")
    api_url = f"https://www.tikwm.com/api/?url={url}"
    try:
        res = requests.get(api_url).json()
        if res.get('code') == 0:
            video_url = res['data']['play']
            print(f"[{index}] تم استخراج الرابط بنجاح، جاري التحميل...")
            
            video_res = requests.get(video_url, stream=True)
            local_filename = f"downloaded_video_{index}.mp4"
            
            with open(local_filename, 'wb') as f:
                for chunk in video_res.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"[{index}] تمت عملية التحميل بنجاح.")
            return local_filename
        else:
            print(f"[{index}] فشل استخراج الرابط المباشر من تيك توك.")
            return None
    except Exception as e:
        print(f"[{index}] حدث خطأ في اتصال التيك توك: {e}")
        return None

def download_video(video_url, index):
    print(f"\n[{index}] جاري بدء التحميل للرابط: {video_url}")
    
    if 'tiktok.com' in video_url.lower():
        file_path = download_tiktok_via_api(video_url, index)
        if file_path:
            return file_path
        print(f"[{index}] سنحاول باستخدام yt-dlp كحل بديل...")

    out_tmpl = f'downloaded_video_{index}.%(ext)s'
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': out_tmpl,
        'quiet': False,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
            
        downloaded_files = glob.glob(f"downloaded_video_{index}.*")
        if downloaded_files:
            print(f"[{index}] تمت عملية التحميل بنجاح.")
            return downloaded_files[0]
        else:
            return None
    except Exception as e:
        print(f"[{index}] حدث خطأ أثناء التحميل: {e}")
        return None

def get_upload_server(api_key):
    """جلب رابط سيرفر الرفع الديناميكي من Vidara"""
    try:
        server_url = f"https://api.vidara.so/v1/upload/server?api_key={api_key}"
        response = requests.get(server_url).json()
        if response.get("status") == 200:
            return response["result"]["upload_server"]
        else:
            print(f"فشل في جلب سيرفر الرفع: {response}")
            return None
    except Exception as e:
        print(f"خطأ في جلب سيرفر الرفع: {e}")
        return None

def upload_to_vidara(file_path, index):
    api_key = os.environ.get('VIDARA_API_KEY')
    
    # 1. جلب سيرفر الرفع أولاً
    print(f"[{index}] جاري طلب سيرفر الرفع...")
    upload_api_url = get_upload_server(api_key)
    
    if not upload_api_url:
        print(f"[{index}] تم إلغاء الرفع لعدم توفر سيرفر.")
        return

    print(f"[{index}] جاري رفع الملف إلى سيرفر Vidara: {upload_api_url} ...")
    try:
        with open(file_path, 'rb') as f:
            # المتغيرات المطلوبة للرفع كما هو موضح في توثيق Vidara
            files = {'file': f}
            data = {'api_key': api_key} 
            
            response = requests.post(upload_api_url, files=files, data=data)
            
            print(f"[{index}] نتيجة الرفع السحابي:")
            try:
                print(response.json())
            except:
                print(response.text)
            
    except Exception as e:
        print(f"[{index}] حدث خطأ أثناء الرفع: {e}")

if __name__ == "__main__":
    urls_input = os.environ.get('VIDEO_URLS', '')
    
    if not urls_input.strip():
        print("لم يتم إدخال أي روابط!")
        exit(1)
        
    urls = re.findall(r'(https?://[^\s,]+)', urls_input)
    urls = list(dict.fromkeys(urls))
    
    if not urls:
        print("لم يتم التعرف على أي روابط صالحة في الإدخال!")
        exit(1)
        
    print(f"تم العثور على ({len(urls)}) روابط بنجاح.\n" + "="*40)
    
    for idx, target_url in enumerate(urls, start=1):
        local_file = download_video(target_url, idx)
        
        if local_file:
            upload_to_vidara(local_file, idx)
            time.sleep(2) # تأخير بسيط بين الرفع لتجنب حظر الـ API
            os.remove(local_file) 
            print(f"[{idx}] تم حذف الملف من السيرفر بنجاح.")
        else:
            print(f"[{idx}] تم تخطي الرفع لفشل التحميل.")
            
        print("="*40)
        
    print("اكتملت المهمة بالكامل!")
