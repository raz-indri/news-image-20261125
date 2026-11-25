#!/usr/bin/env python3
"""Render one front page of the world's news of Wednesday 25 November 2026.

Original work for make.fun news-image-20261125. Draws a single
deterministic 1024x1024 newspaper front page (news.png) with PIL only:
masthead, lead story, regional panels and a timeline. No network, no
randomness, no clock reads: the same input always renders the same bytes.
"""

import hashlib
import os
from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
FONT_DIR = "/usr/share/fonts/truetype/dejavu"

PAPER = (247, 243, 232)
INK = (20, 20, 20)
NAVY = (15, 42, 74)
NAVY_DARK = (10, 30, 54)
RED = (176, 42, 30)
GOLD = (201, 162, 39)
GOLD_LIGHT = (232, 203, 110)
GREY = (90, 88, 82)
RULE = (180, 175, 160)
SEA = (23, 68, 110)
SEA_DARK = (13, 46, 80)
SKY = (24, 32, 54)

REGION_COLORS = {
    "EUROPE": (29, 78, 137),
    "ASIA-PACIFIC": (14, 122, 95),
    "MIDDLE EAST": (138, 90, 0),
    "AFRICA": (122, 62, 0),
    "UNITED STATES": (90, 30, 90),
    "TECH & SCIENCE": (40, 90, 40),
}

# (region, bold lead, rest of the one-liner) -- each entry is one story.
PANELS = [
    ("EUROPE", [
        ("Sarkozy to stand trial.",
         " Court orders ex-president to trial; hearing Apr 2027."),
        ("V4 reject EU budget cut.",
         " Four PMs demand the ETS2 carbon price be delayed."),
        ("UK: nuclear veterans panel.",
         " Burnham orders an inquiry into atomic test veterans' health."),
        ("UK: age of consent review.",
         " Ministers open a public consultation on changing it."),
        ("EU hits Russia again.",
         " Brussels announces fresh sanctions as the war grinds on."),
    ]),
    ("ASIA-PACIFIC", [
        ("Australia-Solomons pact.",
         " Canberra becomes Honiara's defence partner of choice."),
        ("ASEAN-China code fails.",
         " Two decades of talks end with no South China Sea code in Manila."),
        ("Russian jets near Korea.",
         " Seoul scrambles fighters as Russian planes enter its zone."),
        ("Seoul minister quits.",
         " Education minister Choi Kyo-jin quits over an AI exam-cheating scandal."),
        ("ICJ: Myanmar guilty of genocide.",
         " World court rules against Myanmar over the Rohingya."),
    ]),
    ("MIDDLE EAST", [
        ("Houthis 60 km from Aden.",
         " Yemen's army says the rebels will not take the capital."),
        ("Gaza: UN sounds alarm.",
         " The UN warns of deepening hardship for civilians seeking aid."),
        ("Hamas security chief killed.",
         " Israeli strikes in Gaza kill a security chief and six others."),
        ("Iran faces a cold, dark winter.",
         " Gas shortages bite; power rationing begins after war damage."),
        ("Iran flogs singer.",
         " A singer is flogged for performing without a hijab, state media report."),
    ]),
    ("AFRICA", [
        ("AU condemns Benghazi attack.",
         " AU chair denounces strikes on ships off Libya's port."),
        ("ECOWAS single currency.",
         " West African ministers review plans for a 2027 launch."),
        ("Germany backs Africa at the UN.",
         " Steinmeier in Accra backs a stronger African voice."),
        ("MSF pulls out of Yei.",
         " Aid group suspends all work in South Sudan after an abduction."),
        ("Senegal keep AFCON crown.",
         " CAS reinstates Senegal's final win over Morocco."),
    ]),
    ("UNITED STATES", [
        ("Medal of Freedom for Giuliani.",
         " Trump honours his former lawyer Giuliani."),
        ("CIA and spy chiefs hacked.",
         " A breach hits unclassified CIA and ODNI systems."),
        ("Huawei convicted.",
         " Telecom giant found guilty in a US trial over its Iran business."),
        ("Turkeys spared.",
         " Trump pardons 'Freedom' and 'Feathers' in the Thanksgiving ceremony."),
        ("Fort Hood gunman seeks stay.",
         " Nidal Hasan asks a court to halt his execution next week."),
    ]),
    ("TECH & SCIENCE", [
        ("Nvidia's $1 trillion day.",
         " Shares jump 31.5% as Jensen Huang returns as CEO."),
        ("Microsoft declares 'Code Red'.",
         " Top-priority push to stop another Microsoft 365 collapse."),
        ("Dell rides the AI boom.",
         " Record quarter lifts forecasts on surging AI server demand."),
        ("Bitcoin funds bleed.",
         " US spot Bitcoin ETFs post a record $4.71 bn in November outflows."),
        ("A quasar from the dawn of time.",
         " Formed just 630 m years after the Big Bang."),
    ]),
]

