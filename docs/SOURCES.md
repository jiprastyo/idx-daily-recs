# Source catalog (verified 2026-08-01)

All URLs were live-checked. Publish-time column = observed/known pattern (see research
file `~/Downloads/Indonesia_Sekuritas_Daily_Research_Map.md` for evidence).

## A. JSON APIs (highest value, structured)

| key | Firm | Method | Endpoint | Notes |
|---|---|---|---|---|
| shinhan | Shinhan Sekuritas Indonesia | POST, JSON | `https://shinhansekuritas.co.id/research/getData` | Returns `viewDaily` / `viewTopic` / `viewOutlook`; PDFs at `https://shinhansekuritas.co.id/file/daily/<file>` |
| minnapadi | Minna Padi Investama Sekuritas Tbk | GET | `https://minnapadi.com/daily-reports-ajax` (token `s4Tjltz4mAeficNg0cgUgjo1aqGfqVprWivXn572`) | Daily reports list; full reports at `/full-reports` |
| verdhana | Verdhana Sekuritas Indonesia | GET HTML | `https://verdhanaresearch.com` | Public equity-research site (BUY reports w/ TP) |
| yuanta | Yuanta Sekuritas Indonesia | GET HTML | `https://www.yuanta.co.id` | Homepage "Latest Research": timestamps + `BUY / TP: IDR:<n>` |

## B. Tier A — listing page → daily report (PDF/HTML)

| key | Firm | Listing URL | Report form |
|---|---|---|---|
| nh | NH Korindo | `https://www.nhis.co.id/id/research/riset-reguler/` | HTML article `/id/daily-report-<date>/` |
| samuel | Samuel | `https://samuel.co.id/research-reports/` | Morning Briefs PDF (published ~07:46 WIB) |
| most | Mandiri MOST | `https://www.most.co.id/riset` | Morning Notes / Afternoon Highlight / Investor Digest |
| mnc | MNC Sekuritas | `https://www.mncsekuritas.id/category/2/` | MNCS Daily Scope |
| mega | Mega Capital | `https://www.megasekuritas.id/research.asp` | Equity Daily Report |
| waterfront | Waterfront | `https://waterfrontsekuritas.com/research` | Daily Report PDF (Unduh) |
| kbvalbury | KB Valbury | `https://www.kbvalbury.com/research/daily-technical-analysis` | Trading Ideas inline |
| victoria | Victoria | `https://victoria-sekuritas.co.id/` | Daily Analysis PDFs (`/wp-content/uploads/…/Daily-Analysis-<date>.pdf`) |
| kiwoom | Kiwoom | `https://www.kiwoom.co.id/market/getMarketReportMain` | Daily Report |
| ajaib | Ajaib | `https://ajaib.co.id/saham/rekomendasi-saham` | Daily article (picks w/ TP/SL) |
| binaartha | Binaartha | `https://binaartha.com/technical-research.html` | Inline technical picks |
| phintraco | Phintraco | `https://phintracosekuritas.com/riset/` | Inline riset posts |
| panin | Panin | `https://pans.co.id/riset` | Daily Technical Recommendation PDF |
| artha | Artha | `https://www.arthasekuritas.com/id/research-analysis.php` | Download Report |
| ocbc | OCBC | `https://www.ocbcsekuritas.com/` | Analisis & Riset (Mid Day Market Update) |
| maybank | Maybank | `https://www.maybank-ke.co.id/riset` | Riset (Tiger Daily) |
| phillip | Phillip | `https://www.phillip.co.id/` | Rekomendasi Saham Harian |
| uob | UOB Kay Hian | `https://utrade.co.id/Research.aspx` | Daily review w/ stock pick |
| cgs | CGS International | `https://www.cgsi.co.id/insights` | Riset articles |
| sucor | Sucor | `https://www.sucorsekuritas.com/product/research/` | Equity Report |
| sf | Surya Fajar | `https://www.sfsekuritas.co.id/produk-layanan/research-recommendation` | Capital Riset |
| evergreen | Evergreen | `https://evergreensekuritas.co.id/news/riset` | Riset articles |
| reliance | Reliance | `https://reliancesekuritas.com/` | Morning Coffee |

## C. YouTube RSS (no API key)

`https://www.youtube.com/feeds/videos.xml?channel_id=<UC…>` — channel ID resolved from
handle at runtime. Handles: `@MiraeAssetSekuritas`, `@rhbsekuritas`, `@bnisekuritas`,
`@PhillipSekuritasIndonesia` (fallback `@talktophillip`), `@maybanksekuritas`,
Sinarmas `channel/UCDMD0mwkcz9pe-3rnmbn9WQ`, KAF `@KAFSekuritasIndonesia`.

## D. X (optional, needs local `xurl` + credentials)

