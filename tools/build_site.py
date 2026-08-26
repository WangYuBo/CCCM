#!/usr/bin/env python3
"""从 src.md（中文）与 tools/content_en.py（英文）生成 CCCM 双语网站。

网站栏目与《理事会简介》目录一一对应：首页 + 七个栏目页。
中文页在根目录，英文页在 /en/ 目录，页头一键切换语言。
内容严格取自 src.md；仅对个人联系方式等隐私信息做发布级脱敏。
在仓库根目录运行：python3 tools/build_site.py
"""
import re
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import content_en

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

ZH = {key: raw[zh] for key, zh in SECTION_MAP}
ZH_AFFILIATES = re.findall(r"^- (.+)$", raw["旗下机构"], re.M)

ZH_SIG = ""
tail = ZH["chairman"]
m = re.search(r"\n国际中医养生大会理事会（CCCM）\n\n\d{4}年\d+月\d+日\s*$", tail)
if m:
    ZH_SIG = tail[m.start():].strip()
    ZH["chairman"] = tail[: m.start()].strip()

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

# ---------------------------------------------------------------- 语言配置
LANGS = {}

LANGS["zh"] = {
    "html_lang": "zh-CN",
    "prefix": "",            # 输出目录前缀（根目录）
    "asset": "assets/",
    "link_prefix": "",       # 站内链接前缀
    "other_prefix": "en/",   # 另一语言页面前缀
    "toggle_label": "EN",
    "nav": [("index.html", "首页"), ("overview.html", "组织概述"), ("mission.html", "成立宗旨"),
            ("activities.html", "标志性活动"), ("outreach.html", "长效传播"),
            ("evaluation.html", "行业评价"), ("summary.html", "总结"), ("chairman.html", "主席简介")],
    "ui": {
        "contents": "章节目录",
        "read": "阅读",
        "reg_h2": "注册与身份",
        "identity_head": "加拿大联邦政府注册 · 非政府 / 非宗教 / 非盈利组织",
        "k_reg": "注册地", "k_addr": "地址",
        "verify": "以上信息可在加拿大联邦政府公司注册登记处（Corporations Canada）在线核验。",
        "aff_h2": "旗下机构",
        "rights": "保留所有权利",
        "footer_tag": "加拿大联邦政府注册非盈利组织",
        "ev_toc_t": "十场标志性活动",
        "index_title": "国际中医养生大会理事会（CCCM）| 中医药国际交流平台",
        "index_desc": "国际中医养生大会理事会（CCCM）是2018年在加拿大联邦政府注册的非政府、非宗教、非盈利组织，搭建跨国界、跨文化的中医药交流平台，主办国医名家论坛、海外国医论坛等标志性活动。",
        "hero_lead": "依托北美华人中医药专业力量，搭建跨国界、跨文化的中医药交流平台--面向全球推动中医养生文化传播、国际中医药AI创新研究、中医针灸学术交流与健康公益服务。",
        "hero_h1": "国际中医养生大会理事会",
        "hero_h1_sub": "INTERNATIONAL COUNCIL OF CONFERENCE ON HEALTH-CARE WITH CHINESE MEDICINE",
        "hero_vtext": "国际中医养生大会理事会 · 二〇一八",
        "btn1": "了解我们", "btn2": "标志性活动",
    },
    "toc_cards": [
        ("一", "组织概述", "overview.html", "加拿大注册的国际公益性行业组织，中医药在欧美传播与发展的核心民间载体。"),
        ("二", "成立宗旨", "mission.html", "扎根“传承、创新、济世”核心理念，五大宗旨与国际中医药AI创新中心。"),
        ("三", "标志性活动", "activities.html", "2017–2025年十场标志性活动全记录，含各家媒体报道原文。"),
        ("四", "长效传播工作", "outreach.html", "病案出版、专业刊物与海外社区公益养生的常态化传播。"),
        ("五", "行业评价体系建设", "evaluation.html", "海外国医大师、名家评审委员会与两届入选名单。"),
        ("六", "总结", "summary.html", "理事会多年工作的回顾与总结。"),
        ("七", "主席简介", "chairman.html", "理事会现任主席焦顺发--“焦氏头针”的创始人和奠基者。"),
    ],
    "sections": ZH,
    "sections_redacted": True,
    "affiliates": ZH_AFFILIATES,
    "sig": ZH_SIG,
    "pages": {
        "overview": ("组织概述 | 国际中医养生大会理事会（CCCM）",
                     "国际中医养生大会理事会（CCCM）组织概述：2018年在加拿大联邦政府注册的国际公益性行业组织，中医药在欧美地区传播与发展的核心民间载体。",
                     "CCCM 简介 · 第一部分", "组织概述",
                     "一个真实、可核验的加拿大注册非盈利中医组织，一个跨国界、跨文化的中医药交流平台。"),
        "mission": ("成立宗旨 | 国际中医养生大会理事会（CCCM）",
                    "理事会成立宗旨：扎根“传承、创新、济世”三大核心理念，五大宗旨与国际中医药AI创新中心。",
                    "CCCM 简介 · 第二部分", "成立宗旨",
                    "理事会的成立宗旨，深深扎根于“传承、创新、济世”三大核心理念。"),
        "activities": ("标志性活动 | 国际中医养生大会理事会（CCCM）",
                       "2017–2025年理事会十场标志性活动全记录：国际中医养生大会、国医名家论坛、海外国医论坛、世界头针年会等。",
                       "CCCM 简介 · 第三部分", "标志性活动",
                       "从2017年温哥华首届国际中医养生大会，到2025年海口第二届国医名家研讨会--十场标志性活动全记录。"),
        "outreach": ("长效传播工作 | 国际中医养生大会理事会（CCCM）",
                     "理事会长效传播工作：海外中医临床病案整理出版、《海外国医》刊物编辑与海外社区公益养生推广。",
                     "CCCM 简介 · 第四部分", "长效传播工作",
                     "记录海外中医发展史料，让养生文化走进海外社区。"),
        "evaluation": ("行业评价体系建设 | 国际中医养生大会理事会（CCCM）",
                       "海外国医大师、名家评审委员会与行业评价体系建设：填补海外中医行业评价体系空白。",
                       "CCCM 简介 · 第五部分", "行业评价体系建设",
                       "填补海外中医行业评价体系的空白，为海外中医师提供坚实的执业后盾。"),
        "summary": ("总结 | 国际中医养生大会理事会（CCCM）",
                    "国际中医养生大会理事会工作总结：不以商业盈利为首要目标，为中加中医药文化交流与海外华人医疗公益事业发挥积极作用。",
                    "CCCM 简介 · 第六部分", "总结",
                    "不以商业盈利为首要目标，助力中医药融入全球健康治理。"),
        "chairman": ("主席简介 | 国际中医养生大会理事会（CCCM）",
                     "理事会现任主席焦顺发简介：“焦氏头针”创始人和奠基者，头针研究的从医历程与临床成果。",
                     "CCCM 简介 · 第七部分", "理事会现任主席焦顺发简介",
                     "“焦氏头针”的创始人和奠基者，理事会现任主席。"),
    },
}

