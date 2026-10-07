"""BugBunny.ai — client API + harvester akun (magic link).

BugBunny.ai (Next.js/Vercel) memakai FastAPI di https://api.bugbunny.ai/api/v1.
Auth: **magic link via email** (tanpa captcha/Turnstile) atau Google OAuth.
Akun dibuat otomatis saat verify magic link.

Alur:
  1. POST /auth/send-magic-link {email}     -> email berisi /login?token=<JWT>
  2. baca token dari temp-mail
  3. POST /auth/verify-magic-link {token}  -> {access_token, user}
  4. GET  /users/me, /billing/usage-balance -> status akun/kredit

Catatan: akun free TIDAK dapat kredit otomatis (can_run_llm:false).
Kredit "gratis" hanya via pilot application (human-reviewed) / referral 30%.
"""
import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional

from rich.console import Console

from .config import DATA_DIR
from .inboxstore import save as save_inbox
from .tempmail import TempikClient

C = Console()

API = "https://api.bugbunny.ai/api/v1"
HOST = "https://bugbunny.ai"
ACCOUNTS = Path(DATA_DIR).parent / "accounts.txt"
INF_KEYS = Path(DATA_DIR).parent / "inference_keys.txt"

_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")


def _headers(token: str = None) -> Dict[str, str]:
    h = {"Content-Type": "application/json", "User-Agent": _UA,
         "Origin": HOST, "Referer": f"{HOST}/login"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def _req(method: str, path: str, body=None, token: str = None, timeout: int = 30):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(API + path, data=data, method=method, headers=_headers(token))
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            return resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()
    except Exception as e:
        return None, str(e)[:200]


# --------------------------- API ---------------------------

def send_magic_link(email: str):
    return _req("POST", "/auth/send-magic-link", {"email": email})


def verify_magic_link(token: str):
    return _req("POST", "/auth/verify-magic-link", {"token": token})


def get_me(access_token: str):
    return _req("GET", "/users/me", token=access_token)


def usage_balance(access_token: str):
    return _req("GET", "/billing/usage-balance", token=access_token)


def referrals_me(access_token: str):
    return _req("GET", "/referrals/me", token=access_token)


def demo_request(first_name, last_name, email, company, title="", message="", consent=True):
    return _req("POST", "/demo-requests", {
        "first_name": first_name, "last_name": last_name, "email": email,
        "company": company, "title": title, "message": message, "consent": consent,
    })


# --------------------------- Inference ($5 free credit) ---------------------------

INFERENCE_BASE = "https://inference.bugbunny.ai/v1"
INFERENCE_MODELS = ["glm-5.3-flash", "mimo-v2.6-flash"]


def inference_balance(access_token: str):
    return _req("GET", "/inference/balance", token=access_token)


def inference_keys(access_token: str):
    return _req("GET", "/inference/keys", token=access_token)


def create_inference_key(access_token: str, name: str = "bugbunny-suite"):
    """Buat API key inference. Key penuh (bbi_...) hanya tampil sekali."""
    return _req("POST", "/inference/keys", {"name": name}, token=access_token)


def test_chat(api_key: str, model: str = "glm-5.3-flash", timeout: int = 90):
    """Uji chat nyata via inference.bugbunny.ai (OpenAI-compatible)."""
    out = {"ok": False, "model": model}
    try:
        body = json.dumps({"model": model,
                           "messages": [{"role": "user", "content": "Reply exactly: PONG"}],
                           "max_tokens": 24}).encode()
        r = urllib.request.Request(INFERENCE_BASE + "/chat/completions", data=body,
                                   headers={"Authorization": f"Bearer {api_key}",
                                            "Content-Type": "application/json", "User-Agent": _UA})
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            d = json.loads(resp.read().decode())
        out["ok"] = True
        ch = (d.get("choices") or [{}])[0].get("message", {})
        out["reply"] = (ch.get("content") or ch.get("reasoning_content") or "")[:60]
    except urllib.error.HTTPError as e:
        out["error"] = f"HTTP {e.code}: {e.read().decode()[:150]}"
    except Exception as e:
        out["error"] = str(e)[:150]
    return out


# --------------------------- helpers ---------------------------

def _read_magic_token(tc: TempikClient, email: str, timeout: int = 120) -> Optional[str]:
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            for m in (tc.get_messages(email) or []):
                plain = (m.get("body", "") or "") + " " + (m.get("subject", "") or "")
                mm = re.search(r"login\?token=([A-Za-z0-9._\-]+)", plain)
                if mm:
                    return mm.group(1)
        except Exception:
            pass
        time.sleep(4)
    return None


# --------------------------- harvester ---------------------------

def harvest_bugbunny(domain: str = "mcgg.me", timeout_mail: int = 120) -> Dict[str, Any]:
    """Buat 1 akun BugBunny.ai via magic link. Return dict hasil."""
    out: Dict[str, Any] = {"site": "bugbunny", "ok": False}
    tc = TempikClient()
    email = tc.create_inbox(domain=domain)
    save_inbox("bugbunny", email, tc.session_id)
    out["email"] = email
    C.print(f"[cyan]bugbunny.ai[/] inbox: {email}")

    st, body = send_magic_link(email)
    # rate-limit per IP: retry dengan backoff
    for attempt in range(4):
        if st != 429:
            break
        wait = 20 * (attempt + 1)
        C.print(f"[yellow]  429 rate-limit, tunggu {wait}s (percobaan {attempt+1})[/]")
        time.sleep(wait)
        st, body = send_magic_link(email)
    if st != 200:
        out["error"] = f"send-magic-link {st}: {body[:120]}"
        return out

    tok = _read_magic_token(tc, email, timeout_mail)
    out["magic_token_len"] = len(tok or "")
    if not tok:
        out["error"] = "magic link tidak diterima"
        return out

    st, body = verify_magic_link(tok)
    if st != 200:
        out["error"] = f"verify {st}: {body[:150]}"
        return out
    try:
        d = json.loads(body)
    except Exception:
        out["error"] = "respons verify bukan JSON"
        return out
    access = d.get("access_token")
    user = d.get("user") or {}
    out["access_token"] = access
    out["user_id"] = user.get("id")
    out["tier"] = user.get("subscription_tier")
    out["role"] = user.get("team_role")

    # ambil status kredit + buat API key inference ($5 free trial credit)
    try:
        st, ub = usage_balance(access)
        ubj = json.loads(ub)
        out["available_usd"] = ubj.get("available_usd")
        out["buffer_usd"] = ubj.get("buffer_usd")
        out["can_run_llm"] = ubj.get("can_run_llm")
    except Exception:
        pass
    try:
        st, ib = inference_balance(access)
        ibj = json.loads(ib)
        out["inference_available_usd"] = ibj.get("available_usd")
        out["inference_trial_usd"] = ibj.get("trial_remaining_usd")
        out["inference_enabled"] = ibj.get("inference_account_enabled")
    except Exception:
        pass
    try:
        st, kb = create_inference_key(access)
        if st in (200, 201):
            kj = json.loads(kb)
            ikey = kj.get("api_key")
            out["inference_key"] = ikey
            out["inference_key_prefix"] = kj.get("key_prefix")
            if ikey:
                INF_KEYS.open("a").write(f"{email}:{ikey}:{INFERENCE_BASE}\n")
                # verifikasi chat nyata
                t = test_chat(ikey)
                out["chat_ok"] = bool(t.get("ok"))
                if not t.get("ok"):
                    out["chat_error"] = t.get("error")
        else:
            out["inference_key_error"] = f"{st}: {kb[:100]}"
    except Exception as e:
        out["inference_key_error"] = str(e)[:120]

    out["ok"] = bool(access)
    if out["ok"]:
        _append_account(email, access, out.get("tier", "free"))
        C.print(f"  [green]akun OK[/] tier={out.get('tier')} "
                f"inference=${out.get('inference_available_usd')} chat_ok={out.get('chat_ok')}")
    return out


def _append_account(email: str, access_token: str, tier: str):
    ACCOUNTS.open("a").write(f"{email}:{tier}:{access_token}\n")


# --------------------------- account store ---------------------------

def parse_accounts(path: Path = None) -> list:
    """Parse accounts.txt: email:tier:access_token (split(':',2))."""
    path = path or ACCOUNTS
    out = []
    if not path.exists():
        return out
    for ln in path.read_text().strip().splitlines():
        ln = ln.strip()
        if not ln or ln.count(":") < 2:
            continue
        try:
            email, tier, token = ln.split(":", 2)
            out.append({"email": email, "tier": tier, "access_token": token})
        except ValueError:
            continue
    return out


def parse_inference_keys(path: Path = None) -> list:
    """Parse inference_keys.txt: email:bbi_key:base_url (split(':',2))."""
    path = path or INF_KEYS
    out = []
    if not path.exists():
        return out
    for ln in path.read_text().strip().splitlines():
        ln = ln.strip()
        if not ln or ln.count(":") < 2:
            continue
        try:
            email, key, base = ln.split(":", 2)
            out.append({"email": email, "key": key, "base_url": base})
        except ValueError:
            continue
    return out