MINIS = [
    ("GULF OF FINLAND", RED,
     "Ukraine hit a Russian ship",
     "Zelenskyy confirms the strike; Norway urges caution."),
    ("STRAIT OF HORMUZ", (138, 90, 0),
     "Three tankers hit by mines",
     "Iran's Revolutionary Guard blames naval mines in the strait."),
    ("POLAND  ·  NATO", (29, 78, 137),
     "Early-warning jets for Poland",
     "NATO to deploy aircraft after missiles landed in an attack on Ukraine."),
    ("MARKETS", (40, 90, 40),
     "Nvidia's $1 trillion day",
     "Shares jump 31.5% as Jensen Huang returns as CEO."),
]

SPORT = [
    "CRICKET: England beat Australia by 8 wickets",
    "FILM: Marvel drops 'Avengers: Doomsday' trailer",
    "CINEMA: Super Bowl LXI live in Imax",
    "GAMES: GTA 6 still tops charts",
]

TIMELINE = [
    ("22 NOV", "Merkury sunk"),
    ("23 NOV", "Zelenskyy confirms"),
    ("24 NOV", "Riyadh hit, 11 hurt"),
    ("00:56", "V4 reject EU cut"),
    ("01:06", "ASEAN-China fail"),
    ("01:50", "Riyadh toll confirmed"),
]

LEAD_KICKER = "UKRAINE  ·  LIBYA  ·  THE MEDITERRANEAN"
LEAD_HEADLINE = "UKRAINE SINKS RUSSIAN WARSHIP OFF LIBYA"
LEAD_DECK = ("Seven Ukrainian sea drones sank the corvette Merkury at Benghazi, "
             "President Zelenskyy confirms. The cargo ship Angara was hit too, "
             "and a Ka-27 helicopter destroyed. Kyiv's war at sea now reaches "
             "2,400 km from its shores.")

RIYADH_KICKER = "SAUDI ARABIA  ·  YEMEN"
RIYADH_HEADLINE = "HOUTHI DRONE HITS RIYADH'S TALLEST TOWER - 11 HURT"
RIYADH_DECK = ("Second strike on the 385 m PIF Tower in a week. The wounded "
               "include Saudis, Indians, Nepalese and Egyptians; the coalition "
               "vows a decisive response.")


def load_font(name, size):
    return ImageFont.truetype(os.path.join(FONT_DIR, name), size)


FONTS = {}


def font(name, size):
    key = (name, size)
    if key not in FONTS:
        FONTS[key] = load_font(name, size)
    return FONTS[key]


def wrap(draw, text, fnt, max_w):
    """Greedy word wrap; returns a list of lines that fit max_w."""
    words = text.split()
    lines, cur = [], ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if draw.textlength(trial, font=fnt) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_wrapped(draw, x, y, text, fnt, max_w, fill, line_h=None):
    """Draw wrapped text; return the y just below the last line."""
    if line_h is None:
        line_h = fnt.size + 4
    for line in wrap(draw, text, fnt, max_w):
        draw.text((x, y), line, font=fnt, fill=fill)
        y += line_h
    return y


