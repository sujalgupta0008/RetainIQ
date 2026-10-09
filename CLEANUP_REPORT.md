# RetainIQ — Cleanup + Optimization Report (`chore/cleanup`)

Date: 2026-10-06 · Branch: `chore/cleanup` (from `audit/full-sweep`).
Rule: behavior identical (same routes/shapes/schema/UI). Verified by tests + live checks, not claimed.

## 1. Before vs after

| Metric | Before | After |
|---|---|---|
| Backend LOC (35 py files) | 2955 | **2949** (-6; -30 dup lines, +25 shared helper, -imports) |
| Frontend LOC (25 ts/tsx/js/css) | 1234 | **1228** (-6) |
| Tracked files | 87 | **88** (+`CLEANUP_PROGRESS.md`; report files stay for review, see §5) |
| Worktree junk | ~140 MB (`.next` 130MB, test DBs 4.8MB, pycache/caches) | **Removed** (regenerable; `retainiq.db` + `node_modules` kept) |
| npm deps | +knip, +depcheck (dev only, deliberate) | No removable prod dep found (recharts/lucide used; rest is build/config) |
| Build (shared First Load JS) | 87.5 kB | **87.5 kB** (unchanged — removals were sub-KB; no bundle win claimed) |
| Tests / coverage | 66 passed, 89% | **66 passed, 90%** (fewer statements, same tests — no drop) |
| Ruff F401/F841/F811/ERA001 | 16 hits | **2 hits, both in protected `tests/` (kept per rules)** |
| Vulture ≥80% | false positives only | Same — nothing actionable |
| Bandit | 0 | **0** |
| Secrets scan (gitleaks N/A → grep fallback) | clean | **clean** |
| Backend boot + flows | OK | **OK** (login→dashboard→product-risk→segments→recs, live DB untouched) |
| Frontend prod serving | OK | **OK** (`next start`, `/login` 200) |
| Product-risk queries (6 products) | 19 SELECTs (N+1) | **4–5 SELECTs** (~5x fewer round trips, measured) |

## 2. Removed items

| Removed item | Type | Location | Proof it was unused |
|---|---|---|---|
| `import shap` (line) | import | `backend/ml/explain.py:4` | grep: only occurrence; fn returns `None` either branch (behavior identical) |
| `json` + top-level `numpy` | imports | `backend/ml/infer.py:13-14` | 0 `json.` uses; `np.` used only where a local `import numpy` exists (kept) |
| `func` | import | `backend/routes/analytics.py:3` | 0 `func.` matches in file |
| `func` | import | `backend/routes/segments.py:3` | 0 `func.` matches in file |
| `ACTIONS` (name only) | import | `backend/routes/campaigns.py:7` | sole match was the import line |
| `math`, `deterioration`, `audit`, `FEATURES` (names only) | imports | `backend/seed.py:2,9` | 0 uses each (`random`/`datetime` kept — used) |
| `now = ...` | dead assignment | `backend/seed.py:132` | ruff F841; timestamps come from model `default=now` |
| `secrets`, `random`, `from datetime import …` | imports | `backend/services.py:2-3` | 0 uses (`import datetime as dt` local kept — used by `make_token`) |
| `inr2` (dup of `inr`) | export | `frontend/lib/format.ts:3` | 0 refs (knip + grep) |
| `Empty` component | component | `frontend/components/ui.tsx:52` | 0 refs (knip + grep) |
| `__pycache__`, `.pytest_cache`, `.ruff_cache`, `.coverage`, `test_audit.db`, `test_smoke.db`, `frontend/.next` | caches | worktree (all gitignored) | regenerable; `retainiq.db` explicitly kept |
| `FEATURES` constant | const | `backend/services.py:8` | 0 refs repo-wide (train/infer keep their own lists) |
| Duplicated product-risk N+1 loop (×2) | logic | `dashboard.py:50-59`, `services.py:244-256` | replaced by single `product_risk_rows()`; covered by endpoint + AI tests |

Security code untouched: auth/tenant filters/validation/rate limits/headers/`escape_like`/caps all intact (grep-verified still present).

## 3. Optimizations (measured)
- **`product_risk_rows()` (services.py), used by `/api/dashboard/product-risk`, `/api/analytics/products`, and `analyst_context`**: 3 batched SELECTs + 1 product lookup instead of 1+3×P queries. Measured on live DB (6 products, read-only): **19 → 4 queries** for the helper. Output shape verified byte-compatible by existing tests (`test_endpoints`: product-risk, analytics, AI analyst) — all 66 pass.

## 4. Needs human review (kept deliberately)
1. `AUDIT_PROGRESS.md`, `AUDIT_REPORT.md`, `CLEANUP_PROGRESS.md` (+ this file): keep in repo vs move to `docs/`? Currently root-level; suggest `docs/` move in a follow-up (or keep — your call).
2. `next/dynamic` lazy-loading for recharts pages: would shrink per-route JS but adds `ssr:false` churn; shared bundle already 87.5 kB — not worth it now.
3. Customers-list in-memory sort/paginate (`q.all()` + Python slice): fine at current scale (7k rows); move to SQL `ORDER BY/LIMIT` only if it grows 10x.
4. `token`/`authHeaders` (knip-flagged): used inside `lib/api.ts` — kept as public lib API.
5. `cls` in pydantic validators, FastAPI handlers, ORM columns: framework-required — kept.
6. Test-only unused imports (`pytest`, `asyncio`): protected by cleanup safety rules — kept.
7. `backend/ml/artifacts/model.pkl` (1.08 MB, only file >1MB): protected artifact — consider Git-LFS later.
8. Next 15 / pin-refresh / cookie-auth items from `AUDIT_REPORT.md` §5: out of cleanup scope, unchanged.

## 5. Final push checklist
```powershell
git log --oneline -8            # expect: perf + docs + refactor commits on chore/cleanup
git status                      # expect: clean
python -m pytest backend/tests/ -q        # expect: 66 passed
npm run build --prefix frontend           # expect: Compiled successfully
git push -u origin chore/cleanup
```
Suggested PR title: `chore(cleanup): drop dead code, batch product-risk queries (19→4)`
Suggested PR body: "No behavior change (66 tests green, 90% cov, build + live flows verified). Removes 10 proven-dead imports/exports/vars, 1 dead constant, 2 dead frontend exports; dedupes product-risk aggregation into one batched helper (19→4 SELECTs); clears ~140MB regenerable worktree junk (gitignored). Protected files (db, models, tests, security, lockfiles) untouched. Reports: CLEANUP_PROGRESS.md; audit context in AUDIT_REPORT.md."
