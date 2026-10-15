import os
import requests
import yt_dlp
import re
import time

def clean_title(title):
    if not title:
        return "Unknown_Video"
    clean = re.sub(r'[\\/*?:"<>|#]', "", title)
    return clean.strip()

def get_tiktok_data(url, index):
    print(f"[{index}] جاري استخراج بيانات تيك توك...")
    api_url = f"https://www.tikwm.com/api/?url={url}"
    try:
        res = requests.get(api_url).json()
        if res.get('code') == 0:
            direct_url = res['data']['play']
            title = res['data'].get('title', f'TikTok_Video_{index}')
            print(f"[{index}] تم استخراج الرابط بنجاح. (العنوان الأصلي: {clean_title(title)})")
            return direct_url, clean_title(title)
        else:
            print(f"[{index}] فشل استخراج بيانات تيك توك.")
            return None, None
    except Exception as e:
        print(f"[{index}] حدث خطأ في اتصال التيك توك: {e}")
        return None, None

def get_general_data(video_url, index):
    print(f"[{index}] جاري استخراج البيانات باستخدام yt-dlp...")
    ydl_opts = {
        'format': 'best',
        'quiet': True,
        'no_warnings': True,
        'simulate': True, 
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            direct_url = info.get('url')
            title = info.get('title', f'Video_{index}')
            
            if direct_url:
                 print(f"[{index}] تم استخراج الرابط بنجاح. (العنوان الأصلي: {clean_title(title)})")
                 return direct_url, clean_title(title)
            return None, None
    except Exception as e:
        print(f"[{index}] حدث خطأ أثناء استخراج الرابط: {e}")
        return None, None

def rename_video(api_key, filecode, custom_title, index):
    rename_endpoint = "https://api.vidara.so/v1/video/rename"
    print(f"[{index}] جاري إعادة تسمية الفيديو في حسابك إلى: {custom_title} ...")
    
    params = {
        'api_key': api_key,
        'filecode': filecode,
        'title': custom_title
    }
    
    try:
        res = requests.get(rename_endpoint, params=params).json()
        if res.get("status") == 200:
            print(f"[{index}] تمت إعادة التسمية بنجاح!")
        else:
            print(f"[{index}] لم نتمكن من إعادة التسمية: {res}")
    except Exception as e:
        print(f"[{index}] خطأ أثناء الاتصال لتغيير الاسم: {e}")

def remote_upload_to_vidara(direct_url, final_title, index):
    api_key = os.environ.get('VIDARA_API_KEY')
    api_endpoint = "https://api.vidara.so/v1/upload/url"
    
    print(f"[{index}] جاري إرسال الرابط المباشر لـ Vidara ليقوم بسحبه...")
    try:
        params = {
            'api_key': api_key,
            'url': direct_url
        }
        
        response = requests.get(api_endpoint, params=params).json()
        
        if response.get("status") == 200:
             filecode = response.get('data', {}).get('filecode')
             print(f"[{index}] تمت إضافة الفيديو لحسابك بنجاح! (Filecode: {filecode})")
             
             if filecode:
                 time.sleep(1) 
                 rename_video(api_key, filecode, final_title, index)
                 
        else:
             print(f"[{index}] حدث خطأ من سيرفر Vidara: {response}")
             
    except Exception as e:
        print(f"[{index}] حدث خطأ أثناء الاتصال بـ Vidara: {e}")

if __name__ == "__main__":
    urls_input = os.environ.get('VIDEO_URLS', '')
    prefix_input = os.environ.get('TITLE_PREFIX', '').strip() # استلام الجملة الإضافية
    
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
        print(f"\n[{idx}] معالجة الرابط: {target_url}")
        
        direct_url = None
        title = None
        
        if 'tiktok.com' in target_url.lower():
            direct_url, title = get_tiktok_data(target_url, idx)
            if not direct_url: 
                direct_url, title = get_general_data(target_url, idx)
        else:
            direct_url, title = get_general_data(target_url, idx)
        
        if direct_url and title:
            # دمج البادئة (Prefix) مع العنوان إذا كان المستخدم قد أدخل واحدة
            if prefix_input:
                final_title = f"{prefix_input} {title}"
            else:
                final_title = title
                
            # تقصير الاسم إلى 100 حرف تجنباً لأخطاء طول العنوان في سيرفر Vidara
            final_title = final_title[:100]
            
            remote_upload_to_vidara(direct_url, final_title, idx)
            time.sleep(3) 
        else:
            print(f"[{idx}] تم تخطي الرابط لفشل استخراج البيانات.")
            
        print("="*40)
        
    print("اكتملت المهمة بالكامل!")
