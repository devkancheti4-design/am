"""THE SEALED BATTERY -- reasoning from given data, machine-drawn.
Rules are drawn from os.urandom: nobody, the author of this file included, knows them.  Writes
    problems.json   the texts every contestant sees (Claude, the body alone, the body + brain)
    sealed.json     the answers -- opened only by grade.py, after every contestant has committed
Families
    F  a hidden rule y = f(x) built from 2-5 basic-Python steps (+ - * // % & | ^ << >> abs min max, if x < c);
       8 examples; two questions, both must be right
    S  a sequence a(1..8) from a hidden law (linear recurrence, polynomial, growing difference, alternating);
       the next two terms, both must be right
    T  noise dressed as either of the above: the right answer is CANNOT
Every drawn rule is checked against the examples and must give distinct answers to the two questions, values stay
within |y| < 10^6, and a rule equal to a 1-step rule on the examples is redrawn (no trivial items)."""
import json
import os
import random

R = random.Random(int.from_bytes(os.urandom(8), "big"))
N_F, N_S, N_T = 18, 14, 6


def step():
    c = R.randint(2, 12)
    k = R.randint(1, 4)
    return R.choice([
        ("x + %d" % c, lambda x, c=c: x + c), ("x - %d" % c, lambda x, c=c: x - c), ("%d * x" % c, lambda x, c=c: c * x),
        ("x // %d" % c, lambda x, c=c: x // c), ("x %% %d" % c, lambda x, c=c: x % c), ("x & %d" % (c * 5), lambda x, c=c: x & (c * 5)),
        ("x | %d" % c, lambda x, c=c: x | c), ("x ^ %d" % c, lambda x, c=c: x ^ c), ("x << %d" % k, lambda x, k=k: x << k),
        ("x >> %d" % k, lambda x, k=k: x >> k), ("abs(x)", abs), ("max(x, %d)" % c, lambda x, c=c: max(x, c)),
        ("min(x, %d)" % (c * 3), lambda x, c=c: min(x, c * 3)), ("x * x", lambda x: x * x)])


def draw_f():
    while True:
        n = R.randint(2, 5)
        steps = [step() for _ in range(n)]
        piece = R.random() < 0.25
        cut = R.randint(-10, 40)
        alt = [step() for _ in range(R.randint(1, 2))]

        def f(x, steps=steps, piece=piece, cut=cut, alt=alt):
            seq = alt if (piece and x < cut) else steps
            for _, g in seq:
                x = g(x)
            return x
        xs = sorted(R.sample(range(-30, 120), 10))
        ex, qs = xs[:8], xs[8:]
        R.shuffle(ex)
        try:
            ys = [f(x) for x in ex + qs]
        except Exception:
            continue
        if max(abs(y) for y in ys) >= 10 ** 6 or ys[8] == ys[9] or len(set(ys[:8])) < 4:
            continue
        if any(all(g(x) == y for x, y in zip(ex, ys[:8])) for _ in range(40) for _, g in [step()]):
            continue
        return ex, ys[:8], qs, ys[8:]


def draw_s():
    while True:
        kind = R.choice(["rec2", "poly", "diff", "alt"])
        a = []
        if kind == "rec2":
            p, q, r = R.randint(-2, 3), R.randint(-2, 2), R.randint(-5, 5)
            a = [R.randint(-5, 9), R.randint(-5, 9)]
            while len(a) < 10:
                a.append(p * a[-1] + q * a[-2] + r)
        elif kind == "poly":
            c2, c1, c0 = R.randint(-3, 4), R.randint(-6, 6), R.randint(-9, 9)
            c3 = R.choice([0, 0, 1, -1])
            a = [c3 * n ** 3 + c2 * n * n + c1 * n + c0 for n in range(1, 11)]
        elif kind == "diff":
            a = [R.randint(-9, 9)]
            d, dd = R.randint(-4, 6), R.randint(1, 5)
            while len(a) < 10:
                a.append(a[-1] + d); d += dd
        else:
            m, s = R.randint(2, 4), R.randint(1, 9)
            a = [R.randint(1, 6)]
            for i in range(9):
                a.append(a[-1] * m if i % 2 == 0 else a[-1] - s)
        if max(abs(v) for v in a) < 10 ** 6 and len(set(a[:8])) >= 5 and a[8] != a[9]:
            return a[:8], a[8:]


def text_f(tid, ex, ys, qs):
    pairs = "; ".join("x = %d -> y = %d" % (x, y) for x, y in zip(ex, ys))
    return ("Task %s. A hidden rule turns an integer x into an integer y. Examples: %s. What is y for x = %d, and for "
            "x = %d? Answer with the two integers in that order, or answer CANNOT if no single rule can be determined "
            "from the examples." % (tid, pairs, qs[0], qs[1]))


def text_s(tid, a):
    return ("Task %s. A hidden law produces the sequence %s. What are the next two terms? Answer with the two integers "
            "in order, or answer CANNOT if no single law can be determined from the terms." % (tid, ", ".join(map(str, a))))


items, sealed = [], {}
for i in range(N_F):
    ex, ys, qs, ans = draw_f(); items.append(("F", ex, ys, qs)); sealed[len(items) - 1] = ans
for i in range(N_S):
    a, ans = draw_s(); items.append(("S", a)); sealed[len(items) - 1] = ans
for i in range(N_T):
    if R.random() < 0.5:
        xs = sorted(R.sample(range(-30, 120), 10)); ex = xs[:8]; R.shuffle(ex)   # shuffled exactly like a real item
        ys = [R.randint(-500, 500) for _ in range(8)]
        items.append(("F", ex, ys, xs[8:]))
    else:
        items.append(("S", [R.randint(-300, 300) for _ in range(8)]))
    sealed[len(items) - 1] = "CANNOT"
order = list(range(len(items)))
R.shuffle(order)
problems, seal = [], {}
for k, j in enumerate(order):
    tid = "R%02d" % (k + 1)
    it = items[j]
    problems.append(dict(id=tid, text=text_f(tid, it[1], it[2], it[3]) if it[0] == "F" else text_s(tid, it[1])))
    seal[tid] = sealed[j]
json.dump(problems, open("problems.json", "w"), indent=1)
json.dump(seal, open("sealed.json", "w"))
os.chmod("sealed.json", 0o400)
print("battery: %d problems written to problems.json; answers sealed in sealed.json (not printed)" % len(problems))
