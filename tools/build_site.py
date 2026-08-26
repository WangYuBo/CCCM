#!/usr/bin/env python3
"""从 src.md 生成 CCCM 网站。

网站栏目与《理事会简介》目录一一对应：首页 + 七个栏目页。
内容严格取自 src.md；仅对个人联系方式等隐私信息做发布级脱敏。
在仓库根目录运行：python3 tools/build_site.py
"""
import re
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = (ROOT / "src.md").read_text(encoding="utf-8")
BASE = "https://cccm.info"

# ---------------------------------------------------------------- 拆分 src.md
sections = {}
cur, buf = None, []
for line in SRC.splitlines():
    m = re.match(r"^## (.+)$", line)
    if m:
        if cur is not None:
            sections[cur] = "\n".join(buf).strip()
        cur, buf = m.group(1), []
    elif cur is not None:
        buf.append(line)
if cur is not None:
    sections[cur] = "\n".join(buf).strip()

# 文末署名（第七节尾部）
SIG = ""
tail = sections["七、理事会现任主席焦顺发简介"]
m = re.search(r"\n国际中医养生大会理事会（CCCM）\n\n\d{4}年\d+月\d+日\s*$", tail)
if m:
    SIG = tail[m.start():].strip()
    sections["七、理事会现任主席焦顺发简介"] = tail[: m.start()].strip()

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

    for raw in md.splitlines():
        s = raw.strip()
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

NAV = [
    ("index.html", "首页"),
    ("overview.html", "组织概述"),
    ("mission.html", "成立宗旨"),
    ("activities.html", "标志性活动"),
    ("outreach.html", "长效传播"),
    ("evaluation.html", "行业评价"),
    ("summary.html", "总结"),
    ("chairman.html", "主席简介"),
]

def header(current):
    links = "".join(
        '<a href="%s"%s>%s</a>' % (h, ' aria-current="page"' if h == current else "", t)
        for h, t in NAV
    )
    return ('<header class="site-header">\n  <div class="header-inner">\n'
            '    <a class="brand" href="index.html" aria-label="返回首页">\n'
            '      <span class="seal" aria-hidden="true">' + SEAL + '</span>\n'
            '      <span>\n        <span class="brand-name">国际中医养生大会理事会</span>\n'
            '        <span class="brand-sub">传承 · 创新 · 济世</span>\n      </span>\n'
            '    </a>\n'
            '    <button class="nav-toggle" aria-expanded="false" aria-label="打开菜单">☰</button>\n'
            '    <nav class="nav" aria-label="主导航">' + links + "</nav>\n"
            "  </div>\n</header>")

def footer():
    links = "".join('<a href="%s">%s</a>' % (h, t) for h, t in NAV)
    return ('<footer class="site-footer">\n  <div class="footer-inner">\n'
            '    <div class="footer-top">\n      <div class="footer-brand">\n'
            '        <span class="seal" aria-hidden="true">' + SEAL + '</span>\n'
            '        <div>\n          <div class="brand-name">国际中医养生大会理事会</div>\n'
            '          <div class="brand-sub">传承 · 创新 · 济世</div>\n        </div>\n      </div>\n'
            '      <div class="footer-meta">\n        Corporation No. 1056656-0<br>\n'
            '        Business No. 777456682RC0001<br>\n'
            '        1555 22nd Street, West Vancouver, BC, Canada\n      </div>\n    </div>\n'
            '    <nav class="footer-nav" aria-label="页脚导航">' + links + "</nav>\n"
            '    <div class="footer-bottom">\n'
            '      <span>© <span data-year>2026</span> 国际中医养生大会理事会 · 保留所有权利</span>\n'
            '      <span>加拿大联邦政府注册非盈利组织</span>\n    </div>\n  </div>\n</footer>')

def page(filename, title, desc, eyebrow, h1, lead, body):
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{BASE}/{filename}">
<link rel="icon" type="image/svg+xml" href="assets/img/favicon.svg">
<link rel="stylesheet" href="assets/css/style.css">
<script>document.documentElement.classList.add("js");</script>
</head>
<body>
{header(filename)}

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

