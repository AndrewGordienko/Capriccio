"""Small-catalog cross-performance baseline: chroma + subsequence DTW + 12 keys.

Scores rank candidates; they are not calibrated match probabilities.
Inspired by AudioLabs' audio-matching/CENS work, not a reproduction of a neural paper.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import librosa
from recognize import decode


def features(path):
    source = Path(path).resolve()
    stat = source.stat()
    key = hashlib.sha256(f"cens-v1:{source}:{stat.st_size}:{stat.st_mtime_ns}".encode()).hexdigest()
    cache = Path("results/features") / f"{key}.npz"
    if cache.exists():
        with np.load(cache) as data:
            return data["chroma"], .2
    y = decode(path, 22050)
    if len(y) < 22050:
        raise ValueError("Use at least one second of audio; 15–30 seconds is preferable")
    # CQT-based CENS: octave folding, energy quantization, temporal smoothing.
    # It reduces sensitivity to loudness and timbre without claiming invariance
    # to every rearrangement. Tuning is estimated by librosa's CQT front-end.
    chroma = librosa.feature.chroma_cens(y=y, sr=22050, hop_length=2205,
                                        n_octaves=7, win_len_smooth=11)
    chroma = chroma.astype(np.float32)[:, ::2]
    cache.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(cache, chroma=chroma)
    return chroma, .2


def align(query, reference):
    """Slope-limited (1,1)/(1,2)/(2,1) subsequence DTW, free reference start."""
    cost = np.clip(1 - query.T @ reference, 0, 2)
    n, m = cost.shape
    d = np.full((n + 1, m + 1), np.inf, dtype=np.float32)
    d[0] = 0
    for i in range(1, n + 1):
        d[i, 1:] = d[i - 1, :-1] + cost[i - 1]
        if m > 1:
            d[i, 2:] = np.minimum(d[i, 2:], d[i - 1, :-2] + cost[i - 1, 1:])
        if i > 1:
            d[i, 1:] = np.minimum(d[i, 1:], d[i - 2, :-1] + cost[i - 2] + cost[i - 1])
    j = int(np.argmin(d[n, 1:])) + 1
    end, total = j, float(d[n, j])
    i = n
    while i > 0:
        moves = [(d[i - 1, j - 1] + cost[i - 1, j - 1], 1, 1)] if j else []
        if j > 1:
            moves.append((d[i - 1, j - 2] + cost[i - 1, j - 1], 1, 2))
        if i > 1 and j:
            moves.append((d[i - 2, j - 1] + cost[i - 2, j - 1] + cost[i - 1, j - 1], 2, 1))
        _, di, dj = min(moves)
        i, j = i - di, j - dj
    return total / n, j, end


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("query")
    p.add_argument("references", nargs="+")
    p.add_argument("--output", default="results/classical.json")
    args = p.parse_args()
    query, dt = features(args.query)
    results = []
    for path in args.references:
        reference, _ = features(path)
        options = []
        for key in range(12):
            score, start, end = align(np.roll(query, key, axis=0), reference)
            options.append((score, key, start, end))
        score, key, start, end = min(options)
        item = dict(file=path, distance=score, query_shift_semitones=key,
                    reference_start_seconds=start * dt, reference_end_seconds=end * dt)
        results.append(item)
        print(json.dumps(item), flush=True)
    results.sort(key=lambda r: r["distance"])
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"status": "candidate_ranking_only", "results": results}, indent=2))


if __name__ == "__main__":
    main()
