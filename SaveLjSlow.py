import requests
from bs4 import BeautifulSoup
import os
import time
import re
import sys
import random
from urllib.parse import urljoin, urlparse

# ================= НАСТРОЙКИ ПО УМОЛЧАНИЮ =================
USERNAME = ""
BASE_URL = ""
OUTPUT_FOLDER = ""
IMAGES_FOLDER = "images"
COMMENTS_FOLDER = "comments_raw"

# Если посты под замком, вставьте сюда строку Cookie (например: 'ljsession=...')
COOKIES = {} 

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

# ✅ НОВЫЕ НАСТРОЙКИ ЗАДЕРЖЕК (ОЧЕНЬ ВАЖНО!)
DELAYS = {
    'between_pages': (2, 5),      # между страницами журнала (сек)
    'between_posts': (2, 6),     # между постами (сек)  
    'between_comments': (1, 4),   # между загрузкой комментариев (сек)
    'before_retry': (5, 10)      # перед повторной попыткой
}

RUS_MONTHS = {
    'января': '01', 'февраля': '02', 'марта': '03', 'апреля': '04',
    'мая': '05', 'июня': '06', 'июля': '07', 'августа': '08',
    'сентября': '09', 'октября': '10', 'ноября': '11', 'декабря': '12',
    'янв': '01', 'фев': '02', 'мар': '03', 'апр': '04', 'май': '05', 'июн': '06',
    'июл': '07', 'авг': '08', 'сен': '09', 'окт': '10', 'ноя': '11', 'дек': '12'
}

# ==========================================================

def random_delay(delay_range):
    """Случайная задержка в заданном диапазоне"""
    min_delay, max_delay = delay_range
    sleep_time = random.uniform(min_delay, max_delay)
    print(f"⏳ Пауза {sleep_time:.1f}с...")
    time.sleep(sleep_time)

def clean_filename(text):
    return re.sub(r'[\\/*?:"<>|]', "", text).strip()[:100]

def parse_russian_date_from_text(text):
    if not text: return None
    text = text.lower()
    match = re.search(r'(\d{1,2})\s+([а-я]+)[,\s]+(\d{4})', text)
    if match:
        day, month_name, year = match.groups()
        month_num = RUS_MONTHS.get(month_name)
        if month_num: return f"{year}_{month_num}_{day.zfill(2)}"
    match_iso = re.search(r'(\d{4})-(\d{2})-(\d{2})', text)
    if match_iso: return f"{match_iso.group(1)}_{match_iso.group(2)}_{match_iso.group(3)}"
    return None

def get_post_date(soup):
    meta_date = soup.find('meta', property='article:published_time')
    if meta_date and meta_date.get('content'):
        return meta_date.get('content').split('T')[0].replace('-', '_')

    time_tags = soup.find_all('time')
    for tag in time_tags:
        dt = tag.get('datetime')
        if dt: return dt.split('T')[0].replace('-', '_')
        parsed = parse_russian_date_from_text(tag.get_text())
        if parsed: return parsed

    potential_containers = soup.find_all(class_=re.compile(r'(date|time|header|meta|subject)'))
    for container in potential_containers:
        parsed = parse_russian_date_from_text(container.get_text())
        if parsed: return parsed
            
    full_text = soup.get_text()[:10000] 
    parsed = parse_russian_date_from_text(full_text)
    if parsed: return parsed

    return "0000_00_00"

def download_image(img_url, filename_prefix, folder_path, max_retries=2):
    for attempt in range(max_retries + 1):
        try:
            parsed = urlparse(img_url)
            ext = os.path.splitext(parsed.path)[1].lower()
            if not ext or len(ext) > 5: ext = '.jpg'
            local_filename = f"{filename_prefix}{ext}"
            local_filepath = os.path.join(folder_path, local_filename)
            if os.path.exists(local_filepath): return local_filename
            
            img_data = requests.get(img_url, headers=HEADERS, timeout=15).content
            with open(local_filepath, 'wb') as handler: handler.write(img_data)
            return local_filename
        except Exception as e:
            if attempt < max_retries:
                print(f"⚠️ Ошибка загрузки изображения (попытка {attempt+1}): {e}")
                random_delay(DELAYS['before_retry'])
            else:
                return None

