"""
奇美 PGY 內科 個人化學習與職涯發展系統 - 後端 API
================================================================
- FastAPI + SQLite
- 提供 REST API 給前端 HTML 呼叫
- 同時 serve 靜態前端 (避免 CORS 問題)
- 正式環境替換為:
    * SQLite -> PostgreSQL / SQL Server
    * Mock SSO -> LDAP / AD / Azure AD
    * In-memory AI -> Claude API / 院內 LLM
================================================================
"""
import json
import os
from datetime import datetime
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Body, Request, Depends, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets as py_secrets
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from database import db_session, init_schema

# 啟動時確保 DB 存在
init_schema()

# Initialize app first
app = FastAPI(
    title="奇美 PGY 內科 個人化學習系統 API",
    version="1.0.0",
    description="""
    這是 MVP 後端，正式上線前需要：
    1. 加入 SSO 認證 (奇美 LDAP / AD)
    2. 串接 e-portfolio 資料庫
    3. 串接 HR 系統取得員工檔案
    4. AI 教練接 Claude API
    """,
)

# CORS（開發階段允許所有來源；正式環境應限制）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================
# HTTP Basic Auth (雲端 demo 用，避免被路過的人亂用)
# 從環境變數讀取帳密；若沒設定則停用驗證 (本機開發方便)
# =============================================================
DEMO_USER = os.environ.get("DEMO_USER", "")
DEMO_PASSWORD = os.environ.get("DEMO_PASSWORD", "")
AUTH_ENABLED = bool(DEMO_USER and DEMO_PASSWORD)

security = HTTPBasic()

def verify_basic_auth(credentials: HTTPBasicCredentials = Depends(security)):
    """驗證 HTTP Basic Auth 帳密。本機未設環境變數時直接放行。"""
    if not AUTH_ENABLED:
        return "anonymous"
    user_ok = py_secrets.compare_digest(credentials.username, DEMO_USER)
    pass_ok = py_secrets.compare_digest(credentials.password, DEMO_PASSWORD)
    if not (user_ok and pass_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="帳號或密碼錯誤",
            headers={"WWW-Authenticate": 'Basic realm="Chimei PGY Demo"'},
        )
    return credentials.username


# 建立一個 "可選" 的依賴，FastAPI 會把它應用到所有後續路由
# 這個依賴本身不返回任何東西，只用來觸發驗證
def require_auth(_: str = Depends(verify_basic_auth)):
    return None





@app.middleware("http")
async def basic_auth_middleware(request: Request, call_next):
    """
    全站 HTTP Basic Auth (env 設了 DEMO_USER / DEMO_PASSWORD 才啟用)
    /api/health 不擋，方便雲端平台健康檢查
    """
    if not AUTH_ENABLED:
        return await call_next(request)
    # 健康檢查端點不擋，讓 Railway 之類能 ping
    if request.url.path == "/api/health":
        return await call_next(request)
    auth = request.headers.get("authorization", "")
    if not auth.startswith("Basic "):
        from fastapi.responses import Response
        return Response(
            status_code=401,
            headers={"WWW-Authenticate": 'Basic realm="Chimei PGY Demo"'},
            content="Authentication required",
        )
    import base64
    try:
        decoded = base64.b64decode(auth[6:]).decode("utf-8")
        user, _, password = decoded.partition(":")
        if not (py_secrets.compare_digest(user, DEMO_USER) and py_secrets.compare_digest(password, DEMO_PASSWORD)):
            raise ValueError()
    except Exception:
        from fastapi.responses import Response
        return Response(
            status_code=401,
            headers={"WWW-Authenticate": 'Basic realm="Chimei PGY Demo"'},
            content="Invalid credentials",
        )
    return await call_next(request)


# =============================================================
# Pydantic Models (請求/回應結構)
# =============================================================
class LoginRequest(BaseModel):
    employee_id: str

class ILPUpdate(BaseModel):
    goal: Optional[str] = None
    motivation: Optional[str] = None
    strategy: Optional[str] = None
    resources: Optional[str] = None
    barriers: Optional[str] = None
    kpi: Optional[str] = None
    timeline: Optional[str] = None
    eportfolio_rating: Optional[int] = None

class ReflectionCreate(BaseModel):
    content: str

class CoachMessage(BaseModel):
    employee_id: str
    message: str

class GeneratePlanRequest(BaseModel):
    employee_id: str


# =============================================================
# Helper functions
# =============================================================
def row_to_dict(row):
    return dict(row) if row else None

def rows_to_list(rows):
    return [dict(r) for r in rows]


# =============================================================
# AUTH (Mock SSO - 正式版接 LDAP)
# =============================================================
@app.post("/api/auth/login", tags=["Auth"])
def login(req: LoginRequest):
    """模擬 SSO 登入。正式版會驗證 LDAP / AD / Azure AD。"""
    with db_session() as conn:
        emp = conn.execute(
            "SELECT * FROM employees WHERE employee_id = ?", (req.employee_id,)
        ).fetchone()
        if not emp:
            raise HTTPException(status_code=404, detail=f"找不到人事號 {req.employee_id}")
        return {
            "token": f"mock-token-{req.employee_id}",  # 正式版用 JWT
            "employee": dict(emp),
            "issued_at": datetime.now().isoformat(),
        }


# =============================================================
# EMPLOYEES
# =============================================================
@app.get("/api/employees", tags=["Employees"])
def list_employees():
    """列出所有員工 (主管/教學中心視角用)"""
    with db_session() as conn:
        rows = conn.execute("SELECT * FROM employees ORDER BY stage, employee_id").fetchall()
        return rows_to_list(rows)


