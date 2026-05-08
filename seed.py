"""種子資料：6 位學員 + 12 門課程"""
import json
from database import db_session, init_schema

STAGE_BENCHMARKS = {
    '實習醫學生':    {'PC': 2.0, 'MK': 2.0, 'PBLI': 1.5, 'ICS': 2.0, 'Prof': 2.5, 'SBP': 1.5},
    'PGY1':         {'PC': 3.0, 'MK': 3.0, 'PBLI': 2.5, 'ICS': 3.0, 'Prof': 3.5, 'SBP': 2.5},
    'PGY1 中醫外訓': {'PC': 3.0, 'MK': 3.0, 'PBLI': 2.5, 'ICS': 3.0, 'Prof': 3.5, 'SBP': 2.5},
    'PGY2 不分組':   {'PC': 4.0, 'MK': 4.0, 'PBLI': 3.5, 'ICS': 4.0, 'Prof': 4.0, 'SBP': 3.5},
    'PGY2 內科組':   {'PC': 4.2, 'MK': 4.2, 'PBLI': 3.8, 'ICS': 4.2, 'Prof': 4.2, 'SBP': 3.8},
}
DIMENSIONS = ['PC', 'MK', 'PBLI', 'ICS', 'Prof', 'SBP']

EMPLOYEES = [
    {'employee_id': 'P10001', 'name': '學員A (內科)', 'avatar': 'A', 'gender': '男',
     'stage': 'PGY1', 'dept': '一般醫學內科 (3 個月)', 'month': '第 2 個月',
     'mentor': '示範教師', 'overall_progress': 35, 'team_status': 'green',
     'competencies': [2.5, 2.7, 2.0, 2.7, 3.2, 2.0],
     'ilp': {'goal': '急症處理能力，插管、CPR、胸管、CVC',
             'motivation': '想走急診', 'strategy': '走急診時多在急診觀看參與急救',
             'resources': '資深學長姐指導、模擬急救場景', 'barriers': '實際操作機會少',
             'kpi': '能在不需幫助的情況下獨立完成操作', 'timeline': '半年', 'eportfolio_rating': 3},
     'milestones': [('done', 'BLS / ACLS 取證', ''), ('done', 'PGY1 第 1 個月 一般內科 完訓', ''),
                    ('active', '第 2 個月 心臟內科', ''), ('active', '本月 4 例完整出院病摘', ''),
                    ('active', 'CVC 模擬訓練 (技能中心)', ''), ('future', '第 3 個月 胸腔內科', ''),
                    ('future', '至少 1 例 4 Box 醫學倫理討論', ''), ('future', '參加 PGY 急救聯合演練', '')],
     'monthly_req': [('4 例完整出院病摘', 1, 4), ('Mini-CEX 評核', 2, 3), ('CbD 評核', 1, 1),
                     ('360 度評量', 0, 1), ('案例分析報告', 0, 1)],
     'weekly_focus': [('本週至少參與 1 例 CVC 操作 (即使是觀摩)', 'PC', 'high'),
                      ('完成 EBM 期刊報告 (急性 STEMI 處置)', 'PBLI', 'normal'),
                      ('本月已完成 1/4 例出院病摘，加快進度', 'MK', 'normal')]},
    {'employee_id': 'P10002', 'name': '學員B (內科)', 'avatar': 'B', 'gender': '女',
     'stage': 'PGY1', 'dept': '一般醫學內科 (3 個月)', 'month': '第 1 個月',
     'mentor': '示範教師', 'overall_progress': 22, 'team_status': 'amber',
     'competencies': [2.2, 2.5, 1.8, 2.5, 3.0, 1.8],
     'ilp': {'goal': '值班處理 complain，怎麼 on CVC',
             'motivation': '在值班時容易緊張，還不會放 CVC',
             'strategy': '想要有多練習，也學長姐帶的機會',
             'resources': '在內科如果有要放 CVC 的可以有個群組通知',
             'barriers': '實際操作機會有限', 'kpi': '同上',
             'timeline': '預計 PGY2 前能學會', 'eportfolio_rating': 4},
     'milestones': [('done', 'BLS / ACLS 取證', ''), ('active', '第 1 個月 一般內科 9A 病房', ''),
                    ('active', 'CVC 模擬訓練 (技能中心)', ''), ('active', '本月 4 例完整出院病摘', ''),
                    ('future', '第 2 個月 胸腔內科', ''), ('future', 'CVC 實際操作 (期望 2 例 supervised)', ''),
                    ('future', 'OSCE 季度測驗', '')],
     'monthly_req': [('4 例完整出院病摘', 0, 4), ('Mini-CEX 評核', 1, 3), ('CbD 評核', 0, 1),
                     ('360 度評量', 0, 1), ('案例分析報告', 0, 1)],
     'weekly_focus': [('高優先：申請加入「內科 CVC 通知群組」', 'PC', 'high'),
                      ('本週值班至少 2 次跟資深 R 帶 unstable 病人', 'PC', 'high'),
                      ('完成第一例出院病摘並請臨床教師回饋', 'MK', 'normal')]},
    {'employee_id': 'P10003', 'name': '學員C (內科)', 'avatar': 'C', 'gender': '男',
     'stage': 'PGY1', 'dept': '一般醫學內科 (3 個月)', 'month': '第 3 個月',
     'mentor': '示範教師', 'overall_progress': 78, 'team_status': 'green',
     'competencies': [3.2, 3.5, 2.8, 3.2, 3.8, 2.7],
     'ilp': {'goal': '電解質（K, Mg, Ca）或 Tachyarrythmia 急性矯正給藥方式',
             'motivation': '比較不熟悉', 'strategy': '清楚指引 + 實作 + 與學長姐討論',
             'resources': '實作後與學長姐討論', 'barriers': '不一定遇到相關個案',
             'kpi': '成功照顧相關病人', 'timeline': '三個月', 'eportfolio_rating': 4},
     'milestones': [('done', 'BLS / ACLS 取證', ''), ('done', 'PGY1 第 1-2 個月 一般內科 完訓', ''),
                    ('done', '已完成 8 例出院病摘', ''), ('active', '第 3 個月 腎臟內科', ''),
                    ('active', '製作院內電解質急救 SOP 簡報', ''), ('active', 'Tachyarrhythmia 個案 CbD', ''),
                    ('future', 'PGY1 完訓總結評估', ''), ('future', 'PGY2 訓練組志願選填', ''),
                    ('future', 'OSCE 季度測驗', '')],
     'monthly_req': [('4 例完整出院病摘', 4, 4), ('Mini-CEX 評核', 3, 3), ('CbD 評核', 1, 1),
                     ('360 度評量', 1, 1), ('案例分析報告', 1, 1)],
     'weekly_focus': [('本週請主治指定 1 例 hyperkalemia 學習病例', 'MK', 'normal'),
                      ('完成 PGY1 完訓自我評核問卷', 'PBLI', 'high'),
                      ('報告 Tachyarrhythmia EBM 期刊', 'PBLI', 'normal')]},
    {'employee_id': 'P10004', 'name': '學員D (內科)', 'avatar': 'D', 'gender': '女',
     'stage': 'PGY2 內科組', 'dept': '8 個月內科 (含 1 個月急診)', 'month': '第 4 個月 (新陳代謝科)',
     'mentor': '示範教師', 'overall_progress': 48, 'team_status': 'amber',
     'competencies': [3.5, 3.7, 3.0, 3.5, 4.0, 3.0],
     'ilp': {'goal': '各大科急症 / 加強內科次專科急症處理能力',
             'motivation': '值班需求，病人安全', 'strategy': '相關課程加強模擬',
             'resources': '相關課程加強模擬', 'barriers': '課程可線上化以免時間相衝',
             'kpi': '模擬練習題', 'timeline': '三個月內', 'eportfolio_rating': 3},
     'milestones': [('done', 'PGY1 內科訓練完訓', ''), ('done', '一般內科 3 個月（PGY2）', ''),
                    ('done', '急診 1 個月', ''), ('done', '心臟內科', ''),
                    ('active', '新陳代謝科 (本月)', ''), ('active', 'POCUS 進階訓練', ''),
                    ('future', '第 5 個月 腎臟內科', ''), ('future', '第 6-8 個月 神內 / 胸腔 / 肝膽胃腸', ''),
                    ('future', 'PGY2 完訓總結', '')],
     'monthly_req': [('4 例完整出院病摘', 2, 4), ('Mini-CEX 評核', 1, 1), ('CbD 評核', 1, 1),
                     ('360 度評量', 0, 1), ('案例分析報告', 0, 1)],
     'weekly_focus': [('高優先：本週完成新陳代謝科 DKA 急救模擬', 'PC', 'high'),
                      ('加強 PBLI：本月 14 天再入院討論會擔任主討論', 'PBLI', 'high'),
                      ('SDM 課程第 2 場參加', 'SBP', 'normal')]},
    {'employee_id': 'P10005', 'name': '學員E (內科)', 'avatar': 'E', 'gender': '男',
     'stage': 'PGY2 內科組', 'dept': '8 個月內科 (含 1 個月急診)', 'month': '第 6 個月 (神經內科)',
     'mentor': '示範教師', 'overall_progress': 72, 'team_status': 'green',
     'competencies': [3.8, 4.0, 3.5, 3.5, 4.2, 3.5],
     'ilp': {'goal': 'AI 應用在論文寫作', 'motivation': 'AI 浪潮、論文要求越來越高',
             'strategy': '學習論文寫作技巧', 'resources': '有投稿過的學長姐、主治醫師',
             'barriers': '臨床時間有限', 'kpi': '發表成果',
             'timeline': '一年以上', 'eportfolio_rating': 3},
     'milestones': [('done', 'PGY1 完訓', ''), ('done', 'PGY2 一般內科 / 急診 / 心內 / 新陳代謝 / 腎內', ''),
                    ('done', '完成 case report 1 篇 (院內海報)', ''), ('active', '神經內科 (本月)', ''),
                    ('active', '次專科甄選準備', ''), ('active', '探索 AI 輔助文獻檢索', ''),
                    ('future', '第 7 個月 胸腔', ''), ('future', '第 8 個月 肝膽胃腸', ''),
                    ('future', '次專科 R1 報到', ''), ('future', '初稿 case report 投稿', '')],
     'monthly_req': [('4 例完整出院病摘', 3, 4), ('Mini-CEX 評核', 1, 1), ('CbD 評核', 1, 1),
                     ('360 度評量', 1, 1), ('案例分析報告', 1, 1)],
     'weekly_focus': [('本週嘗試以 PubMed MCP + AI 協助文獻整理', 'PBLI', 'normal'),
                      ('神經內科必訓技能 LP 完成 supervised 操作', 'PC', 'high'),
                      ('完成案例分析報告主題：AI 輔助 EBM', 'PBLI', 'normal')]},
    {'employee_id': 'P10006', 'name': '學員F (內科)', 'avatar': 'F', 'gender': '男',
     'stage': 'PGY1', 'dept': '一般醫學內科 (3 個月)', 'month': '第 2 個月',
     'mentor': '示範教師', 'overall_progress': 40, 'team_status': 'amber',
     'competencies': [2.5, 2.8, 2.0, 2.5, 3.2, 2.0],
     'ilp': {'goal': 'POCUS', 'motivation': '值班時候 survey 病人',
             'strategy': '值班時候病人數少，才有時間想處置',
             'resources': '手持超音波', 'barriers': '臨床太忙',
             'kpi': '無', 'timeline': '2 年', 'eportfolio_rating': 4},
     'milestones': [('done', 'BLS / ACLS 取證', ''), ('done', 'PGY1 第 1 個月 一般內科', ''),
                    ('active', '第 2 個月 肝膽胃腸科', ''), ('active', 'POCUS 基礎課程', ''),
                    ('active', '本月 4 例出院病摘', ''), ('future', '第 3 個月 感染科', ''),
                    ('future', 'POCUS 實作測驗', ''), ('future', 'OSCE 季度測驗', '')],
     'monthly_req': [('4 例完整出院病摘', 1, 4), ('Mini-CEX 評核', 2, 3), ('CbD 評核', 0, 1),
                     ('360 度評量', 0, 1), ('案例分析報告', 0, 1)],
     'weekly_focus': [('高優先：你的 KPI 為「無」，本週與導師重新訂 POCUS SMART 目標', 'PBLI', 'high'),
                      ('本週至少 2 次手持超音波 supervised 操作', 'PC', 'normal'),
                      ('完成第 2 個月出院病摘 1/4', 'MK', 'normal')]},
]