Handles: `@MaybankTradeID`, `@MiraeAssetID`, `@SM_Sekuritas`, `@Stockbit`, `@semesta_mg`.
Disabled by default in CI (no credentials); see `docs/DEPLOY_LOCAL.md`.

## Excluded by design

- **Instagram** — login wall/anti-bot; not scrapable reliably (KGI daily picks, Trimegah
  Trima+ Picks, RHB/BNI IG posts live there; manual paste workflow documented in
  `docs/MAINTENANCE.md`).
- App-only feeds (IPOT, BIONS, SimInvest, Maybank Trade ID, POEMS, HEI5).
- Tier C firms confirmed to publish nothing public (see research map).

## Current status (verified 2026-08-01, live run)

| Status | Sources |
|---|---|
| ✅ Working (records produced) | shinhan (80), mega (13), minnapadi (16), artha (9), verdhana (6), yuanta (6), YT: maybank/sinarmas/rhb/mirae/phillip/kaf, samuel, nh, ajaib (structured price/TP/SL), kbvalbury, kiwoom, binaartha, phillip, evergreen |
| ⚠️ Flaky (work intermittently from some networks; health shows `failed` on bad days) | shinhan, kiwoom, waterfront, yuanta, victoria — DNS/connect hangs; per-source daemon threads + timeouts keep them from stalling the run |
| 🔒 JS-rendered, not scrapable via plain HTTP | mnc (Next.js), waterfront (React), victoria, panin, most (403), ajaib (article is server-rendered — works) |
| ➖ Reachable, no picks found on a given day | ocbc, maybank, uob, cgs, sucor, sf, reliance, phintraco |
| ⏭️ Skipped by default | x (needs local `xurl` + credentials, `--with-x`) |

## Measured publish times (2026-08-01, live probe)

Methods: YouTube RSS `<published>` timestamps (last 15 uploads/channel, exact);
`article:published_time` meta; PDF `Last-Modified` headers (GMT → WIB = +7h).
Times are WIB. Small samples — treat as typical windows, not guarantees.

| Source | Evidence | Typical publish (WIB) |
|---|---|---|
| Minna Padi (Morning Dew PDF) | Last-Modified, 2 days | **04:45–07:45** (pre-market) |
| Samuel Morning Brief | article meta, 1 day | **~07:46** (pre-market) |
| Shinhan Daily (bond/equity PDF) | Last-Modified, 1 day | **~08:42** (pre-market) |
| Mega Equity Daily Report | Last-Modified, 2 days | **~08:30–08:45** (pre-market — not evening!) |
| RHB (YouTube Morning Stock Pick) | RSS, n=15 | **09:08** (tight 08:57–09:24) |
| Maybank (YouTube Tiger Daily/Chartist) | RSS, n=15 | **~10:12** (09:02–17:00) |
| Mirae (YouTube Morning Meeting) | RSS, n=15 | ~12:22 (mixed content, 06:09–20:15) |
| KAF (YouTube) | RSS, n=7 | ~14:01 (09:45–15:17) |
| Yuanta research updates | homepage timestamps, 6 samples | **11:00–11:30 and 14:50–15:30** |
| Phillip (YouTube) | RSS, n=4 | ~17:10 (15:21–23:23) |
| Sinarmas (YouTube) | RSS, n=15 | ~19:00 (08:53–19:00) |
| BNI (YouTube) | RSS, n=15 | **~21:25** (09:29–21:44 — evening uploads) |
| Samuel macro monitor | article meta, 1 day | 18:51 WIB (evening before) |

**Inferred from naming (no direct measurement):** MOST Morning Notes ~08:00, MOST
Afternoon Highlight ~16:00, BRI Danareksa Equity Snapshot evening (post-close),
KB Valbury/Kiwoom/Panin/Binaartha/Phintraco/Ajaib morning, Reliance "Morning Coffee"
morning, OCBC mid-day update, Trimegah Trima+ Picks (app, unknown).
**Unmeasurable (JS/403):** Victoria, Waterfront, Panin, MOST, NH (no meta found),
Artha (only install manuals on site), Trimegah.

### Cluster summary → scheduling

- **Pre-market cluster 04:45–08:45 WIB:** Minna Padi, Samuel, Shinhan, Mega
- **Mid-morning 09:00–10:30:** RHB (09:08), Maybank (10:12)
- **Midday–afternoon 11:00–15:30:** Yuanta (two windows), KAF (14:01), Mirae
- **Post-close evening 16:00–21:45:** BRI snapshot, MOST Afternoon Highlight, Sinarmas (19:00), BNI (21:25), Phillip (17:10)

Suggested cron runs (UTC; WIB = UTC+7): **09:45 WIB = `0 2 * * 1-5`** (morning
cluster), **16:15 WIB = `0 9 * * 1-5`** (post-close), **21:45 WIB = `0 14 * * 1-5`**
(optional late YT catch-up so BNI/Sinarmas land same-day).
