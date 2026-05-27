# zotero-mineru 使用指南

> 把 Zotero 里的每篇 PDF 自动转成高质量 Markdown（通过 MinerU），并生成全库索引供 AI / 人检索。

---

## 目录

1. [这个工具是干什么的](#1-这个工具是干什么的)
2. [架构总览](#2-架构总览)
3. [前置条件](#3-前置条件)
4. [配置说明（config.json）](#4-配置说明configjson)
5. [核心用法](#5-核心用法)
   - [5.1 一次性批量转换（batch.py）](#51-一次性批量转换batchpy)
   - [5.2 后台守护自动转换（watcher.py）](#52-后台守护自动转换watcherpy)
   - [5.3 查看状态与进度](#53-查看状态与进度)
6. [索引系统（build_index.py）](#6-索引系统build_indexpy)
7. [查询与导出](#7-查询与导出)
   - [7.1 命令行查询（zotero_query.py）](#71-命令行查询zotero_querypy)
   - [7.2 命令行导出（export_md.py）](#72-命令行导出export_mdpy)
   - [7.3 GUI 导出工具（export_gui.py）](#73-gui-导出工具export_guipy)
8. [Zotero 内集成（Actions 脚本）](#8-zotero-内集成actions-脚本)
9. [审计与清理工具](#9-审计与清理工具)
10. [大 PDF 处理机制](#10-大-pdf-处理机制)
11. [mineru-api 模式详解](#11-mineru-api-模式详解)
12. [数据流与目录结构](#12-数据流与目录结构)
13. [state.json 状态说明](#13-statejson-状态说明)
14. [常见问题与排查](#14-常见问题与排查)
15. [完整命令速查表](#15-完整命令速查表)

---

## 1. 这个工具是干什么的

你在 Zotero 里积累了几十上百篇 PDF 论文。你想让 AI（或你自己）能按 Markdown 格式快速消化每篇论文的全文，包括文字、公式、表格、图片。

zotero-mineru 做的事：

1. **扫描** Zotero 本地 storage 目录，找到所有 PDF
2. **调用 MinerU** 把每篇 PDF 转成 Markdown + 图片
3. **输出** 到 mineru-mirror 目录，每个 PDF 对应一个子文件夹
4. **维护** 一个 state.json 记录每篇的转换状态（成功/失败/跳过）
5. **构建** 一个 index.json，把 Zotero 的元数据（标题、作者、标签、collection）和 MinerU 转换状态交叉引用，供 AI agent 或查询脚本使用

```
Zotero/storage/               mineru-mirror/
├── 3HB4TPVV/                 ├── 3HB4TPVV/
│   └── paper.pdf      ──→    │   └── hybrid_auto/
│                              │       ├── 3HB4TPVV.md
│                              │       └── images/
│                              │           ├── figure1.jpg
│                              │           └── figure2.jpg
├── 4IN7R2D9/                 ├── 4IN7R2D9/
│   └── another.pdf    ──→    │   └── hybrid_auto/
│                              │       ├── 4IN7R2D9.md
│                              │       └── images/...
└── ...                        └── index.json
```

---

## 2. 架构总览

```
                                   ┌───────────────┐
                                   │  config.json  │ ← 所有路径和参数
                                   └───────┬───────┘
                                           │
         ┌──────────────────┬──────────────┼──────────────┬──────────────┐
         ▼                  ▼              ▼              ▼              ▼
    ┌─────────┐      ┌────────────┐  ┌─────────┐  ┌────────────┐  ┌──────────┐
    │ batch.py│      │ watcher.py │  │status.py │  │build_index │  │export_md │
    │(一次性) │      │ (后台守护) │  │(看进度)  │  │  .py       │  │  .py     │
    └────┬────┘      └─────┬──────┘  └──────────┘  └──────┬─────┘  └──────────┘
         │                 │                               │
         ▼                 ▼                               ▼
    ┌──────────────────────────┐                    ┌───────────┐
    │       common.py          │                    │ Zotero    │
    │  (转换引擎 + 状态管理)   │                    │ local API │
    │  - scan_storage()        │                    │ :23119    │
    │  - process_pdf()         │                    └───────────┘
    │  - convert_one()         │
    │  - convert_large_pdf()   │
    │  - start/stop_mineru_api │
    │  - cleanup_deleted       │
    └──────────┬───────────────┘
               │
               ▼
    ┌──────────────────┐
    │   MinerU (CLI    │    输入: PDF 文件
    │   或 API 模式)   │ →  输出: .md + images/
    └──────────────────┘
```

**文件职责一览：**

| 文件 | 用途 |
|------|------|
| `config.json` | 所有路径、参数、开关的集中配置 |
| `common.py` | 共享引擎：PDF 扫描、转换、状态管理、API 生命周期、清理 |
| `batch.py` | 一次性批量转换：扫描 → 转 → 清理 → 重建索引 |
| `watcher.py` | 后台守护：监听文件变化 → 自动转 / 清理 / 重建索引 |
| `status.py` | 仪表盘：一条命令看全局进度 |
| `check-progress.py` | 快速查看 state.json 中各状态的计数 |
| `build_index.py` | 从 Zotero API + state.json 构建 AI 可读的 index.json |
| `zotero_query.py` | 命令行查询 index.json（按 tag / collection / 搜索 / 年份筛选） |
| `export_md.py` | 命令行导出：把符合条件的 MD 复制到指定目录 |
| `export_gui.py` | GUI 版导出工具（Tkinter），支持多条件高级搜索 |
| `audit-orphans.py` | 审计：找出 Zotero storage 中没有 parent item 的孤儿 PDF |
| `audit-trash.py` | 审计：找出进了 Zotero 回收站的 PDF |
| `find-testable.py` | 找出已转换且有 parent item 的条目（用于验证流程） |
| `zotero-action-attach-md.js` | Zotero Actions 插件脚本：把 MD 作为链接附件挂到条目 |
| `zotero-action-md-to-note.js` | Zotero Actions 插件脚本：把 MD 内容导入为 Zotero 笔记 |
| `run-batch.ps1` | PowerShell 快捷入口 → batch.py |
| `start-watcher.ps1` | PowerShell 快捷入口 → watcher.py |
| `status.ps1` | PowerShell 快捷入口 → status.py |
| `export_gui.ps1` | PowerShell 快捷入口 → export_gui.py（用 pythonw 无控制台） |

---

## 3. 前置条件

| 依赖 | 最低版本 | 用途 |
|------|---------|------|
| Python (conda env `mineru`) | 3.11+ | 运行时 |
| `pypdf` | latest | 读取 PDF 页数、分割大 PDF |
| `mineru` | latest | MinerU 本体（PDF → MD 转换引擎） |
| `watchdog` | latest | watcher.py 的文件监控 |
| `httpx` | latest | （可选）API 模式下的 HTTP 客户端 |
| Zotero 桌面版 | ≥ 7.0 | 提供本地 API（端口 23119） |
| Zotero 设置 | — | Edit → Preferences → Advanced → "Allow other applications to communicate with Zotero" 必须**开启** |

**安装命令：**

```powershell
conda activate mineru
pip install pypdf mineru watchdog httpx
```

---

## 4. 配置说明（config.json）

位于 `zotero-mineru\config.json`，所有脚本共用这一个配置文件。

```jsonc
{
  // ===== MinerU 路径 =====
  "mineru_exe":         "C:\\ProgramData\\miniconda3\\envs\\mineru\\Scripts\\mineru.exe",
  "mineru_api_exe":     "C:\\ProgramData\\miniconda3\\envs\\mineru\\Scripts\\mineru-api.exe",

  // ===== API 模式配置（推荐开启）=====
  "use_api": true,              // true = 用 mineru-api 服务模式（模型只加载一次）
  "api_host": "127.0.0.1",
  "api_port": 8000,
  "api_concurrency": 4,         // 最大并发请求数
  "api_render_threads": 16,     // PDF 渲染线程数
  "api_processing_window_size": 32,
  "api_preload": true,          // 启动时预加载 VLM 模型

  // ===== 路径 =====
  "zotero_storage":  "C:\\Users\\Administrator\\Zotero\\storage",       // Zotero 存 PDF 的地方
  "mirror_dir":      "C:\\Users\\Administrator\\Zotero\\mineru-mirror", // 转换产物输出到这里
  "index_file":      "C:\\Users\\Administrator\\Zotero\\mineru-mirror\\index.json",
  "state_file":      "C:\\paper-pipline\\zotero-mineru\\state.json",    // 转换状态记录
  "log_dir":         "C:\\paper-pipline\\zotero-mineru\\logs",

  // ===== 转换参数 =====
  "mineru_extra_args": [],       // 传给 mineru CLI 的额外参数
  "max_retries": 3,              // 失败后最多重试几次
  "convert_timeout_seconds": 1800, // 单篇转换超时（30 分钟）
  "max_pages": 200,              // 超过此页数的 PDF 标记为 skipped_too_large（除非启用 split）
  "split_chunk_pages": 40,       // 大 PDF 分割时每块的页数

  // ===== Watcher 配置 =====
  "stable_seconds": 10,          // PDF 文件大小稳定多久后才处理（防止写入一半就触发）
  "sync_interval_seconds": 300,  // watcher 空闲时每隔多久做一次清理扫描
  "watcher_enabled": true,       // watcher.py 启动时检查此项
  "watcher_auto_convert": false, // false = watcher 只做清理+索引，不自动转换
                                 // true = watcher 也自动转换新 PDF

  // ===== 清理策略 =====
  "skip_trashed": true,          // 跳过 Zotero 回收站里的条目
  "cleanup_deleted": true,       // 清理已删除 PDF 的转换产物
  "cleanup_check_zotero": true,  // 清理前查询 Zotero API 确认状态
  "remove_mirror_on_delete": true, // 清理时同时删除 mirror 目录下的产物

  // ===== 索引 =====
  "rebuild_index_on_change": true,    // 有变化时自动重建索引
  "rebuild_index_after_batch": true,  // batch.py 跑完后自动重建索引
  "index_rebuild_timeout_seconds": 900,

  // ===== Zotero API =====
  "zotero_api_base":   "http://localhost:23119",
  "zotero_library_id": 12146168   // 你的 Zotero userID（见 https://www.zotero.org/settings/keys）
}
```

**你需要改的字段：**

| 字段 | 改什么 |
|------|--------|
| `zotero_storage` | 改成你的 Zotero storage 路径（通常在 `C:\Users\<你的用户名>\Zotero\storage`） |
| `mirror_dir` | MD 输出目录，放在任何你想放的地方 |
| `zotero_library_id` | 你的 Zotero userID，在 https://www.zotero.org/settings/keys 查看 |
| `mineru_exe` / `mineru_api_exe` | 如果 conda env 路径不同，需要改 |

---

## 5. 核心用法

### 5.1 一次性批量转换（batch.py）

**这是最常用的方式**。扫描 Zotero 的所有 PDF，把还没转过的全部转一遍。

```powershell
# 最简单的用法（PowerShell 快捷入口）
cd C:\paper-pipline\zotero-mineru
.\run-batch.ps1

# 或者直接调 Python
C:\ProgramData\miniconda3\envs\mineru\python.exe batch.py
```

**常用参数：**

```powershell
# 先看看有多少需要转的，不实际执行
python batch.py --dry-run

# 只转 3 篇就停（适合测试）
python batch.py --limit 3

# 强制重新转换所有（忽略 state.json 里的 ok 记录）
python batch.py --force

# 只转指定的 Zotero key
python batch.py --key 3HB4TPVV

# 大 PDF 处理策略
python batch.py --large yes    # 直接启用分割模式，不问
python batch.py --large no     # 跳过大 PDF
python batch.py --large ask    # （默认）交互式询问
```

**batch.py 的执行流程：**

```
1. 读 config.json
2. 加载 state.json
3. 如果 --force，清空所有 status
4. 询问是否处理大 PDF（--large 参数控制）
5. 清理：删除已不存在的 PDF 对应的 state 条目和 mirror 产物
6. 扫描 Zotero/storage 下所有 PDF
7. 筛选出需要转换的（needs_conversion）
8. 如果 use_api=true，启动 mineru-api 服务（模型加载一次）
9. 逐个转换：
   - 普通 PDF → convert_one()
   - 大 PDF → convert_large_pdf()（分割+合并）
10. 每转完一篇，立即更新 state.json
11. 关闭 mineru-api
12. 重建 index.json
```

### 5.2 后台守护自动转换（watcher.py）

watcher 持续运行，监听 Zotero storage 目录的文件变化。

```powershell
# PowerShell 快捷入口
.\start-watcher.ps1

# 或直接调
python watcher.py
```

**watcher 做什么：**

- **`watcher_auto_convert=false`（默认）**：只做清理和索引重建，不自动转换 PDF。新 PDF 需要手动跑 `batch.py`。
- **`watcher_auto_convert=true`**：新 PDF 进入 Zotero storage 后自动触发转换。

**watcher 的行为细节：**

| 事件 | watcher 响应 |
|------|-------------|
| 新 PDF 出现 | 等文件大小稳定 → 转换（如果 auto_convert=true）或只刷新索引 |
| PDF 被删除 | 清理对应的 state 条目和 mirror 产物 |
| PDF 被修改 | 重新转换 |
| 空闲超过 sync_interval | 做一次全局清理扫描 |

**参数：**

```powershell
python watcher.py --no-initial-sweep   # 启动时不扫描已有 PDF
python watcher.py --force              # 即使 config 里 watcher_enabled=false 也强制启动
```

### 5.3 查看状态与进度

**仪表盘（推荐）：**

```powershell
.\status.ps1
# 或
python status.py
```

输出包括：
- 各文件的存在状态和最后修改时间
- 转换统计（ok / failed / skipped_too_large / skipped_trashed）
- 索引新鲜度和同步状态
- 最近日志
- 待办事项（需要人干预的事）

**快速进度查看：**

```powershell
python check-progress.py
```

只输出 state.json 的状态统计和所有成功条目的列表。

---

## 6. 索引系统（build_index.py）

index.json 是 AI agent 的"Zotero 导航地图"，把 Zotero 的全部元数据和 MinerU 转换状态合在一起。

**内容结构：**

```json
{
  "generated_at": "2026-05-27T10:30:00",
  "library_id": 12146168,
  "summary": {
    "total_items_in_index": 150,
    "total_collections": 12,
    "total_tags": 45,
    "items_with_md": 130
  },
  "collections": {
    "ABCD1234": {
      "key": "ABCD1234",
      "name": "路由论文",
      "parent": null,
      "children": ["EFGH5678"],
      "path": "路由论文"
    }
  },
  "tags": {
    "100papers": ["KEY1", "KEY2"],
    "路由": ["KEY3", "KEY4"]
  },
  "items": {
    "KEY1": {
      "key": "KEY1",
      "itemType": "journalArticle",
      "title": "Paper Title",
      "creators": [...],
      "year": 2024,
      "abstract": "...",
      "tags": ["100papers"],
      "collections": ["ABCD1234"],
      "attachments": [
        {
          "key": "3HB4TPVV",
          "mineru_status": "ok",
          "md_path": "C:\\...\\mineru-mirror\\3HB4TPVV\\hybrid_auto\\3HB4TPVV.md",
          "page_count": 12
        }
      ],
      "notes": [...]
    }
  }
}
```

**手动重建索引：**

```powershell
python build_index.py

# 自定义参数
python build_index.py --state C:\path\to\state.json --out C:\path\to\index.json
```

**自动重建时机：**
- batch.py 跑完后（如果 `rebuild_index_after_batch=true`）
- watcher 检测到变化后
- export_gui 里点"Rebuild index"按钮

> 注意：构建索引需要 Zotero 桌面版正在运行（要查询 local API），耗时约 3-5 分钟取决于库的大小。

---

## 7. 查询与导出

### 7.1 命令行查询（zotero_query.py）

基于 index.json 的离线查询，Zotero 不需要运行。输出 JSON，适合人看也适合 AI agent 调用。

```powershell
# 列出所有 collection
python zotero_query.py collections

# 列出所有 tag（按使用频率排序）
python zotero_query.py tags
python zotero_query.py tags --min-count 2    # 只看用了 2 次以上的

# 按 tag 筛选论文
python zotero_query.py items --tag 100papers

# 按 collection 筛选
python zotero_query.py items --collection "SatNet"

# 搜索标题/摘要/作者
python zotero_query.py items --search "Hypatia"

# 按年份筛选
python zotero_query.py items --year-min 2020

# 只看有 MD 的
python zotero_query.py items --has-md

# 按作者
python zotero_query.py items --author "Zhang"

# 组合筛选
python zotero_query.py items --tag 路由 --year-min 2020 --has-md

# 查看某篇的完整信息
python zotero_query.py show KEY1

# 只输出 MD 文件路径（方便管道）
python zotero_query.py md-paths --tag 100papers

# 美化输出
python zotero_query.py items --tag 100papers --pretty

# 限制返回数量
python zotero_query.py items --search satellite --limit 10
```

### 7.2 命令行导出（export_md.py）

把符合条件的 MD 文件复制到指定目录，脱离 Zotero 使用。

```powershell
# 平铺导出（一个目录下放所有 .md + .meta.json）
python export_md.py --collection "100papers" --out C:\export\100papers

# Obsidian 风格导出（每篇一个子文件夹）
python export_md.py --tag 路由 --year-min 2020 --out C:\export\routing --layout perdoc

# 包含图片
python export_md.py --tag 路由 --out C:\export\routing --layout perdoc --with-images

# 导出全部有 MD 的
python export_md.py --has-md --out C:\export\all

# 先预览不实际导出
python export_md.py --collection "SatNet" --out C:\tmp --dry-run

# 导出前清空目标目录
python export_md.py --has-md --out C:\export\all --clear
```

**导出产物结构：**

Flat 模式：
```
C:\export\output\
├── 2024 - Paper Title.md
├── 2024 - Paper Title.meta.json
├── 2023 - Another Paper.md
├── 2023 - Another Paper.meta.json
└── manifest.json
```

Perdoc 模式（带 `--with-images`）：
```
C:\export\output\
├── 2024 - Paper Title/
│   ├── 2024 - Paper Title.md
│   ├── meta.json
│   └── images/
│       ├── figure1.jpg
│       └── figure2.jpg
├── 2023 - Another Paper/
│   └── ...
└── manifest.json
```

### 7.3 GUI 导出工具（export_gui.py）

图形化的高级搜索 + 导出界面，类似 Web of Science 的检索条件构建器。

```powershell
# 启动 GUI（用 pythonw 无控制台窗口）
.\export_gui.ps1

# 或直接
C:\ProgramData\miniconda3\envs\mineru\pythonw.exe export_gui.py
```

**GUI 功能：**

- **多条件搜索**：支持 AND / OR 组合，字段包括：
  - Tag（精确匹配 / 包含匹配）
  - Collection
  - 标题包含 / 摘要包含 / 标题或摘要
  - 作者
  - **全文搜索**（搜 MD 内容）
  - 年份范围
- **预览匹配结果**：点"Preview matches"先看有几篇命中
- **导出选项**：Flat / Per-doc 布局，是否包含图片
- **实时状态刷新**：每次搜索都从 state.json 刷新 MinerU 状态
- **Rebuild index**：直接在 GUI 里触发索引重建

---

## 8. Zotero 内集成（Actions 脚本）

需要安装 Zotero 插件 [Actions and Tags](https://github.com/windingwind/zotero-actions-tags)。

### zotero-action-attach-md.js

**功能**：把 MinerU 转换好的 MD 文件作为"链接附件"挂到 Zotero 条目上。

**效果**：在 Zotero 里双击就能打开 MD 文件。

**使用**：
1. 在 Zotero Actions and Tags 插件里新建一个 Action
2. 把 `zotero-action-attach-md.js` 的内容粘贴进去
3. 选中一个或多个条目 → 触发该 Action
4. 脚本会找到每个条目的 PDF 附件 key → 在 mineru-mirror 下找对应的 MD → 挂为链接附件

### zotero-action-md-to-note.js

**功能**：把 MD 内容转成 HTML 导入为 Zotero 笔记。

**效果**：MD 内容直接出现在 Zotero 的笔记面板里，图片通过 `file://` 链接引用本地 mirror 目录。

**使用**：与上面类似，创建 Action → 选中条目 → 触发。如果同名笔记已存在则更新，不会重复创建。

> 两个脚本都要求条目有 parent item。对于 standalone PDF（没有 parent），先在 Zotero 里右键 → "Create Parent Item"。

---

## 9. 审计与清理工具

### audit-orphans.py

找出 Zotero storage 里**没有 parent item 的孤儿 PDF**（standalone attachment）。这些 PDF 通常是刚导入还没被 Zotero 识别元数据的。

```powershell
python audit-orphans.py
```

输出示例：
```
checking 150 attachments...
=== summary ===
orphans (no parent item): 3
parented (proper item)  : 147
errors                  : 0
```

处理方式：在 Zotero 里右键孤儿条目 → "Create Parent Item" 或 "Retrieve Metadata"。

### audit-trash.py

找出虽然物理文件还在 Zotero/storage 里、但在 Zotero 数据库里已经标记为"已删除"（在回收站）的条目。

```powershell
python audit-trash.py
```

batch.py 和 watcher.py 会自动跳过并清理这些条目（如果 `skip_trashed=true`），但这个脚本能让你看到全貌。

### find-testable.py

找出已经成功转换且有 parent item 的条目，输出 Zotero 跳转链接，方便逐篇检查转换质量。

```powershell
python find-testable.py
```

输出：
```
  PDF [3HB4TPVV]  parent [ABCD1234]
    Routing in Satellite Networks
    jump URL: zotero://select/library/items/ABCD1234
```

---

## 10. 大 PDF 处理机制

超过 `max_pages`（默认 200 页）的 PDF 被视为"大 PDF"。

**默认行为**：标记为 `skipped_too_large`，不转换。

**启用分割模式**：
```powershell
python batch.py --large yes
```

**分割流程：**

```
1. 用 pypdf 把大 PDF 物理分割成 split_chunk_pages（默认 40 页）大小的块
2. 每块单独调用 MinerU 转换
3. 转完后合并所有块的 MD 内容：
   - MD 文本按顺序拼接
   - 图片去重（同名同内容只保留一份，名字冲突加 p01_ 前缀）
   - 图片引用路径自动修正
4. 合并结果放到 mineru-mirror/<KEY>/ 下
```

**性能说明**：分割模式下 GPU 仍然是串行的（MinerU 内部有全局锁），c=4 并发只能节省模型加载时间，实际 GPU 推理不能并行。大 PDF 走 API 模式大约比直接 CLI 快 ~11%。

---

## 11. mineru-api 模式详解

config.json 里 `use_api=true` 时，batch.py / watcher.py 会在开始工作前自动启动一个 mineru-api HTTP 服务。

**优势**：MinerU 模型（VLM）只加载一次，后续每篇 PDF 复用已加载的模型，省去反复加载模型的时间。对于小 PDF（<40 页），API 模式比直接调 CLI 快约 **15 倍**。

**生命周期**：
1. batch.py 启动时 → 调用 `start_mineru_api()` → 等 `/health` 返回 200
2. 每篇 PDF 转换时 → mineru CLI 加 `--api-url http://127.0.0.1:8000` 参数
3. batch.py 结束或 Ctrl+C → 调用 `stop_mineru_api()` 优雅关闭

**环境变量（通过 config 控制）**：
- `MINERU_API_MAX_CONCURRENT_REQUESTS` → `api_concurrency`
- `MINERU_PDF_RENDER_THREADS` → `api_render_threads`
- `MINERU_PROCESSING_WINDOW_SIZE` → `api_processing_window_size`

**如果 API 启动失败**（exe 不存在、超时无响应等），自动回退到 legacy 模式（直接调 mineru CLI）。

---

## 12. 数据流与目录结构

```
C:\Users\Administrator\Zotero\
├── storage\                        ← Zotero 管理的 PDF 存储
│   ├── 3HB4TPVV\paper.pdf           每个 PDF 一个 8 字符 key 目录
│   ├── 4IN7R2D9\another.pdf
│   └── ...
│
└── mineru-mirror\                  ← zotero-mineru 的输出
    ├── index.json                    AI 导航索引
    ├── 3HB4TPVV\                     与 storage key 对应
    │   └── hybrid_auto\
    │       ├── 3HB4TPVV.md           转换后的 Markdown
    │       ├── 3HB4TPVV_origin.pdf   MinerU 的原始 PDF 副本
    │       ├── images\                提取的图片
    │       └── *.json                 MinerU 的结构化中间产物
    └── 4IN7R2D9\
        └── ...

C:\paper-pipline\zotero-mineru\
├── state.json                      ← 每篇 PDF 的转换状态
├── logs\
│   ├── 2026-05-26.log                按日期的运行日志
│   ├── 2026-05-27.log
│   └── mineru-api.log                API 服务日志
└── (脚本文件)
```

---

## 13. state.json 状态说明

state.json 以 Zotero attachment key 为键，记录每篇 PDF 的处理状态。

```json
{
  "3HB4TPVV": {
    "pdf_path": "C:\\Users\\Administrator\\Zotero\\storage\\3HB4TPVV\\paper.pdf",
    "pdf_mtime": 1716700000.0,
    "pdf_size": 2345678,
    "page_count": 12,
    "status": "ok",
    "md_path": "C:\\Users\\Administrator\\Zotero\\mineru-mirror\\3HB4TPVV\\hybrid_auto\\3HB4TPVV.md",
    "attempts": 0,
    "last_error": null,
    "last_run": "2026-05-26T15:30:00",
    "elapsed_seconds": 45.2
  }
}
```

**状态值含义：**

| status | 含义 | 下次 batch 行为 |
|--------|------|----------------|
| `ok` | 转换成功 | 跳过（除非 PDF 文件变了或 MD 丢失） |
| `failed` | 转换失败 | 重试（直到达到 max_retries） |
| `skipped_too_large` | 页数超过 max_pages | 跳过（除非用 `--large yes`） |
| `skipped_trashed` | 在 Zotero 回收站 | 每次重新检查（万一用户恢复了） |
| 无记录 | 从未处理 | 转换 |

**判断是否需要重新转换的逻辑**（`needs_conversion()`）：
- 没有 state 条目 → 需要
- PDF 的 mtime 或 size 变了 → 需要（文件被替换了）
- status=ok 但 md_path 指向的文件不存在 → 需要
- status=failed 且 attempts < max_retries → 需要
- status=skipped_too_large → 不需要（config 变了或文件变了才重新评估）
- status=skipped_trashed → 需要（重新检查是否还在回收站）

---

## 14. 常见问题与排查

### "mineru 命令找不到"

```powershell
conda activate mineru
where mineru      # 确认路径
# 然后在 config.json 里写对 mineru_exe
```

### "state.json 标记为已处理，但我想重新转"

```powershell
# 方法 1：强制全部重跑
python batch.py --force

# 方法 2：只重跑一篇
python batch.py --key 3HB4TPVV --force

# 方法 3：手动删 state.json 里对应的条目
```

### "watcher 启动后说 disabled"

config.json 里 `watcher_enabled` 要设成 `true`。或者用 `--force` 参数强制启动。

### "Zotero local API not reachable"

1. 确认 Zotero 桌面版在运行
2. 确认 Edit → Preferences → Advanced → "Allow other applications..." 已开启
3. 测试：`curl http://localhost:23119/api/users/<你的ID>/items?limit=1`

### "转换后 MD 是空的或乱码"

- 检查原始 PDF 是否是扫描件（纯图片没有文字层）→ 先在 Zotero 里右键 OCR
- 检查 logs 目录下的日志看 MinerU 的错误信息
- 试试单独跑 MinerU CLI：`mineru -p input.pdf -o output/`

### "index.json 里看不到新转的论文"

- 跑完 batch.py 后通常自动重建，如果没有：`python build_index.py`
- 重建需要 Zotero 在跑

### "watcher_auto_convert 和 batch.py 冲突吗？"

不冲突。两者共享同一个 state.json，互相尊重对方写入的状态。watcher 处理每个 PDF 前会重新 load state，如果 batch 已经转过了就跳过。

### Windows 路径过长

MinerU 输出子目录名 = 输入 PDF 的文件名。中文长标题的论文可能导致路径超过 260 字符。代码已有 workaround：把 PDF 复制为短名（用 8 字符 key）后再喂给 MinerU。

---

## 15. 完整命令速查表

```powershell
# ============ 切换到工作目录 ============
cd C:\paper-pipline\zotero-mineru

# ============ 批量转换 ============
.\run-batch.ps1                           # 一次性转换全部未处理的 PDF
python batch.py --dry-run                 # 预览：哪些会被转
python batch.py --limit 5                 # 只转 5 篇
python batch.py --force                   # 全部强制重转
python batch.py --key ABCD1234            # 只转指定 key
python batch.py --large yes               # 启用大 PDF 分割模式

# ============ 后台守护 ============
.\start-watcher.ps1                       # 启动 watcher
python watcher.py --force                 # 即使 config 禁用也启动
python watcher.py --no-initial-sweep      # 不扫描已有 PDF

# ============ 查看状态 ============
.\status.ps1                              # 全面仪表盘
python check-progress.py                  # 快速统计

# ============ 索引 ============
python build_index.py                     # 手动重建索引

# ============ 查询 ============
python zotero_query.py collections                          # 列出 collection
python zotero_query.py tags                                 # 列出 tag
python zotero_query.py items --tag 100papers --pretty       # 按 tag 查
python zotero_query.py items --search "routing" --has-md    # 搜索有 MD 的
python zotero_query.py show KEY1 --pretty                   # 查看某篇详情
python zotero_query.py md-paths --collection "SatNet"       # 输出 MD 路径

# ============ 导出 ============
python export_md.py --tag 路由 --out C:\export\routing --layout perdoc --with-images
python export_md.py --has-md --out C:\export\all --dry-run
.\export_gui.ps1                          # GUI 导出

# ============ 审计 ============
python audit-orphans.py                   # 找无 parent 的孤儿 PDF
python audit-trash.py                     # 找回收站里的 PDF
python find-testable.py                   # 找可以验证转换质量的条目
```
