#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""盘点 PDF：文本规模、彩色 span、注释、矢量横线。用于判断“干净版/批注版”。

用法：
  python inspect_pdf.py book.pdf
  python inspect_pdf.py book.pdf --json report.json
"""
import argparse
import json
import sys
from collections import Counter

try:
    import pymupdf
except ImportError:
    sys.exit("需要 PyMuPDF：pip install pymupdf")


def inspect(path):
    doc = pymupdf.open(path)
    pages = []
    color_chars = Counter()
    color_examples = {}
    annot_types = Counter()
    annot_examples = []
    total_chars = 0
    total_hlines = 0

    for pno, page in enumerate(doc):
        text = page.get_text("text")
        total_chars += len(text)
        hlines = 0
        for d in page.get_drawings():
            for it in d.get("items", []):
                if it[0] == "l":
                    a, b = it[1], it[2]
                    if abs(a.y - b.y) < 0.8 and abs(a.x - b.x) > 1.5:
                        hlines += 1
        total_hlines += hlines

        for b in page.get_text("dict")["blocks"]:
            for line in b.get("lines", []):
                for s in line["spans"]:
                    if s["color"] != 0 and s["text"].strip():
                        key = "#%06x" % s["color"]
                        color_chars[key] += len(s["text"])
                        color_examples.setdefault(key, s["text"][:60])

        anns = list(page.annots() or [])
        for a in anns:
            annot_types[a.type[1]] += 1
            if len(annot_examples) < 8:
                annot_examples.append({
                    "page": pno + 1,
                    "type": a.type[1],
                    "rect": [round(v, 1) for v in a.rect],
                    "colors": a.colors,
                })

        pages.append({
            "page": pno + 1,
            "rect": [round(v, 1) for v in page.rect],
            "chars": len(text),
            "images": len(page.get_images()),
            "annots": len(anns),
            "horizontal_lines": hlines,
            "first_line": next((l.strip() for l in text.splitlines() if l.strip()), ""),
        })

    return {
        "file": path,
        "pages": len(doc),
        "total_chars": total_chars,
        "annotations": dict(annot_types),
        "annotation_examples": annot_examples,
        "colored_spans": dict(color_chars),
        "color_examples": color_examples,
        "horizontal_lines": total_hlines,
        "page_details": pages,
        "hint": (
            "有 Ink/FreeText 注释 → 多半是批注版；横向线几乎等于正文行数 → 可能是装饰线/表格线。"
            "优先找“无注释、横线稀疏”的干净版作为下划线来源。"
        ),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--json", help="把完整报告写入 JSON")
    args = ap.parse_args()
    data = inspect(args.pdf)
    print(f"文件: {data['file']}")
    print(f"页数: {data['pages']}  总字符: {data['total_chars']}")
    print(f"注释: {data['annotations'] or '无'}")
    print(f"彩色文字: {data['colored_spans'] or '无'}")
    print(f"横向矢量线: {data['horizontal_lines']}")
    for p in data["page_details"][:8]:
        print(f"  p{p['page']}: chars={p['chars']} annots={p['annots']} hlines={p['horizontal_lines']}")
    print("提示:", data["hint"])
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print("写入", args.json)


if __name__ == "__main__":
    main()
