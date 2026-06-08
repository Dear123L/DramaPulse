"""
更新图片分支的 ai_response 为真实续写文字（原来是占位内容）
"""
import sys
sys.path.insert(0, '.')
import config
import pymysql

updates = [
    (17, 'A', '你提着手电毅然踏入左侧岔道，脚底忽然踩到一片碎瓷，嘎吱声在墓道里回响。光柱在蔓延的陈腐气息中向前推进，隐约能看到前方有块黑色石碑立在尽头……'),
    (17, 'B', '你转身沿原路折返，靴底踩碎一层浮土，每一步都像在惊醒什么沉睡已久的东西。走了不到十步，背后传来一声沉闷的石板位移声——那扇岔路仿佛在你离开的瞬间自行关合……'),
    (17, 'C', '你摸出随身匕首，在岔口石壁上用力刻下两道十字印记。冷钢在砖石上划过的声音在密闭空间里格外清脆，粉白的石灰粉扑簌落下，标记深入石缝，即便再走一遍也不会迷失……'),
    (9,  'A', '你屏息迈步，靴尖稳稳落在棺椁旁的石板缝隙，黄铜棺钉在手电光下泛着幽绿冷晕。棺盖边沿有一道细小的磨痕，像是被人从内侧撑开过——你的心跳陡然加速……'),
    (9,  'B', '你侧身紧贴石壁向两侧散开，脚步轻得像踩在棉花上。队友的手电划出一道弧形，照亮了棺椁后方的暗龛——里面空无一物，却有一股隐约的沉香气息飘散开来……'),
    (9,  'C', '你攥紧拳头僵在原地，让前两人先行，腐腥混着陈腐麝香的风从前方穿堂而来，刮过颧骨带来一阵细细的寒意。棺椁在静默中纹丝不动，仿佛只是一具普通的石棺……'),
    (23, 'A', '你一步踏出门槛，脚底传来轻微的震颤，古墓的机关已被触发——前方通道缓缓升起，晨光在尽头漫进来，透过百年尘埃织成一道金色光柱。你听到了呼吸，是自己的，也是历史的……'),
    (23, 'B', '你凑近封印细看，石缝里有一行极细的刻字，字迹因年代久远已风化大半，隐约可辨"非时不开"四个字。封印表面温热，和周围冰凉的石壁形成诡异的对比，像是内部藏着某种热源……'),
    (23, 'C', '你向同伴发出撤退信号，迅速沿来路折返。身后的密室随着你的离开发出低沉的回响，石门以肉眼可见的速度慢慢合拢，最后一线光缝消失时，一种说不清楚的遗憾涌上心头……'),
]

conn = pymysql.connect(
    host=config.MYSQL_HOST, port=config.MYSQL_PORT,
    user=config.MYSQL_USER, password=config.MYSQL_PASSWORD,
    database=config.MYSQL_DATABASE, charset='utf8mb4', autocommit=True
)
cur = conn.cursor()
for hl_id, br_id, text in updates:
    cur.execute(
        'UPDATE branch_results SET ai_response=%s WHERE highlight_id=%s AND branch_id=%s',
        (text, hl_id, br_id)
    )
    print(f'HL#{hl_id:2d} {br_id}: {cur.rowcount} row updated')
conn.close()
print('done')
