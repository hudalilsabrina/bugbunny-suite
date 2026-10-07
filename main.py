#!/usr/bin/env python3
"""BugBunny.ai Suite - CLI: harvest akun (magic link), batch, test, report, sync, pilot.

Command:
  harvest [domain]     Buat 1 akun (magic link -> verify -> $5 inference credit -> API key)
  batch <n>            Buat N akun berurutan
  test                 Test semua inference key (chat nyata)
  report               Ringkasan akun + inference keys
  sync                 Inject inference keys ke 9router (node openai-compatible)
  pilot                Kirim aplikasi free pilot (butuh data perusahaan)
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from rich.console import Console
from rich.table import Table
from rich import box

from src import bugbunny as bb

C = Console()


def cmd_harvest(domain):
    r = bb.harvest_bugbunny(domain=domain)
    red = {k: (v if not isinstance(v, str) or len(v) < 24 else v[:12] + "..." + v[-4:])
           for k, v in r.items()}
    C.print(json.dumps(red, indent=1, default=str))
    C.print("[green]AKUN + $5 inference credit[/]" if r.get("ok") else f"[yellow]GAGAL: {r.get('error')}[/]")


def cmd_batch(n, domain):
    ok = 0
    for i in range(1, n + 1):
        C.print(f"[cyan]=== Akun {i}/{n} ===[/]")
        r = bb.harvest_bugbunny(domain=domain)
        if r.get("ok"):
            ok += 1
            C.print(f"[green]  OK {r.get('email')} (inference=${r.get('inference_available_usd')}, chat={r.get('chat_ok')})[/]")
        else:
            C.print(f"[yellow]  gagal: {r.get('error')}[/]")
    C.print(f"\n[bold]Batch: {ok}/{n} sukses[/]")


def cmd_test():
    keys = bb.parse_inference_keys()
    if not keys:
        C.print("[yellow]Belum ada inference key. Jalankan: ./run.sh harvest[/]")
        return
    t = Table(box=box.ROUNDED, title=f"BugBunny inference keys ({len(keys)})")
    t.add_column("Email", style="cyan")
    t.add_column("OK", style="green")
    t.add_column("Model", style="white")
    t.add_column("Error", style="red", overflow="fold")
    ok = 0
    for a in keys:
        r = bb.test_chat(a["key"])
        ok += bool(r.get("ok"))
        t.add_row(a["email"][:28], "yes" if r.get("ok") else "no",
                  r.get("model") or "-", (r.get("error") or "")[:40])
    C.print(t)
    C.print(f"[bold]{ok}/{len(keys)} valid[/]")


def cmd_report():
    accs = bb.parse_accounts()
    keys = bb.parse_inference_keys()
    C.print(f"[bold]Akun BugBunny.ai: {len(accs)}  |  inference keys: {len(keys)}[/]")
    t = Table(box=box.ROUNDED, title="BugBunny.ai accounts")
    t.add_column("Email", style="cyan")
    t.add_column("Tier", style="white")
    t.add_column("Inference key", style="green")
    kmap = {k["email"]: k["key"] for k in keys}
    for a in accs:
        k = kmap.get(a["email"])
        t.add_row(a["email"], a["tier"], (k[:16] + "...") if k else "-")
    C.print(t)


def cmd_sync():
    from src import router9
    keys = bb.parse_inference_keys()
    if not keys:
        C.print("[yellow]Tidak ada inference key untuk disync[/]")
        return
    r = router9.ingest_gateway("bugbunny-inference", "bugbunny", bb.INFERENCE_BASE, keys, None)
    C.print(json.dumps(r))


def cmd_pilot(args):
    r = bb.demo_request(args.first, args.last, args.email, args.company,
                        title=args.title, message=args.message)
    C.print(json.dumps(r, indent=1)[:400])


def main():
    ap = argparse.ArgumentParser(prog="bugbunny", description="BugBunny.ai Suite")
    sub = ap.add_subparsers(dest="cmd")
    h = sub.add_parser("harvest"); h.add_argument("domain", nargs="?", default="mcgg.me")
    b = sub.add_parser("batch"); b.add_argument("n", type=int); b.add_argument("--domain", default="mcgg.me")
    sub.add_parser("test")
    sub.add_parser("report")
    sub.add_parser("sync")
    p = sub.add_parser("pilot")
    p.add_argument("--first", required=True); p.add_argument("--last", required=True)
    p.add_argument("--email", required=True); p.add_argument("--company", required=True)
    p.add_argument("--title", default=""); p.add_argument("--message", default="")
    a = ap.parse_args()
    if a.cmd == "harvest":
        cmd_harvest(a.domain)
    elif a.cmd == "batch":
        cmd_batch(a.n, a.domain)
    elif a.cmd == "test":
        cmd_test()
    elif a.cmd == "report":
        cmd_report()
    elif a.cmd == "sync":
        cmd_sync()
    elif a.cmd == "pilot":
        cmd_pilot(a)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
