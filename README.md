# AM

**AM is a self-improving harness that makes any AI model check and fix its own answers before they ship, and on
rule-finding tasks it answers 50x cheaper than the model alone.**

## Where it helps

- **AI coding assistants that ship broken code.**
  - When a model's answer fails its own visible tests, the harness sends the failing tests back for a fix instead of shipping it.
  - LiveCodeBench v6: +8 contest problems solved and none lost, at about $0.20 per extra solve ([results/coding](results/coding/)).
- **The bill for AI code generation.**
  - It asks for a cheap answer first, and pays for more thinking only when the answer is cut off.
  - HumanEval+: 161 vs 162 solved, with 64% fewer output tokens ([results/coding](results/coding/)).
- **Rule-finding questions** (number patterns and hidden integer rules, as in aptitude tests and math practice).
  - The model only lays out the data, and AM finds the rule.
  - On 60 sealed problems with three Gemini models it was 53–122x cheaper per problem than the model reasoning alone, at a similar score (41 vs 35–36; the difference is not significant).
  - Two caveats: AM's own CPU time (about 25 s per problem, in Python) is not in those dollars, and it gave more wrong answers (8 vs 1–5) ([results/api](results/api/)).

**AM** is a core reasoner: given integer examples, it finds the rule behind them and answers new questions, or says
`CANNOT` when no rule can be determined.  **AM SPLITTER** prepares the problem for it: it decides how to cut the
examples into pieces (by a cut point, parity, residue mod 3, or sign) so AM can solve each piece.

Every decision both make is a **machine-authored law**: integer kernels synthesised lane by lane by an integer
program-synthesis engine and proven exhaustively.  The engine is not part of this repository.  Here are the laws, their
eyes, the proofs and the sealed results.

Like a microscope, it has a narrow field of view but is exact within it: AM sees short integer rules (up to 3
basic-Python steps, sequence laws, piecewise rules once split).  It does not see strings, graphs or long algorithms.

## Use

```bash
make && make test
```

```python
import sys; sys.path.insert(0, "python")
from am import answer, answer_split

answer({"kind": "sequence", "terms": [2, 8, 3, 12, 7, 28, 23, 92]})              # -> [87, 348]
answer({"kind": "rule", "pairs": [[55, 440], [68, 544], [19, 152], [29, 232],
        [95, 760], [4, 32], [92, 736], [13, 104]], "queries": [111, 118]})        # -> [888, 944]
answer_split({"kind": "rule", "pairs": [[48, 528], [17, 26], [4, 44], [109, 118],
              [86, 946], [35, 44], [-28, -308], [112, 1232]], "queries": [-30, 21]})  # -> [-330, 30]
```

## How it works

| part | file | role |
|---|---|---|
| eyes | `python/am/look.py` | list every rule of at most 3 basic-Python steps (`+ - * // % & \| ^ << >>`, `abs`, `min`, `max`, `x*x`, `x*x*x`) that fits, for each view and each upper lane; decide nothing |
| **AM** | `c/am.c` (= `python/am/am_law.py`) | 14-bit state (problem kind, four sources × shallowest depth and agreement, all-agree) → `CANNOT` or which source to answer with |
| splitter's eyes | `python/am/split_look.py` | every way of cutting (none / cut / parity / mod 3 / sign); for each, whether every piece has a short rule and how short |
| **AM SPLITTER** | `c/am_split.c` (= `python/am/am_split_law.py`) | 10-bit structure state (2 bits per family) → `CANNOT` or the split; uses no predictions |

Both laws are branchless integer code with masks-and-ORs glue: AM has 18 synthesised lanes, the splitter 34.  Each was
authored from a design battery of 608 and 700 problems respectively, never from the test batteries.

## Proof (`make prove`, `proofs/`)

- **AM:** the law equals the synthesised table at all 49 measured states, and makes 0 illegal moves over all 16,384 states.
- **AM SPLITTER:** the law equals the table at all 64 measured states, and makes 0 illegal moves over all 1,024 states.
- **Both:** every int32 outside the state space gives `CANNOT`; all 2^32 inputs are swept.
- **C and Python ports:** identical (`tests/`).
- **Authorship** (`proofs/verify_*.txt`, `proofs/lanes_*.json`):
  - every lane is exact on its rows and appears verbatim in the C;
  - lanes re-synthesised from scratch on a second machine came out identical.

