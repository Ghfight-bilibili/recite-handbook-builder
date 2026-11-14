---
name: recite-handbook-builder
description: 从 PDF 讲义/教材生成单文件、离线、可背诵的 HTML 学习手册：精确保留老师批注与原始排版下划线、知识树、三段式卡片、挖空/关键词/自测、暗色、网页全屏、全屏标记与笔记、JSON 备份。用户要把课程 PDF 做成平板背诵手册、要求“严格按 PDF 划线”、或复刻这套交互时用。Build a single-file offline recite handbook from PDFs with exact underlines, study modes, dark theme, fullscreen reader, marks/notes and JSON backup.
whenToUse: 用户提供 PDF/讲义并要求生成背诵手册、背诵网页、平板复习页；或需要给已有手册补内容、修下划线、加暗色/全屏/标记/备份；或要复刻“PDF → 知识树 → 卡片 → 背诵模式”的整套流程。
---

# 学习手册生成器（recite-handbook-builder）

把“PDF 讲义”变成“平板上能背的手册”，难点不在排版，而在**内容保真**和**交互不打架**。本 skill 记录一套已经实际交付过的方法、脚本与踩坑。

## 0. 适用与不适用

**适用**

- 有 1–10 份课程 PDF：正文、老师批注、真题、密训讲义。
- 要生成一个 `.html`，双击可开，断网可用，平板横屏阅读。
- 需要知识树、卡片、原文、批注、真题、背诵模式、全屏阅读、标记笔记。
- 之后可能还要导出横版 A4 PDF。

**不适用**

- 只想把 PDF 转成 Markdown：先用 `pdf-to-recite-md`。
- 只想要简单的折叠卡片：用 `html-recite-deck` 即可。
- 需要在线题库、账号系统、多人协作：这不是静态手册。

## 1. 先立三条硬规则

1. **原文不改写**。只允许改明显的错别字、标点、OCR 断行；不要用 AI 总结替代原文。
2. **下划线只认“干净版”排版线**。老师手写勾画（Ink/FreeText 注释）不是下划线依据；没有干净版时，宁可不画，也不要按“关键词句”自动猜。
3. **一个 HTML、零外部依赖**。CSS/JS 内联；系统字体；图片用内联 SVG 或 data URI；断网打开必须正常。

## 2. 输入盘点（先别写代码）

把文件分成四类，分别记录：

| 类型 | 用途 | 关键检查 |
|---|---|---|
| 必背原理（干净版） | 原文 + **排版下划线** | 有没有 Ink 注释？下划线是稀疏短语还是每行都有？ |
| 必背原理（批注版） | 老师红/蓝笔文字 | 颜色、字号、批注位置 |
| 密训 PPT | 答题方法、题型、真题索引 | 题号、关键词、模板 |
| 真题练习 | 题干、参考答案 | 哪些题有完整答案，哪些只有题干 |

先跑：

```bash
python scripts/inspect_pdf.py "马原分析题必背原理.pdf"
python scripts/inspect_pdf.py "马原分析题必背原理 - 横版.pdf"
```

看三件事：

- `annots`：有 Ink/FreeText 说明是批注版。
- `drawings`：横向线数量。**每行正文都有一条**通常是排版装饰线/表格线，不是语义下划线；稀疏的才是重点划线。
- `colored spans`：蓝色/红色文字，是老师笔记，不是下划线。

> 真实踩坑：第一版把“批注版”的红笔手写线 + 关键词所在句当成下划线，导致大面积多划。用户要的是“干净版 PDF 的排版线”，不是老师勾画。

## 3. 内容建模

不要直接拼 HTML。先建 JSON（或 Python 数据模块）：

