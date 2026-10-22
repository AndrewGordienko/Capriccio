"""Plot the actual landmark selection and cross-performance chroma evidence."""
import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from polaris.config import DEFAULT_CONFIG
from polaris.engine import read_audio
from polaris.fingerprint import analyze_shift, compute_spectrogram

from classical import features


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("query")
    p.add_argument("reference_excerpt")
    p.add_argument("--output", default="results/evidence.png")
    args = p.parse_args()
    config = DEFAULT_CONFIG
    samples = read_audio(args.query, sample_rate=config.audio.sample_rate)
    analysis = analyze_shift(samples, config.audio.sample_rate, 0, config)
    points = analysis.landmarks()
    query, dt = features(args.query)
    ref, _ = features(args.reference_excerpt)
    fig, axes = plt.subplots(3, 1, figsize=(12, 9), constrained_layout=True)
    spec = compute_spectrogram(samples, window_size=config.audio.window_size,
                               hop_size=config.audio.hop_size)
    axes[0].imshow(spec, origin="lower", aspect="auto", cmap="magma",
                   extent=[0, spec.shape[1] * config.audio.hop_size / config.audio.sample_rate,
                           0, config.audio.sample_rate / 2], vmin=0, vmax=75)
    axes[0].scatter([x.time_bin * config.audio.hop_size / config.audio.sample_rate for x in points],
                    [x.frequency_bin * config.audio.sample_rate / config.audio.window_size for x in points],
                    s=9, color="#72ffb6", linewidths=0)
    axes[0].set(ylim=(0, 4000), ylabel="Frequency (Hz)",
                title=f"55:59–56:19: {len(points)} POLARIS spectral landmarks")
    labels = ["C", "C♯", "D", "D♯", "E", "F", "F♯", "G", "G♯", "A", "A♯", "B"]
    for ax, values, title in zip(axes[1:], [query, ref],
            ["Query: Frankfurt / Altinoglu — CENS harmonic features",
             "Reference: Capriccio italien / Repušic, approximately 6:18–6:38"]):
        ax.imshow(values, origin="lower", aspect="auto", cmap="viridis", vmin=0, vmax=.65,
                  extent=[0, values.shape[1] * dt, -.5, 11.5])
        ax.set(yticks=range(12), yticklabels=labels, ylabel="Pitch class", title=title)
    axes[-1].set_xlabel("Seconds within each excerpt (before tempo alignment)")
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(out)


if __name__ == "__main__":
    main()
