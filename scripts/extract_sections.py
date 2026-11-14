#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从“干净版”PDF 提取章节正文 + 字符级下划线标记。

输出 sections.json：
  [{title, raw, text, flags:[bool...], phrases:[...]}]

用法：
  python extract_sections.py clean.pdf -o sections.json
  python extract_sections.py clean.pdf -o sections.json --debug

原理：
  - rawdict 拿到每个字符的 bbox；
  - get_drawings() 的横向线 = 排版下划线；
  - 字符 bbox 与横线 x 区间重叠 >22%，且线在行底 ±3.5pt → 标 true；
  - 按标题字号切 section；跳过页码和篇/章大标题。
"""
import argparse
import json
import re
import sys

try:
    import pymupdf
except ImportError:
    sys.exit("需要 PyMuPDF：pip install pymupdf")

PUNCT = "。，；：、"


def is_horizontal_line(item):
    if item[0] != "l":
        return None
    a, b = item[1], item[2]
    if abs(a.y - b.y) < 0.8 and abs(a.x - b.x) > 1.5:
        return (min(a.x, b.x), max(a.x, b.x), a.y)
    return None


def heading_title(txt):
    txt = txt.strip()
    m = re.match(r"^\d+\.\s*(.+)$", txt)
    if m:
        return m.group(1).strip()
    if txt.startswith("质量互变规律"):
        return txt
    return None


def extract(path, heading_min=11.5, group_min=13.5, body_max=12.5, debug=False):
    doc = pymupdf.open(path)
    sections = []
    cur = None

    for pno, page in enumerate(doc):
        underlines = []
        for d in page.get_drawings():
            for it in d.get("items", []):
                seg = is_horizontal_line(it)
                if seg:
                    underlines.append(seg)

        for block in page.get_text("rawdict")["blocks"]:
            for line in block.get("lines", []):
                spans = line.get("spans", [])
                if not spans:
                    continue
                text = "".join(
                    "".join(c["c"] for c in s.get("chars", [])) for s in spans
                ).strip()
                if not text:
                    continue
                size = max(s["size"] for s in spans)

                # 页码
                if size < 10 and re.fullmatch(r"\d+", text):
                    continue

                title = heading_title(text) if size >= heading_min else None
                if title:
                    cur = {"title": title, "raw": text, "text": "", "flags": []}
                    sections.append(cur)
                    if debug:
                        print(f"HEAD p{pno+1} [{text}] size={size}")
                    continue

                # 篇/章大标题（不编号，字号明显大于正文）
                if size >= group_min:
                    if debug:
                        print(f"GROUP p{pno+1} [{text}] size={size}")
                    continue

                if cur is None:
                    continue

                chars = []
                for s in spans:
                    chars.extend(s.get("chars", []))

                for c in chars:
                    cw = max(0.1, c["bbox"][2] - c["bbox"][0])
                    flag = False
                    for x0, x1, y in underlines:
                        if not (line["bbox"][1] - 2 <= y <= line["bbox"][3] + 3.5):
                            continue
                        overlap = max(0.0, min(c["bbox"][2], x1) - max(c["bbox"][0], x0))
                        if overlap > cw * 0.22:
                            flag = True
                            break
                    cur["text"] += c["c"]
                    cur["flags"].append(flag)

    # 短语 + 去开头标点
    for sec in sections:
        chars, flags = sec["text"], sec["flags"]
        phrases = []
        i = 0
        while i < len(flags):
            if flags[i]:
                j = i
                while j < len(flags) and flags[j]:
                    j += 1
                s, e = i, j
                while s < e and chars[s] in PUNCT:
                    s += 1
                if e > s:
                    phrases.append(chars[s:e])
                i = j
            else:
                i += 1
        sec["phrases"] = phrases

    return sections


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("-o", "--out", default="sections.json")
    ap.add_argument("--heading-min", type=float, default=11.5)
    ap.add_argument("--group-min", type=float, default=13.5)
    ap.add_argument("--body-max", type=float, default=12.5)
    ap.add_argument("--debug", action="store_true")
    args = ap.parse_args()

    secs = extract(args.pdf, args.heading_min, args.group_min, args.body_max, args.debug)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(secs, f, ensure_ascii=False, indent=1)

    n_flags = sum(sum(1 for x in s["flags"] if x) for s in secs)
    print(f"识别 {len(secs)} 个章节，{n_flags} 个下划线字符，写入 {args.out}")
    for s in secs[:6]:
        print(f"- {s['title']}  chars={len(s['text'])}  phrases={len(s['phrases'])}")
    if n_flags == 0:
        print("警告：没有识别到下划线。检查这是否为干净版，或横线是否被判定为装饰线。")


if __name__ == "__main__":
    main()
