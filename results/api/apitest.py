"""AM as a tool on the Claude API: real tokens and real dollars (API_PROTOCOL.txt + API_ADDENDUM1.txt; arm T = T-SUPPLY: Claude supplies, AM decides).
    .venv/bin/python -I -u apitest.py dry      the tool alone on the 60 problems' true data (no API call)
    .venv/bin/python -I -u apitest.py run      resumable and spend-capped; writes api_runs.json
    .venv/bin/python -I apitest.py report"""
import json, os, sys, time, threading, hashlib
from concurrent.futures import ThreadPoolExecutor
from math import comb

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "python"))
import tokentest as TT

MODELS = [("claude-haiku-5-5", 0.10, 0.50), ("claude-sonnet-5-5", 2.00, 10.00), ("claude-opus-5-5", 4.00, 20.00)]
CAP = 25.00
RUNS = os.path.join(HERE, "api_runs.json")
TOOL_ASK = ("\n\nUse the am_solve tool: pass it this task's data exactly as given. Then give the final answer on the "
            "last line exactly as\nANSWER: <first>, <second>\nor\nANSWER: CANNOT")
AM_TOOL = {
    "name": "am_solve",
    "description": ("Exact reasoner for integer rule and sequence tasks. Give it the task's examples; it finds the rule "
                    "behind them and answers the questions, or returns CANNOT when no single rule can be determined."),
    "input_schema": {"type": "object", "properties": {
        "kind": {"type": "string", "enum": ["rule", "sequence"]},
        "pairs": {"type": "array", "items": {"type": "array", "items": {"type": "integer"}},
                  "description": "rule tasks: every example as [x, y]"},
        "queries": {"type": "array", "items": {"type": "integer"}, "description": "rule tasks: the x values asked about"},
        "terms": {"type": "array", "items": {"type": "integer"}, "description": "sequence tasks: the terms in order"}},
        "required": ["kind"]}}
LOCK = threading.Lock()


def am_tool(inp):
    import am
    try:
        if inp["kind"] == "sequence":
            data = {"kind": "sequence", "terms": [int(v) for v in inp["terms"]]}
        else:
            data = {"kind": "rule", "pairs": [[int(a), int(b)] for a, b in inp["pairs"]],
                    "queries": [int(q) for q in inp["queries"]]}
        a = am.answer(data)
        if a == "CANNOT" and data["kind"] == "rule":
            a = am.answer_split(data)
        return {"answer": a}
    except Exception as e:
        return {"error": repr(e)[:200]}


def load():
    return {(r["model"], r["arm"], r["id"]): r for r in json.load(open(RUNS))} if os.path.exists(RUNS) else {}


def spent(done):
    return sum(r["usd"] for r in done.values())


def call_alone(client, model, text):
    t0 = time.time()
    with client.messages.stream(model=model, max_tokens=32000, output_config={"effort": "high"},
                                messages=[{"role": "user", "content": text + TT.ALONE}]) as s:
        r = s.get_final_message()
    return dict(text="".join(b.text for b in r.content if b.type == "text"), tin=r.usage.input_tokens,
                tout=r.usage.output_tokens, secs=round(time.time() - t0, 1), stop=r.stop_reason, tool_calls=0, am_cpu=0.0)


SUPPLY_ASK = ("\n\nDo not solve the task. Lay out its data as am_solve calls: one call, or one per reading if the text "
              "can be read more than one way. Do not answer.")


def call_supply(client, model, text):
    """ARM T-SUPPLY (API_ADDENDUM1.txt): one request; Claude's tool calls are the options; AM alone decides"""
    t0 = time.time()
    r = client.messages.create(model=model, max_tokens=4000, output_config={"effort": "low"}, tools=[AM_TOOL],
                               messages=[{"role": "user", "content": text + SUPPLY_ASK}])
    options = [b.input for b in r.content if b.type == "tool_use"]
    c0 = time.time()
    outs = [am_tool(o) for o in options]
    cpu = time.time() - c0
    answers = {json.dumps(o["answer"]) for o in outs if "answer" in o and o["answer"] != "CANNOT"}
    final = json.loads(answers.pop()) if len(answers) == 1 else "CANNOT"
    return dict(text="", forced=final, options=options, tin=r.usage.input_tokens, tout=r.usage.output_tokens,
                secs=round(time.time() - t0, 1), stop=r.stop_reason, tool_calls=len(options), am_cpu=round(cpu, 2))