LANGS["en"] = {
    "html_lang": "en",
    "prefix": "en/",
    "asset": "../assets/",
    "link_prefix": "../",
    "other_prefix": "../",
    "toggle_label": "中文",
    "nav": [("index.html", "Home"), ("overview.html", "Overview"), ("mission.html", "Mission"),
            ("activities.html", "Signature Events"), ("outreach.html", "Outreach"),
            ("evaluation.html", "Evaluation"), ("summary.html", "Conclusion"), ("chairman.html", "Chairman")],
    "ui": {
        "contents": "Contents",
        "read": "Read",
        "reg_h2": "Registration & Identity",
        "identity_head": "Registered with the Government of Canada · Non-governmental / Non-religious / Non-profit",
        "k_reg": "Registered In", "k_addr": "Address",
        "verify": "The above information can be verified online at Corporations Canada, the federal corporate registry.",
        "aff_h2": "Affiliated Institutions",
        "rights": "All rights reserved",
        "footer_tag": "A federally registered non-profit organization in Canada",
        "ev_toc_t": "The Ten Signature Events",
        "index_title": "International Council of Conference on Health-Care with Chinese Medicine (CCCM)",
        "index_desc": "The International Council of Conference on Health-Care with Chinese Medicine (CCCM) is a non-governmental, non-religious, non-profit organization registered with the Government of Canada in 2018, building a transnational, cross-cultural platform for Chinese medicine and hosting signature events such as the National Masters Forum and the Overseas Chinese Medicine Forum.",
        "hero_lead": "Drawing on the professional strength of North America's Chinese-medicine community, we build a transnational, cross-cultural platform for Chinese medicine--promoting wellness culture, TCM-AI innovation research, academic exchange in acupuncture, and public-health services worldwide.",
        "hero_h1": "International Council of Conference on Health-Care with Chinese Medicine",
        "hero_h1_sub": "国际中医养生大会理事会",
        "hero_vtext": "CCCM · EST. 2018",
        "btn1": "About Us", "btn2": "Signature Events",
    },
    "toc_cards": [
        ("1", "Overview", "overview.html", "A Canadian-registered, non-profit international TCM organization--a core civil-society vehicle for Chinese medicine in Europe and North America."),
        ("2", "Mission", "mission.html", "Inheritance, Innovation, and Service to the World: five mission pillars and the International TCM AI Innovation Center."),
        ("3", "Signature Events", "activities.html", "The complete record of ten signature events, 2017-2025."),
        ("4", "Ongoing Outreach", "outreach.html", "Case publications, professional journals, and community wellness programs."),
        ("5", "Industry Evaluation", "evaluation.html", "The Overseas Masters and Notables Evaluation Committee and its two selection rounds."),
        ("6", "Conclusion", "summary.html", "A retrospective on the Council's work over the years."),
        ("7", "Chairman", "chairman.html", "Jiao Shunfa, Chairman of the Council--founder and pioneer of scalp acupuncture."),
    ],
    "sections": content_en.SECTIONS,
    "sections_redacted": False,
    "affiliates": content_en.AFFILIATES,
    "sig": content_en.SIG,
    "pages": {
        "overview": ("Overview | CCCM",
                     "Overview of the International Council of Conference on Health-Care with Chinese Medicine (CCCM): an international non-profit TCM organization registered with the Government of Canada in 2018.",
                     "CCCM Profile · Part One", "Overview",
                     "A real, verifiable Canadian-registered non-profit TCM organization; a transnational, cross-cultural platform for Chinese medicine."),
        "mission": ("Mission | CCCM",
                    "The mission of the CCCM: rooted in the three core concepts of Inheritance, Innovation, and Service to the World; five mission pillars and the International TCM AI Innovation Center.",
                    "CCCM Profile · Part Two", "Mission",
                    "The Council's mission is deeply rooted in the three core concepts of Inheritance, Innovation, and Service to the World."),
        "activities": ("Signature Events | CCCM",
                       "The complete record of the CCCM's ten signature events, 2017-2025: international TCM wellness conferences, the National Masters Forum, the Overseas Chinese Medicine Forum, and the World Scalp Acupuncture Congress.",
                       "CCCM Profile · Part Three", "Signature Events",
                       "From the first conference in Vancouver, 2017, to the Second National Masters Symposium in Haikou, 2025--English summaries of all ten signature events, with the full Chinese reports linked."),
        "outreach": ("Ongoing Outreach | CCCM",
                     "The CCCM's ongoing outreach: publishing overseas TCM clinical cases, editing the journal Overseas Chinese Medicine, and community wellness programs.",
                     "CCCM Profile · Part Four", "Ongoing Outreach",
                     "Documenting the history of overseas Chinese medicine; bringing wellness culture into overseas communities."),
        "evaluation": ("Industry Evaluation System | CCCM",
                       "The Overseas Masters and Notables of Chinese Medicine Evaluation Committee: filling the gap in the overseas TCM evaluation system.",
                       "CCCM Profile · Part Five", "Industry Evaluation System",
                       "Filling the gap in the overseas TCM evaluation system--a solid professional backbone for overseas practitioners."),
        "summary": ("Conclusion | CCCM",
                    "The work of the CCCM in review: never placing commercial profit first, and helping Chinese medicine enter global health governance.",
                    "CCCM Profile · Part Six", "Conclusion",
                    "Never placing commercial profit first; helping Chinese medicine enter global health governance."),
        "chairman": ("The Chairman: Jiao Shunfa | CCCM",
                     "A profile of Jiao Shunfa, Chairman of the CCCM: founder and pioneer of scalp acupuncture, his medical journey and clinical achievements.",
                     "CCCM Profile · Part Seven", "The Chairman: Jiao Shunfa",
                     "Founder and pioneer of scalp acupuncture; Chairman of the Council."),
    },
}