def get_all_post_urls():
    print(f"Начинаю сбор ссылок для журнала {USERNAME}...")
    unique_urls = set()
    skip = 0
    step = 20
    consecutive_empty = 0  # Счетчик пустых страниц подряд
    
    while True:
        page_url = f"{BASE_URL}/?skip={skip}"
        print(f"📄 Сканирую страницу: {page_url}")
        
        try:
            r = requests.get(page_url, headers=HEADERS, cookies=COOKIES, timeout=20)
            
            if r.status_code == 429:  # Rate limit
                print("🚫 Rate limit обнаружен! Большая пауза...")
                random_delay((60, 120))
                continue
                
            if r.status_code != 200: 
                print(f"❌ Страница недоступна: {r.status_code}")
                break
                
            soup = BeautifulSoup(r.text, 'html.parser')
            links = soup.find_all('a', href=True)
            found = 0
            
            for link in links:
                href = link['href']
                if f"{USERNAME}.livejournal.com" in href and re.search(r'/\d+\.html$', href):
                    if href not in unique_urls:
                        unique_urls.add(href)
                        found += 1
            
            print(f"✅ Новых ссылок на этой странице: {found}")
            
            if found == 0:
                consecutive_empty += 1
                if consecutive_empty >= 3:  # 3 пустые страницы подряд = конец
                    break
            else:
                consecutive_empty = 0
                
            skip += step
            random_delay(DELAYS['between_pages'])
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            random_delay(DELAYS['before_retry'])
            break
            
    print(f"📊 Всего найдено уникальных постов: {len(unique_urls)}")
    return sorted(list(unique_urls), reverse=True)

def get_mobile_comments(username, post_id, raw_save_path):
    mobile_url = f"https://m.livejournal.com/read/user/{username}/{post_id}/comments"
    print(f"💬 Загружаю комментарии: {mobile_url}")
    
    try:
        r = requests.get(mobile_url, headers=HEADERS, cookies=COOKIES, timeout=25)
        
        # Сохраняем сырой HTML
        with open(raw_save_path, 'w', encoding='utf-8') as f:
            f.write(r.text)

        if r.status_code == 429:
            print("🚫 Rate limit на комментариях! Пропускаем...")
            return "<p>Комментарии временно недоступны (rate limit).</p>"
            
        if r.status_code != 200:
            return f"<p>Ошибка доступа к комментариям (код {r.status_code}).</p>"
        
        soup = BeautifulSoup(r.text, 'html.parser')
        
        comments_container = soup.find(class_='b-tree') or \
                             soup.find(class_='comments-body') or \
                             soup.find('section', class_='comments') or \
                             soup.find('div', id='comments') or \
                             soup.find(class_='b-comments')

        if not comments_container:
            main_wrapper = soup.find('main') or soup.find('div', class_='app-widget')
            if main_wrapper:
                comments_container = main_wrapper
            else:
                if "Нет комментариев" in r.text or "No comments" in r.text:
                    return "<p>Комментариев нет.</p>"
                else:
                    return "<p>Автоматически извлечь комментарии не удалось.</p>"

        # Очистка мусора
        for junk in comments_container.find_all(['form', 'input', 'textarea', 'button', 'script', 'style']):
            junk.decompose()
            
        for a in comments_container.find_all('a'):
            txt = a.get_text().lower()
            if 'ответить' in txt or 'reply' in txt or 'expand' in txt or 'развернуть' in txt:
                a.decompose()
        
        for img in comments_container.find_all('img'):
            src = img.get('src')
            if src: img['src'] = urljoin(mobile_url, src)

        return str(comments_container)

    except Exception as e:
        return f"<p>Ошибка при обработке комментариев: {e}</p>"

