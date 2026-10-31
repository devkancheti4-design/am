"""AM as a tool on the Gemini API: real tokens and real money (GEMINI_PROTOCOL.txt + GEMINI_ADDENDUM1.txt: the classic generate_content endpoint).
    .venv/bin/python -I -u geminitest.py smoke     one call per arm on problem 1; prints raw usage and steps
    .venv/bin/python -I -u geminitest.py run       resumable and spend-capped; writes gemini_runs.json
    .venv/bin/python -I geminitest.py report"""
import json, os, sys, time, threading, hashlib
from concurrent.futures import ThreadPoolExecutor
from math import comb

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "python"))
import tokentest as TT
from apitest import am_tool, SUPPLY_ASK, AM_TOOL

MODELS = [("gemini-3.5-flash-lite", 0.30, 2.50), ("gemini-3.8-flash", 0.75, 3.75), ("gemini-4-argon", 2.00, 10.00)]
CAP = 25.00
RUNS = os.path.join(HERE, "gemini_runs.json")
AM_FN = {"type": "function", "name": AM_TOOL["name"], "description": AM_TOOL["description"],
         "parameters": AM_TOOL["input_schema"]}
LOCK = threading.Lock()


def _http():
    from google.genai import types
    return types.HttpOptions(timeout=900000, retry_options=types.HttpRetryOptions(attempts=3))


def usage(resp):
    """GEMINI_ADDENDUM1.txt: input = prompt + tool-use prompt; billed output = candidates + thoughts"""
    u = resp.usage_metadata
    g = lambda k: int(getattr(u, k, 0) or 0)
    tin = g("prompt_token_count") + g("tool_use_prompt_token_count")
    out, tth = g("candidates_token_count"), g("thoughts_token_count")
    return dict(tin=tin, tout=out + tth, raw_out=out, thought=tth, total=g("total_token_count"))


def call_alone(client, model, text):
    from google.genai import types
    t0 = time.time()
    r = client.models.generate_content(model=model, contents=text + TT.ALONE, config=types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_level="high"), max_output_tokens=32000))
    return dict(usage(r), text=r.text or "", secs=round(time.time() - t0, 1), tool_calls=0, am_cpu=0.0)


def call_supply(client, model, text):
    from google.genai import types
    t0 = time.time()
    fn = types.FunctionDeclaration(name=AM_TOOL["name"], description=AM_TOOL["description"],
                                   parameters_json_schema=AM_TOOL["input_schema"])
    r = client.models.generate_content(model=model, contents=text + SUPPLY_ASK, config=types.GenerateContentConfig(
        tools=[types.Tool(function_declarations=[fn])],
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        thinking_config=types.ThinkingConfig(thinking_level="low"), max_output_tokens=4000))
    options = [dict(c.args or {}) for c in (r.function_calls or []) if c.name == "am_solve"]
    it = r
    c0 = time.time()
    outs = [am_tool(o) for o in options]
    cpu = time.time() - c0
    answers = {json.dumps(o["answer"]) for o in outs if "answer" in o and o["answer"] != "CANNOT"}
    final = json.loads(answers.pop()) if len(answers) == 1 else "CANNOT"
    return dict(usage(it), text="", forced=final, options=options, secs=round(time.time() - t0, 1),
                tool_calls=len(options), am_cpu=round(cpu, 2))


def load():
    return {(r["model"], r["arm"], r["id"]): r for r in json.load(open(RUNS))} if os.path.exists(RUNS) else {}


def spent(done):
    return sum(r["usd"] for r in done.values())


def smoke():
    from google import genai
    client = genai.Client(http_options=_http())
    it0 = TT.pick()[0]
    model = MODELS[0][0]
    for name, fn in (("T supply", call_supply), ("A alone", call_alone)):
        r = fn(client, model, TT.render(it0))
        print(name, json.dumps({k: v for k, v in r.items() if k != "text"}, default=str)[:600])
        print("   text tail:", repr(r.get("text", "")[-160:]))


