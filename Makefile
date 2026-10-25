# make          build lib/libam.so and lib/libam_split.so
# make test     the Python ports, the C laws and worked examples
# make prove    exhaustive proofs: law == the synthesised table at every measured state, legal at every state, and every
#               int32 outside the state space -> CANNOT (each sweeps all 2^32 inputs, ~15 s)
CC ?= cc
CFLAGS ?= -O2 -fwrapv -Wall
all: lib/libam.so lib/libam_split.so
lib/libam.so: c/am.c
	mkdir -p lib && $(CC) $(CFLAGS) -shared -fPIC -o $@ $<
lib/libam_split.so: c/am_split.c
	mkdir -p lib && $(CC) $(CFLAGS) -shared -fPIC -o $@ $<
test: all
	python3 tests/test_am.py
prove:
	$(CC) $(CFLAGS) -o proofs/prove_am proofs/prove_am.c && ./proofs/prove_am
	$(CC) $(CFLAGS) -o proofs/prove_split proofs/prove_split.c && ./proofs/prove_split
clean:
	rm -rf lib proofs/prove_am proofs/prove_split
.PHONY: all test prove clean