def process_posts(urls):
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)
    images_dir = os.path.join(OUTPUT_FOLDER, IMAGES_FOLDER)
    if not os.path.exists(images_dir):
        os.makedirs(images_dir)
    comments_raw_dir = os.path.join(OUTPUT_FOLDER, COMMENTS_FOLDER)
    if not os.path.exists(comments_raw_dir):
        os.makedirs(comments_raw_dir)

    print(f"\n🚀 Обработка {len(urls)} постов. Сохранение в: {OUTPUT_FOLDER}")

    for i, url in enumerate(urls):
        try:
            post_id = re.search(r'/(\d+)\.html', url).group(1)
            print(f"\n[{i+1}/{len(urls)}] 📝 Пост #{post_id}")
            
            print("   🔗 Загружаю основной пост...")
            r = requests.get(url, headers=HEADERS, cookies=COOKIES, timeout=25)
            
            if r.status_code == 429:
                print("🚫 Rate limit! Большая пауза...")
                random_delay((120, 180))
                continue
                
            if r.status_code != 200: 
                print(f"   ❌ Пост недоступен: {r.status_code}")
                continue
                
            if r.encoding != 'utf-8': r.encoding = r.apparent_encoding
            soup = BeautifulSoup(r.text, 'html.parser')
            
            date_str = get_post_date(soup)
            title_tag = soup.find('h1') or soup.find('h3', class_='entry-header') or soup.find('title')
            title_text = title_tag.get_text(strip=True) if title_tag else "No Title"
            safe_title = clean_filename(title_text)
            
            html_filename = f"{date_str}_{post_id}_{safe_title}.html"
            html_filepath = os.path.join(OUTPUT_FOLDER, html_filename)
            
            if os.path.exists(html_filepath):
                print(f"   ✅ Уже скачан: {html_filename}")
                random_delay(DELAYS['between_posts'])
                continue

            content = soup.find(class_='entry-content') or soup.find(class_='b-singlepost-body') or soup.find('article') or soup.find('div', {'id': 'entry-text'})
            if not content: content = soup.find('body')

            # Картинки
            images = content.find_all('img')
            if images:
                print(f"   🖼️ Найдено {len(images)} картинок")
                img_counter = 1
                for img in images:
                    src = img.get('src')
                    if not src: continue
                    abs_url = urljoin(url, src)
                    img_prefix = f"{date_str}_{post_id}_{img_counter}"
                    local_img_name = download_image(abs_url, img_prefix, images_dir)
                    if local_img_name:
                        img['src'] = f"{IMAGES_FOLDER}/{local_img_name}"
                        for attr in ['width', 'height', 'style', 'srcset']:
                            if img.has_attr(attr): del img[attr]
                    img_counter += 1
                    time.sleep(0.5)  # Пауза между картинками

            # Комментарии
            raw_comment_filename = f"comments_{post_id}.html"
            raw_comment_path = os.path.join(comments_raw_dir, raw_comment_filename)
            
            random_delay(DELAYS['between_comments'])
            comments_html = get_mobile_comments(USERNAME, post_id, raw_comment_path)

            # Сохранение HTML (код тот же)
            final_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset='utf-8'>
                <title>{title_text}</title>
                <style>
                    body {{ font-family: 'Verdana', sans-serif; max-width: 800px; margin: auto; padding: 20px; background: #f4f4f4; }}
                    .container {{ background: #fff; padding: 30px; border-radius: 5px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
                    img {{ max-width: 100%; height: auto; display: block; margin: 15px 0; border-radius: 3px; }}
                    h1 {{ color: #333; }}
                    .meta {{ color: #777; font-size: 0.9em; margin-bottom: 20px; border-bottom: 1px solid #eee; padding-bottom: 10px; }}
                    a {{ color: #0066cc; text-decoration: none; }}
                    .comments-section {{ margin-top: 50px; border-top: 2px solid #eee; padding-top: 20px; }}
                    .comments-header {{ font-size: 1.5em; font-weight: bold; margin-bottom: 20px; }}
                    .b-tree {{ padding-left: 0; }}
                    .b-tree__item {{ list-style: none; margin-bottom: 20px; border-left: 3px solid #e0e0e0; padding-left: 15px; }}
                    .b-tree__item .b-tree__item {{ margin-left: 15px; margin-top: 10px; border-left: 2px solid #ccc; }}
                    .b-tree__content {{ background: #fdfdfd; padding: 10px; border-radius: 4px; border: 1px solid #eee; }}
                    .userbox {{ font-weight: bold; color: #444; margin-bottom: 5px; display: block; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>{title_text}</h1>
                    <div class="meta">
                        Дата: {date_str.replace('_', '-')} | ID: {post_id} | 
                        <a href='{url}' target='_blank'>Оригинал</a>
                    </div>
                    <div class="content">
                        {str(content)}
                    </div>
                    
                    <div class="comments-section">
                        <div class="comments-header">Комментарии</div>
                        {comments_html}
                    </div>
                </div>
            </body>
            </html>
            """
            
            with open(html_filepath, 'w', encoding='utf-8') as f:
                f.write(final_html)
            
            print(f"   ✅ ГОТОВО: {html_filename}")
            
        except Exception as e:
            print(f"   ❌ Ошибка с постом {post_id}: {e}")
            
        # ✅ КЛЮЧЕВАЯ ЗАДЕРЖКА МЕЖДУ ПОСТАМИ
        random_delay(DELAYS['between_posts'])

if __name__ == "__main__":
    user_input = input("Введите название журнала (username): ").strip()
    
    if not user_input:
        print("Имя не может быть пустым.")
        sys.exit()

    check_url = f"https://{user_input}.livejournal.com"
    print(f"🔍 Проверка журнала: {check_url} ...")

    try:
        check_response = requests.get(check_url, headers=HEADERS, timeout=15)
        if check_response.status_code == 404:
            print("❌ Журнал не найден")
            sys.exit()
    except:
        print("❌ Журнал не найден")
        sys.exit()

    print("✅ Журнал найден! Начинаем медленное скачивание...")

    USERNAME = user_input
    BASE_URL = check_url
    OUTPUT_FOLDER = user_input

    urls = get_all_post_urls()
    if urls:
        process_posts(urls)
        print("\n🎉 === СКАЧИВАНИЕ ЗАВЕРШЕНО ===\n📁 Результаты в папке:", OUTPUT_FOLDER)
    else:
        print("❌ Постов не найдено.")