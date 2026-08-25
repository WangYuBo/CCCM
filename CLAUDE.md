# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is the content source for the official website of 国际中医养生大会理事会 (International Council of Conference on health-care with Chinese Medicine, CCCM) — a Canada-registered non-profit TCM organization (Corporation Number 1056656-0, registered 2018-01-04). It is a **content-only repository**: there is no website code, no build system, no package manager, and no tests. The single deliverable is `src.md`, the master Chinese-language content document (~790 lines) that will become the website.

- **Domain**: `cccm.info` — purchased via 腾讯云 (Tencent Cloud); registrar is 烟台帝思普网络科技有限公司.

## Working here

- There are no build/lint/test commands. The primary artifact is `src.md` (plain Markdown) — edit it directly; nothing compiles.
- All content is in Chinese. Most is simplified, but passages republished from older news reports mix in traditional characters (e.g. 歷) — preserve the original character forms when copying passages.
- Recurring entities to recognize: 张辉 (理事会执行主席 / 世界华人周刊社长), 焦顺发 (焦氏头针创始人, 第二届理事会主席), 世界华人周刊, 海外国医杂志社.

## `src.md` structure (the "big picture")

`src.md` is a cleaned, single-file Chinese content document assembled from the organization's own description plus republished news reports. Structure:

- **Document flow**: 组织概述 → 成立宗旨 (5 pillars) → 标志性活动 (11 events, 2017–2025) → 长效传播工作 → 行业评价体系建设 → 总结.
- **Heading hierarchy**: `#` title + registration-info card → `##` six main sections → `###` individual events (numbered （一）–（十一）) → `**bold**` internal sub-headings.
- **Large portions are third-party news reports republished with attribution** (中新网, 世界华人周刊, 搜狐, 澳门《中葡经贸导报》, 朔州日报, WeChat 公众号, etc.) — keep bylines/source links when restructuring.
- **Known gaps, not defects**: the 2022/2023 国医名家论坛 sections are empty placeholders ("内容待补充"); the 2024 温哥华 section carries a "⚠️ 此处原为图片/视频等素材，同步失败，待补充" marker where an asset failed to sync.
- **PII / privacy watch**: the 2020 线上 section retains a verbatim-duplicated "论坛详情" block and a Zoom link plus personal contact info (WeChat/phone/email of 张辉) from the original posts — **review and likely redact before publishing publicly** on ccccm.info.
- Content describes a **real registered non-profit organization** — treat all dates, names, and event descriptions as factual records; do not invent or alter history.