def draw_rich_item(draw, x, y, lead, rest, max_w, size=13, line_h=15, max_lines=2):
    """Draw one panel item: bold lead + regular rest, wrapped word by word
    with each word measured in its own font, at most max_lines lines.
    Returns the y just below the last line."""
    f_b = font("DejaVuSans-Bold.ttf", size)
    f_r = font("DejaVuSans.ttf", size)
    words = [(w, True) for w in lead.split(" ")]
    words += [(w, False) for w in rest.split(" ")]
    lines, cur, cur_w = [], [], 0
    for word, bold in words:
        fnt = f_b if bold else f_r
        ww = draw.textlength(word, font=fnt)
        sp = draw.textlength(" ", font=fnt) if cur else 0
        if cur and cur_w + sp + ww > max_w:
            lines.append(cur)
            cur, cur_w = [(word, bold, ww)], ww
        else:
            cur.append((word, bold, ww))
            cur_w += sp + ww
    if cur:
        lines.append(cur)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        last = lines[-1]
        ell = draw.textlength("…", font=f_r)
        while last and sum(w[2] for w in last) + \
                sum(draw.textlength(" ", font=f_b if w[1] else f_r)
                    for w in last[1:]) + ell > max_w:
            last.pop()
        last.append(("…", False, ell))
    for li, line in enumerate(lines):
        cx = x
        for j, (word, bold, ww) in enumerate(line):
            fnt = f_b if bold else f_r
            if j > 0:
                cx += draw.textlength(" ", font=fnt)
            draw.text((cx, y + li * line_h), word, font=fnt, fill=INK)
            cx += ww
    return y + len(lines) * line_h


def story_count():
    total = 1 + 1 + len(MINIS) + len(SPORT)
    for _region, items in PANELS:
        total += len(items)
    return total


def draw_lead_scene(draw, x, y, w, h):
    """Geometric night-sea scene: sky, sea, ship silhouette, drones, blast."""
    draw.rectangle([x, y, x + w, y + h], fill=SKY)
    # stars
    for sx, sy in [(18, 8), (52, 20), (95, 6), (150, 16), (205, 9), (260, 18),
                   (320, 7), (380, 15), (440, 8), (500, 17), (560, 9)]:
        if sx < w - 4:
            draw.ellipse([x + sx, y + sy, x + sx + 3, y + sy + 3], fill=GOLD_LIGHT)
    # moon
    draw.ellipse([x + w - 58, y + 8, x + w - 30, y + 36], fill=(235, 230, 210))
    draw.ellipse([x + w - 50, y + 12, x + w - 26, y + 32], fill=SKY)
    # sea
    sea_y = y + h - 46
    draw.rectangle([x, sea_y, x + w, y + h], fill=SEA)
    for wx in range(0, w, 46):
        draw.line([x + wx, sea_y + 12, x + wx + 26, sea_y + 12], fill=SEA_DARK, width=2)
        draw.line([x + wx + 10, sea_y + 28, x + wx + 36, sea_y + 28], fill=SEA_DARK, width=2)
    # ship silhouette
    hx, hy = x + 150, sea_y - 6
    draw.polygon([(hx, hy), (hx + 300, hy), (hx + 272, hy + 26),
                  (hx + 28, hy + 26)], fill=(8, 12, 18))
    draw.rectangle([hx + 70, hy - 22, hx + 150, hy], fill=(8, 12, 18))
    draw.rectangle([hx + 180, hy - 14, hx + 230, hy], fill=(8, 12, 18))
    draw.line([hx + 250, hy - 34, hx + 250, hy], fill=(8, 12, 18), width=3)
    # lit portholes
    for px in range(hx + 40, hx + 280, 26):
        draw.ellipse([px, hy + 8, px + 5, hy + 13], fill=GOLD_LIGHT)
    # explosion starburst above the bow
    bx, by = hx + 285, hy - 26
    for dx, dy in [(0, -16), (11, -11), (16, 0), (11, 11), (0, 16),
                   (-11, 11), (-16, 0), (-11, -11)]:
        draw.line([bx, by, bx + dx, by + dy], fill=(255, 176, 32), width=3)
    draw.ellipse([bx - 9, by - 9, bx + 9, by + 9], fill=(255, 214, 90))
    # seven drones with trails
    for dx, dy in [(30, 26), (80, 14), (130, 30), (330, 12),
                   (390, 26), (450, 16), (510, 28)]:
        if dx < w - 20:
            draw.line([x + dx - 22, y + dy + 4, x + dx, y + dy + 4],
                      fill=(200, 210, 225), width=2)
            draw.ellipse([x + dx - 3, y + dy, x + dx + 3, y + dy + 6],
                         fill=(230, 235, 240))


