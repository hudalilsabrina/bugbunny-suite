# BugBunny.ai Suite

Harvester akun + kredit **$5 inference** dari **[bugbunny.ai](https://bugbunny.ai)**
via **magic link** — tanpa captcha/Turnstile.

Alur: kirim magic link → baca token dari temp-mail → verify → akun dibuat
otomatis → **$5 kredit inference** → buat API key `bbi_...` → test chat → sync 9router.

## 💵 Yang didapat per akun
- Akun BugBunny.ai (role `owner`, tier `free`)
- **$5 free trial credit (Inference only)** — `type: inference_trial_credit`
- API key OpenAI-compatible `bbi_...`
- Terverifikasi chat nyata (`glm-5.3-flash`)

## Endpoint inference (OpenAI-compatible)
| Item | Nilai |
|---|---|
| Base URL | `https://inference.bugbunny.ai/v1` |
| Auth | `Authorization: Bearer bbi_...` |
| Models | `glm-5.3-flash`, `mimo-v2.6-flash` |
| Buat key | `POST /api/v1/inference/keys {name}` |
| Balance | `GET /api/v1/inference/balance` |

## Command

```bash
./run.sh harvest [domain]   # buat 1 akun + $5 credit + inference key + test chat
./run.sh batch <n>          # buat N akun (backoff rate-limit)
./run.sh test               # test semua inference key (chat nyata)
./run.sh report             # ringkasan akun + key
./run.sh sync               # inject inference keys ke 9router
./run.sh pilot --first .. --last .. --email .. --company ..   # aplikasi free pilot
```

## Catatan
- **Inference** ($5) ≠ **Audit Console** (butuh plan; `POST /audits` → 402).
- Rate-limit `send-magic-link` (429/IP) → harvester auto-retry backoff.
- Domain temp-mail yang dipakai: `mcgg.me` (andal).

## File
```
main.py                CLI
src/bugbunny.py        client API + harvester + inference
src/tempmail.py        klien temp-mail (tempik)
src/router9.py         integrasi 9router
accounts.txt           email:tier:access_token
inference_keys.txt     email:bbi_key:base_url
backfill.py            buat inference key utk akun lama
```
