#!/usr/bin/env python3
"""Generate a short narrated video, "Love Your Neighbor".

Inspired by the Sower and Seeds Ministries message
"Israelis or Palestinians: Whom should I support and why?"
(https://www.youtube.com/watch?v=SQ4wA0pgaJo).

Everything is generated in code: the artwork is drawn with Pillow/numpy,
the narration is synthesized with espeak-ng, and the music bed is a soft
synthesized chord pad. Output: output/love_your_neighbor.mp4

Requirements: python3, numpy, pillow, ffmpeg, espeak-ng
"""
import math
import os
import subprocess
import tempfile
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1280, 720, 24
SR = 22050
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
OUT_FILE = os.path.join(OUT_DIR, "love_your_neighbor.mp4")

FONT_DIRS = ["/usr/share/fonts/opentype/inter", "/usr/share/fonts/truetype/dejavu",
             "/System/Library/Fonts/Supplemental", "/Library/Fonts"]


def font(names, size):
    for d in FONT_DIRS:
        for n in names:
            p = os.path.join(d, n)
            if os.path.exists(p):
                return ImageFont.truetype(p, size)
    return ImageFont.load_default(size)


TITLE_FONT = font(["InterDisplay-Bold.otf", "DejaVuSans-Bold.ttf", "Arial Bold.ttf"], 64)
BODY_FONT = font(["InterDisplay-SemiBold.otf", "DejaVuSans.ttf", "Arial.ttf"], 46)
SMALL_FONT = font(["Inter-Medium.otf", "DejaVuSans.ttf", "Arial.ttf"], 28)

# ---------------------------------------------------------------- scenes
# Each scene: background style, on-screen text, small reference line, narration.
SCENES = [
    dict(bg="night", title="Israelis or Palestinians?", sub="Whom should I support, and why?",
         say="Israelis or Palestinians. Whom should I support, and why?"),
    dict(bg="dusk", title="Two peoples. One land.", sub="So much pain on every side.",
         say="Two peoples share one land, and there is deep pain and loss on every side. "
             "Many of us feel we must pick a team."),
    dict(bg="parchment", title="“Who is my neighbour?”", sub="Luke 10:29",
         say="Long ago, a man asked Jesus the same kind of question. Who is my neighbor?"),
    dict(bg="rays", title="“Thou shalt love thy neighbour\nas thyself.”", sub="Matthew 22:39",
         say="And the answer of our Lord is clear. Love your neighbor as yourself."),
    dict(bg="two", title="Both are our neighbours.", sub="Every family. Every child. Every life.",
         say="Both Israelis and Palestinians are our neighbors. Every family, every child, "
             "every life is precious to God."),
    dict(bg="olive", title="“Blessed are the peacemakers.”", sub="Matthew 5:9",
         say="So we do not take up hatred for one against the other. We pray, and we work for peace."),
    dict(bg="candles", title="Pray for every grieving home.", sub="",
         say="Pray for the hostages and for the hungry. Pray for every mother and father who grieves."),
    dict(bg="sunrise", title="All are safe in the will of God.", sub="",
         say="This is the good news. All are safe in the will of God. Let us run to Him and be saved."),
    dict(bg="dawn", title="“Come unto me …\nand I will give you rest.”", sub="Matthew 11:28",
         say="The Lord Jesus Christ is calling everyone to repent and come to Him, "
             "for that very place of rest."),
    dict(bg="end", title="Love your neighbour.", sub="Inspired by a message from Sower and Seeds Ministries",
         say="Love your neighbor."),
]

# ---------------------------------------------------------------- backgrounds
BW, BH = int(W * 1.12), int(H * 1.12)  # oversized for slow zoom


def vgrad(top, bottom, h=BH, w=BW, power=1.0):
    t = np.linspace(0, 1, h)[:, None, None] ** power
    a, b = np.array(top, float), np.array(bottom, float)
    return np.broadcast_to(a + (b - a) * t, (h, w, 3)).copy()


def radial(img, cx, cy, radius, color, strength):
    yy, xx = np.mgrid[0:img.shape[0], 0:img.shape[1]]
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / radius
    g = np.clip(1 - d, 0, 1)[..., None] ** 2 * strength
    return img * (1 - g) + np.array(color, float) * g


