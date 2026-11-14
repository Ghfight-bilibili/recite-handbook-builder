# 验证手册

## 1. 四档冒烟

```bash
python scripts/verify_html.py "手册.html" \
  --chrome /root/.cache/pw/shell/chrome-headless-shell-linux-arm64/chrome-headless-shell \
  --shots shots
```

必须全部通过：

- 1280×900、1024×768、820×1180、390×844；
- `scrollWidth === innerWidth`；
- `pageerror` / console error 为 0；
- 卡片数、`part-mark` 数、`keys-view` 数、`u.pdf-u` 数符合预期。

## 2. 手工点一遍

- 五种模式逐个切换；速记三栏、挖空点击显示、关键词模糊→清晰、自测计数。
- 明暗按钮独立可点；切换后正文、批注、设置面板都可读。
- 卡片右上角全屏；阅读器内 A−/A+；关闭后退出网页全屏。
- 标记：点“标记”→ 底部栏 → 长按选中 → 高亮/下划线；系统菜单在上方不冲突。
- 笔记：输入→关闭→重开还在。
- 设置：导出 JSON；导入同一文件；状态行计数变化。
- 刷新页面：标记/笔记/主题/字号还在。
- 打印预览：无 toolbar/sidebar/reader；卡片不被切断；挖空恢复全文。

## 3. 内容抽查

- 打开 3 条有代表性的卡片：一条下划线多、一条只有一处、一条完全没有。
- 对照干净版 PDF 的同一页，逐字看下划线起止。
- 检查三段标记的 ①/②/③ 是否在该在的位置，且没有跑进 `<b>`。
- 检查蓝笔/红笔批注颜色与来源。

## 4. 结构检查

```python
import re
html = open("手册.html", encoding="utf-8").read()
assert html.count("<article class=\"card") == 卡片数
# 标签平衡
for tag in ["b","u","p","div","span"]:
    assert len(re.findall(rf"<{tag}[\s>]", html)) == html.count(f"</{tag}>")
# 外链
assert not re.search(r'(src|href)="https?://', html)
```

## 5. 打印检查

- `@page { size: A4 landscape; }`
- 打印前 `document.querySelectorAll('details').forEach(d=>d.open=true)`
- 打印后第一页不应有大片空白；卡片 `break-inside:avoid`。
- 如果封面/方法区独占一页，考虑 `break-before:page` 或压缩高度。

## 6. 交付

- 文件放 `/sdcard/Download/DSH-Go/`（手机环境）。
- 附一句“标记和笔记保存在浏览器本地，建议定期导出 JSON”。
- 如果用户还要加讲义，保留内容 JSON/生成脚本，不要只留最终 HTML。
