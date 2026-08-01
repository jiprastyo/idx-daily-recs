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

## Measured publish times per source (2026-08-01 live probe)

Methods: YouTube RSS `<published>` timestamps (exact, last 15 uploads/channel);
`article:published_time` meta; PDF `Last-Modified` headers (GMT → WIB = +7h);
homepage timestamps. All times WIB. Small samples — typical windows, not guarantees.

| Sekuritas (key) | Source type | Publish time (WIB) | Detail / evidence |
|---|---|---|---|
| Minna Padi (minnapadi) | JSON API → PDF | **04:45–07:45** | Last-Modified, 2 days ("Morning Dew") |
| Samuel Sekuritas (samuel) | PDF / article | **~07:46** | article:published_time, 1 day (Morning Brief); macro monitor 18:51 evening before |
| Shinhan (shinhan) | JSON API → PDF | **~08:42** | Last-Modified, 1 day (Daily Bond Market Update) |
| Mega Capital (mega) | PDF | **~08:30–08:45** | Last-Modified, 2 days (Equity Daily Report — morning, not evening) |
| RHB (yt_rhb) | YouTube RSS | **09:08** (08:57–09:24) | n=15, Morning Stock Pick |
| Maybank (yt_maybank) | YouTube RSS | **~10:12** (09:02–17:00) | n=15 |
| Mirae (yt_mirae) | YouTube RSS | ~12:22 (06:09–20:15) | n=15, mixed content |
| KAF (yt_kaf) | YouTube RSS | ~14:01 (09:45–15:17) | n=7 |
| Yuanta (yuanta) | HTML | **11:00–11:30 + 14:50–15:30** | homepage timestamps, 6 samples |
| Phillip (yt_phillip) | YouTube RSS | ~17:10 (15:21–23:23) | n=4 |
| Sinarmas (yt_sinarmas) | YouTube RSS | ~19:00 (08:53–19:00) | n=15 |
| BNI (yt_bni) | YouTube RSS | **~21:25** (09:29–21:44) | n=15, evening uploads |
| NH Korindo (nh) | HTML article | morning (unverified) | no meta found; report named for trading day |
| Ajaib (ajaib) | HTML article | morning (unverified) | no datePublished meta; article day-of |
| KB Valbury (kbvalbury) | HTML | morning (inferred) | "Trading Ideas" for the trading day |
| Kiwoom (kiwoom) | PDF / HTML | morning (inferred) | "Daily Stock Picks" |
| Binaartha (binaartha) | HTML | morning (inferred) | daily technical research |
| Phintraco (phintraco) | HTML | morning (inferred) | daily riset posts |
| Panin (panin) | PDF (JS site) | unmeasurable | riset page JS-rendered |
| Artha (artha) | PDF | unmeasurable | only install manuals hosted |
| OCBC (ocbc) | HTML | mid-day (inferred) | "Mid Day Market Update" |
| UOB Kay Hian (uob) | HTML | morning (inferred) | daily review w/ stock pick |
| CGS (cgs) | HTML | morning/afternoon (inferred) | riset articles |
| Sucor (sucor) | HTML | irregular | company updates |
| Surya Fajar (sf) | HTML | irregular | riset posts |
| Evergreen (evergreen) | HTML | irregular | riset posts |
| Reliance (reliance) | PDF | morning (inferred) | "Morning Coffee" |
| Mandiri MOST (most) | PDF (403) | Morning Notes ~08:00 · Afternoon Highlight ~16:00 (inferred) | 403 blocks direct probing |
| Verdhana (verdhana) | HTML | midday (inferred) | company reports (BUY/TP) |
| Waterfront (waterfront) | PDF (SPA) | unmeasurable | React app, no server-rendered data |
| MNC (mnc) | HTML (JS) | unmeasurable | Next.js, no HTTP API |
| Victoria (victoria) | PDF | unmeasurable | flaky site, PDFs not linked on homepage |
| BRI Danareksa (—) | HTML (brights.id) | evening (inferred) | "Equity Snapshot", post-close |
| BCA (—) | portal (login) | unknown | research portal behind login |
| Indo Premier (—) | app (IPOT) | unknown | app-only |
| Trimegah (—) | app (Trima+ Picks) | unknown | app-only |
| X sources (x) | X social | n/a | requires local `xurl` + credentials |

### Cluster summary → scheduling

- **Pre-market cluster 04:45–08:45 WIB:** Minna Padi, Samuel, Shinhan, Mega
- **Mid-morning 09:00–10:30:** RHB (09:08), Maybank (10:12)
- **Midday–afternoon 11:00–15:30:** Yuanta (two windows), KAF (14:01), Mirae
- **Post-close evening 16:00–21:45:** BRI snapshot, MOST Afternoon Highlight, Sinarmas (19:00), BNI (21:25), Phillip (17:10)

Suggested cron runs (UTC; WIB = UTC+7): **09:45 WIB = `0 2 * * 1-5`** (morning
cluster), **16:15 WIB = `0 9 * * 1-5`** (post-close), **21:45 WIB = `0 14 * * 1-5`**
(optional late YT catch-up so BNI/Sinarmas land same-day).
