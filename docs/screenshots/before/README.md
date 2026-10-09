# Before screenshots

Automated Playwright capture requires running backend (port 8000) + frontend (port 3000) with demo auth.
Audit table in `UI_PROGRESS.md` is the source of truth for Phase 1.

To capture later:
```powershell
# backend
uvicorn backend.main:app --port 8000
# frontend
npm run dev --prefix frontend
# then
npx playwright screenshot --viewport-size=1440,900 http://localhost:3000/login docs/screenshots/before/login.png
```
