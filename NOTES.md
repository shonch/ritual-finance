# Valhalla notes (as of 2026-10-11)

Written so a future session can start from facts instead of memory.

## How it runs now
- Everything runs locally on this Mac. The cloud copy (Render, Vercel, Atlas) still exists but its data is stale. Enter data only on this machine, never on the website.
- Start Phoenix with `phoenix`. MongoDB runs as the launchd agent `local.mongodb` on 127.0.0.1:27017, data in `~/mongo-data`, one database `phoenix_engine`.
- Env files (both gitignored): Phoenix `~/phoenix/phoenix_portfolio/.env`, Valhalla `~/git_repos/active/emotional_budget_tracker/.env`. The old Atlas versions are in `~/Backups/env-atlas/`.
- Frontend is `~/phoenix/phoenix_frontend` (SvelteKit). Typing a page address into the browser sends you to login; get to pages through the in-app links.

## Backups
- `~/Backups/nightly-backup.sh` dumps phoenix_engine daily at 20:00 (launchd agent `local.valhalla-backup`). It keeps 30 days and logs to `~/Backups/nightly.log`. Run it by hand with `bash ~/Backups/nightly-backup.sh`, especially after entering a lot of data.
- Restore only from these dumps (a test restore recovered 728 of 728 documents). Do not rely on a cloud backup of the live `~/mongo-data` files.
- Backblaze license problem: support ticket sent 2026-10-11, no answer yet. Once it works, confirm `~/Backups` is included in the backup.
- To do: check FileVault is on (`fdesetup status`). Consider a Backblaze private encryption key.

## Git
- Both repos use dev and main. Backend repo is ritual-finance (this one); frontend repo is phoenix_frontend. Vercel builds the frontend from main. Render only builds when triggered by hand (it pulls ritual-finance from GitHub at build time).
- Before any git work: `git remote -v`, `git branch --show-current`, `git status`.
- Commit messages and PR text: no Co-Authored-By or Claude-Session lines.
- On 2026-10-11 dev and main matched: backend 9d5b5f3, frontend 395cd1d.

## What exists and why
- Hall: balance, projected month end, lowest point, so far this month, still owed.
- Foretelling: month arrows, up to 3 months ahead.
- History page (`/valhalla/history`): month arrows, all-time toggle, search across category, source, description and tags (every word must match), type and status filters, sorting, 25 per page. Backed by GET /valhalla/transactions/ with q, type, status, sort, limit, skip, slim; it also returns a total.
- Burdens: category and balance fields removed. A Burden is a cash-flow commitment only.
- Posted transactions are written in stone. Only foretold ones can be edited or removed. A drifted balance is fixed with a reckoning adjustment.
- The Hoard card is hidden from the Hall. The page, its backend and the data are still there. Revisit with the savings plan in December.

## Open or deferred
- Savings plan: wait until checking has a cushion (probably December). The projection already has a `floor` option for a minimum balance. Two-way transfers between checking and savings are designed but not built: record a Ledger entry plus a link to the savings entry (the local database cannot do two writes as one unit, so undo the first if the second fails).
- Logout: skipped. It would only clear the stored token (convenience, not data safety).
- Tags vs free-text category: decide after real use. Autocomplete: deferred on purpose.
- Not yet tested: Foretelling Edit and Remove (try on a throwaway $1 entry); the first real Landed (permanent).
- Friction list: Hall "Still Owed" leaves out overdue Burdens; transaction field label "Category" vs "What was this for?"; Last Reckoned is gone from the Hall; projections treat ACH delay strictly; Hoard Owed and Net Worth semantics.
- Older backlog: plan-wide edit for NetCredit's rows; Coming Due list on Foretelling; read-only history; unique index on ragnarok_log; dead code (create_setup.py, edit_setup.py, generate_due_dates); legacy transactions without a status; the times_used double-increment bug; multi-tag UI; reconciliation-gap prompt; "balance after this" preview.

## Ideas
- Self-contained native Mac app: Swift and SwiftUI, local storage (SQLite or SwiftData), no server and no web engine. Work in the terminal with Neovim, `swift build` and `swift test`. Port Valhalla first, with tests that compare results against the Python version on a copy of real data. Prefer learning Swift hands-on over a bulk port. Swift 6.4 is installed; `~/swift-play` is a throwaway test project. Xcode is only needed for packaging and signing; RAM is 8 GB on an M1, so keep Xcode use short.
- Privacy position: data stays on this machine. Cloud backup would have to be encrypted or opt-in for that to stay true.