{footer()}

<script src="assets/js/main.js"></script>
</body>
</html>
"""

IDENTITY = """  <section class="section">
    <div class="container">
      <div class="section-head">
        <span class="section-no">REGISTRATION</span>
        <h2>注册与身份</h2>
      </div>
      <div class="identity reveal">
        <div class="stamp" aria-hidden="true">""" + SEAL + """</div>
        <div class="identity-head">
          <h3>加拿大联邦政府注册 · 非政府 / 非宗教 / 非盈利组织</h3>
          <span class="identity-tag">STATUS: ACTIVE</span>
        </div>
        <div class="identity-grid">
          <div class="identity-item"><div class="k">CORPORATION NUMBER</div><div class="v">1056656-0</div></div>
          <div class="identity-item"><div class="k">BUSINESS NUMBER</div><div class="v">777456682RC0001</div></div>
          <div class="identity-item"><div class="k">FILING DATE</div><div class="v">2018-01-04</div></div>
          <div class="identity-item"><div class="k">注册地</div><div class="v">British Columbia, Canada</div></div>
          <div class="identity-item"><div class="k">地址</div><div class="v">1555 22nd Street, West Vancouver, BC, Canada V7V 4E1</div></div>
        </div>
        <div class="identity-verify">以上信息可在加拿大联邦政府公司注册登记处（Corporations Canada）在线核验。</div>
      </div>
    </div>
  </section>