# ---------------------------------------------------------------- 页面组装
def hreflang(file, lang_code):
    zh_url = BASE + "/" + file
    en_url = BASE + "/en/" + file
    return ('<link rel="alternate" hreflang="zh" href="%s">\n'
            '<link rel="alternate" hreflang="en" href="%s">\n'
            '<link rel="alternate" hreflang="x-default" href="%s">\n') % (zh_url, en_url, zh_url)

def header(L, current):
    links = "".join(
        '<a href="%s"%s>%s</a>' % (h, ' aria-current="page"' if h == current else "", t)
        for h, t in L["nav"]
    )
    toggle_href = L["other_prefix"] + current
    return ('<header class="site-header">\n  <div class="header-inner">\n'
            '    <a class="brand" href="%sindex.html" aria-label="home">\n'
            '      <span class="seal" aria-hidden="true">' % L["link_prefix"] + SEAL + '</span>\n'
            '      <span>\n        <span class="brand-name">国际中医养生大会理事会</span>\n'
            '        <span class="brand-sub">传承 · 创新 · 济世</span>\n      </span>\n'
            '    </a>\n'
            '    <button class="nav-toggle" aria-expanded="false" aria-label="menu">☰</button>\n'
            '    <nav class="nav" aria-label="primary">' + links + "</nav>\n"
            '    <a class="lang-btn" href="%s" aria-label="language">%s</a>\n'
            "  </div>\n</header>") % (toggle_href, L["toggle_label"])