RESOURCES = [
    ('院內', 'PC', '一般醫學內科示範病房 (9A)', '40 床專屬病房，每日教學迴診 2 小時', '醫療大樓 9 樓', ['CVC', 'CPR', '臨床技能']),
    ('skill', 'PC', '臨床技能中心 - CVC 模擬訓練', '高擬真假人 + 超音波導引', '臨床訓練中心', ['CVC', 'POCUS']),
    ('skill', 'PC', '臨床技能中心 - OSCE 訓練', '15 站國家級 OSCE 考場', '每季 1 次', ['OSCE']),
    ('skill', 'PC', '動物實驗中心 (Wet lab)', '微創 / 內視鏡 / 達文西', '研究大樓', ['procedure']),
    ('院內', 'MK', '晨會 (Morning Meeting)', '臨床病例討論', '週一三五 7:30', ['MK', '病例']),
    ('院內', 'PBLI', 'EBM 期刊文獻選讀討論會', '實證文獻報告', '每週四 7:30', ['EBM', 'PBLI']),
    ('院內', 'PBLI', '14 天再入院討論會', 'Health-care Matrix', '每月 1 次', ['PBLI']),
    ('院內', 'MK', 'Grand Round', '院級臨床大查房', '每週 1 次', ['MK']),
    ('院內', 'Prof', '醫學倫理討論會 (4 Box)', '臨床倫理 4 Box 分析', '每月 1 次', ['倫理', 'Prof']),
    ('院內', 'ICS', 'CICARE 醫病溝通課程', 'PGY 必修', '每月 2 次', ['溝通', 'CICARE']),
    ('院內', 'SBP', '跨領域團隊合作會議', '建立跨職類互動', '每月 1 次', ['SBP', '團隊']),
    ('院內', 'SBP', '醫療品質 / 感染控制討論會', '醫療品質與感控', '每月各 1 次', ['SBP']),
    ('book', 'MK', '奇美醫院內科工作規範', '院內 SOP', '院內提供', ['SOP']),
    ('book', 'MK', 'Washington Manual', '內科治療標準', '圖書館', ['MK', '治療']),
    ('book', 'MK', "Harrison's Principles", '內科', '圖書館', ['MK']),
    ('online', 'MK', '圖書館電子資源', '電子期刊、電子書', '院內外可用', ['MK', '文獻']),
    ('online', 'PBLI', 'E-portfolio 電子歷程', '案例登錄、評核', '院內系統', ['PBLI']),
    ('skill', 'PC', '胃腸內科 內視鏡訓練', '住院醫師可實際操作', '胃腸內科協調', ['endoscopy']),
]

