import os
import requests
import yt_dlp
import glob

def download_video(video_url, index):
    print(f"\n[{index}] جاري بدء التحميل للرابط: {video_url}")
    
    # إعدادات yt-dlp للتحميل
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
            
        # البحث عن الملف الذي تم تحميله
        downloaded_files = glob.glob(f"downloaded_video_{index}.*")
        if downloaded_files:
            print(f"[{index}] تمت عملية التحميل بنجاح.")
            return downloaded_files[0]
        else:
            return None
    except Exception as e:
        print(f"[{index}] حدث خطأ أثناء التحميل: {e}")
        return None

def upload_to_vidara(file_path, index):
    api_key = os.environ.get('VIDARA_API_KEY')
    
    # --- تنبيه: راجع الرابط أدناه بناءً على صفحة API Docs في Vidara ---
    # أغلب مواقع الرفع تستخدم هذا الرابط المباشر للـ API
    upload_api_url = "https://vidara.to/api/upload" 
    
    print(f"[{index}] جاري رفع الملف ({file_path}) إلى موقع Vidara...")
    try:
        with open(file_path, 'rb') as f:
            # المتغيرات المطلوبة للرفع (file للـ فيديو، و key لمفتاح حسابك)
            files = {'file': f}
            data = {'key': api_key} 
            
            response = requests.post(upload_api_url, files=files, data=data)
            
            print(f"[{index}] نتيجة الرفع:")
            print(response.text)
            
    except Exception as e:
        print(f"[{index}] حدث خطأ أثناء الرفع: {e}")

if __name__ == "__main__":
    # استلام الروابط من GitHub Actions
    urls_input = os.environ.get('VIDEO_URLS', '')
    
    if not urls_input.strip():
        print("لم يتم إدخال أي روابط!")
        exit(1)
        
    # تنظيف الروابط وفصلها سواء تم إدخالها بفاصلة (,) أو كل رابط في سطر
    urls = [url.strip() for url in urls_input.replace(',', '\n').split('\n') if url.strip()]
    
    print(f"تم العثور على {len(urls)} روابط للعمل عليها.\n" + "="*40)
    
    # المرور على كل رابط بالترتيب: تحميل -> رفع -> حذف من جيت هب
    for idx, target_url in enumerate(urls, start=1):
        local_file = download_video(target_url, idx)
        
        if local_file:
            upload_to_vidara(local_file, idx)
            os.remove(local_file) # حذف الفيديو لتفريغ المساحة للرابط الذي يليه
            print(f"[{idx}] تم حذف الملف المؤقت من سيرفر جيت هب.")
        else:
            print(f"[{idx}] تم تخطي عملية الرفع لأن التحميل فشل للرابط: {target_url}")
            
        print("="*40)
        
    print("تم الانتهاء من جميع الروابط بنجاح!")
