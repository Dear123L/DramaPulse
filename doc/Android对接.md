# 前端接口对接

基地址：`http://localhost:8000`

---

## 1. 加载视频流

```
GET /video/stream
```

请求无参数。

响应：`Content-Type: video/mp4` 二进制流。

---

## 2. 获取高光点（进入播放页时调用）

```
GET /episodes/67/highlights
```

响应（`HighlightListResponse`）：

```json
{
  "episode_no": 67,
  "title": "古墓疑云",
  "theme": "古墓探险",
  "total_duration": 300,
  "highlight_count": 25,
  "highlights": [
    {
      "id": 51,
      "timestamp": 45,
      "type": "悬疑",
      "intensity": 7,
      "emotion": "紧张",
      "scene_desc": "古墓入口的幽暗甬道",
      "action_desc": "主角手持手电筒探路",
      "trigger": {
        "auto": true,
        "gesture": "double_tap",
        "window_ms": 4000,
        "cooldown_ms": 10000
      },
      "visual_effect": "flashlight_flicker",
      "particle_type": "dust_mote",
      "haptic_pattern": "vibrate_light",
      "audio_cue": "creak_sound",
      "show_branch": true,
      "branch_options": [
        {"id": "A", "text": "探查前方暗道", "consequence": "触发隐藏机关"},
        {"id": "B", "text": "原地等待观察", "consequence": "发现墙上有暗号"},
        {"id": "C", "text": "回头撤退", "consequence": "退路已被封死"}
      ],
      "ai_prompt": "场景:古墓入口的幽暗甬道..."
    }
  ]
}
```

> 前端用 `highlight.timestamp` 比对视频 `currentTime` 触发高光点，用 `highlight.id` 调 AI 接口。

---

## 3. 分支选择 → AI 续写

### 方案A：纯文字

```
POST /ai/branch
```

请求（`BranchRequest`）：

```json
{
  "episode_no": 67,
  "highlight_id": 51,
  "branch_id": "A",
  "branch_text": "探查前方暗道",
  "context": ""
}
```

响应（`BranchTextResponse`）：

```json
{
  "branch_id": "A",
  "text": "三束手电光扫过斑驳的木构门楣时，一阵阴冷的穿堂风突然从甬道深处涌出...",
  "cached": false,
  "token_usage": 569
}
```

### 方案B：文字 + 文生图

```
POST /ai/branch-with-image
```

请求：同上 `BranchRequest`。

响应（`BranchImageResponse`）：

```json
{
  "branch_id": "A",
  "text": "三束手电光扫过斑驳的木构门楣时...",
  "image_url": "/assets/ep67/hl51_branchA_1718000000.png",
  "result_type": "image",
  "cached": false,
  "token_usage": 569
}
```

> `image_url` 为空串表示文生图失败，前端仅显示 `text`。

---

## 降级策略

```
POST /ai/branch-with-image
  ├─ 200 → 显示 image_url 图片 + text 打字机
  └─ 404/失败 → POST /ai/branch
                  └─ 200 → 仅 text 打字机
```

先试方案B，失败降级方案A。
