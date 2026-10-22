"""Regenerate the comparison clips with yt-dlp and FFmpeg.

Run with the Python environment containing requirements.txt. Requires FFmpeg
and Node (for YouTube's JavaScript challenges). Existing downloads are reused.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "media"
DIST = ROOT / "dist" / "media"


def run(*command):
    subprocess.run([str(part) for part in command], check=True)


def download(name, url, start, end):
    output = RAW / f"{name}-source.mp4"
    if not output.exists():
        run(sys.executable, "-m", "yt_dlp", "--js-runtimes", "node",
            "--force-keyframes-at-cuts", "--download-sections", f"*{start}-{end}",
            "-f", "bv*[height<=720][vcodec^=avc1]+ba[ext=m4a]/b[height<=720]/best",
            "--merge-output-format", "mp4", "--no-playlist", "-o", output, url)
    return output


def render(source, name, duration, speed=1.0, pitch=0):
    video_filter = f"setpts=PTS/{speed},scale=960:-2"
    audio_filter = f"atempo={speed}"
    if pitch:
        ratio = 2 ** (pitch / 12)
        audio_filter = (f"aresample=48000,asetrate=48000*{ratio:.10f},"
                        f"aresample=48000,atempo={speed / ratio:.10f}")
    run("ffmpeg", "-v", "error", "-y", "-i", source,
        "-vf", video_filter, "-af", audio_filter, "-t", duration,
        "-c:v", "libx264", "-preset", "fast", "-crf", "24",
        "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", DIST / name)


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    DIST.mkdir(parents=True, exist_ok=True)
    original = download("original", "https://www.youtube.com/watch?v=R4MMZt_1sQg",
                        "00:55:59", "00:56:19")
    reference = download("reference", "https://www.youtube.com/watch?v=NMvFoCqdZHc",
                         "00:06:17.6", "00:06:38.0")
    render(original, "original.mp4", 20)
    render(reference, "reference.mp4", 20.4)
    render(reference, "reference-adjusted.mp4", 20, speed=1.02)
    render(reference, "reference-minus2.mp4", 20, speed=1.02, pitch=-2)
    render(reference, "reference-plus2.mp4", 20, speed=1.02, pitch=2)
    for name in ("original", "reference"):
        run("ffmpeg", "-v", "error", "-y", "-ss", "5", "-i", DIST / f"{name}.mp4",
            "-frames:v", "1", "-q:v", "3", DIST / f"{name}.jpg")
    print(f"Media ready in {DIST}")


if __name__ == "__main__":
    main()