def run():
    from google import genai
    client = genai.Client(http_options=_http())
    P = TT.pick()
    done = load()
    print("protocol", open(os.path.join(HERE, "GEMINI_PROTOCOL.sha256")).read().split()[0][:16],
          "| %d problems, %d records, spent $%.4f of $%.2f" % (len(P), len(done), spent(done), CAP), flush=True)
    for model, pin, pout in MODELS:
        for arm, fn, worst_out in (("T", call_supply, 4000), ("A", call_alone, 32000)):
            todo = [it for it in P if (model, arm, it["id"]) not in done]

            def one(it):
                with LOCK:
                    if spent(done) + (3000 * pin + worst_out * pout) / 1e6 > CAP:
                        return None
                try:
                    res, err = fn(client, model, TT.render(it)), None
                except Exception as e:                       # an API error is recorded as no answer, never skipped
                    res, err = dict(tin=0, tout=0, raw_out=0, thought=0, total=0, text="", secs=0, tool_calls=0,
                                    am_cpu=0.0), repr(e)[:200]
                usd = (res["tin"] * pin + res["tout"] * pout) / 1e6
                rec = dict(res, model=model, arm=arm, id=it["id"], set=it["set"], usd=usd, error=err,
                           answer=res["forced"] if "forced" in res else TT.parse(res["text"]), tail=res["text"][-200:])
                with LOCK:
                    done[(model, arm, it["id"])] = rec
                    json.dump(list(done.values()), open(RUNS, "w"), indent=1)
                print("%-22s %s %s in %6d out %6d (thought %6d) $%.5f %5.1fs options %d%s" % (
                    model, arm, it["id"], res["tin"], res["tout"], res["thought"], usd, res["secs"], res["tool_calls"],
                    (" ERROR " + err) if err else ""), flush=True)
                return rec

            with ThreadPoolExecutor(3) as ex:
                out = list(ex.map(one, todo))
            if any(o is None for o in out):
                print("SPEND CAP reached: stopped at %s arm %s" % (model, arm), flush=True)
                return
    print("all runs done; computed spend $%.4f" % spent(done), flush=True)


def report():
    fs = os.path.join(HERE, "fresh", "sealed.json")
    assert hashlib.sha256(open(fs, "rb").read()).hexdigest().startswith("ee7c04d8"), "fresh seal changed"
    T = json.load(open(fs))
    done = load()
    P = TT.pick()
    sc = lambda a, t: 1 if TT.ok(a, t) else (0 if a in ("CANNOT", None) else -1)
    print("AM as a tool on the Gemini API: %d problems (%d traps); paid list prices; computed spend $%.4f"
          % (len(P), sum(T[it["id"]] == "CANNOT" for it in P), spent(done)))
    print("%-22s %-3s %5s %5s %5s %6s %6s | %8s %8s | %10s %10s | %6s" % (
        "model", "arm", "score", "right", "wrong", "CANNOT", "no ans", "tok in", "tok out", "$/problem", "$/right", "s/prob"))
    for model, _, _ in MODELS:
        arms = {}
        for arm in ("A", "T"):
            R = [done.get((model, arm, it["id"])) for it in P]
            if any(r is None for r in R):
                continue
            s = [sc(r["answer"], T[r["id"]]) for r in R]
            usd, right = sum(r["usd"] for r in R), sum(x == 1 for x in s)
            arms[arm] = dict(s=s, usd=usd)
            print("%-22s %-3s %5d %5d %5d %6d %6d | %8.0f %8.0f | %10.5f %10s | %6.1f" % (
                model, arm, sum(s), right, sum(x == -1 for x in s), sum(r["answer"] == "CANNOT" for r in R),
                sum(r["answer"] is None for r in R), sum(r["tin"] for r in R) / len(R), sum(r["tout"] for r in R) / len(R),
                usd / len(R), "%.5f" % (usd / right) if right else "-", sum(r["secs"] for r in R) / len(R)))
        if "A" in arms and "T" in arms:
            a, t = arms["A"], arms["T"]
            better = sum(p > q for p, q in zip(t["s"], a["s"]))
            worse = sum(p < q for p, q in zip(t["s"], a["s"]))
            n = better + worse
            p = 1.0 if n == 0 else min(1.0, 2 * sum(comb(n, i) for i in range(min(better, worse) + 1)) / 2 ** n)
            save = (a["usd"] - t["usd"]) / len(P)
            print("   AM decides: saves $%.5f per problem = $%s per 1,000,000 problems (%.1fx cheaper); accuracy: "
                  "T better on %d, worse on %d, p = %.3g" % (save, format(round(save * 1e6), ","),
                                                           a["usd"] / t["usd"] if t["usd"] else float("inf"), better, worse, p))


if __name__ == "__main__":
    {"smoke": smoke, "run": run, "report": report}[sys.argv[1]]()
