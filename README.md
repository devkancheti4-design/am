# AM

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

## Results (sealed batteries, `results/`)

Claude (Opus 5.5) answered first, by reasoning only, and the answers were hashed before any other arm was read.

| battery | Claude | AM | AM + splitter | Qwen3-8B alone |
|---|---|---|---|---|
| rules and sequences (38) | 32 | **31** (as the brain over a Qwen3-8B body) | — | 7 |
| multi-branch rules (38) | 33 | 16 | **32** | — |

Limits:
- Each battery is 38 problems from one generator.
- The eyes see the same step family the generator draws from.
- Claude answered without tools.
