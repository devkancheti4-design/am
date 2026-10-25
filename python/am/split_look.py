"""THE SPLITTER'S EYES -- every way of cutting the examples, looked at; nothing decided.
FAMILIES  none (all examples one piece), cut (x < c, every c between examples leaving >= 3 a side; the best-fitting c
          kept: shallowest deepest piece, then shallowest total), parity (x % 2), mod3 (x % 3), sign (x < 0).
A family is FOUND when every piece has a rule of <= 3 basic-Python steps (look.chains).  Its prediction for a
question comes from the piece the question falls in (the most common prediction at that piece's shallowest depth).
    family_report(data) -> {family: dict(found, depth, uniq, pred)}"""
from collections import Counter
from . import look

FAMS = ("none", "cut", "parity", "mod3", "sign")
KEY = {"parity": lambda x: x % 2, "mod3": lambda x: x % 3, "sign": lambda x: int(x < 0)}


def piece(lane, queries):
    """rule for one piece: (depth, uniq, {query: prediction}) or None"""
    if len(lane) < 2:
        return None
    qs = list(queries)
    found = look.chains([x for x, _ in lane] + qs, [y for _, y in lane]) if qs else \
        look.chains([x for x, _ in lane], [y for _, y in lane])
    if not found:
        return None
    d = min(f[0] for f in found)
    at = [f[1] for f in found if f[0] == d]
    votes = Counter(at)
    top = max(votes.items(), key=lambda kv: (kv[1], [-v for v in kv[0]]))[0]
    return d, int(len(votes) == 1), dict(zip(qs, top))


def split_by(pairs, queries, key):
    lanes = {}
    for x, y in pairs:
        lanes.setdefault(key(x), []).append((x, y))
    qlane = {q: key(q) for q in queries}
    res = {}
    for k, lane in lanes.items():
        p = piece(lane, [q for q in queries if qlane[q] == k])
        if p is None:
            return None
        res[k] = p
    if any(qlane[q] not in res for q in queries):
        return None                                        # a question falls in a piece with no examples
    depth = max(p[0] for p in res.values())
    uniq = int(all(p[1] for p in res.values()))
    pred = [res[qlane[q]][2][q] for q in queries]
    return dict(found=1, depth=depth, uniq=uniq, pred=pred, total=sum(p[0] for p in res.values()))


def family_report(data):
    P = [tuple(p) for p in data["pairs"]]
    Q = list(data["queries"])
    rep = {}
    rep["none"] = split_by(P, Q, lambda x: 0)
    xs = sorted(set(x for x, _ in P))
    best = None
    for i in range(1, len(xs)):
        c = xs[i]
        if sum(x < c for x, _ in P) < 3 or sum(x >= c for x, _ in P) < 3:
            continue
        r = split_by(P, Q, lambda x, c=c: int(x >= c))
        if r and (best is None or (r["depth"], r["total"]) < (best["depth"], best["total"])):
            best = dict(r, cut=c)
    rep["cut"] = best
    for f in ("parity", "mod3", "sign"):
        rep[f] = split_by(P, Q, KEY[f])
    return {f: (rep[f] or dict(found=0)) for f in FAMS}