def footer(L):
    links = "".join('<a href="%s">%s</a>' % (h, t) for h, t in L["nav"])
    return ('<footer class="site-footer">\n  <div class="footer-inner">\n'
            '    <div class="footer-top">\n      <div class="footer-brand">\n'
            '        <span class="seal" aria-hidden="true">' + SEAL + '</span>\n'
            '        <div>\n          <div class="brand-name">国际中医养生大会理事会</div>\n'
            '          <div class="brand-sub">传承 · 创新 · 济世</div>\n        </div>\n      </div>\n'
            '      <div class="footer-meta">\n        Corporation No. 1056656-0<br>\n'
            '        Business No. 777456682RC0001<br>\n'
            '        1555 22nd Street, West Vancouver, BC, Canada\n      </div>\n    </div>\n'
            '    <nav class="footer-nav" aria-label="footer">' + links + "</nav>\n"
            '    <div class="footer-bottom">\n'
            '      <span>© <span data-year>2026</span> International Council of Conference on Health-Care with Chinese Medicine · ' + L["ui"]["rights"] + '</span>\n'
            '      <span>' + L["ui"]["footer_tag"] + '</span>\n    </div>\n  </div>\n</footer>')

def page(L, filename, title, desc, eyebrow, h1, lead, body):
    url = BASE + "/" + L["prefix"] + filename
    return f"""<!DOCTYPE html>
<html lang="{L['html_lang']}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{url}">
{hreflang(filename, L['html_lang'])}<link rel="icon" type="image/svg+xml" href="{L['asset']}img/favicon.svg">
<link rel="stylesheet" href="{L['asset']}css/style.css">
<script>document.documentElement.classList.add("js");</script>
</head>
<body>
{header(L, filename)}

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
    return ('  <section class="section">\n    <div class="container">\n'
            '      <div class="section-head">\n        <span class="section-no">REGISTRATION</span>\n'
            '        <h2>%s</h2>\n      </div>\n' % L["ui"]["reg_h2"]
            + '      <div class="identity reveal">\n'
            '        <div class="stamp" aria-hidden="true">' + SEAL + '</div>\n'
            '        <div class="identity-head">\n'
            '          <h3>' + L["ui"]["identity_head"] + '</h3>\n'
            '          <span class="identity-tag">STATUS: ACTIVE</span>\n        </div>\n'
            '        <div class="identity-grid">\n'
            '          <div class="identity-item"><div class="k">CORPORATION NUMBER</div><div class="v">1056656-0</div></div>\n'
            '          <div class="identity-item"><div class="k">BUSINESS NUMBER</div><div class="v">777456682RC0001</div></div>\n'
            '          <div class="identity-item"><div class="k">FILING DATE</div><div class="v">2018-01-04</div></div>\n'
            '          <div class="identity-item"><div class="k">' + L["ui"]["k_reg"] + '</div><div class="v">British Columbia, Canada</div></div>\n'
            '          <div class="identity-item"><div class="k">' + L["ui"]["k_addr"] + '</div><div class="v">1555 22nd Street, West Vancouver, BC, Canada V7V 4E1</div></div>\n'
            '        </div>\n'
            '        <div class="identity-verify">' + L["ui"]["verify"] + '</div>\n'
            '      </div>\n    </div>\n  </section>\n')

def chips_section(L):
    lis = "".join("        <li>%s</li>\n" % esc(i) for i in L["affiliates"])
    return ('  <section class="section">\n    <div class="container">\n'
            '      <div class="section-head">\n        <span class="section-no">NETWORK</span>\n'
            '        <h2>%s</h2>\n      </div>\n' % L["ui"]["aff_h2"]
            + '      <ul class="chips reveal">\n' + lis + '      </ul>\n    </div>\n  </section>\n')

def prose(L, no, h2, md, extra=""):
    if L["sections_redacted"]:
        md = redact(md)
    return ('  <section class="section">\n    <div class="container">\n'
            '      <div class="section-head">\n        <span class="section-no">%s</span>\n        <h2>%s</h2>\n      </div>\n%s'
            '      <div class="prose reveal">\n%s\n      </div>\n    </div>\n  </section>\n'
            % (no, h2, extra, md_to_html(md)))

# ---------------------------------------------------------------- 生成
for lang, L in LANGS.items():
    outdir = ROOT / L["prefix"]
    outdir.mkdir(parents=True, exist_ok=True)

    # 七个栏目页
    section_keys = ["overview", "mission", "activities", "outreach", "evaluation", "summary", "chairman"]
    for key in section_keys:
        title, desc, eyebrow, h1, lead = L["pages"][key]
        md = L["sections"][key]
        extra = ""
        if key == "activities":
            evs = re.findall(r"^### (.+)$", md, re.M)
            extra = ('      <nav class="ev-toc reveal" aria-label="event index">\n'
                     '        <span class="ev-toc-t">%s</span>\n        <ol>\n' % L["ui"]["ev_toc_t"]
                     + "".join('          <li><a href="#ev%d">%s</a></li>\n' % (i + 1, esc(t)) for i, t in enumerate(evs))
                     + "        </ol>\n      </nav>\n")
        body = prose(L, key.upper(), h1, md, extra=extra)
        if key == "overview":
            body += identity_section(L) + chips_section(L)
        if key == "chairman" and L["sig"]:
            sig_html = '\n      <div class="sig">%s</div>\n' % esc(L["sig"]).replace("\n", "<br>")
            body = body.replace("      </div>\n    </div>\n  </section>\n",
                                sig_html + "      </div>\n    </div>\n  </section>\n", 1)
        (outdir / (key + ".html")).write_text(
            page(L, key + ".html", title, desc, eyebrow, h1, lead, body), encoding="utf-8")
        print("wrote", L["prefix"] + key + ".html")

    # 首页
    cards = "".join(
        ('        <article class="card reveal">\n'
         '          <span class="toc-no">%s</span>\n'
         '          <h3><a href="%s">%s</a></h3>\n'
         '          <p class="desc">%s</p>\n'
         '          <a class="more" href="%s">%s -&gt;</a>\n'
         '        </article>\n') % (no, href, t, d, href, L["ui"]["read"])
        for no, t, href, d in L["toc_cards"]
    )
    ui = L["ui"]
    index_html = f"""<!DOCTYPE html>