```json
{
  "subjects": [
    {
      "id": "my",
      "title": "马克思主义基本原理",
      "groups": [
        {
          "title": "唯物辩证法",
          "cards": [
            {
              "id": "m01",
              "num": "01",
              "title": "实践是人与自然关系的基础",
              "essence": "实践是人与自然分化与统一的现实基础。",
              "tag": "人与自然",
              "parts": [
                {"label": "① 含义", "html": "<p>……</p>"},
                {"label": "② 特征", "html": "<p>……</p>"},
                {"label": "③ 方法论", "html": "<p>……</p>"}
              ],
              "notes": [{"kind": "red", "html": "……"}],
              "keywords": ["生态环境", "垃圾分类"],
              "exams": [
                {"year": "2011", "q": "34(1)", "title": "……", "answer": "……"}
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

字段约定：

- `parts`：三段式。单概念用 **含义 / 特征 / 方法论**；对子概念用 **含义 / 关系 / 方法论**。允许例外（评价、意义、做法），但要显式标出来。
- `notes.kind`：`blue` / `red`，对应老师蓝笔/红笔；不要把所有批注都染成同一种颜色。
- `keywords`：材料信号词，用于卡片底部 chips；不是下划线。
- `exams`：题干简短化；完整材料不要塞进卡片，放折叠区或索引。

### 知识树

树状图必须和讲义首页一致：科目 → 篇/章 → 子类 → 编号。不要按自己的理解重排。示例：

```text
马原
├ 唯物辩证法（13）
│  ├ 人与自然：01 02
│  ├ 两大特征：03 04
│  ├ 基本范畴：05 06 07
│  └ 矛盾分析法：08–12
├ 认识论（11）
└ 唯物史观（2）
```

如果讲义树里列了、正文却没有（例如“道德模范”），**留一个明确标注“待补”的占位卡**，不要编内容。

## 4. 精确下划线（本 skill 的核心）

### 4.1 从干净版 PDF 提取字符级标记

用 `scripts/extract_sections.py`：

```bash
python scripts/extract_sections.py "马原分析题必背原理.pdf" -o my_sections.json
python scripts/extract_sections.py "思修法基分析题必备原理.pdf" -o sx_sections.json
```

脚本做四件事：

1. 用 `page.get_text("rawdict")` 拿**每个字符**的 bbox（`dict` 没有 `chars`，这是坑）。
2. 用 `page.get_drawings()` 找横向线：`abs(y1-y2)<0.8`、长度>1.5、线宽<1。
3. 字符 bbox 与横线 x 区间重叠 >22%，且横线 y 在文本行底部 ±3.5 → 标记该字符为下划线。
4. 按标题字号（≥11.5 且 `^\d+\.`，或“质量互变规律（补充）”）切 section；跳过页码（字号<10）和篇/章大标题（≥13.5）。

输出每个 section：

```json
{
  "title": "实践是人与自然关系的基础",
  "text": "……",
  "flags": [false, false, true, ...],
  "phrases": ["……"]
}
```

**关键细节**

- 先看渲染图确认“横线”是不是语义下划线；有些 PDF 每行都有线，那是装饰。
- 首尾字符用“重叠比例”而不是“中心点”，否则会漏掉第一个字。
- 下划线可能跨行；把行文本直接拼接，flag 连续即可。
- 短语开头常会带前一句的 `。` 或 `，`，这是坐标边界造成的；对齐后把开头的 `。，；：、` 去掉。
- 少数短语会从词中间开始（如“脉是……”），用一个很小的 `PREFIX_FIXES` 手动补前几个字，不要全局放宽。

### 4.2 对齐到卡片文本

用 `scripts/align_underlines.py`：

```bash
python scripts/align_underlines.py \
  --sections my_sections.json \
  --content content.json \
  --subject my \
  --out underlines.json
```

算法：

1. section 按顺序映射到卡片（标题仅用于校验；顺序更可靠）。
2. `pdf_text == card_text` → flag 直接复制。
3. 不等 → `difflib.SequenceMatcher`，只在 matching block 内复制 flag；replace/delete 区域不复制。
4. 合并连续 true，去掉开头标点。
5. 输出 `{card_id: [[start,end], ...]}`。

**不要做的事**

- 不要用“句子包含关键词”当 flag。
- 不要把老师 Ink 注释的红色线条当 flag。
- 不要在没有干净版时猜；某条没有下划线就留空（例如“法治思维/法律权威”在干净版里确实没有线）。

### 4.3 把 range 写回 HTML

不要用 `html.replace(phrase, "<u>"+phrase+"</u>")`：

- 短语里常有 `<b>`、`<em>`，replace 匹配不到；
- 跨标签会破坏结构。

用 `wrap_ranges(html, ranges)`：按 `<tag>` 切 token，只对文本 token 的重叠部分包 `<u class="pdf-u">`。一个 range 跨标签时会变成多个相邻 `<u>`，视觉上仍连续。

```python
tokens = re.split(r'(<[^>]+>)', html)
# 计算每个 text token 的 [start,end)
# 对每个 range，切出 token 内的重叠段，包 <u>...</u>
```

### 4.4 三段标记的插入顺序

**先下划线，后插三段标记**，否则 range 偏移全变。

但下划线会产生 `<u>`，导致 `body.replace(prefix, marker+prefix)` 失败。必须按**纯文本 offset** 插入：

```python
idx = plain_text(body).find(prefix)
body = insert_at_text(body, idx, marker)
```

`insert_at_text` 的坑：

- `re.split` 会在相邻标签间产生空字符串 token；先过滤空 token，否则“`</u>` 后面是不是 `</b>`”判断会失败，标记会落进 `<b>`。
- offset 在文本 token 末尾时，要越过紧跟的 `</u></b>` 再插入；在开头时，要越过前面的 `<b><u>`。
- 插入后检查：任何 `<b>` 内都不能有 `part-mark`；否则关键词视图会把“② 关系”当成关键词。

## 5. HTML 结构与交互

### 5.1 卡片骨架

```html
<article class="card" id="m01">
  <div class="card-head">
    <div class="num">01</div>
    <div class="titles">
      <h3>实践是人与自然关系的基础</h3>
      <p class="ess">实践是人与自然分化与统一的现实基础。</p>
    </div>
    <span class="badge">人与自然</span>
    <button class="expand" aria-label="全屏背诵">…</button>
  </div>
  <div class="card-body">
    <div class="full">
      <span class="part-mark">① 含义</span>
      <p>…<b data-k="0">关键词</b>…</p>
      <span class="part-mark">② 特征</span>
      <p>…</p>
      <span class="part-mark">③ 方法论</span>
      <p>…</p>
    </div>
    <div class="keys-view">…</div>
    <div class="note blue/red">…</div>
    <div class="kw">…</div>
    <div class="exams">…</div>
  </div>
