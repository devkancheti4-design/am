"""AM -- a core reasoner whose every decision is a machine-authored law; AM SPLITTER -- the slide-preparer.

    from am import answer, answer_split
    answer({"kind": "rule", "pairs": [[x, y], ...], "queries": [q1, q2]})        -> [y1, y2] or "CANNOT"
    answer({"kind": "sequence", "terms": [a1, ..., a8]})                          -> [a9, a10] or "CANNOT"
    answer_split({"kind": "rule", "pairs": [...], "queries": [...]})            -> [y1, y2] or "CANNOT"

The eyes (look.py, split_look.py) only list what fits; every decision is a synthesised law (am_law.am, am_split_law.am_split,
identical to c/am.c and c/am_split.c)."""
from collections import Counter
from . import look, split_look
from .am_law import am as _am
from .am_split_law import am_split as _am_split

SRC = {"rule": [("x", 0), ("x", 1), ("x", 2), ("x", 3)], "sequence": [("n", 0), ("succ", 0), ("alt", 0), ("rec2", 0)]}
FAMS = ("none", "cut", "parity", "mod3", "sign")


def state(kind, cands):
    """AM's 14-bit state and each source's top prediction (see README)"""
    n = 0 if kind == "rule" else 1
    tops = []
    for i, (view, lane) in enumerate(SRC[kind]):
        cs = [c for c in cands if c["view"] == view and c["lane"] == lane]
        if not cs:
            tops.append(None); continue
        d = min(c["depth"] for c in cs)
        votes = Counter(tuple(c["pred"]) for c in cs if c["depth"] == d)
        top = max(votes.items(), key=lambda kv: (kv[1], [-v for v in kv[0]]))[0]
        n |= ((1 if d <= 1 else min(d, 3)) | int(len(votes) == 1) << 2) << (1 + 3 * i)
        tops.append(list(top))
    found = [t for t in tops if t is not None]
    if found and all(t == found[0] for t in found):
        n |= 1 << 13
    return n, tops


def answer(data):
    n, tops = state(data["kind"], look.candidates(data))
    m = _am(n)
    return "CANNOT" if m == 0 or tops[m - 1] is None else tops[m - 1]


def split_state(rep):
    n = 0
    for i, f in enumerate(FAMS):
        r = rep[f]
        n |= (0 if not r.get("found") else (1 if r["depth"] <= 1 else min(r["depth"], 3))) << (2 * i)
    return n


def answer_split(data):
    rep = split_look.family_report(data)
    m = _am_split(split_state(rep))
    return "CANNOT" if m == 0 else rep[FAMS[m - 1]]["pred"]