COURSES = [
    {'course_code': 'ONLINE-CICARE', 'title': 'CICARE 醫病溝通模式 線上自學',
     'description': '透過情境影片學習 CICARE 5 步驟', 'type': 'online',
     'instructor': '醫教部', 'location': '院內 e-learning 平台',
     'competency_uplift': {'ICS': 0.3, 'Prof': 0.1}, 'duration_minutes': 90,
     'schedule_type': 'on_demand', 'credit_hours': 1.5,
     'content_url': 'https://elearning.chimei.org.tw/cicare-pgy',
     'tags': ['CICARE', '溝通', 'ICS', 'PGY 必修']},
    {'course_code': 'ONLINE-ETHICS', 'title': '醫學倫理線上測驗（年度必修）',
     'description': '醫療倫理 4 box 工具 + 案例分析測驗', 'type': 'online',
     'instructor': '醫教部', 'location': '院內 e-learning 平台',
     'competency_uplift': {'Prof': 0.2}, 'duration_minutes': 60,
     'schedule_type': 'on_demand', 'credit_hours': 1.0,
     'tags': ['倫理', 'Prof', '4 box', '年度必修']},
    {'course_code': 'ONLINE-INFECTION', 'title': '院內感染控制 線上課程',
     'description': '手部衛生、隔離防護、針扎防範', 'type': 'online',
     'instructor': '感管中心', 'location': '院內 e-learning 平台',
     'competency_uplift': {'SBP': 0.15, 'Prof': 0.05}, 'duration_minutes': 45,
     'schedule_type': 'on_demand', 'credit_hours': 0.75,
     'tags': ['感控', 'SBP', '年度必修']},
    {'course_code': 'SKILL-CVC-001', 'title': '臨床技能中心 - CVC 中央靜脈導管 模擬訓練',
     'description': '高擬真假人 + 超音波導引模擬，4 小時實作', 'type': 'skill',
     'instructor': '示範教師', 'location': '臨床訓練中心 3F 模擬室',
     'competency_uplift': {'PC': 0.4, 'MK': 0.1}, 'duration_minutes': 240,
     'schedule_type': 'recurring', 'scheduled_at': '每月第 2 週 週六 09:00',
     'credit_hours': 4.0, 'requires_qr_checkin': 1, 'requires_instructor_signoff': 1,
     'capacity': 8, 'tags': ['CVC', 'PC', '中央靜脈', '技能中心']},
    {'course_code': 'SKILL-POCUS-001', 'title': '床邊超音波 (POCUS) 基礎工作坊',
     'description': 'RUSH protocol 實作', 'type': 'skill',
     'instructor': '示範教師', 'location': '臨床訓練中心 2F',
     'competency_uplift': {'PC': 0.3, 'MK': 0.2}, 'duration_minutes': 360,
     'schedule_type': 'recurring', 'scheduled_at': '每季 1 場',
     'credit_hours': 6.0, 'requires_qr_checkin': 1, 'requires_instructor_signoff': 1,
     'capacity': 12, 'tags': ['POCUS', 'PC', '超音波']},
    {'course_code': 'SKILL-OSCE-Q1', 'title': 'OSCE 季度測驗 (15 站)',
     'description': '15 站國家級 OSCE 模擬測驗', 'type': 'skill',
     'instructor': '臨床訓練中心', 'location': '臨床訓練中心 1F OSCE 考場',
     'competency_uplift': {'PC': 0.3, 'ICS': 0.2, 'MK': 0.1}, 'duration_minutes': 120,
     'schedule_type': 'recurring', 'scheduled_at': '每季最後一週',
     'credit_hours': 2.0, 'requires_qr_checkin': 1, 'requires_instructor_signoff': 1,
     'tags': ['OSCE', 'PC', 'ICS']},
    {'course_code': 'INPERSON-MORNING', 'title': '一般醫學內科晨會（週一三五）',
     'description': '臨床病例討論', 'type': 'in_person',
     'instructor': '示範教師', 'location': '9A 病房討論室',
     'competency_uplift': {'MK': 0.05, 'PBLI': 0.05}, 'duration_minutes': 60,
     'schedule_type': 'recurring', 'scheduled_at': '週一/三/五 07:30',
     'credit_hours': 1.0, 'requires_qr_checkin': 1, 'auto_complete_after_signin': 1,
     'tags': ['MK', 'PBLI', '晨會']},
    {'course_code': 'INPERSON-EBM', 'title': 'EBM 期刊文獻選讀討論會',
     'description': '輪流由學員依臨床情境搜尋實證文獻並報告', 'type': 'in_person',
     'instructor': '示範教師', 'location': '9A 病房討論室',
     'competency_uplift': {'PBLI': 0.15, 'MK': 0.05}, 'duration_minutes': 60,
     'schedule_type': 'recurring', 'scheduled_at': '週四 07:30',
     'credit_hours': 1.0, 'requires_qr_checkin': 1, 'auto_complete_after_signin': 1,
     'tags': ['EBM', 'PBLI']},
    {'course_code': 'INPERSON-GR', 'title': 'Grand Round 院級臨床大查房',
     'description': '院級疑難病例討論', 'type': 'in_person',
     'instructor': '示範教師（與客座專家）', 'location': '院區大會議室',
     'competency_uplift': {'MK': 0.15}, 'duration_minutes': 60,
     'schedule_type': 'recurring', 'scheduled_at': '週五 07:30',
     'credit_hours': 1.0, 'requires_qr_checkin': 1, 'auto_complete_after_signin': 1,
     'tags': ['MK', 'Grand Round']},
    {'course_code': 'INPERSON-MM', 'title': '14 天再入院 / 死亡及疾病討論會',
     'description': 'Health-care Matrix 工具', 'type': 'in_person',
     'instructor': '示範教師', 'location': '9A 病房討論室',
     'competency_uplift': {'PBLI': 0.2, 'SBP': 0.15}, 'duration_minutes': 60,
     'schedule_type': 'recurring', 'scheduled_at': '每月最後一週週三 14:00',
     'credit_hours': 1.0, 'requires_qr_checkin': 1, 'requires_instructor_signoff': 1,
     'tags': ['PBLI', 'SBP', 'M&M']},
    {'course_code': 'EXTERNAL-ACLS', 'title': 'ACLS 高級心臟救命術 認證',
     'description': '美國心臟學會 ACLS 認證課程', 'type': 'external',
     'instructor': '台灣 ACLS 訓練中心', 'location': '自選認證機構',
     'competency_uplift': {'PC': 0.3, 'MK': 0.2}, 'duration_minutes': 960,
     'schedule_type': 'on_demand', 'credit_hours': 16.0, 'cme_credits': 16.0,
     'requires_certificate_upload': 1,
     'tags': ['ACLS', 'PC', 'MK', '急救', '外部認證']},
    {'course_code': 'EXTERNAL-ATLS', 'title': 'ATLS 高級創傷救命術 認證',
     'description': 'ACS-COT 認證', 'type': 'external',
     'instructor': 'ACS-COT 認證機構', 'location': '外部訓練中心',
     'competency_uplift': {'PC': 0.3, 'MK': 0.2}, 'duration_minutes': 960,
     'schedule_type': 'on_demand', 'credit_hours': 16.0, 'cme_credits': 16.0,
     'requires_certificate_upload': 1,
     'tags': ['ATLS', 'PC', '創傷', '外部認證']},
]

