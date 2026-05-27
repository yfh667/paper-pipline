# paper-fetcher 使用指南

> 从一坨杂乱的"想读论文"笔记，全自动清洗 → 按出版商抓 PDF → 推入 Zotero。

---

## 目录

1. [这个工具是干什么的](#1-这个工具是干什么的)
2. [架构总览](#2-架构总览)
3. [前置条件](#3-前置条件)
4. [完整流程图](#4-完整流程图)
5. [第一步：清洗（clean_list.py）](#5-第一步清洗clean_listpy)
6. [第二步：AI / 人工决策（apply_decisions.py）](#6-第二步ai--人工决策apply_decisionspy)
7. [第三步：抓 PDF（run.py）](#7-第三步抓-pdfrunpy)
8. [第四步：推入 Zotero（import_to_zotero.py）](#8-第四步推入-zoteroimport_to_zoteropy)
9. [四个 Handler 详解](#9-四个-handler-详解)
   - [9.1 IEEE Xplore（ieee.py）](#91-ieee-xploreieeepy)
   - [9.2 ACM Digital Library（acm.py）](#92-acm-digital-libraryacmpy)
   - [9.3 ScienceDirect / Elsevier（elsevier.py + Node）](#93-sciencedirect--elsevierelsevierpy--node)
   - [9.4 Optica Publishing（optica.py）](#94-optica-publishingopticapy)
10. [输入输出文件格式](#10-输入输出文件格式)
11. [目录结构](#11-目录结构)
12. [DOI 前缀 → 出版商映射表](#12-doi-前缀--出版商映射表)
13. [反爬对策与已知行为](#13-反爬对策与已知行为)
14. [常见问题与排查](#14-常见问题与排查)
15. [完整命令速查表](#15-完整命令速查表)

---

## 1. 这个工具是干什么的

你日常攒了一个 txt 文件（或者剪贴板笔记），里面堆着几十上百条"想读的论文"——有的是英文标题、有的带中文注释、有的是 URL、有的甚至是同事发来的乱码。

paper-fetcher 做的事：

1. **清洗**：把杂乱笔记解析成结构化的 `[publisher] 标题 (doi=xxx)` 格式，通过 CrossRef API 自动查 DOI 和出版商
2. **AI 辅助**：对 CrossRef 拿不准的条目，生成 review.json 让 AI / 人做最终判断
3. **抓 PDF**：按出版商分流，四个 handler 并行抓取（IEEE / ACM / ScienceDirect / Optica）
4. **推 Zotero**：把抓到的 PDF 通过 Zotero 本地 API 推入桌面版，自动识别元数据

```
 杂乱 txt          clean_list.py         AI/人决策          run.py            import_to_zotero.py
 ─────── ──→ clean.txt + review.json ──→ decisions.json ──→ PDF 文件 ──→ Zotero 桌面
```

---

## 2. 架构总览

```
                          ┌───────────────┐
                          │ 杂乱 messy.txt│
                          └───────┬───────┘
                                  │
                                  ▼
                      ┌───────────────────────┐
                      │  clean_list.py        │  CrossRef API 查 DOI
                      │  (确定性清洗脚本)      │  1s/req polite 间隔
                      └───────┬───────┬───────┘
                              │       │
                              ▼       ▼
               paperlist_clean.txt   paperlist_review.json
               (机器搞定的)          (拿不准的 → AI/人)
                              │       │
                              │       ▼
                              │  ┌──────────────────────┐
                              │  │  apply_decisions.py   │
                              │  │  (AI 给的 decisions   │
                              │  │   合并回 clean.txt)   │
                              │  └──────────┬───────────┘
                              │             │
                              ◄─────────────┘
                              │
                              ▼
                      ┌───────────────────────┐
                      │      run.py           │  async 调度器
                      │   (CLI 主入口)        │
                      └───────┬───────────────┘
                              │
              ┌───────┬───────┼───────┬──────────┐
              ▼       ▼       ▼       ▼          ▼
          ┌──────┐┌──────┐┌────────┐┌──────┐ ┌─────────┐
          │ IEEE ││ ACM  ││Elsevier││Optica│ │ manual/ │
          │(HTTP)││(uc)  ││(Node)  ││(uc)  │ │needs_   │
          └──┬───┘└──┬───┘└───┬────┘└──┬───┘ │manual   │
             │       │        │        │     │.txt     │
             ▼       ▼        ▼        ▼     └─────────┘
        output/   output/  output/  output/
        ieee/     acm/     sd/      optica/
           │       │        │        │
           └───────┴────────┴────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │ import_to_zotero.py   │  POST /connector/saveStandaloneAttachment
              │ (推入 Zotero 桌面)    │  :23119
              └───────────────────────┘
```

**并发模型**：四个 publisher handler 并行运行（不同出版商之间互不干扰），每个 handler 内部串行（同一出版商的论文按顺序抓，间隔 60 秒防反爬）。

**文件职责一览：**

| 文件 | 用途 |
|------|------|
| `clean_list.py` | 杂乱 txt → 结构化清单 + CrossRef 查 DOI |
| `apply_decisions.py` | 把 AI/人写的 decisions.json 合并到 clean.txt |
| `run.py` | CLI 主入口：读清单 → 分流 → 并行抓 PDF |
| `core.py` | async 调度引擎：按 tag 分组 → 每组一个协程 → 串行执行 |
| `import_to_zotero.py` | 把 output 里的 PDF 推入本地 Zotero |
| `handlers/base.py` | Job 数据模型 + PublisherHandler 抽象基类 |
| `handlers/ieee.py` | IEEE Xplore handler（纯 HTTP requests + stamp.jsp） |
| `handlers/acm.py` | ACM DL handler（undetected-chromedriver 过 Cloudflare） |
| `handlers/elsevier.py` | ScienceDirect handler（subprocess 调 Node 脚本） |
| `handlers/optica.py` | Optica handler（undetected-chromedriver 过 Turnstile） |
| `sd-fetch-node/fetch-one.mjs` | Node 版 SD 抓取脚本（puppeteer-extra + stealth 插件） |
| `AI_WORKFLOW.md` | AI 清洗决策的操作手册（给 Sonnet/Haiku 看的 prompt 规范） |

---

## 3. 前置条件

| 依赖 | 版本 | 用途 |
|------|------|------|
| Python (conda env `mineru`) | 3.11+ | 运行时 |
| `requests` | latest | IEEE handler / CrossRef 查询 / Zotero 推送 |
| `undetected-chromedriver` | latest | ACM + Optica handler（过 Cloudflare / Turnstile） |
| Node.js | ≥ 18 | ScienceDirect handler 的 puppeteer |
| `puppeteer-core` / `puppeteer-extra` / `stealth` | (在 sd-fetch-node/) | SD 专用，`npm install` 装齐 |
| Google Chrome | latest | ACM/Optica 的 undetected-chromedriver 和 Node puppeteer 都调系统 Chrome |
| Zotero 桌面版 | ≥ 7.0 | import_to_zotero.py 需要 |

**安装命令：**

```powershell
# Python 依赖
conda activate mineru
pip install requests undetected-chromedriver

# Node 依赖
cd C:\paper-pipline\paper-fetcher\sd-fetch-node
npm install
```

---

## 4. 完整流程图

```
         [用户]
           │  把 messy.txt 丢到 paper-fetcher/input/
           ▼
┌─────────────────────────────────────────┐
│  python clean_list.py input/messy.txt   │
│  (CrossRef 查 DOI，~1s/条，100 条约 2min)│
└──────────────────┬──────────────────────┘
                   │
          ┌────────┴────────┐
          ▼                 ▼
 paperlist_clean.txt   paperlist_review.json
   (机器搞定的)          (机器拿不准的)
                            │
                            ▼
         [AI / 人 看 review.json，写 decisions.json]
          规则见 AI_WORKFLOW.md
                            │
                            ▼
┌──────────────────────────────────────────────┐
│ python apply_decisions.py output/decisions.json │
└──────────────────┬───────────────────────────┘
                   │
                   ▼
   paperlist_clean.txt（更全） + review.json（缩到只剩 manual）
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│ python run.py output/paperlist_clean.txt --skip-existing │
│ (四个 publisher 并行，各 60s 间隔)                        │
└──────────────────┬──────────────────────────────────────┘
                   │
          ┌────────┼────────┬──────────┐
          ▼        ▼        ▼          ▼
     output/   output/   output/   output/
     ieee/     acm/      sd/       optica/
          └────────┼────────┴──────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────┐
│ python import_to_zotero.py                        │
│ (Zotero 桌面 app 必须开着；                        │
│  建议先在 UI 里选中目标 collection)                 │
└──────────────────────────────────────────────────┘
                   │
                   ▼
         Zotero 桌面 app
         自动：PDF → 识别元数据 → journalArticle
```

---

## 5. 第一步：清洗（clean_list.py）

把杂乱的论文笔记变成结构化的清单，是整条流水线的起点。

### 基本用法

```powershell
cd C:\paper-pipline\paper-fetcher
python clean_list.py input\messy.txt
```

### 它做了什么（全自动，无需 AI）

1. **按段落切分** → 逐段提取 URL / DOI 字面值 / 候选英文标题
2. **去除噪音** → markdown 装饰（`**`、`#`、链接语法）、中文注释尾巴、命令行残留
3. **DOI → CrossRef 反查**：找到的 DOI → 查标题和出版商
4. **标题 → CrossRef 搜索**：找到的英文标题 → CrossRef 模糊搜索 → 高置信度（≥85% 相似度）自动采纳到 clean.txt
5. **不确定的 → review.json**：CrossRef 多个相近候选 / 完全没匹配 / 未知域名 URL

### 参数

```powershell
python clean_list.py input\messy.txt                  # 默认输出到 output/
python clean_list.py input\messy.txt --out my_clean.txt --review my_review.json
python clean_list.py input\messy.txt --no-crossref     # 跳过 CrossRef（所有标题 → review）
python clean_list.py input\messy.txt --crossref-gap 2  # CrossRef 间隔改成 2 秒
```

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `input` | (必填) | 杂乱 txt 路径 |
| `--out` | `output/paperlist_clean.txt` | 清洗后的输出 |
| `--review` | `output/paperlist_review.json` | 拿不准的条目 |
| `--log` | `output/clean.log` | 清洗日志 |
| `--no-crossref` | false | 不调 CrossRef，标题全部归入 review |
| `--crossref-gap` | 1.0 | CrossRef API 请求间隔（秒） |

### 输入支持的格式

messy.txt 可以包含任意混合格式，脚本会自动识别：

```
# 这些全都能被正确解析：

Routing in Satellite Networks: A Survey
https://ieeexplore.ieee.org/document/12345678
10.1109/TCOM.2024.1234567
**CMAP: Certificate-less MQTT-based Authentication Protocol** 这篇讲物联网的认证

LEO Constellation Design for Global Internet Access 一篇关于 LEO 星座设计的论文
https://dl.acm.org/doi/10.1145/3456789.1234567
https://www.sciencedirect.com/science/article/pii/S0140366424001234
```

### CrossRef polite pool 规范

脚本的 HTTP User-Agent 里带了 `mailto:` 字段，这样 CrossRef 会走 polite pool（响应更快）。每次请求间隔 1 秒是 CrossRef 的底线要求。

### 输出示例

**paperlist_clean.txt**：
```
[acm] A Survey on Routing in LEO Satellite Networks  (doi=10.1145/3456789.1234567)
[elsevier] Link Planning for LEO Satellite Constellation  (doi=10.1016/j.comnet.2024.123456)
[ieee] Routing in Satellite Networks  (doi=10.1109/TCOM.2024.1234567)
```

**paperlist_review.json**：
```json
[
  {
    "kind": "title",
    "title": "CMAP: Certificate-less MQTT-based Authentication Protocol",
    "top_score": 0.602,
    "candidates": [
      {"doi": "10.1109/access.2026.3684371", "title": "CMAP: Certificateless...", "publisher": "IEEE", "score": 60.2},
      {"doi": "10.1007/s13369-023-08047-6", "title": "CMAP-IoT: Chaotic Map...", "publisher": "Springer", "score": 37.3}
    ]
  },
  {
    "kind": "url",
    "url": "https://kluedo.ub.rptu.de/frontdoor/deliver/...",
    "reason": "unknown domain"
  }
]
```

---

## 6. 第二步：AI / 人工决策（apply_decisions.py）

review.json 里是 clean_list.py 拿不准的条目。需要 AI 或人来做判断，写成 decisions.json。

### decisions.json 格式

```json
{
  "accepts": [
    {
      "match": "CMAP: Certificate-less",
      "tag": "ieee",
      "title": "CMAP: Certificateless MQTT-Based Authentication Protocol for Medical IoT",
      "doi": "10.1109/access.2026.3684371"
    }
  ],
  "noise": [
    {"match": "wikipedia.org/wiki/Guowang"},
    {"match": "scholar.google.com/citations"}
  ],
  "manual": [
    {
      "match": "Starlink Constellation: Deployment",
      "reason": "no good CrossRef match; likely too recent"
    }
  ]
}
```

**三个桶的含义：**

| 桶 | 含义 | 效果 |
|----|------|------|
| `accepts` | AI/人确认了正确的匹配 | 追加到 clean.txt，从 review.json 删除 |
| `noise` | 不是论文，丢弃 | 从 review.json 删除 |
| `manual` | 真不确定，留给人 | 在 review.json 里标记 `_manual`，置顶 |

### match 字段语义

`match` 是**子串匹配**（不区分大小写），脚本会拼接 review 条目的所有文本（title + url + 候选的 title + doi）做 substring search。写法：

- 写条目里独有的一段文本即可
- 不要太短（会误中）也不要太长（可能被标点差异打断）

### 用法

```powershell
python apply_decisions.py output\decisions.json

# 自定义路径
python apply_decisions.py my_decisions.json --clean output\paperlist_clean.txt --review output\paperlist_review.json
```

apply_decisions 是**幂等的**（clean.txt 内部用 set 去重），多次运行安全。

### AI 决策的判断标准（详见 AI_WORKFLOW.md）

**归 accepts 的信号：**
- 候选 #1 标题跟查询标题几乎一样（只差 hyphen/空格/大小写，如 `Certificate-less` vs `Certificateless`）
- 候选 #1 的 score 是 #2 的 1.5× 以上，且话题一致
- 候选 #1 的出版商跟标题主题契合

**归 noise 的信号：**
- Wikipedia / GitHub / Bilibili / Notion / Google Scholar 作者页
- 重复条目、加密过的链接

**归 manual 的信号：**
- 候选全部不相关
- 论文太新 CrossRef 没收录
- 标题被截断只有部分

---

## 7. 第三步：抓 PDF（run.py）

读取清洗后的清单，按出版商分流，并行抓取 PDF。

### 基本用法

```powershell
# 标准用法（跳过已经下载过的）
python run.py output\paperlist_clean.txt --skip-existing

# 不跳过，全部重抓
python run.py output\paperlist_clean.txt
```

### 参数

| 参数 | 说明 |
|------|------|
| `list` | (必填) 清洗后的 paper list 文件路径 |
| `--skip-existing` | 如果 output 目录下已有同名 PDF，跳过不重抓 |

### 执行流程

1. 逐行解析输入文件（格式：`[tag] title  (doi=xxx)`）
2. tag 在 `REGISTRY` 里的（ieee/acm/elsevier/optica）→ 创建 Job
3. tag 不在 REGISTRY 里的，或 doi 为空 → 写入 `output/manual/needs_manual.txt`
4. Job 按 tag 分组 → 每组启动一个 async 协程
5. 四个协程并行运行，组内串行，每篇间隔 `gap_seconds`（60 秒）
6. 结果汇总：OK / FAIL 统计 + 日志

### 日志

运行日志写到 `output/logs/run-YYYYMMDD-HHMMSS.log`，同时输出到控制台。

### 时间估算

每篇论文 ~70-100 秒（60 秒间隔 + 10-40 秒下载）。因为四个 publisher 并行，总时间取决于最长的那个队列：

| 场景 | 大约耗时 |
|------|---------|
| 9 篇 (3 IEEE + 3 ACM + 3 SD) | ~12 分钟 |
| 30 篇 (10 IEEE + 10 ACM + 10 SD) | ~20 分钟 |
| 100 篇 (50 IEEE + 30 ACM + 20 SD) | ~60 分钟 |

### PDF 文件命名

文件名 = 论文标题（去掉 Windows 非法字符，截到 140 字符）+ `.pdf`。不是 DOI 命名。

---

## 8. 第四步：推入 Zotero（import_to_zotero.py）

把 output/{ieee,acm,sd,optica} 下的 PDF 通过 Zotero 本地 API 推入桌面版。

### 前提

- Zotero 桌面版**正在运行**
- Edit → Preferences → Advanced → "Allow other applications to communicate with Zotero" **已开启**
- （推荐）在 Zotero UI 里先选中你想放 PDF 的 collection

### 基本用法

```powershell
python import_to_zotero.py                  # 导入所有新 PDF
python import_to_zotero.py --limit 1        # 先导入 1 篇测试
python import_to_zotero.py --dry-run        # 预览会导入哪些
```

### 参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--limit` | 0 | 最多导入几篇（0 = 全部） |
| `--dry-run` | false | 只列出会被导入的 PDF，不实际上传 |
| `--no-dedupe` | false | 不做 MD5 去重（默认会查 Zotero 已有的附件 MD5） |
| `--gap` | 2.0 | 两次上传之间的间隔秒数（让 Zotero 有时间处理） |

### 工作原理

1. 扫描 `output/{ieee,acm,sd,optica}/*.pdf`
2. 查询 Zotero 已有附件的 MD5 → 跳过重复
3. 逐个 POST 到 `http://127.0.0.1:23119/connector/saveStandaloneAttachment`
4. Zotero 收到后自动：
   - 复制 PDF 到 `Zotero/storage/<KEY>/`
   - 从 PDF 文本提取 DOI → 查 CrossRef/DOI.org → 创建完整的 journalArticle/conferencePaper 父条目
   - 条目进入当前选中的 collection（如果没选中则进 Unfiled Items）

### 注意事项

- **新条目进哪个 collection？** 进你 Zotero UI 当前选中的那个。所以跑之前请在 Zotero 左边栏点一下目标 collection。
- **元数据识别需要几秒**：上传后 Zotero 后台会自动识别，稍等几秒 PDF 就会变成完整的文献条目。
- **扫描件（纯图片 PDF）** 不能自动识别元数据 → 右键 → "Retrieve Metadata" 或手动填。
- 日志写到 `output/logs/zotero_import.log`。

---

## 9. 四个 Handler 详解

### 9.1 IEEE Xplore（ieee.py）

**技术方案**：纯 HTTP（`requests` 库），不需要浏览器。

**抓取流程：**

```
DOI
  │  requests.get("https://doi.org/{doi}")  → 跟随重定向
  ▼
ieeexplore.ieee.org/document/{arnumber}/
  │  提取 arnumber
  ▼
/stamp/stamp.jsp?arnumber={arnum}           → 设置 Akamai 认证 cookie
  ▼
/stampPDF/getPDF.jsp?arnumber={arnum}       → PDF 字节流
  ▼
output/ieee/{title}.pdf
```

**反爬对策：**
- Akamai CDN 偶尔返回 "APM_DO_NOT_TOUCH" HTML 挑战页
- 处理方式：自动 sleep 90 秒 → 重建 HTTP session（清 cookie）→ 重试（最多 2 次）

**关键参数：**

| 参数 | 值 | 说明 |
|------|-----|------|
| `gap_seconds` | 60 | 两篇之间间隔 |
| `HTML_RETRY_SLEEP` | 90 | APM 挑战后等待秒数 |
| `MAX_ATTEMPTS` | 2 | 最大重试次数 |

### 9.2 ACM Digital Library（acm.py）

**技术方案**：`undetected-chromedriver`（真实 Chrome 浏览器，过 Cloudflare）。

**为什么不用 requests？** ACM DL 全站 Cloudflare 保护，普通 HTTP 请求直接被拦。

**抓取流程：**

```
DOI
  │  Chrome 打开 dl.acm.org/doi/{doi}
  ▼
等 Cloudflare "Just a moment..." 页面消失（最多 60 秒）
  ▼
导航到 dl.acm.org/doi/pdf/{doi}  → 触发 PDF 下载
  ▼
监听临时目录 _acm_dl_tmp/ 等 .pdf 出现（120 秒超时）
  ▼
移动到 output/acm/{title}.pdf
```

**反爬对策：**
- Cloudflare 可能卡住不放行
- 处理方式：kill Chrome driver → sleep 90 秒 → 重启 driver → 重试（最多 2 次）

**关键参数：**

| 参数 | 值 | 说明 |
|------|-----|------|
| `gap_seconds` | 60 | 两篇之间间隔 |
| `CLOUDFLARE_WAIT_SEC` | 60 | 等 Cloudflare 放行的超时 |
| `DOWNLOAD_TIMEOUT` | 120 | 等 PDF 下载完成的超时 |
| `RETRY_BACKOFF_SEC` | 90 | 重试前等待 |
| `MAX_ATTEMPTS` | 2 | 最大重试次数 |

### 9.3 ScienceDirect / Elsevier（elsevier.py + Node）

**技术方案**：Python handler 壳 + Node.js 实际抓取（puppeteer-extra + stealth 插件）。

**为什么用 Node 不用 Python？** ScienceDirect 的 WAF 极其敏感。我们试过 Python 的 `playwright-stealth`，被 SD 识破了。只有 Node 的 `puppeteer-extra-plugin-stealth` 能稳定绕过。

**抓取流程（Node fetch-one.mjs）：**

```
DOI
  │  puppeteer 打开 https://doi.org/{doi}  → 重定向到 SD 文章页
  ▼
等全文 section 渲染（检测 Introduction / Methods / Results 等 h2 标题出现）
  │  最多等 90 秒
  ▼
反爬检测：如果页面包含 "are you a robot" / "access denied" → 报错退出
  ▼
展开折叠内容（accordion / show-more 按钮）
  ▼
滚动整页（触发懒加载的图片和引用）
  ▼
移除干扰层（popover / sticky bar / Reading Assistant / cookie 横幅）
  ▼
page.pdf() 打印成 A4 PDF
  ▼
output/sd/{title}.pdf
```

**关键参数：**

| 参数 | 值 | 说明 |
|------|-----|------|
| `gap_seconds` | 60 | 两篇之间间隔（底线值，别再低了） |
| `NODE_TIMEOUT` | 300 | Node 进程超时（秒） |
| Node `NAV_TIMEOUT_MS` | 120,000 | 页面导航超时 |
| Node `BODY_WAIT_MS` | 90,000 | 等全文加载超时 |

**特别注意：**
- **60 秒间隔是底线**。更短的间隔会触发 SD WAF，IP 进观察池。
- 一旦被 "are you a robot" 拦截，**唯一办法是等 30-60 分钟**。
- **别同时跑多个 SD 实例**，别紧密重试。

### 9.4 Optica Publishing（optica.py）

**技术方案**：`undetected-chromedriver`（与 ACM handler 类似）。

**抓取流程：**

```
DOI (10.1364/...)
  │  Chrome 打开 https://doi.org/{doi}  → opg.optica.org/*/abstract.cfm?uri=...
  ▼
等 Cloudflare Turnstile 通过（60 秒超时）
  │  从 URL / page source 提取 URI（如 jocn-18-6-614）
  ▼
导航到 /viewmedia.cfm?uri={URI}&seq=0  → 触发 PDF 下载
  │  如果首次失败，尝试 &r=1 备用 URL
  ▼
监听 _optica_dl_tmp/ 等 .pdf 出现（120 秒超时）
  ▼
移动到 output/optica/{title}.pdf
```

**反爬对策：**
- Cloudflare Turnstile challenge（undetected-chromedriver 的真实 Chrome 自动解决）
- PDF 页可能也有 Turnstile → 等待 + 备用 URL 重试

---

## 10. 输入输出文件格式

### 输入：clean.txt 行格式

```
[tag] Paper Title Here  (doi=10.xxxx/yyyy.zzzz)
```

- `[tag]`：出版商短标签，`ieee` / `acm` / `elsevier` / `optica` 会被自动抓取
- 其他 tag（`springer` / `wiley` / `spie` 等）→ 归入 `needs_manual.txt`
- `doi=` 为空的行 → 也归入 `needs_manual.txt`

### 输出目录

| 路径 | 内容 |
|------|------|
| `output/ieee/*.pdf` | IEEE Xplore 下载的 PDF |
| `output/acm/*.pdf` | ACM DL 下载的 PDF |
| `output/sd/*.pdf` | ScienceDirect 下载的 PDF |
| `output/optica/*.pdf` | Optica 下载的 PDF |
| `output/manual/needs_manual.txt` | 不在四大出版商的条目 |
| `output/paperlist_clean.txt` | 清洗后的完整清单 |
| `output/paperlist_review.json` | 待 AI/人决策的条目 |
| `output/clean.log` | clean_list.py 运行日志 |
| `output/logs/run-*.log` | run.py 运行日志 |
| `output/logs/zotero_import.log` | import_to_zotero.py 日志 |

---

## 11. 目录结构

```
paper-fetcher/
├── README.md                    ← 本文档
├── AI_WORKFLOW.md               ← AI 决策操作手册
├── run.py                       ← CLI 主入口（并行抓 PDF）
├── core.py                      ← async 调度器
├── clean_list.py                ← 杂乱 txt → 结构化清单 + CrossRef 查 DOI
├── apply_decisions.py           ← AI 给的 decisions.json → 合并到 clean.txt
├── import_to_zotero.py          ← 把 PDF 推入本地 Zotero
├── handlers/
│   ├── __init__.py              ← handler 注册表（REGISTRY）
│   ├── base.py                  ← Job 数据模型 + PublisherHandler 抽象基类
│   ├── ieee.py                  ← IEEE Xplore：requests + stamp.jsp
│   ├── acm.py                   ← ACM DL：undetected-chromedriver（过 Cloudflare）
│   ├── elsevier.py              ← ScienceDirect：subprocess 调 Node
│   └── optica.py                ← Optica：undetected-chromedriver（过 Turnstile）
├── sd-fetch-node/
│   ├── fetch-one.mjs            ← Node 版 SD 抓取脚本
│   ├── package.json
│   └── node_modules/            ← npm install 后生成
├── input/                       ★ 把杂乱 txt 丢这里 ★
│   └── (messy.txt)
└── output/                      ← 所有产物（.gitignore 排除大部分）
    ├── paperlist_clean.txt
    ├── paperlist_review.json
    ├── decisions.json
    ├── clean.log
    ├── ieee/                    ← IEEE PDF
    ├── acm/                     ← ACM PDF
    ├── sd/                      ← SD PDF
    ├── optica/                  ← Optica PDF
    ├── manual/
    │   └── needs_manual.txt     ← 需要手动处理的
    ├── _acm_dl_tmp/             ← ACM 下载暂存（自动清理）
    ├── _optica_dl_tmp/          ← Optica 下载暂存（自动清理）
    └── logs/
        ├── run-YYYYMMDD-HHMMSS.log
        └── zotero_import.log
```

---

## 12. DOI 前缀 → 出版商映射表

clean_list.py 用这个表把 DOI 分类到对应的 publisher tag：

| DOI 前缀 | Tag | 能自动抓 |
|----------|-----|---------|
| `10.1109/` | ieee | Yes |
| `10.1145/` | acm | Yes |
| `10.5555/` | acm | Yes |
| `10.1016/` | elsevier | Yes |
| `10.1364/` | optica | Yes |
| `10.1007/` | springer | No → manual |
| `10.1002/` | wiley | No → manual |
| `10.3389/` | frontiers | No → manual |
| `10.3390/` | mdpi | No → manual |
| `10.1117/` | spie | No → manual |
| `10.3233/` | ios-press | No → manual |
| `10.34133/` | science-partner | No → manual |
| `10.36227/` | techrxiv | No → manual |

只有 `ieee` / `acm` / `elsevier` / `optica` 四个 tag 有对应的自动 handler，其他出版商的条目会被 run.py 写入 `needs_manual.txt`。

URL 域名也有类似的映射（用于清洗步骤识别 URL 来源）：

| 域名 | Tag |
|------|-----|
| `ieeexplore.ieee.org` | ieee |
| `dl.acm.org` | acm |
| `sciencedirect.com` | elsevier |
| `opg.optica.org` | optica |
| `link.springer.com` | springer |
| `arxiv.org` | arxiv |
| ...等 | ... |

---

## 13. 反爬对策与已知行为

### IEEE Xplore

- **风险**：Akamai CDN 偶尔返回 "APM HTML 挑战页"
- **自动处理**：sleep 90s → 换 session → 重试 1 次
- **人工干预**：如果连续多篇失败 → 暂停 10 分钟再来
- **TechRxiv 坑**：DOI `10.36227/...` 被 CrossRef 标成 "IEEE"，但实际不在 ieeexplore 上。IEEE handler 会报 "no arnumber in landing url"。这些条目会自动归入 manual。

### ACM Digital Library

- **风险**：Cloudflare 拦截
- **自动处理**：重启 Chrome driver + sleep 90s → 重试 1 次
- **人工干预**：换时间段再试

### ScienceDirect（最严格）

- **风险**：SD WAF 极其敏感
- **自动处理**：检测到 "are you a robot" 等文本 → 立即报错退出（不自动重试，避免加重 IP 封禁）
- **关键规则**：
  - 60 秒/篇的间隔是底线，**别缩短**
  - **别同时跑多个 SD 实例**
  - **别紧密重试**
  - 一旦撞 WAF → **停手等 30-60 分钟**，期间别再碰 SD
  - 别在跑批的时候改 `fetch-one.mjs`
- **Python stealth 不行**：试过 playwright-stealth，被 SD 识破了，只能用 Node 的 puppeteer-extra-plugin-stealth

### Optica

- **风险**：Cloudflare Turnstile challenge
- **自动处理**：undetected-chromedriver 的真实 Chrome 自动解决 Turnstile；如果卡住 → 重启 driver + sleep 90s → 重试 1 次

### 通用规则

- 所有 handler 的 `gap_seconds = 60`，这是踩坑后确定的最低值
- 三个浏览器类 handler（ACM/Optica/SD）各自独立的 Chrome 实例，互不干扰
- 日志合在一个文件里（`output/logs/run-*.log`），按时间戳区分

---

## 14. 常见问题与排查

### Zotero 相关

| 症状 | 原因 | 处理 |
|------|------|------|
| `Zotero local API not reachable` | Zotero 没开 / 端口被挡 / 设置没开 | 启动 Zotero → Edit → Preferences → Advanced → 勾上"Allow other apps" |
| 上传后条目没元数据 | PDF 是扫描件没文字层 / Zotero 识别慢 | 等 10 秒；扫描件需先 OCR |
| 条目进了 Unfiled Items | 没选中目标 collection | 先在 Zotero UI 点一下目标 collection 再跑 import |
| PowerShell 的 `Invoke-WebRequest` 报错 | Zotero 返回 HTTP/1.0，PowerShell 不处理 | 用 Python requests 或 curl |

### Handler 相关

| 症状 | 原因 | 处理 |
|------|------|------|
| IEEE `no arnumber in landing url` | TechRxiv preprint 或非 IEEE 文章 | 正常行为，归入 manual |
| IEEE `APM HTML challenge` 连续失败 | Akamai 限速 | 暂停 10 分钟 |
| ACM `cloudflare stuck` | CF 不放行 | 换时间段；检查 Chrome 版本 |
| SD `anti-bot blocked: are you a robot` | IP 进了 WAF 名单 | **停手等 30-60 分钟** |
| Optica `turnstile stuck` | Turnstile 不过 | 重启脚本；换时间段 |
| `node not available` | Node.js 没装 / 不在 PATH | 装 Node ≥ 18，确认 `where node` |
| `Node fetch script missing` | sd-fetch-node 没 npm install | `cd sd-fetch-node && npm install` |

### 清洗相关

| 症状 | 原因 | 处理 |
|------|------|------|
| CrossRef 查出来的标题不对 | CrossRef 模糊搜索不准确 | 正常行为，归入 review.json 让 AI/人判断 |
| review.json 里条目太多 | 输入格式太乱 / 太多中文标题 | 预处理 txt 让每行一篇英文标题效果最好 |
| clean.txt 有重复 | 不会，脚本内部去重了 | — |
| `--skip-existing` 没跳过旧 PDF | 旧 PDF 可能是 DOI 命名，现在改成标题命名了 | 删掉旧文件或不用 --skip-existing |

---

## 15. 完整命令速查表

```powershell
# ============ 切换到工作目录 ============
cd C:\paper-pipline\paper-fetcher

# ============ 第一步：清洗 ============
python clean_list.py input\messy.txt                      # 标准清洗
python clean_list.py input\messy.txt --no-crossref         # 跳过 CrossRef
python clean_list.py input\messy.txt --crossref-gap 2      # 慢一点查 CrossRef

# ============ 第二步：AI/人决策 ============
# 看 output\paperlist_review.json → 写 output\decisions.json
python apply_decisions.py output\decisions.json

# ============ 第三步：抓 PDF ============
python run.py output\paperlist_clean.txt --skip-existing   # 标准抓取
python run.py output\paperlist_clean.txt                   # 全部重抓

# ============ 第四步：推入 Zotero ============
python import_to_zotero.py                                 # 导入所有新 PDF
python import_to_zotero.py --limit 1                       # 先测试 1 篇
python import_to_zotero.py --dry-run                       # 预览
python import_to_zotero.py --no-dedupe                     # 不做 MD5 去重
python import_to_zotero.py --gap 5                         # 上传间隔 5 秒

# ============ 一条龙（最常用） ============
python clean_list.py input\messy.txt
# → 看 review.json，写 decisions.json
python apply_decisions.py output\decisions.json
python run.py output\paperlist_clean.txt --skip-existing
python import_to_zotero.py
```
