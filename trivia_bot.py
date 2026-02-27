import os
import sys
import random
import textwrap
import requests
import io
import base64

# GitHub Actions / Linux ortamında stdout encoding
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    except AttributeError:
        pass

# GitHub Actions: token ve secret dosyalarını env'den yaz
def _write_from_env(env_var, filepath):
    val = os.environ.get(env_var)
    if val and not os.path.exists(filepath):
        with open(filepath, 'wb') as f:
            f.write(base64.b64decode(val))
        print(f"[OK] {env_var} yazildi.")

_script_dir = os.path.dirname(os.path.abspath(__file__))
_write_from_env("TOKEN_JSON", os.path.join(_script_dir, "token.json"))
_write_from_env("SECRET_JSON", os.path.join(_script_dir, "secret.json"))

from PIL import Image, ImageDraw, ImageFont
from groq import Groq
from moviepy import ImageClip, concatenate_videoclips, AudioFileClip
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

# ============================================================
# AYARLAR
# ============================================================
os.chdir(_script_dir)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
SECRET_PATH  = os.path.join(_script_dir, "secret.json")
TOKEN_PATH   = os.path.join(_script_dir, "token.json")
OUTPUT_VIDEO = os.path.join(_script_dir, "trivia_shorts.mp4")

W, H = 1080, 1920  # YouTube Shorts boyutu

# Renkler
COL_BG       = (10, 10, 20)
COL_TITLE    = (255, 215, 0)    # Altın sarısı
COL_QUESTION = (255, 255, 255)  # Beyaz
COL_ANSWER   = (80, 220, 120)   # Yeşil
COL_FACT     = (180, 180, 180)  # Gri
COL_COUNTDOWN= (255, 80, 80)    # Kırmızı
COL_OVERLAY  = (0, 0, 0, 160)


# ============================================================
# ADIM 1: GROQ İLE TRİVİA ÜRET
# ============================================================
def generate_trivia():
    print("Groq'tan trivia sorusu uretiliyor...")
    try:
        client = Groq(api_key=GROQ_API_KEY)
        prompt = """
        You are the editor of the most viral "Did You Know?" YouTube Shorts channel.

        Generate ONE surprising, mind-blowing trivia fact that will make people stop scrolling.

        Rules:
        - The question must be genuinely surprising or counterintuitive
        - Keep QUESTION to 10-16 words ending with "?"
        - ANSWER must be 3-6 words, punchy and direct
        - FACT adds 1 sentence of amazing context (max 18 words)
        - CATEGORY must be one of: science, history, nature, space, animals, food, technology, psychology

        DO NOT use these overused facts: bananas are radioactive, honey never expires,
        octopuses have 3 hearts, humans share DNA with bananas, cleopatra lived closer to
        moon landing than pyramids.

        Format EXACTLY (no extra text):
        QUESTION: [question here]
        ANSWER: [answer here]
        FACT: [one sentence context]
        CATEGORY: [category]
        """
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )
        text = resp.choices[0].message.content.strip()
        data = {"question": None, "answer": None, "fact": None, "category": "science"}
        for line in text.split("\n"):
            if line.startswith("QUESTION:"):
                data["question"] = line.replace("QUESTION:", "").strip().strip('"')
            elif line.startswith("ANSWER:"):
                data["answer"] = line.replace("ANSWER:", "").strip().strip('"')
            elif line.startswith("FACT:"):
                data["fact"] = line.replace("FACT:", "").strip().strip('"')
            elif line.startswith("CATEGORY:"):
                data["category"] = line.replace("CATEGORY:", "").strip().lower()

        if not data["question"] or not data["answer"]:
            raise Exception("Bos cevap")

        print(f"[OK] Soru: {data['question']}")
        print(f"[OK] Cevap: {data['answer']}")
        return data

    except Exception as e:
        print(f"[WARN] Groq hatasi ({e}). Yedek kullaniliyor.")
        fallbacks = [
            {"question": "How long would it take to drive to the Moon at highway speed?",
             "answer": "About 6 months.",
             "fact": "The Moon is 384,400 km away, which equals roughly 160 days of non-stop driving at 100 km/h.",
             "category": "space"},
            {"question": "What percentage of the ocean floor has been mapped by humans?",
             "answer": "Less than 25%.",
             "fact": "We have better maps of Mars and the Moon than of Earth's own ocean floor.",
             "category": "science"},
            {"question": "How many earths could fit inside the Sun?",
             "answer": "Over 1.3 million Earths.",
             "fact": "Yet the Sun is considered a medium-sized star compared to giants like UY Scuti.",
             "category": "space"},
        ]
        return random.choice(fallbacks)


