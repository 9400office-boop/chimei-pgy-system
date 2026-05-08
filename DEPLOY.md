# 部署指引：GitHub → 公開 demo URL

## 為什麼不用 Vercel？

你提到想用「GitHub → Vercel」工作流。Vercel 確實很方便，但**我們的後端用 SQLite + FastAPI，Vercel 的 serverless 環境檔案系統是唯讀的，無法寫入 SQLite**。要走 Vercel 必須整個架構改造（換 Vercel Postgres 或 Turso、把 FastAPI 改成 serverless functions），工程量很大。

**最接近 Vercel 體驗的替代方案：Railway**
- ✅ 一樣 GitHub 連結後自動部署
- ✅ 一樣推 commit 自動更新
- ✅ 一樣免費取得公開 URL（如 `chimei-pgy.up.railway.app`）
- ✅ 支援 SQLite + FastAPI，不用改一行程式碼
- ✅ 免費額度：每月 $5 美金額度 + 500 hours 執行時間（demo 完全夠用）

替代方案還有 **Render**（類似但 free tier 會在閒置 15 分鐘後睡眠）、**Fly.io**（要裝 CLI）。本指引以 Railway 為主。

---

## 完整步驟（從零到 demo URL，約 15 分鐘）

### 步驟 1：建立 GitHub Repo