def run():
    import anthropic
    client = anthropic.Anthropic()
    P = TT.pick()
    done = load()
    print("protocol", open(os.path.join(HERE, "API_PROTOCOL.sha256")).read().split()[0][:16],
          "| %d problems, %d records, spent so far $%.4f of $%.2f" % (len(P), len(done), spent(done), CAP), flush=True)
    for model, pin, pout in MODELS:
        for arm, fn, worst_out, worst_calls in (("T", call_supply, 4000, 1), ("A", call_alone, 32000, 1)):
            todo = [it for it in P if (model, arm, it["id"]) not in done]

            def one(it):
                worst = worst_calls * (3000 * pin + worst_out * pout) / 1e6
                with LOCK:
                    if spent(done) + worst > CAP:
                        return None
                try:
                    res = fn(client, model, TT.render(it))
                    err = None
                except anthropic.APIStatusError as e:
                    res, err = dict(text="", tin=0, tout=0, secs=0, stop="error", tool_calls=0, am_cpu=0.0), "%s %s" % (
                        e.status_code, str(e.message)[:160])
                except anthropic.APIConnectionError as e:
                    res, err = dict(text="", tin=0, tout=0, secs=0, stop="error", tool_calls=0, am_cpu=0.0), repr(e)[:160]
                usd = (res["tin"] * pin + res["tout"] * pout) / 1e6
                rec = dict(res, model=model, arm=arm, id=it["id"], set=it["set"], usd=usd, error=err,
                           answer=res["forced"] if "forced" in res else TT.parse(res["text"]), tail=res["text"][-200:])
                with LOCK:
                    done[(model, arm, it["id"])] = rec
                    json.dump(list(done.values()), open(RUNS, "w"), indent=1)
                print("%-18s %s %s in %6d out %6d $%.4f %5.1fs calls %d %s%s" % (
                    model, arm, it["id"], res["tin"], res["tout"], usd, res["secs"], res["tool_calls"], res["stop"],
                    (" ERROR " + err) if err else ""), flush=True)
                return rec

            with ThreadPoolExecutor(3) as ex:
                out = list(ex.map(one, todo))
            if any(o is None for o in out):
                print("SPEND CAP reached: stopped before %s arm %s finished" % (model, arm), flush=True)
                return
    print("all runs done; total spent $%.4f" % spent(done), flush=True)


def dry():
    P = TT.pick()
    rows = []
    for it in P:
        d = it["data"]
        inp = dict(kind=d["kind"], terms=d.get("terms"), pairs=d.get("pairs"), queries=d.get("queries"))
        t0 = time.time()
        rows.append((it["id"], am_tool(inp), round(time.time() - t0, 1)))
    T = json.load(open(os.path.join(HERE, "fresh", "sealed.json")))
    right = sum(TT.ok(r[1].get("answer"), T[r[0]]) for r in rows)
    print("tool on true data: %d / %d right, %.1f s CPU per problem, errors %d"
          % (right, len(rows), sum(r[2] for r in rows) / len(rows), sum("error" in r[1] for r in rows)))


def report():
    fs = os.path.join(HERE, "fresh", "sealed.json")
    assert hashlib.sha256(open(fs, "rb").read()).hexdigest().startswith("ee7c04d8"), "fresh seal changed"
    T = json.load(open(fs))
    done = load()
    P = TT.pick()
    sc = lambda a, t: 1 if TT.ok(a, t) else (0 if a in ("CANNOT", None) else -1)
    print("AM as a tool on the Claude API: %d problems (%d traps); list prices; spend $%.4f"
          % (len(P), sum(T[it["id"]] == "CANNOT" for it in P), spent(done)))
    print("%-18s %-4s %5s %5s %5s %6s %6s | %8s %8s | %10s %10s | %6s | %5s" % (
        "model", "arm", "score", "right", "wrong", "CANNOT", "no ans", "tok in", "tok out", "$/problem", "$/right",
        "s/prob", "calls"))
    for model, _, _ in MODELS:
        arms = {}
        for arm in ("A", "T"):
            R = [done.get((model, arm, it["id"])) for it in P]
            if any(r is None for r in R):
                continue
            s = [sc(r["answer"], T[r["id"]]) for r in R]
            usd = sum(r["usd"] for r in R)
            right = sum(x == 1 for x in s)
            arms[arm] = dict(s=s, usd=usd)
            print("%-18s %-4s %5d %5d %5d %6d %6d | %8.0f %8.0f | %10.5f %10s | %6.1f | %5.2f" % (
                model, arm, sum(s), right, sum(x == -1 for x in s), sum(r["answer"] == "CANNOT" for r in R),
                sum(r["answer"] is None for r in R), sum(r["tin"] for r in R) / len(R), sum(r["tout"] for r in R) / len(R),
                usd / len(R), "%.5f" % (usd / right) if right else "-", sum(r["secs"] for r in R) / len(R),
                sum(r["tool_calls"] for r in R) / len(R)))
        if "A" in arms and "T" in arms:
            a, t = arms["A"], arms["T"]
            better = sum(p > q for p, q in zip(t["s"], a["s"]))
            worse = sum(p < q for p, q in zip(t["s"], a["s"]))
            n = better + worse
            p = 1.0 if n == 0 else min(1.0, 2 * sum(comb(n, i) for i in range(min(better, worse) + 1)) / 2 ** n)
            save = (a["usd"] - t["usd"]) / len(P)
            print("   AM as a tool saves $%.5f per problem = $%s per 1,000,000 problems (%.1fx cheaper); "
                  "accuracy: T better on %d, worse on %d, p = %.3g" % (save, format(round(save * 1e6), ","),
                                                                     a["usd"] / t["usd"] if t["usd"] else float("inf"),
                                                                     better, worse, p))


if __name__ == "__main__":
    {"run": run, "dry": dry, "report": report}[sys.argv[1]]()