SAMPLE_ENROLLMENTS = [
    ('P10001', 'SKILL-CVC-001', 'registered'),
    ('P10001', 'ONLINE-CICARE', 'in_progress'),
    ('P10001', 'INPERSON-MORNING', 'completed'),
    ('P10001', 'INPERSON-EBM', 'in_progress'),
    ('P10002', 'SKILL-CVC-001', 'registered'),
    ('P10002', 'ONLINE-CICARE', 'registered'),
    ('P10002', 'INPERSON-MORNING', 'in_progress'),
    ('P10003', 'INPERSON-MORNING', 'completed'),
    ('P10003', 'INPERSON-EBM', 'completed'),
    ('P10003', 'INPERSON-GR', 'completed'),
    ('P10003', 'ONLINE-ETHICS', 'completed'),
    ('P10003', 'EXTERNAL-ACLS', 'completed'),
    ('P10004', 'EXTERNAL-ACLS', 'completed'),
    ('P10004', 'SKILL-POCUS-001', 'in_progress'),
    ('P10004', 'INPERSON-MM', 'in_progress'),
    ('P10005', 'EXTERNAL-ACLS', 'completed'),
    ('P10005', 'EXTERNAL-ATLS', 'completed'),
    ('P10005', 'SKILL-OSCE-Q1', 'completed'),
    ('P10006', 'SKILL-POCUS-001', 'registered'),
    ('P10006', 'INPERSON-MORNING', 'in_progress'),
]

