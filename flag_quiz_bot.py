"""
FLAG QUIZ BOT - YouTube Shorts Generator
Format: 10 bayrak, Easy/Medium/Hard/Expert zorluk
Test modu: Video dosyası üretir, YouTube'a yüklemez
"""

import os, sys, random, requests, base64
import io as _io
from PIL import Image, ImageDraw, ImageFont

# ── Encoding fix ──────────────────────────────────────────────
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout = _io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    except: pass

from moviepy.editor import ImageClip, concatenate_videoclips

script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# ── GitHub Actions: env'den token/secret dosyalarını yaz ──────
def _write_from_env(env_var, filepath):
    val = os.environ.get(env_var)
    if val and not os.path.exists(filepath):
        with open(filepath, 'wb') as f:
            f.write(base64.b64decode(val))
        print(f"[OK] {env_var} yazildi.")

_write_from_env("TOKEN_JSON", os.path.join(script_dir, "token.json"))
_write_from_env("SECRET_JSON", os.path.join(script_dir, "secret.json"))

OUTPUT_VIDEO          = os.path.join(script_dir, "flag_quiz.mp4")
OUTPUT_VIDEO_BRAINROT    = os.path.join(script_dir, "brainrot_quiz.mp4")
OUTPUT_VIDEO_CAPITAL     = os.path.join(script_dir, "capital_quiz.mp4")
OUTPUT_VIDEO_MULTICHOICE = os.path.join(script_dir, "multichoice_quiz.mp4")
OUTPUT_VIDEO_TRIVIA      = os.path.join(script_dir, "trivia_quiz.mp4")
MODE_FILE           = os.path.join(script_dir, "kullanilan_quiz.json")
GROQ_API_KEY        = os.environ.get("GROQ_API_KEY", "")
TELEGRAM_BOT_TOKEN  = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID    = os.environ.get("TELEGRAM_CHAT_ID", "")
SECRET_PATH  = os.path.join(script_dir, "secret.json")
TOKEN_PATH   = os.path.join(script_dir, "token.json")
W, H = 1080, 1920


# ─────────────────────────────────────────────────────────────
# TELEGRAM BİLDİRİM
# ─────────────────────────────────────────────────────────────
def send_telegram(msg):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    import urllib.request, urllib.parse
    try:
        data = urllib.parse.urlencode({
            "chat_id": TELEGRAM_CHAT_ID,
            "text": msg,
            "parse_mode": "HTML"
        }).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            data=data
        )
        urllib.request.urlopen(req, timeout=10)
        print("[Telegram] Mesaj gonderildi.")
    except Exception as e:
        print(f"[Telegram] Hata: {e}")

# ─────────────────────────────────────────────────────────────
# ÜLKE VERİSİ  (kod → isim, zorluk)
# flagcdn.com/w320/{kod}.png  → ücretsiz bayrak görseli
# ─────────────────────────────────────────────────────────────
COUNTRIES = {
    # EASY
    "us": ("USA",           "easy"),
    "gb": ("UK",            "easy"),
    "ca": ("Canada",        "easy"),
    "au": ("Australia",     "easy"),
    "de": ("Germany",       "easy"),
    "fr": ("France",        "easy"),
    "jp": ("Japan",         "easy"),
    "br": ("Brazil",        "easy"),
    "it": ("Italy",         "easy"),
    "cn": ("China",         "easy"),
    # MEDIUM
    "tr": ("Turkey",        "medium"),
    "mx": ("Mexico",        "medium"),
    "in": ("India",         "medium"),
    "es": ("Spain",         "medium"),
    "ru": ("Russia",        "medium"),
    "kr": ("South Korea",   "medium"),
    "za": ("South Africa",  "medium"),
    "ar": ("Argentina",     "medium"),
    "eg": ("Egypt",         "medium"),
    "se": ("Sweden",        "medium"),
    # HARD
    "ng": ("Nigeria",       "hard"),
    "pk": ("Pakistan",      "hard"),
    "bd": ("Bangladesh",    "hard"),
    "vn": ("Vietnam",       "hard"),
    "ua": ("Ukraine",       "hard"),
    "nl": ("Netherlands",   "hard"),
    "pl": ("Poland",        "hard"),
    "ro": ("Romania",       "hard"),
    "my": ("Malaysia",      "hard"),
    "ph": ("Philippines",   "hard"),
    # EXPERT
    "bt": ("Bhutan",        "expert"),
    "mv": ("Maldives",      "expert"),
    "mh": ("Marshall Islands", "expert"),
    "ki": ("Kiribati",      "expert"),
    "vu": ("Vanuatu",       "expert"),
    "pg": ("Papua New Guinea","expert"),
    "tl": ("Timor-Leste",   "expert"),
    "kp": ("North Korea",   "expert"),
    "cy": ("Cyprus",        "expert"),
    "mt": ("Malta",         "expert"),
}

CAPITALS = {
    "us": "Washington D.C.", "gb": "London",        "ca": "Ottawa",       "au": "Canberra",
    "de": "Berlin",          "fr": "Paris",          "jp": "Tokyo",        "br": "Brasilia",
    "it": "Rome",            "cn": "Beijing",
    "tr": "Ankara",          "mx": "Mexico City",    "in": "New Delhi",    "es": "Madrid",
    "ru": "Moscow",          "kr": "Seoul",          "za": "Pretoria",     "ar": "Buenos Aires",
    "eg": "Cairo",           "se": "Stockholm",
    "ng": "Abuja",           "pk": "Islamabad",      "bd": "Dhaka",        "vn": "Hanoi",
    "ua": "Kyiv",            "nl": "Amsterdam",      "pl": "Warsaw",       "ro": "Bucharest",
    "my": "Kuala Lumpur",    "ph": "Manila",
    "bt": "Thimphu",         "mv": "Male",           "mh": "Majuro",       "ki": "South Tarawa",
    "vu": "Port Vila",       "pg": "Port Moresby",   "tl": "Dili",
    "kp": "Pyongyang",       "cy": "Nicosia",        "mt": "Valletta",
}

DIFF_COLORS = {
    "easy":   (80,  220, 100),   # Yeşil
    "medium": (255, 200,  50),   # Sarı
    "hard":   (255, 100,  60),   # Turuncu
    "expert": (220,  60,  60),   # Kırmızı
}

# ─────────────────────────────────────────────────────────────
# BRAINROT KARAKTERLER  (dosya adı (uzantsız) → isim, zorluk)
# brainrot_images/ klasöründe .jpg veya .png olarak olmalı
# ─────────────────────────────────────────────────────────────
BRAINROT_CHARS = {
    "tralalero_tralala":    ("Tralalero Tralala",    "easy"),
    "bombardiro_crocodilo": ("Bombardiro Crocodilo",  "easy"),
    "tung_tung_sahur":      ("Tung Tung Sahur",       "easy"),
    "cappuccino_assassino": ("Cappuccino Assassino",  "medium"),
    "chimpanzini_bananini": ("Chimpanzini Bananini",  "medium"),
    "lirili_larila":        ("Lirili Larila",         "medium"),
    "la_vaca_saturno":      ("La Vaca Saturno",       "medium"),
    "glorbo_fruttodrillo":  ("Glorbo Fruttodrillo",   "hard"),
    "swag_soda":            ("Swag Soda",             "hard"),
    "brr_brr_patapim":      ("Brr Brr Patapim",       "hard"),
    "bobritto_bandito":     ("Bobritto Bandito",      "hard"),
    "bombombini_gusini":    ("Bombombini Gusini",     "hard"),
    "burbaloni_luliloli":   ("Burbaloni Luliloli",    "expert"),
    "frigo_camelo":         ("Frigo Camelo",          "expert"),
    "rhino_toasterino":     ("Rhino Toasterino",      "expert"),
    "boneca_ambalabu":      ("Boneca Ambalabu",       "expert"),
    "job_job_sahur":        ("Job Job Sahur",         "expert"),
    "karkerkar_kurkur":     ("Karkerkar Kurkur",      "expert"),
    "la_esok_sekolah":      ("La Esok Sekolah",       "expert"),
    "svinina_bombardino":   ("Svinina Bombardino",    "expert"),
}


# ─────────────────────────────────────────────────────────────
# YARDIMCI: FONT YÜKLEYİCİ
# ─────────────────────────────────────────────────────────────
def load_font(size, bold=False):
    paths = []
    if bold:
        paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "C:\\Windows\\Fonts\\arialbd.ttf",
            "C:\\Windows\\Fonts\\impact.ttf",
        ]
    else:
        paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "C:\\Windows\\Fonts\\arial.ttf",
        ]
    for p in paths:
        if os.path.exists(p):
            try: return ImageFont.truetype(p, size)
            except: continue
    return ImageFont.load_default(size=size)


# ─────────────────────────────────────────────────────────────
# BAYRAK İNDİR
# ─────────────────────────────────────────────────────────────
def download_flag(code):
    url = f"https://flagcdn.com/w320/{code}.png"
    try:
        r = requests.get(url, timeout=8)
        if r.status_code == 200:
            return Image.open(_io.BytesIO(r.content)).convert("RGBA")
    except Exception as e:
        print(f"  [WARN] Bayrak indirilemedi ({code}): {e}")
    return None


# ─────────────────────────────────────────────────────────────
# SORULARI SEÇ  (3 easy, 3 medium, 3 hard, 1 expert)
# ─────────────────────────────────────────────────────────────
def pick_questions():
    by_diff = {"easy": [], "medium": [], "hard": [], "expert": []}
    for code, (name, diff) in COUNTRIES.items():
        by_diff[diff].append((code, name))

    selected = []
    for diff, count in [("easy", 3), ("medium", 3), ("hard", 3), ("expert", 1)]:
        chosen = random.sample(by_diff[diff], count)
        for code, name in chosen:
            selected.append((code, name, diff))
    return selected


# ─────────────────────────────────────────────────────────────
# BRAINROT SORULARI SEÇ  (3 easy, 3 medium, 3 hard, 1 expert)
# ─────────────────────────────────────────────────────────────
def pick_brainrot_questions():
    by_diff = {"easy": [], "medium": [], "hard": [], "expert": []}
    for key, (name, diff) in BRAINROT_CHARS.items():
        by_diff[diff].append((key, name))

    selected = []
    for diff, count in [("easy", 3), ("medium", 3), ("hard", 3), ("expert", 1)]:
        pool = by_diff[diff]
        chosen = random.sample(pool, min(count, len(pool)))
        for key, name in chosen:
            selected.append((key, name, diff))
    return selected


def pick_capital_questions():
    by_diff = {"easy": [], "medium": [], "hard": [], "expert": []}
    for code, (name, diff) in COUNTRIES.items():
        capital = CAPITALS.get(code)
        if capital:
            by_diff[diff].append((code, capital))
    selected = []
    for diff, count in [("easy", 3), ("medium", 3), ("hard", 3), ("expert", 1)]:
        chosen = random.sample(by_diff[diff], count)
        for code, capital in chosen:
            selected.append((code, capital, diff))
    return selected


