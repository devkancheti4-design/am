"""THE SPLITTER'S WORLD -- multi-branch rules, machine-drawn (os.urandom).  A rule picks its branch by one predicate
of x -- a cut (x < c), parity (x % 2), residue (x % 3) or sign (x < 0) -- or has no branch at all; every branch is a
chain of 1-3 basic-Python steps (the same steps as the first battery).  12 examples, 2 questions drawn from the same
range (so a question can fall in any branch); traps are noise.  Distinct answers; |y| < 10^6.
    python3 gen_split.py design N  -> design.json (data + truth: design is meant to be seen)
    python3 gen_split.py test   N  -> problems.json (texts) + sealed.json (answers, never printed)"""
import json, os, random, sys
R = random.Random(int.from_bytes(os.urandom(8), "big"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib.util
spec = importlib.util.spec_from_file_location("g", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "rules", "gen_battery.py"))
SRC = open(spec.origin).read()
ns = {}
exec(SRC[:SRC.index("def draw_f")].replace("R = random.Random(int.from_bytes(os.urandom(8), \"big\"))", ""), dict(ns, R=R, random=random, os=os, json=json), ns)
step = lambda: eval("step", ns)()  # noqa
STEP = ns["step"]

PRED = {"cut": None, "parity": lambda x: x % 2, "mod3": lambda x: x % 3, "sign": lambda x: int(x < 0)}


def chain():
    return [STEP() for _ in range(R.randint(1, 3))]


def run(ch, x):
    for _, g in ch:
        x = g(x)
    return x


def draw_rule():
    while True:
        kind = R.choice(["none", "cut", "parity", "mod3", "sign"])
        cut = R.randint(0, 60)
        nb = {"none": 1, "cut": 2, "parity": 2, "mod3": 3, "sign": 2}[kind]
        br = [chain() for _ in range(nb)]
        def which(x):
            return 0 if kind == "none" else (int(x >= cut) if kind == "cut" else PRED[kind](x))
        xs = R.sample(range(-40, 121), 14)
        try:
            ys = [run(br[which(x)], x) for x in xs]
        except Exception:
            continue
        if max(abs(y) for y in ys) >= 10 ** 6 or ys[12] == ys[13] or len(set(ys[:12])) < 6:
            continue
        if kind != "none" and len(set(which(x) for x in xs[:12])) < nb:
            continue                                       # every branch shows in the examples
        return kind, xs[:12], ys[:12], xs[12:], ys[12:]


def text(tid, ex, ys, qs):
    pairs = "; ".join("x = %d -> y = %d" % (x, y) for x, y in zip(ex, ys))
    return ("Task %s. A hidden rule turns an integer x into an integer y. Examples: %s. What is y for x = %d, and for "
            "x = %d? Answer with the two integers in that order, or answer CANNOT if no single rule can be determined "
            "from the examples." % (tid, pairs, qs[0], qs[1]))


if __name__ == "__main__":
    mode, n = sys.argv[1], int(sys.argv[2])
    items = []
    for i in range(n):
        if R.random() < 0.15:
            xs = R.sample(range(-40, 121), 14)
            items.append(("trap", xs[:12], [R.randint(-500, 500) for _ in range(12)], xs[12:], "CANNOT"))
        else:
            k, ex, ys, qs, ans = draw_rule()
            items.append((k, ex, ys, qs, ans))
    if mode == "design":
        json.dump([dict(id="S%04d" % i, kind=k, data=dict(kind="rule", pairs=[[a, b] for a, b in zip(ex, ys)], queries=qs),
                        truth=ans) for i, (k, ex, ys, qs, ans) in enumerate(items)], open("design.json", "w"))
        print("design: %d items" % len(items), {k: sum(1 for it in items if it[0] == k) for k in ("none", "cut", "parity", "mod3", "sign", "trap")})
    else:
        json.dump([dict(id="T%02d" % (i + 1), text=text("T%02d" % (i + 1), ex, ys, qs)) for i, (k, ex, ys, qs, ans) in enumerate(items)],
                  open("problems.json", "w"), indent=1)
        json.dump({"T%02d" % (i + 1): ans for i, (k, ex, ys, qs, ans) in enumerate(items)}, open("sealed.json", "w"))
        os.chmod("sealed.json", 0o400)
        print("test battery: %d problems; answers sealed (not printed)" % len(items))