def hills(draw, base, amp, color, seed, w=BW, h=BH):
    rng = np.random.default_rng(seed)
    ph = rng.uniform(0, 6.28, 3)
    pts = [(0, h)]
    for x in range(0, w + 8, 8):
        y = base + amp * (0.6 * math.sin(x / 210 + ph[0]) + 0.3 * math.sin(x / 90 + ph[1])
                          + 0.1 * math.sin(x / 37 + ph[2]))
        pts.append((x, y))
    pts.append((w, h))
    draw.polygon(pts, fill=color)


def make_bg(kind):
    if kind in ("night", "end"):
        arr = vgrad((6, 10, 30), (30, 26, 60))
        arr = radial(arr, BW * 0.5, BH * 0.95, BH * 0.9, (90, 60, 120), 0.5)
    elif kind == "dusk":
        arr = vgrad((40, 30, 80), (230, 120, 80), power=1.3)
    elif kind == "parchment":
        arr = vgrad((236, 220, 186), (205, 180, 140))
        noise = np.random.default_rng(3).normal(0, 6, (BH, BW, 1))
        arr = arr + noise
        arr = radial(arr, BW / 2, BH / 2, BW * 0.8, (250, 240, 215), 0.4)
    elif kind == "rays":
        arr = vgrad((20, 30, 70), (90, 110, 170))
        yy, xx = np.mgrid[0:BH, 0:BW]
        ang = np.arctan2(yy + 200, xx - BW / 2)
        ray = (np.sin(ang * 26) * 0.5 + 0.5) ** 6
        fall = np.clip(1 - (yy + 200) / (BH * 1.3), 0, 1)
        arr = arr + (ray * fall)[..., None] * np.array([255, 230, 170]) * 0.45
        arr = radial(arr, BW / 2, -100, BH, (255, 240, 200), 0.6)
    elif kind == "two":
        arr = vgrad((15, 25, 50), (60, 50, 90))
    elif kind == "olive":
        arr = vgrad((200, 215, 190), (120, 150, 110))
    elif kind == "candles":
        arr = vgrad((8, 6, 10), (35, 20, 18))
    elif kind == "sunrise":
        arr = vgrad((60, 90, 160), (250, 170, 100), power=1.2)
        arr = radial(arr, BW / 2, BH * 0.78, BH * 0.7, (255, 225, 150), 0.9)
    elif kind == "dawn":
        arr = vgrad((140, 180, 230), (255, 220, 170), power=0.9)
        arr = radial(arr, BW / 2, BH * 0.7, BH * 0.9, (255, 250, 225), 0.9)
    else:
        arr = vgrad((0, 0, 0), (40, 40, 40))
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img)

    if kind == "dusk":
        hills(d, BH * 0.70, 40, (70, 40, 70), 1)
        hills(d, BH * 0.80, 30, (40, 22, 45), 2)
    elif kind == "dawn":
        hills(d, BH * 0.84, 30, (150, 140, 120), 6)
        hills(d, BH * 0.91, 20, (100, 110, 90), 7)
    elif kind == "olive":
        draw_olive_branch(img)
    return img


def draw_olive_branch(img):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    stem = [(BW * 0.12 + i * 9, BH * 0.86 - 90 * math.sin(i / 40)) for i in range(120)]
    d.line(stem, fill=(80, 70, 40, 255), width=7)
    for i in range(6, 118, 9):
        x, y = stem[i]
        for side in (-1, 1):
            leaf = Image.new("RGBA", (90, 30), (0, 0, 0, 0))
            ImageDraw.Draw(leaf).ellipse((0, 0, 89, 29), fill=(70, 110, 60, 235))
            leaf = leaf.rotate(side * 40 + i * 0.3, expand=True)
            layer.alpha_composite(leaf, (int(x - 10), int(y - 50 if side < 0 else y - 5)))
        if i % 27 == 0:
            d.ellipse((x + 10, y + 8, x + 34, y + 40), fill=(60, 70, 40, 255))
    img.paste(layer, (0, 0), layer)


BG_CACHE = {}
SUNRISE_HILLS = None


def sunrise_frame(p):
    """Sky + sun glow + hills, so the sun rises from behind the hills."""
    global SUNRISE_HILLS
    if SUNRISE_HILLS is None:
        SUNRISE_HILLS = Image.new("RGBA", (BW, BH), (0, 0, 0, 0))
        d = ImageDraw.Draw(SUNRISE_HILLS)
        hills(d, BH * 0.80, 35, (90, 60, 80, 255), 4)
        hills(d, BH * 0.88, 25, (50, 35, 55, 255), 5)
    sun = Image.new("RGBA", (BW, BH), (0, 0, 0, 0))
    d = ImageDraw.Draw(sun)
    cx, cy = BW / 2, BH * (0.86 - 0.2 * p)
    for r, a in ((230, 30), (140, 60), (80, 230)):
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 235, 170, a))
    img = BG_CACHE["sunrise"].convert("RGBA")
    img.alpha_composite(sun.filter(ImageFilter.GaussianBlur(10)))
    img.alpha_composite(SUNRISE_HILLS)
    return img


