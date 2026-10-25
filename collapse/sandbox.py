"""THE COLLAPSE SANDBOX -- exact arithmetic, every number checked exhaustively.
WORLD   64 hidden integer laws on x = 0..255: one basic-Python step, then x % c or x & 5c (outputs 0..60).  The truth is
        the full table, 64 x 256 = 16,384 exact points.
LEARNER a small MLP (input: law id one-hot + the 8 bits of x; output: 64 classes).  Each generation sees a fresh random
        25% of every law's inputs and must generalise to the rest -- its mistakes are real.
RECURSION  generation g trains a FRESH model only on labels made by generation g-1 (the regime in which collapse is known).
ARMS    unverified  - the model's labels, as they come
        accumulate  - every earlier training set kept, plus the model's new labels (real gen-0 data stays in)
        am          - AM as maintainer: per law, AM sees 8 of the model's labelled points at a time (6 tries), extracts a
                      rule from them, keeps the rule that agrees with most of the model's labels, and relabels every
                      sampled point with it; if no rule agrees with at least half, the law's points are dropped (abstain).
                      AM never sees the true law.  (Blind: no reference example.)
        am_anchor   - AM as maintainer shown ONE reference example: per law, 8 exact points (3% of the table) fixed
                      before generation 0.  AM extracts the rule from them and relabels every sampled point with it;
                      if it answers CANNOT (or a rule outside 0..63), the law's points are dropped (abstain).
        proven      - exact labels (the proven-laws corpus)
METRICS per generation: accuracy over all 16,384 points; on the TAILS (points whose true output is one of the rarest
        values, < 1% of the table); the arm's training-label error rate; distinct (law, output) pairs the model gets right.
    python3 sandbox.py SEEDS GENS                -> sandbox_results.json (unverified, accumulate, am, proven)
    python3 sandbox.py SEEDS GENS am_anchor      -> sandbox_results_am_anchor.json"""
import json, os, random, sys, time
from multiprocessing import Pool
import numpy as np
import torch, torch.nn as nn
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "python"))
from am import look, answer
look.chains.__defaults__ = (2,)                     # the eyes' depth for this world (laws have 2 steps)
torch.set_num_threads(1)

