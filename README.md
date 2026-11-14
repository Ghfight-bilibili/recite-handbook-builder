# recite-handbook-builder

一个 DSH / Agent skill：把课程 PDF 讲义做成**单文件、离线、平板可背**的 HTML 学习手册。

不是简单的 PDF 转 Markdown，而是解决这几件麻烦事：

- **精确保留下划线**：区分老师手写批注和 PDF 排版下划线；从“干净版”逐字提取，不用 AI 猜。
- **三段式卡片**：含义 / 特征（或关系）/ 方法论；知识树与讲义首页一致。
- **五种背诵模式**：精读、速记、挖空、关键词、自测。
- **暗色模式**：独立月亮/太阳按钮，不是藏在设置里。
- **网页全屏 + 全屏阅读器**：隐藏浏览器地址栏，可调字号。
- **标记与笔记**：高亮/下划线/笔记，保存在本机；支持 JSON 导出导入。
- **可打印**：后续可接横版 A4 PDF。

## 安装

把整个目录放进 skill 目录：

```bash
git clone https://github.com/Ghfight-bilibili/recite-handbook-builder.git \
  ~/.dsh/skills/recite-handbook-builder
```

或直接复制 `SKILL.md` 所在目录到你的 skills 路径。重启会话后，技能目录里会出现 `recite-handbook-builder`。

## 包含内容

```text
SKILL.md                      # 主流程、硬规则、检查清单
references/
  pdf-underlines.md            # 字符级下划线提取与对齐
  html-patterns.md             # 五模式/暗色/dialog/全屏/标记/备份代码
  pitfalls.md                  # 按症状查的踩坑表
  verification.md              # 四档验收
scripts/
  inspect_pdf.py               # 盘点 PDF：注释/彩色字/矢量线
  extract_sections.py          # 干净版 PDF → 字符级下划线 flags
  align_underlines.py          # sections + content → 每卡 range
  verify_html.py               # Playwright 四档冒烟测试
templates/
  content.example.json         # 内容模型
  deck-skeleton.html           # 最小可运行的五模式/暗色/全屏骨架
```

## 快速开始

```bash
# 1. 看 PDF 是干净版还是批注版
python scripts/inspect_pdf.py 讲义.pdf

# 2. 从干净版提取下划线
python scripts/extract_sections.py 干净版.pdf -o sections.json

# 3. 对齐到你的 content.json
python scripts/align_underlines.py \
  --sections sections.json \
  --content content.json \
  --subject my \
  --skip-ids s13 \
  --out underlines.json

# 4. 按 SKILL.md 渲染 HTML（或从 deck-skeleton.html 改）

# 5. 四档验证
python scripts/verify_html.py 手册.html --chrome /path/to/chrome-headless-shell --shots shots
```

## 依赖

- Python 3.10+
- `pymupdf`：PDF 解析
- `playwright`：渲染验证（可选，但强烈建议）

```bash
pip install pymupdf playwright
```

国内网络装 Chromium 容易卡；见 `SKILL.md` 的 npmmirror 手动安装说明。

## 设计原则

1. 原文不改写，只修错别字。
2. 下划线只认干净版排版线；没有就不画。
3. 一个 HTML，零外链，断网可用。
4. 先内容与下划线，后交互；返工成本最高的是数据层。
5. 在 1280 / 1024 / 820 / 390 四档实际渲染，不靠“看代码觉得没问题”。

## License

MIT. 示例内容仅用于演示，不包含任何课程 PDF 或用户笔记。
