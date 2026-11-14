# HTML 交互模式与代码片段

## 1. 五种模式的状态机

```js
function setMode(m) {
  body.classList.toggle('brief', m === 'brief');
  body.classList.toggle('blank', m === 'blank');
  body.classList.toggle('keys', m === 'keys');
  body.classList.toggle('quiz', m === 'quiz');
  document.querySelectorAll('.revealed').forEach(el => el.classList.remove('revealed'));
  // 更新按钮 aria-pressed、计数、提示条
}
```

| 模式 | 显示 | 隐藏 |
|---|---|---|
| read | `.full` `.note` `.exams` | `.keys-view` |
| brief | `.titles` `.ess` `.kw` | `.full` `.note` `.exams` `.keys-view` |
| blank | `.full`（`b` 透明） | `.note` `.exams` `.keys-view` |
| keys | `.keys-view` | `.full` `.note` `.exams` |
| quiz | 卡片标题 | `.card-body`，点开才显示 |

## 2. 挖空的优先级

```css
body.blank .full b,
body.blank .card.sx .full b {
  color: transparent !important;
  background: var(--paper-2) !important;
  box-shadow: inset 0 -1px 0 var(--line-2);
  cursor: pointer;
}
body.blank .card.sx .full b.revealed {
  color: var(--sx-deep) !important;
  background: linear-gradient(transparent 61%, #f6e2da 61%) !important;
}
html.dark body.blank .full b,
html.dark body.blank .card.sx .full b {
  color: transparent !important;
  background: #28221b !important;
}
```

**为什么必须这么写**：`.card.sx .full b` 的 specificity 是 (0,3,1)，`body.blank .full b` 只有 (0,2,2)，前者会覆盖透明色，导致思修卡片挖空漏字。`html.dark .full b` 也会覆盖。

## 3. 关键词视图

```html
<div class="keys-view">
  <div class="kpart">
    <div class="kpart-h">① 含义</div>
    <div class="kchips">
      <button class="kchip">六十日</button>
      <button class="kchip">一年</button>
    </div>
  </div>
</div>
```

```css
.keys-view { display: none; }
body.keys .keys-view { display: block; }
body.keys .full, body.keys .note, body.keys .exams { display: none; }
.kchip { filter: blur(6px); opacity: .45; transition: filter .32s, opacity .32s; }
.kchip.revealed { filter: none; opacity: 1; }
```

- 关键词按“含义/特征/方法论”分组，不要平铺一大片。
- 关键词从 `<b>` 提取时，正则 `<b[^>]*>(.*?)</b>`，再 strip 标签和尾部 `。`。
- 卡片底部 `全部显示/全部隐藏` 吸附在 toolbar 下方；移动端不要放在顶部浮动。

## 4. 暗色变量

```css
html.dark {
  --paper:#13110e; --card:#1c1915; --ink:#e9e2d5; --ink2:#cdc4b5;
  --muted:#9b9181; --line:#332e27; --accent:#62c0ae; --accent2:#dd8a70;
  --gold:#d1a85e; --goldbg:#2d2719;
  color-scheme: dark;
}
```

必补的硬编码：

```css
html.dark .full, html.dark .subblock p { color: #d8cfc1; }
html.dark .titles h3 { color: #f1e9db; }
html.dark .full b { color:#9ed9ca; background:linear-gradient(transparent 61%,#1e3a33 61%); }
```

`<head>` 里提前应用，避免闪白：

```html
<script>
try {
  var t = localStorage.getItem('zz-theme') || 'auto';
  if (t === 'dark' || (t === 'auto' && matchMedia('(prefers-color-scheme: dark)').matches))
    document.documentElement.classList.add('dark');
} catch (e) {}
</script>
```

## 5. 设置用 `<dialog>`

```html
<dialog class="settings" id="settings">…</dialog>
```

```js
settings.showModal();  // 打开
settings.close();      // 关闭
```

```css
dialog.settings {
  position: fixed; inset: 0; margin: auto;
  width: min(372px, calc(100vw - 28px));
  max-height: min(84dvh, 760px);
  overflow: auto;
}
dialog.settings::backdrop { background: rgba(30,24,15,.42); backdrop-filter: blur(3px); }
```

**反例**：`position:fixed` 的 div 放在 `backdrop-filter` 的 toolbar 内，fixed 会相对 toolbar 定位，面板盖住按钮或跑出屏幕。`<dialog>` 在 top layer，不受影响。

## 6. 全屏阅读器

```js
async function toggleFullscreen() {
  if (document.fullscreenElement) return document.exitFullscreen();
  await document.documentElement.requestFullscreen();
}
document.addEventListener('fullscreenchange', () => {
  document.body.classList.toggle('fs', !!document.fullscreenElement);
});
```

- 关闭阅读器时自动退出全屏，否则手机上找不到退出入口。
- 全屏时：

```css
body.fs .reader { padding: 0; }
body.fs .reader-shell { width:100%; height:100dvh; border-radius:0; border:0; }
```

- iOS Safari 对 `requestFullscreen` 支持差，失败时提示用 Chrome/Edge。

## 7. 底部标记栏（避开系统选择菜单）

```html
<div class="sel-toolbar" id="selToolbar" hidden>
  <span id="selInfo">先选中文字</span>
  <button data-mark="hl">高亮</button>
  <button data-mark="ul">下划线</button>
  <button data-mark="clear">清除</button>
  <button data-mark="done">完成</button>
</div>
```

```css
.sel-toolbar {
  position: fixed; left: 50%; bottom: calc(14px + env(safe-area-inset-bottom));
  transform: translateX(-50%); z-index: 160;
}
```

流程：

1. 点“标记” → 显示底部栏。
2. 用户正常长按选中文字；系统菜单在上方，互不遮挡。
3. 点底部按钮。系统可能先收起选区，所以 `lastRange` 要保留约 3 秒：

```js
document.addEventListener('selectionchange', () => {
  if (!marking) return;
  const sel = getSelection();
  if (!sel || sel.isCollapsed) {
    if (lastRange) {
      setEnabled(true);
      clearTimeout(timer);
      timer = setTimeout(() => { lastRange = null; setEnabled(false); }, 3000);
    }
    return;
  }
  lastRange = sel.getRangeAt(0).cloneRange();
  setEnabled(true);
});
```

## 8. 标记/笔记存储

```js
const MARK_KEY = 'zz-marks-v1';
const NOTE_KEY = 'zz-notes-v1';
// marks: { cardId: [{s,e,t,text}] }, t = 'hl' | 'ul'
```

- 用纯文本 offset，而不是 HTML 字符串；换主题、改字号、加 `<u>` 不影响 offset。
- 应用时先 unwrap 旧的 `.user-hl/.user-ul`，再按 range 包；重叠 range 跳过。
- 导出：`{app, version, exportedAt, marks, notes, settings}`。
- 导入：`confirm` 后**合并**，按 `s-e-t` 去重；不删本机已有记录。

## 9. 打印

```css
@media print {
  @page { size: A4 landscape; margin: 8mm 9mm; }
  .side, .toolbar, .modebar, .reader, .settings, .expand { display: none !important; }
  .cards { grid-template-columns: 1fr 1fr; }
  .card { break-inside: avoid; box-shadow: none; }
  body.blank .full b { color: inherit !important; background: none !important; }
  body.keys .full { display: block !important; }
  body.keys .keys-view { display: none !important; }
}
```

打印前把所有 `details` 打开。
