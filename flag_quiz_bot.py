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

OUTPUT_VIDEO = os.path.join(script_dir, "flag_quiz.mp4")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
SECRET_PATH  = os.path.join(script_dir, "secret.json")
TOKEN_PATH   = os.path.join(script_dir, "token.json")
W, H = 1080, 1920

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
BRAINROT_IMAGES_DIR = os.path.join(script_dir, "brainrot_images")

QUIZ_MODE = random.choice(["flag", "brainrot"])
print(f"[MODE] {QUIZ_MODE.upper()} QUIZ secildi")

BRAINROT_CHARACTERS = {
    "easy": [
        {"name": "Tralalero Tralala",    "image": "tralalero_tralala"},
        {"name": "Bombardiro Crocodilo", "image": "bombardiro_crocodilo"},
        {"name": "Tung Tung Tung Sahur", "image": "tung_tung_sahur"},
        {"name": "Cappuccino Assassino", "image": "cappuccino_assassino"},
        {"name": "La Vaca Saturno",      "image": "la_vaca_saturno"},
    ],
    "medium": [
        {"name": "Bombombini Gusini",    "image": "bombombini_gusini"},
        {"name": "Frigo Camelo",         "image": "frigo_camelo"},
        {"name": "Brr Brr Patapim",      "image": "brr_brr_patapim"},
        {"name": "Lirili Larila",        "image": "lirili_larila"},
        {"name": "Chimpanzini Bananini", "image": "chimpanzini_bananini"},
    ],
    "hard": [
        {"name": "Boneca Ambalabu",      "image": "boneca_ambalabu"},
        {"name": "Burbaloni Luliloli",   "image": "burbaloni_luliloli"},
        {"name": "Bobritto Bandito",     "image": "bobritto_bandito"},
        {"name": "Glorbo Fruttodrillo",  "image": "glorbo_fruttodrillo"},
        {"name": "Job Job Sahur",        "image": "job_job_sahur"},
    ],
    "expert": [
        {"name": "Karkerkar Kurkur",     "image": "Karkerkar_kurkur"},
        {"name": "La Esok Sekolah",      "image": "la_Esok_Sekolah"},
        {"name": "Rhino Toasterino",     "image": "Rhino_Toasterino"},
        {"name": "Swag Soda",            "image": "swag_soda"},
        {"name": "Svinina Bombardino",   "image": "Svinina_Bombardino"},
    ],
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

def load_brainrot_image(basename):
    for ext in [".jpg", ".jpeg", ".png", ".webp", ".JPG", ".PNG", ".JPEG"]:
        path = os.path.join(BRAINROT_IMAGES_DIR, basename + ext)
        if os.path.exists(path):
            try:
                return Image.open(path).convert("RGBA")
            except Exception as e:
                print(f"  [WARN] Gorsel yuklenemedi: {e}")
    if "." in basename:
        path = os.path.join(BRAINROT_IMAGES_DIR, basename)
        if os.path.exists(path):
            try: return Image.open(path).convert("RGBA")
            except: pass
    print(f"  [WARN] Dosya bulunamadi: {basename}")
    return None


def generate_tts(text, filename="tts_temp.mp3"):
    try:
        from gtts import gTTS
        tts = gTTS(text=text, lang="en", slow=False)
        tts.save(filename)
        return filename
    except Exception as e:
        print(f"  [WARN] TTS hatasi: {e}")
        return None

def pick_questions():
    if QUIZ_MODE == "brainrot":
        selected = []
        for diff, count in [("easy", 3), ("medium", 3), ("hard", 3), ("expert", 1)]:
            pool = BRAINROT_CHARACTERS[diff]
            chosen = random.sample(pool, min(count, len(pool)))
            for char in chosen:
                selected.append((char["image"], char["name"], diff))
        return selected
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


def make_frame(questions, current_idx, revealed_up_to, flag_img,
               bar_progress=None, countdown=None, bg_img=None):
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
    title = "BRAINROT QUIZ" if QUIZ_MODE == "brainrot" else "FLAG QUIZ"
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

    for i, (identifier, name, diff) in enumerate(questions):
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
    note_text = "Who is this?" if QUIZ_MODE == "brainrot" else "Which country?"
    note = f"{note_text} ({current_idx+1}/10)"
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
def create_video(questions):
    print("Gorseller yukleniyor...")
    subjects = {}
    for identifier, name, diff in questions:
        print(f"  {name}...", end=" ")
        if QUIZ_MODE == "brainrot":
            subjects[identifier] = load_brainrot_image(identifier)
        else:
            subjects[identifier] = download_flag(identifier)
        print("OK" if subjects[identifier] else "HATA")

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

    n = len(questions)
    ding_times   = []  # cevap açılma zamanları
    tick_starts  = []  # countdown başlangıçları
    whoosh_times = []  # bayrak geçiş zamanları
    global_t = 0.0

    for i, (identifier, name, diff) in enumerate(questions):
        bar_start = i / n
        bar_end   = (i + 1) / n
        # 6 x 0.5sn = 3sn: sayaç 3→2→1
        countdown_map = {0:3, 1:3, 2:2, 3:2, 4:1, 5:1}
        steps = 6
        for s in range(steps):
            progress = bar_start + (bar_end - bar_start) * (s / steps)
            cd = countdown_map[s]
            img_q = make_frame(questions, i, i-1, subjects[identifier],
                               bar_progress=progress, countdown=cd, bg_img=bg_img)
            path_q = f"_frame_q_{i}_{s}.jpg"
            img_q.save(path_q, quality=92)
            clips.append(ImageClip(path_q, duration=0.5))
            if s == 0:
                tick_starts.append(global_t)
                if i > 0:
                    whoosh_times.append(max(0, global_t - 0.35))
            global_t += 0.5

        # Cevap reveal (1 sn) — ding sesi
        img_a = make_frame(questions, i, i, subjects[identifier],
                           bar_progress=bar_end, countdown=None, bg_img=bg_img)
        path_a = f"_frame_a_{i}.jpg"
        img_a.save(path_a, quality=92)
        clips.append(ImageClip(path_a, duration=1))
        ding_times.append(global_t)
        global_t += 1.0

    # Son frame: tüm cevaplar açık, 2 sn
    img_end = make_frame(questions, 9, 9, subjects[questions[-1][0]], bg_img=bg_img)
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

    final.write_videofile(OUTPUT_VIDEO, fps=24, codec="libx264", logger=None)
    print(f"\n[OK] Video hazir: {OUTPUT_VIDEO}")

    # Temizlik
    for i in range(10):
        for s in range(6):
            try: os.remove(f"_frame_q_{i}_{s}.jpg")
            except: pass
        try: os.remove(f"_frame_a_{i}.jpg")
        except: pass
    try: os.remove("_frame_end.jpg")
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

    # Groq ile viral başlık üret
    hooks = [
        "Only 1% can name all 10 flags!",
        "How many flags can you identify?",
        "Can you name all 10 country flags?",
        "Test your geography knowledge!",
        "World flags challenge — how good are you?",
        "Flag quiz: Easy to Expert!",
    ]
    hook = random.choice(hooks)

    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content":
                f'Create a viral YouTube Shorts title for a flag quiz video with 10 flags '
                f'(Easy to Expert difficulty). Hook style: "{hook}". Max 60 chars. '
                f'End with #shorts. ONLY THE TITLE, no quotes:'}]
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
        print(f"\n[OK] Yayinlandi! https://youtube.com/shorts/{response['id']}")
    except Exception as e:
        print(f"[ERROR] YouTube yukleme hatasi: {e}")


# ─────────────────────────────────────────────────────────────
# ANA AKIŞ
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=== FLAG QUIZ BOT ===\n")
    questions = pick_questions()
    print("Secilen sorular:")
    for i, (identifier, name, diff) in enumerate(questions):
        print(f"  {i+1}. {name} ({diff})")
    print()
    create_video(questions)
    upload_to_youtube(questions)
    print("\n=== Tamamlandi! ===")
    print(f"Video: {OUTPUT_VIDEO}")
