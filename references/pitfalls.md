# 踩坑速查表

按症状查，不要按顺序读。

## PDF / 下划线

| 症状 | 原因 | 修法 |
|---|---|---|
| 下划线大面积覆盖，几乎每句都有 | 用了批注版的红笔手写线，或按“关键词所在句”自动加 | 换干净版；只提取 `get_drawings()` 的稀疏横线；某条没有线就留空 |
| 下划线每行都有、长度固定 | 把表格线/页面装饰线当语义下划线 | 渲染一页目视；只保留长度随文字变化的线 |
| 首字丢失：“脉是……”“正是……” | 用字符中心点判断，横线起点在字符左缘 | 用 bbox 重叠 >22% |
| 开头多一个“。”“，” | 横线覆盖了上一句的标点 | 对齐后去掉 range 开头的 `。，；：、` |
| 某条完全没有下划线 | 干净版里确实没有 | 保持空白，不要补画 |
| 下划线跨行断成两段 | PDF 换行；字符拼接后 flag 连续即可 | 合并相邻 range；不要按行断开 |
| 对齐后下划线错位 | 先插了三段标记，或改了原文 | 先提取/对齐，再插入三段；原文改动后重新生成 ranges |
| 某些短语多划/少划一个字 | 你修正过错别字或补过字 | `SequenceMatcher` 只复制 matching block；差异处留空；必要时用 prefix fixes |
| `get_text("dict")` 没有 `chars` | 用错模式 | 改 `rawdict` |
| section 数比卡片数多/少 | 页码、篇标题被当成 section；或有“待补”卡 | 跳过页码/大标题；`--skip-ids` 排除占位卡 |

## HTML / CSS

| 症状 | 原因 | 修法 |
|---|---|---|
| 思修卡片挖空仍能看见文字 | `.card.sx .full b` 的 specificity 高于 `body.blank .full b` | 加 `body.blank .card.sx .full b { color:transparent !important; }` |
| 暗色下挖空能看见文字 | `html.dark .full b` 覆盖透明色 | 加 `html.dark body.blank ...` 的同级规则 |
| 暗色正文几乎看不见 | `.full`/`.subblock p` 有硬编码 `color:#2c271f` | 加 `html.dark .full, html.dark .subblock p { color:#d8cfc1 }` |
| 设置面板盖住按钮/跑出屏幕 | `position:fixed` 在 `backdrop-filter` 的 toolbar 内 | 用 `<dialog>` + `showModal()` |
| 设置面板底部被截断 | 绝对定位 + 低高度平板 | `<dialog>` + `max-height:84dvh; overflow:auto` |
| 手机关键词模式两列挤成一字一行 | `body.keys .cards { grid-template-columns: repeat(2,...) }` 写在媒体查询之后 | 在文件最后加 `@media(max-width:820px){ body.keys .cards, body.blank .cards { grid-template-columns:1fr } }` |
| 五模式工具栏在手机溢出 | 按钮太多 | <=560 缩小 padding、隐藏页面全屏按钮；阅读器里保留全屏 |
| 三段标记跑进 `<b>` 里 | 按文本 offset 插入时遇到空 token / 标签边界 | 过滤空 token；offset 在末尾越过 `</u></b>`；在开头越过 `<b><u>`；最后检查 `<b>` 内无 `part-mark` |
| 下划线包坏标签 | 用 `replace(phrase, "<u>...")` | 按 token 包文本重叠段 |
| 关键词视图把“② 关系”当关键词 | 段标记在 `<b>` 内 | 同上；修完跑 tag 平衡/标记检查 |
| 打印时 reader/设置/toolbar 还在 | 打印 CSS 没隐藏 | 全部 `display:none !important`；打印前打开 details |

## 交互 / 手机

| 症状 | 原因 | 修法 |
|---|---|---|
| 标记浮层被系统选择菜单挡住 | 浮层跟随选区，在选区上方 | 改成底部固定操作栏；点“标记”才出现 |
| 点底部“高亮”没反应 | 系统先收起选区，`lastRange` 被清空 | 收起时保留 range 3 秒；点按钮后再清 |
| 关闭阅读器后还在网页全屏 | 没退出 fullscreen | `closeReader()` 里 `exitFullscreen()` |
| 导出没反应 | 浏览器拦截下载 | 用 Chrome/Edge；或加“复制 JSON”兜底 |
| 刷新后标记/笔记丢了 | 清除了浏览器数据 / 换浏览器 | 导出 JSON；导入合并 |
| 导入后标记错位 | 内容改过，offset 变了 | 重新生成 ranges；应用时校验 `text`，不匹配就搜索文本 |
| 主题按钮找不到 | 藏在设置里 | 工具栏独立月亮/太阳按钮；设置里保留三态 |
| 全屏按钮在手机上不见 | 工具栏放不下被隐藏 | 阅读器 header 保留一个全屏按钮 |

## 验证 / 工具

| 症状 | 原因 | 修法 |
|---|---|---|
| Playwright 下载卡住 | 官方 CDN 慢 | 用 npmmirror 的 `chrome-for-testing` 包手动解压，`--chrome` 指过去 |
| Chrome 启动缺库 | 没装 NSS/GTK 等 | `apt-get install libnss3 libnspr4 libgbm1 libasound2t64 ...` |
| 截图里卡片顶部被切 | 页面滚动到 sticky toolbar 下面 | 截图前 `scrollIntoView({block:'center'})` 或截元素而非视口 |
| 测试显示 2 列但手机 1 列 | 媒体查询顺序被后面的规则覆盖 | 把移动端覆盖放到最后 |
| 控制台无报错但布局错 | 只看代码没看渲染 | 必须四档截图 + `scrollWidth===innerWidth` |
