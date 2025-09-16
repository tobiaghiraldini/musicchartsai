
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick analysis of fs_candidates.csv:
- histograms of scores (by bucket)
- count of matches by bucket/origin
Generates PNGs in ./acr_fs_dump/plots
"""
import os, csv
import pandas as pd
import matplotlib.pyplot as plt

IN = "acr_fs_dump/fs_candidates.csv"
OUTDIR = "acr_fs_dump/plots"

def main():
    os.makedirs(OUTDIR, exist_ok=True)
    df = pd.read_csv(IN)
    # coerce numeric
    for c in ("score","similarity","distance"):
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    # Histogram score overall
    plt.figure()
    df["score"].dropna().hist(bins=20)
    plt.title("Score distribution (all candidates)")
    plt.xlabel("score"); plt.ylabel("count")
    plt.savefig(os.path.join(OUTDIR, "hist_score_all.png"), dpi=140)
    plt.close()

    # By bucket
    for bucket in df["bucket"].dropna().unique():
        sub = df[df["bucket"]==bucket]
        if sub["score"].notna().any():
            plt.figure()
            sub["score"].dropna().hist(bins=20)
            plt.title(f"Score distribution ({bucket})")
            plt.xlabel("score"); plt.ylabel("count")
            plt.savefig(os.path.join(OUTDIR, f"hist_score_{bucket}.png"), dpi=140)
            plt.close()

    # Counts by bucket
    counts = df["bucket"].value_counts().sort_index()
    plt.figure()
    counts.plot(kind="bar")
    plt.title("Candidates by bucket")
    plt.xlabel("bucket"); plt.ylabel("count")
    plt.tight_layout()
    plt.savefig(os.path.join(OUTDIR, "counts_by_bucket.png"), dpi=140)
    plt.close()

    print("Saved plots to", OUTDIR)

if __name__ == "__main__":
    main()