BASIC = [("+", lambda x, c: x + c), ("-", lambda x, c: x - c), ("*", lambda x, c: x * c), ("//", lambda x, c: x // c),
         ("^", lambda x, c: x ^ c), ("|", lambda x, c: x | c), ("<<", lambda x, c: x << (c % 4 + 1)), (">>", lambda x, c: x >> (c % 4 + 1)),
         ("sq", lambda x, c: x * x), ("max", lambda x, c: max(x, c))]
FINAL = [("%", lambda x, c: x % c), ("&", lambda x, c: x & (5 * c))]
K, X = 64, 256


def world(seed):
    R = random.Random(seed); laws = []
    while len(laws) < K:
        (_, f), c = R.choice(BASIC), R.randint(2, 12)
        (_, g), d = R.choice(FINAL), R.randint(2, 12)
        tab = [g(f(x, c), d) for x in range(X)]
        if len(set(tab)) >= 3 and max(tab) < 64:
            laws.append(tab)
    return np.array(laws)                             # K x X, exact


def features(k, x):
    v = np.zeros((len(k), K + 8), np.float32)
    v[np.arange(len(k)), k] = 1
    for b in range(8):
        v[:, K + b] = (x >> b) & 1
    return torch.from_numpy(v)


def fit(k, x, y, seed, steps=1500):
    torch.manual_seed(seed)
    m = nn.Sequential(nn.Linear(K + 8, 256), nn.ReLU(), nn.Linear(256, 256), nn.ReLU(), nn.Linear(256, 64))
    opt = torch.optim.Adam(m.parameters(), 3e-3)
    F, Y = features(k, x), torch.from_numpy(y.astype(np.int64))
    g = torch.Generator().manual_seed(seed)
    for _ in range(steps):
        i = torch.randint(len(Y), (512,), generator=g)
        loss = nn.functional.cross_entropy(m(F[i]), Y[i])
        opt.zero_grad(); loss.backward(); opt.step()
    return m


ALLK, ALLX = np.repeat(np.arange(K), X), np.tile(np.arange(X), K)


def predict(m, k, x):
    with torch.no_grad():
        return m(features(k, x)).argmax(1).numpy()


def am_relabel(xs, ys, rng):
    """AM as maintainer for one law: rules from 8-point subsets of the model's labels; the one agreeing with most of
    them relabels every point; None if no rule agrees with at least half"""
    best = None
    for _ in range(6):
        idx = rng.sample(range(len(xs)), 8)
        q = [int(v) for v in xs]
        a = answer({"kind": "rule", "pairs": [[int(xs[i]), int(ys[i])] for i in idx], "queries": q})
        if a == "CANNOT" or min(a) < 0 or max(a) > 63:
            continue                                  # a law of this world only outputs 0..63: any other rule is not it
        agree = sum(int(p) == int(t) for p, t in zip(a, ys))
        if best is None or agree > best[0]:
            best = (agree, a)
    if best is None or best[0] < len(xs) / 2:
        return None
    return np.array(best[1])


def run(args):
    seed, G, arms = args
    truth = world(seed); rng = np.random.default_rng(seed); R = random.Random(seed)
    counts = np.bincount(truth.ravel(), minlength=64); rare = counts < 0.01 * truth.size
    tailmask = rare[truth.ravel()]

    def sample():
        k = np.repeat(np.arange(K), X // 4); x = np.concatenate([rng.choice(X, X // 4, replace=False) for _ in range(K)])
        return k, x
    out = {}
    anchor = {law: sorted(R.sample(range(X), 8)) for law in range(K)}   # the handmade reference: 8 exact points a law (3%)
    for arm in arms:
        k, x = sample(); y = truth[k, x]
        pool = [(k, x, y)]
        m = fit(k, x, y, seed * 100)
        rec = []
        for g in range(G + 1):
            p = predict(m, ALLK, ALLX); t = truth.ravel()
            rec.append(dict(gen=g, acc=float((p == t).mean()), tail=float((p[tailmask] == t[tailmask]).mean()) if tailmask.any() else None,
                            pairs=int(len(set(zip(ALLK[p == t], p[p == t])))), label_err=(float(err) if g else 0.0)))
            if g == G:
                break
            k, x = sample(); lab = predict(m, k, x)
            if arm == "proven":
                lab = truth[k, x]
            elif arm == "am_anchor":
                kk, xx, ll = [], [], []
                for law in range(K):
                    s = k == law
                    a = answer({"kind": "rule", "pairs": [[int(v), int(truth[law, v])] for v in anchor[law]],
                                "queries": [int(v) for v in x[s]]})
                    if a != "CANNOT" and min(a) >= 0 and max(a) <= 63:
                        kk.append(k[s]); xx.append(x[s]); ll.append(np.array(a))
                k, x, lab = (np.concatenate(kk), np.concatenate(xx), np.concatenate(ll)) if kk else (k[:0], x[:0], lab[:0])
            elif arm == "am":
                kk, xx, ll = [], [], []
                for law in range(K):
                    s = k == law
                    new = am_relabel(x[s], lab[s], R)
                    if new is not None:
                        kk.append(k[s]); xx.append(x[s]); ll.append(new)
                k, x, lab = (np.concatenate(kk), np.concatenate(xx), np.concatenate(ll)) if kk else (k[:0], x[:0], lab[:0])
            err = (lab != truth[k, x]).mean() if len(lab) else 0.0
            if arm == "accumulate":
                pool.append((k, x, lab)); k, x, lab = (np.concatenate([a[i] for a in pool]) for i in range(3))
            m = fit(k, x, lab, seed * 100 + g + 1)
        out[arm] = rec
    return seed, out


ARMS_RUN = ("unverified", "accumulate", "am", "proven")
if __name__ == "__main__":
    S, G = int(sys.argv[1]), int(sys.argv[2])
    if len(sys.argv) > 3:
        ARMS_RUN = tuple(sys.argv[3].split(","))
    t0 = time.time()
    with Pool(min(S, 12)) as pool:
        R = dict(pool.map(run, [(s, G, ARMS_RUN) for s in range(S)]))
    json.dump(R, open("sandbox_results%s.json" % ("" if len(sys.argv) <= 3 else "_" + sys.argv[3].replace(",", "_")), "w"), indent=1)
    print("done: %d seeds x %d generations x %d arms in %.0f s" % (S, G, len(ARMS_RUN), time.time() - t0))
