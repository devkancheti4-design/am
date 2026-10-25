"""Written before the results were read.  Mean and 95% interval (t, df = seeds - 1) per arm per generation; the four
hypotheses tested with the decision rules fixed in advance:
  H1 collapse:  unverified accuracy falls by more than 5 points from generation 0 to the last
  H2 stable:    proven stays within 2 points of generation 0
  H3 maintainer: AM ends within 2 points of proven (AM never saw the true laws)
  H4 tails:     unverified loses a larger share of its tail accuracy than of its overall accuracy"""
import json, math
R = json.load(open("sandbox_results.json"))
seeds = sorted(R, key=int); S = len(seeds); ARMS = ("unverified", "accumulate", "am", "proven")
T95 = {2: 12.71, 3: 4.30, 4: 3.18, 5: 2.78, 6: 2.57, 7: 2.45, 8: 2.36, 9: 2.31, 10: 2.26}.get(S, 2.0)
def ci(v):
    m = sum(v) / len(v); sd = math.sqrt(sum((x - m) ** 2 for x in v) / (len(v) - 1)) if len(v) > 1 else 0
    return m, T95 * sd / math.sqrt(len(v))
G = len(R[seeds[0]]["unverified"]) - 1
M = {a: {key: [ci([R[s][a][g][key] for s in seeds]) for g in range(G + 1)] for key in ("acc", "tail", "label_err", "pairs")} for a in ARMS}
print("accuracy over all 16,384 points (mean +- 95%% CI, %d seeds)" % S)
print("gen " + "".join("%22s" % a for a in ARMS))
for g in range(G + 1):
    print("%3d " % g + "".join("%15.1f%% +-%4.1f" % (100 * M[a]["acc"][g][0], 100 * M[a]["acc"][g][1]) for a in ARMS))
print("\ntails (rarest outputs) accuracy")
for g in range(G + 1):
    print("%3d " % g + "".join("%15.1f%% +-%4.1f" % (100 * M[a]["tail"][g][0], 100 * M[a]["tail"][g][1]) for a in ARMS))
print("\ntraining-label error rate (the arm's own labels)")
for g in range(1, G + 1):
    print("%3d " % g + "".join("%15.1f%% +-%4.1f" % (100 * M[a]["label_err"][g][0], 100 * M[a]["label_err"][g][1]) for a in ARMS))
a0 = lambda a, k="acc": M[a][k][0][0]; aG = lambda a, k="acc": M[a][k][G][0]
h1 = a0("unverified") - aG("unverified") > 0.05
h2 = abs(aG("proven") - a0("proven")) <= 0.02
h3 = aG("proven") - aG("am") <= 0.02
rt = (a0("unverified", "tail") - aG("unverified", "tail")) / max(a0("unverified", "tail"), 1e-9)
ro = (a0("unverified") - aG("unverified")) / max(a0("unverified"), 1e-9)
h4 = rt > ro
print("\nH1 collapse (unverified falls > 5 pts):        %s   (%.1f%% -> %.1f%%)" % ("CONFIRMED" if h1 else "not confirmed", 100 * a0("unverified"), 100 * aG("unverified")))
print("H2 proven stable (within 2 pts):              %s   (%.1f%% -> %.1f%%)" % ("CONFIRMED" if h2 else "not confirmed", 100 * a0("proven"), 100 * aG("proven")))
print("H3 AM within 2 pts of proven at the end:      %s   (AM %.1f%%, proven %.1f%%)" % ("CONFIRMED" if h3 else "not confirmed", 100 * aG("am"), 100 * aG("proven")))
print("H4 tails lost first (relative loss tail > all): %s   (tail -%.0f%%, all -%.0f%%)" % ("CONFIRMED" if h4 else "not confirmed", 100 * rt, 100 * ro))
print("accumulate at the end: %.1f%% (gen 0 %.1f%%)" % (100 * aG("accumulate"), 100 * a0("accumulate")))
json.dump(dict(M=M, H=dict(H1=h1, H2=h2, H3=h3, H4=h4)), open("analysis.json", "w"), indent=1)
# H5, written after H1-H4 were read and BEFORE the anchored run: AM anchored on 8 exact reference points per law (3% of the
# table, the "one handmade algorithm shown to it") ends within 2 points of proven.
import os
if os.path.exists("sandbox_results_am_anchor.json"):
    RA = json.load(open("sandbox_results_am_anchor.json"))
    acc = [ci([RA[s]["am_anchor"][g]["acc"] for s in sorted(RA, key=int)]) for g in range(G + 1)]
    err = [ci([RA[s]["am_anchor"][g]["label_err"] for s in sorted(RA, key=int)]) for g in range(1, G + 1)]
    tail = [ci([RA[s]["am_anchor"][g]["tail"] for s in sorted(RA, key=int)]) for g in range(G + 1)]
    print("\nAM anchored (8 exact points a law): accuracy " + "  ".join("%.1f%%" % (100 * a[0]) for a in acc))
    print("                                    tails    " + "  ".join("%.1f%%" % (100 * a[0]) for a in tail))
    print("                                    label error " + "  ".join("%.1f%%" % (100 * e[0]) for e in err))
    h5 = aG("proven") - acc[G][0] <= 0.02
    print("H5 anchored AM within 2 pts of proven at the end: %s   (anchored %.1f%% +- %.1f, proven %.1f%%)" % ("CONFIRMED" if h5 else "not confirmed", 100 * acc[G][0], 100 * acc[G][1], 100 * aG("proven")))
