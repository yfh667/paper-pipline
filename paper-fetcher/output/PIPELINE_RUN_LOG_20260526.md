# Pipeline 全流程运行记录 — 2026-05-26

## 目标论文

**Title:** Eavesdropping exposure model and energy-efficient survivable routing based on extended OISLs in optical satellite networks  
**DOI:** 10.1364/JOCN.586930  
**Publisher:** Optica Publishing Group (Journal of Optical Communications and Networking)  
**Pages:** 15 pages (Vol. 18, Issue 6, pp. 614-628)

## Step 1: 准备输入清单

- 创建 `paper-fetcher/input/optica_test.txt`
- 格式: `[optica] 论文标题 (doi=10.1364/JOCN.586930)`
- 时间: 10:49

## Step 2: paper-fetcher 下载 PDF

- 命令: `python run.py input\optica_test.txt --skip-existing`
- Handler: OpticaHandler (undetected-chromedriver 过 Cloudflare Turnstile)
- 流程: DOI → doi.org 跳转 → opg.optica.org → 提取 URI (jocn-18-6-614) → viewmedia.cfm 下载 PDF
- 结果: **成功**
- 耗时: 29.8s
- 输出: `output/optica/Eavesdropping exposure model and energy-efficient survivable routing based on extended OISLs in optical satellite networks.pdf`
- 大小: 4,575,757 bytes (4.36 MB)
- 日志: `output/logs/run-20260526-105007.log`
- 时间: 10:50

## Step 3: 导入 Zotero

- 命令: `python import_to_zotero.py`
- 方式: POST /connector/saveStandaloneAttachment (PDF 字节 + X-Metadata header)
- 去重: MD5 检查，已有的跳过
- 结果: **成功** (canRecognize=True)
- Zotero 自动识别元数据: 标题、作者、期刊、DOI
- Zotero 分配存储 key: BGTJHNWV
- PDF 物理路径: `C:\Users\Administrator\Zotero\storage\BGTJHNWV\*.pdf`
- 时间: 10:51-10:52
- 注: PDF 默认进入 Zotero "Unfiled Items"，需手动拖到目标 collection

## Step 4: MinerU 转 Markdown

- 命令: `python batch.py --large yes --key BGTJHNWV`
- 模式: API 模式 (use_api=true, mineru-api 常驻服务)
- 该论文 15 页，不触发大 PDF split（阈值 200 页）
- mineru-api 启动 → 模型加载 → 通过 --api-url 处理
- 输出: `C:\Users\Administrator\Zotero\mineru-mirror\BGTJHNWV\`
  - `*.md` — Markdown 全文
  - `images/` — 提取的图片
- 状态记录: `zotero-mineru/state.json` 中 BGTJHNWV 条目更新
- API 启动: 33.6s (模型加载)
- 转换耗时: **144.0s** (含 API 调用)
- 输出 MD: 103,919 bytes, 包含完整论文全文
- 提取图片: 44 张
- 时间: 11:06:16 API 启动 → 11:09:15 转换完成

## 最终结果

**全流程成功完成。** 从下载到 markdown 全自动。

| 步骤 | 耗时 | 状态 |
|------|------|------|
| PDF 下载 (Optica) | 29.8s | ✓ |
| 导入 Zotero | 2s | ✓ |
| API 启动 + 模型加载 | 33.6s | ✓ |
| MinerU 转 Markdown | 144.0s | ✓ |
| **端到端总耗时** | **~210s (3.5 min)** | **✓** |

## 环境信息

- MinerU: 3.1.14
- Backend: hybrid-auto-engine
- GPU: NVIDIA RTX A5000 24GB
- Python: 3.11 (conda env: mineru)
- Zotero: 9.0.4 (本地 API 端口 23119)
- OS: Windows Server 2025

## 涉及的代码文件

| 步骤 | 主要文件 |
|------|---------|
| 下载 | `paper-fetcher/handlers/optica.py`, `paper-fetcher/run.py` |
| 导入 | `paper-fetcher/import_to_zotero.py` |
| 转换 | `zotero-mineru/batch.py`, `zotero-mineru/common.py` |
| 配置 | `zotero-mineru/config.json` |
