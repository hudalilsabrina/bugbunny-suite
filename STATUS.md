# BugBunny.ai Suite — Status

## ✅ SELESAI & TERVERIFIKASI

| Item | Hasil |
|---|---|
| Recon (tanpa proxy) | `bugbunny-recon/FINDINGS.md` |
| Auth | **magic link** (email) / Google OAuth — **tanpa captcha** |
| Harvester | `./run.sh harvest` → akun + **$5 inference credit** + API key `bbi_...` |
| Batch | `./run.sh batch <n>` (backoff rate-limit) |
| Test chat | `./run.sh test` → **valid** (glm-5.3-flash) |
| Sync 9router | `./run.sh sync` → **4/4 valid** |
| Akun | 4 akun × $5 = **$20 kredit inference** |

## 💵 KREDIT $5 (ini yang dimaksud "register dapat $5")

Ternyata $5 itu **nyata & bisa dipakai** — tapi khusus **Inference** (menu
"Inference" BETA di dashboard), bukan Audit Console:

```
GET  /inference/balance ->
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
