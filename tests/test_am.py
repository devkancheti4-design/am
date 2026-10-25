"""python3 tests/test_am.py   (from the repo root; run `make` first to also check the C laws)"""
import ctypes, os, random, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "python"))
from am import answer, answer_split
from am.am_law import am
from am.am_split_law import am_split


def table(name):
    t = open(os.path.join(ROOT, "proofs", f"table_{name}.bin"), "rb").read()
    r = open(os.path.join(ROOT, "proofs", f"reached_{name}.bin"), "rb").read()
    return t, r


def check(cond, what):
    print(("  ok    " if cond else "  FAIL  ") + what)
    return cond


ok = True
t, r = table("am")
ok &= check(all(am(n) == t[n] for n in range(1 << 14) if r[n]), "AM (Python) equals the synthesised table at every measured state")
ok &= check(all(am(n) == 0 or ((n >> (1 + 3 * (am(n) - 1))) & 3) for n in range(1 << 14)), "AM never picks a source that found nothing")
t, r = table("split")
ok &= check(all(am_split(n) == t[n] for n in range(1 << 10) if r[n]), "AM SPLITTER (Python) equals the synthesised table at every measured state")
ok &= check(all(am_split(n) == 0 or ((n >> (2 * (am_split(n) - 1))) & 3) for n in range(1 << 10)), "AM SPLITTER never picks a split whose pieces have no rule")
lib = os.path.join(ROOT, "lib")
if os.path.exists(os.path.join(lib, "libam.so")):
    A = ctypes.CDLL(os.path.join(lib, "libam.so")).am; A.argtypes = [ctypes.c_int32]
    S = ctypes.CDLL(os.path.join(lib, "libam_split.so")).am_split; S.argtypes = [ctypes.c_int32]
    xs = [random.randint(-2 ** 31, 2 ** 31 - 1) for _ in range(100000)]
    ok &= check(all(A(n) == am(n) for n in list(range(1 << 14)) + xs), "c/am.c equals the Python port (all 16,384 states + 100,000 random int32)")
    ok &= check(all(S(n) == am_split(n) for n in list(range(1 << 10)) + xs), "c/am_split.c equals the Python port (all 1,024 states + 100,000 random int32)")
else:
    print("  skip  C laws (run `make` to build lib/)")
# worked examples (rules drawn by the battery generator; the sealed batteries are in results/)
ok &= check(answer({"kind": "rule", "pairs": [[55, 440], [68, 544], [19, 152], [29, 232], [95, 760], [4, 32], [92, 736], [13, 104]],
                    "queries": [111, 118]}) == [888, 944], "AM: y = 8x  ->  [888, 944]")
ok &= check(answer({"kind": "sequence", "terms": [2, 8, 3, 12, 7, 28, 23, 92]}) == [87, 348], "AM: x4, -5, x4, -5 ...  ->  [87, 348]")
par = [[48, 528], [4, 44], [86, 946], [54, 594], [72, 792], [17, 26], [109, 118], [35, 44], [106, 1166], [32, 352], [-28, -308], [112, 1232]]
ok &= check(answer_split({"kind": "rule", "pairs": par, "queries": [-30, 21]}) == [-330, 30], "AM SPLITTER: even 11x, odd x + 9  ->  [-330, 30]")
noise = [[7, -321], [34, 310], [87, -458], [31, -27], [48, -383], [3, -395], [-6, -315], [104, -372], [76, -366], [66, 482], [47, 88], [67, -116]]
ok &= check(answer_split({"kind": "rule", "pairs": noise, "queries": [24, 20]}) == "CANNOT", "AM SPLITTER: noise  ->  CANNOT")
print("\nALL PASS" if ok else "\nFAILURES ABOVE")
sys.exit(0 if ok else 1)