1. 註冊 / 登入 [GitHub](https://github.com)（如果還沒帳號）
2. 右上角 `+` → `New repository`
3. Repo 名稱：`chimei-pgy-system`（或你喜歡的）
4. **設為 Private**（醫療相關內容建議私人）
5. 勾選 `Add a README file`
6. 按 `Create repository`

### 步驟 2：上傳 chimei_backend 整個資料夾到 GitHub

**最簡單方式（用網頁拖曳上傳）：**

1. 進入剛建立的 repo
2. 按 `Add file` → `Upload files`
3. 把 `chimei_backend` 資料夾裡的**所有檔案**拖進去（不要拖整個資料夾，要拖**裡面的檔案**）：
   - `main.py`
   - `database.py`
   - `seed.py`
   - `frontend.html`
   - `qr_checkin.html`
   - `requirements.txt`
   - `Dockerfile`
   - `Procfile`
   - `railway.json`
   - `.gitignore`
   - `README.md`
4. 下方 commit message 寫 `Initial commit`，按 `Commit changes`

⚠️ **不要上傳 `chimei.db`** — `.gitignore` 已經設定排除，但拖檔案時也注意不要拖它

**進階方式（用 git command line）：**
```bash
cd chimei_backend
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/你的帳號/chimei-pgy-system.git
git push -u origin main
```

### 步驟 3：到 Railway 部署

1. 開瀏覽器到 [railway.app](https://railway.app)
2. 按 `Login` → 用 GitHub 帳號登入（按 `Login with GitHub`）
3. 進入 dashboard 後按 `+ New Project`
4. 選 `Deploy from GitHub repo`
5. **第一次使用時** Railway 會請你授權存取 GitHub 的 repo，按 `Configure` 選 `Only select repositories` → 選 `chimei-pgy-system` → 按 `Install & Authorize`
6. 回到 Railway，再按一次 `Deploy from GitHub repo`，這次就會看到你的 repo
7. 點 `chimei-pgy-system`
8. Railway 會**自動偵測 Dockerfile**，開始建置
9. 等 2-3 分鐘，看到 `Build successful` + `Deployed`

### 步驟 4：取得公開 URL

1. 進入剛建立的 service
2. 按 `Settings` 分頁
3. 找到 `Networking` 區塊，按 `Generate Domain`
4. Railway 會給你一個公開網址，類似 `chimei-pgy-system-production.up.railway.app`
5. 等 30 秒讓 DNS 生效，**用瀏覽器開那個網址**

🎉 你的系統已經在 internet 上跑了！把網址貼給任何人都能開。


### 步驟 4.5：在 Railway 設定密碼（重要）

部署完成後，建議**立即設定密碼保護**，避免任何 internet 上的人都能存取：

1. 進入你的 Railway service
2. 按 `Variables` 分頁
3. 按 `+ New Variable` 新增兩筆：
   - 名稱：`DEMO_USER`，值：`demo`（或你想要的帳號）
   - 名稱：`DEMO_PASSWORD`，值：`chimei2026`（或你想要的密碼，至少 8 字元）
4. Railway 會偵測變更並自動重新部署（約 30 秒）
5. 重新整理你的 demo 網址 → 會跳出瀏覽器原生的帳密提示窗
6. 輸入剛剛設定的帳密就能進入

**未設這兩個環境變數的話，網站完全不需要密碼**（適合本機開發）。

把帳密用比較安全的方式分享給要試用的同事（如 Line 私訊，不要寫在公開文件）。

### 步驟 5：之後要修改怎麼辦？

任何人改了 GitHub 上的檔案 → **Railway 會自動重新部署**（與 Vercel 一樣）

---

## 替代方案 A：Render

如果你想用 Render（也很簡單）：

1. [render.com](https://render.com) 用 GitHub 帳號註冊
2. Dashboard → `New +` → `Web Service`
3. 連結 GitHub → 選 `chimei-pgy-system`
4. Render 會偵測 Dockerfile，按 `Create Web Service`
5. 等部署完成 → 拿到網址 `chimei-pgy-system.onrender.com`

**Render 的差異**：免費版閒置 15 分鐘會睡眠，下次有人開時會 cold start（30 秒慢）。Railway 不會。

---

## 替代方案 B：真的非要 Vercel 不可

如果你**一定要 Vercel**（例如你已經有 Vercel 帳號），需要這些改造：

1. **資料庫換掉**：SQLite 改用 [Turso](https://turso.tech)（免費 LibSQL，是 SQLite 變雲端版）或 Vercel Postgres
2. **FastAPI 改 serverless**：把 `main.py` 改寫成 Vercel 的 serverless function 格式（每個 endpoint 變成獨立的 `/api/xxx.py`）
3. **靜態前端**：`frontend.html` 改放 `/public/index.html`，靜態 serve

這些工程約需 1-2 天。如果你真的需要這條路，告訴我，我可以幫你改造。

---

## 部署後的注意事項

### A. 資料庫資料會在部署後重置嗎？

**會** — Railway 每次重新部署都會重建容器，SQLite 資料會還原到 seed 資料。如果你在 demo 中新增了反思、回饋、課程，重新部署後會消失。

**正式版解決方法**（已寫在架構文件中）：
- 把 SQLite 換成 Railway 提供的 Managed PostgreSQL（按一個按鈕就有，免費 500MB）
- 或加上 Volume mount 讓 SQLite 檔案持久化

但 demo 階段不重要 — 同事看完關掉就好。

### B. QR Code 簽到還能用嗎？

可以！部署後 QR Code 內含的 URL 會自動變成 Railway 的公開網址（例如 `chimei-pgy-system-production.up.railway.app/qr-checkin?token=xxx`），任何手機只要有網路都能掃。

### C. 我還想改畫面或加功能怎麼辦？

1. 直接在 GitHub 編輯檔案（網頁上點檔案 → 鉛筆 icon → 改 → Commit）
2. Railway 會在 1-2 分鐘內自動重新部署
3. 重新整理你的網址即看到新版

### D. 怎麼分享給同事 / 主管 demo？

把 Railway 給的 URL 貼給他們即可，不需要 VPN、不需要在同 WiFi。任何人都可以：
- 用人事號 P10001 ~ P10006 登入
- 切換三種視角體驗
- 完整使用 QR 簽到 / 課程 / ILP 等功能

如果是給高層 demo，建議先在分享前測一次：
1. 自己用無痕視窗開那個 URL
2. 跑一輪：登入 → 雷達圖 → 我的課程 → 教師簽核 → 看到能力分數變化

確認沒問題再分享。

---

## 故障排除

### Railway 顯示 "Build failed"

點 `Deployments` → 最新一筆 → 看 build log，最常見原因：
- requirements.txt 漏了某個套件 → 加上去
- 某個檔案沒上傳到 GitHub → 補上

### 網址 404

Railway 部署後可能 cold start 30 秒，再重整一次。如果還是 404，看 `Deployments` → `Logs` 有沒有 error。

### 想刪掉重來

Railway dashboard → 該 project → Settings → Danger Zone → Delete Project。

GitHub repo 也要砍：repo → Settings → Danger Zone → Delete this repository。

---

## 個資合規提醒（重要）

雖然這是 demo 用虛擬資料，但部署到雲端後**任何在 internet 上的人都可能存取**。建議：

1. **不要把真實學員資料放進去** — 目前的 6 位學員是真實 ILP 問卷的姓名，建議在 demo 給外部看前**改成假名**（在 `seed.py` 把 name 改掉）
2. **加上簡單密碼** — 可以在 main.py 加個 HTTP Basic Auth，避免被路過的人亂用
3. **正式版必須走院內網路** — 醫療資料依《個資法》與《醫療法》第 67 條不得未經同意外傳，雲端 demo 只適合 mock 資料測試

如果想加密碼，告訴我，我可以幫你加上 HTTP Basic Auth（5 分鐘搞定）。
