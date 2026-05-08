# 奇美 PGY 內科 個人化學習與職涯發展系統

## 啟動步驟（Windows / Mac / Linux 通用）

### 1. 安裝 Python（≥ 3.10）

確認你電腦有 Python：

```bash
python --version
# 若顯示 Python 3.10.x 以上即可
```

### 2. 安裝相依套件

```bash
cd chimei_backend
pip install -r requirements.txt
```

### 3. 寫入種子資料（第一次執行）

```bash
python seed.py
```

這會：
- 建立 SQLite 資料庫 `chimei.db`
- 寫入 6 位真實學員（依你的 ILP 問卷）、18 項院內資源、階段標竿等

### 4. 啟動後端

```bash
python main.py
```

啟動成功會看到：

```
🏥 奇美 PGY 內科 個人化學習系統 - 後端已啟動
============================================================
  前端 UI:    http://localhost:8000
  API Docs:  http://localhost:8000/docs
  ReDoc:     http://localhost:8000/redoc
============================================================
```

### 5. 開啟瀏覽器

打開 [http://localhost:8000](http://localhost:8000)

用 `P10001` ~ `P10006` 任一人事號登入。

---

## 重要驗證點

進系統後請特別觀察這些「真的有資料流動」的地方：

### A. ILP 寫入資料庫
1. 進「ILP 個人化學習計畫」頁
2. 修改任一欄位
3. 按「儲存 ILP」 → 寫入 SQLite `ilps` table
4. 重新整理頁面 → 修改的內容仍在（驗證真的存進資料庫）

### B. AI 產生計畫
1. 在 ILP 頁按「AI 產生個人化學習計畫」
2. 後端會即時從 DB 讀取你的 ILP + 能力分數 + 院內資源做匹配
3. 結果存入 `ilps.ai_generated_plan`

### C. 反思日誌
1. 進「反思日誌」頁
2. 寫一段反思 → 按「儲存到資料庫」
3. 重新整理 → 你寫的反思會出現在「過往反思」區

### D. AI 教練對話歷史
1. 進「AI 教練」頁，跟它說話
2. 訊息會儲存到 `coach_messages` table
3. 切到別位學員再切回來 → 對話歷史完整保留

### E. 教學中心即時分析
1. 切到「教學中心」視角
2. 共通需求、KPI 模糊統計都是即時從 DB 計算（不是寫死的資料）

### F. 課程模組 + QR Code 簽到（最新）
四種課程類型 (線上 / 技能中心 / 實體 / 外部認證) 全整合，QR 簽到 → 自動更新能力分數 → 里程碑變綠 → 本月規定打勾，全部串成閉環。

**完整 demo 流程（用 P10001 陳冠霖試最快）：**

1. 進入「📚 我的課程」頁 → 看見 4 個分類（進行中 / 已報名 / 已完成）
2. 進入「🔍 課程瀏覽」→ 看見 12 門課智能排序，CVC 課程被打上「🎯 對應你的 ILP」
3. 在 CVC 課程卡片點「🧑‍🏫 講師：產生 QR」→ 跳出 QR Code 大圖（含 token）
4. 複製 token → 回「我的課程」找到 CVC → 點「📱 掃描 QR 簽到」→ 貼上 token → 簽到
5. 簽到成功彈窗顯示：能力分數變化（CVC 課程要講師簽核才會更新）
6. 回到「我的課程」找到 CVC 進行中 → 點「👨‍⚕️ 講師簽核」→ 填分數 + 評語
7. 完成彈窗顯示：**PC: 2.5 → 2.9 (+0.4) ｜ MK: 2.7 → 2.8 (+0.1)**
8. 回到「六大核心能力」頁面，雷達圖立刻變大（PC 凸出來）

**自動完成型課程（晨會 / EBM / Grand Round）：**
這類課程設定為 `auto_complete_after_signin=1`，學員 QR 簽到當下就直接完成、加分、更新里程碑，不需要講師再簽核。試試 P10006 掃描晨會課程的 QR 即可看到 MK / PBLI 立即變化。

**四種完成驗證對應：**
- 線上課程 → 自我提交 + 反思（同步寫入反思日誌）
- 技能中心 → QR 簽到 + 講師簽核（自動寫一筆 Mini-CEX 評核）
- 實體課程 → QR 簽到（多數可自動完成，M&M 需講師簽核）
- 外部認證 → 上傳證書連結 / 編號（demo 直接通過審核）

---

## 🔥 讓手機真的掃 QR Code（不只 demo）

要讓學員用手機掃 QR Code 完成簽到，需要兩個前提：

### 前提 1：手機跟電腦在同一個 WiFi 網路
（醫院的話通常是同一個內網即可）

### 前提 2：QR Code 內含的 URL 不能是 `localhost`，要是電腦的區網 IP

**找出你電腦的區網 IP（Windows）：**

開啟 PowerShell 輸入：
```
ipconfig
```

找「IPv4 位址」開頭，通常是 `192.168.x.x` 或 `10.x.x.x`，例如 `192.168.1.100`。

### 啟動方式

啟動後端時，瀏覽器網址列**用區網 IP 開啟系統**，而非 localhost：

```
http://192.168.1.100:8000        ← 改用你的區網 IP
```

這樣產生 QR Code 時，內含的 URL 會自動變成 `http://192.168.1.100:8000/qr-checkin?token=xxx`，手機掃描後就能連到你的電腦完成簽到。

### Windows 防火牆設定（首次需要）

第一次啟動 `python main.py` 時 Windows 會跳出防火牆詢問視窗，**請勾選「私人網路」並按允許**，這樣手機才連得到。

如果之前不小心按了「拒絕」，可去：
- 設定 → 網路與網際網路 → Windows 防火牆 → 允許應用程式通過防火牆
- 找到 Python，勾選「私人」

### 驗證手機能否連上

手機瀏覽器直接打開 `http://192.168.1.100:8000/api/health`，看到 `{"status":"ok",...}` 就代表能連到了。

### 完整 QR 簽到 demo 流程（雙螢幕）

1. **電腦端（講師角色）**：在 `http://192.168.1.100:8000` 登入講師視角 → 課程瀏覽 → 找一門技能課 → 點「🧑‍🏫 講師：產生 QR」 → QR Code 顯示在電腦螢幕
2. **手機端（學員角色）**：用相機 App 對著電腦螢幕的 QR Code 掃描 → 跳出通知點開 → 自動進入手機友善的簽到頁
3. **手機輸入人事號**（例如 `P10001`）→ 按「📲 簽到」
4. **手機立刻顯示**：✅ 簽到成功 + 能力分數變化（例如 PC: 2.5 → 2.9 +0.4）
5. **回電腦端**：重新整理「我的課程」/「能力雷達」 → 看到剛才簽到的課程已變綠、雷達圖 PC 變大

### 不想設定區網？同電腦也能 demo

QR Code 跳出來後，旁邊有顯示完整 URL 與 token。可以：
- 直接點 URL（在同一台電腦上開）
- 或複製 token，到「我的課程 → 掃描 QR 簽到」貼上模擬掃描

效果完全一樣，只是少了「手機掃實體 QR Code」的儀式感。

---

## API 文件

啟動後端後造訪：[http://localhost:8000/docs](http://localhost:8000/docs)

完整 Swagger UI，可以直接在瀏覽器測試每個 API。

主要端點：
- `POST /api/auth/login` — 模擬 SSO
- `GET /api/employees` — 列出所有員工
- `GET /api/employees/{id}/dashboard` — 一次取得儀表板所需所有資料
- `GET / PUT /api/employees/{id}/ilp` — ILP 讀寫
- `POST /api/ilp/generate-plan` — AI 產生計畫
- `GET / POST /api/employees/{id}/reflections` — 反思日誌
- `GET /api/resources?employee_id=X` — 智能資源推薦
- `POST /api/coach/chat` — AI 教練對話
- `GET /api/analytics/heatmap` — 全體能力熱圖
- `GET /api/analytics/common-goals` — ILP 共通需求
- `GET /api/analytics/insights` — 智能洞察

---

## 檔案結構

```
chimei_backend/
├── main.py            # FastAPI app + 所有 API 端點
├── database.py        # SQLite 連線 + schema 初始化
├── seed.py            # 種子資料（6 位學員 + 18 項資源）
├── frontend.html      # 前端 UI（fetch /api/*）
├── requirements.txt   # Python 相依套件
├── README.md          # 本檔案
└── chimei.db          # SQLite 資料庫（執行 seed.py 後產生）
```

---

## 從 MVP 邁向正式版的修改點

### 1. 資料庫
| 環節 | MVP | 正式版 |
|---|---|---|
| 資料庫 | SQLite | PostgreSQL / SQL Server |
| 連線方式 | sqlite3 | SQLAlchemy + asyncpg |
| 備份 | 無 | 院內資料庫備援機制 |

### 2. 認證
| 環節 | MVP | 正式版 |
|---|---|---|
| 登入 | 直接接受人事號 | LDAP / Active Directory / Azure AD SSO |
| Token | mock 字串 | JWT + refresh token |
| 權限 | 無 | RBAC（學員 / 教師 / 教學中心 / HR） |

### 3. AI 服務
| 環節 | MVP | 正式版 |
|---|---|---|
| AI 教練 | 規則式回應 | Claude API / 院內 LLM |
| ILP 產生 | 規則式 | Claude API + RAG（讀院內 SOP） |
| 智能洞察 | 寫死 | Claude API 動態生成 |

### 4. 整合奇美現有系統
- **HR 系統** → 同步員工檔案、人事號
- **E-portfolio** → 同步病摘、Mini-CEX、CbD、360 度評分
- **教育訓練系統** → 同步課程記錄、認證
- **Outlook / 院內行事曆** → 同步教學活動

### 5. 部署
| 環節 | MVP | 正式版 |
|---|---|---|
| 執行環境 | 本機 python | Docker + Kubernetes / Azure App Service |
| 監控 | 無 | Prometheus + Grafana |
| Log | 無 | Application Insights / ELK |

---

## 常見問題

### Q: 啟動後 http://localhost:8000 無法開啟
- 確認 `python main.py` 仍在執行（Terminal 視窗未關）
- 確認沒有其他程式佔用 8000 port
- 防火牆是否擋住

### Q: 資料庫位置在哪？
- `chimei_backend/chimei.db`，可用 [DB Browser for SQLite](https://sqlitebrowser.org/) 開啟查看

### Q: 怎麼重置資料庫？
- 刪除 `chimei.db` 檔案，再執行 `python seed.py`

### Q: 怎麼新增學員？
- 編輯 `seed.py` 的 `EMPLOYEES` list
- 刪除 `chimei.db`，重新執行 `python seed.py`
- 或正式版透過 HR 系統 API 自動同步