def draw_tower_scene(draw, x, y, w, h):
    """Geometric night skyline: the PIF Tower, neighbours, blast at the top."""
    draw.rectangle([x, y, x + w, y + h], fill=SKY)
    for sx, sy in [(12, 8), (40, 18), (300, 10), (320, 22)]:
        draw.ellipse([x + sx, y + sy, x + sx + 3, y + sy + 3], fill=GOLD_LIGHT)
    # neighbour towers
    for tx, tw, th in [(8, 52, 52), (70, 44, 38), (252, 48, 44), (306, 34, 30)]:
        draw.rectangle([x + tx, y + h - th, x + tx + tw, y + h], fill=(30, 44, 66))
        for wy in range(y + h - th + 6, y + h - 4, 9):
            for wx in range(x + tx + 6, x + tx + tw - 5, 10):
                draw.rectangle([wx, wy, wx + 4, wy + 4], fill=(120, 130, 150))
    # the PIF Tower: tall, gold-edged, window grid
    tx, tw = x + 138, 68
    draw.rectangle([tx, y + 16, tx + tw, y + h], fill=(52, 68, 96))
    draw.rectangle([tx, y + 16, tx + tw, y + h], outline=GOLD, width=2)
    for wy in range(y + 24, y + h - 4, 10):
        for wx in range(tx + 8, tx + tw - 7, 11):
            draw.rectangle([wx, wy, wx + 5, wy + 5], fill=(214, 196, 120))
    # blast star at the tower crown
    bx, by = tx + tw // 2, y + 16
    for dx, dy in [(0, -14), (10, -10), (14, 0), (10, 10), (0, 14),
                   (-10, 10), (-14, 0), (-10, -10)]:
        draw.line([bx, by, bx + dx, by + dy], fill=(255, 176, 32), width=3)
    draw.ellipse([bx - 8, by - 8, bx + 8, by + 8], fill=(255, 214, 90))


