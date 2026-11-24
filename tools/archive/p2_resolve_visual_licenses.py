#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P2-3: Fetch exact Wikimedia Commons license & attribution metadata for all external visual assets."""
from __future__ import annotations

import csv
import html
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def clean_html(val: str) -> str:
    if not val:
        return ""
    # Remove hidden spans like <span style="display: none;">Unknown author</span>
    val = re.sub(r'<span[^>]*display:\s*none[^>]*>.*?</span>', '', val, flags=re.I | re.S)
    val = re.sub(r'<[^>]+>', ' ', val)
    val = html.unescape(val)
    val = re.sub(r'\s+', ' ', val).strip()
    # Deduplicate trivial repeated words like "Unknown author Unknown author"
    if val.lower() in ("unknown author", "unknown", "anonymous"):
        return "Unknown author"
    return val[:120]


def fetch_commons_meta(titles: list[str]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for i in range(0, len(titles), 15):
        batch = titles[i:i + 15]
        params = urllib.parse.urlencode({
            "action": "query",
            "titles": "|".join(batch),
            "redirects": "1",
            "prop": "imageinfo",
            "iiprop": "extmetadata|user",
            "format": "json",
        })
        url = f"https://commons.wikimedia.org/w/api.php?{params}"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "RedMapProject/1.0 (https://github.com/CochraneK/red-map)"},
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        q = data.get("query", {})
        norm_map = {n["from"]: n["to"] for n in q.get("normalized", [])}
        redir_map = {r["from"]: r["to"] for r in q.get("redirects", [])}
        pages_by_title = {}
        for p in q.get("pages", {}).values():
            pages_by_title[p.get("title", "")] = p

        for orig in batch:
            t = norm_map.get(orig, orig)
            t = redir_map.get(t, t)
            p = pages_by_title.get(t, {})
            if p.get("missing") is not None:
                out[orig] = {"missing": True, "resolved_title": t}
                continue
            ii = (p.get("imageinfo") or [{}])[0]
            em = ii.get("extmetadata") or {}
            lic = clean_html(em.get("LicenseShortName", {}).get("value", ""))
            usage = clean_html(em.get("UsageTerms", {}).get("value", ""))
            artist = clean_html(em.get("Artist", {}).get("value", ""))
            credit = clean_html(em.get("Credit", {}).get("value", ""))
            uploader = clean_html(ii.get("user", ""))
            out[orig] = {
                "missing": False,
                "resolved_title": t,
                "license": lic or usage,
                "usage": usage,
                "artist": artist,
                "credit": credit,
                "uploader": uploader,
            }
    return out


def main() -> int:
    va_path = ROOT / "data_edit/visual_assets.csv"
    with va_path.open("r", encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f)
        fields = list(r.fieldnames or [])
        rows = list(r)

    title_by_id: dict[str, str] = {}
    for row in rows:
        u = row.get("imagePageUrl", "").strip()
        if "commons.wikimedia.org/wiki/" in u:
            title_by_id[row["id"]] = urllib.parse.unquote(u.split("/wiki/", 1)[1])

    meta = fetch_commons_meta(list(title_by_id.values()))

    updated = 0
    missing_list = []
    for row in rows:
        vid = row["id"]
        if vid not in title_by_id:
            continue
        t = title_by_id[vid]
        m = meta.get(t, {})
        if m.get("missing"):
            missing_list.append((vid, t))
            print(f"  [MISSING] {vid:28s} | {t}")
            continue
        lic = m.get("license") or ""
        artist = m.get("artist") or ""
        uploader = m.get("uploader") or ""
        if artist and artist.lower() != "unknown author":
            credit_str = f"{artist} / Wikimedia Commons"
        elif uploader:
            credit_str = f"Unknown author (uploaded by {uploader}) / Wikimedia Commons"
        else:
            credit_str = "Wikimedia Commons"

        if lic:
            row["license"] = lic
        row["credit"] = credit_str
        updated += 1
        print(f"  [OK] {vid:28s} | lic={row['license']:26s} | credit={row['credit'][:55]}")

    with va_path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    print(f"\nUpdated {updated}/{len(title_by_id)} external visual assets. Missing: {len(missing_list)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