## Coding: AM as a self-improving harness (`results/coding/`)

Around an API model, AM and its machine-authored law work as a self-improving harness. The model writes the code. The
law reads only the situation (does the answer pass the samples, do the answers agree, is it valid, was it cut off) and
rules the next act: ship, show the failing samples back, ask for complete code, or raise the thinking budget.

| Set (live, sealed, judged on hidden tests) | Model alone | With the harness |
|---|---|---|
| HumanEval+, 164 tasks | 162 | 161, at **−64% output tokens** |
| LiveCodeBench v6, 174 problems | 132 | **140 (+8, 0 lost)** |
| LiveCodeBench v6, amdev (AM reasons, law steers) | 132 | **139 (8 won, 1 lost)** |

Details, per-task results and the limits are in `results/coding/README.md`.

## Results (sealed batteries, `results/`)

Claude (Opus 5.5) answered first, by reasoning only, and the answers were hashed before any other arm was read.
The raw files are in `results/batteries/rules/` and `results/batteries/multibranch/`: the generator (rules drawn from
`os.urandom`), the problem texts, the sealed answers, Claude's committed answers with their SHA-256
(`shasum -a 256 -c claude_answers.sha256`), and every other arm's answers.

| battery | Claude | AM | AM + splitter | Qwen3-8B alone |
|---|---|---|---|---|
| rules and sequences (38) | 32 | **31** (as the brain over a Qwen3-8B body) | — | 7 |
| multi-branch rules (38) | 33 | 16 | **32** | — |

Limits:
- Each battery is 38 problems from one generator.
- The eyes see the same step family the generator draws from.
- Claude answered without tools.

## Model collapse sandbox (`collapse/`)

This tests the use AM is made for: a maintainer that keeps machine-trained machines true to one reference example.

The setup:
- **World:** 64 hidden integer laws on x = 0..255, giving 16,384 exact points.
- **Learner:** a small MLP. Each generation trains a fresh model on 25% of each law's inputs, labelled by the
  previous generation. This is the recursive regime in which model collapse is known to happen.
- **Arms:**
  - *unverified* takes the model's labels as they come;
  - *accumulate* keeps all earlier training data, including the real data from generation 0;
  - *AM blind* gets no reference and extracts rules from the model's own labels;
  - *AM shown the example* gets 8 exact points per law (3% of the table), fixed before generation 0. AM extracts each
    law's rule from them and relabels every point, or answers `CANNOT` and the law's points are dropped;
  - *proven* uses exact labels.

The scale is 10 seeds × 6 generations, with mean ± 95% CI. Accuracy is measured over all 16,384 points, from
generation 0 to generation 6:

| arm | accuracy | rarest outputs (tails) | wrong training labels |
|---|---|---|---|
| unverified | 69.7 → **49.9** | 84.0 → 54.6 | 30.3% → 48.9% |
| accumulate | 69.8 → 66.2 | 84.1 → 83.7 | 30.3% → 33.8% |
| AM blind | 69.5 → 55.0 | 83.9 → 67.4 | 4.0% → 38.4% |
| **AM shown the example** | **69.7 → 69.3** ± 1.4 | **84.0 → 83.5** | **0.7% → 0.6%** |
| proven | 69.8 → 69.8 | 84.4 → 84.0 | 0% |

The decision rules were written in `collapse/analyse.py` before the results were read:

| hypothesis | result |
|---|---|
| H1: unverified collapses (falls > 5 points) | confirmed |
| H2: proven stays stable (within 2 points) | confirmed |
| H3: AM blind ends within 2 points of proven | **not confirmed** |
| H4: tails are lost first | confirmed (tails −35%, overall −28%) |
| H5: AM shown the example ends within 2 points of proven | **confirmed** |

H5 was added after H1–H4 were read, and before its run.

So AM needs the reference example. Shown 8 exact points per law, its labels stay 99.4% right in every generation,
so errors never compound. Run blind on a model's own labels, it slowly learns the model's mistakes.

Limits:
- The learner is a small MLP, not a language model.
- Every law lies within the eyes' field of view. A law AM cannot see is dropped (`CANNOT`), not repaired.

To run it (numpy and torch; about 10 minutes on 10 cores):

```bash
cd collapse
python3 sandbox.py 10 6
python3 sandbox.py 10 6 am_anchor
python3 analyse.py
```

The raw results are `sandbox_results*.json`; the printed analysis is `verdict.txt`.