def render():
    img = Image.new("RGB", (W, H), PAPER)
    draw = ImageDraw.Draw(img)
    n = story_count()

    # ---- Masthead ----
    draw.rectangle([0, 0, W, 106], fill=NAVY)
    draw.rectangle([0, 106, W, 110], fill=GOLD)
    title = "THE WORLD TODAY"
    tf = font("DejaVuSerif-Bold.ttf", 56)
    draw.text(((W - draw.textlength(title, font=tf)) / 2, 12),
              title, font=tf, fill=(250, 248, 240))
    sub = ("WEDNESDAY  25 NOVEMBER 2026    ·    %d STORIES FROM 7 REGIONS"
           "    ·    AS REPORTED BY 01:20 UTC" % n)
    sf = font("DejaVuSans-Bold.ttf", 14)
    draw.text(((W - draw.textlength(sub, font=sf)) / 2, 78),
              sub, font=sf, fill=GOLD_LIGHT)

    # ---- Lead story (left) ----
    lx, lw = 24, 616
    y = 124
    draw.text((lx, y), LEAD_KICKER, font=font("DejaVuSans-Bold.ttf", 13), fill=RED)
    y = 146
    y = draw_wrapped(draw, lx, y, LEAD_HEADLINE,
                     font("DejaVuSans-Bold.ttf", 34), lw, INK, line_h=40)
    y += 6
    y = draw_wrapped(draw, lx, y, LEAD_DECK,
                     font("DejaVuSans.ttf", 15), lw, (40, 40, 40), line_h=20)
    draw_lead_scene(draw, lx, 318, lw, 82)

    # ---- Riyadh story (right) ----
    rx, rw = 656, 344
    draw_tower_scene(draw, rx, 124, rw, 108)
    y = 242
    draw.text((rx, y), RIYADH_KICKER, font=font("DejaVuSans-Bold.ttf", 13), fill=RED)
    y = 264
    y = draw_wrapped(draw, rx, y, RIYADH_HEADLINE,
                     font("DejaVuSans-Bold.ttf", 21), rw, INK, line_h=25)
    y += 4
    draw_wrapped(draw, rx, y, RIYADH_DECK,
                 font("DejaVuSans.ttf", 13), rw, (40, 40, 40), line_h=17)

    # ---- Mini stories row ----
    my = 416
    draw.line([24, my, 1000, my], fill=RULE, width=2)
    col_w = 232
    for i, (kick, color, head, detail) in enumerate(MINIS):
        x = 24 + i * (col_w + 16)
        draw.text((x, my + 10), kick, font=font("DejaVuSans-Bold.ttf", 12), fill=color)
        y = draw_wrapped(draw, x, my + 30, head,
                         font("DejaVuSans-Bold.ttf", 15), col_w, INK, line_h=18)
        draw_wrapped(draw, x, y + 2, detail,
                     font("DejaVuSans.ttf", 12), col_w, (60, 60, 60), line_h=15)

    # ---- Region panels ----
    py = 524
    pw, ph = 314, 199
    for idx, (region, items) in enumerate(PANELS):
        col, row = idx % 3, idx // 3
        x = 24 + col * (pw + 16)
        yy = py + row * (ph + 12)
        color = REGION_COLORS[region]
        draw.rectangle([x, yy, x + pw, yy + 26], fill=color)
        draw.text((x + 8, yy + 5), region,
                  font=font("DejaVuSans-Bold.ttf", 14), fill=(255, 255, 255))
        draw.text((x + pw - 34, yy + 6), "%d" % len(items),
                  font=font("DejaVuSans-Bold.ttf", 13), fill=GOLD_LIGHT)
        iy = yy + 34
        for lead, rest in items:
            iy = draw_rich_item(draw, x + 6, iy, lead, rest, pw - 12,
                                size=12, line_h=14) + 3
        draw.rectangle([x, yy, x + pw, yy + ph - 1], outline=RULE, width=1)

    # ---- Sport & culture strip (one line) ----
    sy = 946
    draw.line([24, sy, 1000, sy], fill=RULE, width=2)
    draw.text((24, sy + 8), "   ·   ".join(SPORT),
              font=font("DejaVuSans.ttf", 11), fill=(40, 40, 40))

    # ---- Timeline (one line) ----
    ty = 972
    draw.line([24, ty, 1000, ty], fill=RULE, width=2)
    tx = 24
    for date, event in TIMELINE:
        label = "%s: %s" % (date, event)
        tw = draw.textlength(label, font=font("DejaVuSans.ttf", 11))
        draw.text((tx, ty + 8), label, font=font("DejaVuSans.ttf", 11),
                  fill=(60, 60, 60))
        tx += tw + 16

    # ---- Footer ----
    draw.text((24, 1002),
              "Sources: Reuters, AP, Al Jazeera, RFE/RL, BBC, AFP, Anadolu, PANA - every story checked against at least two reports.",
              font=font("DejaVuSans.ttf", 10), fill=GREY)
    return img


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    out = os.path.join(here, "news.png")
    img = render()
    img.save(out, format="PNG")
    data = open(out, "rb").read()
    print("wrote %s (%d bytes, sha256 %s, %d stories)"
          % (out, len(data), hashlib.sha256(data).hexdigest(), story_count()))


if __name__ == "__main__":
    main()