# ============================================================
# ADIM 2: ARKA PLAN SEÇ
# ============================================================
def get_background():
    available = [i for i in range(1, 11)
                 if os.path.exists(os.path.join(_script_dir, f"arkaplan{i}.jpg"))]
    if not available:
        print("[WARN] Arkaplan bulunamadi, siyah kullanilacak.")
        return None
    idx = random.choice(available)
    path = os.path.join(_script_dir, f"arkaplan{idx}.jpg")
    print(f"[OK] Arkaplan: arkaplan{idx}.jpg")
    return path


# ============================================================
# ADIM 3: FONT YUKLEYİCİ
# ============================================================
def load_font(size, bold=False):
    candidates = []
    if bold:
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/ubuntu/Ubuntu-B.ttf",
            "C:\\Windows\\Fonts\\impact.ttf",
            "C:\\Windows\\Fonts\\arialbd.ttf",
        ]
    else:
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf",
            "C:\\Windows\\Fonts\\arial.ttf",
        ]
    for f in candidates:
        if os.path.exists(f):
            try:
                return ImageFont.truetype(f, size)
            except:
                continue
    return ImageFont.load_default()


# ============================================================
# ADIM 4: FRAME ÜRETİCİ
# ============================================================
def make_base_image(bg_path):
    """Arka planı yükle, overlay ekle."""
    if bg_path and os.path.exists(bg_path):
        img = Image.open(bg_path).convert("RGB")
        iw, ih = img.size
        ir, tr = iw / ih, W / H
        if ir > tr:
            nw = int(tr * ih)
            img = img.crop(((iw - nw) // 2, 0, (iw - nw) // 2 + nw, ih))
        else:
            nh = int(iw / tr)
            img = img.crop((0, (ih - nh) // 2, iw, (ih - nh) // 2 + nh))
        img = img.resize((W, H), Image.Resampling.LANCZOS)
    else:
        img = Image.new("RGB", (W, H), COL_BG)

    overlay = Image.new("RGBA", (W, H), COL_OVERLAY)
    img = img.convert("RGBA")
    img = Image.alpha_composite(img, overlay)
    return img.convert("RGB")


def draw_centered_text(draw, text, y, font, color, max_width=900):
    """Metni ortala, gerekirse satıra sar."""
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = (current + " " + word).strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] > max_width and current:
            lines.append(current)
            current = word
        else:
            current = test
    if current:
        lines.append(current)

    line_h = font.size + 12
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        x = (W - (bbox[2] - bbox[0])) // 2
        # Gölge
        draw.text((x + 3, y + i * line_h + 3), line, font=font, fill=(0, 0, 0))
        draw.text((x, y + i * line_h), line, font=font, fill=color)

    return y + len(lines) * line_h


def make_question_frame(bg_path, question):
    img = make_base_image(bg_path)
    draw = ImageDraw.Draw(img)

    # Üst çizgi dekor
    draw.rectangle([(W//2 - 200, 220), (W//2 + 200, 224)], fill=COL_TITLE)

    # "DID YOU KNOW?" başlık
    f_title = load_font(88, bold=True)
    draw_centered_text(draw, "DID YOU KNOW?", 240, f_title, COL_TITLE)

    # Soru metni
    f_q = load_font(62, bold=False)
    draw_centered_text(draw, question, 520, f_q, COL_QUESTION)

    # Alt dekor
    draw.rectangle([(W//2 - 200, H - 220), (W//2 + 200, H - 216)], fill=COL_TITLE)

    img.save("frame_question.jpg", quality=95)
    return "frame_question.jpg"


def make_countdown_frame(bg_path, number):
    img = make_base_image(bg_path)
    draw = ImageDraw.Draw(img)

    f_num = load_font(320, bold=True)
    bbox = draw.textbbox((0, 0), str(number), font=f_num)
    x = (W - (bbox[2] - bbox[0])) // 2
    y = (H - (bbox[3] - bbox[1])) // 2 - 60
    draw.text((x + 6, y + 6), str(number), font=f_num, fill=(0, 0, 0))
    draw.text((x, y), str(number), font=f_num, fill=COL_COUNTDOWN)

    f_small = load_font(48, bold=False)
    draw_centered_text(draw, "Think about it...", H - 300, f_small, (180, 180, 180))

    path = f"frame_count_{number}.jpg"
    img.save(path, quality=95)
    return path


def make_answer_frame(bg_path, answer, fact):
    img = make_base_image(bg_path)
    draw = ImageDraw.Draw(img)

    draw.rectangle([(W//2 - 200, 220), (W//2 + 200, 224)], fill=COL_ANSWER)

    f_ans_lbl = load_font(72, bold=True)
    draw_centered_text(draw, "ANSWER:", 240, f_ans_lbl, COL_ANSWER)

    f_ans = load_font(78, bold=True)
    next_y = draw_centered_text(draw, answer.upper(), 380, f_ans, COL_QUESTION)

    if fact:
        f_fact = load_font(46, bold=False)
        draw_centered_text(draw, fact, next_y + 60, f_fact, COL_FACT)

    draw.rectangle([(W//2 - 200, H - 220), (W//2 + 200, H - 216)], fill=COL_ANSWER)

    img.save("frame_answer.jpg", quality=95)
    return "frame_answer.jpg"


# ============================================================
# ADIM 5: VİDEO OLUŞTUR
# ============================================================
def create_video(trivia, bg_path):
    print("Video olusturuluyor...")

    q_frame  = make_question_frame(bg_path, trivia["question"])
    cd_frames = [make_countdown_frame(bg_path, n) for n in range(5, 0, -1)]
    a_frame  = make_answer_frame(bg_path, trivia["answer"], trivia.get("fact", ""))

    clips = []
    clips.append(ImageClip(q_frame, duration=3))
    for f in cd_frames:
        clips.append(ImageClip(f, duration=1))
    clips.append(ImageClip(a_frame, duration=4))

    final = concatenate_videoclips(clips, method="compose")

    # Müzik ekle
    music_path = os.path.join(_script_dir, "music.mp3")
    if os.path.exists(music_path):
        try:
            audio = AudioFileClip(music_path)
            start = random.randint(10, 30) if audio.duration > 35 else 0
            audio = audio.subclipped(start, min(start + 12, audio.duration))
            audio = audio.with_effects([
                __import__('moviepy.audio.fx', fromlist=['AudioFadeIn']).AudioFadeIn(0.5),
                __import__('moviepy.audio.fx', fromlist=['AudioFadeOut']).AudioFadeOut(1.0),
                __import__('moviepy.audio.fx', fromlist=['MultiplyVolume']).MultiplyVolume(0.2),
            ])
            final = final.with_audio(audio)
            print("[OK] Muzik eklendi.")
        except Exception as e:
            print(f"[WARN] Muzik eklenemedi: {e}")

    final.write_videofile(OUTPUT_VIDEO, fps=24, codec="libx264", logger=None)
    print(f"[OK] Video hazir: {OUTPUT_VIDEO}")

    # Temizlik
    for f in [q_frame, a_frame] + cd_frames:
        try: os.remove(f)
        except: pass

    return OUTPUT_VIDEO


# ============================================================
# ADIM 6: YOUTUBE'A YUKLE
# ============================================================
def upload_to_youtube(trivia):
    print("\nYouTube'a yukleniyor...")

    if not os.path.exists(SECRET_PATH):
        print(f"[ERROR] {SECRET_PATH} bulunamadi.")
        return

    SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
    creds = None

    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(SECRET_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, 'w') as f:
            f.write(creds.to_json())

    # Viral başlık üret
    hooks = [
        "Nobody talks about this...",
        "This will blow your mind.",
        "99% of people get this wrong.",
        "Wait for the answer...",
        "Can you guess the answer?",
        "This fact broke the internet.",
        "Most people don't know this.",
        "You won't believe this.",
    ]
    hook = random.choice(hooks)

    try:
        client = Groq(api_key=GROQ_API_KEY)
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content":
                f'Create a viral YouTube Shorts title for this trivia: "{trivia["question"]}" '
                f'Use this hook style: "{hook}". Max 60 chars. End with #shorts. ONLY THE TITLE:'}]
        )
        title = resp.choices[0].message.content.strip().replace('"', '')
    except:
        title = f"{hook} #shorts"

    cat_tags = {
        "science":    "#science #facts #didyouknow #mindblown #sciencefacts",
        "history":    "#history #historyfacts #didyouknow #historicalfacts #facts",
        "nature":     "#nature #naturefacts #didyouknow #wildlife #earthfacts",
        "space":      "#space #spacefacts #didyouknow #universe #nasa",
        "animals":    "#animals #animalfacts #didyouknow #wildlife #nature",
        "food":       "#food #foodfacts #didyouknow #cooking #nutrition",
        "technology": "#technology #techfacts #didyouknow #innovation #science",
        "psychology": "#psychology #mindset #didyouknow #brain #psychologyfacts",
    }
    extra = cat_tags.get(trivia.get("category", "science"),
                         "#facts #didyouknow #mindblown #interesting #learn")
    desc = f'Did you know? {trivia["question"]}\n\nAnswer: {trivia["answer"]}\n\n{trivia.get("fact","")}\n\n#shorts #didyouknow {extra}'

    print(f"Baslik: {title}")

    yt = build('youtube', 'v3', credentials=creds)
    body = {
        'snippet': {
            'title': title,
            'description': desc,
            'tags': ['did you know', 'facts', 'shorts', 'trivia', 'mindblown',
                     'interesting facts', 'daily facts', trivia.get("category", "science")],
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


# ============================================================
# ANA AKIŞ
# ============================================================
if __name__ == "__main__":
    print("\n=== Did You Know? Bot Basladi ===\n")

    trivia   = generate_trivia()
    bg_path  = get_background()
    video    = create_video(trivia, bg_path)
    upload_to_youtube(trivia)

    print("\n=== Tamamlandi! ===")
