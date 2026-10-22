"""Query Shazam with separate overlapping windows; retain raw evidence."""
import argparse
import asyncio
import io
import json
import subprocess
import wave
from pathlib import Path

import numpy as np
from shazamio import Shazam


def decode(path, rate=16000):
    raw = subprocess.check_output([
        "ffmpeg", "-v", "error", "-i", str(path), "-vn", "-ac", "1",
        "-ar", str(rate), "-f", "f32le", "-",
    ])
    return np.frombuffer(raw, dtype="<f4")


def wav_bytes(samples, rate=16000):
    out = io.BytesIO()
    with wave.open(out, "wb") as wav:
        wav.setparams((1, 2, rate, 0, "NONE", "not compressed"))
        wav.writeframes((np.clip(samples, -1, 1) * 32767).astype("<i2").tobytes())
    return out.getvalue()


async def run(args):
    samples = decode(args.file)
    duration = len(samples) / 16000
    client = Shazam()
    records = []
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    # Each window stays contiguous. Do not concatenate disconnected fragments.
    starts = sorted(set([*np.arange(0, max(0, duration - 12), args.hop), max(0, duration - 12)]))
    for start in starts:
        chunk = samples[round(start * 16000):round((start + 12) * 16000)]
        record = {"clip_offset_seconds": float(start), "source_seconds": args.source_start + float(start)}
        try:
            result = await asyncio.wait_for(client.recognize(wav_bytes(chunk)), timeout=35)
            record["response"] = result
            track = result.get("track", {})
            print(f"{start:.1f}s: {track.get('subtitle', '')} — {track.get('title', 'NO MATCH')}", flush=True)
        except Exception as exc:
            record["error"] = str(exc)
            print(f"{start:.1f}s: ERROR {exc}", flush=True)
        records.append(record)
        output.write_text(json.dumps(records, indent=2, ensure_ascii=False))
        await asyncio.sleep(1)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("file")
    p.add_argument("--hop", type=float, default=8)
    p.add_argument("--source-start", type=float, default=3339)
    p.add_argument("--output", default="results/shazam.json")
    a = p.parse_args()
    if a.hop <= 0:
        p.error("--hop must be positive")
    asyncio.run(run(a))