@app.get("/api/employees/{employee_id}", tags=["Employees"])
def get_employee(employee_id: str):
    """取得員工基本資料"""
    with db_session() as conn:
        row = conn.execute("SELECT * FROM employees WHERE employee_id = ?", (employee_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"找不到人事號 {employee_id}")
        return dict(row)


@app.get("/api/employees/{employee_id}/dashboard", tags=["Employees"])
def get_dashboard(employee_id: str):
    """
    一次取得 dashboard 所需所有資料
    （前端就不用呼叫多支 API，減少 round-trip）
    """
    with db_session() as conn:
        emp = conn.execute("SELECT * FROM employees WHERE employee_id = ?", (employee_id,)).fetchone()
        if not emp:
            raise HTTPException(status_code=404)

        emp = dict(emp)

        # 能力分數 + 標竿
        comps = conn.execute(
            "SELECT dimension, score FROM competencies c WHERE employee_id = ? AND evaluated_at = (SELECT MAX(evaluated_at) FROM competencies WHERE employee_id = c.employee_id AND dimension = c.dimension)", (employee_id,)
        ).fetchall()
        comp_map = {r['dimension']: r['score'] for r in comps}

        bench = conn.execute(
            "SELECT dimension, score FROM stage_benchmarks WHERE stage = ?", (emp['stage'],)
        ).fetchall()
        bench_map = {r['dimension']: r['score'] for r in bench}

        # 本週重點
        focus = conn.execute(
            "SELECT title, tag, urgency FROM weekly_focus WHERE employee_id = ?", (employee_id,)
        ).fetchall()

        # 本月規定
        req = conn.execute(
            "SELECT item, done, total FROM monthly_requirements WHERE employee_id = ?", (employee_id,)
        ).fetchall()

        # ILP
        ilp = conn.execute(
            "SELECT * FROM ilps WHERE employee_id = ? ORDER BY updated_at DESC LIMIT 1", (employee_id,)
        ).fetchone()

        return {
            "employee": emp,
            "competencies": comp_map,
            "benchmarks": bench_map,
            "weekly_focus": rows_to_list(focus),
            "monthly_requirements": rows_to_list(req),
            "ilp": dict(ilp) if ilp else None,
        }


# =============================================================
# COMPETENCIES
# =============================================================
@app.get("/api/employees/{employee_id}/competencies", tags=["Competencies"])
def get_competencies(employee_id: str):
    """取得個人六大核心能力分數 + 階段標竿"""
    with db_session() as conn:
        emp = conn.execute("SELECT stage FROM employees WHERE employee_id = ?", (employee_id,)).fetchone()
        if not emp:
            raise HTTPException(status_code=404)

        scores = conn.execute(
            "SELECT dimension, score, evaluator, evaluated_at FROM competencies c WHERE employee_id = ? AND evaluated_at = (SELECT MAX(evaluated_at) FROM competencies WHERE employee_id = c.employee_id AND dimension = c.dimension)",
            (employee_id,)
        ).fetchall()
        bench = conn.execute(
            "SELECT dimension, score FROM stage_benchmarks WHERE stage = ?", (emp['stage'],)
        ).fetchall()

        return {
            "stage": emp['stage'],
            "current": {r['dimension']: r['score'] for r in scores},
            "benchmark": {r['dimension']: r['score'] for r in bench},
        }


# =============================================================
# ILP (Individualized Learning Plan)
# =============================================================
@app.get("/api/employees/{employee_id}/ilp", tags=["ILP"])
def get_ilp(employee_id: str):
    with db_session() as conn:
        ilp = conn.execute(
            "SELECT * FROM ilps WHERE employee_id = ? ORDER BY updated_at DESC LIMIT 1", (employee_id,)
        ).fetchone()
        return dict(ilp) if ilp else None


@app.put("/api/employees/{employee_id}/ilp", tags=["ILP"])
def update_ilp(employee_id: str, body: ILPUpdate):
    """更新 ILP（建立新版本，保留歷史）"""
    with db_session() as conn:
        emp = conn.execute("SELECT * FROM employees WHERE employee_id = ?", (employee_id,)).fetchone()
        if not emp:
            raise HTTPException(status_code=404)

        existing = conn.execute(
            "SELECT * FROM ilps WHERE employee_id = ? ORDER BY updated_at DESC LIMIT 1", (employee_id,)
        ).fetchone()
        existing = dict(existing) if existing else {}

        # 合併欄位（未提供的保持原值）
        merged = {
            'goal': body.goal if body.goal is not None else existing.get('goal'),
            'motivation': body.motivation if body.motivation is not None else existing.get('motivation'),
            'strategy': body.strategy if body.strategy is not None else existing.get('strategy'),
            'resources': body.resources if body.resources is not None else existing.get('resources'),
            'barriers': body.barriers if body.barriers is not None else existing.get('barriers'),
            'kpi': body.kpi if body.kpi is not None else existing.get('kpi'),
            'timeline': body.timeline if body.timeline is not None else existing.get('timeline'),
            'eportfolio_rating': body.eportfolio_rating if body.eportfolio_rating is not None else existing.get('eportfolio_rating'),
        }

        conn.execute("""
            INSERT INTO ilps (employee_id, goal, motivation, strategy, resources, barriers, kpi, timeline, eportfolio_rating, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (employee_id, merged['goal'], merged['motivation'], merged['strategy'],
              merged['resources'], merged['barriers'], merged['kpi'], merged['timeline'],
              merged['eportfolio_rating']))

        return {"status": "ok", "message": "ILP 已更新"}


@app.post("/api/ilp/generate-plan", tags=["ILP"])
def generate_ai_plan(req: GeneratePlanRequest):
    """
    AI 自動產生個人化學習計畫
    正式版會呼叫 Claude API；目前用規則式 fallback
    """
    employee_id = req.employee_id
    with db_session() as conn:
        emp = conn.execute("SELECT * FROM employees WHERE employee_id = ?", (employee_id,)).fetchone()
        ilp = conn.execute(
            "SELECT * FROM ilps WHERE employee_id = ? ORDER BY updated_at DESC LIMIT 1", (employee_id,)
        ).fetchone()
        if not emp or not ilp:
            raise HTTPException(status_code=404, detail="找不到員工或 ILP")

        emp = dict(emp); ilp = dict(ilp)
        goal = ilp.get('goal') or ''
        kpi = ilp.get('kpi') or ''
        timeline = ilp.get('timeline') or '3 個月'
        barriers = ilp.get('barriers') or ''

        # 對應 ACGME 核心
        if any(k in goal for k in ['CVC', 'CPR', 'POCUS', '插管', 'procedure', '急救', '超音波', '技能']):
            comp_tag = '病人照護 (PC)'
        elif any(k in goal for k in ['鑑別診斷', '診斷', 'knowledge', '藥物', 'domain']):
            comp_tag = '醫學知識 (MK)'
        elif any(k in goal for k in ['論文', '寫作', 'AI', '文獻', 'EBM']):
            comp_tag = '從工作中學習成長 (PBLI)'
        else:
            comp_tag = '病人照護 (PC)'

        # KPI 強度檢查
        kpi_weak = (not kpi) or len(kpi) < 5 or kpi in ('無', '.')
        smart_kpi = _generate_smart_kpi(goal, emp['stage'])

        # 里程碑
        milestones = _generate_milestones(goal, timeline, emp['stage'])

        # 配對資源
        all_resources = conn.execute("SELECT * FROM resources").fetchall()
        matched = []
        for r in all_resources:
            keywords = json.loads(r['match_keywords']) if r['match_keywords'] else []
            if any(k.lower() in goal.lower() for k in keywords):
                matched.append(dict(r))
        matched = matched[:5]

        # 障礙建議
        barrier_advice = _generate_barrier_advice(barriers)

        plan = {
            "competency_tag": comp_tag,
            "kpi_assessment": {
                "is_weak": kpi_weak,
                "original": kpi,
                "smart_version": smart_kpi,
            },
            "milestones": milestones,
            "matched_resources": matched,
            "barrier_advice": barrier_advice,
            "monthly_integration": "建議用此目標的學習材料，作為本月「醫療品質應用案例分析報告」的素材，達成「一案多用」效益（符合奇美 PGY 訓練規定）。",
        }

        # 儲存到 DB
        conn.execute(
            "UPDATE ilps SET ai_generated_plan = ? WHERE id = ?",
            (json.dumps(plan, ensure_ascii=False), ilp['id'])
        )

        return plan


def _generate_smart_kpi(goal: str, stage: str) -> str:
    g = goal.lower()
    if 'cvc' in g:
        if stage.startswith('PGY1'):
            return '完訓前完成 supervised CVC 5 例 + 通過模擬中心 OSCE 評核'
        return '完訓前獨立完成 CVC 3 例，併發症率 < 院內基準'
    if 'pocus' in g:
        return '12 週內通過院內 POCUS 實作測驗 + 完成 30 例 self-scan log'
    if any(k in g for k in ['cpr', 'acls']):
        return '通過 ACLS 認證測驗 + 至少參與 3 場實際急救並能主導 BLS algorithm'
    if any(k in goal for k in ['論文', '寫作']):
        return '一年內完成 1 篇 case report 投稿 IF 1-3 期刊（須有 mentor 共同作者）'
    if any(k in goal for k in ['鑑別診斷', '診斷']):
        return '3 個月內針對 8 種內科常見症狀均能獨立列出 ≥3 個 differential diagnosis'
    return '3 個月內，能在 supervised 條件下獨立完成此能力的 5 個案例，並通過導師評核'


def _generate_milestones(goal: str, timeline: str, stage: str) -> list:
    g = goal.lower()
    if 'cvc' in g:
        return [
            '第 1 週：技能中心 CVC 模擬訓練 (含超音波導引)',
            '第 2-4 週：申請加入「內科 CVC 通知群組」並至少 supervised 觀摩 5 次',
            '第 5-8 週：supervised 操作 3 例，每次後與導師回饋',
            '第 9-12 週：再 2 例 supervised，達成總 5 例',
            '第 13 週：通過 Mini-CEX 評核（CVC 站）',
        ]
    if 'pocus' in g:
        return [
            '第 1 週：完成 RUSH protocol 線上課程',
            '第 2-4 週：每次值班 self-scan 1 例（hypotension 病人）',
            '第 5-8 週：與 attending 討論 self-scan 影像，建立 30 例 log',
            '第 9-12 週：通過院內 POCUS 實作測驗',
        ]
    if any(k in goal for k in ['論文', '寫作']):
        return [
            '第 1 個月：找 mentor + 確認研究題目',
            '第 2-3 個月：IRB 申請 + 資料收集',
            '第 4-6 個月：分析 + 初稿撰寫',
            '第 7-9 個月：投稿 + 修改',
            '第 10-12 個月：發表 / 重新投稿',
        ]
    if any(k in g for k in ['急症', '急救', 'cpr']):
        return [
            '第 1 週：通過 ACLS 認證',
            '第 2-4 週：值班至少觀摩 3 場急救',
            '第 5-8 週：主動上 supervised 急救情境 (技能中心)',
            '第 9-12 週：在 supervised 下能主導 BLS algorithm',
        ]
    return [
        '第 1-2 週：與導師確認具體子技能與評核標準',
        '第 3-8 週：每週至少 1 次相關案例 + 反思日誌',
        '第 9-12 週：透過 Mini-CEX / CbD 完成評核',
    ]


def _generate_barrier_advice(barriers: str) -> str:
    if not barriers:
        return '請填寫可能遭遇的困難，AI 才能給出具體建議。'
    b = barriers
    if any(k in b for k in ['操作機會', '機會少', '機會有限']):
        return '系統建議：(1) 主動申請加入相關 procedure 通知群組；(2) 多位學員提出同樣需求，建議向導師反映建立「PGY 學員 procedure 預約系統」；(3) 善用技能中心模擬訓練填補實機會缺口。'
    if any(k in b for k in ['時間', '繁忙', '衝突']):
        return '系統建議：(1) 與導師討論調整臨床負荷；(2) 善用早晨 7:30 前與午休時段；(3) 部分課程可申請線上化（多位學員提出此需求，可彙整成科部建議案）。'
    return '建議與導師 1-on-1 討論此障礙的具體解法，並列入下次教學執行檢討會議議程。'


# =============================================================
# MILESTONES (Learning Map)
# =============================================================
@app.get("/api/employees/{employee_id}/milestones", tags=["Milestones"])
def get_milestones(employee_id: str):
    with db_session() as conn:
        rows = conn.execute(
            "SELECT * FROM milestones WHERE employee_id = ? ORDER BY sort_order", (employee_id,)
        ).fetchall()
        return rows_to_list(rows)


# =============================================================
# REFLECTIONS
# =============================================================
@app.get("/api/employees/{employee_id}/reflections", tags=["Reflections"])
def get_reflections(employee_id: str):
    with db_session() as conn:
        rows = conn.execute(
            "SELECT * FROM reflections WHERE employee_id = ? ORDER BY created_at DESC", (employee_id,)
        ).fetchall()
        return rows_to_list(rows)


@app.post("/api/employees/{employee_id}/reflections", tags=["Reflections"])
def create_reflection(employee_id: str, body: ReflectionCreate):
    with db_session() as conn:
        cur = conn.execute(
            "INSERT INTO reflections (employee_id, content) VALUES (?, ?)",
            (employee_id, body.content)
        )
        return {"id": cur.lastrowid, "status": "ok"}


# =============================================================
# RESOURCES (院內學習資源)
# =============================================================
@app.get("/api/resources", tags=["Resources"])
def get_resources(employee_id: Optional[str] = None):
    """
    取得院內學習資源；若帶 employee_id，會依其 ILP 學習目標 + 能力差距智能排序
    """
    with db_session() as conn:
        rows = conn.execute("SELECT * FROM resources").fetchall()
        resources = rows_to_list(rows)

        if not employee_id:
            return resources

        # 取得 ILP & 能力差距
        ilp = conn.execute(
            "SELECT goal FROM ilps WHERE employee_id = ? ORDER BY updated_at DESC LIMIT 1", (employee_id,)
        ).fetchone()
        emp = conn.execute("SELECT stage FROM employees WHERE employee_id = ?", (employee_id,)).fetchone()
        if not emp:
            return resources

        comps = conn.execute(
            "SELECT dimension, score FROM competencies c WHERE employee_id = ? AND evaluated_at = (SELECT MAX(evaluated_at) FROM competencies WHERE employee_id = c.employee_id AND dimension = c.dimension)", (employee_id,)
        ).fetchall()
        comp_map = {r['dimension']: r['score'] for r in comps}

        bench = conn.execute(
            "SELECT dimension, score FROM stage_benchmarks WHERE stage = ?", (emp['stage'],)
        ).fetchall()
        bench_map = {r['dimension']: r['score'] for r in bench}

        gaps = {dim: bench_map.get(dim, 0) - comp_map.get(dim, 0) for dim in comp_map}
        goal = (ilp['goal'] if ilp else '').lower()

        # 排序
        def sort_key(r):
            keywords = json.loads(r['match_keywords']) if r['match_keywords'] else []
            ilp_match = any(k.lower() in goal for k in keywords)
            tag_gap = gaps.get(r['tag'], 0)
            return (-int(ilp_match), -tag_gap)  # ILP 匹配優先 -> gap 大優先

        resources.sort(key=sort_key)

        # 標記匹配
        for r in resources:
            keywords = json.loads(r['match_keywords']) if r['match_keywords'] else []
            r['matches_ilp'] = any(k.lower() in goal for k in keywords)
            r['gap_score'] = round(gaps.get(r['tag'], 0), 2)

        return resources


# =============================================================
# AI COACH
# =============================================================
COACH_SCRIPTS = {
    'cvc': [
        ('coach', "看到你想學會獨立放 CVC（依奇美 PGY 訓練計畫，這是 PC 核心技能）。先跟我說：<br><br><strong>(1) 你目前見過 / 操作過幾次？</strong>分別在 supervised / unsupervised 條件下？<br><strong>(2) 你最不確定的步驟是什麼？</strong>定位、消毒、超音波導引、wire 進入、固定？"),
    ],
    'pocus': [
        ('coach', "床邊超音波（POCUS）在 PGY 內科訓練中是「加分技能」，但對值班時 unstable 病人的 quick assessment 非常有用。先問三題：<br><br>(1) 你目前最想能用 POCUS 解答哪個臨床問題？<br>(2) 你的科部是否有手持超音波可使用？<br>(3) 你願意每週投入幾小時練習？"),
    ],
    'night': [
        ('coach', "值班遇到 unstable 病人是 PGY 階段最重要的學習時刻。先問你：<br><br><strong>最近一次讓你最焦慮的 unstable 病人，發生了什麼？</strong>"),
    ],
    'reflect': [
        ('coach', "我用蘇格拉底式提問引導你反思這個月。<br><br><strong>1. 這個月你最有成就感的一刻是什麼？</strong>具體場景、誰在場、發生了什麼？"),
    ],
}


@app.post("/api/coach/chat", tags=["AI Coach"])
def coach_chat(msg: CoachMessage):
    """
    AI 教練對話端點
    正式版會：
      1. 讀取員工的能力雷達 + ILP + 過往對話
      2. 組成 system prompt
      3. 呼叫 Claude API
      4. 把回覆儲存到 coach_messages
    現在用規則式回應（demo 用）
    """
    with db_session() as conn:
        # 儲存用戶訊息
        conn.execute(
            "INSERT INTO coach_messages (employee_id, role, content) VALUES (?, ?, ?)",
            (msg.employee_id, "user", msg.message)
        )

        # 簡單 keyword routing
        m = msg.message.lower()
        if any(k in m for k in ['cvc', '中央靜脈', 'central line']):
            response = "看到你想討論 CVC。<br>建議步驟：(1) 先到技能中心預約模擬訓練；(2) 申請加入科部 CVC 通知群組；(3) 累積 supervised 5 例。<br><br>正式版我會：依你目前能力分數 + 已完成里程碑，給更精準的下一步建議。"
        elif 'pocus' in m or '超音波' in m:
            response = "POCUS 學習路徑建議：<br>1. RUSH protocol 入門<br>2. 每次值班 self-scan 1 例<br>3. 建立 30 例 log<br>4. 通過院內 POCUS 實作測驗"
        elif any(k in m for k in ['反思', 'reflect', '心得']):
            response = "我用蘇格拉底式提問引導你反思：<br><br>1. 這週讓你最有成就感的一刻是什麼？<br>2. 在那次經驗中，你做了什麼「以前不敢做」的事？<br>3. 對應到 ACGME 哪一個核心能力的成長？"
        else:
            response = "謝謝你的訊息。<br>正式版本將串接 Claude API，能：<br>(1) 讀你的能力雷達 + ILP + 過往對話脈絡<br>(2) 用蘇格拉底式提問引導<br>(3) 自動產生可加入學習地圖的里程碑"

        # 儲存 coach 回應
        conn.execute(
            "INSERT INTO coach_messages (employee_id, role, content) VALUES (?, ?, ?)",
            (msg.employee_id, "coach", response)
        )

        return {"role": "coach", "content": response}


@app.get("/api/coach/history/{employee_id}", tags=["AI Coach"])
def coach_history(employee_id: str, limit: int = 50):
    with db_session() as conn:
        rows = conn.execute(
            "SELECT role, content, created_at FROM coach_messages WHERE employee_id = ? ORDER BY created_at LIMIT ?",
            (employee_id, limit)
        ).fetchall()
        return rows_to_list(rows)


# =============================================================
# ANALYTICS (教學中心視角)
# =============================================================
@app.get("/api/analytics/heatmap", tags=["Analytics"])
def heatmap():
    """全體學員 × 六大核心能力 熱圖資料"""
    with db_session() as conn:
        emps = conn.execute("SELECT * FROM employees ORDER BY employee_id").fetchall()
        result = []
        for emp in emps:
            comps = conn.execute(
                "SELECT dimension, score FROM competencies WHERE employee_id = ?", (emp['employee_id'],)
            ).fetchall()
            result.append({
                "employee_id": emp['employee_id'],
                "name": emp['name'],
                "stage": emp['stage'],
                "competencies": {r['dimension']: r['score'] for r in comps}
            })
        return result


@app.get("/api/analytics/common-goals", tags=["Analytics"])
def common_goals():
    """ILP 共通需求分析（基於關鍵字統計）"""
    with db_session() as conn:
        ilps = conn.execute("SELECT goal FROM ilps").fetchall()
        goals = [r['goal'].lower() if r['goal'] else '' for r in ilps]
        total = len(goals)

        keywords = {
            'CVC 中央靜脈導管放置': ['cvc', '中央靜脈'],
            'CPR / ACLS / 急救處理': ['cpr', 'acls', '急救'],
            'POCUS 床邊超音波': ['pocus', '超音波'],
            'Procedure 操作能力': ['procedure', '插管', '胸管'],
            '臨床鑑別診斷': ['鑑別', '診斷'],
            '值班緊急情況': ['值班', 'unstable', '緊急'],
            '次專科 domain knowledge': ['次專科', 'domain'],
            'AI 應用 / 論文寫作': ['ai', '論文', '寫作'],
        }
        counts = []
        for label, kws in keywords.items():
            cnt = sum(1 for g in goals if any(k in g for k in kws))
            counts.append({"goal": label, "count": cnt, "total": total})
        counts.sort(key=lambda x: -x['count'])
        return counts


@app.get("/api/analytics/insights", tags=["Analytics"])
def insights():
    """
    教學中心智能洞察
    正式版會結合更多歷史資料 + LLM 自動產生
    """
    with db_session() as conn:
        # 找出進度落後 (overall_progress < 30) 的學員
        amber_red = conn.execute(
            "SELECT employee_id, name, stage, overall_progress FROM employees WHERE team_status IN ('amber','red') ORDER BY overall_progress"
        ).fetchall()
        # 找 KPI 模糊的 ILP
        weak_kpi = conn.execute(
            "SELECT e.name, e.stage, i.kpi FROM ilps i JOIN employees e ON i.employee_id = e.employee_id WHERE LENGTH(i.kpi) < 5 OR i.kpi IN ('無','.')"
        ).fetchall()

        return {
            "students_need_attention": rows_to_list(amber_red),
            "weak_kpi_count": len(weak_kpi),
            "weak_kpi_examples": rows_to_list(weak_kpi),
        }


# =============================================================
# Health check
# =============================================================
@app.get("/api/health", tags=["Meta"])
def health():
    return {"status": "ok", "time": datetime.now().isoformat()}



# =============================================================
# COURSES & ENROLLMENTS (課程模組)
# =============================================================
import secrets
from datetime import datetime, timedelta


class EnrollRequest(BaseModel):
    employee_id: str

class QrTokenRequest(BaseModel):
    course_id: int
    issued_by: Optional[str] = None
    valid_minutes: int = 30          # token 有效分鐘

class QrCheckinRequest(BaseModel):
    token: str
    employee_id: str

class CompleteOnlineRequest(BaseModel):
    employee_id: str
    self_reflection: Optional[str] = None

class InstructorSignoffRequest(BaseModel):
    instructor_feedback: str
    final_score: Optional[float] = None

class UploadCertRequest(BaseModel):
    certificate_url: str
    final_score: Optional[float] = None


def _apply_completion(conn, enrollment_id: int) -> dict:
    """
    完成課程後的副作用（這是讓系統「真的會動」的關鍵函數）：
      1. 把 enrollment 設為 completed
      2. 依 course.competency_uplift 加分到 competencies (建立新一筆評核)
      3. 把對應的 milestone 改為 done
      4. 更新對應的 monthly_requirements 進度
    """
    enr = conn.execute("""
        SELECT e.*, c.title AS course_title, c.competency_uplift, c.type AS course_type, c.course_code
        FROM enrollments e JOIN courses c ON e.course_id = c.id
        WHERE e.id = ?
    """, (enrollment_id,)).fetchone()
    if not enr:
        raise HTTPException(status_code=404, detail="找不到 enrollment")

    employee_id = enr['employee_id']
    side_effects = {"enrollment_id": enrollment_id, "course_title": enr['course_title']}

    # 1. mark completed
    conn.execute(
        "UPDATE enrollments SET status='completed', completed_at=CURRENT_TIMESTAMP WHERE id=?",
        (enrollment_id,)
    )

    # 2. competencies uplift
    uplift = json.loads(enr['competency_uplift']) if enr['competency_uplift'] else {}
    side_effects['competency_changes'] = []
    for dim, delta in uplift.items():
        cur = conn.execute(
            "SELECT score FROM competencies WHERE employee_id=? AND dimension=? ORDER BY evaluated_at DESC LIMIT 1",
            (employee_id, dim)
        ).fetchone()
        old = cur['score'] if cur else 0
        new_score = min(5.0, old + delta)
        conn.execute(
            "INSERT INTO competencies (employee_id, dimension, score, evaluator) VALUES (?, ?, ?, ?)",
            (employee_id, dim, new_score, f"課程完成自動更新: {enr['course_code']}")
        )
        side_effects['competency_changes'].append({
            "dimension": dim, "from": round(old, 2), "to": round(new_score, 2), "delta": delta
        })

    # 3. mark related milestone done (依關鍵字匹配)
    keywords = enr['course_title']
    rows = conn.execute(
        "SELECT id, title, status FROM milestones WHERE employee_id=? AND status != 'done'",
        (employee_id,)
    ).fetchall()
    side_effects['milestones_completed'] = []
    for r in rows:
        if any(k in r['title'] for k in [enr['course_code'].split('-')[1] if '-' in enr['course_code'] else enr['course_code']]) \
           or any(w in r['title'] and w in keywords for w in ['CVC', 'POCUS', 'OSCE', '晨會', 'EBM', 'Grand', 'ACLS', 'ATLS', '倫理', '14 天']):
            conn.execute("UPDATE milestones SET status='done' WHERE id=?", (r['id'],))
            side_effects['milestones_completed'].append(r['title'])

    # 4. update monthly_requirements
    if enr['course_type'] in ('skill', 'in_person'):
        # 完成講師簽核類課程通常算 Mini-CEX 或 CbD
        req = conn.execute(
            "SELECT id, item, done, total FROM monthly_requirements WHERE employee_id=? AND item LIKE '%Mini-CEX%' AND done < total",
            (employee_id,)
        ).fetchone()
        if req:
            conn.execute("UPDATE monthly_requirements SET done = done + 1 WHERE id = ?", (req['id'],))
            side_effects['monthly_req_updated'] = req['item']

    return side_effects


@app.get("/api/courses", tags=["Courses"])
def list_courses(employee_id: Optional[str] = None, type_filter: Optional[str] = None):
    """
    取得課程清單；若帶 employee_id 則依 ILP + 能力差距智能排序
    """
    with db_session() as conn:
        sql = "SELECT * FROM courses"
        params = []
        if type_filter:
            sql += " WHERE type = ?"
            params.append(type_filter)
        rows = conn.execute(sql, params).fetchall()
        courses = [dict(r) for r in rows]
        for c in courses:
            c['competency_uplift'] = json.loads(c['competency_uplift']) if c['competency_uplift'] else {}
            c['tags'] = json.loads(c['tags']) if c['tags'] else []

        if not employee_id:
            return courses

        # smart sort
        emp = conn.execute("SELECT stage FROM employees WHERE employee_id = ?", (employee_id,)).fetchone()
        if not emp:
            return courses
        comps = conn.execute(
            "SELECT dimension, MAX(score) as score FROM competencies WHERE employee_id = ? GROUP BY dimension",
            (employee_id,)
        ).fetchall()
        bench = conn.execute(
            "SELECT dimension, score FROM stage_benchmarks WHERE stage = ?", (emp['stage'],)
        ).fetchall()
        comp_map = {r['dimension']: r['score'] for r in comps}
        bench_map = {r['dimension']: r['score'] for r in bench}
        gaps = {d: bench_map.get(d, 0) - comp_map.get(d, 0) for d in comp_map}

        ilp = conn.execute(
            "SELECT goal FROM ilps WHERE employee_id = ? ORDER BY updated_at DESC LIMIT 1", (employee_id,)
        ).fetchone()
        goal = (ilp['goal'].lower() if ilp else '')

        # 已報名的 course_id set
        enrolled = {r['course_id']: r['status'] for r in conn.execute(
            "SELECT course_id, status FROM enrollments WHERE employee_id = ?", (employee_id,)
        ).fetchall()}

        for c in courses:
            ilp_match = any(t.lower() in goal for t in c['tags']) if c['tags'] else False
            max_gap = max((c['competency_uplift'].get(d, 0) * gaps.get(d, 0) for d in c['competency_uplift']), default=0)
            c['recommendation_score'] = (1.0 if ilp_match else 0) + max_gap
            c['matches_ilp'] = ilp_match
            c['gap_value'] = round(max_gap, 2)
            c['enrollment_status'] = enrolled.get(c['id'])

        courses.sort(key=lambda c: -c['recommendation_score'])
        return courses


@app.get("/api/courses/{course_id}", tags=["Courses"])
def get_course(course_id: int):
    with db_session() as conn:
        row = conn.execute("SELECT * FROM courses WHERE id = ?", (course_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404)
        c = dict(row)
        c['competency_uplift'] = json.loads(c['competency_uplift']) if c['competency_uplift'] else {}
        c['tags'] = json.loads(c['tags']) if c['tags'] else []
        return c


@app.post("/api/courses/{course_id}/enroll", tags=["Courses"])
def enroll_course(course_id: int, req: EnrollRequest):
    with db_session() as conn:
        course = conn.execute("SELECT id, capacity FROM courses WHERE id = ?", (course_id,)).fetchone()
        if not course:
            raise HTTPException(status_code=404, detail="找不到課程")
        existing = conn.execute(
            "SELECT id, status FROM enrollments WHERE employee_id = ? AND course_id = ?",
            (req.employee_id, course_id)
        ).fetchone()
        if existing:
            return {"status": "already_enrolled", "enrollment_id": existing['id'], "current_status": existing['status']}
        cur = conn.execute(
            "INSERT INTO enrollments (employee_id, course_id, status) VALUES (?, ?, 'registered')",
            (req.employee_id, course_id)
        )
        return {"status": "enrolled", "enrollment_id": cur.lastrowid}


@app.delete("/api/enrollments/{enrollment_id}", tags=["Courses"])
def cancel_enrollment(enrollment_id: int):
    with db_session() as conn:
        conn.execute("UPDATE enrollments SET status='cancelled' WHERE id=?", (enrollment_id,))
        return {"status": "cancelled"}


@app.get("/api/employees/{employee_id}/enrollments", tags=["Courses"])
def my_enrollments(employee_id: str):
    """取得學員的所有課程報名"""
    with db_session() as conn:
        rows = conn.execute("""
            SELECT e.*, c.title, c.type, c.location, c.instructor, c.scheduled_at,
                   c.duration_minutes, c.credit_hours, c.competency_uplift, c.tags,
                   c.requires_qr_checkin, c.requires_instructor_signoff,
                   c.requires_certificate_upload, c.auto_complete_after_signin,
                   c.content_url, c.course_code
            FROM enrollments e JOIN courses c ON e.course_id = c.id
            WHERE e.employee_id = ? ORDER BY e.enrolled_at DESC
        """, (employee_id,)).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d['competency_uplift'] = json.loads(d['competency_uplift']) if d['competency_uplift'] else {}
            d['tags'] = json.loads(d['tags']) if d['tags'] else []
            result.append(d)
        return result


# ===== QR Code 簽到 =====
@app.post("/api/courses/{course_id}/qr-token", tags=["QR Checkin"])
def create_qr_token(course_id: int, req: QrTokenRequest, request: Request = None):
    """講師端：產生 QR Code 用 token (預設 30 分鐘有效)"""
    with db_session() as conn:
        course = conn.execute("SELECT id, title FROM courses WHERE id = ?", (course_id,)).fetchone()
        if not course:
            raise HTTPException(status_code=404)
        token = secrets.token_urlsafe(16)
        expires = (datetime.now() + timedelta(minutes=req.valid_minutes)).isoformat()
        conn.execute(
            "INSERT INTO qr_tokens (course_id, token, issued_by, expires_at) VALUES (?, ?, ?, ?)",
            (course_id, token, req.issued_by or '示範教師', expires)
        )
        # 用 request host 組出完整 URL（手機掃描後可直接連到此 server）
        base = ""
        if request:
            base = f"{request.url.scheme}://{request.headers.get('host', 'localhost:8000')}"
        return {
            "token": token,
            "course_id": course_id,
            "course_title": course['title'],
            "expires_at": expires,
            "checkin_url": f"{base}/qr-checkin?token={token}"
        }


@app.post("/api/qr/checkin", tags=["QR Checkin"])
def qr_checkin(req: QrCheckinRequest):
    """
    學員端：用 QR Code 掃到的 token 簽到
    流程：(1) 驗證 token (2) 找對應 enrollment (沒有就自動建立) (3) 寫入 attendance_logs
         (4) 若 course 設定 auto_complete_after_signin=1 就直接觸發完成流程
    """
    with db_session() as conn:
        token_row = conn.execute(
            "SELECT * FROM qr_tokens WHERE token = ?", (req.token,)
        ).fetchone()
        if not token_row:
            raise HTTPException(status_code=400, detail="QR Code 無效或已過期")
        if datetime.fromisoformat(token_row['expires_at']) < datetime.now():
            raise HTTPException(status_code=400, detail="QR Code 已過期，請講師重新產生")

        course = conn.execute("SELECT * FROM courses WHERE id = ?", (token_row['course_id'],)).fetchone()
        if not course:
            raise HTTPException(status_code=404)

        # 找或建立 enrollment（如果沒事先報名也允許簽到）
        enr = conn.execute(
            "SELECT * FROM enrollments WHERE employee_id = ? AND course_id = ?",
            (req.employee_id, course['id'])
        ).fetchone()
        if not enr:
            cur = conn.execute(
                "INSERT INTO enrollments (employee_id, course_id, status, started_at) VALUES (?, ?, 'in_progress', CURRENT_TIMESTAMP)",
                (req.employee_id, course['id'])
            )
            enrollment_id = cur.lastrowid
        else:
            enrollment_id = enr['id']
            if enr['status'] == 'registered':
                conn.execute(
                    "UPDATE enrollments SET status='in_progress', started_at=CURRENT_TIMESTAMP WHERE id=?",
                    (enrollment_id,)
                )

        # 寫簽到紀錄
        conn.execute(
            "INSERT INTO attendance_logs (enrollment_id, method, notes) VALUES (?, 'qr', ?)",
            (enrollment_id, f"QR Code 簽到 (token: {req.token[:6]}...)")
        )
        conn.execute("UPDATE qr_tokens SET used_count = used_count + 1 WHERE id = ?", (token_row['id'],))

        side_effects = None
        # 如果課程設定為簽到後自動完成（如晨會、EBM、Grand Round）
        if course['auto_complete_after_signin']:
            side_effects = _apply_completion(conn, enrollment_id)

        return {
            "status": "checkin_success",
            "course_title": course['title'],
            "course_type": course['type'],
            "auto_completed": course['auto_complete_after_signin'] == 1,
            "side_effects": side_effects,
            "message": (
                f"✅ 簽到成功！本課程設定為簽到後自動完成。能力分數已更新："
                if course['auto_complete_after_signin']
                else f"✅ 簽到成功！這堂課需要 "
                     + ("講師簽核" if course['requires_instructor_signoff'] else "自我提交")
                     + "後才會完成。"
            )
        }


# ===== 完成驗證 (4 種方法) =====
@app.post("/api/enrollments/{enrollment_id}/complete-online", tags=["Course Completion"])
def complete_online(enrollment_id: int, req: CompleteOnlineRequest):
    """① 線上課程：學員自我提交完成 + 反思"""
    with db_session() as conn:
        if req.self_reflection:
            conn.execute("UPDATE enrollments SET self_reflection=? WHERE id=?",
                         (req.self_reflection, enrollment_id))
            # 同步寫入反思日誌
            conn.execute(
                "INSERT INTO reflections (employee_id, content) VALUES (?, ?)",
                (req.employee_id, f"[課程反思] {req.self_reflection}")
            )
        side_effects = _apply_completion(conn, enrollment_id)
        return {"status": "completed", "method": "online_self_report", "side_effects": side_effects}


@app.post("/api/enrollments/{enrollment_id}/instructor-signoff", tags=["Course Completion"])
def instructor_signoff(enrollment_id: int, req: InstructorSignoffRequest):
    """② 技能 / 實體課程：講師簽核完成"""
    with db_session() as conn:
        conn.execute(
            "UPDATE enrollments SET instructor_feedback=?, final_score=? WHERE id=?",
            (req.instructor_feedback, req.final_score, enrollment_id)
        )
        side_effects = _apply_completion(conn, enrollment_id)
        # 額外寫入 evaluations
        enr = conn.execute("SELECT employee_id FROM enrollments WHERE id=?", (enrollment_id,)).fetchone()
        if enr:
            conn.execute(
                "INSERT INTO evaluations (employee_id, method, score, feedback, evaluator) VALUES (?, 'Mini-CEX', ?, ?, '示範教師')",
                (enr['employee_id'], req.final_score or 0, req.instructor_feedback)
            )
        return {"status": "completed", "method": "instructor_signoff", "side_effects": side_effects}


@app.post("/api/enrollments/{enrollment_id}/upload-certificate", tags=["Course Completion"])
def upload_certificate(enrollment_id: int, req: UploadCertRequest):
    """③ 外部認證：上傳證書 → 系統審核（demo 直接通過）"""
    with db_session() as conn:
        conn.execute(
            "UPDATE enrollments SET certificate_url=?, final_score=? WHERE id=?",
            (req.certificate_url, req.final_score or 100, enrollment_id)
        )
        side_effects = _apply_completion(conn, enrollment_id)
        return {"status": "completed", "method": "certificate_upload", "side_effects": side_effects}


# ===== 統計 =====
@app.get("/api/analytics/course-completion", tags=["Analytics"])
def course_completion_analytics():
    """全院課程完成率分析"""
    with db_session() as conn:
        rows = conn.execute("""
            SELECT c.title, c.type, c.id as course_id,
                   COUNT(e.id) as enrolled,
                   SUM(CASE WHEN e.status='completed' THEN 1 ELSE 0 END) as completed,
                   SUM(CASE WHEN e.status='in_progress' THEN 1 ELSE 0 END) as in_progress
            FROM courses c LEFT JOIN enrollments e ON e.course_id = c.id
            GROUP BY c.id ORDER BY enrolled DESC
        """).fetchall()
        return rows_to_list(rows)


# =============================================================
# Static frontend
# =============================================================


# =============================================================
# REFLECTION FEEDBACK (講師對學員反思的回饋)
# =============================================================
class FeedbackCreate(BaseModel):
    reflection_id: int
    employee_id: str
    instructor: str = "示範教師"
    content: str
    rating: Optional[int] = None


@app.get("/api/employees/{employee_id}/reflections-with-feedback", tags=["Feedback"])
def reflections_with_feedback(employee_id: str):
    """學員端：取得自己的反思 + 每筆反思的講師回饋"""
    with db_session() as conn:
        refs = conn.execute(
            "SELECT id, content, created_at FROM reflections WHERE employee_id = ? ORDER BY created_at DESC",
            (employee_id,)
        ).fetchall()
        result = []
        for r in refs:
            fbs = conn.execute(
                "SELECT id, instructor, content, rating, created_at FROM reflection_feedbacks WHERE reflection_id = ? ORDER BY created_at",
                (r['id'],)
            ).fetchall()
            result.append({
                "id": r['id'],
                "content": r['content'],
                "created_at": r['created_at'],
                "feedbacks": [dict(fb) for fb in fbs]
            })
        return result


@app.post("/api/reflection-feedbacks", tags=["Feedback"])
def create_feedback(body: FeedbackCreate):
    """講師端：對學員的反思給回饋"""
    with db_session() as conn:
        cur = conn.execute("""
            INSERT INTO reflection_feedbacks (reflection_id, employee_id, instructor, content, rating)
            VALUES (?, ?, ?, ?, ?)
        """, (body.reflection_id, body.employee_id, body.instructor, body.content, body.rating))
        return {"status": "ok", "feedback_id": cur.lastrowid}


@app.get("/api/instructor/pending-reflections", tags=["Feedback"])
def pending_reflections():
    """講師端：列出所有學員的反思（未回饋優先）"""
    with db_session() as conn:
        rows = conn.execute("""
            SELECT r.id, r.employee_id, r.content, r.created_at,
                   e.name AS student_name, e.stage,
                   (SELECT COUNT(*) FROM reflection_feedbacks WHERE reflection_id = r.id) AS feedback_count
            FROM reflections r JOIN employees e ON r.employee_id = e.employee_id
            ORDER BY feedback_count ASC, r.created_at DESC
        """).fetchall()
        return rows_to_list(rows)


# =============================================================
# COURSE CREATION (教學部新增課程)
# =============================================================
class CourseCreate(BaseModel):
    course_code: str
    title: str
    description: Optional[str] = ""
    type: str  # online / skill / in_person / external
    instructor: Optional[str] = "示範教師"
    location: Optional[str] = ""
    competency_uplift: dict = {}     # e.g. {"PC": 0.2, "MK": 0.1}
    duration_minutes: int = 60
    schedule_type: str = "on_demand"
    scheduled_at: Optional[str] = ""
    credit_hours: float = 0
    cme_credits: float = 0
    requires_qr_checkin: int = 0
    requires_instructor_signoff: int = 0
    requires_certificate_upload: int = 0
    auto_complete_after_signin: int = 0
    content_url: Optional[str] = ""
    capacity: int = 30
    tags: List[str] = []


@app.post("/api/courses", tags=["Courses"])
def create_course(body: CourseCreate):
    """教學部：新增課程，新增後立即出現在課程瀏覽供學員選擇"""
    with db_session() as conn:
        existing = conn.execute("SELECT id FROM courses WHERE course_code = ?", (body.course_code,)).fetchone()
        if existing:
            raise HTTPException(status_code=400, detail=f"課程代碼 {body.course_code} 已存在")
        cur = conn.execute("""
            INSERT INTO courses (course_code, title, description, type, instructor, location,
                competency_uplift, duration_minutes, schedule_type, scheduled_at, credit_hours, cme_credits,
                requires_qr_checkin, requires_instructor_signoff, requires_certificate_upload,
                auto_complete_after_signin, content_url, capacity, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (body.course_code, body.title, body.description, body.type,
              body.instructor, body.location,
              json.dumps(body.competency_uplift, ensure_ascii=False),
              body.duration_minutes, body.schedule_type, body.scheduled_at,
              body.credit_hours, body.cme_credits,
              body.requires_qr_checkin, body.requires_instructor_signoff,
              body.requires_certificate_upload, body.auto_complete_after_signin,
              body.content_url, body.capacity,
              json.dumps(body.tags, ensure_ascii=False)))
        return {"status": "created", "course_id": cur.lastrowid, "title": body.title}


@app.delete("/api/courses/{course_id}", tags=["Courses"])
def delete_course(course_id: int):
    with db_session() as conn:
        # 只刪沒人報名的課程
        cnt = conn.execute("SELECT COUNT(*) AS c FROM enrollments WHERE course_id = ?", (course_id,)).fetchone()['c']
        if cnt > 0:
            raise HTTPException(status_code=400, detail=f"已有 {cnt} 位學員報名此課程，無法刪除")
        conn.execute("DELETE FROM courses WHERE id = ?", (course_id,))
        return {"status": "deleted"}


# =============================================================
# 手機 QR 簽到頁 (mobile-friendly standalone page)
# =============================================================
@app.get("/qr-checkin", include_in_schema=False)
def qr_checkin_page():
    """手機掃描 QR Code 後跳轉到的頁面"""
    p = os.path.join(os.path.dirname(__file__), "qr_checkin.html")
    if os.path.exists(p):
        return FileResponse(p, headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
        })
    return JSONResponse({"error": "qr_checkin.html not found"})


@app.get("/", include_in_schema=False)
def serve_frontend():
    p = os.path.join(os.path.dirname(__file__), "frontend.html")
    if os.path.exists(p):
        # 強制不快取，避免使用者看到舊版前端
        return FileResponse(p, headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
        })
    return JSONResponse({"message": "frontend.html 未放入 chimei_backend 資料夾。請從 outputs 複製。"})


# =============================================================
# Entry point
# =============================================================
if __name__ == "__main__":
    import uvicorn

    # 啟動前確保有種子資料 (本機與雲端部署都會跑)
    with db_session() as conn:
        cnt = conn.execute("SELECT COUNT(*) as c FROM employees").fetchone()['c']
    if cnt == 0:
        print("⚠️  資料庫為空，自動執行種子資料寫入...")
        from seed import seed
        seed()

    # PORT 從環境變數讀取（Railway / Render / Fly / Heroku 都會自動帶入）
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")

    print("\n" + "="*60)
    print("🏥 奇美 PGY 內科 個人化學習系統 - 後端已啟動")
    print("="*60)
    print(f"  Host:Port:  {host}:{port}")
    print(f"  前端 UI:    http://localhost:{port}")
    print(f"  API Docs:  http://localhost:{port}/docs")
    print("="*60 + "\n")

    uvicorn.run(app, host=host, port=port)
