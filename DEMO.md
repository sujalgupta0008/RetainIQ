# DEMO.md — 3-minute hackathon script (exact words + clicks)

> Total ~180s. Login BEFORE the timer starts. Keep http://localhost:3000 + http://localhost:8000/docs open.

**0:00–0:20 — Hook (Command Center).**
"Financial churn tools answer *who will leave*. RetainIQ answers: *who should we save, what
should we do, what will it cost, and will it be profitable?* This is the Executive Command
Center — every number is computed live from the database." Point at **Revenue at Risk (est.)**,
**High-risk count**, **Expected ROI**.

**0:20–0:50 — Customer 360.**
"Let's open our riskiest high-value customer." Customers → sort by Revenue at Risk → open #1.
"Risk 87% — and here's *why*, in plain English, computed from real behavior deltas, not
hallucinated: transaction frequency fell, balance fell, complaints spiked." Scroll to
**trajectory** (90→today rising) and **Recommended next best action** with cost/success/ROI.

**0:50–1:20 — ROI Simulator (hero).**
"This is the hero." Open ROI Simulator. "A ₹10 lakh retention budget." Set churn threshold
50%, success-rate slider 28% → ROI updates live. Drag success to 15% → ROI drops; to 40% →
soars. "Every board question — what if our success rate is wrong? — answered by the
conservative/expected/optimistic scenarios."

**1:20–1:50 — Campaign + Experiment.**
Campaigns → Create "Diwali Save" (rm_call, proba ≥0.5) → projected ROI shown *before* spend →
Launch. Open it: "80/20 treatment/control A/B. Treatment retention vs control, incremental
lift, revenue protected, ROI — measured, not predicted."

**1:50–2:20 — AI Analyst.**
Ask: *"How should we spend ₹10 lakh to maximize expected retention value?"* "The analyst
queries live aggregates — top accounts, segment risk, intervention success — and answers with
real numbers. No API key needed: deterministic analytics fallback; plug in Gemini/OpenAI keys
and it upgrades to LLM prose grounded in the same data."

**2:20–2:40 — Model trust.**
Risk & Model page: "AUC 0.91, precision/recall/F1 + confusion matrix. XGBoost with logistic
baseline — and every prediction is explainable."

**Close (one line):**
"RetainIQ turns churn prediction into a P&L decision — who to save, what to do, and whether
it pays."

## Backup answers
- "Is XGBoost really used?" → Yes, with HistGradientBoosting fallback if the package is missing; metrics on the Risk page prove it.
- "Real money?" → Estimates labeled everywhere; only experiment outcomes are called realized.
- "Multi-tenant?" → One-click Demo Fintech login on the login page — different data, same app.
