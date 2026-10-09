# RetainIQ — Simulator Guide (User Manual)

> Yeh file batati hai ki as a user aap RetainIQ app ko kaise open karenge,
> har button kya karta hai, app andar se kaise kaam karta hai,
> aur poore app ko end-to-end kaise simulate karenge.

---

## 1. App ko open kaise kare (Step-by-Step)

### Step 1 — Backend start karo (Terminal 1)
```powershell
cd 'D:\LATEST PROJECT\RetainIQ'
python -m uvicorn backend.main:app --reload --port 8000
```
- API chalegi: http://localhost:8000
- Docs (API list): http://localhost:8000/docs

### Step 2 — Frontend start karo (Terminal 2)
```powershell
cd 'D:\LATEST PROJECT\RetainIQ\frontend'
npm run dev
```
- App khulegi: **http://localhost:3000**

### Step 3 — Login karo
- Browser me http://localhost:3000 kholo → `/login` page khulega.
- **Option A (asli login):** Email + Password bharo → **Sign in** dabao.
- **Option B (1-click demo — easy):**
  - 🏦 **Demo Bank** button → 400 customers wala data khulega
  - 💳 **Demo Fintech** button → 200 customers wala data khulega
- Demo password: `demo123`
- Login hote hi app **Command Center (`/dashboard`)** par le jayega.

> Pehli baar setup kar rahe ho to backend me seed + training ek baar chalana hota hai:
> ```powershell
> python -m backend.seed --reset
> python -m backend.ml.train
> ```

---

## 2. Har page aur button kaise kaam karta hai

### 🔐 Login (`/login`)
| Button | Kaam |
|---|---|
| Sign in | Email + password check karke andar le jata hai |
| 🏦 Demo Bank | Bina type kiye Bank demo login |
| 💳 Demo Fintech | Bina type kiye Fintech demo login |

### 📊 Command Center (`/dashboard`)
Yeh home screen hai. 12 numbers (total customers, high-risk, revenue at risk, ROI % …) **database se live calculate** hokar aate hain. Neeche charts hain: risk distribution, segment-wise risk, risk trend, product-wise risk, value×risk quadrants, campaign performance. Yahan **koi button nahi** — sirf data dekhna hai.

### 👥 Customers (`/customers`)
| Cheez | Kaam |
|---|---|
| Search box | Naam se customer dhoondo (type karte hi filter) |
| All risk dropdown | High / Medium / Low risk se filter |
| All segments dropdown | Mass / Affluent / HNI / SME se filter |
| Sort dropdown | Revenue at risk / Churn prob / CLV / Name se ranking |
| Prev / Next | Pages badlo (20 customers per page) |
| Customer naam (link) | Click → uska 360° detail page khulta hai |

### 🧑 Customer 360 (`/customers/[id]`)
Customer ka poora profile: churn %, CLV, revenue at risk, **"why at risk" explanation** (asli behavior comparison se), risk trajectory chart (90 din ka), **recommended action** (cost + success % + ROI ke saath), balances, products, transactions. Yahan koi action button nahi — samajhne ke liye page hai.

### ⚠️ Risk & Model (`/risk`)
- Model ke marks: ROC-AUC, Precision, Recall, F1 + Confusion Matrix.
| Button | Kaam |
|---|---|
| Retrain model | Naya data aane par model dobara train + predictions refresh |

### 🧩 Segments (`/segments`)
4 box: High Value/High Risk, High Value/Low Risk, Low Value/High Risk, Low Value/Low Risk — paisa kahan atka hai, yeh dikhata hai. Sirf view page hai.

### ⭐ Next Best Actions (`/recommendations`)
Priority dropdown (Critical / High Priority / Monitor / Low Priority) se queue filter karo. Har row me customer + action + **kyun yeh action** (reason) + cost + success + expected ROI. Naam par click → Customer 360.

### 🧮 ROI Simulator (`/roi-simulator`) — HERO FEATURE
Sliders ghumao → numbers **live** badalte hain:
| Slider | Matlab |
|---|---|
| Churn threshold | Kitne % risk se upar walo ko target karna hai |
| Min CLV | Kitni value se upar wale customers |
| Intervention cost | Ek customer par kharcha (₹) |
| Expected success rate | Kitne % bachne ki ummeed |
| Campaign reach | Audience ka kitna % cover karenge |
- Output: targeted, retained, cost, revenue protected, net value, **ROI %**, break-even rate.
- Neeche **Conservative / Expected / Optimistic** scenarios ka chart.
| Button | Kaam |
|---|---|
| Create campaign from this audience → | Campaigns page par le jata hai |

### 📣 Campaign Studio (`/campaigns`)
**Left form — New campaign:**
- Name, Intervention (cashback, rm_call…), Min churn prob, Min CLV, Offer cost, Expected success, Duration bharo →
| Button | Kaam |
|---|---|
| Create & project ROI | Campaign banao + **kharch karne se PEHLE** projected ROI dikhao |
**Right table:** sab campaigns + status + **Open →** link (detail page).

### 📣 Campaign Detail (`/campaigns/[id]`)
| Button | Kaam |
|---|---|
| Launch campaign | 80% treatment / 20% control me baantkar simulated result nikalo |
- Launch ke baad: Control vs Treatment retention, **incremental lift**, cost, revenue, ROI.

### 🧪 Experiments (`/experiments`)
Har campaign ka A/B test result table: treatment vs control retention, lift, revenue, ROI. Sirf view page hai.

