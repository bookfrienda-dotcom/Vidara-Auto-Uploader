import os
import requests
import yt_dlp
import re
import time

def get_tiktok_direct_url(url, index):
    """استخراج الرابط المباشر لتيك توك عبر API مجاني (بدون تحميله محلياً)"""
    print(f"[{index}] جاري استخراج الرابط المباشر لتيك توك...")
    api_url = f"https://www.tikwm.com/api/?url={url}"
    try:
        res = requests.get(api_url).json()
        if res.get('code') == 0:
            direct_url = res['data']['play']
            print(f"[{index}] تم استخراج الرابط بنجاح.")
            return direct_url
        else:
            print(f"[{index}] فشل استخراج الرابط المباشر.")
            return None
    except Exception as e:
        print(f"[{index}] حدث خطأ في اتصال التيك توك: {e}")
        return None

def get_general_direct_url(video_url, index):
    """استخراج الرابط المباشر لباقي المواقع باستخدام yt-dlp (بدون تحميل)"""
    print(f"[{index}] جاري استخراج الرابط المباشر للموقع...")
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'quiet': True,
        'no_warnings': True,
        'simulate': True, # لا تقم بالتحميل، فقط اعطني البيانات
        'forceurl': True, # اجبره على طباعة الرابط المباشر
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            direct_url = info.get('url')
            if direct_url:
                 print(f"[{index}] تم استخراج الرابط بنجاح.")
                 return direct_url
            return None
    except Exception as e:
        print(f"[{index}] حدث خطأ أثناء استخراج الرابط: {e}")
        return None

def remote_upload_to_vidara(direct_url, index):
    """إرسال أمر لـ Vidara ليسحب الفيديو مباشرة من الرابط"""
    api_key = os.environ.get('VIDARA_API_KEY')
    
    # استخدام أمر Upload URL من الدوكمنتيشن
    api_endpoint = f"https://api.vidara.so/v1/upload/url"
    
    print(f"[{index}] جاري إرسال الرابط المباشر لـ Vidara ليقوم بسحبه...")
    try:
        # الدوكمنتيشن يقول إنه طلب GET
        params = {
            'api_key': api_key,
            'url': direct_url
        }
        
        response = requests.get(api_endpoint, params=params).json()
        
        if response.get("status") == 200:
             print(f"[{index}] تمت إضافة الفيديو لحسابك بنجاح!")
             print(f"[{index}] التفاصيل: {response.get('data')}")
        else:
             print(f"[{index}] حدث خطأ من سيرفر Vidara: {response}")
             
    except Exception as e:
        print(f"[{index}] حدث خطأ أثناء الاتصال بـ Vidara: {e}")

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
        print(f"\n[{idx}] معالجة الرابط: {target_url}")
        
        direct_url = None
        if 'tiktok.com' in target_url.lower():
            direct_url = get_tiktok_direct_url(target_url, idx)
            # إذا فشل tikwm، جرب yt-dlp
            if not direct_url:
                direct_url = get_general_direct_url(target_url, idx)
        else:
            direct_url = get_general_direct_url(target_url, idx)
        
        if direct_url:
            remote_upload_to_vidara(direct_url, idx)
            time.sleep(2) # تأخير لتجنب الضغط على الـ API
        else:
            print(f"[{idx}] تم تخطي الرابط لفشل استخراج الرابط المباشر.")
            
        print("="*40)
        
    print("اكتملت المهمة بالكامل!")