</article>
```

### 5.2 五种模式

`精读 / 速记 / 挖空 / 关键词 / 自测`：

- 精读：全文 + 批注 + 真题。
- 速记：只留标题、一句话、关键词，三栏。
- 挖空：全文保留，`<b>` 文字 `color:transparent`，点击逐个 reveal。
- 关键词：只显示按三段分组的 `<b>` chips，默认 `filter: blur(6px)`，点击清晰。
- 自测：隐藏 `.card-body`，点卡片展开，计数。

**CSS 优先级的坑**：思修卡片的 `.card.sx .full b { color: ... }` 比 `body.blank .full b { color: transparent }` 更具体，挖空会漏字。必须写：

```css
body.blank .full b,
body.blank .card.sx .full b { color: transparent !important; background: var(--paper-2) !important; }
body.blank .card.sx .full b.revealed { color: var(--sx-deep) !important; }
```

暗色模式还有 `html.dark .full b` 覆盖，同样要加 `html.dark body.blank ...`。

### 5.3 暗色

- 用 `html.dark { --变量 }`，不要给每个组件写一套颜色。
- 但正文里常有硬编码 `color:#2c271f`；必须补 `html.dark .full, html.dark .subblock p { color:#d8cfc1 }`，否则暗色下正文是黑的。
- 主题三态：`auto/light/dark`；`auto` 用 `matchMedia`，变化时重算。
- 在 `<head>` 里放一段极小的内联脚本先加 `.dark`，避免刷新闪白。

### 5.4 设置面板用 `<dialog>`

不要用 `position:fixed` 的 div 放在带 `backdrop-filter` 的 toolbar 里：`backdrop-filter` 会创建 containing block，fixed 变成相对 toolbar，面板会盖住按钮或跑出屏幕。

用原生 `<dialog>` + `showModal()`：

```css
dialog.settings { position:fixed; inset:0; margin:auto; width:min(372px,calc(100vw - 28px)); max-height:84dvh; overflow:auto; }
dialog.settings::backdrop { background:rgba(30,24,15,.42); backdrop-filter:blur(3px); }
```

低高度平板（1024×768）也不会截断；内容多时面板内部滚动。

### 5.5 全屏阅读

- 卡片右上角一个四角图标；阅读器里再放一个。
- `document.documentElement.requestFullscreen()`，`fullscreenchange` 更新图标。
- 关闭阅读器时如果还在全屏，自动 `exitFullscreen()`，否则手机上关掉阅读器后没有退出入口。
- 全屏时把阅读器 shell 设为 `100dvh`、`padding:0`、`border-radius:0`，真正铺满。

### 5.6 标记：不要跟系统选择菜单抢位置

手机长按选中文字时，系统菜单出现在**选区上方**。自定义浮层也放上方会被挡住。

正确逻辑：

1. 点“标记” → 屏幕**底部固定**出现操作栏（高亮/下划线/清除/完成）。
2. 用户正常长按选中；系统菜单在上方无所谓。
3. 点底部按钮；即使系统先收起了选区，也要保留 `lastRange` **约 3 秒**，否则点按钮会落空。
4. `selectionchange` 收起时不要立刻 `lastRange=null`，延迟清理。
5. 标记/笔记存 `localStorage`，按卡片 id 分组；导出/导入 JSON。

### 5.7 备份

设置里：