### 📈 Analytics (`/analytics`)
- **Alerts:** risk spike / danger-zone customer / low-ROI experiment (naam par click → customer khulta hai).
- **Product analytics:** kaunse product me kitna risk.
- **Behavioral deterioration:** bigadte hue customers ki list.

### 🤖 AI Analyst (`/ai-analyst`)
- Upar ready-made sawal chips (click karte hi jawab aata hai).
- Neeche apna sawal type karo → **Ask** dabao (Enter bhi chalega).
- Jawab **live database numbers** se banta hai, man-gadhant nahi.
- Try karo: *"How should we spend ₹10 lakh to maximize expected retention value?"*

### 💾 Data (`/data`)
| Button | Kaam |
|---|---|
| Choose CSV | File chuno → **dataset auto-detect** (banking / IBM Telco / generic) + mapping preview |
| Import & Normalize | Preview ke baad customers import karo (Telco ke Churn Value ko label banakar) |
| Download sample CSV | Banking sample file download |
| Retrain model | Import ke baad model ko naya data sikhao + predictions refresh |

### ⚙️ Settings (`/settings`)
- User, role, tenant info + **Audit log** (login, simulate, campaign, upload, AI — sab record).
| Cheez | Kaam |
|---|---|
| Tenant ID + Switch tenant | Demo me Bank ↔ Fintech data badlo |
| Sign out (sidebar neeche) | Logout → login page |

---

## 3. Yeh app andar se kaise work karta hai (simple me)

```
Login (JWT token)
   ↓
Dashboard — database se live numbers
   ↓
ML Model — har customer ka churn % nikalta hai
   (tenure, balance trend, transaction frequency,
    complaints, logins, inactivity… 16 signals)
   ↓
Explain — risk KYUN hai (tenant average se tulna karke, plain English me)
   ↓
CLV × Churn % = Revenue at Risk (₹)
   ↓
Priority Score — Critical / High / Monitor / Low
   ↓
Next Best Action — sabse profitable action (success × CLV − cost)
   ↓
ROI Simulator — "agar itna kharch kiya to kitna milega?" (estimate)
   ↓
Campaign — audience + action + budget → Launch (80/20 A/B test)
   ↓
Experiment Result — lift, revenue, ROI (measured)
   ↓
AI Analyst — inhi real numbers par sawal-jawab
```

**3 golden rules yaad rakho:**
1. **Estimated / Predicted** = andaza (model ya simulation) · **Realized** = campaign se mapa hua.
2. Paisa kharch karne se **pehle** ROI Simulator me check karo.
3. Naya CSV dalne ke baad **Retrain** dabana mat bhoolo, tabhi model naya data seekhega.

---

## 4. Poore app ka full simulation (15 minute me, as a user)

### Part A — Dekho (5 min)
1. 🏦 **Demo Bank** se login karo.
2. **Dashboard:** Revenue at Risk (₹) aur High-risk count note karo.
3. **Customers** → Sort: *Revenue at risk* → sabse upar wale naam par click.
4. **Customer 360** me padho: churn % kya hai, **kyun** hai (explanation box), recommended action kaunsi hai.
5. **Risk & Model:** AUC / Precision / Confusion Matrix dekho (model kitna bharosemand hai).
6. **Segments:** sabse zyada paisa kaunse box me atka hai?

### Part B — Socho + Simulate (4 min)
7. **Next Best Actions:** Priority = *Critical* filter karo → top 5 note karo.
8. **ROI Simulator:** sliders set karo — threshold 50%, Min CLV ₹50,000, cost ₹1,000, success 28% → ROI % dekho.
9. Success slider ko 15% karke dekho (ROI girta hai), phir 40% karo (ROI uchalta hai) — yahi **sensitivity analysis** hai.
10. Budget wala sawal ready karo: ₹10 lakh.

### Part C — Karo + Maapo (4 min)
11. **Campaigns:** form bharo — Name `Diwali Save`, Intervention `rm_call`, Min prob `0.5`, Offer cost `1000`, Expected success `0.3` → **Create & project ROI** (kharch se pehle andaza!).
12. Campaign **Open →** → **Launch campaign** dabao.
13. Result dekho: Treatment vs Control retention, **lift %**, revenue, ROI.
14. **Experiments** page me apna experiment verify karo.

### Part D — AI se poocho + doosra tenant (2 min)
15. **AI Analyst:** poocho — *"How should we spend ₹10 lakh to maximize expected retention value?"* → jawab me real customer naam + numbers check karo.
16. **Sign out** → 💳 **Demo Fintech** se login → Dashboard badla hua dikhega (alag data, same app — yahi multi-tenancy hai).
17. **Data** page: sample CSV download karo → Choose CSV → preview dekho → Import → **Retrain** → Dashboard numbers update.

### ✅ Simulation complete checklist
- [ ] Login (dono tenants)
- [ ] Dashboard numbers dekhe
- [ ] Customer 360 + explanation padha
- [ ] Model metrics dekhe
- [ ] ROI simulator sliders ghumaye + scenarios dekhe
- [ ] Campaign banaya + launch kiya + lift/ROI dekha
- [ ] AI se budget sawal poocha
- [ ] CSV import + retrain kiya
- [ ] Audit log me apne actions dikhe (Settings)

> Demo me dikhana ho to `DEMO.md` me 3-minute wala script ready hai.
