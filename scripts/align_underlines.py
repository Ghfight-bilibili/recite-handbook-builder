#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把干净版 PDF 的字符级下划线，对齐到内容 JSON 的卡片文本。

输入：
  sections.json  （extract_sections.py 输出）
  content.json   （cards/subjects，字段见 templates/content.example.json）
输出：
  underlines.json = {"version":1,"ranges":{card_id:[[start,end],...]}}

用法：
  python align_underlines.py --sections my.json --content content.json --out underlines.json
  python align_underlines.py ... --subject my --skip-ids s13
  python align_underlines.py ... --map map.json --prefix-fixes fixes.json

注意：
  - 默认按 section 顺序对应卡片顺序；标题只用于提示。
  - 默认不跳过任何卡；有“待补/模板”卡时用 --skip-ids。
  - 某条没有下划线是正常的；不要为了“好看”补画。
"""
import argparse
import json
import re
import sys
from difflib import SequenceMatcher

PUNCT = "。，；：、"


def plain(html):
    return re.sub(r"<[^>]+>", "", html or "")


def norm(s):
    return re.sub(r"\s+", "", s or "")


def flatten_cards(data, subject=None):
    if isinstance(data, list):
        cards = data
    elif "cards" in data:
        cards = data["cards"]
    elif "subjects" in data:
        cards = []
        for sub in data["subjects"]:
            if subject and sub.get("id") != subject:
                continue
            for g in sub.get("groups", []):
                cards.extend(g.get("cards", []))
    else:
        raise SystemExit("content JSON 需要 cards 或 subjects")

    out = []
    for c in cards:
        body = c.get("body")
        if not body and c.get("parts"):
            body = "".join(p.get("html", "") for p in c["parts"])
        if not body:
            continue
        out.append({
            "id": c["id"],
            "title": c.get("title", ""),
            "text": norm(plain(body)),
        })
    return out


def transfer(pdf_text, flags, card_text):
    card_flags = [False] * len(card_text)
    if pdf_text == card_text:
        for i, f in enumerate(flags):
            if i < len(card_flags):
                card_flags[i] = f
    else:
        sm = SequenceMatcher(None, pdf_text, card_text, autojunk=False)
        for a, b, n in sm.get_matching_blocks():
            for k in range(n):
                if a + k < len(flags) and flags[a + k]:
                    card_flags[b + k] = True

    ranges = []
    i = 0
    while i < len(card_flags):
        if card_flags[i]:
            j = i
            while j < len(card_flags) and card_flags[j]:
                j += 1
            s, e = i, j
            while s < e and card_text[s] in PUNCT:
                s += 1
            if e > s:
                ranges.append([s, e])
            i = j
        else:
            i += 1

    merged = []
    for s, e in ranges:
        if merged and s <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])
    return merged


def load_prefix_fixes(path):
    if not path:
        return {}
    data = json.load(open(path, encoding="utf-8"))
    # {"card_id": [["needle_start","prefix"], ...]}
    return data


def fix_prefix(cid, card_text, ranges, fixes):
    out = []
    for s, e in ranges:
        for needle, pre in fixes.get(cid, []):
            if card_text[s:e].startswith(needle) and card_text[max(0, s - len(pre)):s] == pre:
                s -= len(pre)
                break
        out.append([s, e])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sections", required=True)
    ap.add_argument("--content", required=True)
    ap.add_argument("--out", default="underlines.json")
    ap.add_argument("--subject", help="只取该 subject id 的卡片")
    ap.add_argument("--skip-ids", default="", help="逗号分隔，如 s13,s-t1")
    ap.add_argument("--map", help="JSON: section raw/title -> card id")
    ap.add_argument("--prefix-fixes", help="JSON: card_id -> [[needle,prefix],...]")
    ap.add_argument("--print-phrases", type=int, default=3)
    args = ap.parse_args()

    sections = json.load(open(args.sections, encoding="utf-8"))
    content = json.load(open(args.content, encoding="utf-8"))
    cards = flatten_cards(content, args.subject)
    skip = {x.strip() for x in args.skip_ids.split(",") if x.strip()}
    if skip:
        cards = [c for c in cards if c["id"] not in skip]

    if len(sections) != len(cards):
        print(f"章节数 {len(sections)} != 卡片数 {len(cards)}", file=sys.stderr)
        print("sections:", [s["raw"] for s in sections], file=sys.stderr)
        print("cards:", [(c["id"], c["title"]) for c in cards], file=sys.stderr)
        print("提示：用 --skip-ids 排除待补/模板卡，或检查是否少了某个 section。", file=sys.stderr)
        sys.exit(2)

    mapping = {}
    if args.map:
        mapping = json.load(open(args.map, encoding="utf-8"))
    fixes = load_prefix_fixes(args.prefix_fixes)
    out = {}

    for sec, card in zip(sections, cards):
        cid = mapping.get(sec.get("raw")) or mapping.get(sec.get("title")) or card["id"]
        ct = card["text"]
        pt = norm(sec["text"])
        ranges = transfer(pt, sec.get("flags", []), ct)
        ranges = fix_prefix(cid, ct, ranges, fixes)
        out[cid] = ranges
        phrases = [ct[s:e] for s, e in ranges]
        print(f"{cid} [{card['title']}] <- [{sec['raw']}]  {len(ranges)} ranges")
        for p in phrases[:args.print_phrases]:
            print("   ", p)

    payload = {
        "version": 1,
        "source": args.sections,
        "ranges": out,
    }
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    print(f"写入 {args.out}：{sum(len(v) for v in out.values())} 个下划线范围")


if __name__ == "__main__":
    main()
