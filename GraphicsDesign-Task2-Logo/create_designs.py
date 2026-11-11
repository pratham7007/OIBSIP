"""Generate original, print-sized graphics deliverables using Pillow."""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).parent
COLORS = {
    "ink": "#142b3b",
    "teal": "#167d80",
    "coral": "#ed765d",
    "cream": "#f7f3e8",
    "gold": "#f2bd55",
    "white": "#ffffff",
    "muted": "#60717b",
}
FONT_DIR = Path(r"C:\Windows\Fonts")


def font(size: int, bold: bool = False, serif: bool = False) -> ImageFont.FreeTypeFont:
    candidates = (
        ["georgiab.ttf", "georgia.ttf"] if serif and bold else
        ["georgia.ttf"] if serif else
        ["segoeuib.ttf", "arialbd.ttf"] if bold else
        ["segoeui.ttf", "arial.ttf"]
    )
    for candidate in candidates:
        path = FONT_DIR / candidate
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def rounded(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], radius: int, fill: str) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill)


def wrap(draw: ImageDraw.ImageDraw, text: str, face: ImageFont.FreeTypeFont, width: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for word in text.split():
        attempt = f"{current} {word}".strip()
        if draw.textbbox((0, 0), attempt, font=face)[2] <= width:
            current = attempt
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def paragraph(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, face: ImageFont.FreeTypeFont,
              fill: str, width: int, gap: int = 8) -> int:
    x, y = xy
    for line in wrap(draw, text, face, width):
        draw.text((x, y), line, font=face, fill=fill)
        y += face.size + gap
    return y


def draw_mark(draw: ImageDraw.ImageDraw, cx: int, cy: int, radius: int, color: str, bg: str | None = None) -> None:
    draw.ellipse((cx-radius, cy-radius, cx+radius, cy+radius), fill=bg or color)
    # Three rising rays form an original, simple sunrise/forward-motion symbol.
    inner = int(radius * 0.48)
    draw.arc((cx-inner, cy-inner, cx+inner, cy+inner), 205, 335, fill=COLORS["white"] if bg else COLORS["cream"], width=max(4, radius//12))
    for angle in (225, 270, 315):
        r1, r2 = radius * 0.58, radius * 0.82
        x1, y1 = cx + math.cos(math.radians(angle))*r1, cy + math.sin(math.radians(angle))*r1
        x2, y2 = cx + math.cos(math.radians(angle))*r2, cy + math.sin(math.radians(angle))*r2
        draw.line((x1, y1, x2, y2), fill=COLORS["white"] if bg else COLORS["cream"], width=max(4, radius//12))


def make_logo() -> None:
    folder = ROOT / "outputs" / "logo"
    folder.mkdir(exist_ok=True)
    variants = [
        ("full_color", COLORS["teal"], COLORS["ink"], (0, 0, 0, 0)),
        ("monochrome", "#111111", "#111111", (0, 0, 0, 0)),
        ("reversed", COLORS["white"], COLORS["white"], COLORS["ink"]),
    ]
    for name, mark_color, type_color, bg in variants:
        size = 1200
        image = Image.new("RGBA", (size, size), bg)
        draw = ImageDraw.Draw(image)
        draw_mark(draw, 600, 390, 195, mark_color, COLORS["ink"] if name == "reversed" else None)
        title_font = font(120, bold=True)
        subtitle_font = font(36)
        draw.text((600, 690), "LUMEN", anchor="mm", font=title_font, fill=type_color)
        draw.text((600, 795), "STUDIO  /  DESIGN WITH PURPOSE", anchor="mm", font=subtitle_font, fill=type_color)
        image.save(folder / f"lumen_logo_{name}.png", dpi=(300, 300))
        fill = mark_color
        svg_bg = f'<rect width="1200" height="1200" fill="{bg}"/>' if bg != (0, 0, 0, 0) else ""
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="1200" viewBox="0 0 1200 1200">
{svg_bg}
<circle cx="600" cy="390" r="195" fill="{COLORS["ink"] if name == "reversed" else fill}"/>
<path d="M520 425 A92 92 0 0 1 680 425 M600 278v48 M520 315l34 35 M680 315l-34 35" fill="none" stroke="{COLORS["white"] if name == "reversed" else COLORS["cream"]}" stroke-width="15" stroke-linecap="round"/>
<text x="600" y="730" text-anchor="middle" font-family="Arial,sans-serif" font-size="120" font-weight="700" fill="{type_color}">LUMEN</text>
<text x="600" y="805" text-anchor="middle" font-family="Arial,sans-serif" font-size="30" letter-spacing="3" fill="{type_color}">STUDIO / DESIGN WITH PURPOSE</text>
</svg>'''
        (folder / f"lumen_logo_{name}.svg").write_text(svg, encoding="utf-8")
    (folder / "design_rationale.txt").write_text(
        "LUMEN Studio uses a rising-sun mark to suggest clarity, momentum, and thoughtful creative work. "
        "Deep teal and warm cream feel composed and approachable, while a restrained geometric mark and "
        "single sans-serif wordmark keep the identity legible at small sizes.\n",
        encoding="utf-8",
    )
    (folder / "linkedin_post_copy.txt").write_text(
        "Introducing the LUMEN Studio identity: a rising-sun mark represents clarity, momentum, and thoughtful "
        "creative work. Deep teal and warm cream create an approachable, composed palette, while a simple "
        "geometric symbol and clear wordmark keep the logo legible across uses.\n\n"
        "#LogoDesign #BrandIdentity #GraphicDesign\n",
        encoding="utf-8",
    )


def poster(path: Path, title: str, subtitle: str, body: str, cta: str, palette: tuple[str, str, str], motif: str) -> None:
    w, h = 1240, 1754
    bg, accent, ink = palette
    image = Image.new("RGB", (w, h), bg)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, w, 24), fill=accent)
    draw.text((80, 82), "LUMEN  /  COMMUNITY SERIES", font=font(30, bold=True), fill=ink)
    if motif == "sun":
        draw_mark(draw, 950, 510, 210, accent)
        draw.arc((750, 300, 1150, 700), 210, 330, fill=ink, width=8)
    else:
        draw.ellipse((760, 300, 1140, 680), fill=accent)
        draw.ellipse((850, 390, 1050, 590), fill=bg)
        for i in range(5):
            draw.line((760, 730+i*18, 1140, 560+i*18), fill=accent, width=6)
    y = 410
    for line in title.split("\n"):
        draw.text((80, y), line, font=font(112, bold=True), fill=ink)
        y += 132
    paragraph(draw, (86, y+22), subtitle, font(42, bold=True), accent, 690, 14)
    paragraph(draw, (86, y+175), body, font(31), ink, 680, 15)
    rounded(draw, (80, 1460, 610, 1560), 22, accent)
    draw.text((345, 1510), cta.upper(), anchor="mm", font=font(30, bold=True), fill=bg)
    draw.text((82, 1660), "ORIGINAL EVENT CONCEPT  •  LUMEN STUDIO", font=font(23), fill=ink)
    image.save(path, dpi=(150, 150))


def make_posters() -> None:
    folder = ROOT / "outputs" / "posters"
    folder.mkdir(exist_ok=True)
    poster(folder / "01_slow_mornings.png", "SLOW\nMORNINGS", "A neighbourhood coffee and makers market",
           "Meet local makers, find your next favourite cup, and take a little time for yourself.\n\nSaturday, 9 AM–2 PM  •  Riverside Hall",
           "Free entry  ·  Bring a friend", (COLORS["cream"], COLORS["teal"], COLORS["ink"]), "sun")
    poster(folder / "02_repair_together.png", "REPAIR\nTOGETHER", "A practical, welcoming community repair day",
           "Bring one small household item and learn how to give it a longer life.\n\nSunday, 10 AM–1 PM  •  The Common Room",
           "Reserve a free place", ("#eaf3f1", COLORS["coral"], COLORS["ink"]), "rings")


def make_cards() -> None:
    folder = ROOT / "outputs" / "business-card"
    folder.mkdir(exist_ok=True)
    w, h = 1075, 720  # 91 x 61 mm including 3 mm bleed at 300 dpi.
    images = []
    front = Image.new("RGB", (w, h), COLORS["ink"])
    d = ImageDraw.Draw(front)
    d.rectangle((0, 0, 28, h), fill=COLORS["coral"])
    draw_mark(d, 210, 215, 110, COLORS["teal"])
    d.text((360, 140), "LUMEN", font=font(70, bold=True), fill=COLORS["white"])
    d.text((365, 225), "STUDIO", font=font(28), fill=COLORS["gold"])
    d.line((360, 315, 960, 315), fill="#45606c", width=2)
    d.text((360, 390), "PRATHAMESH KARANJKAR", font=font(42, bold=True), fill=COLORS["white"])
    d.text((362, 455), "Creative Director", font=font(30), fill="#c6d6d5")
    d.text((360, 625), "DESIGN WITH PURPOSE", font=font(22, bold=True), fill=COLORS["gold"])
    images.append(front)
    back = Image.new("RGB", (w, h), COLORS["cream"])
    d = ImageDraw.Draw(back)
    d.rectangle((0, 0, w, 20), fill=COLORS["teal"])
    d.text((80, 88), "LET'S MAKE", font=font(32, bold=True), fill=COLORS["teal"])
    d.text((80, 132), "something meaningful.", font=font(46, serif=True), fill=COLORS["ink"])
    d.line((80, 235, 995, 235), fill="#c4d2cc", width=3)
    details = [
        ("PHONE", "+91 8010956261"),
        ("EMAIL", "pkaranjkar7007@gmail.com"),
        ("WEB", "lumen.studio.example"),
        ("SOCIAL", "@lumen.studio  ·  linkedin.com/in/prathmesh-karanjkar"),
    ]
    y = 285
    for label, value in details:
        d.text((82, y), label, font=font(20, bold=True), fill=COLORS["teal"])
        d.text((270, y-2), value, font=font(27), fill=COLORS["ink"])
        y += 84
    images.append(back)
    for name, image in zip(("front", "back"), images):
        image.save(folder / f"lumen_business_card_{name}.png", dpi=(300, 300))
    images[0].save(folder / "lumen_business_card_print.pdf", save_all=True, append_images=images[1:], resolution=300)


def make_infographic() -> None:
    folder = ROOT / "outputs" / "infographic"
    folder.mkdir(exist_ok=True)
    w, h = 800, 2000
    palette = {
        "cream": "#f7f3e8",
        "ink": "#142b3b",
        "teal": "#167d80",
        "gold": "#f2bd55",
    }
    image = Image.new("RGB", (w, h), palette["cream"])
    d = ImageDraw.Draw(image)
    d.rectangle((0, 0, w, 350), fill=palette["ink"])
    d.text((48, 40), "WELLBEING  /  FIELD GUIDE", font=font(20, bold=True), fill=palette["gold"])
    d.text((48, 92), "SMALL HABITS,", font=font(48, bold=True), fill=palette["cream"])
    d.text((48, 150), "STRONGER DAYS", font=font(48, bold=True), fill=palette["cream"])
    paragraph(d, (50, 225), "Five practical, evidence-based reminders for a healthier routine.",
              font(21), palette["cream"], 660, 5)
    cards = [
        ("01", "MOVE MORE", "Adults: aim for 150–300 minutes of moderate activity each week.",
         "A brisk walk counts. Break it into manageable sessions.", "150–300", "min / week"),
        ("02", "BUILD STRENGTH", "Work all major muscle groups on 2 or more days each week.",
         "Body-weight exercises are one accessible option.", "2+", "days / week"),
        ("03", "KIDS NEED PLAY", "Children and adolescents should average at least 60 minutes of activity per day.",
         "Make movement enjoyable and age appropriate.", "60", "min / day"),
        ("04", "PROTECT SLEEP", "Adults aged 18–60 should get 7 or more hours of sleep per night.",
         "A consistent bedtime can support a regular routine.", "7+", "hours / night"),
        ("05", "TAKE SMALL STEPS", "Some activity is better than none; start where you are and build gradually.",
         "Choose one action you can repeat this week.", "1", "next step"),
    ]
    for index, (num, title, lead, detail, stat, unit) in enumerate(cards):
        y = 375 + index * 278
        d.rounded_rectangle((40, y, 760, y + 255), radius=20, fill=palette["cream"],
                            outline=palette["teal"], width=3)
        d.ellipse((62, y + 28, 112, y + 78), fill=palette["teal"])
        d.text((87, y + 53), num, anchor="mm", font=font(17, bold=True), fill=palette["cream"])
        d.text((130, y + 31), title, font=font(25, bold=True), fill=palette["ink"])
        paragraph(d, (64, y + 92), lead, font(17, bold=True), palette["ink"], 650, 4)
        d.text((64, y + 157), stat, font=font(35, bold=True), fill=palette["teal"])
        d.text((220, y + 174), unit, font=font(16, bold=True), fill=palette["ink"])
        paragraph(d, (64, y + 210), detail, font(14), palette["ink"], 640, 2)

        visual_x = 555
        visual_y = y + 184
        if index == 0:
            d.text((visual_x, y + 116), "WEEKLY RANGE", font=font(11, bold=True), fill=palette["ink"])
            d.line((visual_x, visual_y, 720, visual_y), fill=palette["ink"], width=4)
            d.line((visual_x + 82, visual_y, 720, visual_y), fill=palette["teal"], width=10)
            d.ellipse((visual_x + 76, visual_y - 6, visual_x + 88, visual_y + 6), fill=palette["gold"])
            d.ellipse((714, visual_y - 6, 726, visual_y + 6), fill=palette["gold"])
            d.text((visual_x, visual_y + 10), "0", font=font(10), fill=palette["ink"])
            d.text((visual_x + 65, visual_y + 10), "150", font=font(10), fill=palette["ink"])
            d.text((695, visual_y + 10), "300", font=font(10), fill=palette["ink"])
        elif index == 1:
            d.text((visual_x, y + 116), "DAYS / WEEK", font=font(11, bold=True), fill=palette["ink"])
            for day in range(7):
                x = visual_x + day * 24
                d.rounded_rectangle((x, visual_y - 13, x + 17, visual_y + 4), radius=4,
                                    fill=palette["teal"] if day < 2 else palette["gold"])
                d.text((x + 8, visual_y + 10), "MTWTFSS"[day], anchor="mm",
                       font=font(9, bold=True), fill=palette["ink"])
        elif index == 2:
            d.text((visual_x, y + 116), "DAILY MOVEMENT", font=font(11, bold=True), fill=palette["ink"])
            d.ellipse((visual_x + 22, visual_y - 25, visual_x + 72, visual_y + 25),
                      outline=palette["gold"], width=8)
            d.arc((visual_x + 22, visual_y - 25, visual_x + 72, visual_y + 25),
                  -90, 180, fill=palette["teal"], width=8)
            d.text((visual_x + 47, visual_y), "60", anchor="mm",
                   font=font(14, bold=True), fill=palette["ink"])
        elif index == 3:
            d.text((visual_x, y + 116), "HOURS / NIGHT", font=font(11, bold=True), fill=palette["ink"])
            d.ellipse((visual_x + 22, visual_y - 25, visual_x + 72, visual_y + 25),
                      outline=palette["teal"], width=4)
            d.line((visual_x + 47, visual_y, visual_x + 47, visual_y - 15,
                    visual_x + 61, visual_y - 15), fill=palette["gold"], width=4)
        else:
            d.text((visual_x, y + 116), "A REPEATABLE ROUTINE", font=font(11, bold=True), fill=palette["ink"])
            nodes = [(visual_x + 12, visual_y), (visual_x + 63, visual_y - 18),
                     (visual_x + 114, visual_y)]
            d.line((nodes[0], nodes[1], nodes[2]), fill=palette["teal"], width=4)
            for point in nodes:
                d.ellipse((point[0] - 8, point[1] - 8, point[0] + 8, point[1] + 8),
                          fill=palette["gold"], outline=palette["ink"], width=2)

    d.text((48, 1770), "SOURCES", font=font(15, bold=True), fill=palette["teal"])
    d.text((48, 1798), "WHO physical activity guidelines: who.int/news-room/fact-sheets/detail/physical-activity",
           font=font(11), fill=palette["ink"])
    d.text((48, 1820), "CDC sleep recommendations: cdc.gov/sleep/about/index.html",
           font=font(11), fill=palette["ink"])
    d.text((48, 1852), "Informational only — not medical advice.", font=font(11), fill=palette["ink"])
    image.save(folder / "small_habits_wellbeing_infographic.png", dpi=(150, 150))


def make_brochure() -> None:
    folder = ROOT / "outputs" / "brochure"
    folder.mkdir(exist_ok=True)
    w, h = 1240, 1754
    pages: list[Image.Image] = []
    topics = [
        ("FIELD NOTES", "A slower kind of weekend", "A guide to small, local discoveries.", "cover"),
        ("01 / ARRIVE", "Leave room to wander", "Choose one neighbourhood, begin on foot, and let curiosity set the pace. The best plans leave a little space for surprise.", "photo"),
        ("02 / TASTE", "Follow the good things", "Look for a seasonal menu, a family-run bakery, or a market stall with a story behind it. Ask what is fresh today.", "article"),
        ("03 / NOTICE", "Take the scenic route", "A park, a quiet side street, a public garden: small pauses can change the rhythm of a day. Bring a notebook, not a checklist.", "photo"),
        ("04 / CONNECT", "Meet the makers", "Buy thoughtfully, learn how something is made, and support the independent places that give a neighbourhood its character.", "article"),
        ("FIELD NOTES", "Make your own map", "Go gently. Stay curious. Leave the place better than you found it.", "back"),
    ]
    for page_number, (kicker, title, copy, style) in enumerate(topics, start=1):
        background = COLORS["ink"] if style in {"cover", "photo", "back"} else COLORS["cream"]
        image = Image.new("RGB", (w, h), background)
        d = ImageDraw.Draw(image)
        if style in {"cover", "photo"}:
            # Original abstract, full-bleed illustration used instead of unlicensed stock photography.
            d.ellipse((520, 380, 1510, 1370), fill=COLORS["teal"] if page_number % 2 else COLORS["coral"])
            d.ellipse((690, 540, 1390, 1240), fill=COLORS["gold"])
            d.polygon([(0, 1170), (430, 770), (790, 1170), (1240, 610), (1240, 1754), (0, 1754)], fill="#315263")
            d.ellipse((870, 690, 1210, 1030), fill=COLORS["cream"])
            d.rectangle((0, 0, w, 22), fill=COLORS["coral"])
            fg = COLORS["white"]
        else:
            fg = COLORS["ink"]
        d.text((86, 75), "LUMEN  /  FIELD NOTES", font=font(24, bold=True), fill=COLORS["gold"] if background == COLORS["ink"] else COLORS["teal"])
        d.text((86, 170), kicker, font=font(20, bold=True), fill=COLORS["coral"] if background == COLORS["ink"] else COLORS["teal"])
        if style in {"cover", "back"}:
            y_title = 1110 if style == "cover" else 330
            for line in wrap(d, title, font(72, bold=True), 1030):
                d.text((86, y_title), line, font=font(72, bold=True), fill=fg)
                y_title += 84
            paragraph(d, (90, y_title+24), copy, font(24), "#e2e8e4", 900, 12)
        elif style == "article":
            d.text((86, 300), title, font=font(58, serif=True), fill=fg)
            d.line((88, 410, 1150, 410), fill=COLORS["coral"], width=6)
            paragraph(d, (90, 490), copy, font(24), COLORS["muted"], 850, 14)
            rounded(d, (90, 900, 1120, 1260), 22, "#eaf3f1")
            d.text((135, 940), "PULL QUOTE", font=font(18, bold=True), fill=COLORS["teal"])
            paragraph(d, (135, 1000), "“A good day is not measured by how much you fit in, but by what you notice.”",
                      font(34, serif=True), COLORS["ink"], 900, 12)
            d.text((90, 1340), "TRY THIS", font=font(20, bold=True), fill=COLORS["teal"])
            paragraph(d, (90, 1390), "Pick one idea. Make it yours. Leave time to pause.", font(26), COLORS["ink"], 900, 10)
        else:
            d.text((86, 300), title, font=font(62, serif=True), fill=fg)
            paragraph(d, (90, 430), copy, font(24), "#dce5e2", 860, 14)
            d.text((90, 640), "A SIMPLE PLAN", font=font(20, bold=True), fill=COLORS["gold"])
            for i, line in enumerate(("Choose one local stop.", "Walk a different street.", "Take a mindful pause.", "Share what you discovered.")):
                y_item = 700 + i * 95
                d.ellipse((95, y_item, 135, y_item+40), fill=COLORS["coral"])
                d.text((165, y_item-2), line, font=font(28), fill=COLORS["white"])
        d.line((86, 1655, 1150, 1655), fill="#55717c" if background == COLORS["ink"] else "#bfd0ca", width=2)
        d.text((88, 1680), f"FIELD NOTES  •  LUMEN STUDIO  •  {page_number:02}", font=font(17, bold=True),
               fill="#dce5e2" if background == COLORS["ink"] else COLORS["muted"])
        pages.append(image)
    pages[0].save(folder / "lumen_field_notes_brochure.pdf", save_all=True, append_images=pages[1:], resolution=150)
    for i, page in enumerate(pages, start=1):
        page.save(folder / f"page_{i:02}.png", dpi=(150, 150))


def main() -> None:
    make_logo()
    make_posters()
    make_cards()
    make_infographic()
    make_brochure()
    print("Created logo variants, two posters, print-ready card, infographic, and six-page brochure.")


if __name__ == "__main__":
    main()
