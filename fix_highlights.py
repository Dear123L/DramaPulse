"""
修复 highlights 数据：增加多样性，不是所有高光点都有分支，选项也不全一样
"""
import json
import database

# 25个高光点的真实配置（基于场景描述设计不同的特效和分支）
FIXED_CONFIG = [
    # t=15  入口甬道 — 纯氛围，无分支
    {"id": 1,  "show_branch": False, "visual_effect": "flashlight_flicker", "particle_type": "dust_mote",     "haptic_pattern": "vibrate_light",          "audio_cue": "creak_sound",       "branch_options": []},
    # t=30  暗室绳梯 — 有分支（爬绳梯相关）
    {"id": 2,  "show_branch": True,  "visual_effect": "flashlight_flicker", "particle_type": "dust_mote",     "haptic_pattern": "vibrate_light",          "audio_cue": "creak_sound",       "branch_options": [
        {"id": "A", "text": "攀爬绳梯向上", "consequence": "发现上层墓室入口"},
        {"id": "B", "text": "检查绳梯牢固度", "consequence": "发现绳梯被虫蛀蚀"},
        {"id": "C", "text": "放弃绳梯另寻出路", "consequence": "在墙角发现暗门"}
    ]},
    # t=45  石砌甬道 — 纯氛围
    {"id": 3,  "show_branch": False, "visual_effect": "flashlight_flicker", "particle_type": "dust_mote",     "haptic_pattern": "vibrate_light",          "audio_cue": "creak_sound",       "branch_options": []},
    # t=60  青砖墓壁 — 有分支（暗号相关）
    {"id": 4,  "show_branch": True,  "visual_effect": "flashlight_flicker", "particle_type": None,            "haptic_pattern": "vibrate_light",          "audio_cue": None,                "branch_options": [
        {"id": "A", "text": "用手电照亮暗号仔细辨认", "consequence": "读出北派密语"},
        {"id": "B", "text": "拍照记录暗号", "consequence": "闪光灯惊动守墓虫群"},
        {"id": "C", "text": "忽略暗号继续前进", "consequence": "误入死胡同"}
    ]},
    # t=75  砖石甬道 — 纯氛围
    {"id": 5,  "show_branch": False, "visual_effect": "flashlight_flicker", "particle_type": "dust_mote",     "haptic_pattern": "vibrate_light",          "audio_cue": "creak_sound",       "branch_options": []},
    # t=90  密闭墓室 — 心跳高潮！无分支（纯情绪）
    {"id": 6,  "show_branch": False, "visual_effect": "heartbeat_pulse",    "particle_type": "dark_fog",      "haptic_pattern": "vibrate_pattern_heartbeat", "audio_cue": "low_freq_drone",    "branch_options": []},
    # t=105 壁画甬道 — 有分支
    {"id": 7,  "show_branch": True,  "visual_effect": "flashlight_flicker", "particle_type": "dust_mote",     "haptic_pattern": "vibrate_light",          "audio_cue": "creak_sound",       "branch_options": [
        {"id": "A", "text": "触摸壁画试探", "consequence": "壁画脱落露出机关"},
        {"id": "B", "text": "用工具撬开壁画", "consequence": "触发毒气喷射"},
        {"id": "C", "text": "绕行不碰壁画", "consequence": "安全通过但错过线索"}
    ]},
    # t=120 墓道转角 — 纯氛围
    {"id": 8,  "show_branch": False, "visual_effect": "flashlight_flicker", "particle_type": "dust_mote",     "haptic_pattern": "vibrate_light",          "audio_cue": "creak_sound",       "branch_options": []},
    # t=135 主墓室入口 — 有分支
    {"id": 9,  "show_branch": True,  "visual_effect": "flashlight_flicker", "particle_type": None,            "haptic_pattern": "vibrate_light",          "audio_cue": None,                "branch_options": [
        {"id": "A", "text": "径直走向棺椁", "consequence": "踩中地板机关"},
        {"id": "B", "text": "先检查四周陪葬品", "consequence": "发现珍贵玉器但触发警报"},
        {"id": "C", "text": "在入口观察不动", "consequence": "发现墓顶有渗水危险"}
    ]},
    # t=150 陪葬品区 — 纯氛围
    {"id": 10, "show_branch": False, "visual_effect": "flashlight_flicker", "particle_type": "dust_mote",     "haptic_pattern": "vibrate_light",          "audio_cue": "creak_sound",       "branch_options": []},
    # t=165 甬道深处 — 有分支
    {"id": 11, "show_branch": True,  "visual_effect": "flashlight_flicker", "particle_type": "dust_mote",     "haptic_pattern": "vibrate_light",          "audio_cue": "creak_sound",       "branch_options": [
        {"id": "A", "text": "点燃火把照明", "consequence": "火光吸引未知生物"},
        {"id": "B", "text": "关闭手电摸黑前进", "consequence": "撞见守墓人影"},
        {"id": "C", "text": "原地呼叫队友", "consequence": "回声暴露位置"}
    ]},
    # t=180 墓室侧室 — 心跳高潮！无分支
    {"id": 12, "show_branch": False, "visual_effect": "heartbeat_pulse",    "particle_type": "dark_fog",      "haptic_pattern": "vibrate_pattern_heartbeat", "audio_cue": "low_freq_drone",    "branch_options": []},
    # t=195 暗门区域 — 有分支
    {"id": 13, "show_branch": True,  "visual_effect": "flashlight_flicker", "particle_type": None,            "haptic_pattern": "vibrate_light",          "audio_cue": None,                "branch_options": [
        {"id": "A", "text": "推开暗门", "consequence": "发现密室藏宝图"},
        {"id": "B", "text": "敲击暗门试探", "consequence": "暗门后传来回应敲击"},
        {"id": "C", "text": "绕开暗门", "consequence": "暗门自动打开涌出黑雾"}
    ]},
    # t=210 甬道尽头 — 纯氛围
    {"id": 14, "show_branch": False, "visual_effect": "flashlight_flicker", "particle_type": "dust_mote",     "haptic_pattern": "vibrate_light",          "audio_cue": "creak_sound",       "branch_options": []},
    # t=225 墓室回廊 — 有分支
    {"id": 15, "show_branch": True,  "visual_effect": "flashlight_flicker", "particle_type": "dust_mote",     "haptic_pattern": "vibrate_light",          "audio_cue": "creak_sound",       "branch_options": [
        {"id": "A", "text": "沿着回廊左侧走", "consequence": "发现殉葬坑"},
        {"id": "B", "text": "沿着回廊右侧走", "consequence": "遇到流沙陷阱"},
        {"id": "C", "text": "在回廊中间停下", "consequence": "地面塌陷坠入下层"}
    ]},
    # t=255 机关密室 — 心跳高潮！无分支
    {"id": 16, "show_branch": False, "visual_effect": "heartbeat_pulse",    "particle_type": "dark_fog",      "haptic_pattern": "vibrate_pattern_heartbeat", "audio_cue": "low_freq_drone",    "branch_options": []},
    # t=270 甬道岔口 — 有分支
    {"id": 17, "show_branch": True,  "visual_effect": "flashlight_flicker", "particle_type": "dust_mote",     "haptic_pattern": "vibrate_light",          "audio_cue": "creak_sound",       "branch_options": [
        {"id": "A", "text": "走左侧岔道", "consequence": "发现古代兵器库"},
        {"id": "B", "text": "走右侧岔道", "consequence": "进入毒气弥漫区"},
        {"id": "C", "text": "在岔口做标记", "consequence": "标记被神秘力量抹去"}
    ]},
    # t=285 墓室天井 — 纯氛围
    {"id": 18, "show_branch": False, "visual_effect": "flashlight_flicker", "particle_type": "dust_mote",     "haptic_pattern": "vibrate_light",          "audio_cue": "creak_sound",       "branch_options": []},
    # t=300 地下暗河 — 有分支
    {"id": 19, "show_branch": True,  "visual_effect": "flashlight_flicker", "particle_type": None,            "haptic_pattern": "vibrate_light",          "audio_cue": None,                "branch_options": [
        {"id": "A", "text": "涉水过河", "consequence": "水中发现古代沉船"},
        {"id": "B", "text": "寻找桥梁", "consequence": "桥是幻觉一踏即空"},
        {"id": "C", "text": "沿河岸绕行", "consequence": "发现河岸刻字"}
    ]},
    # t=315 墓室祭坛 — 纯氛围
    {"id": 20, "show_branch": False, "visual_effect": "flashlight_flicker", "particle_type": "dust_mote",     "haptic_pattern": "vibrate_light",          "audio_cue": "creak_sound",       "branch_options": []},
    # t=330 甬道崩塌区 — 有分支
    {"id": 21, "show_branch": True,  "visual_effect": "flashlight_flicker", "particle_type": "dust_mote",     "haptic_pattern": "vibrate_light",          "audio_cue": "creak_sound",       "branch_options": [
        {"id": "A", "text": "快速冲过崩塌区", "consequence": "被落石砸伤但逃出"},
        {"id": "B", "text": "寻找支撑点慢慢通过", "consequence": "发现崩塌后的新通道"},
        {"id": "C", "text": "退回寻找其他路", "consequence": "退路已被完全封死"}
    ]},
    # t=343 墓室核心区 — 心跳高潮！无分支
    {"id": 22, "show_branch": False, "visual_effect": "heartbeat_pulse",    "particle_type": "dark_fog",      "haptic_pattern": "vibrate_pattern_heartbeat", "audio_cue": "low_freq_drone",    "branch_options": []},
    # t=345 棺椁前 — 有分支（终极选择）
    {"id": 23, "show_branch": True,  "visual_effect": "flashlight_flicker", "particle_type": None,            "haptic_pattern": "vibrate_light",          "audio_cue": None,                "branch_options": [
        {"id": "A", "text": "打开棺椁", "consequence": "发现墓主人留下的终极秘密"},
        {"id": "B", "text": "绕行棺椁", "consequence": "发现棺椁下方的逃生通道"},
        {"id": "C", "text": "跪拜棺椁", "consequence": "触发墓主人生前设下的祝福机关"}
    ]},
    # t=348 墓室出口 — 纯氛围
    {"id": 24, "show_branch": False, "visual_effect": "flashlight_flicker", "particle_type": "dust_mote",     "haptic_pattern": "vibrate_light",          "audio_cue": "creak_sound",       "branch_options": []},
    # t=353 最终甬道 — 有分支（逃出方式）
    {"id": 25, "show_branch": True,  "visual_effect": "flashlight_flicker", "particle_type": "dust_mote",     "haptic_pattern": "vibrate_light",          "audio_cue": "creak_sound",       "branch_options": [
        {"id": "A", "text": "从原路返回", "consequence": "发现来时的路已变"},
        {"id": "B", "text": "寻找新出口", "consequence": "发现墓室设计师的逃生密道"},
        {"id": "C", "text": "触发自毁机关同归于尽", "consequence": "意外发现机关后是另一座古墓"}
    ]},
]

