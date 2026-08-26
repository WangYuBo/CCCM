#!/usr/bin/env python3
"""从 src.md（中文）与 tools/content_*.py（英/法/德）生成 CCCM 四语网站。

网站栏目与《理事会简介》目录一一对应：首页 + 七个栏目页。
中文页在根目录，英/法/德页面在 /en/ /fr/ /de/ 目录，页头一键切换语言。
内容严格取自 src.md；仅对个人联系方式等隐私信息做发布级脱敏。
在仓库根目录运行：python3 tools/build_site.py
"""
import re
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import content_zh
import content_en
import content_fr
import content_de

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = (ROOT / "src.md").read_text(encoding="utf-8")
BASE = "https://cccm.info"

SECTION_MAP = [
    ("overview", "一、组织概述"),
    ("mission", "二、成立宗旨"),
    ("activities", "三、标志性活动"),
    ("outreach", "四、长效传播工作"),
    ("evaluation", "五、行业评价体系建设"),
    ("summary", "六、总结"),
    ("chairman", "七、理事会现任主席焦顺发简介"),
]

# ---------------------------------------------------------------- 解析 src.md
raw = {}
cur, buf = None, []
for line in SRC.splitlines():
    m = re.match(r"^## (.+)$", line)
    if m:
        if cur is not None:
            raw[cur] = "\n".join(buf).strip()
        cur, buf = m.group(1), []
    elif cur is not None:
        buf.append(line)
if cur is not None:
    raw[cur] = "\n".join(buf).strip()

ZH_SECTIONS = {key: raw[zh] for key, zh in SECTION_MAP}
ZH_AFFILIATES = re.findall(r"^- (.+)$", raw["旗下机构"], re.M)

ZH_SIG = ""
tail = ZH_SECTIONS["chairman"]
m = re.search(r"\n国际中医养生大会理事会（CCCM）\n\n\d{4}年\d+月\d+日\s*$", tail)
if m:
    ZH_SIG = tail[m.start():].strip()
    ZH_SECTIONS["chairman"] = tail[: m.start()].strip()

# ---------------------------------------------------------------- 语言配置
# LANGS[lang] = {meta, content}; content 提供SECTIONS/AFFILIATES/SIG/NAV/UI/TOC_CARDS/PAGES_META
LANGS = {
    "zh": {
        "html_lang": "zh-CN", "prefix": "", "asset": "assets/", "link_prefix": "",
        "label": "中文", "short": "中文",
        "content": {
            "SECTIONS": ZH_SECTIONS, "AFFILIATES": ZH_AFFILIATES, "SIG": ZH_SIG,
            "NAV": content_zh.NAV, "UI": content_zh.UI,
            "TOC_CARDS": content_zh.TOC_CARDS, "PAGES_META": content_zh.PAGES_META,
        },
        "sections_redacted": True,
    },
    "en": {
        "html_lang": "en", "prefix": "en/", "asset": "../assets/", "link_prefix": "../",
        "label": "English", "short": "EN",
        "content": vars(content_en),
        "sections_redacted": False,
    },
    "fr": {
        "html_lang": "fr", "prefix": "fr/", "asset": "../assets/", "link_prefix": "../",
        "label": "Français", "short": "FR",
        "content": vars(content_fr),
        "sections_redacted": False,
    },
    "de": {
        "html_lang": "de", "prefix": "de/", "asset": "../assets/", "link_prefix": "../",
        "label": "Deutsch", "short": "DE",
        "content": vars(content_de),
        "sections_redacted": False,
    },
}
LANG_ORDER = ["zh", "en", "fr", "de"]

# ---------------------------------------------------------------- 隐私脱敏（仅网站发布，src.md 原文保留）
REDACT_DROP = [
    "ZOOM视频会议Meeting ID：464 565 7758 会议密码（Passcode）123",
    "请提前下载好Zoom软件，点击加入会议，输入会议Click：",
    "https://us02web.zoom.us/j/4645657758?pwd=",
    "手机：13910272918（微信）、778-987-3260（温哥华） 电邮：1065780000@qq.com",
]
REDACT_REPLACE = [
    ("只要添加组委会主任张辉个人微信号13910272918即可全程参会。",
     "由组委会主任统一邀请即可全程参会。"),
    ("有兴趣的中医药协会可以加张辉社长微信号13910272918和郑会长微信号jackzheng1960洽谈合作意向。",
     "有兴趣的中医药协会可与理事会洽谈合作意向。"),
]

