"""AM as the core-reasoning API: the token test (PROTOCOL.txt, sha256 in PROTOCOL.sha256).
Every arm gets the same 60 fresh sealed problems.  The model is qwen3.5:4b through Ollama on this Mac, and the token
counts are Ollama's own.
    python3 -I -u tokentest.py run      (resumable; writes runs.json, one record per problem)
    python3 -I tokentest.py report      (reads the truths only here)"""
import json, os, re, sys, time, random, ctypes, hashlib, urllib.request
from math import comb

HERE = os.path.dirname(os.path.abspath(__file__))
AM2 = HERE                       # ./fresh holds the sealed set; the AM2 library is not in this repository
sys.path.insert(0, AM2)
OLLAMA = "http://localhost:11434/api/chat"
MODEL = "qwen3.5:4b"
ALONE = ("\n\nThink it through, then give the final answer on the last line exactly as\nANSWER: <first>, <second>\n"
         "or\nANSWER: CANNOT")                                     # verbatim from reason/duel/body.py
EXTRACT = ("\n\nDo not solve it. Copy its data into JSON and reply with only the JSON: for a rule task "
           '{"kind": "rule", "pairs": [[x, y], ...], "queries": [first x, second x]}; for a sequence task '
           '{"kind": "sequence", "terms": [...]}.')                 # verbatim from reason/duel/body.py
RUNS = os.path.join(HERE, "runs.json")


def text_f(tid, ex, ys, qs):                                       # verbatim from brain/gen_design.py (= gen_split's text)
    pairs = "; ".join("x = %d -> y = %d" % (x, y) for x, y in zip(ex, ys))
    return ("Task %s. A hidden rule turns an integer x into an integer y. Examples: %s. What is y for x = %d, and for "
            "x = %d? Answer with the two integers in that order, or answer CANNOT if no single rule can be determined "
            "from the examples." % (tid, pairs, qs[0], qs[1]))


def text_s(tid, a):                                                # verbatim from brain/gen_design.py
    return ("Task %s. A hidden law produces the sequence %s. What are the next two terms? Answer with the two integers "
            "in order, or answer CANNOT if no single law can be determined from the terms." % (tid, ", ".join(map(str, a))))


def render(item):
    d = item["data"]
    if d["kind"] == "sequence":
        return text_s(item["id"], d["terms"])
    return text_f(item["id"], [p[0] for p in d["pairs"]], [p[1] for p in d["pairs"]], d["queries"])


def pick():
    items = json.load(open(os.path.join(AM2, "fresh", "items.json")))
    rng = random.Random(2029)
    out = []
    for s in ("fresh_rules", "fresh_split"):
        ids = sorted(i["id"] for i in items if i["set"] == s)
        out += sorted(rng.sample(ids, 30))
    by = {i["id"]: i for i in items}
    return [by[i] for i in out]


def chat(content, think, cap, sampling):
    body = dict(model=MODEL, messages=[{"role": "user", "content": content}], stream=False, think=think,
                options=dict(num_predict=cap, seed=0, **sampling))
    req = urllib.request.Request(OLLAMA, json.dumps(body).encode(), {"Content-Type": "application/json"})
    t0 = time.time()
    r = json.load(urllib.request.urlopen(req, timeout=7200))
    m = r.get("message") or {}
    return dict(content=m.get("content") or "", thinking_chars=len(m.get("thinking") or ""),
                tin=r.get("prompt_eval_count", 0), tout=r.get("eval_count", 0), secs=round(time.time() - t0, 1),
                done=r.get("done_reason"))


def parse_strict(reply):                                           # the original regex, for comparison only
    m = re.findall(r"ANSWER:\s*(CANNOT|-?\d+\s*,\s*-?\d+)", reply.replace("*", ""))
    return "CANNOT" if m and m[-1] == "CANNOT" else ([int(v) for v in m[-1].split(",")] if m else None)


def parse(reply):
    boxed = re.findall(r"\\boxed\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}", reply)
    s = reply
    for t in ("*", "$", "\\text{", "\\boxed{", "}"):
        s = s.replace(t, "")
    m = re.findall(r"ANSWER:\s*(CANNOT|-?\d+\s*,\s*-?\d+)", s, flags=re.I)
    if m:
        return "CANNOT" if m[-1].upper() == "CANNOT" else [int(v) for v in m[-1].split(",")]
    for b in reversed(boxed):
        if "CANNOT" in b.upper():
            return "CANNOT"
        nums = re.findall(r"-?\d+", b)
        if len(nums) == 2:
            return [int(v) for v in nums]
    singles = [re.findall(r"-?\d+", b) for b in boxed]
    singles = [int(n[0]) for n in singles if len(n) == 1]
    return singles[-2:] if len(singles) >= 2 else None


def reason(item_set, data):
    import eyes
    import law24
    lib = ctypes.CDLL(os.path.join(AM2, "libam2.so"))
    lib.am2.restype, lib.am2.argtypes = ctypes.c_int32, [ctypes.c_int32]
    t0 = time.time()
    try:
        row = eyes.summarise((dict(id="x", set=item_set, data=data), None, None))
    except Exception as e:
        return dict(old_AM="CANNOT", AM2="CANNOT", plain="CANNOT", error=repr(e)[:120]), round(time.time() - t0, 2)
    if row["kind"] is None:
        return dict(old_AM="CANNOT", AM2="CANNOT", plain="CANNOT"), round(time.time() - t0, 2)
    split = item_set.endswith("split")
    m = lib.am2(row["n24"])
    return (dict(old_AM=row["old_split"] if split else row["old_am"], AM2=law24.pred(row, m) if m else "CANNOT",
                 plain=row["S2"] if split else row["B"]), round(time.time() - t0, 2))