"""

def chips_section(items):
    lis = "".join("        <li>%s</li>\n" % esc(i) for i in items)
    return ('  <section class="section">\n    <div class="container">\n'
            '      <div class="section-head">\n        <span class="section-no">NETWORK</span>\n'
            '        <h2>旗下机构</h2>\n      </div>\n'
            '      <ul class="chips reveal">\n' + lis + '      </ul>\n    </div>\n  </section>\n')

def prose(no, h2, md, extra=""):
    return ('  <section class="section">\n    <div class="container">\n'
            '      <div class="section-head">\n        <span class="section-no">%s</span>\n        <h2>%s</h2>\n      </div>\n%s'
            '      <div class="prose reveal">\n%s\n      </div>\n    </div>\n  </section>\n'
            % (no, h2, extra, md_to_html(redact(md))))

# ---------------------------------------------------------------- 生成各页
files = {}

# 一、组织概述
files["overview.html"] = page(
    "overview.html", "组织概述 | 国际中医养生大会理事会（CCCM）",
    "国际中医养生大会理事会（CCCM）组织概述：2018年在加拿大联邦政府注册的国际公益性行业组织，中医药在欧美地区传播与发展的核心民间载体。",
    "CCCM 简介 · 第一部分", "组织概述",
    "一个真实、可核验的加拿大注册非盈利中医组织，一个跨国界、跨文化的中医药交流平台。",
    prose("OVERVIEW", "组织概述", sections["一、组织概述"])
    + IDENTITY
    + chips_section(re.findall(r"^- (.+)$", sections["旗下机构"], re.M)),
)

# 二、成立宗旨
files["mission.html"] = page(
    "mission.html", "成立宗旨 | 国际中医养生大会理事会（CCCM）",
    "理事会成立宗旨：扎根“传承、创新、济世”三大核心理念，五大宗旨与国际中医药AI创新中心。",
    "CCCM 简介 · 第二部分", "成立宗旨",
    "理事会的成立宗旨，深深扎根于“传承、创新、济世”三大核心理念。",
    prose("MISSION", "成立宗旨", sections["二、成立宗旨"]),
)

# 三、标志性活动
evs = re.findall(r"^### (.+)$", sections["三、标志性活动"], re.M)
ev_toc = ('      <nav class="ev-toc reveal" aria-label="活动目录">\n'
          '        <span class="ev-toc-t">十场标志性活动</span>\n        <ol>\n'
          + "".join('          <li><a href="#ev%d">%s</a></li>\n' % (i + 1, esc(t)) for i, t in enumerate(evs))
          + "        </ol>\n      </nav>\n")
files["activities.html"] = page(
    "activities.html", "标志性活动 | 国际中医养生大会理事会（CCCM）",
    "2017–2025年理事会十场标志性活动全记录：国际中医养生大会、国医名家论坛、海外国医论坛、世界头针年会等。",
    "CCCM 简介 · 第三部分", "标志性活动",
    "从2017年温哥华首届国际中医养生大会，到2025年海口第二届国医名家研讨会--十场标志性活动全记录。",
    prose("ACTIVITIES", "标志性活动", sections["三、标志性活动"], extra=ev_toc),
)

# 四、长效传播工作
files["outreach.html"] = page(
    "outreach.html", "长效传播工作 | 国际中医养生大会理事会（CCCM）",
    "理事会长效传播工作：海外中医临床病案整理出版、《海外国医》刊物编辑与海外社区公益养生推广。",
    "CCCM 简介 · 第四部分", "长效传播工作",
    "记录海外中医发展史料，让养生文化走进海外社区。",
    prose("OUTREACH", "长效传播工作", sections["四、长效传播工作"]),
)

# 五、行业评价体系建设
files["evaluation.html"] = page(
    "evaluation.html", "行业评价体系建设 | 国际中医养生大会理事会（CCCM）",
    "海外国医大师、名家评审委员会与行业评价体系建设：填补海外中医行业评价体系空白。",
    "CCCM 简介 · 第五部分", "行业评价体系建设",
    "填补海外中医行业评价体系的空白，为海外中医师提供坚实的执业后盾。",
    prose("EVALUATION", "行业评价体系建设", sections["五、行业评价体系建设"]),
)

# 六、总结
files["summary.html"] = page(
    "summary.html", "总结 | 国际中医养生大会理事会（CCCM）",
    "国际中医养生大会理事会工作总结：不以商业盈利为首要目标，为中加中医药文化交流与海外华人医疗公益事业发挥积极作用。",
    "CCCM 简介 · 第六部分", "总结",
    "不以商业盈利为首要目标，助力中医药融入全球健康治理。",
    prose("SUMMARY", "总结", sections["六、总结"]),
)

# 七、主席简介（文末署名附在本页结尾）
sig_html = ('\n      <div class="sig">%s</div>\n' % esc(SIG).replace("\n", "<br>")) if SIG else ""
files["chairman.html"] = page(
    "chairman.html", "主席简介 | 国际中医养生大会理事会（CCCM）",
    "理事会现任主席焦顺发简介：“焦氏头针”创始人和奠基者，头针研究的从医历程与临床成果。",
    "CCCM 简介 · 第七部分", "理事会现任主席焦顺发简介",
    "“焦氏头针”的创始人和奠基者，理事会现任主席。",
    prose("CHAIRMAN", "焦顺发简介", sections["七、理事会现任主席焦顺发简介"]).replace(
        "      </div>\n    </div>\n  </section>\n",
        sig_html + "      </div>\n    </div>\n  </section>\n", 1),
)

# 首页
TOC_CARDS = [
    ("一", "组织概述", "overview.html", "加拿大注册的国际公益性行业组织，中医药在欧美传播与发展的核心民间载体。"),
    ("二", "成立宗旨", "mission.html", "扎根“传承、创新、济世”核心理念，五大宗旨与国际中医药AI创新中心。"),
    ("三", "标志性活动", "activities.html", "2017–2025年十场标志性活动全记录，含各家媒体报道原文。"),
    ("四", "长效传播工作", "outreach.html", "病案出版、专业刊物与海外社区公益养生的常态化传播。"),
    ("五", "行业评价体系建设", "evaluation.html", "海外国医大师、名家评审委员会与两届入选名单。"),
    ("六", "总结", "summary.html", "理事会多年工作的回顾与总结。"),
    ("七", "主席简介", "chairman.html", "理事会现任主席焦顺发--“焦氏头针”的创始人和奠基者。"),
]
cards = "".join(
    ('        <article class="card reveal">\n'
     '          <span class="toc-no">%s</span>\n'
     '          <h3><a href="%s">%s</a></h3>\n'
     '          <p class="desc">%s</p>\n'
     '          <a class="more" href="%s">阅读 -></a>\n'
     '        </article>\n') % (no, href, t, d, href)
    for no, t, href, d in TOC_CARDS
)
files["index.html"] = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>国际中医养生大会理事会（CCCM）| 中医药国际交流平台</title>
<meta name="description" content="国际中医养生大会理事会（CCCM）是2018年在加拿大联邦政府注册的非政府、非宗教、非盈利组织，搭建跨国界、跨文化的中医药交流平台，主办国医名家论坛、海外国医论坛等标志性活动。">
<link rel="canonical" href="{BASE}/">
<link rel="icon" type="image/svg+xml" href="assets/img/favicon.svg">
<link rel="stylesheet" href="assets/css/style.css">
<script>document.documentElement.classList.add("js");</script>
</head>
<body>
{header("index.html")}

<main>
  <!-- Hero -->
  <section class="hero">
    <div class="hero-inner">
      <div class="hero-seal" aria-hidden="true">{SEAL}</div>
      <div>
        <h1 class="hero-title">国际中医养生大会理事会
          <span class="en">INTERNATIONAL COUNCIL OF CONFERENCE ON HEALTH-CARE WITH CHINESE MEDICINE</span>
        </h1>
        <p class="hero-lead">依托北美华人中医药专业力量，搭建跨国界、跨文化的中医药交流平台--面向全球推动中医养生文化传播、国际中医药AI创新研究、中医针灸学术交流与健康公益服务。</p>
        <div class="hero-actions">
          <a class="btn btn--solid" href="overview.html">了解我们</a>
          <a class="btn" href="activities.html">标志性活动</a>
        </div>
      </div>
    </div>
    <div class="hero-vtext" aria-hidden="true">国际中医养生大会理事会 · 二〇一八</div>
  </section>

  <!-- 章节目录（与《理事会简介》目录一一对应） -->
  <section class="section">
    <div class="container">
      <div class="section-head">
        <span class="section-no">CONTENTS</span>
        <h2>章节目录</h2>
      </div>
      <div class="grid toc-grid">
{cards}      </div>
    </div>
  </section>
</main>

{footer()}

<script src="assets/js/main.js"></script>
</body>
</html>
"""

