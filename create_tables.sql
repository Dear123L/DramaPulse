-- DramaPulse backend - MySQL schema
-- DB: drama_pulse   host: 127.0.0.1:3306   user: root / root

DROP DATABASE IF EXISTS drama_pulse;
CREATE DATABASE drama_pulse CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE drama_pulse;

DROP TABLE IF EXISTS branch_results;
DROP TABLE IF EXISTS highlights;
DROP TABLE IF EXISTS episodes;

-- ============================
-- 表1: episodes  剧集信息表
-- ============================
CREATE TABLE episodes (
  id              INT AUTO_INCREMENT PRIMARY KEY          COMMENT '主键ID（自增）',
  episode_no      INT NOT NULL UNIQUE                     COMMENT '剧集编号，如67、68，App用这个字段请求数据',
  title           VARCHAR(255) NOT NULL                   COMMENT '剧集标题，如：北派寻宝笔记·第67集',
  theme           VARCHAR(100) DEFAULT ''                 COMMENT '主题标签，如：古墓探险 / 悬疑解谜',
  total_duration  INT DEFAULT 0                           COMMENT '视频总时长（秒），用于进度条计算',
  video_path      VARCHAR(500) DEFAULT ''                 COMMENT '视频文件本地路径，分析时用，App不用这个',
  status          ENUM('pending','analyzing','done','failed') DEFAULT 'pending'
                                                          COMMENT '分析状态：pending=待分析 analyzing=分析中 done=完成 failed=失败',
  frame_count     INT DEFAULT 0                           COMMENT '实际截帧数量（每15秒截一帧）',
  highlight_count INT DEFAULT 0                           COMMENT '识别出的高光点总数，冗余字段方便展示',
  created_at      DATETIME DEFAULT CURRENT_TIMESTAMP      COMMENT '记录创建时间',
  updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                                                          COMMENT '最后更新时间（自动更新）',
  INDEX idx_status (status),
  INDEX idx_episode_no (episode_no)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='剧集信息表：每一行代表一集短剧，存储分析状态和基础元数据';

-- ============================
-- 表2: highlights  高光点配置表（核心表）
-- ============================
CREATE TABLE highlights (
  id             BIGINT AUTO_INCREMENT PRIMARY KEY        COMMENT '高光点主键ID，AI分支续写时用它关联',
  episode_id     INT NOT NULL                             COMMENT '关联的剧集ID（对应episodes.id）',
  timestamp      INT NOT NULL                             COMMENT '高光点触发时间（秒），App靠这个字段判断何时触发特效',
  highlight_type VARCHAR(50) DEFAULT ''                   COMMENT '场景类型：悬疑/恐惧/危机等，后台分类用',
  emotion        VARCHAR(100) DEFAULT ''                  COMMENT '情绪描述文字，如：紧张、悬疑，续写AI提示词用',
  intensity      TINYINT DEFAULT 0                        COMMENT '情绪强度评分 1~10，越高越紧张，可用于决定特效强度',
  scene_desc     TEXT                                     COMMENT '场景描述（AI生成），描述当前画面内容，续写时作为背景',
  action_desc    TEXT                                     COMMENT '角色动作描述（AI生成），描述人物在干什么',
  trigger_json   JSON                                     COMMENT '触发配置JSON：auto=是否自动触发 gesture=手势类型 window_ms=手势窗口毫秒 cooldown_ms=冷却毫秒',
  visual_effect  VARCHAR(100) DEFAULT ''                  COMMENT '视觉特效类型：flashlight_flicker=手电闪烁 heartbeat_pulse=心跳脉搏',
  particle_type  VARCHAR(100) DEFAULT ''                  COMMENT '粒子特效类型：dust_mote=悬浮尘埃 dark_fog=黑暗雾气',
  haptic_pattern VARCHAR(100) DEFAULT ''                  COMMENT '震动类型：vibrate_light=轻微震动 vibrate_pattern_heartbeat=心跳节奏震动',
  audio_cue      VARCHAR(100) DEFAULT ''                  COMMENT '音效提示：creak_sound=木质嘎吱声 low_freq_drone=低频嗡鸣声',
  show_branch    TINYINT(1) DEFAULT 0                     COMMENT '是否弹出剧情分支弹窗：1=弹出 0=不弹（只播特效）',
  branch_options TEXT                                     COMMENT '剧情分支选项JSON数组，格式：[{id:A,text:探查前方,consequence:触发机关}]',
  ai_prompt      TEXT                                     COMMENT '传给豆包的续写提示词模板，App调用/ai/branch时发送',
  frame_file     VARCHAR(255) DEFAULT ''                  COMMENT '该时刻截帧的图片文件名，调试用',
  created_at     DATETIME DEFAULT CURRENT_TIMESTAMP       COMMENT '记录创建时间',
  FOREIGN KEY (episode_id) REFERENCES episodes(id) ON DELETE CASCADE,
  INDEX idx_ep_ts (episode_id, timestamp),
  INDEX idx_type (highlight_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='高光点配置表：每行是一个触发时刻，存储特效类型和分支配置，App核心数据源';

-- ============================
-- 表3: branch_results  AI续写结果缓存表
-- ============================
CREATE TABLE branch_results (
  id             BIGINT AUTO_INCREMENT PRIMARY KEY          COMMENT '主键ID（自增）',
  highlight_id   BIGINT NOT NULL                            COMMENT '关联的高光点ID（highlights.id）',
  episode_id     INT NOT NULL                               COMMENT '关联的剧集ID（冗余，方便按集查询）',
  branch_id      VARCHAR(10) NOT NULL                       COMMENT '分支选项标识：A / B / C',
  branch_text    VARCHAR(255) DEFAULT ''                    COMMENT '分支选项文字，如：探查前方暗道',
  result_type    VARCHAR(20) DEFAULT 'text'                 COMMENT '返回类型：text=纯文字 image=AI配图 video=预渲染视频',
  ai_response    TEXT                                       COMMENT '豆包API返回的续写正文，这个字段的值展示给用户看',
  media_path     VARCHAR(500) DEFAULT ''                     COMMENT '多媒体文件路径，result_type=image/video时存相对路径',
  prompt_sent    TEXT                                       COMMENT '实际发给AI的完整提示词（用于调试/复现）',
  token_usage    INT DEFAULT 0                              COMMENT '本次调用消耗的token数量（用于统计费用）',
  created_at     DATETIME DEFAULT CURRENT_TIMESTAMP         COMMENT '生成时间（同一highlight+branch组合只生成一次，后续走缓存）',
  UNIQUE KEY uk_hl_branch (highlight_id, branch_id)       COMMENT '唯一约束：同一高光点的同一分支只保存一份缓存',
  FOREIGN KEY (highlight_id) REFERENCES highlights(id) ON DELETE CASCADE,
  FOREIGN KEY (episode_id)   REFERENCES episodes(id)  ON DELETE CASCADE,
  INDEX idx_br_ep (episode_id),
  INDEX idx_result_type (result_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='AI续写结果缓存表：避免同一分支重复调用豆包API，降低费用；支持text/image/video三种返回类型';

-- 初始种子数据：第67集
INSERT INTO episodes (episode_no, title, theme, total_duration, status, highlight_count)
VALUES (67, '北派寻宝笔记·第67集', '古墓探险', 363, 'done', 25);