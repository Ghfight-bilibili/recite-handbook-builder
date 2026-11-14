# PDF 下划线：从“看见”到“逐字对上”

## 1. 三种“线”，不要混

| 来源 | PyMuPDF | 含义 | 用法 |
|---|---|---|---|
| 老师手写勾画 | `page.annots()` 的 `Ink` / `FreeText` | 个人批注 | 只作为“老师批注”文字/颜色参考，**不能当下划线源** |
| 排版下划线 | `page.get_drawings()` 的横向 `l` | 讲义本来就划的重点 | 干净版里才是下划线源 |
| 每行都有的线 | `get_drawings()` 大量等距横线 | 表格线/装饰线/页面横线 | 不是语义下划线，忽略 |

**判断方法**：渲染一页看。若每一行正文下都有一条等长线，那是装饰；语义下划线只覆盖部分短语，且长度、起止点随文字变化。

## 2. 提取字符级 flags

```python
# 每个字符的 bbox
for block in page.get_text("rawdict")["blocks"]:
    for line in block["lines"]:
        for span in line["spans"]:
            for ch in span["chars"]:
                ...
```

`get_text("dict")` 的 span 没有 `chars`，只有 `text`；必须用 `rawdict`。

横向线：

```python
for d in page.get_drawings():
    for it in d["items"]:
        if it[0] == "l":
            a, b = it[1], it[2]
            if abs(a.y - b.y) < 0.8 and abs(a.x - b.x) > 1.5:
                # (x0, x1, y)
```

字符是否被划：

```python
overlap = max(0, min(ch_x1, line_x1) - max(ch_x0, line_x0))
flag = overlap > (ch_x1 - ch_x0) * 0.22
```

- 用 **overlap > 22%**，不要用“字符中心点在区间内”。否则首尾字会漏。
- 垂直线判定：`line.bbox[1] - 2 <= y <= line.bbox[3] + 3.5`。线在基线下方，太严会漏。
- 线宽通常 0.48–0.8；太粗的可能是表格边框。

## 3. 切 section

标题特征：

- 字号明显大于正文（如正文 10.4，标题 12.0）；
- 文本匹配 `^\d+\.`；
- 或特殊标题如“质量互变规律（补充）”。

跳过：

- 页码（字号 9，纯数字）；
- 篇/章标题（字号 14–15，如“唯物辩证法（13）”“（一）联系和发展”）。

**按顺序映射比按标题映射稳**。标题可能有全半角、冒号/逗号差异；顺序 + 标题校验最可靠。

## 4. 对齐到卡片文本

```python
if pdf_text == card_text:
    flags 直接复制
else:
    SequenceMatcher(None, pdf_text, card_text).get_matching_blocks()
    # 只在 matching block 内复制 flags
```

为什么会有差异：

- 你修正了错别字（“政造”→“改造”）；
- 你补了字（“检验的唯一标准”→“检验认识真理性的唯一标准”）；
- 你删了重复句；
- PDF 断行拼接与卡片空格不同。

`SequenceMatcher` 会把差异段跳过，所以差异处不会有下划线；这是可接受的，不要为了“连续”把差异段也划上。

## 5. 清理 range

- 去掉开头的 `。，；：、`：这些常是上一句的标点，被横线边界带进来。
- 合并连续/重叠 range。
- 不合并“中间隔了一个字”的 range，除非你确认那是错别字差异；否则会多划。
- 单字 range 保留（可能是“量变”这类关键词），但要目视确认。

## 6. 写回 HTML

不要 `replace(phrase, "<u>"+phrase+"</u>")`：短语可能跨 `<b>`，replace 匹配不到或破坏结构。

按标签切 token，只包文本重叠段：

```python
tokens = re.split(r'(<[^>]+>)', html)
# 对每个 text token 计算 [start,end)
# 对 range 与 token 的重叠段包 <u class="pdf-u">...</u>
```

一个 range 跨 `<b>` 会变成多个相邻 `<u>`；视觉上仍连续。

## 7. 三段标记的插入

**顺序：先下划线，再插三段标记。**

但下划线产生 `<u>`，`replace(prefix, marker+prefix)` 会失败。用纯文本 offset 插入：

```python
idx = plain_text(body).find(prefix)
body = insert_at_text(body, idx, marker)
```

`insert_at_text` 必须处理：

- `re.split` 的空 token：先过滤，否则 `</u>` 与 `</b>` 之间的空串会让“是否紧跟闭合标签”判断失败。
- offset 在文本末尾：越过 `</u></b>` 再插。
- offset 在文本开头：越过 `<b><u>` 再插。
- 插完检查 `<b>` 内没有 `part-mark`。

## 8. 常见反例

- **把红笔手写线当下划线**：会多划一大片；用户一眼看出。
- **按“关键词所在句”自动加下划线**：句子里的非重点也被划，且和干净版不一致。
- **没有干净版就猜**：宁可不划；某条没有线是正常的。
- **range 用字符中心点**：首字丢失，出现“脉是……”“正是……”这种半个词。
- **为了连续把差异字也划上**：多划一个字也是错。
- **先插三段再算偏移**：range 全错位。
