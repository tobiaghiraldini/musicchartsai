
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ACRCLOUD FILE SCANNING → RAW DUMP (WITH NO-MATCH FLAG)
------------------------------------------------------
Exports raw File Scanning results *as-is* preserving all candidates (including cover with missing scores)
and marking explicit no-match cases.

Outputs:
  - fs_files.csv
  - fs_candidates.csv
  - fs_raw.jsonl

Usage:
  export ACR_BASE_URL="https://api-<region>.acrcloud.com"
  export ACR_BEARER="YOUR_CONSOLE_API_BEARER"
  export ACR_CONTAINER_ID="YOUR_FS_CONTAINER_ID"
  python dump_acrcloud_fs_raw.py --limit 0
"""
import os, sys, csv, json, argparse
from urllib.parse import urlencode
import urllib.request
from typing import Dict, Any, List, Optional

def http_get_json(url: str, bearer: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if params:
        url = url + ("&" if "?" in url else "?") + urlencode(params)
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {bearer}",
        "Accept": "application/json"
    })
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))

def ensure_dir(path: str):
    if not os.path.isdir(path):
        os.makedirs(path, exist_ok=True)

def safe_get(d: Dict[str, Any], path: List[str], default=None):
    cur = d
    for k in path:
        if isinstance(cur, dict) and k in cur:
            cur = cur[k]
        else:
            return default
    return cur

def normalize_file_item(file_item: Dict[str, Any]) -> Dict[str, Any]:
    res = file_item.get("results") or {}
    has_music = bool(res.get("music"))
    has_cover = bool(res.get("cover_songs"))
    has_any = has_music or has_cover
    return {
        "file_id": file_item.get("id"),
        "filename": file_item.get("name"),
        "engine": file_item.get("engine"),  # 1=fingerprint, 2=cover, 3=both
        "duration_ms": file_item.get("duration_ms"),
        "status": file_item.get("status"),
        "created_at": file_item.get("created_at"),
        "updated_at": file_item.get("updated_at"),
        "tags": ",".join(file_item.get("tags") or []) if isinstance(file_item.get("tags"), list) else file_item.get("tags"),
        "has_results": 1 if has_any else 0,
        "has_music": 1 if has_music else 0,
        "has_cover": 1 if has_cover else 0,
        "is_no_match": 1 if not has_any else 0,
        "result_status_code": safe_get(file_item, ["results","status","code"]),
        "raw_len_music": len(res.get("music") or []),
        "raw_len_cover": len(res.get("cover_songs") or []),
    }

def iter_candidates(file_item: Dict[str, Any]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    res = file_item.get("results") or {}
    for bucket, origin in [("music", "fingerprint"), ("cover_songs", "cover")]:
        items = res.get(bucket) or []
        for rank, itm in enumerate(items, start=1):
            r = itm.get("result") or {}
            out.append({
                "file_id": file_item.get("id"),
                "rank": rank,
                "bucket": bucket,
                "origin": origin,
                "acrid": r.get("acrid"),
                "title": r.get("title"),
                "artists": ", ".join([a.get("name") for a in (r.get("artists") or []) if a.get("name")]),
                "album": safe_get(r, ["album","name"]),
                "label": r.get("label"),
                "isrc": safe_get(r, ["external_ids","isrc"]) or r.get("isrc"),
                "external_ids": json.dumps(r.get("external_ids") or {}, ensure_ascii=False),
                "duration_ms": r.get("duration_ms"),
                "play_offset_ms": r.get("play_offset_ms"),
                "db_begin_time_offset_ms": r.get("db_begin_time_offset_ms"),
                "score": r.get("score"),
                "similarity": r.get("similarity"),
                "distance": r.get("distance"),
                "pattern_matching": r.get("pattern_matching"),
                "risk": r.get("risk"),
                "match_type": r.get("match_type"),
                "raw_result": json.dumps(r, ensure_ascii=False)
            })
    if not out:
        out.append({
            "file_id": file_item.get("id"),
            "rank": None,
            "bucket": "none",
            "origin": "none",
            "acrid": None,
            "title": None,
            "artists": None,
            "album": None,
            "label": None,
            "isrc": None,
            "external_ids": "{}",
            "duration_ms": None,
            "play_offset_ms": None,
            "db_begin_time_offset_ms": None,
            "score": None,
            "similarity": None,
            "distance": None,
            "pattern_matching": None,
            "risk": None,
            "match_type": None,
            "raw_result": "{}",
        })
    return out

def dump_fs_container(base_url: str, bearer: str, container_id: str, limit: int=0, page_size: int=100, outdir: str="acr_fs_dump"):
    ensure_dir(outdir)
    files_csv = os.path.join(outdir, "fs_files.csv")
    cand_csv = os.path.join(outdir, "fs_candidates.csv")
    raw_jsonl = os.path.join(outdir, "fs_raw.jsonl")

    with open(files_csv, "w", newline="", encoding="utf-8") as f_files,\
         open(cand_csv, "w", newline="", encoding="utf-8") as f_cand,\
         open(raw_jsonl, "w", encoding="utf-8") as f_raw:
        files_writer = csv.DictWriter(f_files, fieldnames=[
            "file_id","filename","engine","duration_ms","status","created_at","updated_at","tags",
            "has_results","has_music","has_cover","is_no_match","result_status_code","raw_len_music","raw_len_cover"
        ]); files_writer.writeheader()
        cand_writer = csv.DictWriter(f_cand, fieldnames=[
            "file_id","rank","bucket","origin","acrid","title","artists","album","label","isrc",
            "external_ids","duration_ms","play_offset_ms","db_begin_time_offset_ms",
            "score","similarity","distance","pattern_matching","risk","match_type","raw_result"
        ]); cand_writer.writeheader()

        page, fetched = 1, 0
        while True:
            params = {"page": page, "per_page": page_size, "with_result": 1}
            url = f"{base_url}/api/fs-containers/{container_id}/files"
            data = http_get_json(url, bearer, params=params)
            items = data.get("data") or data.get("items") or data.get("files") or []
            if not items: break
            for item in items:
                files_writer.writerow(normalize_file_item(item))
                f_raw.write(json.dumps(item, ensure_ascii=False) + "\n")
                for c in iter_candidates(item):
                    cand_writer.writerow(c)
                fetched += 1
                if limit and fetched >= limit:
                    break
            if limit and fetched >= limit: break
            page += 1
            total_pages = data.get("total_pages") or data.get("last_page")
            if total_pages and page > int(total_pages): break
            if not total_pages and len(items) < page_size: break

    print("Done. Outputs in", outdir)

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--base_url", default=os.environ.get("ACR_BASE_URL","").rstrip("/"))
    p.add_argument("--bearer", default=os.environ.get("ACR_BEARER",""))
    p.add_argument("--container", default=os.environ.get("ACR_CONTAINER_ID",""))
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--page_size", type=int, default=100)
    p.add_argument("--outdir", default="acr_fs_dump")
    a = p.parse_args()
    if not a.base_url or not a.bearer or not a.container:
        print("Missing --base_url/--bearer/--container or env vars.", file=sys.stderr); sys.exit(2)
    dump_fs_container(a.base_url, a.bearer, a.container, a.limit, a.page_size, a.outdir)
