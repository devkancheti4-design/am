/* am_split == the table at every measured state; legal at every one of the 1,024 numbers; CANNOT (0) for every
 * int32 with a bit above 9 (all 2^32 inputs swept); every output in 0..5.  cc -O2 -fwrapv prove_brain.c */
#include <stdio.h>
#include <stdint.h>
#include "../c/am_split.c"
int main(void) {
    static unsigned char tab[1 << 10], reached[1 << 10];
    FILE *f = fopen("proofs/table_split.bin", "rb"); fread(tab, 1, sizeof tab, f); fclose(f);
    f = fopen("proofs/reached_split.bin", "rb"); fread(reached, 1, sizeof reached, f); fclose(f);
    long wrong = 0, illegal = 0, range = 0, hi = 0, nreached = 0;
    for (int n = 0; n < (1 << 10); n++) {
        int m = am_split(n);
        if (m < 0 || m > 5) range++;
        if (m && ((n >> (2 * (m - 1))) & 3) == 0) illegal++;
        if (reached[n]) { nreached++; if (m != tab[n]) wrong++; }
    }
    uint32_t x = 0;
    do { if (x >> 10) { int m = am_split((int32_t)x); if (m != 0) hi++; if (m < 0 || m > 5) range++; } x++; } while (x);
    printf("  measured states: %ld, law != table at %ld\n  legal at all 1,024 numbers: %ld illegal\n"
           "  every int32 with a bit above 9 -> CANNOT: %ld violations (2^32 swept)\n  outputs in 0..5: %ld violations\n",
           nreached, wrong, illegal, hi, range);
    return (wrong || illegal || hi || range) != 0; }
