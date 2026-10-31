# Coding: AM and its law as a self-improving harness

Here AM works as a **harness around an API model**. The model writes the code, and the harness never reads the code or
the problem text. It reads only the **situation** of the work and rules the next act:
- whether an answer passes the visible samples (BUILT, REFUTED);
- whether the answers agree (AMB);
- whether the answer is valid code (NOTWIN);
- whether it was cut off (CAPPED).

The acts are:
- **SHIP:** send out the current answer.
- **HARVEST_COUNTEREXAMPLE:** show the model the samples it fails and ask it to fix them.
- **RESHAPE:** ask for complete code.
- **RAISE_BUDGET:** give the model more thinking tokens.
- **ADD_STATE:** ask for a new answer from a different view.

The controller is a machine-authored law (integer program synthesis), authored once from 22 measured events. Every run
was sealed before it ran and judged once, on hidden tests nobody saw during the run.

## HumanEval+ (164 tasks, live): `humaneval/`

| Arm | Solved | Output tokens per task |
|---|---|---|
| Gemini 3.5 Flash-Lite alone, high thinking | 162 | 1,268 |
| **Harness + Gemini** (low thinking first; CAPPED → RAISE_BUDGET) | **161** | **452 (−64%)** |
| Gemini, low thinking (control) | 159 | 120 |

On an easy set the harness keeps the accuracy at about a third of the tokens. Two of its misses come from HumanEval's own
wrong docstring examples.

## LiveCodeBench v6 (174 contest problems, Jan–Apr 2025, live, $7.70): `lcb_final/`

| Arm | Solved | Easy (43) | Medium (52) | Hard (79) | Cost |
|---|---|---|---|---|---|
| Gemini 3.5 Flash-Lite alone, high thinking | 132 | 43 | 44 | 45 | $5.00 |
| **Harness + Gemini** | **140** | 43 | **47** | **50** | $6.69 |
| **AM over every answer** | **140** | 43 | **47** | **50** | $6.33 |
| Harness, cheap answer first | 123 | 43 | 42 | 38 | $3.56 |
| Gemini, low thinking (control) | 95 | 41 | 36 | 18 | $0.73 |

- **+8 problems, none lost** (sign test p ≈ 0.008), about 20 cents per extra solve.
- **How the 8 were won:**
  - In 7 of them, Gemini's first answer failed the problem's own samples and Gemini alone shipped it anyway. The law read BUILT + REFUTED and ruled HARVEST_COUNTEREXAMPLE, and the fixed answer passed all 40 hidden tests.
  - In the 8th, the first answer was not valid code, and the law ruled RESHAPE.

## amdev: AM reasons over the answers, the law steers (`amdev/`)

The run covered 173 of 174 problems, starting from Gemini alone's own first answer.

| Arm | Solved | Easy | Medium | Hard | Cost |
|---|---|---|---|---|---|
| Gemini alone (re-judged together) | 132 | 43 | 44 | 45 | $4.93 |
| **amdev** | **139** | 43 | **46** | **50** | $12.96 |

8 wins and 1 loss against Gemini alone (sign test p ≈ 0.04). The loss: two answers shared a subtle bug and outvoted the
correct one. AM cancels only the errors the models do not share.

## Limits

- **Contamination:** every model used is newer than the LiveCodeBench v6 problems.
- **Sampling:** n = 1 sample, not the leaderboard's 10.
- **Scaffold:** the harness uses the visible sample tests in its loop, so it counts as a scaffold, not plain generation.
- **Not an entry:** nothing here was submitted to any leaderboard.

The protocols here are redacted copies (engine names replaced). Their sealed hashes belong to the private originals.