SAMPLE_REFLECTIONS = {
    'P10001': ['本週主管帶我看一個 thyroid storm 病人，第一次完整跟到從急診到加護病房。',
               '收到 PBLI 評估回饋說我案例討論引用文獻不足。下週開始固定每週讀 1 篇 NEJM Resident 360。'],
    'P10003': ['本週成功處理一個 hyperkalemia 病人（K=6.8）。'],
    'P10004': ['第一個月新陳代謝科最大收穫是搞懂 DKA 的 anion gap 計算。'],
}


def seed():
    init_schema()
    with db_session() as conn:
        for tbl in ['attendance_logs', 'qr_tokens', 'enrollments', 'courses',
                    'weekly_focus', 'monthly_requirements', 'milestones', 'reflections',
                    'ilps', 'competencies', 'evaluations', 'coach_messages',
                    'employees', 'stage_benchmarks', 'resources']:
            conn.execute(f"DELETE FROM {tbl}")

        for stage, dims in STAGE_BENCHMARKS.items():
            for dim, score in dims.items():
                conn.execute("INSERT INTO stage_benchmarks (stage, dimension, score) VALUES (?, ?, ?)",
                             (stage, dim, score))

        for emp in EMPLOYEES:
            conn.execute("""INSERT INTO employees (employee_id, name, avatar, gender, stage, dept, month, mentor, overall_progress, team_status)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (emp['employee_id'], emp['name'], emp['avatar'], emp['gender'],
                 emp['stage'], emp['dept'], emp['month'], emp['mentor'],
                 emp['overall_progress'], emp['team_status']))
            for i, dim in enumerate(DIMENSIONS):
                conn.execute("INSERT INTO competencies (employee_id, dimension, score, evaluator) VALUES (?, ?, ?, ?)",
                             (emp['employee_id'], dim, emp['competencies'][i], emp['mentor']))
            ilp = emp['ilp']
            conn.execute("""INSERT INTO ilps (employee_id, goal, motivation, strategy, resources, barriers, kpi, timeline, eportfolio_rating)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (emp['employee_id'], ilp['goal'], ilp['motivation'], ilp['strategy'],
                 ilp['resources'], ilp['barriers'], ilp['kpi'], ilp['timeline'], ilp['eportfolio_rating']))
            for order, (status, title, desc) in enumerate(emp['milestones']):
                conn.execute("INSERT INTO milestones (employee_id, status, title, description, sort_order) VALUES (?, ?, ?, ?, ?)",
                             (emp['employee_id'], status, title, desc, order))
            for item, done, total in emp['monthly_req']:
                conn.execute("INSERT INTO monthly_requirements (employee_id, item, done, total) VALUES (?, ?, ?, ?)",
                             (emp['employee_id'], item, done, total))
            for title, tag, urgency in emp['weekly_focus']:
                conn.execute("INSERT INTO weekly_focus (employee_id, title, tag, urgency) VALUES (?, ?, ?, ?)",
                             (emp['employee_id'], title, tag, urgency))
            if emp['employee_id'] in SAMPLE_REFLECTIONS:
                for content in SAMPLE_REFLECTIONS[emp['employee_id']]:
                    conn.execute("INSERT INTO reflections (employee_id, content) VALUES (?, ?)",
                                 (emp['employee_id'], content))

        for type_, tag, title, desc, meta, keywords in RESOURCES:
            conn.execute("INSERT INTO resources (type, tag, title, description, meta, match_keywords) VALUES (?, ?, ?, ?, ?, ?)",
                         (type_, tag, title, desc, meta, json.dumps(keywords, ensure_ascii=False)))

        for c in COURSES:
            conn.execute("""INSERT INTO courses (course_code, title, description, type, instructor, location,
                            competency_uplift, duration_minutes, schedule_type, scheduled_at, credit_hours, cme_credits,
                            requires_qr_checkin, requires_instructor_signoff, requires_certificate_upload,
                            auto_complete_after_signin, content_url, capacity, tags)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (c['course_code'], c['title'], c['description'], c['type'],
                 c.get('instructor'), c.get('location'),
                 json.dumps(c['competency_uplift'], ensure_ascii=False),
                 c.get('duration_minutes', 60), c.get('schedule_type', 'on_demand'),
                 c.get('scheduled_at'), c.get('credit_hours', 0), c.get('cme_credits', 0),
                 c.get('requires_qr_checkin', 0), c.get('requires_instructor_signoff', 0),
                 c.get('requires_certificate_upload', 0), c.get('auto_complete_after_signin', 0),
                 c.get('content_url'), c.get('capacity', 100),
                 json.dumps(c.get('tags', []), ensure_ascii=False)))

        for emp_id, code, status in SAMPLE_ENROLLMENTS:
            course = conn.execute("SELECT id FROM courses WHERE course_code = ?", (code,)).fetchone()
            if not course:
                continue
            if status == 'completed':
                conn.execute("""INSERT INTO enrollments (employee_id, course_id, status, completed_at, final_score)
                                VALUES (?, ?, 'completed', datetime('now', '-3 days'), 85.0)""",
                             (emp_id, course['id']))
            else:
                conn.execute("INSERT INTO enrollments (employee_id, course_id, status) VALUES (?, ?, ?)",
                             (emp_id, course['id'], status))

    print(f"Seeded {len(EMPLOYEES)} employees, {len(RESOURCES)} resources, {len(COURSES)} courses, {len(SAMPLE_ENROLLMENTS)} enrollments")


if __name__ == "__main__":
    seed()