def fix_highlights():
    conn = database.get_connection()
    cur = conn.cursor()

    for cfg in FIXED_CONFIG:
        hid = cfg["id"]
        show_branch = 1 if cfg["show_branch"] else 0
        visual = cfg["visual_effect"]
        particle = cfg["particle_type"]
        haptic = cfg["haptic_pattern"]
        audio = cfg["audio_cue"]
        branches = json.dumps(cfg["branch_options"], ensure_ascii=False) if cfg["branch_options"] else "[]"

        cur.execute("""
            UPDATE highlights
            SET show_branch = %s,
                visual_effect = %s,
                particle_type = %s,
                haptic_pattern = %s,
                audio_cue = %s,
                branch_options = %s
            WHERE id = %s
        """, (show_branch, visual, particle, haptic, audio, branches, hid))
        print(f"  更新 #{hid:02d}: show_branch={show_branch}, visual={visual}, particle={particle}, audio={audio}, branches={len(cfg['branch_options'])}个")

    conn.commit()
    print("\n✅ 全部25个高光点已更新")

    # 统计
    cur.execute("SELECT show_branch, visual_effect, COUNT(*) FROM highlights GROUP BY show_branch, visual_effect")
    print("\n更新后统计:")
    for row in cur.fetchall():
        print(f"  show_branch={row['show_branch']}, visual={row['visual_effect']}: {row['COUNT(*)']}个")

if __name__ == "__main__":
    fix_highlights()