<html lang="{L['html_lang']}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(ui['index_title'])}</title>
<meta name="description" content="{esc(ui['index_desc'])}">
<link rel="canonical" href="{BASE}/{L['prefix']}">
{hreflang('index.html', L['html_lang'])}<link rel="icon" type="image/svg+xml" href="{L['asset']}img/favicon.svg">
<link rel="stylesheet" href="{L['asset']}css/style.css">
<script>document.documentElement.classList.add("js");</script>
</head>
<body>
{header(L, "index.html")}

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

# 404（双语）
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
{header(L, "index.html")}

<main>
  <section class="section">
    <div class="container" style="max-width:620px; text-align:center;">
      <div class="eyebrow" style="justify-content:center;">404</div>
      <h1 style="font-size:34px;">页面未找到 / Page Not Found</h1>
      <p style="color:var(--ink-soft); margin-top:14px;">您访问的页面不存在或已移动。<br>The page you requested does not exist or has moved.</p>
      <p style="margin-top:24px;">
        <a class="btn btn--solid" href="index.html">返回首页</a>
        <a class="btn" href="en/index.html">English</a>
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

# sitemap（双语）
urls = []
for f in PAGES:
    zh_url = BASE + "/" + f
    en_url = BASE + "/en/" + f
    alt = ('<xhtml:link rel="alternate" hreflang="zh" href="%s"/>'
           '<xhtml:link rel="alternate" hreflang="en" href="%s"/>'
           '<xhtml:link rel="alternate" hreflang="x-default" href="%s"/>') % (zh_url, en_url, zh_url)
    pri = "1.0" if f == "index.html" else "0.8"
    urls.append('  <url>%s<loc>%s</loc><changefreq>monthly</changefreq><priority>%s</priority></url>' % (alt, zh_url, pri))
    urls.append('  <url>%s<loc>%s</loc><changefreq>monthly</changefreq><priority>%s</priority></url>' % (alt, en_url, pri))
(ROOT / "sitemap.xml").write_text(
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
    '        xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
    + "\n".join(urls) + "\n</urlset>\n", encoding="utf-8")
print("wrote sitemap.xml")
