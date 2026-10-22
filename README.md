# Local music identification lab

[Open the public comparison player](https://capriccio-listening-room.perkyplume9.chatgpt.site)

## Run the comparison website

The video excerpts and adjusted reference variants are included, so there is no frontend build or package installation:

```sh
node comparison/serve.mjs
```

Open **http://localhost:3000**. The player supports linked playback, A/B audio switching, an untouched reference, pitch variants, pitch-preserving speed adjustment and a timing nudge. Copy-share links preserve the selected settings.

To regenerate the media from the original YouTube sources after installing the Python requirements and FFmpeg:

```sh
.venv/bin/python comparison/prepare_media.py
```

The local GitHub checkout is independent of the source repository used by the Sites deployment. `comparison/.openai/hosting.json` records the existing public Site identity.


The music at **55:59** in [the supplied concert](https://www.youtube.com/watch?v=R4MMZt_1sQg&t=3359s) is **Pyotr Ilyich Tchaikovsky — Capriccio italien, Op. 45**. The concert performer is the Frankfurt Radio Symphony with Alain Altinoglu.

The extracted 55:59–56:19 query aligns to approximately **6:17.6–6:38.0** in [a separate performance conducted by Ivan Repušic](https://www.youtube.com/watch?v=NMvFoCqdZHc&t=377s). Our CENS/subsequence-DTW baseline gives distance **0.0341** for that passage, versus **0.1159** for the best passage/key in Chabrier's España. Lower is better; these are ranking distances, not probabilities. This is a two-work comparison, not a large-catalog accuracy benchmark. The work is also in the [official concert programme](https://www.hr-sinfonieorchester.de/livestreams/europa-open-air-2026-im-livestream-v1,livestream-20-08-2026-100.html).

Three consecutive, non-overlapping 20-second queries align in order to the separate performance: approximately 5:58–6:17, 6:18–6:38, and 6:38–6:57. All rank Capriccio above España. A test copy transposed up two semitones and accelerated by approximately 12% retrieves the same passage and the correct compensating key shift (10 semitones modulo 12). Raw results are in `results/multiple-passages.json`. The local landmark engine retrieves the source excerpt with 932 matching hashes and the exact **20.0-second** offset; the separate performance has 12 matched hashes. That contrast illustrates the different strengths of the two paths. See `results/evidence.png` for the selected landmarks and harmonic features.

## What runs locally

- `classical.py`: CQT-derived CENS chroma, all 12 circular key shifts, and slope-limited subsequence dynamic time warping. Finds matching passages despite moderate tempo/rubato differences and reduces dependence on instrumentation. It ranks provided reference files; it cannot identify music absent from those files. Features are cached under `results/features/`.
- `local.py`: a local landmark fingerprint index using the authors' **POLARIS** implementation, pinned to a Git commit. It extracts salient spectrogram landmarks, groups them into Delaunay triplets, hashes them, then votes for consistent recording/time offsets. This is an alternative to classic Shazam peak-pair hashing, not a reimplementation of proprietary Shazam. It identifies copies of recordings, not arbitrary renditions of compositions.
- `recognize.py`: computes Shazam-compatible signatures locally through ShazamIO and sends them to Shazam's online catalog, one contiguous 12-second window at a time. ShazamIO is an unofficial, reverse-engineered client. Responses and errors are saved without claiming that every returned title is correct.

Arbitrary local landmark hashes cannot be searched in Shazam, AcoustID, AudD or ACRCloud interchangeably. A service needs its own signature format or the audio itself. Local fingerprinting still requires a reference catalog; metadata databases alone do not provide one.

## Setup and repeat

Requires Python 3.12, FFmpeg and a JavaScript runtime supported by yt-dlp (Node works here).

```sh
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements.txt

# Re-encode the boundaries: stream-copy sections can include preroll.
.venv/bin/yt-dlp --js-runtimes node --force-keyframes-at-cuts \
  --download-sections '*00:55:39-00:56:39' -f 'bestaudio/best' \
  -o 'audio/exact.%(ext)s' 'https://www.youtube.com/watch?v=R4MMZt_1sQg'
ffmpeg -y -ss 20 -i audio/exact.webm -t 20 -ac 1 -ar 22050 audio/55m59s.wav

.venv/bin/python recognize.py audio/exact.webm --source-start 3339
.venv/bin/python classical.py audio/55m59s.wav audio/references/*.webm
.venv/bin/python local.py index results/fingerprints audio/exact.webm audio/references/*.webm
.venv/bin/python local.py query results/fingerprints audio/55m59s.wav
ffmpeg -y -ss 377.6 -i audio/references/capriccio-repusic.webm -t 20.4 -ac 1 -ar 22050 audio/capriccio-comparison.wav
.venv/bin/python inspect_audio.py audio/55m59s.wav audio/capriccio-comparison.wav

uv pip install --python .venv/bin/python pytest
.venv/bin/python -m pytest -q tests
```

Download the two comparison references:

```sh
.venv/bin/yt-dlp --js-runtimes node -f bestaudio -o 'audio/references/capriccio-repusic.%(ext)s' 'https://www.youtube.com/watch?v=NMvFoCqdZHc'
.venv/bin/yt-dlp --js-runtimes node -f bestaudio -o 'audio/references/espana-altinoglu.%(ext)s' 'https://www.youtube.com/watch?v=9iHFZX9xD3M'
```

`audio/exact.webm` is the accurate 60-second extract. `audio/target.webm` is the initial stream-copy extract with about nine seconds of preroll; its historical Shazam responses in `results/shazam.json` have approximate source times and must not be used as exact timestamp evidence. A window from that extract returned Capriccio italien attributed to Jansons/Oslo, which is useful only as a candidate composition. The boundary-accurate run (`results/shazam-exact.json`) mostly returned no match and also returned an unrelated title, illustrating why a single API answer is insufficient.

## Research considered, checked 22 October 2026

**Different tasks require different evidence.** Exact recording identification should preserve acoustic details. Cross-performance identification should suppress performance-specific details while retaining a distinctive musical phrase. Strong noise robustness does not imply robustness to another orchestra, transposition or arrangement.

| Research | Relevant finding and practical consequence | Limit |
| --- | --- | --- |
| [AudioLabs classical audio matching](https://www.audiolabs-erlangen.de/resources/MIR/FMP/C7/C7S2_AudioMatching.html), and [classical cross-version retrieval, 2020](https://www.mdpi.com/2076-3417/10/1/19) | Chroma/CENS sequences, short musical shingles and subsequence DTW target different performances, instruments and nonlinear tempo variation. This is the transparent CPU baseline implemented here. | Chroma loses register/voicing detail; generic scales, sustained chords and very short fragments can be ambiguous. |
| [CLEWS, ICML 2025](https://arxiv.org/abs/2502.16936), [official code/weights](https://github.com/sony/clews) | Learns version-invariant representations of approximately 20-second musical segments using weak labels and supervised contrastive learning. Strong candidate for a learned cross-version retrieval stage. | General version datasets do not establish accuracy on short orchestral excerpts or every arrangement. Not installed or benchmarked here. |
| [Unified Music Identification for Tracks and Versions, August 2026](https://arxiv.org/abs/2608.19919), [official Fish code/weights](https://github.com/raraz15/unified-track-and-version-id) | Directly compares exact-track and version retrieval. Its ablation shows a tradeoff between 10-second and 20-second segments; boundary alignment and query/index duration mismatch matter. This motivates overlapping windows and separate exact/phrase retrieval settings. | Its shipped retrieval uses NVIDIA cuVS with no CPU fallback. Published benchmark results are not proof of universal classical recognition. Not installed here. |
| [ByteCover3, ICASSP 2023](https://arxiv.org/abs/2303.11692) | Short-query version matching benefits from local features, local alignment loss and two-stage retrieval rather than a whole-song average. | Paper considered for design; not reproduced here. |
| [POLARIS, September 2026 preprint](https://arxiv.org/abs/2609.14820) | Local saliency normalization, geometric triplet hashes and adaptive query-side expansion improve noisy recording matching without training. Authors' engine is integrated locally. | Its reported PEX protocol explicitly excludes pitch and tempo shifts. It is not a solution to cross-performance classical matching. |
| [NMFP, ISMIR 2025](https://arxiv.org/abs/2506.22661), [real microphone evaluation, 2025](https://arxiv.org/abs/2507.06070) | Realistic room/channel/noise augmentation and evaluation matter; clean or synthetic benchmarks can overstate performance. | Learned exact-recording robustness is different from rendition invariance. |
| [Variable-Length Audio Fingerprinting, 2026](https://arxiv.org/abs/2603.23947) | Content-aware variable-length segmentation addresses boundary and time-stretch mismatch. | Its “live identification” task should not be read as evidence that arbitrary live orchestral renditions match studio recordings. |
| [Generative track identification, June 2026 preprint](https://arxiv.org/abs/2606.17301) | Reports strong very-short-query results by predicting catalog IDs directly. Interesting research direction for fixed catalogs. | Requires catalog-dependent training; does not supply an open worldwide search catalog or establish cross-performance accuracy. |

## Next architecture and evaluation

The recommended extension is a **two-path retriever**: exact fingerprints or NMFP for recording copies, and CLEWS/Fish phrase embeddings for other renditions. Index overlapping phrases from multiple performances, keyed by composer/work/movement/performance. Re-rank candidates with transposition-aware local alignment; preserve separate work and recording identities. CENS/DTW remains an interpretable verifier and CPU fallback.

For disconnected fragments, search each fragment separately, preserve its boundary, and combine evidence at work level. Do not create landmark pairs or a continuous alignment across an edit. Adjacent overlapping windows are correlated, so count distinct musical passages rather than presenting window count as independent evidence. Keep raw audio as a search branch; source separation can help an obscured passage but can also erase useful information.

Before claiming improvement, evaluate held-out performances and composers with 2/5/10/20/30-second queries, transpositions, instrument/arrangement changes, rubato, applause, speech, reverberation, compression and edits. Include catalog-absent queries and confusing works with similar motifs. Report work/movement recall@k, recording accuracy separately, false accepts/abstention, passage localization, latency and index size. Calibrate rejection against catalog size and negative examples. The current three alignment tests, three passages from one real cross-performance comparison, and one synthetic pitch/speed alteration are prototype checks, not that benchmark.
