#!/usr/bin/env python3
"""HealthPlanet API → personal/data/health.json 同期スクリプト.

事前準備:
  1. https://www.healthplanet.jp/apis_account.do でアプリ登録
     - サービス種別: 一般ユーザ向けサービス
     - Redirect URL: https://www.healthplanet.jp/success.html
     - スコープ: innerscan
  2. /Users/major/Documents/00_Shota-all/n_secret/healthplanet.json に下記を保存:
        {
          "client_id": "...",
          "client_secret": "...",
          "refresh_token": "..."
        }
     初回 refresh_token は --auth コマンドで取得する.

使い方:
  # 初回認可（refresh_token を取得して n_secret に保存）:
  python3 healthplanet_sync.py --auth

  # 通常同期（過去90日分を取得し health.json をマージ更新）:
  python3 healthplanet_sync.py

  # 全期間取得:
  python3 healthplanet_sync.py --days 3650
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "health.json"
SECRET_FILE = Path("/Users/major/Documents/00_Shota-all/n_secret/healthplanet.json")

REDIRECT_URI = "https://www.healthplanet.jp/success.html"
SCOPE = "innerscan"
AUTH_URL = "https://www.healthplanet.jp/oauth/auth"
TOKEN_URL = "https://www.healthplanet.jp/oauth/token"
INNERSCAN_URL = "https://www.healthplanet.jp/status/innerscan.json"

# HealthPlanet tag → health.json key (全身)
# https://www.healthplanet.jp/apis/api.do
TAG_MAP = {
    "6021": "weight_kg",
    "6022": "body_fat_pct",
    "6023": "muscle_mass_kg",
    "6024": "muscle_score",
    "6025": "visceral_fat_level",     # 内臓脂肪レベル2 (0.5刻み)
    "6026": "visceral_fat_level_int", # 内臓脂肪レベル (整数)
    "6027": "basal_metabolic_rate",
    "6028": "metabolic_age",
    "6029": "estimated_bone_mass_kg",
}

# 部位別タグ: (タグID, 部位キー, フィールド名)
# 部位コード: 左腕=01, 右腕=02, 左脚=03, 右脚=04, 体幹=05
# 体脂肪率=6101-6105 / 筋肉量=6121-6125
PART_TAG_MAP = {
    # body fat per part
    "6101": ("left_arm",  "body_fat_pct"),
    "6102": ("right_arm", "body_fat_pct"),
    "6103": ("left_leg",  "body_fat_pct"),
    "6104": ("right_leg", "body_fat_pct"),
    "6105": ("trunk",     "body_fat_pct"),
    # muscle mass per part
    "6121": ("left_arm",  "muscle_mass_kg"),
    "6122": ("right_arm", "muscle_mass_kg"),
    "6123": ("left_leg",  "muscle_mass_kg"),
    "6124": ("right_leg", "muscle_mass_kg"),
    "6125": ("trunk",     "muscle_mass_kg"),
}

ALL_TAGS = ",".join(list(TAG_MAP.keys()) + list(PART_TAG_MAP.keys()))


def http_post(url: str, data: dict) -> dict:
    body = urllib.parse.urlencode(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def http_get(url: str, params: dict) -> dict:
    qs = urllib.parse.urlencode(params)
    req = urllib.request.Request(f"{url}?{qs}", method="GET")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def load_secret() -> dict:
    if not SECRET_FILE.exists():
        sys.exit(
            f"secret file not found: {SECRET_FILE}\n"
            "create it with {client_id, client_secret, refresh_token}"
        )
    return json.loads(SECRET_FILE.read_text())


def save_secret(secret: dict) -> None:
    SECRET_FILE.parent.mkdir(parents=True, exist_ok=True)
    SECRET_FILE.write_text(json.dumps(secret, indent=2, ensure_ascii=False))
    SECRET_FILE.chmod(0o600)


def cmd_auth() -> None:
    """初回認可フロー: ブラウザを開いてcodeを貼り付けてもらう。"""
    secret = {}
    if SECRET_FILE.exists():
        secret = json.loads(SECRET_FILE.read_text())

    client_id = secret.get("client_id") or input("client_id: ").strip()
    client_secret = secret.get("client_secret") or input("client_secret: ").strip()

    auth_params = {
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPE,
        "response_type": "code",
    }
    url = f"{AUTH_URL}?{urllib.parse.urlencode(auth_params)}"
    print(f"\n以下のURLをブラウザで開いて認可してください:\n{url}\n")
    try:
        webbrowser.open(url)
    except Exception:
        pass
    code = input("リダイレクト後の URL に含まれる code= の値を貼り付け: ").strip()

    token = http_post(TOKEN_URL, {
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": REDIRECT_URI,
        "code": code,
        "grant_type": "authorization_code",
    })
    if "refresh_token" not in token:
        sys.exit(f"token exchange failed: {token}")

    secret.update({
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": token["refresh_token"],
    })
    save_secret(secret)
    print(f"\nrefresh_token を保存しました → {SECRET_FILE}")


def get_access_token(secret: dict) -> str:
    token = http_post(TOKEN_URL, {
        "client_id": secret["client_id"],
        "client_secret": secret["client_secret"],
        "redirect_uri": REDIRECT_URI,
        "refresh_token": secret["refresh_token"],
        "grant_type": "refresh_token",
    })
    if "access_token" not in token:
        sys.exit(f"access_token refresh failed: {token}")
    # refresh_token がローテーションされる場合は更新
    if "refresh_token" in token and token["refresh_token"] != secret.get("refresh_token"):
        secret["refresh_token"] = token["refresh_token"]
        save_secret(secret)
    return token["access_token"]


def fetch_innerscan(access_token: str, from_dt: dt.datetime, to_dt: dt.datetime) -> list[dict]:
    res = http_get(INNERSCAN_URL, {
        "access_token": access_token,
        "date": "1",  # measurement date (0=registered)
        "from": from_dt.strftime("%Y%m%d%H%M%S"),
        "to": to_dt.strftime("%Y%m%d%H%M%S"),
        "tag": ALL_TAGS,
    })
    return res.get("data", [])


def aggregate_by_date(rows: list[dict], height_cm: float | None = None) -> dict[str, dict]:
    """同じ日に複数測定がある場合は最後の値を採用。BMIは weight + height_cm から計算。"""
    by_date: dict[str, dict] = {}
    int_keys = {"muscle_score", "metabolic_age", "basal_metabolic_rate", "visceral_fat_level_int"}

    for r in sorted(rows, key=lambda x: x["date"]):
        d = r["date"]
        date_iso = f"{d[0:4]}-{d[4:6]}-{d[6:8]}"
        tag = r.get("tag")
        try:
            val = float(r["keydata"])
        except (TypeError, ValueError):
            continue
        rec = by_date.setdefault(date_iso, {"date": date_iso})

        if tag in TAG_MAP:
            key = TAG_MAP[tag]
            if key in int_keys:
                val = int(val)
            rec[key] = val
        elif tag in PART_TAG_MAP:
            part, field = PART_TAG_MAP[tag]
            parts = rec.setdefault("parts", {})
            p = parts.setdefault(part, {})
            p[field] = val

    # BMI を計算
    if height_cm:
        m = height_cm / 100.0
        for rec in by_date.values():
            w = rec.get("weight_kg")
            if w:
                rec["bmi"] = round(w / (m * m), 1)

    return by_date


def merge_measurements(existing: list[dict], incoming: dict[str, dict]) -> list[dict]:
    by_date = {m["date"]: dict(m) for m in existing}
    for date_iso, rec in incoming.items():
        merged = by_date.get(date_iso, {"date": date_iso})
        # parts は dict なので深くマージ
        if "parts" in rec:
            existing_parts = merged.get("parts", {})
            for part, fields in rec["parts"].items():
                existing_parts.setdefault(part, {}).update(fields)
            merged["parts"] = existing_parts
            rec_no_parts = {k: v for k, v in rec.items() if k != "parts"}
            merged.update(rec_no_parts)
        else:
            merged.update(rec)
        by_date[date_iso] = merged
    return sorted(by_date.values(), key=lambda x: x["date"])


def cmd_sync(days: int) -> None:
    secret = load_secret()
    if "refresh_token" not in secret:
        sys.exit("refresh_token not set. run --auth first.")

    access_token = get_access_token(secret)
    to_dt = dt.datetime.now()
    from_dt = to_dt - dt.timedelta(days=days)
    rows = fetch_innerscan(access_token, from_dt, to_dt)
    print(f"fetched {len(rows)} rows from HealthPlanet")

    payload = json.loads(DATA_FILE.read_text())
    height_cm = (payload.get("user") or {}).get("height_cm")
    incoming = aggregate_by_date(rows, height_cm=height_cm)
    if not incoming:
        print("no new measurements")
        return

    payload["measurements"] = merge_measurements(payload.get("measurements", []), incoming)
    payload["last_synced"] = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    DATA_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    print(f"updated {DATA_FILE} ({len(payload['measurements'])} measurements total)")


def main() -> None:
    p = argparse.ArgumentParser(description="HealthPlanet API sync")
    p.add_argument("--auth", action="store_true", help="initial OAuth flow")
    p.add_argument("--days", type=int, default=90, help="days to fetch (default: 90)")
    args = p.parse_args()

    if args.auth:
        cmd_auth()
    else:
        cmd_sync(args.days)


if __name__ == "__main__":
    main()
