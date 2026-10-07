"""Backfill: buat inference key untuk akun lama yang belum punya, lalu uji chat."""
import sys, json
sys.path.insert(0, "/root/bugbunny-suite")
from src import bugbunny as bb

accs = bb.parse_accounts()
have = {k["email"] for k in bb.parse_inference_keys()}
for a in accs:
    if a["email"] in have:
        continue
    st, b = bb.create_inference_key(a["access_token"], name="bugbunny-suite")
    if st in (200, 201):
        kj = json.loads(b); key = kj.get("api_key")
        if key:
            bb.INF_KEYS.open("a").write(f"{a['email']}:{key}:{bb.INFERENCE_BASE}\n")
            t = bb.test_chat(key)
            print(f"{a['email']} -> key {kj.get('key_prefix')}... chat_ok={t.get('ok')} {t.get('error','')}")
    else:
        print(f"{a['email']} -> FAIL {st} {b[:100]}")
print("total inference keys:", len(bb.parse_inference_keys()))
