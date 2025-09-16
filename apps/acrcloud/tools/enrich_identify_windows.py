
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ACRCLOUD IDENTIFICATION ENRICHMENT (OPTIONAL)
---------------------------------------------
Given fs_candidates.csv (from dump) and corresponding local audio files,
re-run Identification API on windows to retrieve *multi-candidate* scores
(top_n>1), especially useful when cover items miss scores in File Scanning.

This is a template. You must provide:
  - HOST (identify-<region>.acrcloud.com)
  - ACCESS_KEY / ACCESS_SECRET (Identification API creds)
  - A mapping from filename -> local audio path (or adjust fetch_audio())

Usage:
  python enrich_identify_windows.py --audio_dir ./audio --candidates acr_fs_dump/fs_candidates.csv --out enr_candidates.csv --top_n 5 --win 12 --hop 6

Note: For brevity, this sends raw audio; you can switch to fingerprints if you prefer.
"""
import os, sys, csv, hmac, hashlib, base64, time, argparse, json
from urllib.parse import urlparse
import urllib.request

IDENT_HOST   = os.environ.get("ACR_ID_HOST", "identify-eu-west-1.acrcloud.com")
ACCESS_KEY   = os.environ.get("ACR_ID_ACCESS_KEY", "")
ACCESS_SECRET= os.environ.get("ACR_ID_ACCESS_SECRET", "")

def sign_string(string_to_sign: str, secret: str) -> str:
    dig = hmac.new(bytes(secret, 'utf-8'), bytes(string_to_sign, 'utf-8'), digestmod=hashlib.sha1).digest()
    return base64.b64encode(dig).decode('utf-8')

def identify_bytes(payload: bytes, data_type="audio", top_n=5):
    path = "/v1/identify"
    method = "POST"
    http_date = time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime())
    string_to_sign = f"{method}\n{path}\n{http_date}\napplication/octet-stream\nx-amz-acrcloud-1"
    sig = sign_string(string_to_sign, ACCESS_SECRET)
    url = f"https://{IDENT_HOST}{path}?data_type={data_type}&top_n={top_n}"
    req = urllib.request.Request(url, data=payload, method="POST", headers={
        "Content-Type":"application/octet-stream",
        "Date": http_date,
        "Authorization": f"ACS {ACCESS_KEY}:{sig}",
        "x-amz-acrcloud-1": "1"
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))

def slice_audio_bytes(full_bytes: bytes, sample_rate=44100, seconds=12, hop=6, channels=1, bytes_per_sample=2):
    # naive slicer for PCM WAV payloads stripped to raw; adjust for your format.
    # In production use pydub/ffmpeg to decode. Placeholder here.
    window = sample_rate * seconds * channels * bytes_per_sample
    stride = sample_rate * hop * channels * bytes_per_sample
    i = 0
    while i + window <= len(full_bytes):
        yield full_bytes[i:i+window]
        i += stride

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--audio_dir", required=True, help="Directory with local audio files named like fs filename")
    ap.add_argument("--candidates", required=True, help="fs_candidates.csv from dump")
    ap.add_argument("--out", default="enr_candidates.csv")
    ap.add_argument("--top_n", type=int, default=5)
    ap.add_argument("--win", type=int, default=12, help="seconds per window")
    ap.add_argument("--hop", type=int, default=6, help="seconds hop between windows")
    args = ap.parse_args()

    if not ACCESS_KEY or not ACCESS_SECRET:
        print("Set ACR_ID_ACCESS_KEY / ACR_ID_ACCESS_SECRET / ACR_ID_HOST env vars.", file=sys.stderr); sys.exit(2)

    # Read list of filenames to process (only cover/no-score or bucket none)
    target_files = set()
    with open(args.candidates, newline='', encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            if row["bucket"] in ("cover_songs","none") and (not row.get("score") or row["score"] in ("", "None")):
                target_files.add(row["file_id"])  # We don't have filename here; join via fs_files if needed.

    # For simplicity, iterate all files in audio_dir
    out_rows = []
    for fn in os.listdir(args.audio_dir):
        path = os.path.join(args.audio_dir, fn)
        if not os.path.isfile(path): continue
        with open(path, "rb") as f:
            audio_bytes = f.read()
        for chunk in slice_audio_bytes(audio_bytes, seconds=args.win, hop=args.hop):
            resp = identify_bytes(chunk, data_type="audio", top_n=args.top_n)
            # Flatten all candidates from metadata.music
            meta = resp.get("metadata", {}) if isinstance(resp, dict) else {}
            for rank, it in enumerate(meta.get("music", []) or [], start=1):
                out_rows.append({
                    "filename": fn,
                    "rank": rank,
                    "title": it.get("title"),
                    "artists": ", ".join([a.get("name") for a in (it.get("artists") or []) if a.get("name")]),
                    "isrc": (it.get("external_ids") or {}).get("isrc") or it.get("isrc"),
                    "score": it.get("score"),
                    "similarity": it.get("similarity"),
                    "play_offset_ms": it.get("play_offset_ms"),
                    "engine_hint": it.get("result_from") or it.get("engine")  # may be absent
                })

    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["filename","rank","title","artists","isrc","score","similarity","play_offset_ms","engine_hint"])
        w.writeheader()
        w.writerows(out_rows)
    print("Wrote", args.out)

if __name__ == "__main__":
    main()
