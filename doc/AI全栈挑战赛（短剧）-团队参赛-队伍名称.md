# AI全栈挑战赛（短剧）\-团队参赛\-队伍名称

> 课题：[AI全栈项目\-\-基于短剧剧情的即时互动激发（宣讲）](https://my.feishu.cn/wiki/R4mVwKXgTiNh3Zkfucrc75C6nfr)
> 
> **使用说明**：请通过本模版文档「**创建副本**」后填写。各小节下的灰色提示为填写引导，提交前可删除。
> 
> 请尽量完整填写，内容可根据实际情况选填。
> 
> 提交前请确认交付物是否**齐全且可访问**
> 
> 




# 参赛队伍名称和成员

> 在下面的表格填入队伍名称等信息
> 
> 

|**项目名称**|DramaPulse|
|---|---|
|队伍名称||
|**成员姓名**||
|**技术栈**|后端：FastAPI / Uvicorn / MySQL / 豆包AI（火山方舟）|




# 项目概述

- **项目思路**：DramaPulse 是一款面向 Android 短剧的 AI 实时互动激发平台。通过预先分析第 67 集视频，将 25 个情绪高光点写入数据库，播放过程中由 Android App 在关键时间点触发对应互动效果（手电照明、心跳震动、AI 弹幕），并在分支节点暂停视频，让用户选择剧情走向，AI 实时续写文字及场景配图，构建沉浸式互动观看体验。

- **核心功能介绍**：

  - **短剧内容理解**：针对第 67 集（北派寻宝笔记·古墓探险主题），提前标注 25 个高光点，每个高光点记录触发时间戳、场景描述、情绪氛围、视觉特效类型等字段，供 App 在播放时精准触发。
  
  - **互动类型智能分析**：新增 `POST /ai/analyze-interaction` 接口，调用豆包 AI 分析每个无分支高光点的场景信息，自动判断最适合的互动方式（1=手电照明 / 2=心跳震动 / 3=AI 弹幕）并写入数据库；若为弹幕类型，同时 AI 生成 5 条简短场景弹幕。

  - **AIGC 剧情分支续写**：用户触达分支高光点时，后端调用豆包 AI 根据场景描述和用户选择实时生成约 100 字的续写文案，结果缓存至 `branch_results` 表，同一分支后续请求直接命中缓存。
  
  - **AI 分支配图**：`POST /ai/branch-with-image` 接口在续写文字的同时返回对应的场景图片，核心高光点（HL#9/17/23）预置精选 AI 图片，其余分支随机从 10 张预设图池中分配并缓存，确保全部分支均有图可返回。
  
  - **分支选项智能生成**：`POST /ai/generate-branch-options` 接口调用豆包 AI，根据高光点场景信息为所有分支高光点自动生成 A/B/C 三个个性化选项（A=冒险、B=谨慎、C=出人意料），替代原始重复的通用选项。

- **产品亮点与创新点**：
  - 互动类型覆盖感官多维度：手电（视觉沉浸）、心跳（触觉反馈）、AI 弹幕（社交临场感），三种类型由 AI 自动匹配场景而非人工标注。
  - 全链路 AI 驱动：从分支选项生成→续写内容→场景配图→互动类型判断，均由豆包 AI 完成，无需人工逐条配置。
  - 结果缓存策略显著降低 AI 调用成本，相同分支只生成一次，后续请求毫秒级命中缓存。
  - 三种分支方案（纯文字/图文/预渲染视频）可同时部署，前端自动降级，保证任何环境下都有可用的互动体验。

- **技术关键点**：
  - 使用 OpenAI SDK 兼容模式接入字节跳动火山方舟豆包 AI，zero adaptation cost。
  - AI 批量调用均加入限流间隔（`time.sleep`）并复用单例 `_get_client()`，避免重复建立 HTTP 连接导致限流。
  - 服务端通过 `SERVER_BASE_URL` 配置项拼接完整图片 URL 返回给 App，App 无需自行拼接域名。
  - FastAPI 同时托管 `/static`（前端资源）和 `/assets`（AI 图片），无需额外 Web 服务器。




# 项目实机演示

> 项目演示录屏，尽量完整，从开发环境启动到实际运行演示，展示核心场景、关键功能、亮点与结果；优先贴公开在线可访问的视频链接
> 
> 




# 项目技术文档

## 1. 整体架构

```
Android App (Retrofit)
        │  HTTP/JSON
        ▼
┌─────────────────────────────┐
│       FastAPI 后端服务        │
│   localhost:8000            │
│                             │
│  api/                       │
│  ├── episodes.py            │  ← 剧集 & 高光点查询
│  ├── ai_branch.py           │  ← 方案A 纯文字续写
│  ├── ai_branch_image.py     │  ← 方案B 文字+配图
│  ├── ai_branch_video_prepared.py │ ← 方案C 预渲染视频
│  ├── ai_branch_options.py   │  ← 分支选项AI生成
│  └── ai_interaction.py      │  ← 互动类型AI分析
│                             │
│  核心层：ai_service.py / database.py / config.py / models.py
└────────────┬────────────────┘
             │
   ┌─────────┴──────────┐
   │  MySQL              │    豆包 AI（火山方舟）
   │  drama_pulse        │    OpenAI 兼容模式
   └─────────────────────┘
```

## 2. 技术选型

| 层级 | 选型 | 理由 |
|------|------|------|
| Web 框架 | FastAPI 0.110+ | 原生异步、自动 OpenAPI 文档、Pydantic 校验 |
| ASGI 服务器 | Uvicorn | FastAPI 官方推荐，轻量高性能 |
| 数据库 | MySQL 8.0 | 关系型，结构化剧情数据，支持 JSON 字段 |
| AI 接口 | 豆包（火山方舟）+ OpenAI SDK 兼容 | zero adaptation cost，支持文字/弹幕/选项多种生成任务 |
| 数据校验 | Pydantic v2 | 内置类型安全与文档生成 |
| 配置管理 | python-dotenv | 环境变量隔离，API Key 不进代码仓库 |

## 3. 数据库设计

### `episodes` — 剧集表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT PK | 主键 |
| episode_no | INT UNIQUE | 集数编号（如 67） |
| title / theme | VARCHAR | 标题、主题标签 |
| total_duration | INT | 视频总时长（秒） |
| status | ENUM | 分析状态 |

### `highlights` — 高光点表（核心）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT PK | 主键 |
| episode_id | INT FK | 所属剧集 |
| timestamp | INT | 触发时间点（秒） |
| scene_desc / action_desc / emotion | TEXT/VARCHAR | 场景描述（AI Prompt 素材） |
| visual_effect / particle_type / audio_cue | VARCHAR | 特效配置 |
| show_branch | TINYINT(1) | 是否弹出分支（1=弹窗/0=纯特效） |
| branch_options | TEXT(JSON) | 分支选项列表 `[{id,text,consequence}]` |
| **interaction_type** | TINYINT | **新增** 互动类型 1=手电/2=心跳/3=AI弹幕 |
| **ai_danmaku** | JSON | **新增** AI生成弹幕列表（type=3时有值） |

### `branch_results` — 续写结果缓存表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT PK | 主键 |
| highlight_id + branch_id | — | 联合唯一键（同组合只生成一次） |
| result_type | VARCHAR | text / image / video |
| ai_response | TEXT | AI 续写文字 |
| media_path | VARCHAR | 图片/视频相对路径（`/assets/ep67/xxx.png`） |
| token_usage | INT | AI 消耗 token 数 |

## 4. 核心接口清单

### 已对接安卓的接口（不可改动）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/episodes/{episode_no}/highlights` | 获取某集全部高光点 |
| GET | `/episodes/{episode_no}/highlights/{id}` | 获取单个高光点详情 |
| GET | `/episodes` | 获取所有剧集列表 |
| GET | `/video/stream` | 第67集视频流 |
| POST | `/ai/branch` | 方案A：AI 文字续写（含缓存） |
| POST | `/ai/branch-with-image` | 方案B：文字+图片（含图片缓存） |
| POST | `/ai/branch-video` | 方案C：预渲染视频分支 |

### 新增接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/ai/generate-branch-options` | 批量 AI 生成分支选项并写入数据库 |
| POST | `/ai/generate-branch-options/{highlight_id}` | 单个高光点 AI 生成分支选项 |
| POST | `/ai/analyze-interaction/{highlight_id}` | AI 分析单个高光点互动类型 |
| POST | `/ai/analyze-interaction/batch/{episode_no}` | 批量分析整集所有无分支高光点互动类型 |

## 5. 关键流程

### 分支续写（方案B）请求链路

```
App 触发分支高光点
        │
        ▼ POST /ai/branch-with-image
查询 branch_results 缓存
        │
        ├─ 命中 → 直接返回（image_url 为完整 URL，含 SERVER_BASE_URL 前缀）
        │
        └─ 未命中 → 调用豆包AI续写文字
                    → 随机从9张预设图池分配一张图片
                    → 写入 branch_results 缓存
                    → 返回完整图片URL + 续写文字
```

### 互动类型分析链路

```
POST /ai/analyze-interaction/batch/{episode_no}
        │
        ▼ 遍历所有 show_branch=0 的高光点
        │
        ├─ 已分析且 force=false → 跳过
        │
        └─ 调用豆包AI，Prompt 包含场景描述/动作/情绪
                    → 返回 {"interaction_type": 1/2/3, "danmaku": [...]}
                    → UPDATE highlights 表写入两个新字段
                    → 调用间隔 0.5s 防限流
```

## 6. 工程难点与解决方案

### 难点1：AI 批量调用限流

**问题**：最初每次请求都 `new OpenAI()` 创建新客户端，批量调用时频繁建立 HTTP 连接，触发火山方舟 API 限流（Rate Limit），导致全部失败。

**解决**：统一改用 `ai_service._get_client()` 返回单例客户端，批量循环中每次 AI 调用后加 `time.sleep(1)`，问题消除，12 个高光点批量生成全部成功。

### 难点2：图片 URL 安卓端无法加载

**问题**：`/ai/branch-with-image` 最初返回的 `image_url` 是相对路径（`/assets/ep67/xxx.png`），安卓端 Retrofit 无法直接拼接访问。

**解决**：在 `config.py` 新增 `SERVER_BASE_URL` 配置项，从 `.env` 读取（如 `http://localhost:8000`），接口返回前统一拼接，安卓端可直接使用 `image_url` 加载图片。

### 难点3：无缓存时生成黑底白字占位图体验差

**问题**：对于没有预置图片的分支，原逻辑依次调用 Stable Diffusion → 豆包文生图 → 生成黑底白字 PIL 占位图，AI 生图 API 未配置时最终呈现黑底白字，视觉效果差。

**解决**：重构无缓存降级策略：直接从 10 张预置精选 AI 图片中随机选取一张返回，并写入 `branch_results` 缓存。既保证了视觉质量，又消除了 AI 生图 API 依赖。

## 7. 工作项拆分

| 模块 | 内容 | 状态 |
|------|------|------|
| 项目骨架 | FastAPI + MySQL + CORS + 静态文件托管 | ✅ 完成 |
| 数据库设计 | episodes / highlights / branch_results 三表 | ✅ 完成 |
| 豆包 AI 接入 | OpenAI 兼容模式，封装 ai_service.py | ✅ 完成 |
| 高光点数据导入 | 25 个高光点解析并写入数据库 | ✅ 完成 |
| 剧集 & 高光点接口 | GET /episodes、GET /highlights（App核心接口） | ✅ 完成 |
| 方案A：文字续写 | POST /ai/branch，含缓存 | ✅ 完成 |
| 方案B：图文分支 | POST /ai/branch-with-image，预设图池 + 随机降级 | ✅ 完成 |
| 方案C：预渲染视频 | POST /ai/branch-video，静态视频文件返回 | ✅ 完成 |
| 分支选项 AI 生成 | POST /ai/generate-branch-options，12个高光点全部更新 | ✅ 完成 |
| 互动类型 AI 分析 | POST /ai/analyze-interaction，highlights 表新增两字段 | ✅ 完成 |
| 接口 URL 修复 | SERVER_BASE_URL 拼接完整图片 URL | ✅ 完成 |
| 目录结构整理 | routes/ → api/，删除一次性脚本，结构规范化 | ✅ 完成 |
| API 文档 | Swagger 自动文档 + doc/BranchOptions.openapi.json | ✅ 完成 |




# 项目代码和产物

> 填写项目的 Github 链接
> 
> 注意：
> 
> - Github 项目需要有清晰的 README 说明
> 
> - 打包的 apk、ipa 等端侧产物，也可以放在 Github 项目中
> 
> - 如果是多人参与，务必标明真实姓名和 github 账号的**对应关系**，方便评委识别
> 
> 




# 项目总结和自评

## 完成情况

本项目后端从零完成搭建，实现了高光点数据管理、三种 AI 分支方案、互动类型智能判断、分支选项自动生成等全部核心功能，并已完成与 Android 端的接口对接。整体架构清晰，接口规范，可直接部署演示。

## 亮点

- 全部 AI 调用统一封装，Prompt 设计贴合短剧场景，生成内容质量稳定。
- 三种分支方案（文字/图文/视频）互相降级，保证任何配置下都有可用体验。
- 新增的互动类型分析（手电/心跳/AI弹幕）完全由 AI 驱动，超出课题基础要求。
- 工程上重视细节：缓存机制降低 AI 成本、SERVER_BASE_URL 解决 App URL 拼接问题、批量调用限流保护。

## 不足与反思

- 高光点数据目前为预标注（人工+脚本），若能接入视频帧分析 + 情绪识别实现全自动提取，AI 全栈属性会更完整。
- `branch_results` 缓存无版本管理，AI 模型升级后旧缓存无法自动失效，后续需加 `model_version` 字段。
- 当前为单机本地部署，未容器化，多用户并发场景需补充连接池与限流中间件。