def background(kind, p):
    """p = progress 0..1 through the scene; slow zoom-in."""
    if kind not in BG_CACHE:
        BG_CACHE[kind] = make_bg(kind)
    img = sunrise_frame(p) if kind == "sunrise" else BG_CACHE[kind]
    z = 1.0 + 0.10 * p
    cw, ch = BW / z, BH / z
    x0, y0 = (BW - cw) / 2, (BH - ch) / 2
    return img.resize((W, H), Image.BILINEAR, box=(x0, y0, x0 + cw, y0 + ch)).convert("RGBA")


def make_glow(size=200, color=(255, 170, 70), peak=0.55):
    yy, xx = np.mgrid[0:size, 0:size]
    d = np.sqrt((xx - size / 2) ** 2 + (yy - size / 2) ** 2) / (size / 2)
    a = (np.clip(1 - d, 0, 1) ** 2 * peak * 255).astype(np.uint8)
    rgb = np.broadcast_to(np.array(color, np.uint8), (size, size, 3))
    return Image.fromarray(np.dstack([rgb, a]), "RGBA")


GLOW = make_glow()
STARS = np.random.default_rng(11).uniform(0, 1, (160, 3))


def animate(kind, frame, t, p):
    """Per-frame animated elements drawn over the background."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer, "RGBA")  # "RGBA" mode blends overlapping shapes
    if kind in ("night", "end"):
        for i, (sx, sy, ph) in enumerate(STARS):
            a = int(120 + 120 * math.sin(t * 2 + ph * 20))
            r = 1 + (i % 3 == 0)
            x, y = sx * W, sy * H * 0.85
            d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 240, a))
    elif kind == "two":
        # Two lights moving toward each other and joining into one glow.
        gap = 380 * (1 - min(1, p * 1.3)) + 60
        for cx, col in ((W / 2 - gap, (120, 180, 255)), (W / 2 + gap, (255, 200, 120))):
            for r, a in ((110, 30), (70, 60), (40, 140), (22, 255)):
                d.ellipse((cx - r, H * 0.68 - r, cx + r, H * 0.68 + r), fill=col + (a,))
        layer = layer.filter(ImageFilter.GaussianBlur(6))
    elif kind == "candles":
        for i, cx in enumerate((W * 0.2, W * 0.35, W * 0.5, W * 0.65, W * 0.8)):
            base = H * 0.92
            hgt = 140 + 30 * (i % 2)
            d.rectangle((cx - 16, base - hgt, cx + 16, base), fill=(235, 225, 205, 255))
            fl = 1 + 0.12 * math.sin(t * 9 + i * 1.7) + 0.06 * math.sin(t * 23 + i)
            top = base - hgt
            g = int(170 * fl)
            layer.alpha_composite(GLOW.resize((g, g)), (int(cx - g / 2), int(top - 22 - g / 2)))
            d.ellipse((cx - 9, top - 30 - 26 * fl, cx + 9, top - 4), fill=(255, 200, 100, 255))
            d.ellipse((cx - 4, top - 22 - 14 * fl, cx + 4, top - 8), fill=(255, 250, 225, 255))
            d.line([(cx, top), (cx, top - 8)], fill=(40, 30, 20, 255), width=2)
    elif kind == "dawn":
        for i in range(5):  # birds
            x = (t * 60 + i * 170) % (W + 200) - 100
            y = H * 0.3 + 40 * math.sin(i * 2.1) + 6 * math.sin(t * 3 + i)
            wing = 10 * math.sin(t * 8 + i)
            d.line([(x - 18, y - wing), (x, y), (x + 18, y - wing)], fill=(60, 60, 80, 220), width=3)
    return layer


# ---------------------------------------------------------------- text
def text_layer(title, sub, alpha, dark):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    fg = (40, 30, 20) if dark else (255, 255, 255)
    sh = (255, 255, 255) if dark else (0, 0, 0)
    tf = TITLE_FONT if len(title) < 34 else BODY_FONT
    tb = d.multiline_textbbox((0, 0), title, font=tf, align="center", spacing=14)
    tw, th = tb[2] - tb[0], tb[3] - tb[1]
    y = H * 0.40 - th / 2
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.multiline_text(((W - tw) / 2, y), title, font=tf, fill=sh + (int(170 * alpha),), align="center", spacing=14)
    if sub:
        sb = d.textbbox((0, 0), sub, font=SMALL_FONT)
        sd.text(((W - (sb[2] - sb[0])) / 2, y + th + 34), sub, font=SMALL_FONT, fill=sh + (int(170 * alpha),))
    layer.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(5)))
    d.multiline_text(((W - tw) / 2, y), title, font=tf, fill=fg + (int(255 * alpha),), align="center", spacing=14)
    if sub:
        d.text(((W - (sb[2] - sb[0])) / 2, y + th + 34), sub, font=SMALL_FONT, fill=fg + (int(230 * alpha),))
    return layer


# ---------------------------------------------------------------- audio
def tts(text, path):
    subprocess.run(["espeak-ng", "-v", "en-us+m3", "-s", "140", "-p", "40", "-g", "6",
                    "-w", path, text], check=True)
    with wave.open(path) as w:
        data = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
        rate = w.getframerate()
    if rate != SR:
        idx = np.linspace(0, len(data) - 1, int(len(data) * SR / rate))
        data = np.interp(idx, np.arange(len(data)), data)
    return data


def pad_music(n):
    """Slow, soft chord pad: I - vi - IV - V in D major, 8 s per chord."""
    t = np.arange(n) / SR
    chords = [(146.83, 185.00, 220.00), (123.47, 146.83, 185.00),
              (196.00, 246.94, 293.66), (220.00, 277.18, 329.63)]
    out = np.zeros(n, np.float32)
    seg = 8 * SR
    for start in range(0, n, seg):
        end = min(n, start + seg + SR)  # 1 s overlap for crossfade
        tt = t[start:end]
        env = np.minimum(1, (tt - tt[0]) / 2) * np.minimum(1, (tt[-1] - tt) / 2 + 0.001)
        for f in chords[(start // seg) % 4]:
            out[start:end] += env * (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * f * 2.003 * tt))
    out /= np.abs(out).max() + 1e-9
    return out * 0.12


def write_wav(path, data):
    data = np.clip(data, -1, 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((data * 32767).astype(np.int16).tobytes())


# ---------------------------------------------------------------- main
def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    tmp = tempfile.mkdtemp()
    lead, tail, fade = 0.8, 1.4, 0.6

    voice_parts, durations = [], []
    for i, s in enumerate(SCENES):
        v = tts(s["say"], os.path.join(tmp, f"v{i}.wav"))
        dur = lead + len(v) / SR + tail
        clip = np.zeros(int(dur * SR), np.float32)
        clip[int(lead * SR):int(lead * SR) + len(v)] = v * 0.9
        voice_parts.append(clip)
        durations.append(len(clip) / SR)
    voice = np.concatenate(voice_parts)
    music = pad_music(len(voice))
    total = len(voice) / SR
    fade_n = int(2 * SR)
    music[-fade_n:] *= np.linspace(1, 0, fade_n)
    audio_path = os.path.join(tmp, "audio.wav")
    write_wav(audio_path, voice + music)

    ff = subprocess.Popen([
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-i", audio_path,
        "-c:v", "libx264", "-preset", "medium", "-crf", "23", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", OUT_FILE,
    ], stdin=subprocess.PIPE)

    frame = 0
    for s, dur in zip(SCENES, durations):
        n = int(round(dur * FPS))
        dark = s["bg"] in ("parchment", "olive", "dawn")
        for k in range(n):
            t = k / FPS
            p = k / max(1, n - 1)
            img = background(s["bg"], p)
            img.alpha_composite(animate(s["bg"], frame, t, p))
            ta = min(1, max(0, (t - 0.3) / 0.8)) * min(1, max(0, (dur - t - 0.2) / 0.6))
            if ta > 0:
                img.alpha_composite(text_layer(s["title"], s["sub"], ta, dark))
            # fade through black between scenes
            edge = min(t / fade, (dur - t) / fade, 1)
            rgb = np.asarray(img.convert("RGB"), np.float32) * max(0, edge)
            ff.stdin.write(rgb.astype(np.uint8).tobytes())
            frame += 1
    ff.stdin.close()
    ff.wait()
    print(f"Wrote {OUT_FILE} ({total:.1f}s, {frame} frames)")


if __name__ == "__main__":
    main()