def redact(md):
    out = [l for l in md.splitlines() if not any(d in l for d in REDACT_DROP)]
    md = "\n".join(out)
    for old, new in REDACT_REPLACE:
        md = md.replace(old, new)
    return md

# ---------------------------------------------------------------- Markdown -> HTML
def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def inline(t):
    t = esc(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(
        r'(https?://[^\s（）()【】《》<>"\']+)',
        r'<a href="\1" target="_blank" rel="noopener">\1</a>',
        t,
    )
    return t

def md_to_html(md):
    html, para, items = [], [], None
    ev = 0

    def flush_para():
        if para:
            html.append("<p>" + inline("".join(para)) + "</p>")
            para.clear()

    def flush_list():
        nonlocal items
        if items:
            html.append("<ul>" + "".join("<li>" + inline(i) + "</li>" for i in items) + "</ul>")
            items = None

    for raw_line in md.splitlines():
        s = raw_line.strip()
        if not s:
            flush_para(); flush_list(); continue
        if s.startswith("- "):
            flush_para()
            if items is None:
                items = []
            items.append(s[2:]); continue
        m = re.match(r"^### (.+)$", s)
        if m:
            flush_para(); flush_list()
            ev += 1
            html.append('<h2 class="ev-h" id="ev%d">%s</h2>' % (ev, inline(m.group(1))))
            continue
        m = re.match(r"^\*\*(.+)\*\*$", s)
        if m:
            flush_para(); flush_list()
            html.append("<h3>%s</h3>" % inline(m.group(1)))
            continue
        flush_list()
        para.append(s)
    flush_para(); flush_list()
    return "\n".join(html)

# ---------------------------------------------------------------- 公共模板
SEAL = ('<svg viewBox="0 0 96 96"><rect x="5" y="5" width="86" height="86" rx="8" fill="#A8432F"/>'
        '<rect x="12" y="12" width="72" height="72" rx="4" fill="none" stroke="#F6F4EC" stroke-width="3" opacity="0.9"/>'
        '<text x="48" y="41" text-anchor="middle" font-family="Georgia,\'Times New Roman\',serif" font-size="27" font-weight="700" fill="#F6F4EC" letter-spacing="1">CC</text>'
        '<line x1="22" y1="50" x2="74" y2="50" stroke="#F6F4EC" stroke-width="2" opacity="0.85"/>'
        '<text x="48" y="75" text-anchor="middle" font-family="Georgia,\'Times New Roman\',serif" font-size="27" font-weight="700" fill="#F6F4EC" letter-spacing="1">CM</text></svg>')

PAGES = ["index.html", "overview.html", "mission.html", "activities.html",
         "outreach.html", "evaluation.html", "summary.html", "chairman.html"]

def lang_href(current_lang, target_lang, filename):
    if target_lang == current_lang:
        prefix = ""
    elif current_lang == "zh":
        prefix = LANGS[target_lang]["prefix"]
    else:
        prefix = "../" + LANGS[target_lang]["prefix"]
    return prefix + filename

def hreflang(filename):
    links = ""
    for lang in LANG_ORDER:
        url = BASE + "/" + LANGS[lang]["prefix"] + filename
        links += '<link rel="alternate" hreflang="%s" href="%s">\n' % (lang, url)
    links += '<link rel="alternate" hreflang="x-default" href="%s/%s">\n' % (BASE, filename)
    return links

def header(L, lang, current):
    C = L["content"]
    links = "".join(
        '<a href="%s"%s>%s</a>' % (h, ' aria-current="page"' if h == current else "", t)
        for h, t in C["NAV"]
    )
    menu = ""
    for target in LANG_ORDER:
        href = lang_href(lang, target, current)
        cur = ' class="cur" aria-current="true"' if target == lang else ""
        menu += '<li><a lang="%s" href="%s"%s>%s</a></li>\n' % (target, href, cur, LANGS[target]["label"])
    return ('<header class="site-header">\n  <div class="header-inner">\n'
            '    <a class="brand" href="%sindex.html" aria-label="home">\n'
            '      <span class="seal" aria-hidden="true">' % L["link_prefix"] + SEAL + '</span>\n'
            '      <span>\n        <span class="brand-name">' + C["UI"]["brand_name"] + '</span>\n'
            '        <span class="brand-sub">' + C["UI"]["brand_sub"] + '</span>\n      </span>\n'
            '    </a>\n'
            '    <button class="nav-toggle" aria-expanded="false" aria-label="menu">☰</button>\n'
            '    <nav class="nav" aria-label="primary">' + links + "</nav>\n"
            '    <div class="lang-switch">\n'
            '      <button class="lang-btn" type="button" aria-expanded="false" aria-haspopup="true" aria-label="%s">🌐 %s</button>\n'
            '      <ul class="lang-menu" aria-label="languages">\n%s      </ul>\n'
            '    </div>\n'
            "  </div>\n</header>") % (C["UI"]["lang_menu"], L["short"], menu)

def footer(L):
    C = L["content"]
    links = "".join('<a href="%s">%s</a>' % (h, t) for h, t in C["NAV"])
    return ('<footer class="site-footer">\n  <div class="footer-inner">\n'
            '    <div class="footer-top">\n      <div class="footer-brand">\n'
            '        <span class="seal" aria-hidden="true">' + SEAL + '</span>\n'
            '        <div>\n          <div class="brand-name">' + C["UI"]["brand_name"] + '</div>\n'
            '          <div class="brand-sub">' + C["UI"]["brand_sub"] + '</div>\n        </div>\n      </div>\n'
            '      <div class="footer-meta">\n        Corporation No. 1056656-0<br>\n'
            '        Business No. 777456682RC0001<br>\n'
            '        1555 22nd Street, West Vancouver, BC, Canada\n      </div>\n    </div>\n'
            '    <nav class="footer-nav" aria-label="footer">' + links + '</nav>\n'
            '    <div class="footer-bottom">\n'
            '      <span>© <span data-year>2026</span> International Council of Conference on Health-Care with Chinese Medicine · ' + C["UI"]["rights"] + '</span>\n'
            '      <span>' + C["UI"]["footer_tag"] + '</span>\n    </div>\n  </div>\n</footer>')

def page(L, lang, filename, title, desc, eyebrow, h1, lead, body):
    url = BASE + "/" + L["prefix"] + filename
    return f"""<!DOCTYPE html>
<html lang="{L['html_lang']}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{url}">
{hreflang(filename)}<link rel="icon" type="image/svg+xml" href="{L['asset']}img/favicon.svg">
<link rel="stylesheet" href="{L['asset']}css/style.css">
<script>document.documentElement.classList.add("js");</script>
</head>
<body>
{header(L, lang, filename)}

<main>
  <section class="page-hero">
    <div class="page-hero-inner">
      <div class="eyebrow">{esc(eyebrow)}</div>
      <h1>{esc(h1)}</h1>
      <p class="lead">{esc(lead)}</p>
    </div>
  </section>

{body}
</main>

{footer(L)}

<script src="{L['asset']}js/main.js"></script>
</body>
</html>
"""

def identity_section(L):
    ui = L["content"]["UI"]
    return ('  <section class="section">\n    <div class="container">\n'
            '      <div class="section-head">\n        <span class="section-no">REGISTRATION</span>\n'
            '        <h2>%s</h2>\n      </div>\n' % ui["reg_h2"]
            + '      <div class="identity reveal">\n'
            '        <div class="stamp" aria-hidden="true">' + SEAL + '</div>\n'
            '        <div class="identity-head">\n'
            '          <h3>' + ui["identity_head"] + '</h3>\n'
            '          <span class="identity-tag">STATUS: ACTIVE</span>\n        </div>\n'
            '        <div class="identity-grid">\n'
            '          <div class="identity-item"><div class="k">CORPORATION NUMBER</div><div class="v">1056656-0</div></div>\n'
            '          <div class="identity-item"><div class="k">BUSINESS NUMBER</div><div class="v">777456682RC0001</div></div>\n'
            '          <div class="identity-item"><div class="k">FILING DATE</div><div class="v">2018-01-04</div></div>\n'
            '          <div class="identity-item"><div class="k">' + ui["k_reg"] + '</div><div class="v">British Columbia, Canada</div></div>\n'
            '          <div class="identity-item"><div class="k">' + ui["k_addr"] + '</div><div class="v">1555 22nd Street, West Vancouver, BC, Canada V7V 4E1</div></div>\n'
            '        </div>\n'
            '        <div class="identity-verify">' + ui["verify"] + '</div>\n'
            '      </div>\n    </div>\n  </section>\n')

def chips_section(L):
    lis = "".join("        <li>%s</li>\n" % esc(i) for i in L["content"]["AFFILIATES"])
    return ('  <section class="section">\n    <div class="container">\n'
            '      <div class="section-head">\n        <span class="section-no">NETWORK</span>\n'
            '        <h2>%s</h2>\n      </div>\n' % L["content"]["UI"]["aff_h2"]
            + '      <ul class="chips reveal">\n' + lis + '      </ul>\n    </div>\n  </section>\n')


# ---------------------------------------------------------------- 活动配图
EVENT_IMAGES = {
    1: [("01-首届国际中医药养生大会在加拿大温哥华举行-人民日报海外版.jpg", False)],
    2: [("（二）2018中医药国际论坛（安徽·合肥）.jpeg", False)],
    3: [("（三）2018中医药康养论坛（山西右玉）.jpg", False)],
    4: [("2019年首届海外国医论坛-长沙开幕.webp", False)],
    6: [("（六）2021国医名家论坛（湖南·长沙）.png", False)],
    7: [("（七）第四届海外国医论坛（金观源教授专场云会）嘉宾邀请函.jpg", True)],
    8: [("（八）首届海外国医名家论坛（加拿大·温哥华）.jpg", False)],
    9: [("“第二届国际中医养生大会”暨“2024世界头针年会”.jpg", False)],
    10: [("第二届国医名家研讨会在海南举行 海内外专家共商中医药现代化.png", False)],
}
EVENT_IMG_CAPTIONS = {
    "01-首届国际中医药养生大会在加拿大温哥华举行-人民日报海外版.jpg": {
        "zh": "首届国际中医药养生大会在加拿大温哥华举行（图源：人民日报海外版）",
        "en": "The First International TCM Wellness Conference in Vancouver, Canada (photo: People's Daily Overseas Edition)",
        "fr": "Premier Congrès international de bien-être de la médecine chinoise à Vancouver, Canada (photo : Édition outre-mer du Quotidien du Peuple)",
        "de": "Der Erste Internationale Kongress für TCM-Gesundheitspflege in Vancouver, Kanada (Foto: People's Daily Overseas Edition)",
    },
    "2019年首届海外国医论坛-长沙开幕.webp": {
        "zh": "2019年首届海外国医论坛在长沙开幕",
        "en": "The 2019 First Overseas TCM Forum opens in Changsha",
        "fr": "Ouverture à Changsha du Premier Forum de la médecine chinoise d'outre-mer 2019",
        "de": "Eröffnung des Ersten Forums der Chinesischen Medizin im Ausland 2019 in Changsha",
    },
    "（二）2018中医药国际论坛（安徽·合肥）.jpeg": {
        "zh": "2018中医药国际论坛（安徽·合肥）",
        "en": "The 2018 International TCM Forum, Anhui · Hefei",
        "fr": "Forum international de médecine chinoise 2018, Anhui · Hefei",
        "de": "2018 Internationales TCM-Forum, Anhui · Hefei",
    },
    "（三）2018中医药康养论坛（山西右玉）.jpg": {
        "zh": "2018中医药康养论坛（山西·右玉）",
        "en": "The 2018 TCM Health and Wellness Forum, Shanxi · Youyu",
        "fr": "Forum 2018 de santé et de bien-être du TCM, Shanxi · Youyu",
        "de": "2018 TCM-Gesundheits- und Wellness-Forum, Shanxi · Youyu",
    },
    "（六）2021国医名家论坛（湖南·长沙）.png": {
        "zh": "2021国医名家论坛（湖南·长沙）",
        "en": "The 2021 National Masters TCM Forum, Hunan · Changsha",
        "fr": "Forum des maîtres nationaux du TCM 2021, Hunan · Changsha",
        "de": "Nationales TCM-Meisterforum 2021, Hunan · Changsha",
    },
    "（七）第四届海外国医论坛（金观源教授专场云会）嘉宾邀请函.jpg": {
        "zh": "第四届海外国医论坛（金观源教授专场云会）嘉宾邀请函",
        "en": "Invitation to the 4th Overseas TCM Forum - Prof. Jin Guanyuan's special online session",
        "fr": "Invitation au 4e Forum de la médecine chinoise d'outre-mer - session spéciale en ligne du Pr Jin Guanyuan",
        "de": "Einladung zum 4. Forum der Chinesischen Medizin im Ausland - Online-Sondersitzung von Prof. Jin Guanyuan",
    },
    "（八）首届海外国医名家论坛（加拿大·温哥华）.jpg": {
        "zh": "首届海外国医名家论坛（加拿大·温哥华）",
        "en": "The First Overseas TCM Masters Forum, Vancouver, Canada",
        "fr": "Premier Forum des maîtres du TCM d'outre-mer, Vancouver, Canada",
        "de": "Erstes Übersee-TCM-Meisterforum, Vancouver, Kanada",
    },
    "“第二届国际中医养生大会”暨“2024世界头针年会”.jpg": {
        "zh": "“第二届国际中医养生大会”暨“2024世界头针年会”（海南）",
        "en": "The 2nd International TCM Wellness Conference & The 2024 World Scalp-Acupuncture Annual Meeting, Hainan",
        "fr": "2e Conférence internationale de bien-être du TCM et Assemblée annuelle mondiale 2024 de l'acupuncture du scalp, Hainan",
        "de": "2. Internationale TCM-Wellness-Konferenz und Weltjahrestagung 2024 für Skalp-Akupunktur, Hainan",
    },
    "第二届国医名家研讨会在海南举行 海内外专家共商中医药现代化.png": {
        "zh": "第二届国医名家研讨会在海南举行，海内外专家共商中医药现代化",
        "en": "The 2nd National Masters Symposium held in Hainan - experts at home and abroad discuss the modernization of TCM",
        "fr": "2e Symposium des maîtres nationaux du TCM tenu à Hainan - experts d'ici et d'ailleurs discutent de la modernisation du TCM",
        "de": "2. Nationales TCM-Meistersymposium in Hainan - in- und ausländische Experten erörtern die Modernisierung der TCM",
    },
}

def event_figures(L, lang):
    out = {}
    for ev, imgs in EVENT_IMAGES.items():
        figs = ""
        for fname, portrait in imgs:
            cap = EVENT_IMG_CAPTIONS[fname][lang]
            cls = "ev-fig ev-fig--portrait" if portrait else "ev-fig"
            figs += ('        <figure class="%s"><img src="%s" alt="%s" loading="lazy">'
                     '<figcaption>%s</figcaption></figure>\n'
                     % (cls, esc(L["asset"] + "img/" + fname), esc(cap), esc(cap)))
        out[ev] = figs
    return out

def prose(L, no, h2, md, extra=""):
    if L["sections_redacted"]:
        md = redact(md)
    return ('  <section class="section">\n    <div class="container">\n'
            '      <div class="section-head">\n        <span class="section-no">%s</span>\n        <h2>%s</h2>\n      </div>\n%s'
            '      <div class="prose reveal">\n%s\n      </div>\n    </div>\n  </section>\n'
            % (no, h2, extra, md_to_html(md)))

# ---------------------------------------------------------------- 生成
for lang in LANG_ORDER:
    L = LANGS[lang]
    C = L["content"]
    outdir = ROOT / L["prefix"]
    outdir.mkdir(parents=True, exist_ok=True)

    for key in ["overview", "mission", "activities", "outreach", "evaluation", "summary", "chairman"]:
        title, desc, eyebrow, h1, lead = C["PAGES_META"][key]
        md = C["SECTIONS"][key]
        extra = ""
        if key == "activities":
            evs = re.findall(r"^### (.+)$", md, re.M)
            extra = ('      <nav class="ev-toc reveal" aria-label="event index">\n'
                     '        <span class="ev-toc-t">%s</span>\n        <ol>\n' % C["UI"]["ev_toc_t"]
                     + "".join('          <li><a href="#ev%d">%s</a></li>\n' % (i + 1, esc(t)) for i, t in enumerate(evs))
                     + "        </ol>\n      </nav>\n")
        body = prose(L, key.upper(), h1, md, extra=extra)
        if key == "activities":
            figs = event_figures(L, lang)
            for ev, fig_html in figs.items():
                pat = re.compile(r'(<h2 class="ev-h" id="ev%d">.*?</h2>)' % ev, re.S)
                body = pat.sub(lambda m: m.group(1) + "\n" + fig_html, body, count=1)
        if key == "overview":
            body += identity_section(L) + chips_section(L)
        if key == "chairman" and C["SIG"]:
            sig_html = '\n      <div class="sig">%s</div>\n' % esc(C["SIG"]).replace("\n", "<br>")
            body = body.replace("      </div>\n    </div>\n  </section>\n",
                                sig_html + "      </div>\n    </div>\n  </section>\n", 1)
        (outdir / (key + ".html")).write_text(
            page(L, lang, key + ".html", title, desc, eyebrow, h1, lead, body), encoding="utf-8")
        print("wrote", L["prefix"] + key + ".html")

    # 首页
    cards = "".join(
        ('        <article class="card reveal">\n'
         '          <span class="toc-no">%s</span>\n'
         '          <h3><a href="%s">%s</a></h3>\n'
         '          <p class="desc">%s</p>\n'
         '          <a class="more" href="%s">%s -&gt;</a>\n'
         '        </article>\n') % (no, href, t, d, href, C["UI"]["read"])
        for no, t, href, d in C["TOC_CARDS"]
    )
    ui = C["UI"]
    index_html = f"""<!DOCTYPE html>
<html lang="{L['html_lang']}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(ui['index_title'])}</title>
<meta name="description" content="{esc(ui['index_desc'])}">
<link rel="canonical" href="{BASE}/{L['prefix']}">
{hreflang('index.html')}<link rel="icon" type="image/svg+xml" href="{L['asset']}img/favicon.svg">
<link rel="stylesheet" href="{L['asset']}css/style.css">
<script>document.documentElement.classList.add("js");</script>
</head>
<body>
{header(L, lang, "index.html")}

<main>
  <!-- Hero -->
  <section class="hero">
    <div class="hero-inner">
      <div class="hero-seal" aria-hidden="true">{SEAL}</div>
      <div>
        <h1 class="hero-title">{esc(ui['hero_h1'])}
          <span class="en">{esc(ui['hero_h1_sub'])}</span>
        </h1>
        <p class="hero-lead">{esc(ui['hero_lead'])}</p>
        <div class="hero-actions">
          <a class="btn btn--solid" href="{L['link_prefix']}overview.html">{esc(ui['btn1'])}</a>
          <a class="btn" href="{L['link_prefix']}activities.html">{esc(ui['btn2'])}</a>
        </div>
      </div>
    </div>
    <div class="hero-vtext" aria-hidden="true">{esc(ui['hero_vtext'])}</div>
  </section>

  <!-- Contents（与《理事会简介》目录一一对应） -->
  <section class="section">
    <div class="container">
      <div class="section-head">
        <span class="section-no">CONTENTS</span>
        <h2>{esc(ui['contents'])}</h2>
      </div>
      <div class="grid toc-grid">
{cards}      </div>
    </div>
  </section>
</main>

{footer(L)}

<script src="{L['asset']}js/main.js"></script>
</body>
</html>
"""
    (outdir / "index.html").write_text(index_html, encoding="utf-8")
    print("wrote", L["prefix"] + "index.html")

# 404（多语言入口）
L = LANGS["zh"]
html_404 = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>页面未找到 | Page Not Found | 国际中医养生大会理事会（CCCM）</title>
<meta name="robots" content="noindex">
<link rel="icon" type="image/svg+xml" href="assets/img/favicon.svg">
<link rel="stylesheet" href="assets/css/style.css">
<script>document.documentElement.classList.add("js");</script>
</head>
<body>
{header(L, "zh", "index.html")}

<main>
  <section class="section">
    <div class="container" style="max-width:620px; text-align:center;">
      <div class="eyebrow" style="justify-content:center;">404</div>
      <h1 style="font-size:34px;">页面未找到 / Page Not Found</h1>
      <p style="color:var(--ink-soft); margin-top:14px;">您访问的页面不存在或已移动。<br>The page you requested does not exist or has moved.</p>
      <p style="margin-top:24px;">
        <a class="btn btn--solid" href="index.html">返回首页</a>
        <a class="btn" href="en/index.html">English</a>
        <a class="btn" href="fr/index.html">Français</a>
        <a class="btn" href="de/index.html">Deutsch</a>
      </p>
    </div>
  </section>
</main>

{footer(L)}

<script src="assets/js/main.js"></script>
</body>
</html>
"""
(ROOT / "404.html").write_text(html_404, encoding="utf-8")
print("wrote 404.html")

