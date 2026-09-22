#!/usr/bin/env python3
"""把 CCCM 机构官网站点文件上传到腾讯云「云开发静态托管」底层 COS 桶。

- 凭据从 ../env.local 读取（SecretId/SecretKey），不入库。
- 目标桶 f503-static-cccm-d1glcxn1w0b83cc6a-1306519554（ap-shanghai）。
- 只上传站点文件（四语 HTML + assets + robots/sitemap）；源码、凭据、进度文档一律不上传。
- 覆盖上线机构站后，删除备案个人站遗留的 about.html / article-1·2·3.html。

用法：
  python3 tools/deploy_site.py --dry-run   # 仅列出将上传/删除的文件，不实际操作
  python3 tools/deploy_site.py             # 实际上传 + 清理遗留
"""
import argparse
import pathlib
import re
import sys
from qcloud_cos import CosConfig, CosS3Client

ROOT = pathlib.Path(__file__).resolve().parent.parent
BUCKET = "f503-static-cccm-d1glcxn1w0b83cc6a-1306519554"
REGION = "ap-shanghai"

# 备案个人站遗留文件，机构站覆盖上线后应删除
ORPHANS = ["about.html", "article-1.html", "article-2.html", "article-3.html"]

CONTENT_TYPE = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".svg": "image/svg+xml",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".txt": "text/plain; charset=utf-8",
    ".xml": "application/xml; charset=utf-8",
}

ROOT_PAGES = [
    "index.html", "overview.html", "mission.html", "activities.html",
    "outreach.html", "evaluation.html", "summary.html", "chairman.html",
    "404.html", "robots.txt", "sitemap.xml",
]


def read_creds():
    cred = {}
    for line in (ROOT / "env.local").read_text(encoding="utf-8").splitlines():
        m = re.match(r"^(SecretId|SecretKey)\s*[:：]\s*(\S+)$", line.strip())
        if m:
            cred[m.group(1)] = m.group(2)
    if set(cred) != {"SecretId", "SecretKey"}:
        sys.exit("env.local 里未找到 SecretId/SecretKey")
    return cred


def collect_files():
    files = []
    for name in ROOT_PAGES:
        p = ROOT / name
        if not p.is_file():
            sys.exit(f"缺失站点文件：{name}")
        files.append(p)
    for lang in ("en", "fr", "de"):
        files += sorted((ROOT / lang).glob("*.html"))
    files += [p for p in sorted((ROOT / "assets").rglob("*")) if p.is_file()]
    return files


def ctype(p):
    return CONTENT_TYPE.get(p.suffix.lower(), "application/octet-stream")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="只列出，不执行")
    args = ap.parse_args()

    cred = read_creds()
    files = collect_files()

    print(f"目标桶 {BUCKET}（{REGION}）")
    print(f"上传 {len(files)} 个文件：")
    for f in files:
        print(f"  UPLOAD  {f.relative_to(ROOT).as_posix()}  [{ctype(f)}]")
    print("删除遗留：")
    for o in ORPHANS:
        print(f"  DELETE  {o}")

    if args.dry_run:
        print("\n（dry-run，未做任何改动）")
        return

    client = CosS3Client(CosConfig(Region=REGION, SecretId=cred["SecretId"],
                                   SecretKey=cred["SecretKey"]))
    ok = fail = 0
    for f in files:
        rel = f.relative_to(ROOT).as_posix()
        try:
            client.put_object(Bucket=BUCKET, Key=rel, Body=f.read_bytes(),
                              ContentType=ctype(f))
            ok += 1
        except Exception as e:  # noqa: BLE001
            fail += 1
            print(f"  [FAIL] {rel}: {e}")

    for o in ORPHANS:
        try:
            client.delete_object(Bucket=BUCKET, Key=o)
            print(f"  [DELETED] {o}")
        except Exception as e:  # noqa: BLE001
            print(f"  [DELETE-FAIL] {o}: {e}")

    print(f"\n完成：上传成功 {ok}，失败 {fail}")


if __name__ == "__main__":
    main()