/* reason_brain == the table at every measured state; legal at every one of the 16,384 numbers; CANNOT (0) for every
 * int32 with a bit above 13 (all 2^32 inputs swept); every output in 0..4.  cc -O2 -fwrapv prove_brain.c */
#include <stdio.h>
#include <stdint.h>
#include "../c/am.c"
int main(void) {
    static unsigned char tab[1 << 14], reached[1 << 14];
    FILE *f = fopen("proofs/table_am.bin", "rb"); fread(tab, 1, sizeof tab, f); fclose(f);
    f = fopen("proofs/reached_am.bin", "rb"); fread(reached, 1, sizeof reached, f); fclose(f);
    long wrong = 0, illegal = 0, range = 0, hi = 0, nreached = 0;
    for (int n = 0; n < (1 << 14); n++) {
        int m = am(n);
        if (m < 0 || m > 4) range++;
        if (m && ((n >> (1 + 3 * (m - 1))) & 3) == 0) illegal++;
        if (reached[n]) { nreached++; if (m != tab[n]) wrong++; }
    }
    uint32_t x = 0;
    do { if (x >> 14) { int m = am((int32_t)x); if (m != 0) hi++; if (m < 0 || m > 4) range++; } x++; } while (x);
    printf("  measured states: %ld, law != table at %ld\n  legal at all 16,384 numbers: %ld illegal\n"
           "  every int32 with a bit above 13 -> CANNOT: %ld violations (2^32 swept)\n  outputs in 0..4: %ld violations\n",
           nreached, wrong, illegal, hi, range);
    return (wrong || illegal || hi || range) != 0; }
