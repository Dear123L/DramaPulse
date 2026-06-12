# DramaPulse - 短剧互动激发平台

AI 驱动的短剧互动体验后端系统，支持高光点自动识别、情绪特效触发、AI 剧情分支续写、AI 互动类型分析。

---

## 使用教程

### 一、运行环境要求

| 软件 | 版本要求 | 说明 |
|------|----------|------|
| Python | 3.9+ | 推荐 Anaconda 管理 |
| MySQL | 5.7 / 8.0 | 本地运行，端口 3306 |
| ffmpeg | 任意版本 | 用于视频截帧和音频提取，需加入 PATH |

---

### 二、初始化步骤（首次运行）

#### 第 1 步：安装 Python 依赖

```bash
cd backend
pip install -r requirements.txt
```

依赖包含：`fastapi` `uvicorn` `pymysql` `python-dotenv` `openai` `opencv-python` `pillow`

---

#### 第 2 步：配置环境变量

```bash
# 复制模板（在 backend/ 目录下执行）
cp .env.example .env

# 用记事本/VSCode 打开 .env，修改以下字段：
```

`.env` 必填项：

```ini
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=root              # 改成你自己的 MySQL 密码

AI_API_KEY=ark-xxxxxxxx-...      # 豆包 API Key（火山方舟控制台获取）
AI_MODEL_ID=ep-xxxxxxxxxxxxxxxx  # 豆包模型端点 ID

SERVER_BASE_URL=http://localhost:8000  # 后端返回给前端的完整URL前缀
```

> ⚠️ `.env` 文件已加入 `.gitignore`，不会被推送到 Git，安全。

---

#### 第 3 步：创建数据库 & 建表

确保 MySQL 服务已启动，然后执行：

```bash
cd backend
python run_create_tables.py
```

成功后数据库 `drama_pulse` 会包含三张表：
- `episodes` — 剧集信息
- `highlights` — 高光点配置（触发时间、特效类型、互动类型、分支选项等）
- `branch_results` — AI 续写结果缓存

> ⚠️ 该脚本会 **DROP 并重建** 数据库，已有数据会清空，仅首次运行或重置时使用。

---

#### 第 4 步：把视频文件放到正确位置

将 `第67集.mp4` 放在 **backend/ 目录内**（推荐），或放在 backend 的上级目录也兼容：

```
backend/第67集.mp4      ← 推荐（和 main.py 同级，随 Git 管理）
```

后端 `/video/stream` 接口会先在 `backend/` 内查找，找不到再向上一级搜索。

> ⚠️ 视频文件较大（通常 >100MB），如不方便推送 Git，可在 clone 后手动放入。

---

#### 第 5 步：启动后端服务

```bash
cd backend
python main.py
```

看到如下输出即启动成功：

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

---

#### 第 6 步：打开前端验证页

