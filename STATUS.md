# BugBunny.ai Suite — Status

## ⚠️ UPDATE PENTING (07 Okt 2026): promo $5 sudah DIMATIKAN

BugBunny **menghentikan** free trial credit $5. Bukti dari 44 akun kita:

| Waktu daftar (UTC) | Akun | Hasil |
|---|---|---|
| 07 Okt 01:25–02:00 | 23 | ✅ **$5** (`inference_trial_credit`) |
| 07 Okt 14:38–15:01 | 21 | ❌ **$0** (`credit_buckets: []`) |

- Domain sama (`mcgg.me`) → **bukan** masalah domain
- Re-check berulang → tetap $0 (bukan delay)
- Promo dimatikan antara 02:00–14:38 (07 Okt 2026)
- **Akun baru tetap dapat API key `bbi_...`, tapi TANPA kredit**

### 💰 Aset yang masih AMAN
```
23 akun × $5 = $115   (expires_at 9999-12-31 → tidak expire)
21 akun × $0 = $0     (dibuat setelah promo mati)
```
Semua 44 akun tetap punya API key aktif.

## ✅ SELESAI & TERVERIFIKASI

| Item | Hasil |
|---|---|
| Recon (tanpa proxy) | `bugbunny-recon/FINDINGS.md` |
| Auth | **magic link** (email) / Google OAuth — **tanpa captcha** |
| Harvester | `./run.sh harvest` → akun + API key (kredit tergantung promo) |
| Batch | `./run.sh batch <n>` (backoff rate-limit) |
| Test chat | `./run.sh test` → valid saat server inference up (kadang 502) |
| Sync 9router | `./run.sh sync` → ✅ |

## 🔧 Catatan teknis (penting)

1. **Endpoint balance** — pakai API utama, BUKAN subdomain inference:
   - ✅ `https://api.bugbunny.ai/api/v1/inference/balance`
   - ❌ `https://inference.bugbunny.ai/v1/balance` (404)
2. **Header `User-Agent` WAJIB** — tanpa UA → **403 Forbidden**
   (urllib default diblok; curl jalan karena punya UA).
3. **`buffer_usd: 5.0` ≠ saldo** — di `/billing/usage-balance` (Audit Console):
   `{"available_usd":0.0,"buffer_usd":5.0,"can_run_llm":false}`.
   `buffer_usd` = plafon/buffer, **bukan kredit**. Saldo nyata = `available_usd`
   di `/inference/balance`.
4. **Chat kadang 502** (Cloudflare) — server inference kadang down (transient).
   `/v1/models` tetap 200.

## 💵 KREDIT $5 (yang dimaksud "register dapat $5")

$5 itu **nyata & bisa dipakai** — khusus **Inference** (menu "Inference" BETA di
dashboard), bukan Audit Console. Berlaku untuk akun yang daftar **sebelum**
promo dimatikan:

```
GET  api.bugbunny.ai/api/v1/inference/balance ->
{"available_usd":5.0,"trial_remaining_usd":5.0,"inference_account_enabled":true,
 "credit_buckets":[{"type":"inference_trial_credit","amount_usd":5.0,
                    "remaining_usd":5.0,"expires_at":"9999-12-31T00:00:00"}]}
```
UI: *"$5.00 in free trial credit remaining · Inference only"*

### Endpoint OpenAI-compatible
| Item | Nilai |
|---|---|
| Base URL | `https://inference.bugbunny.ai/v1` |
| Auth | `Authorization: Bearer bbi_...` |
| Buat key | `POST /api/v1/inference/keys {name}` → `{api_key:"bbi_..."}` (tampil sekali) |
| List key | `GET /api/v1/inference/keys` |
| Balance | `GET /api/v1/inference/balance` |
| Models | `glm-5.3-flash`, `mimo-v2.6-flash` |
| Limits | 120 req/min, 500k token/min, 15 concurrent |

### Contoh pakai
```bash
curl https://inference.bugbunny.ai/v1/chat/completions \
  -H "Authorization: Bearer bbi_..." -H "Content-Type: application/json" \
  -d '{"model":"glm-5.3-flash","messages":[{"role":"user","content":"hi"}]}'
```

## Catatan: Audit Console (beda dari Inference)
- `POST /api/v1/audits` → **402 "Insufficient domains available"** (butuh plan).
- Dashboard Audit: **"No Plan — Subscribe to start scanning"**.
- Jadi: **$5 = inference only**; audit/pentest tetap perlu subscribe.
- `buffer_usd: 5.0` di `/billing/usage-balance` (audit) = buffer, bukan saldo.

## Rate-limit
`send-magic-link` = 429 per IP → harvester retry backoff 20/40/60/80s.

## File
```
main.py                CLI: harvest/batch/test/report/sync/pilot
src/bugbunny.py        client API + harvester + inference ($5)
src/tempmail.py        klien temp-mail (tempik)
src/router9.py         integrasi 9router
accounts.txt           email:tier:access_token
inference_keys.txt     email:bbi_key:base_url
backfill.py            buat inference key utk akun lama
```
