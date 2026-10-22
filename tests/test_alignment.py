import numpy as np

from classical import align


def musical_sequence(seed, count, hold=3):
    rng = np.random.default_rng(seed)
    # Non-periodic changing chord vectors, each held for several frames.
    x = np.zeros((12, count))
    for i in range(0, count, hold):
        notes = rng.choice(12, 3, replace=False)
        x[notes, i:i + hold] = 1 / np.sqrt(3)
    return x.astype(np.float32)


def test_find_unknown_offset():
    ref = musical_sequence(9, 150, hold=1)
    score, start, end = align(ref[:, 43:93], ref)
    assert score < 1e-6
    assert abs(start - 43) <= 2
    assert abs(end - 93) <= 2


def test_tempo_change_still_beats_unrelated_music():
    ref = musical_sequence(7, 180)
    query = ref[:, 40:100:2]
    positive, _, _ = align(query, ref)
    negative, _, _ = align(query, musical_sequence(8, 180))
    assert positive < 1e-6
    assert negative > positive + .05


def test_transposition_search_recovers_correct_key():
    ref = musical_sequence(17, 180)
    query = np.roll(ref[:, 32:92], 5, axis=0)
    candidates = [(align(np.roll(query, k, axis=0), ref)[0], k) for k in range(12)]
    score, key = min(candidates)
    assert key == 7
    assert score < 1e-6