浏览器访问：[http://localhost:8000/player](http://localhost:8000/player)

页面操作流程：
1. 点击 **「从服务器加载第67集」** — 加载视频流
2. 点击 **「加载高光点」** — 从数据库拉取 25 个触发节点
3. 点击播放 ▶ — 视频播放到高光点时自动触发特效
4. 遇到分支高光点时，视频**自动暂停**并弹出分支弹窗
5. 选择一个方向 → AI 续写文字以打字机效果显示
6. 点击 **「继续播放」** — 关闭弹窗，主视频继续

> Swagger 文档：[http://localhost:8000/docs](http://localhost:8000/docs)（可直接测试所有 API）

---

### 三、三种 AI 分支方案使用说明

#### 方案 A：纯文字续写（默认，开箱即用）

**无需额外配置**，只要豆包 API Key 填好就能用。

前端调用接口：`POST /ai/branch`

```json
请求体：
{
  "episode_no": 67,
  "highlight_id": 17,
  "branch_id": "A",
  "branch_text": "走左侧岔道"
}

返回：
{
  "text": "你悄然踏入左侧岔道...",
  "result_type": "text",
  "token_usage": 582,
  "cached": false
}
```

效果：弹窗内文字以**打字机动画**逐字显示，播完出现「继续播放」按钮。

---

#### 方案 B：文字 + AI 配图（需要文生图 API Key）

**第 1 步**：在 `.env` 中填入文生图 Key（二选一）：

```ini
# 选项1：Stable Diffusion（https://platform.stability.ai/ 注册，有免费额度）
STABLE_DIFFUSION_API_KEY=sk-xxxxxxxxxxxxxxxx

# 选项2：豆包文生图（火山引擎控制台，需单独开通图像模型权限）
DOUBAO_IMAGE_API_KEY=ark-xxxxxxxx-...
```

**第 2 步**：重启后端服务（配置变更需重启）

**第 3 步**：前端调用接口改为：`POST /ai/branch-with-image`

效果：弹窗同时显示 **AI 续写文字 + AI 生成场景图**（512×512）。

> 若无 Key，接口会自动从预设图片池随机返回一张预设图代替，不会报错。

---

#### 方案 C：预渲染分支视频（离线制作，演示效果最佳）

**第 1 步**：制作分支视频（每个高光点的每个选项各一段，5~15 秒）

推荐工具：可灵 / 剪映 AI / Runway / Pika

详细提示词见 `后端AI生图提示词.md`（精选了 HL#17、HL#9、HL#23 三个高光点）

**第 2 步**：按命名规则放入目录

```
├── frontend/branch_media/ep67/hl17_branchA.mp4   ← HL#17 的 A 选项
├── frontend/branch_media/ep67/hl17_branchB.mp4   ← HL#17 的 B 选项
├── frontend/branch_media/ep67/hl17_branchC.mp4   ← HL#17 的 C 选项
```

**第 3 步**：往数据库插缓存记录（让后端知道视频已准备好）

```sql
INSERT INTO branch_results
  (highlight_id, episode_id, branch_id, branch_text, ai_response, media_path, result_type, token_usage)
VALUES
  (17, 1, 'A', '走左侧岔道', '你选择了左侧岔道，火光在前方闪烁...', 'branch_media/ep67/hl17_branchA.mp4', 'video', 0);
```

**第 4 步**：重启后端，在前端选 HL#17 的任意分支 → 主视频暂停，**分支视频自动播放**，播完出现「继续播放」

---

### 四、前端自动降级逻辑

前端会按优先级尝试三个接口，哪个可用就用哪个：

```
POST /ai/branch-video  →  POST /ai/branch-with-image  →  POST /ai/branch
     方案C（视频）              方案B（图+文）                方案A（纯文字）
```

所以三种方案**同时部署完全没问题**，有视频就播视频，没视频就退到配图，连 Key 都没有就纯文字。

---

### 五、AI 互动类型分析

每个高光点都标注了互动类型，决定前端应触发的互动形式：

| 枚举值 | 类型 | 前端表现 |
|--------|------|----------|
| 1 | 手电 | 手电筒光效互动 |
| 2 | 心跳 | 心跳震动/脉冲特效 |
| 3 | AI弹幕 | 弹幕式评论互动，附带 AI 生成的弹幕内容 |

相关接口：
- `POST /ai/analyze-interaction/{highlight_id}` — 分析单个高光点的互动类型
- `POST /ai/analyze-interaction/batch/{episode_no}` — 批量分析某集所有高光点

高光点接口 `GET /episodes/{episode_no}/highlights` 返回值中包含 `interaction_type` 和 `ai_danmaku` 字段。

---

### 六、常见问题

**Q：启动报 `ModuleNotFoundError: No module named 'fastapi'`**
A：依赖没装，执行 `pip install -r requirements.txt`

**Q：`Connection refused` 连不上 MySQL**
A：确认 MySQL 服务已启动（Windows：`net start mysql80`），并检查 `.env` 里的 `MYSQL_PORT`

**Q：AI 续写返回空 / `401 Unauthorized`**
A：豆包 API Key 失效或额度用完，去火山方舟控制台检查 Key 状态，更换后重启服务

**Q：视频页面播放失败**
A：确认 `第67集.mp4` 放在 `backend/` 目录（或其上级目录）；或检查后端日志里 `/video/stream` 是否报 `video not found`

**Q：分支弹窗里方案B显示占位图不是真实图片**
A：需要在 `.env` 里填入文生图 API Key，参考"方案B使用说明"

---

## 项目结构

```
backend/                                  # 后端服务（Git 仓库根目录）
├── main.py                               # 服务入口，注册所有路由，托管前端静态文件
├── config.py                             # 配置中心：数据库/AI/服务端口/SERVER_BASE_URL
├── database.py                           # MySQL 连接管理（pymysql）
├── models.py                             # 数据模型 & API 响应格式化
├── ai_service.py                         # 豆包 AI 封装：剧情续写 + 视频帧分析
├── run_create_tables.py                  # 执行建表脚本
├── requirements.txt                      # Python 依赖清单
├── .env.example                          # 环境变量模板（.env 本体不推送）
├── .gitignore                            # Git 忽略规则
├── README.md                             # 本文件
├── 技术文档.md                            # 项目技术文档
├── 前端对接指南.md                        # Android 前端对接文档
├── 后端AI生图提示词.md                    # 精选分支的 AI 生图提示词
├── api/                                  # 接口路由模块
│   ├── __init__.py
│   ├── episodes.py                       # 剧集/高光点查询（安卓核心接口）
│   ├── ai_branch.py                      # 【方案A】AI 文字续写：POST /ai/branch
│   ├── ai_branch_image.py                # 【方案B】文字+AI配图：POST /ai/branch-with-image
│   ├── ai_branch_video_prepared.py       # 【方案C】预渲染视频分支：POST /ai/branch-video
│   ├── ai_branch_options.py              # AI 生成分支选项：POST /ai/branch-options
│   └── ai_interaction.py                 # AI 互动类型分析：POST /ai/analyze-interaction
├── scripts/                              # 工具脚本（非运行依赖）
│   ├── mock_analyze_interaction.py       # 模拟生成互动类型数据
│   └── assign_images.py                  # 把预渲染图片写入 branch_results 缓存
├── doc/                                  # 对接文档
│   └── AiInteraction.openapi.json        # AI互动分析接口 OpenAPI 规范
├── frontend/                             # 前端验证页（随后端一起部署）
│   ├── index.html                        # 验证页主页面
│   ├── app.js                            # 前端核心逻辑
│   └── branch_media/                     # 预渲染分支视频存放目录
└── multimodal_assets/
    └── ep67/                             # 预渲染分支图片（hl{id}_branch{label}.png，已入库）

# 注：第67集.mp4 推荐放在 backend/ 目录，也兼容放在上级目录（不推送到 Git 时）
```

---

## 三种 AI 分支方案说明

### 方案A：纯文字续写（当前使用，成本最低）
- **文件**：`api/ai_branch.py`
- **接口**：`POST /ai/branch`
- **流程**：用户选分支 → 调豆包文字模型 → 返回100字续写文案 → 前端打字机效果显示
- **成本**：约 0.001 元/次
- **状态**：✅ 已实现并可运行

### 方案B：文字续写 + AI 文生图（代码已实现，API Key 待填）
- **文件**：`api/ai_branch_image.py`
- **接口**：`POST /ai/branch-with-image`
- **流程**：文字续写 + 同时调文生图 API → 返回 文字 + 图片路径 → 前端弹窗同时显示
- **成本**：文生图约 0.1~0.5 元/张（Stable Diffusion 自建免费）
- **降级策略**：无文生图 Key 时，从预设图片池随机返回一张预设图
- **状态**：✅ 代码框架完成，文生图 API 需自行开通

### 方案C：预渲染视频分支（代码已实现，视频待制作）
- **文件**：`api/ai_branch_video_prepared.py`
- **接口**：`POST /ai/branch-video`
- **流程**：提前用 AI 视频工具生成短视频 → 放入 `frontend/branch_media/ep67/` → 数据库填好路径 → 用户选分支直接播放视频
- **成本**：离线生成，运行时零成本
- **视频命名规则**：`hl{highlight_id}_branch{branch_id}.mp4`（例：`hl17_branchA.mp4`）
- **状态**：✅ 代码完成，预渲染视频需自行制作并放入目录

> **答辩策略建议**：演示时用方案C（预渲染视频，效果最好），代码提交保留方案B的接口（体现多模态AI能力）。

---

## 数据库表结构

### `episodes` - 剧集信息表
| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | INT AI | 主键 |
| `episode_no` | INT UNIQUE | 剧集编号（App 用这个请求） |
| `title` | VARCHAR(255) | 剧集标题 |
| `theme` | VARCHAR(100) | 主题标签 |
| `total_duration` | INT | 视频总时长（秒） |
| `status` | ENUM | 分析状态：pending/analyzing/done/failed |
| `highlight_count` | INT | 高光点总数 |

### `highlights` - 高光点配置表（核心表）
| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | BIGINT AI | 主键，AI分支续写时用它关联 |
| `episode_id` | INT | 关联剧集 |
| `timestamp` | INT | 触发时间（秒），App 靠这个判断 |
| `scene_desc` | TEXT | 场景描述（AI生成，续写提示词用） |
| `action_desc` | TEXT | 角色动作描述 |
| `emotion` | VARCHAR(100) | 情绪氛围 |
| `visual_effect` | VARCHAR(100) | 视觉特效类型 |
| `particle_type` | VARCHAR(100) | 粒子特效类型 |
| `audio_cue` | VARCHAR(100) | 音效提示 |
| `show_branch` | TINYINT(1) | 是否弹出分支弹窗 |
| `branch_options` | TEXT(JSON) | 分支选项：`[{id:A, text:...}]` |
| `interaction_type` | TINYINT | 互动类型：1=手电 2=心跳 3=AI弹幕 NULL=未分析 |
| `ai_danmaku` | JSON | AI弹幕列表，仅 interaction_type=3 时有值 |

### `branch_results` - AI 续写结果缓存表
| 字段 | 类型 | 说明 |
|------|------|------|
| `highlight_id` | BIGINT | 关联高光点 |
| `branch_id` | VARCHAR(10) | 分支标识：A/B/C |
| `result_type` | VARCHAR(20) | 返回类型：text/image/video |
| `ai_response` | TEXT | AI 续写文字（展示给用户） |
| `media_path` | VARCHAR(500) | 多媒体文件路径（image/video 时填） |
| `token_usage` | INT | 消耗 token 数 |
> **缓存机制**：同一 `highlight_id + branch_id` 组合只生成一次，后续直接返回缓存，大幅降低费用。

---

## 环境变量 / 敏感配置

> ⚠️ **API Key 等敏感信息不能写在代码里推到 Git，一律放在 `.env` 文件中。**

### 初始化步骤

```bash
# 1. 复制模板（在 backend/ 目录下执行）
cp .env.example .env

# 2. 编辑 .env，填入你自己的 Key
#    必填：AI_API_KEY、MYSQL_PASSWORD、SERVER_BASE_URL
#    选填：STABLE_DIFFUSION_API_KEY（方案B）、DOUBAO_IMAGE_API_KEY（方案B豆包图）
```

`.env` 文件格式（示例）：
```ini
MYSQL_PASSWORD=root
AI_API_KEY=ark-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
AI_MODEL_ID=ep-xxxxxxxxxxxxxxxxxxxx
SERVER_BASE_URL=http://localhost:8000
STABLE_DIFFUSION_API_KEY=sk-xxxxxxxxxxxxxxxx  # 选填
```

### Git 规则

- `.env` —— **禁止推送**（含真实 Key，已加入根目录 `.gitignore`）
- `.env.example` —— **推送**（模板，其他人 clone 后参考这个填值）
- `config.py` —— **推送**（只有 `os.getenv` 读取逻辑，不含任何真实 Key）

---

## 快速启动

```bash
# 1. 安装依赖（在 backend/ 目录下执行）
pip install -r requirements.txt

# 2. 复制并填写环境变量
cp .env.example .env
# 编辑 .env 填入 MYSQL_PASSWORD、AI_API_KEY 和 SERVER_BASE_URL

# 3. 建表
python run_create_tables.py

# 4. 启动服务
python main.py
# 服务运行在 http://localhost:8000

# 5. 打开前端验证页
# 浏览器访问：http://localhost:8000/player
```

---

## API 接口一览

> 图例：🟢 前端当前已接入并调用 | 🔵 前端已实现调用逻辑（降级链中） | ⚪ 后端已实现，前端未直接调用

### 基础 / 页面类

| 状态 | 方法 | 路径 | 说明 |
|------|------|------|------|
| ⚪ | GET | `/` | 健康检查，返回 `{"status":"ok"}` |
| ⚪ | GET | `/docs` | Swagger 自动文档（浏览器可直接测试） |
| 🟢 | GET | `/player` | 前端验证页入口，返回 `frontend/index.html` |
| 🟢 | GET | `/video/stream` | 第67集视频流（前端 `<video>` 标签 src 指向这里） |
| ⚪ | GET | `/api/summary` | 接口摘要列表（JSON） |

### 剧集 / 高光点类

| 状态 | 方法 | 路径 | 说明 |
|------|------|------|------|
| ⚪ | GET | `/episodes` | 获取所有剧集列表 |
| ⚪ | GET | `/episodes/{episode_no}` | 获取单集信息 |
| 🟢 | GET | `/episodes/{episode_no}/highlights` | **获取某集全部高光点配置**（含 interaction_type、ai_danmaku） |
| ⚪ | GET | `/episodes/{episode_no}/highlights/{id}` | 获取单个高光点详情 |

### AI 分支续写类（三种方案，前端按优先级依次降级）

| 状态 | 方法 | 路径 | 方案 | 说明 |
|------|------|------|------|------|
| 🔵 | POST | `/ai/branch-video` | 方案C | 先查预渲染视频缓存，有真实视频文件才返回200，否则 404 触发前端降级 |
| 🔵 | POST | `/ai/branch-with-image` | 方案B | 查图片缓存，有缓存直接返回；无缓存调文生图API或返回预设图 |
| 🟢 | POST | `/ai/branch` | 方案A | 查文字缓存；无缓存调豆包AI续写并存入缓存。**当前最终兜底** |

### AI 互动类型分析类

| 状态 | 方法 | 路径 | 说明 |
|------|------|------|------|
| ⚪ | POST | `/ai/analyze-interaction/{highlight_id}` | 分析单个高光点的互动类型 |
| ⚪ | POST | `/ai/analyze-interaction/batch/{episode_no}` | 批量分析某集所有高光点 |

### AI 分支选项生成类

| 状态 | 方法 | 路径 | 说明 |
|------|------|------|------|
| ⚪ | POST | `/ai/branch-options/{highlight_id}` | AI 生成分支选项 |

**前端降级调用顺序（`app.js` 中实现）：**
```
POST /ai/branch-video  →(404)→  POST /ai/branch-with-image  →(404)→  POST /ai/branch
```

**三个接口共用请求体：**
```json
{
  "episode_no": 67,
  "highlight_id": 17,
  "branch_id": "A",
  "branch_text": "走左侧岔道"
}
```

**`/ai/branch` 返回（方案A）：**
```json
{
  "branch_id": "A",
  "text": "你提着手电毅然踏入左侧岔道...",
  "result_type": "text",
  "token_usage": 245,
  "cached": true
}
```

**`/ai/branch-with-image` 返回（方案B）：**
```json
{
  "branch_id": "A",
  "text": "你提着手电毅然踏入左侧岔道...",
  "image_url": "http://localhost:8000/assets/ep67/hl17_branchA.png",
  "result_type": "image",
  "token_usage": 0,
  "cached": true
}
```

> `image_url` 已包含完整服务器地址（由 `SERVER_BASE_URL` 拼接），前端可直接使用。

**`/ai/branch-video` 返回（方案C，需要提前放好视频文件）：**
```json
{
  "branch_id": "A",
  "text": "你提着手电毅然踏入左侧岔道...",
  "media_url": "/static/branch_media/ep67/hl17_branchA.mp4",
  "result_type": "video",
  "token_usage": 0,
  "cached": true
}
```

---

### 静态文件访问

| 路径前缀 | 映射目录 | 用途 |
|---------|---------|------|
| `/static/...` | `backend/frontend/` | 前端 JS/CSS 及分支视频 |
| `/assets/...` | `backend/multimodal_assets/` | AI 生成/预渲染分支图片 |

示例：`http://localhost:8000/assets/ep67/hl17_branchA.png`

---

## 精选分支提示词

见 `后端AI生图提示词.md`，包含 HL#17、HL#9、HL#23 三个高光点的详细文生图提示词，
可直接复制发给 Stable Diffusion / 豆包文生图 / Leonardo.ai 等平台使用。