- 导出：`marks + notes + settings + exportedAt` → JSON 下载。
- 导入：`confirm` 后**合并**，同一张卡笔记以导入为准，标记按 `s-e-t` 去重；不删除本机已有记录。
- 状态行显示“几张卡有标记 / 多少处 / 几条笔记”。
- 下载可能被浏览器拦截；提示用户用 Chrome，或后续加“复制 JSON”兜底。

## 6. 验证（必须做）

用 `scripts/verify_html.py`：

```bash
python scripts/verify_html.py handbook.html --chrome "$CHROME_PATH"
```

检查：

- 1280×900、1024×768、820×1180、390×844 四档；
- `document.documentElement.scrollWidth === innerWidth`（无横向溢出）；
- `pageerror` / console error 为 0；
- 卡片数、`part-mark` 数、`keys-view` 数、`u.pdf-u` 数；
- 点击五种模式、主题、全屏、设置、标记，截图；
- `details` 初始全折叠；
- 打印前打开所有 details。

### Playwright 安装（国内网络）

官方 CDN 可能卡住。用镜像手动装 Chrome headless shell：

```bash
pip install playwright
# 从 npmmirror 下载 chrome-headless-shell-linux-arm64.zip
# 解压后把可执行文件路径传给 verify_html.py --chrome
```

缺系统库时 `apt-get install`：`libglib2.0-0t64 libnss3 libnspr4 libdbus-1-3 libatk1.0-0t64 libatk-bridge2.0-0t64 libcups2t64 libxcb1 libxcomposite1 libxdamage1 libxext6 libxfixes3 libxrandr2 libgbm1 libxkbcommon0 libasound2t64 libatspi2.0-0t64 libpango-1.0-0 libcairo2`。

## 7. 打印 / 横版 PDF

HTML 稳定后再做。要点：

- `@page { size: A4 landscape; margin: 8mm 9mm; }`
- 隐藏 sidebar/toolbar/modebar/reader/settings/expand；
- `details` 全部打开；
- 卡片 `break-inside: avoid`；
- 挖空/关键词模式在打印时恢复全文；
- 用 Chrome `--print-to-pdf` 或 Playwright `page.pdf(landscape=True)`；
- 打印前先目视第一页，避免封面/方法区产生大片空白。

## 8. 推荐工作顺序

1. 盘点 PDF（干净版/批注版）。
2. 提取原文、彩色批注、真题。
3. 手工建知识树与卡片 JSON。
4. 从干净版提取字符级下划线。
5. 对齐到卡片，生成 `underlines.json`。
6. 渲染 HTML（先内容，后交互）。
7. 加五种模式、暗色、全屏、标记、备份。
8. Playwright 四档验证 + 截图。
9. 修版式，再导出 PDF。

**不要**先做花哨交互再补内容；下划线/三段/关键词都是数据层的事，返工成本最高。

## 9. 交付前检查清单

- [ ] 每条原理原文与讲义一致（仅错别字修正）。
- [ ] 下划线只来自干净版 PDF；老师手写勾画没有混入。
- [ ] 没有下划线的条目保持空白，没有“补画”。
- [ ] 三段标签正确（含义/特征或关系/方法论）。
- [ ] 蓝笔/红笔批注颜色与来源对应。
- [ ] 知识树与 PDF 首页树状图一致；缺条目有“待补”占位。
- [ ] 五种模式可用；挖空在思修+暗色下不漏字。
- [ ] 明暗按钮独立可见，不是藏在设置里。
- [ ] 全屏可进可退；关闭阅读器自动退出全屏。
- [ ] 标记/笔记可保存、刷新不丢、可导出导入。
- [ ] 四档宽度无横向滚动；console 无报错。
- [ ] 断网打开正常；无 CDN/外链字体/外链图片。
- [ ] 文件在 `/sdcard/Download/DSH-Go/` 有副本（手机环境）。

## 10. 脚本

- `scripts/inspect_pdf.py`：盘点 PDF 的文本、颜色、注释、矢量线。
- `scripts/extract_sections.py`：干净版 PDF → section + 字符级下划线 flags。
- `scripts/align_underlines.py`：sections + content → 每卡 range。
- `scripts/verify_html.py`：Playwright 四档冒烟测试 + 截图。
- `templates/content.example.json`：内容模型示例。
- `templates/deck-skeleton.html`：最小可运行的五模式/暗色骨架，复制后扩展。

参考：

- `references/pdf-underlines.md`：下划线提取的细节与反例。
- `references/html-patterns.md`：卡片、模式、全屏、标记、备份的代码模式。
- `references/pitfalls.md`：按症状查的踩坑表。
- `references/verification.md`：验收清单与 Playwright 命令。