def run():
    P = pick()
    done = {r["id"]: r for r in json.load(open(RUNS))} if os.path.exists(RUNS) else {}
    print("protocol", open(os.path.join(HERE, "PROTOCOL.sha256")).read().split()[0][:16], "| %d problems, %d done"
          % (len(P), len(done)), flush=True)
    for k, it in enumerate(P, 1):
        if it["id"] in done:
            continue
        txt = render(it)
        body = chat(txt + EXTRACT, False, 1024, dict(temperature=0.0))
        s = body["content"]
        try:
            data = json.loads(s[s.find("{"): s.rfind("}") + 1])
        except Exception:
            data = None
        ans, cpu = reason(it["set"], data)
        nothink = chat(txt + ALONE, False, 1024, dict(temperature=0.0))
        alone = chat(txt + ALONE, True, 16384, dict(temperature=0.6, top_p=0.95, top_k=20))
        rec = dict(id=it["id"], set=it["set"], body=dict(body, data_ok=data is not None, data_exact=data == it["data"]),
                   reasoners=ans, reasoner_cpu=cpu,
                   nothink=dict(nothink, answer=parse(nothink["content"]), strict=parse_strict(nothink["content"]),
                                tail=nothink["content"][-200:]),
                   alone=dict(alone, answer=parse(alone["content"]), strict=parse_strict(alone["content"]),
                              tail=alone["content"][-200:]))
        done[it["id"]] = rec
        json.dump(list(done.values()), open(RUNS, "w"), indent=1)
        print("%2d %s %-11s body %4d tok %4.1fs | nothink %5d tok | alone %6d tok %6.1fs (%s)" % (
            k, it["id"], it["set"], body["tin"] + body["tout"], body["secs"], nothink["tin"] + nothink["tout"],
            alone["tin"] + alone["tout"], alone["secs"], alone["done"]), flush=True)


def ok(got, want):                                                 # verbatim from splitter/grade_split.py
    return (got == "CANNOT") if want == "CANNOT" else (isinstance(got, list) and got == list(want))


def report():
    fs = os.path.join(AM2, "fresh", "sealed.json")
    assert hashlib.sha256(open(fs, "rb").read()).hexdigest().startswith("ee7c04d8"), "fresh seal changed"
    T = json.load(open(fs))
    R = json.load(open(RUNS))
    arms = {"A  Qwen alone, thinking": lambda r: (r["alone"]["answer"], r["alone"]),
            "A' same, original parser": lambda r: (r["alone"]["strict"], r["alone"]),
            "N  Qwen alone, no thinking": lambda r: (r["nothink"]["answer"], r["nothink"]),
            "B-AM   body + old AM": lambda r: (r["reasoners"]["old_AM"], r["body"]),
            "B-AM2  body + AM2": lambda r: (r["reasoners"]["AM2"], r["body"]),
            "B-plain body + plain search": lambda r: (r["reasoners"]["plain"], r["body"])}

    def sc(a, t):
        return 1 if ok(a, t) else (0 if a in ("CANNOT", None) else -1)

    print("%d problems (%d rules/sequences, %d multi-branch), %d traps; model %s on this Mac"
          % (len(R), sum(r["set"] == "fresh_rules" for r in R), sum(r["set"] == "fresh_split" for r in R),
             sum(T[r["id"]] == "CANNOT" for r in R), MODEL))
    print("%-28s %5s %5s %5s %6s %6s | %8s %8s %8s | %7s | %9s" % ("arm", "score", "right", "wrong", "CANNOT", "no ans",
          "tok in", "tok out", "tok tot", "s/prob", "tok/right"))
    res = {}
    for name, f in arms.items():
        s = [sc(f(r)[0], T[r["id"]]) for r in R]
        right = sum(x == 1 for x in s)
        tin = sum(f(r)[1]["tin"] for r in R)
        tout = sum(f(r)[1]["tout"] for r in R)
        secs = sum(f(r)[1]["secs"] for r in R)
        res[name] = dict(score=sum(s), right=right, scores=s, tok=tin + tout)
        print("%-28s %5d %5d %5d %6d %6d | %8.0f %8.0f %8.0f | %7.1f | %9s" % (
            name, sum(s), right, sum(x == -1 for x in s), sum(f(r)[0] == "CANNOT" for r in R),
            sum(f(r)[0] is None for r in R), tin / len(R), tout / len(R), (tin + tout) / len(R), secs / len(R),
            "%.0f" % ((tin + tout) / right) if right else "-"))
    cpu = sum(r["reasoner_cpu"] for r in R) / len(R)
    a = res["A  Qwen alone, thinking"]
    for b in ("B-AM   body + old AM", "B-AM2  body + AM2", "B-plain body + plain search"):
        x = res[b]
        better = sum(p > q for p, q in zip(x["scores"], a["scores"]))
        worse = sum(p < q for p, q in zip(x["scores"], a["scores"]))
        n = better + worse
        p = 1.0 if n == 0 else min(1.0, 2 * sum(comb(n, i) for i in range(min(better, worse) + 1)) / 2 ** n)
        print("%s vs A: tokens %.1fx fewer (%.0f saved per problem); scores better on %d, worse on %d, p = %.3g -> %s"
              % (b.strip(), a["tok"] / x["tok"], (a["tok"] - x["tok"]) / len(R), better, worse, p,
                 "MATCHES OR BEATS A" if better >= worse else "BELOW A"))
    print("AM's own work: %.2f s of CPU per problem, 0 tokens; body JSON parsed %d/%d, exact %d/%d"
          % (cpu, sum(r["body"]["data_ok"] for r in R), len(R), sum(r["body"]["data_exact"] for r in R), len(R)))


if __name__ == "__main__":
    {"run": run, "report": report}[sys.argv[1]]()