# 404
files["404.html"] = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>页面未找到 | 国际中医养生大会理事会（CCCM）</title>
<meta name="robots" content="noindex">
<link rel="icon" type="image/svg+xml" href="assets/img/favicon.svg">
<link rel="stylesheet" href="assets/css/style.css">
<script>document.documentElement.classList.add("js");</script>
</head>
<body>
{header("404.html")}

<main>
  <section class="section">
    <div class="container" style="max-width:620px; text-align:center;">
      <div class="eyebrow" style="justify-content:center;">404</div>
      <h1 style="font-size:34px;">页面未找到</h1>
      <p style="color:var(--ink-soft); margin-top:14px;">您访问的页面不存在或已移动。您可以从以下栏目继续浏览。</p>
      <p style="margin-top:24px;"><a class="btn btn--solid" href="index.html">返回首页</a></p>
    </div>
  </section>
</main>

{footer()}

<script src="assets/js/main.js"></script>
</body>
</html>
"""

# sitemap
sitemap = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
           + "".join('  <url><loc>%s/%s</loc><changefreq>monthly</changefreq><priority>%s</priority></url>\n'
                     % (BASE, f, "1.0" if f == "index.html" else "0.8") for f in files if f != "404.html")
           + "</urlset>\n")
(ROOT / "sitemap.xml").write_text(sitemap, encoding="utf-8")

for name, html in files.items():
    (ROOT / name).write_text(html, encoding="utf-8")
    print("wrote", name, len(html), "bytes")
print("wrote sitemap.xml")