def load_brainrot_image(key):
    """brainrot_images/ klasöründen karakter görselini yükle (.jpg veya .png)."""
    folder = os.path.join(script_dir, "brainrot_images")
    for ext in ("jpg", "jpeg", "png", "webp"):
        path = os.path.join(folder, f"{key}.{ext}")
        if os.path.exists(path):
            try:
                return Image.open(path).convert("RGBA")
            except Exception as e:
                print(f"  [WARN] Gorsel acilamadi ({path}): {e}")
    print(f"  [WARN] Brainrot gorseli bulunamadi: {key}")
    return None


# ─────────────────────────────────────────────────────────────
# FRAME ÜRETİCİ
# ─────────────────────────────────────────────────────────────
def load_background():
    """Rastgele arkaplan seç, yoksa koyu renk döndür."""
    available = [i for i in range(1, 11)
                 if os.path.exists(os.path.join(script_dir, f"arkaplan{i}.jpg"))]
    if not available:
        return None
    idx = random.choice(available)
    path = os.path.join(script_dir, f"arkaplan{idx}.jpg")
    img = Image.open(path).convert("RGB")
    # 1080x1920'ye kırp
    iw, ih = img.size
    ir, tr = iw/ih, W/H
    if ir > tr:
        nw = int(tr * ih)
        img = img.crop(((iw-nw)//2, 0, (iw-nw)//2+nw, ih))
    else:
        nh = int(iw/tr)
        img = img.crop((0, (ih-nh)//2, iw, (ih-nh)//2+nh))
    img = img.resize((W, H), Image.Resampling.LANCZOS)
    print(f"  Arkaplan: arkaplan{idx}.jpg")
    return img


def get_overlay_and_text_colors(bg_img):
    """Arka planın parlaklığına göre overlay ve yazı rengi seç."""
    if bg_img is None:
        return (0,0,0,180), (255,255,255), (255,220,50)
    # Küçük örnek alarak ortalama parlaklık hesapla
    sample = bg_img.resize((20, 20)).convert("L")
    import numpy as _np
    brightness = _np.array(sample).mean()
    # Açık arka plan → daha koyu overlay
    overlay_alpha = 200 if brightness > 128 else 160
    return (0,0,0,overlay_alpha), (255,255,255), (255,220,50)


def make_intro_frame(flag_img, bg_img=None, quiz_mode="flag"):
    """Hook frame — izleyiciyi ilk 2 saniyede yakala."""
    if bg_img:
        img = bg_img.copy()
    else:
        img = Image.new("RGB", (W, H), (12, 12, 28))

    overlay_col, text_col, accent_col = get_overlay_and_text_colors(bg_img)
    r, g, b, a = overlay_col
    overlay = Image.new("RGBA", (W, H), (r, g, b, max(0, a - 40)))
    img = img.convert("RGBA")
    img = Image.alpha_composite(img, overlay)
    img = img.convert("RGB")
    draw = ImageDraw.Draw(img)

    # Üst başlık
    f_title = load_font(80, bold=True)
    if quiz_mode == "brainrot":
        title = "BRAINROT QUIZ"
    elif quiz_mode == "capital":
        title = "CAPITAL QUIZ"
    elif quiz_mode == "multichoice":
        title = "FLAG QUIZ"
    elif quiz_mode == "trivia":
        title = "TRIVIA QUIZ"
    else:
        title = "FLAG QUIZ"
    bbox = draw.textbbox((0, 0), title, font=f_title)
    tx = (W - (bbox[2] - bbox[0])) // 2
    draw.text((tx + 4, 65), title, font=f_title, fill=(0, 0, 0))
    draw.text((tx, 62), title, font=f_title, fill=accent_col)

    # Büyük bayrak/görsel (ekran ortası)
    if flag_img:
        fw, fh = flag_img.size
        max_w, max_h = 960, 580
        scale = min(max_w / fw, max_h / fh)
        nw, nh = int(fw * scale), int(fh * scale)
        flag_r = flag_img.resize((nw, nh), Image.Resampling.LANCZOS)
        flag_y = 220
        border = 10
        draw.rectangle(
            [(W // 2 - nw // 2 - border + 6, flag_y - border + 6),
             (W // 2 + nw // 2 + border + 6, flag_y + nh + border + 6)],
            fill=(0, 0, 0)
        )
        draw.rectangle(
            [(W // 2 - nw // 2 - border, flag_y - border),
             (W // 2 + nw // 2 + border, flag_y + nh + border)],
            outline=accent_col, width=border
        )
        img.paste(flag_r, (W // 2 - nw // 2, flag_y),
                  flag_r if flag_r.mode == "RGBA" else None)

    # ── HOOK METNİ (ortada büyük, dikkat çekici) ─────────────
    hook_lines = {
        "flag":        ["Can YOU get", "10/10?"],
        "brainrot":    ["Do you know", "all of them?"],
        "capital":     ["Can you name", "every capital?"],
        "multichoice": ["Can YOU get", "10/10?"],
        "trivia":      ["How smart", "are you really?"],
    }
    lines = hook_lines.get(quiz_mode, ["Can YOU get", "10/10?"])

    f_hook = load_font(88, bold=True)
    hook_y = H - 680
    for line in lines:
        bbox_h = draw.textbbox((0, 0), line, font=f_hook)
        hx = (W - (bbox_h[2] - bbox_h[0])) // 2
        for dx, dy in [(-3,0),(3,0),(0,-3),(0,3),(-2,-2),(2,2),(-2,2),(2,-2)]:
            draw.text((hx+dx, hook_y+dy), line, font=f_hook, fill=(0, 0, 0))
        draw.text((hx, hook_y), line, font=f_hook, fill=(255, 255, 255))
        hook_y += (bbox_h[3] - bbox_h[1]) + 12

    # Alt — "Comment your score below!"
    f_cta = load_font(52, bold=True)
    cta = "Comment your score below!"
    bbox_c = draw.textbbox((0, 0), cta, font=f_cta)
    cx2 = (W - (bbox_c[2] - bbox_c[0])) // 2
    for dx, dy in [(-2,0),(2,0),(0,-2),(0,2)]:
        draw.text((cx2+dx, H-162+dy), cta, font=f_cta, fill=(0, 0, 0))
    draw.text((cx2, H - 162), cta, font=f_cta, fill=accent_col)

    return img


def make_frame(questions, current_idx, revealed_up_to, flag_img,
               bar_progress=None, countdown=None, bg_img=None, quiz_mode="flag", score=0):
    """
    questions      : [(code, name, diff), ...]
    current_idx    : şu an gösterilen bayrak (0-9)
    revealed_up_to : kaçıncı cevaba kadar açık (-1 = hiç)
    flag_img       : PIL Image
    bar_progress   : 0.0-1.0 arası özel bar doluluk (None = otomatik)
    bg_img         : arka plan PIL Image (None = koyu düz renk)
    """
    if bg_img:
        img = bg_img.copy()
    else:
        img = Image.new("RGB", (W, H), (12, 12, 28))

    # Koyu overlay — renkli arka planda yazı okunabilsin
    overlay_col, text_col, accent_col = get_overlay_and_text_colors(bg_img)
    overlay = Image.new("RGBA", (W, H), overlay_col)
    img = img.convert("RGBA")
    img = Image.alpha_composite(img, overlay)
    img = img.convert("RGB")
    draw = ImageDraw.Draw(img)

    # ── Üst başlık ───────────────────────────────────────────
    f_title = load_font(72, bold=True)
    if quiz_mode == "brainrot":
        title = "BRAINROT QUIZ"
    elif quiz_mode == "capital":
        title = "CAPITAL QUIZ"
    else:
        title = "FLAG QUIZ"
    bbox = draw.textbbox((0,0), title, font=f_title)
    tx = (W - (bbox[2]-bbox[0])) // 2
    draw.text((tx+3, 53), title, font=f_title, fill=(0,0,0))
    draw.text((tx, 50), title, font=f_title, fill=accent_col)

    # ── İlerleme çubuğu ──────────────────────────────────────
    bar_x, bar_y, bar_w, bar_h = 60, 145, W-120, 18
    draw.rectangle([bar_x, bar_y, bar_x+bar_w, bar_y+bar_h],
                   fill=(40,40,60), outline=(80,80,100), width=2)
    if bar_progress is None:
        bar_progress = (current_idx + 1) / len(questions)
    filled = int(bar_w * bar_progress)
    if filled > 0:
        draw.rectangle([bar_x, bar_y, bar_x+filled, bar_y+bar_h],
                       fill=accent_col)


    # ── Bayrak görseli (merkez üst) ───────────────────────────
    flag_area_y = 190
    if flag_img:
        fw, fh = flag_img.size
        max_w, max_h = 700, 420
        scale = min(max_w/fw, max_h/fh)
        nw, nh = int(fw*scale), int(fh*scale)
        flag_r = flag_img.resize((nw, nh), Image.Resampling.LANCZOS)

        # Çerçeve
        border = 6
        frame_rect = [(W//2 - nw//2 - border, flag_area_y - border),
                      (W//2 + nw//2 + border, flag_area_y + nh + border)]
        draw.rectangle(frame_rect, outline=(255,220,50), width=border)

        img.paste(flag_r, (W//2 - nw//2, flag_area_y),
                  flag_r if flag_r.mode == "RGBA" else None)

    # ── Capital modunda ülke adını bayrak altında göster ──────
    if quiz_mode == "capital":
        cur_code = questions[current_idx][0]
        country_name = COUNTRIES.get(cur_code, (cur_code,))[0]
        f_country = load_font(54, bold=True)
        bbox_cn = draw.textbbox((0, 0), country_name, font=f_country)
        cnx = (W - (bbox_cn[2] - bbox_cn[0])) // 2
        draw.text((cnx + 2, 622), country_name, font=f_country, fill=(0, 0, 0))
        draw.text((cnx, 620), country_name, font=f_country, fill=(255, 255, 255))

    # ── Liste ─────────────────────────────────────────────────
    list_y = 660
    f_label = load_font(42, bold=True)
    f_item  = load_font(40, bold=False)
    f_ans   = load_font(40, bold=True)

    diff_labels = {"easy": "EASY", "medium": "MEDIUM",
                   "hard": "HARD", "expert": "EXPERT"}
    last_diff = None
    line_h = 68

    for i, (code, name, diff) in enumerate(questions):
        # Zorluk başlığı
        if diff != last_diff:
            col = DIFF_COLORS[diff]
            draw.text((70, list_y), diff_labels[diff],
                      font=f_label, fill=col)
            list_y += 52
            last_diff = diff

        # Sıra numarası
        num_str = f"{i+1}."
        draw.text((70, list_y), num_str, font=f_item, fill=(180,180,180))

        if i <= revealed_up_to:
            # Cevap açık
            col = DIFF_COLORS[diff]
            draw.text((120, list_y), name, font=f_ans, fill=col)
        else:
            # Boş çizgi
            draw.line([(120, list_y+32), (380, list_y+32)],
                      fill=(80,80,80), width=2)

        list_y += line_h

    # ── Alt soru notu ─────────────────────────────────────────
    f_note = load_font(44, bold=True)
    if quiz_mode == "brainrot":
        note = f"Name this character! ({current_idx+1}/10)"
    elif quiz_mode == "capital":
        cur_code = questions[current_idx][0]
        cur_country = COUNTRIES.get(cur_code, (cur_code,))[0]
        note = f"Capital of {cur_country}? ({current_idx+1}/10)"
    else:
        note = f"Which country? ({current_idx+1}/10)"
    bbox = draw.textbbox((0,0), note, font=f_note)
    nx = (W - (bbox[2]-bbox[0])) // 2
    draw.text((nx+2, H-408), note, font=f_note, fill=(0,0,0))
    draw.text((nx, H-410), note, font=f_note, fill=text_col)

    # ── Sayaç (alt orta, büyük renkli) ───────────────────────
    if countdown is not None:
        f_cd = load_font(200, bold=True)
        cd_str = str(countdown)
        cd_col = {3:(80,220,100), 2:(255,200,50), 1:(255,60,60)}.get(countdown, (255,255,255))
        bbox = draw.textbbox((0,0), cd_str, font=f_cd)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        cx = (W - tw) // 2
        cy = H - th - 80
        # Glow efekti (çoklu gölge)
        for offset in range(12, 0, -3):
            glow_col = tuple(int(c * 0.3) for c in cd_col)
            draw.text((cx - offset, cy), cd_str, font=f_cd, fill=glow_col)
            draw.text((cx + offset, cy), cd_str, font=f_cd, fill=glow_col)
            draw.text((cx, cy - offset), cd_str, font=f_cd, fill=glow_col)
            draw.text((cx, cy + offset), cd_str, font=f_cd, fill=glow_col)
        # Siyah outline
        for ox, oy in [(-4,0),(4,0),(0,-4),(0,4),(-3,-3),(3,3),(-3,3),(3,-3)]:
            draw.text((cx+ox, cy+oy), cd_str, font=f_cd, fill=(0,0,0))
        # Ana sayı
        draw.text((cx, cy), cd_str, font=f_cd, fill=cd_col)

    return img


# ─────────────────────────────────────────────────────────────
# VİDEO OLUŞTUR
# ─────────────────────────────────────────────────────────────
def create_video(questions, quiz_mode="flag"):
    label = "Karakterler" if quiz_mode == "brainrot" else "Bayraklar / Ulkeler"
    print(f"{label} yukleniyor...")
    flags = {}
    for key, name, diff in questions:
        print(f"  {name} ({key})...", end=" ")
        if quiz_mode == "brainrot":
            flags[key] = load_brainrot_image(key)
        else:
            flags[key] = download_flag(key)
        print("OK" if flags[key] else "HATA")

    print("\nArkaplan yukleniyor...")
    bg_img = load_background()
    print("\nFrameler olusturuluyor...")
    clips = []

    # Her bayrak için:
    #  - 3 sn: o bayrak gösterilir, önceki cevaplar açık, bu soru boş
    #  - 1 sn: cevap açılır (reveal frame)
    import numpy as np
    from moviepy.audio.AudioClip import AudioArrayClip, CompositeAudioClip

    SR = 44100  # sample rate

    from moviepy.editor import AudioFileClip as AFC

    tick_mp3  = os.path.join(script_dir, "tick.mp3")
    tick_clip = AFC(tick_mp3).volumex(0.9) if os.path.exists(tick_mp3) else None

    def make_ding(freq=1200, dur=0.2, volume=0.9):
        """Cevap açılırken ding sesi (sentetik)."""
        t = np.linspace(0, dur, int(SR * dur), endpoint=False)
        wave = np.sin(2 * np.pi * freq * t) * np.linspace(1,0,int(SR*dur)) * volume
        stereo = np.column_stack([wave, wave]).astype(np.float32)
        return AudioArrayClip(stereo, fps=SR)

    sfx_path = os.path.join(script_dir, "soundeffect.mp3")
    sfx_clip = AFC(sfx_path).volumex(0.9) if os.path.exists(sfx_path) else None

    def make_whoosh():
        """Geçiş sesi — soundeffect.mp3 kullan."""
        if sfx_clip:
            return sfx_clip
        # Yedek sentetik
        dur = 0.3
        t = np.linspace(0, dur, int(SR * dur), endpoint=False)
        freq_sweep = np.linspace(200, 1200, len(t))
        phase = np.cumsum(freq_sweep) / SR
        wave = np.sin(2 * np.pi * phase)
        env = np.array(np.linspace(0,1,len(t)//3).tolist() + np.linspace(1,0,len(t)-len(t)//3).tolist()[:len(t)-len(t)//3])
        wave = wave * env * 0.5
        stereo = np.column_stack([wave, wave]).astype(np.float32)
        return AudioArrayClip(stereo, fps=SR)

    # ── Intro frame (thumbnail için — sadece bayrak/karakter, cevap listesi yok) ──
    first_code = questions[0][0]
    img_intro = make_intro_frame(flags[first_code], bg_img=bg_img, quiz_mode=quiz_mode)
    path_intro = "_frame_intro.jpg"
    img_intro.save(path_intro, quality=92)
    # Thumbnail olarak da kaydet (upload sonrası set edilecek)
    clips.append(ImageClip(path_intro, duration=2))

    n = len(questions)
    ding_times   = []  # cevap açılma zamanları
    tick_starts  = []  # countdown başlangıçları
    whoosh_times = []  # bayrak geçiş zamanları
    global_t = 2.0     # intro 2 sn sürdü

    for i, (code, name, diff) in enumerate(questions):
        bar_start = i / n
        bar_end   = (i + 1) / n
        score_so_far = i  # bu sorudan önce kaç cevap açıldı
        # 6 x 0.5sn = 3sn: sayaç 3→2→1
        countdown_map = {0:3, 1:3, 2:2, 3:2, 4:1, 5:1}
        steps = 6
        for s in range(steps):
            progress = bar_start + (bar_end - bar_start) * (s / steps)
            cd = countdown_map[s]
            img_q = make_frame(questions, i, i-1, flags[code],
                               bar_progress=progress, countdown=cd, bg_img=bg_img,
                               quiz_mode=quiz_mode, score=score_so_far)
            path_q = f"_frame_q_{i}_{s}.jpg"
            img_q.save(path_q, quality=92)
            clips.append(ImageClip(path_q, duration=0.5))
            if s == 0:
                tick_starts.append(global_t)
                if i > 0:
                    whoosh_times.append(max(0, global_t - 0.35))
            global_t += 0.5

        # Cevap reveal (1 sn) — ding sesi
        img_a = make_frame(questions, i, i, flags[code],
                           bar_progress=bar_end, countdown=None, bg_img=bg_img,
                           quiz_mode=quiz_mode, score=i+1)
        path_a = f"_frame_a_{i}.jpg"
        img_a.save(path_a, quality=92)
        clips.append(ImageClip(path_a, duration=1))
        ding_times.append(global_t)
        global_t += 1.0

    # Son frame: tüm cevaplar açık, 3 sn — güçlü CTA
    img_end = make_frame(questions, 9, 9, flags[questions[-1][0]], bg_img=bg_img,
                         quiz_mode=quiz_mode, score=10)
    img_end_draw = ImageDraw.Draw(img_end)
    f_end  = load_font(72, bold=True)
    f_end2 = load_font(56, bold=True)
    # Satır 1
    line1 = "Comment your score below!"
    bbox1 = img_end_draw.textbbox((0,0), line1, font=f_end)
    ex1 = (W - (bbox1[2]-bbox1[0])) // 2
    img_end_draw.text((ex1+3, H-240), line1, font=f_end, fill=(0,0,0))
    img_end_draw.text((ex1,   H-243), line1, font=f_end, fill=(255,220,50))
    # Satır 2
    line2 = "LIKE if you got 10/10"
    bbox2 = img_end_draw.textbbox((0,0), line2, font=f_end2)
    ex2 = (W - (bbox2[2]-bbox2[0])) // 2
    img_end_draw.text((ex2+2, H-158), line2, font=f_end2, fill=(0,0,0))
    img_end_draw.text((ex2,   H-160), line2, font=f_end2, fill=(80,220,100))
    path_end = "_frame_end.jpg"
    img_end.save(path_end, quality=92)
    clips.append(ImageClip(path_end, duration=3))

    print("Video birlestiriliyor...")
    final = concatenate_videoclips(clips, method="compose")
    total_dur = final.duration

    # Tik + Ding seslerini oluştur ve composite et
    audio_clips = []
    # Her bayrak için 3 saniyelik tick sesi ekle
    if tick_clip:
        for t in tick_starts:
            seg = tick_clip.subclip(0, min(3.0, tick_clip.duration))
            audio_clips.append(seg.set_start(t))
    for t in whoosh_times:
        if t < total_dur:
            audio_clips.append(make_whoosh().set_start(t))
    for t in ding_times:
        if t < total_dur:
            audio_clips.append(make_ding(freq=1200).set_start(t))

    # Arka plan müziği — NCS'ten rastgele indir (yt-dlp), çok düşük ses
    SC_QUERIES = [
        "scsearch1:NCS electronic instrumental upbeat",
        "scsearch1:NCS gaming music no copyright",
        "scsearch1:royalty free electronic quiz music",
        "scsearch1:NCS release instrumental energetic",
        "scsearch1:no copyright music upbeat electronic",
        "scsearch1:NCS house music instrumental",
        "scsearch1:copyright free background music quiz",
    ]
    tmp_music = os.path.join(script_dir, "_bg_music.mp3")
    chosen_music = None
    try:
        import yt_dlp
        try:
            import imageio_ffmpeg
            ffmpeg_bin = imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            ffmpeg_bin = "ffmpeg"

        query = random.choice(SC_QUERIES)
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": tmp_music.replace(".mp3", ""),
            "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}],
            "ffmpeg_location": ffmpeg_bin,
            "quiet": True,
            "no_warnings": True,
        }
        print(f"Muzik indiriliyor (SoundCloud)...")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([query])
        if os.path.exists(tmp_music):
            chosen_music = tmp_music
            print("Muzik indirildi.")
    except Exception as e:
        print(f"Muzik indirme hatasi: {e}")

    if not chosen_music:
        local = os.path.join(script_dir, "music.mp3")
        if os.path.exists(local):
            chosen_music = local
            print("Yedek muzik kullaniliyor.")

    if chosen_music:
        try:
            from moviepy.editor import AudioFileClip
            bg = AudioFileClip(chosen_music)
            start = random.randint(0, max(0, int(bg.duration) - int(total_dur) - 5))
            bg = bg.subclip(start, min(start + total_dur, bg.duration))
            bg = bg.volumex(0.03)   # çok düşük — efektler baskın kalsın
            audio_clips.append(bg)
            print("Muzik eklendi.")
        except Exception as e:
            print(f"Muzik eklenemedi: {e}")
        finally:
            try: os.remove(tmp_music)
            except: pass

    if audio_clips:
        final = final.set_audio(CompositeAudioClip(audio_clips))

    if quiz_mode == "brainrot":
        out_path = OUTPUT_VIDEO_BRAINROT
    elif quiz_mode == "capital":
        out_path = OUTPUT_VIDEO_CAPITAL
    else:
        out_path = OUTPUT_VIDEO
    final.write_videofile(out_path, fps=24, codec="libx264", logger=None)
    print(f"\n[OK] Video hazir: {out_path}")

    # Temizlik
    for i in range(10):
        for s in range(6):
            try: os.remove(f"_frame_q_{i}_{s}.jpg")
            except: pass
        try: os.remove(f"_frame_a_{i}.jpg")
        except: pass
    try: os.remove("_frame_end.jpg")
    except: pass
    try: os.remove("_frame_intro.jpg")
    except: pass


# ─────────────────────────────────────────────────────────────
# YOUTUBE'A YÜKLE
# ─────────────────────────────────────────────────────────────
def upload_to_youtube(questions):
    print("\nYouTube'a yukleniyor...")

    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    if not os.path.exists(SECRET_PATH):
        print(f"[ERROR] {SECRET_PATH} bulunamadi. Yukleme atlaniyor.")
        return

    SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
    creds = None

    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            from google_auth_oauthlib.flow import InstalledAppFlow
            flow = InstalledAppFlow.from_client_secrets_file(SECRET_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, 'w') as f:
            f.write(creds.to_json())

    # Groq ile viral başlık üret — geniş ve çeşitli hook listesi
    hooks = [
        # Curiosity / challenge angle
        "Bet you can't name all 10 flags",
        "My friend got 3/10. Can you beat him?",
        "Stop scrolling — name this flag",
        "I failed this quiz. Can you pass?",
        "Your geography teacher would be disappointed",
        # Score / result angle
        "Score 10/10 and you're a genius",
        "Most people quit at flag #7",
        "Average person gets 4. What's yours?",
        "10/10 = legend. 5/10 = normal. 0/10 = ???",
        "Rate your score in the comments",
        # Surprising / contrarian
        "These flags look identical but aren't",
        "The hardest flag quiz on YouTube",
        "No one gets the last flag right",
        "Flag #9 tricks everyone",
        "You think you know flags? Think again",
        # Identity / ego
        "Real geography nerd gets 10/10",
        "This separates travelers from tourists",
        "Your passport knows these. Do you?",
        "World traveler or just pretending?",
        "How cultured are you really?",
    ]
    hook = random.choice(hooks)

    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content":
                f'Create a YouTube Shorts title for a 10-flag quiz (Easy to Expert). '
                f'Use this angle/hook: "{hook}". '
                f'Rules: max 60 chars, end with #shorts, do NOT use the words "Only 1%" or "Geography", '
                f'must feel natural and scroll-stopping. ONLY THE TITLE, no quotes:'}]
        )
        title = resp.choices[0].message.content.strip().replace('"', '').strip()
        if not title:
            raise ValueError("Bos baslik")
    except Exception as e:
        print(f"[WARN] Groq hatasi ({e}). Yedek baslik kullaniliyor.")
        title = f"{hook} #shorts"

    desc = (
        "Can you name all 10 country flags? Easy → Expert difficulty!\n\n"
        "3 Easy | 3 Medium | 3 Hard | 1 Expert\n\n"
        "How many did you get right? Comment below! 👇\n"
        "🔔 Subscribe for a new quiz every day!\n\n"
        "#Shorts #flagquiz #geography #flags #quiz #worldflags #countryflags "
        "#geographyquiz #trivia #challenge #quiztime #viral"
    )
    tags = [
        "flag quiz", "flags", "geography", "world flags", "country flags",
        "quiz", "shorts", "geography quiz", "flag challenge", "educational",
        "trivia", "flag game", "country quiz", "geography challenge",
        "flag identification", "world geography", "quiz challenge"
    ]

    print(f"Baslik: {title}")

    yt = build('youtube', 'v3', credentials=creds)
    body = {
        'snippet': {
            'title': title[:100],
            'description': desc,
            'tags': tags,
            'categoryId': '27'  # Education
        },
        'status': {
            'privacyStatus':           'public',
            'selfDeclaredMadeForKids': False,
            'containsSyntheticMedia':  False
        }
    }

    try:
        media = MediaFileUpload(OUTPUT_VIDEO, mimetype='video/mp4', resumable=True)
        req = yt.videos().insert(part='snippet,status', body=body, media_body=media)
        response = None
        while response is None:
            status, response = req.next_chunk()
            if status:
                print(f"  %{int(status.progress() * 100)}")
        video_id = response['id']
        print(f"\n[OK] Yayinlandi! https://youtube.com/shorts/{video_id}")
        return video_id
    except Exception as e:
        print(f"[ERROR] YouTube yukleme hatasi: {e}")
        return None


# ─────────────────────────────────────────────────────────────
# BRAINROT YOUTUBE UPLOAD
# ─────────────────────────────────────────────────────────────
def upload_to_youtube_brainrot(questions):
    print("\nYouTube'a (brainrot) yukleniyor...")

    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    if not os.path.exists(SECRET_PATH):
        print(f"[ERROR] {SECRET_PATH} bulunamadi. Yukleme atlaniyor.")
        return

    SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            from google_auth_oauthlib.flow import InstalledAppFlow
            flow = InstalledAppFlow.from_client_secrets_file(SECRET_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, 'w') as f:
            f.write(creds.to_json())

    hooks = [
        "Can you name all 10 brainrot characters?",
        "My friend got 3/10. Can you beat him?",
        "Stop scrolling — name this character",
        "I failed this quiz. Can you pass?",
        "True brainrot fan gets 10/10",
        "Score 10/10 and you're a legend",
        "Most people quit at character #7",
        "Average person gets 4. What's yours?",
        "10/10 = sigma. 0/10 = you're cooked",
        "Rate your score in the comments",
        "These characters look similar but aren't",
        "The hardest brainrot quiz on YouTube",
        "No one gets the last character right",
        "Character #9 tricks everyone",
        "You think you know brainrot? Think again",
        "Real brainrot nerd gets 10/10",
        "This separates real fans from casuals",
        "How deep is your brainrot really?",
        "Comment your score below",
        "Only real ones get 10/10",
    ]
    hook = random.choice(hooks)

    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content":
                f'Create a YouTube Shorts title for a 10-question brainrot character quiz (Easy to Expert). '
                f'Use this angle/hook: "{hook}". '
                f'Rules: max 60 chars, end with #shorts, must feel natural and scroll-stopping. '
                f'ONLY THE TITLE, no quotes:'}]
        )
        title = resp.choices[0].message.content.strip().replace('"', '').strip()
        if not title:
            raise ValueError("Bos baslik")
    except Exception as e:
        print(f"[WARN] Groq hatasi ({e}). Yedek baslik kullaniliyor.")
        title = f"{hook} #shorts"

    desc = (
        "Can you name all 10 brainrot characters? Easy → Expert difficulty!\n\n"
        "3 Easy | 3 Medium | 3 Hard | 1 Expert\n\n"
        "How many did you get right? Comment below! 👇\n"
        "🔔 Subscribe for a new quiz every day!\n\n"
        "#Shorts #brainrot #quiz #brainrotquiz #viral "
        "#tralalero #bombardiro #tungsung #brainrotcharacters #quiztime"
    )
    tags = [
        "brainrot", "brainrot quiz", "brainrot characters", "quiz", "shorts",
        "tralalero tralala", "bombardiro crocodilo", "tung tung sahur",
        "brainrot challenge", "viral", "funny quiz", "italian brainrot"
    ]

    print(f"Baslik: {title}")

    yt = build('youtube', 'v3', credentials=creds)
    body = {
        'snippet': {
            'title': title[:100],
            'description': desc,
            'tags': tags,
            'categoryId': '22'  # People & Blogs
        },
        'status': {
            'privacyStatus':           'public',
            'selfDeclaredMadeForKids': False,
            'containsSyntheticMedia':  False
        }
    }

    try:
        media = MediaFileUpload(OUTPUT_VIDEO_BRAINROT, mimetype='video/mp4', resumable=True)
        req = yt.videos().insert(part='snippet,status', body=body, media_body=media)
        response = None
        while response is None:
            status, response = req.next_chunk()
            if status:
                print(f"  %{int(status.progress() * 100)}")
        video_id = response['id']
        print(f"\n[OK] Yayinlandi! https://youtube.com/shorts/{video_id}")
        return video_id
    except Exception as e:
        print(f"[ERROR] YouTube yukleme hatasi: {e}")
        return None


# ─────────────────────────────────────────────────────────────
# CAPITAL YOUTUBE UPLOAD
# ─────────────────────────────────────────────────────────────
def upload_to_youtube_capital(questions):
    print("\nYouTube'a (capital) yukleniyor...")

    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    if not os.path.exists(SECRET_PATH):
        print(f"[ERROR] {SECRET_PATH} bulunamadi. Yukleme atlaniyor.")
        return

    SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            from google_auth_oauthlib.flow import InstalledAppFlow
            flow = InstalledAppFlow.from_client_secrets_file(SECRET_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, 'w') as f:
            f.write(creds.to_json())

    hooks = [
        "Can you name all 10 capitals?",
        "Most people fail at capital #7",
        "Average person gets 4/10. What's yours?",
        "Stop scrolling — what's this capital?",
        "I failed this quiz. Can you pass?",
        "Score 10/10 and you're a genius",
        "Your teacher would be proud of 10/10",
        "10/10 = geography king. 0/10 = oof",
        "Rate your score in the comments",
        "The hardest capital quiz on YouTube",
        "No one gets the last capital right",
        "Capital #9 tricks everyone",
        "You think you know capitals? Think again",
        "Real geography nerd gets 10/10",
        "Kids ace this. Can adults?",
        "This is easier than it looks. Or is it?",
        "How well do you know world capitals?",
        "My 10-year-old got 8/10. Can you beat her?",
        "School geography quiz. How do you score?",
        "Comment your score — no cheating!",
    ]
    hook = random.choice(hooks)

    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content":
                f'Create a YouTube Shorts title for a 10-question world capitals quiz (Easy to Expert). '
                f'Use this angle/hook: "{hook}". '
                f'Rules: max 60 chars, end with #shorts, must feel natural and scroll-stopping. '
                f'ONLY THE TITLE, no quotes:'}]
        )
        title = resp.choices[0].message.content.strip().replace('"', '').strip()
        if not title:
            raise ValueError("Bos baslik")
    except Exception as e:
        print(f"[WARN] Groq hatasi ({e}). Yedek baslik kullaniliyor.")
        title = f"{hook} #shorts"

    desc = (
        "Can you name all 10 world capitals? Easy → Expert difficulty!\n\n"
        "3 Easy | 3 Medium | 3 Hard | 1 Expert\n\n"
        "How many did you get right? Comment below! 👇\n"
        "🔔 Subscribe for a new quiz every day!\n\n"
        "#Shorts #capitalquiz #geography #worldcapitals #quiz "
        "#geographyquiz #trivia #capitals #educational #school #quiztime"
    )
    tags = [
        "capital quiz", "world capitals", "geography", "capitals", "quiz",
        "shorts", "geography quiz", "capital cities", "educational",
        "trivia", "country capitals", "school quiz", "kids quiz"
    ]

    print(f"Baslik: {title}")

    yt = build('youtube', 'v3', credentials=creds)
    body = {
        'snippet': {
            'title': title[:100],
            'description': desc,
            'tags': tags,
            'categoryId': '27'  # Education
        },
        'status': {
            'privacyStatus':           'public',
            'selfDeclaredMadeForKids': False,
            'containsSyntheticMedia':  False
        }
    }

    try:
        media = MediaFileUpload(OUTPUT_VIDEO_CAPITAL, mimetype='video/mp4', resumable=True)
        req = yt.videos().insert(part='snippet,status', body=body, media_body=media)
        response = None
        while response is None:
            status, response = req.next_chunk()
            if status:
                print(f"  %{int(status.progress() * 100)}")
        video_id = response['id']
        print(f"\n[OK] Yayinlandi! https://youtube.com/shorts/{video_id}")
        return video_id
    except Exception as e:
        print(f"[ERROR] YouTube yukleme hatasi: {e}")
        return None


# ─────────────────────────────────────────────────────────────
# GENEL KÜLTÜR QUIZ
# ─────────────────────────────────────────────────────────────

TRIVIA_FALLBACK = [
    {"question": "How many bones are in the adult human body?", "choices": ["196", "206", "216", "226"], "correct": 1, "category": "Science"},
    {"question": "What is the fastest animal on land?", "choices": ["Lion", "Horse", "Cheetah", "Falcon"], "correct": 2, "category": "Animals"},
    {"question": "Which planet is closest to the Sun?", "choices": ["Venus", "Earth", "Mars", "Mercury"], "correct": 3, "category": "Space"},
    {"question": "How many sides does an octagon have?", "choices": ["6", "7", "8", "9"], "correct": 2, "category": "Math"},
    {"question": "What is the capital of Australia?", "choices": ["Sydney", "Melbourne", "Canberra", "Brisbane"], "correct": 2, "category": "Geography"},
    {"question": "Which gas do plants absorb from the air?", "choices": ["Oxygen", "Nitrogen", "Carbon Dioxide", "Hydrogen"], "correct": 2, "category": "Science"},
    {"question": "How many continents are there on Earth?", "choices": ["5", "6", "7", "8"], "correct": 2, "category": "Geography"},
    {"question": "What is the largest ocean on Earth?", "choices": ["Atlantic", "Indian", "Arctic", "Pacific"], "correct": 3, "category": "Geography"},
    {"question": "How many strings does a standard guitar have?", "choices": ["4", "5", "6", "7"], "correct": 2, "category": "Music"},
    {"question": "What is the hardest natural substance on Earth?", "choices": ["Gold", "Iron", "Diamond", "Quartz"], "correct": 2, "category": "Science"},
    {"question": "Which country has the largest population?", "choices": ["USA", "India", "China", "Brazil"], "correct": 1, "category": "Geography"},
    {"question": "How many players are on a standard soccer team?", "choices": ["9", "10", "11", "12"], "correct": 2, "category": "Sports"},
    {"question": "What is the chemical symbol for water?", "choices": ["WA", "H2O", "HO2", "W2O"], "correct": 1, "category": "Science"},
    {"question": "Which animal has the longest neck?", "choices": ["Elephant", "Giraffe", "Camel", "Horse"], "correct": 1, "category": "Animals"},
    {"question": "How many hours are in a week?", "choices": ["144", "168", "172", "196"], "correct": 1, "category": "Math"},
    {"question": "What is the largest planet in our solar system?", "choices": ["Saturn", "Neptune", "Jupiter", "Uranus"], "correct": 2, "category": "Space"},
    {"question": "Which country invented pizza?", "choices": ["France", "Spain", "Greece", "Italy"], "correct": 3, "category": "Food"},
    {"question": "How many colors are in a rainbow?", "choices": ["5", "6", "7", "8"], "correct": 2, "category": "Science"},
    {"question": "What is the smallest country in the world?", "choices": ["Monaco", "Liechtenstein", "Vatican City", "San Marino"], "correct": 2, "category": "Geography"},
    {"question": "Which big cat can roar but cannot purr?", "choices": ["Cheetah", "Puma", "Lion", "Jaguar"], "correct": 2, "category": "Animals"},
    {"question": "How many teeth does an adult human normally have?", "choices": ["28", "30", "32", "34"], "correct": 2, "category": "Science"},
    {"question": "Which metal is liquid at room temperature?", "choices": ["Lead", "Tin", "Mercury", "Silver"], "correct": 2, "category": "Science"},
    {"question": "What is the longest river in the world?", "choices": ["Amazon", "Nile", "Yangtze", "Mississippi"], "correct": 1, "category": "Geography"},
    {"question": "How many legs does a spider have?", "choices": ["6", "8", "10", "12"], "correct": 1, "category": "Animals"},
    {"question": "Which planet has rings around it?", "choices": ["Mars", "Venus", "Jupiter", "Saturn"], "correct": 3, "category": "Space"},
]

CATEGORY_COLORS = {
    "Science":   (52,  152, 219),
    "Animals":   (46,  204, 113),
    "Geography": (230, 126,  34),
    "Space":     (155,  89, 182),
    "Math":      (231,  76,  60),
    "Music":     (241, 196,  15),
    "Sports":    (26,  188, 156),
    "Food":      (243, 156,  18),
    "History":   (189, 195, 199),
    "Technology":(52,  73,  94),
}


def generate_trivia_questions():
    """Groq ile 10 genel kültür sorusu üret; başarısız olursa fallback kullan."""
    try:
        from groq import Groq
        import json as _json
        client = Groq(api_key=GROQ_API_KEY)
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content":
                "Generate 10 multiple choice trivia questions for ages 11-17 (middle/high school level).\n"
                "Topics: science, animals, geography, history, space, nature, technology, food, sports.\n"
                "Rules: interesting, educational, family-friendly, not too easy, not university level.\n"
                "Return ONLY a valid JSON array, no other text:\n"
                '[{"question":"...","choices":["A","B","C","D"],"correct":0,"category":"Science"}]\n'
                "correct is the 0-based index of the correct answer. Generate exactly 10 questions."}]
        )
        text  = resp.choices[0].message.content.strip()
        start = text.find('[')
        end   = text.rfind(']') + 1
        qs    = _json.loads(text[start:end])
        if len(qs) >= 10:
            print("[OK] Groq ile 10 soru uretildi.")
            return qs[:10]
        raise ValueError("Yetersiz soru")
    except Exception as e:
        print(f"[WARN] Groq soru uretimi hatasi ({e}). Fallback kullaniliyor.")
        return random.sample(TRIVIA_FALLBACK, min(10, len(TRIVIA_FALLBACK)))


def make_trivia_frame(q_data, question_num, total, revealed, bg_img=None, bar_progress=None):
    """
    q_data   : {"question":..., "choices":[...], "correct":0, "category":...}
    revealed : True ise doğru=yeşil, yanlış=kırmızı
    """
    if bg_img:
        img = bg_img.copy()
    else:
        img = Image.new("RGB", (W, H), (12, 12, 28))

    overlay_col, text_col, accent_col = get_overlay_and_text_colors(bg_img)
    overlay = Image.new("RGBA", (W, H), overlay_col)
    img = img.convert("RGBA")
    img = Image.alpha_composite(img, overlay)
    img = img.convert("RGB")
    draw = ImageDraw.Draw(img)

    # ── Başlık ──────────────────────────────────────────────
    f_title = load_font(72, bold=True)
    title   = "TRIVIA QUIZ"
    bbox = draw.textbbox((0, 0), title, font=f_title)
    tx   = (W - (bbox[2] - bbox[0])) // 2
    draw.text((tx + 3, 53), title, font=f_title, fill=(0, 0, 0))
    draw.text((tx, 50),     title, font=f_title, fill=accent_col)

    # ── Progress bar ────────────────────────────────────────
    bar_x, bar_y, bar_w, bar_h = 60, 145, W - 120, 18
    draw.rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + bar_h], fill=(40, 40, 60))
    progress = bar_progress if bar_progress is not None else question_num / total
    filled   = int(bar_w * progress)
    if filled > 0:
        draw.rectangle([bar_x, bar_y, bar_x + filled, bar_y + bar_h], fill=accent_col)

    # ── Kategori rozeti ─────────────────────────────────────
    category  = q_data.get("category", "General")
    cat_color = CATEGORY_COLORS.get(category, (100, 100, 100))
    f_cat     = load_font(34, bold=True)
    cat_text  = f"● {category.upper()}"
    bbox_c    = draw.textbbox((0, 0), cat_text, font=f_cat)
    cw        = bbox_c[2] - bbox_c[0]
    cx        = (W - cw) // 2
    draw.rounded_rectangle([cx - 20, 178, cx + cw + 20, 224], radius=18, fill=cat_color)
    draw.text((cx, 182), cat_text, font=f_cat, fill="white")

    # ── Soru metni (sarmalanmış) ─────────────────────────────
    f_q     = load_font(52, bold=True)
    q_text  = q_data["question"]
    q_words = q_text.split()
    q_lines, cur = [], ""
    for word in q_words:
        test = (cur + " " + word).strip()
        if draw.textbbox((0, 0), test, font=f_q)[2] > W - 80 and cur:
            q_lines.append(cur)
            cur = word
        else:
            cur = test
    if cur:
        q_lines.append(cur)

    line_h = 68
    total_q_h = len(q_lines) * line_h
    q_start_y = 260 + max(0, (280 - total_q_h) // 2)
    for line in q_lines:
        bbox_l = draw.textbbox((0, 0), line, font=f_q)
        lx = (W - (bbox_l[2] - bbox_l[0])) // 2
        draw.text((lx + 2, q_start_y + 2), line, font=f_q, fill=(0, 0, 0))
        draw.text((lx, q_start_y),         line, font=f_q, fill=text_col)
        q_start_y += line_h

    # ── Soru numarası ────────────────────────────────────────
    f_num  = load_font(40, bold=False)
    num_t  = f"Question {question_num}/{total}"
    bbox_n = draw.textbbox((0, 0), num_t, font=f_num)
    draw.text(((W - (bbox_n[2] - bbox_n[0])) // 2, 568),
              num_t, font=f_num, fill=(160, 160, 160))

    # ── 4 Şık (2×2 grid) ────────────────────────────────────
    labels   = ["A", "B", "C", "D"]
    correct  = q_data["correct"]
    btn_w    = 472
    btn_h    = 155
    gap_x    = 24
    gap_y    = 24
    start_x  = (W - btn_w * 2 - gap_x) // 2
    start_y  = 640
    f_lbl    = load_font(54, bold=True)
    f_opt    = load_font(38, bold=False)
    f_opt_sm = load_font(30, bold=False)

    for i, choice_text in enumerate(q_data["choices"]):
        col = i % 2
        row = i // 2
        bx  = start_x + col * (btn_w + gap_x)
        by  = start_y + row * (btn_h + gap_y)

        if not revealed:
            bg_col     = (35, 35, 58)
            lbl_col    = accent_col
            txt_col    = (220, 220, 220)
            border_col = (70, 70, 100)
        elif i == correct:
            bg_col     = (25, 150, 65)
            lbl_col    = (255, 255, 255)
            txt_col    = (255, 255, 255)
            border_col = (50, 220, 100)
        else:
            bg_col     = (70, 25, 25)
            lbl_col    = (180, 80, 80)
            txt_col    = (130, 130, 130)
            border_col = (100, 40, 40)

        draw.rounded_rectangle([bx, by, bx + btn_w, by + btn_h],
                                radius=22, fill=bg_col, outline=border_col, width=3)
        draw.text((bx + 20, by + (btn_h - 60) // 2), labels[i], font=f_lbl, fill=lbl_col)

        div_x = bx + 82
        draw.line([(div_x, by + 18), (div_x, by + btn_h - 18)], fill=border_col, width=2)

        name_x     = div_x + 16
        max_name_w = bx + btn_w - name_x - 60
        bbox_ch    = draw.textbbox((0, 0), choice_text, font=f_opt)
        f_use      = f_opt if bbox_ch[2] - bbox_ch[0] <= max_name_w else f_opt_sm
        name_y     = by + (btn_h - (46 if f_use == f_opt else 34)) // 2
        draw.text((name_x, name_y), choice_text, font=f_use, fill=txt_col)

        # Doğru cevaba mavi tik
        if revealed and i == correct:
            ts = 46
            tx = bx + btn_w - ts - 14
            ty = by + (btn_h - ts) // 2
            draw.ellipse([tx, ty, tx + ts, ty + ts], fill=(29, 155, 240))
            draw.line([(tx + ts*0.22, ty + ts*0.52), (tx + ts*0.44, ty + ts*0.72)],
                      fill="white", width=max(2, int(ts*0.13)))
            draw.line([(tx + ts*0.44, ty + ts*0.72), (tx + ts*0.78, ty + ts*0.28)],
                      fill="white", width=max(2, int(ts*0.13)))

    return img


def create_trivia_video(questions):
    """Genel kültür quiz videosu oluştur."""
    bg_img = load_background()
    print("Trivia video olusturuluyor...")
    clips = []

    import numpy as np
    from moviepy.audio.AudioClip import AudioArrayClip, CompositeAudioClip
    from moviepy.editor import AudioFileClip as AFC

    SR        = 44100
    tick_mp3  = os.path.join(script_dir, "tick.mp3")
    tick_clip = AFC(tick_mp3).volumex(0.7) if os.path.exists(tick_mp3) else None

    def make_ding(freq=1100, dur=0.25, volume=0.85):
        t      = np.linspace(0, dur, int(SR * dur), endpoint=False)
        wave   = np.sin(2 * np.pi * freq * t) * np.linspace(1, 0, int(SR * dur)) * volume
        stereo = np.column_stack([wave, wave]).astype(np.float32)
        return AudioArrayClip(stereo, fps=SR)

    audio_clips = []
    elapsed     = 0.0
    total       = len(questions)

    for i, q in enumerate(questions):
        prev_p = i / total
        cur_p  = (i + 1) / total

        # Bar animasyonu (0.4 sn)
        anim_steps = 8
        anim_dur   = 0.4 / anim_steps
        for step in range(anim_steps):
            p     = prev_p + (cur_p - prev_p) * (step + 1) / anim_steps
            f_img = make_trivia_frame(q, i + 1, total, False, bg_img, bar_progress=p)
            clips.append(ImageClip(np.array(f_img), duration=anim_dur))
        elapsed += 0.4

        # Soru frame (2.6 sn)
        q_img  = make_trivia_frame(q, i + 1, total, False, bg_img, bar_progress=cur_p)
        q_clip = ImageClip(np.array(q_img), duration=2.6)
        clips.append(q_clip)
        if tick_clip:
            seg = tick_clip.subclip(0, min(2.6, tick_clip.duration))
            audio_clips.append(seg.set_start(elapsed))
        elapsed += 2.6

        # Reveal frame (1.5 sn)
        r_img  = make_trivia_frame(q, i + 1, total, True, bg_img, bar_progress=cur_p)
        r_clip = ImageClip(np.array(r_img), duration=1.5)
        clips.append(r_clip)
        audio_clips.append(make_ding().set_start(elapsed))
        elapsed += 1.5

    # ── Outro frame (3 sn) ──────────────────────────────────
    if bg_img:
        outro_img = bg_img.copy()
    else:
        outro_img = Image.new("RGB", (W, H), (12, 12, 28))
    overlay_col, text_col, accent_col = get_overlay_and_text_colors(bg_img)
    outro_overlay = Image.new("RGBA", (W, H), overlay_col)
    outro_img = outro_img.convert("RGBA")
    outro_img = Image.alpha_composite(outro_img, outro_overlay)
    outro_img = outro_img.convert("RGB")
    odraw = ImageDraw.Draw(outro_img)

    # Büyük emoji-style score icon (daire)
    cx_o, cy_o, r_o = W // 2, 620, 180
    odraw.ellipse([cx_o - r_o, cy_o - r_o, cx_o + r_o, cy_o + r_o],
                  fill=(29, 155, 240))
    # Tik içinde — tek polyline, birleşim noktası boşluk bırakmaz
    ts = int(r_o * 1.2)
    ttx = cx_o - ts // 2
    tty = cy_o - ts // 2
    tp1 = (int(ttx + ts*0.18), int(tty + ts*0.52))
    tp2 = (int(ttx + ts*0.42), int(tty + ts*0.74))
    tp3 = (int(ttx + ts*0.80), int(tty + ts*0.26))
    lw  = max(5, int(ts * 0.09))
    odraw.line([tp1, tp2, tp3], fill="white", width=lw)
    # Köşe noktasına dolu daire — PIL kalın çizgi bıraktığı boşluğu kapat
    r_j = lw // 2
    odraw.ellipse([tp2[0]-r_j, tp2[1]-r_j, tp2[0]+r_j, tp2[1]+r_j], fill="white")

    f_o1 = load_font(72, bold=True)
    f_o2 = load_font(52, bold=False)
    f_o3 = load_font(46, bold=True)

    line1 = "Quiz Complete!"
    bbox1 = odraw.textbbox((0, 0), line1, font=f_o1)
    odraw.text(((W - (bbox1[2] - bbox1[0])) // 2 + 3, 853), line1, font=f_o1, fill=(0, 0, 0))
    odraw.text(((W - (bbox1[2] - bbox1[0])) // 2,     850), line1, font=f_o1, fill=accent_col)

    line2 = "How many did you get right?"
    bbox2 = odraw.textbbox((0, 0), line2, font=f_o2)
    odraw.text(((W - (bbox2[2] - bbox2[0])) // 2 + 2, 962), line2, font=f_o2, fill=(0, 0, 0))
    odraw.text(((W - (bbox2[2] - bbox2[0])) // 2,     960), line2, font=f_o2, fill=(255, 255, 255))

    line3 = "Comment your score below!"
    bbox3 = odraw.textbbox((0, 0), line3, font=f_o2)
    odraw.text(((W - (bbox3[2] - bbox3[0])) // 2,    1048), line3, font=f_o2, fill=(200, 200, 200))

    # Subscribe + like reminder box
    box_y = 1160
    odraw.rounded_rectangle([80, box_y, W - 80, box_y + 260], radius=32,
                             fill=(35, 35, 58), outline=(70, 70, 110), width=3)
    sub_line1 = "Subscribe for a new quiz every day!"
    sub_line2 = "Don't forget to LIKE this video!"
    bbox_s1 = odraw.textbbox((0, 0), sub_line1, font=f_o3)
    bbox_s2 = odraw.textbbox((0, 0), sub_line2, font=f_o3)
    odraw.text(((W - (bbox_s1[2] - bbox_s1[0])) // 2, box_y + 36),
               sub_line1, font=f_o3, fill=(255, 80, 80))
    odraw.text(((W - (bbox_s2[2] - bbox_s2[0])) // 2, box_y + 112),
               sub_line2, font=f_o3, fill=(29, 155, 240))

    # Like + sub icon row
    icon_y = box_y + 175
    icon_cx = W // 2
    # Red subscribe pill
    odraw.rounded_rectangle([icon_cx - 220, icon_y, icon_cx - 20, icon_y + 60],
                             radius=14, fill=(200, 0, 0))
    f_icon = load_font(34, bold=True)
    sub_t = "SUBSCRIBE"
    bbox_si = odraw.textbbox((0, 0), sub_t, font=f_icon)
    odraw.text((icon_cx - 220 + (200 - (bbox_si[2] - bbox_si[0])) // 2, icon_y + 13),
               sub_t, font=f_icon, fill="white")
    # Blue like pill
    odraw.rounded_rectangle([icon_cx + 20, icon_y, icon_cx + 160, icon_y + 60],
                             radius=14, fill=(29, 155, 240))
    like_t = "LIKE"
    bbox_li = odraw.textbbox((0, 0), like_t, font=f_icon)
    odraw.text((icon_cx + 20 + (140 - (bbox_li[2] - bbox_li[0])) // 2, icon_y + 13),
               like_t, font=f_icon, fill="white")

    clips.append(ImageClip(np.array(outro_img), duration=3.0))
    # Ding sesi outro'da
    def make_fanfare(freq=520, dur=0.5, volume=0.35):
        t = np.linspace(0, dur, int(SR * dur), endpoint=False)
        wave = (np.sin(2 * np.pi * freq * t) * 0.6 +
                np.sin(2 * np.pi * freq * 1.25 * t) * 0.3 +
                np.sin(2 * np.pi * freq * 1.5 * t) * 0.1) * np.linspace(1, 0, int(SR * dur)) * volume
        stereo = np.column_stack([wave, wave]).astype(np.float32)
        return AudioArrayClip(stereo, fps=SR)
    audio_clips.append(make_fanfare().set_start(elapsed))

    print("Video birlestiriliyor...")
    final = concatenate_videoclips(clips, method="compose")
    if audio_clips:
        final = final.set_audio(CompositeAudioClip(audio_clips))

    out = os.path.join(script_dir, "trivia_quiz.mp4")
    final.write_videofile(out, fps=24, codec="libx264", logger=None)
    print(f"[OK] Video hazir: {out}")
    return out


def upload_to_youtube_trivia():
    """Trivia quiz videosunu YouTube'a yükle."""
    import base64 as _b64, json as _json
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    token_env = os.environ.get("TOKEN_JSON", "")
    if token_env:
        try:    token_data = _b64.b64decode(token_env).decode()
        except: token_data = token_env
        with open(TOKEN_PATH, "w") as f:
            f.write(token_data)

    SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
    with open(TOKEN_PATH) as f:
        td = _json.load(f)
    creds = Credentials(
        token=td.get("token"), refresh_token=td.get("refresh_token"),
        token_uri=td.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=td.get("client_id"), client_secret=td.get("client_secret"),
        scopes=SCOPES
    )

    hooks = [
        "How smart are you really? 🧠",
        "Can you score 10/10? Most people can't!",
        "Test your knowledge — pause before the answer!",
        "Only 1 in 10 gets all of these right",
        "How many can YOU get? 🤔",
    ]
    hook = random.choice(hooks)
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content":
                f'YouTube Shorts title for a 10-question general knowledge trivia quiz (middle/high school level). '
                f'Hook: "{hook}". Max 60 chars, end with #Shorts, scroll-stopping. ONLY THE TITLE:'}]
        )
        title = resp.choices[0].message.content.strip().replace('"', '').strip() or hook + " #Shorts"
    except Exception as e:
        print(f"[WARN] Groq baslik hatasi: {e}")
        title = hook + " #Shorts"

    out_path = os.path.join(script_dir, "trivia_quiz.mp4")
    desc = (
        "10 trivia questions — science, geography, animals, space & more!\n\n"
        "Can you score 10/10? Pause before the reveal and test yourself! 🧠\n\n"
        "Comment your score below! 👇\n"
        "🔔 Subscribe for a new quiz every day!\n\n"
        "#Shorts #trivia #quiz #generalknowledge #science #geography "
        "#educational #quiztime #knowledge #viral"
    )
    tags = ["trivia", "general knowledge", "quiz", "shorts", "science quiz",
            "geography quiz", "educational", "knowledge test", "school quiz",
            "10 questions", "trivia challenge", "smart quiz"]

    print(f"Baslik: {title}")
    yt   = build('youtube', 'v3', credentials=creds)
    body = {
        'snippet': {'title': title[:100], 'description': desc,
                    'tags': tags, 'categoryId': '27'},
        'status':  {'privacyStatus': 'public', 'selfDeclaredMadeForKids': False, 'containsSyntheticMedia': False}
    }
    try:
        media = MediaFileUpload(out_path, mimetype='video/mp4', resumable=True)
        req   = yt.videos().insert(part='snippet,status', body=body, media_body=media)
        response = None
        while response is None:
            status, response = req.next_chunk()
            if status:
                print(f"  %{int(status.progress() * 100)}")
        video_id = response['id']
        print(f"\n[OK] Yayinlandi! https://youtube.com/shorts/{video_id}")
        return video_id
    except Exception as e:
        print(f"[ERROR] YouTube yukleme hatasi: {e}")
        return None


# ─────────────────────────────────────────────────────────────
# 4 ŞIKLI MULTIPLE CHOICE QUIZ
# ─────────────────────────────────────────────────────────────

def get_distractors(correct_code, n=3):
    """Doğru cevap dışında n adet yanlış şık seç (farklı zorluklardan karışık)."""
    pool = [(code, data[0]) for code, data in COUNTRIES.items() if code != correct_code]
    random.shuffle(pool)
    return pool[:n]


def make_multichoice_frame(flag_img, question_num, total, choices, revealed,
                           correct_idx, bg_img=None, bar_progress=None):
    """
    choices    : [(code, name), (code, name), (code, name), (code, name)]
    revealed   : True ise doğru=yeşil, yanlış=kırmızı
    correct_idx: doğru şıkkın indeksi (0-3)
    """
    if bg_img:
        img = bg_img.copy()
    else:
        img = Image.new("RGB", (W, H), (12, 12, 28))

    overlay_col, text_col, accent_col = get_overlay_and_text_colors(bg_img)
    overlay = Image.new("RGBA", (W, H), overlay_col)
    img = img.convert("RGBA")
    img = Image.alpha_composite(img, overlay)
    img = img.convert("RGB")
    draw = ImageDraw.Draw(img)

    # ── Başlık ──────────────────────────────────────────────
    f_title = load_font(72, bold=True)
    bbox = draw.textbbox((0, 0), "FLAG QUIZ", font=f_title)
    tx = (W - (bbox[2] - bbox[0])) // 2
    draw.text((tx + 3, 53), "FLAG QUIZ", font=f_title, fill=(0, 0, 0))
    draw.text((tx, 50),     "FLAG QUIZ", font=f_title, fill=accent_col)

    # ── İlerleme çubuğu ─────────────────────────────────────
    bar_x, bar_y, bar_w, bar_h = 60, 145, W - 120, 18
    draw.rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + bar_h], fill=(40, 40, 60))
    progress = bar_progress if bar_progress is not None else question_num / total
    filled = int(bar_w * progress)
    if filled > 0:
        draw.rectangle([bar_x, bar_y, bar_x + filled, bar_y + bar_h], fill=accent_col)

    # ── Bayrak ──────────────────────────────────────────────
    flag_area_y = 200
    if flag_img:
        fw, fh = flag_img.size
        max_w, max_h = 820, 460
        scale = min(max_w / fw, max_h / fh)
        nw, nh = int(fw * scale), int(fh * scale)
        flag_r = flag_img.resize((nw, nh), Image.Resampling.LANCZOS)
        border = 8
        draw.rectangle(
            [(W // 2 - nw // 2 - border, flag_area_y - border),
             (W // 2 + nw // 2 + border, flag_area_y + nh + border)],
            outline=accent_col, width=border
        )
        img.paste(flag_r, (W // 2 - nw // 2, flag_area_y),
                  flag_r if flag_r.mode == "RGBA" else None)

    # ── Soru metni ──────────────────────────────────────────
    q_y = 710
    f_q = load_font(54, bold=True)
    q_text = f"Which country? ({question_num}/{total})"
    bbox = draw.textbbox((0, 0), q_text, font=f_q)
    qx = (W - (bbox[2] - bbox[0])) // 2
    draw.text((qx + 2, q_y + 2), q_text, font=f_q, fill=(0, 0, 0))
    draw.text((qx, q_y),         q_text, font=f_q, fill=text_col)

    # ── 4 Şık (2×2 grid) ────────────────────────────────────
    labels   = ["A", "B", "C", "D"]
    btn_w    = 472
    btn_h    = 140
    gap_x    = 24
    gap_y    = 22
    start_x  = (W - btn_w * 2 - gap_x) // 2
    start_y  = 810
    f_lbl    = load_font(54, bold=True)
    f_opt    = load_font(40, bold=False)
    f_opt_sm = load_font(32, bold=False)

    for i, (code, name) in enumerate(choices):
        col = i % 2
        row = i // 2
        bx  = start_x + col * (btn_w + gap_x)
        by  = start_y + row * (btn_h + gap_y)

        if not revealed:
            bg_col  = (35, 35, 58)
            lbl_col = accent_col
            txt_col = (220, 220, 220)
            border_col = (70, 70, 100)
        elif i == correct_idx:
            bg_col  = (25, 150, 65)
            lbl_col = (255, 255, 255)
            txt_col = (255, 255, 255)
            border_col = (50, 220, 100)
        else:
            bg_col  = (70, 25, 25)
            lbl_col = (180, 80, 80)
            txt_col = (130, 130, 130)
            border_col = (100, 40, 40)

        draw.rounded_rectangle([bx, by, bx + btn_w, by + btn_h],
                                radius=22, fill=bg_col, outline=border_col, width=3)

        # Etiket (A/B/C/D)
        draw.text((bx + 20, by + (btn_h - 60) // 2), labels[i],
                  font=f_lbl, fill=lbl_col)

        # Ayraç çizgisi
        div_x = bx + 82
        draw.line([(div_x, by + 18), (div_x, by + btn_h - 18)],
                  fill=border_col, width=2)

        # Ülke adı (sığmıyorsa küçük font)
        name_x = div_x + 16
        max_name_w = bx + btn_w - name_x - 12
        bbox_n = draw.textbbox((0, 0), name, font=f_opt)
        if bbox_n[2] - bbox_n[0] > max_name_w:
            f_use = f_opt_sm
            name_y = by + (btn_h - 36) // 2
        else:
            f_use = f_opt
            name_y = by + (btn_h - 46) // 2
        draw.text((name_x, name_y), name, font=f_use, fill=txt_col)

        # Doğru cevapta mavi tik rozeti
        if revealed and i == correct_idx:
            ts = 46
            tx = bx + btn_w - ts - 16
            ty = by + (btn_h - ts) // 2
            draw.ellipse([tx, ty, tx + ts, ty + ts], fill=(29, 155, 240))
            draw.line([(tx + ts*0.22, ty + ts*0.52), (tx + ts*0.44, ty + ts*0.72)],
                      fill="white", width=max(2, int(ts*0.13)))
            draw.line([(tx + ts*0.44, ty + ts*0.72), (tx + ts*0.78, ty + ts*0.28)],
                      fill="white", width=max(2, int(ts*0.13)))

    return img


def create_multichoice_video(questions):
    """4 şıklı multiple choice flag quiz videosu oluştur."""
    print("Bayraklar yukleniyor (multichoice)...")
    flags = {}
    for code, name, diff in questions:
        print(f"  {name} ({code})...", end=" ")
        flags[code] = download_flag(code)
        print("OK" if flags[code] else "HATA")

    # Her soru için şıkları hazırla
    choices_list = []
    for code, name, diff in questions:
        distractors = get_distractors(code, n=3)
        all_choices = [(code, name)] + distractors
        random.shuffle(all_choices)
        correct_idx = next(i for i, (c, _) in enumerate(all_choices) if c == code)
        choices_list.append((all_choices, correct_idx))

    bg_img = load_background()
    print("\nFrameler olusturuluyor...")
    clips = []

    import numpy as np
    from moviepy.audio.AudioClip import AudioArrayClip, CompositeAudioClip
    from moviepy.editor import AudioFileClip as AFC

    SR = 44100
    tick_mp3  = os.path.join(script_dir, "tick.mp3")
    tick_clip = AFC(tick_mp3).volumex(0.7) if os.path.exists(tick_mp3) else None

    def make_ding(freq=1100, dur=0.25, volume=0.85):
        t     = np.linspace(0, dur, int(SR * dur), endpoint=False)
        wave  = np.sin(2 * np.pi * freq * t) * np.linspace(1, 0, int(SR * dur)) * volume
        stereo = np.column_stack([wave, wave]).astype(np.float32)
        return AudioArrayClip(stereo, fps=SR)

    audio_clips = []
    elapsed = 0.0

    for i, (code, name, diff) in enumerate(questions):
        choices, correct_idx = choices_list[i]
        flag_img = flags[code]

        # Bar animasyonu: önceki konumdan bu soruya kadar 0.4 sn'de doldur
        prev_progress = i / len(questions)
        cur_progress  = (i + 1) / len(questions)
        anim_steps    = 8
        anim_dur      = 0.4 / anim_steps
        for step in range(anim_steps):
            p = prev_progress + (cur_progress - prev_progress) * (step + 1) / anim_steps
            f_img = make_multichoice_frame(flag_img, i + 1, len(questions),
                                           choices, False, correct_idx, bg_img,
                                           bar_progress=p)
            clips.append(ImageClip(np.array(f_img), duration=anim_dur))
        elapsed += 0.4

        # Soru frame (2.6 sn — toplam soru süresi = 3 sn)
        q_img  = make_multichoice_frame(flag_img, i + 1, len(questions),
                                        choices, False, correct_idx, bg_img,
                                        bar_progress=cur_progress)
        q_clip = ImageClip(np.array(q_img), duration=2.6)
        clips.append(q_clip)
        if tick_clip:
            seg = tick_clip.subclip(0, min(2.6, tick_clip.duration))
            audio_clips.append(seg.set_start(elapsed))
        elapsed += 2.6

        # Reveal frame (1.5 sn)
        r_img  = make_multichoice_frame(flag_img, i + 1, len(questions),
                                        choices, True, correct_idx, bg_img,
                                        bar_progress=cur_progress)
        r_clip = ImageClip(np.array(r_img), duration=1.5)
        clips.append(r_clip)
        audio_clips.append(make_ding().set_start(elapsed))
        elapsed += 1.5

    print("Video birlestiriliyor...")
    final = concatenate_videoclips(clips, method="compose")
    if audio_clips:
        final = final.set_audio(CompositeAudioClip(audio_clips))

    final.write_videofile(OUTPUT_VIDEO_MULTICHOICE, fps=24, codec="libx264", logger=None)
    print(f"[OK] Video hazir: {OUTPUT_VIDEO_MULTICHOICE}")


def upload_to_youtube_multichoice(questions):
    """4 şıklı quiz videosunu YouTube'a yükle."""
    import base64 as _b64
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    token_env = os.environ.get("TOKEN_JSON", "")
    if token_env:
        try:
            token_data = _b64.b64decode(token_env).decode()
        except Exception:
            token_data = token_env
        with open(TOKEN_PATH, "w") as f:
            f.write(token_data)

    SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
    import json as _json
    with open(TOKEN_PATH) as f:
        td = _json.load(f)
    creds = Credentials(
        token=td.get("token"), refresh_token=td.get("refresh_token"),
        token_uri=td.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=td.get("client_id"), client_secret=td.get("client_secret"),
        scopes=SCOPES
    )

    hooks = [
        "Can you guess all 4? Most people miss #7",
        "Only geniuses get 10/10 — can you?",
        "How many flags can YOU identify?",
        "This quiz stumps 90% of people",
        "Pause before the reveal — be honest!",
    ]
    hook = random.choice(hooks)
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content":
                f'Create a YouTube Shorts title for a 4-choice flag quiz with 10 questions. '
                f'Use this hook: "{hook}". '
                f'Rules: max 60 chars, end with #Shorts, scroll-stopping. ONLY THE TITLE:'}]
        )
        title = resp.choices[0].message.content.strip().replace('"', '').strip()
        if not title:
            raise ValueError("bos")
    except Exception as e:
        print(f"[WARN] Groq hatasi ({e}). Yedek baslik.")
        title = f"{hook} #Shorts"

    desc = (
        "Can you pick the right country from 4 choices? Easy → Expert!\n\n"
        "10 flags | 4 choices each | Can you go 10/10?\n\n"
        "Comment your score below! 👇\n"
        "🔔 Subscribe for a new quiz every day!\n\n"
        "#Shorts #flagquiz #geography #quiz #multiplechoice "
        "#worldflags #geographyquiz #trivia #quiztime #viral"
    )
    tags = [
        "flag quiz", "multiple choice", "geography quiz", "world flags",
        "quiz", "shorts", "country quiz", "flag challenge", "4 choices",
        "trivia", "geography", "educational", "viral quiz"
    ]

    print(f"Baslik: {title}")
    yt   = build('youtube', 'v3', credentials=creds)
    body = {
        'snippet': {
            'title': title[:100], 'description': desc,
            'tags': tags, 'categoryId': '27'
        },
        'status': {'privacyStatus': 'public', 'selfDeclaredMadeForKids': False, 'containsSyntheticMedia': False}
    }
    try:
        media = MediaFileUpload(OUTPUT_VIDEO_MULTICHOICE, mimetype='video/mp4', resumable=True)
        req   = yt.videos().insert(part='snippet,status', body=body, media_body=media)
        response = None
        while response is None:
            status, response = req.next_chunk()
            if status:
                print(f"  %{int(status.progress() * 100)}")
        video_id = response['id']
        print(f"\n[OK] Yayinlandi! https://youtube.com/shorts/{video_id}")
        return video_id
    except Exception as e:
        print(f"[ERROR] YouTube yukleme hatasi: {e}")
        return None


# ─────────────────────────────────────────────────────────────
# ÇALIŞMA LOGU
# ─────────────────────────────────────────────────────────────
def save_run_log(status, video_id=None, title=None, error=None, mode=None):
    import json as _json
    from datetime import datetime
    log_path = os.path.join(script_dir, "run_log.json")
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            data = _json.load(f)
    except:
        data = {"bot": "flaq_quiz", "runs": []}
    entry = {"ts": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"), "status": status}
    if video_id: entry["video_id"] = video_id
    if title:    entry["title"]    = title[:80]
    if error:    entry["error"]    = str(error)[:200]
    if mode:     entry["mode"]     = mode
    data["runs"].append(entry)
    data["runs"] = data["runs"][-20:]
    with open(log_path, 'w', encoding='utf-8') as f:
        _json.dump(data, f, ensure_ascii=False, indent=2)


# ─────────────────────────────────────────────────────────────
# ANA AKIŞ
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import json
    TEST_MODE = "--test" in sys.argv

    # Mod dosyasını oku — brainrot → flag → multichoice → trivia → brainrot → ...
    MODES = ["brainrot", "flag", "multichoice", "trivia"]
    if os.path.exists(MODE_FILE):
        with open(MODE_FILE, 'r') as f:
            last_mode = json.load(f).get("last_mode", "trivia")
    else:
        last_mode = "trivia"

    last_idx = MODES.index(last_mode) if last_mode in MODES else 3
    quiz_mode = MODES[(last_idx + 1) % len(MODES)]

    # Yeni modu kaydet
    with open(MODE_FILE, 'w') as f:
        json.dump({"last_mode": quiz_mode}, f)

    print(f"=== {quiz_mode.upper()} QUIZ BOT ===\n")
    print(f"Mod: {quiz_mode.upper()}")

    if quiz_mode == "flag":
        questions = pick_questions()
    elif quiz_mode == "capital":
        questions = pick_capital_questions()
    elif quiz_mode == "multichoice":
        questions = pick_questions()   # flag sorularını kullan, şıklar kod içinde üretiliyor
    elif quiz_mode == "trivia":
        questions = generate_trivia_questions()
    else:
        questions = pick_brainrot_questions()

    if quiz_mode == "trivia":
        print("Uretilen sorular:")
        for i, q in enumerate(questions):
            print(f"  {i+1}. [{q.get('category','')}] {q['question']}")
    else:
        print("Secilen sorular:")
        for i, (key, name, diff) in enumerate(questions):
            print(f"  {i+1}. {name} ({diff})")
    print()

    if quiz_mode == "multichoice":
        create_multichoice_video(questions)
    elif quiz_mode == "trivia":
        create_trivia_video(questions)
    else:
        create_video(questions, quiz_mode=quiz_mode)

    bot_labels = {"flag": "Flag Quiz", "brainrot": "Brainrot Quiz",
                  "capital": "Capital Quiz", "multichoice": "4-Choice Flag Quiz",
                  "trivia": "Trivia Quiz"}
    bot_label = bot_labels.get(quiz_mode, quiz_mode)
    out_paths  = {"flag": OUTPUT_VIDEO, "brainrot": OUTPUT_VIDEO_BRAINROT,
                  "capital": OUTPUT_VIDEO_CAPITAL, "multichoice": OUTPUT_VIDEO_MULTICHOICE,
                  "trivia": OUTPUT_VIDEO_TRIVIA}

    if TEST_MODE:
        print("\n[TEST] YouTube yuklemesi atlandi.")
        print(f"[TEST] Video: {out_paths.get(quiz_mode, OUTPUT_VIDEO)}")
        sys.exit(0)

    if quiz_mode == "flag":
        video_id = upload_to_youtube(questions)
    elif quiz_mode == "capital":
        video_id = upload_to_youtube_capital(questions)
    elif quiz_mode == "multichoice":
        video_id = upload_to_youtube_multichoice(questions)
    elif quiz_mode == "trivia":
        video_id = upload_to_youtube_trivia()
    else:
        video_id = upload_to_youtube_brainrot(questions)

    if video_id:
        save_run_log("ok", video_id=video_id, mode=quiz_mode)
        send_telegram(
            f"✅ <b>flaq_quiz ({bot_label})</b> video yayınlandı!\n"
            f"🔗 https://youtube.com/shorts/{video_id}"
        )
    else:
        save_run_log("error", error="YouTube upload failed", mode=quiz_mode)
        send_telegram(f"❌ <b>flaq_quiz ({bot_label})</b> YouTube yüklemesi başarısız!")

    out_path = out_paths.get(quiz_mode, OUTPUT_VIDEO)
    print("\n=== Tamamlandi! ===")
    print(f"Video: {out_path}")
