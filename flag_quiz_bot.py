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
OUTPUT_VIDEO_BRAINROT = os.path.join(script_dir, "brainrot_quiz.mp4")
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
    """Sadece bayrak/karakter gösteren intro — cevap listesi yok, thumbnail için."""
    if bg_img:
        img = bg_img.copy()
    else:
        img = Image.new("RGB", (W, H), (12, 12, 28))

    overlay_col, text_col, accent_col = get_overlay_and_text_colors(bg_img)
    # Intro'da overlay daha hafif olsun — bayrak daha net görünsün
    r, g, b, a = overlay_col
    overlay = Image.new("RGBA", (W, H), (r, g, b, max(0, a - 40)))
    img = img.convert("RGBA")
    img = Image.alpha_composite(img, overlay)
    img = img.convert("RGB")
    draw = ImageDraw.Draw(img)

    # Büyük üst başlık
    f_title = load_font(96, bold=True)
    title = "BRAINROT QUIZ" if quiz_mode == "brainrot" else "FLAG QUIZ"
    bbox = draw.textbbox((0, 0), title, font=f_title)
    tx = (W - (bbox[2] - bbox[0])) // 2
    draw.text((tx + 4, 72), title, font=f_title, fill=(0, 0, 0))
    draw.text((tx, 68), title, font=f_title, fill=accent_col)

    # Soru sayısı chip
    f_chip = load_font(52, bold=True)
    chip = "10 CHARS" if quiz_mode == "brainrot" else "10 FLAGS"
    bbox_c = draw.textbbox((0, 0), chip, font=f_chip)
    cw = bbox_c[2] - bbox_c[0]
    cx = (W - cw) // 2
    draw.rounded_rectangle([cx - 24, 185, cx + cw + 24, 255], radius=22, fill=accent_col)
    draw.text((cx, 190), chip, font=f_chip, fill=(0, 0, 0))

    # Çok büyük bayrak (ekranın büyük kısmı)
    if flag_img:
        fw, fh = flag_img.size
        max_w, max_h = 980, 660
        scale = min(max_w / fw, max_h / fh)
        nw, nh = int(fw * scale), int(fh * scale)
        flag_r = flag_img.resize((nw, nh), Image.Resampling.LANCZOS)
        flag_y = 300
        border = 10
        # Gölge efekti
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

    # Alt soru metni
    f_sub = load_font(62, bold=True)
    sub = "Name this character!" if quiz_mode == "brainrot" else "Which country is this?"
    bbox2 = draw.textbbox((0, 0), sub, font=f_sub)
    sx = (W - (bbox2[2] - bbox2[0])) // 2
    draw.text((sx + 3, H - 260), sub, font=f_sub, fill=(0, 0, 0))
    draw.text((sx, H - 263), sub, font=f_sub, fill=(255, 255, 255))

    # En alt tag
    f_tag = load_font(44, bold=False)
    tag = "#brainrot  #shorts  #quiz" if quiz_mode == "brainrot" else "#flagquiz  #shorts  #geography"
    bbox3 = draw.textbbox((0, 0), tag, font=f_tag)
    draw.text(((W - (bbox3[2] - bbox3[0])) // 2, H - 170), tag,
              font=f_tag, fill=(180, 180, 180))

    return img


def make_frame(questions, current_idx, revealed_up_to, flag_img,
               bar_progress=None, countdown=None, bg_img=None, quiz_mode="flag"):
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
    title = "BRAINROT QUIZ" if quiz_mode == "brainrot" else "FLAG QUIZ"
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
    note = (f"Name this character! ({current_idx+1}/10)"
            if quiz_mode == "brainrot"
            else f"Which country? ({current_idx+1}/10)")
    bbox = draw.textbbox((0,0), note, font=f_note)
    nx = (W - (bbox[2]-bbox[0])) // 2
    draw.text((nx+2, H-128), note, font=f_note, fill=(0,0,0))
    draw.text((nx, H-130), note, font=f_note, fill=text_col)

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
    label = "Karakterler" if quiz_mode == "brainrot" else "Bayraklar"
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
        # 6 x 0.5sn = 3sn: sayaç 3→2→1
        countdown_map = {0:3, 1:3, 2:2, 3:2, 4:1, 5:1}
        steps = 6
        for s in range(steps):
            progress = bar_start + (bar_end - bar_start) * (s / steps)
            cd = countdown_map[s]
            img_q = make_frame(questions, i, i-1, flags[code],
                               bar_progress=progress, countdown=cd, bg_img=bg_img,
                               quiz_mode=quiz_mode)
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
                           quiz_mode=quiz_mode)
        path_a = f"_frame_a_{i}.jpg"
        img_a.save(path_a, quality=92)
        clips.append(ImageClip(path_a, duration=1))
        ding_times.append(global_t)
        global_t += 1.0

    # Son frame: tüm cevaplar açık, 2 sn
    img_end = make_frame(questions, 9, 9, flags[questions[-1][0]], bg_img=bg_img,
                         quiz_mode=quiz_mode)
    img_end_draw = ImageDraw.Draw(img_end)
    f_end = load_font(64, bold=True)
    bbox = img_end_draw.textbbox((0,0), "How many did you get?", font=f_end)
    ex = (W - (bbox[2]-bbox[0])) // 2
    img_end_draw.text((ex, H-200), "How many did you get?",
                      font=f_end, fill=(255,220,50))
    path_end = "_frame_end.jpg"
    img_end.save(path_end, quality=92)
    clips.append(ImageClip(path_end, duration=2))

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

    # Arka plan müziği ekle
    music_path = os.path.join(script_dir, "music.mp3")
    if os.path.exists(music_path):
        try:
            from moviepy.editor import AudioFileClip
            bg = AudioFileClip(music_path)
            start = random.randint(10, 30) if bg.duration > 40 else 0
            bg = bg.subclip(start, min(start + total_dur, bg.duration))
            bg = bg.volumex(0.15)
            audio_clips.append(bg)
            print("Muzik eklendi.")
        except Exception as e:
            print(f"Muzik eklenemedi: {e}")

    if audio_clips:
        final = final.set_audio(CompositeAudioClip(audio_clips))

    out_path = OUTPUT_VIDEO_BRAINROT if quiz_mode == "brainrot" else OUTPUT_VIDEO
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
        "How many did you get right? Comment below!\n\n"
        "#shorts #flagquiz #geography #flags #quiz #worldflags #countryflags "
        "#geographyquiz #trivia #challenge"
    )
    tags = [
        "flag quiz", "flags", "geography", "world flags", "country flags",
        "quiz", "shorts", "geography quiz", "flag challenge", "educational",
        "trivia", "flag game", "country quiz"
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
            'privacyStatus': 'public',
            'selfDeclaredMadeForKids': False
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
        "How many did you get right? Comment below!\n\n"
        "#shorts #brainrot #quiz #brainrotquiz #viral "
        "#tralalero #bombardiro #tungsung #brainrotcharacters"
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
            'privacyStatus': 'public',
            'selfDeclaredMadeForKids': False
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
# ANA AKIŞ
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import json

    # Mod dosyasını oku — flag ve brainrot arasında sırayla geç
    if os.path.exists(MODE_FILE):
        with open(MODE_FILE, 'r') as f:
            last_mode = json.load(f).get("last_mode", "brainrot")
    else:
        last_mode = "brainrot"

    quiz_mode = "flag" if last_mode == "brainrot" else "brainrot"

    # Yeni modu kaydet
    with open(MODE_FILE, 'w') as f:
        json.dump({"last_mode": quiz_mode}, f)

    print(f"=== {'FLAG' if quiz_mode == 'flag' else 'BRAINROT'} QUIZ BOT ===\n")
    print(f"Mod: {quiz_mode.upper()}")

    if quiz_mode == "flag":
        questions = pick_questions()
    else:
        questions = pick_brainrot_questions()

    print("Secilen sorular:")
    for i, (key, name, diff) in enumerate(questions):
        print(f"  {i+1}. {name} ({diff})")
    print()

    create_video(questions, quiz_mode=quiz_mode)

    bot_label = "Flag Quiz" if quiz_mode == "flag" else "Brainrot Quiz"
    if quiz_mode == "flag":
        video_id = upload_to_youtube(questions)
    else:
        video_id = upload_to_youtube_brainrot(questions)

    if video_id:
        send_telegram(
            f"✅ <b>flaq_quiz ({bot_label})</b> video yayınlandı!\n"
            f"🔗 https://youtube.com/shorts/{video_id}"
        )
    else:
        send_telegram(f"❌ <b>flaq_quiz ({bot_label})</b> YouTube yüklemesi başarısız!")

    out_path = OUTPUT_VIDEO if quiz_mode == "flag" else OUTPUT_VIDEO_BRAINROT
    print("\n=== Tamamlandi! ===")
    print(f"Video: {out_path}")
