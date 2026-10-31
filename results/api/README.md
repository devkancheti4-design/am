# AM as a tool on the Gemini API: real tokens, real money

This test checks whether a model should reason about a hidden integer rule itself, or only lay out the data and let AM
find the rule.

- **Problems:** 60 fresh sealed problems (seed 2029): rules and sequences, plus multi-branch rules. 12 of them are
  traps with no single rule, where "can't" is the right answer. The texts are in `fresh/items.json`. The truths are in
  `fresh/sealed.json` (sha256 `ee7c04d8…`, as in the protocol).
- **Arms:**
  - **A:** the model reasons alone, with high thinking.
  - **T:** the model only lays the data out as options for AM (low thinking), and AM decides locally, for 0 tokens.
- **Prices:** paid tier, at Google's list prices. The protocol was sealed before any call: `GEMINI_PROTOCOL.txt` and its
  addenda; check them with `shasum -a 256 -c GEMINI_PROTOCOL.sha256`.

| Model | Arm | Score | Right | Wrong | Can't | $ per problem | Cheaper |
|---|---|---|---|---|---|---|---|
| Gemini 3.5 Flash-Lite | A | 35 | 40 | 5 | 27 | 0.01811 | |
| Gemini 3.5 Flash-Lite | **T** | **41** | 49 | 8 | 15 | **0.00034** | **53.5x** |
| Gemini 3.8 Flash | A | 35 | 40 | 5 | 21 | 0.07829 | |
| Gemini 3.8 Flash | **T** | **41** | 49 | 8 | 15 | **0.00064** | **122.5x** |
| Gemini 4 Argon | A | 36 | 37 | 1 | 28 | 0.10294 | |
| Gemini 4 Argon | **T** | **41** | 49 | 8 | 15 | **0.00173** | **59.4x** |

Score = right − wrong. Per million problems, T saves $17.8k, $77.7k and $101.2k.

**Read it honestly:**
- **Accuracy:** T's higher score is not significant (sign test p = 0.33–0.38), and T gave more wrong answers (8 vs 1–5).
- **CPU time:** AM's own CPU time, about 25–30 s per problem in Python on a laptop, is not in the dollars.
- **Real bill:** Google's charge matched the computed spend to 98% (`real_charge.redacted.txt`).

**Reproduce the table:**

```bash
python3 -I results/api/geminitest.py report
```

**Files:**
- `gemini_runs.json` holds every call (tokens, answers, options), and `gemini_run.log` is the run log.
- `apitest.py`, `tokentest.py` and `geminitest.py` are the test code, with local paths made relative.
- `PROTOCOL.redacted.txt` is the base protocol: a redacted copy whose sealed hash belongs to the private original.
