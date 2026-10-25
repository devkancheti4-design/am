/* AM: 14-bit state in, the move out (0 CANNOT, 1..4 answer with that source).  Every lane was
 * machine-authored by integer program synthesis, lane by lane, each lane verified; the glue is masks and ORs.  A number with a
 * bit above 13 answers CANNOT.  This is AM; built from proofs/lanes_am.json. */
#include <stdint.h>
#define LANE static inline int32_t

LANE I_HI      (int32_t x){ return ((1 + ((x - 1) >> 31)) - ((x + (x >> 31)) >> 31)); }
LANE EMIT      (int32_t x){ return (x & (-x)); }
LANE ACT_OF    (int32_t x){ return ((x & 4) ^ (x & (x - (x >> 2)))); }
LANE GKIND_0                   (int32_t x){ return (x ^ 1); }
LANE GSA_2_4_a_c_e             (int32_t x){ return ((x & ((x + 2) >> 3)) + (2 & (x + (x >> 1)))); }
LANE GSB_0_10_20_40_50_60_70   (int32_t x){ return ((4 + (4 & (x >> 4))) - (4 & (x - ((x - 4) >> 5)))); }
LANE GKIND_1                   (int32_t x){ return x; }
LANE GSA_2_4_6_a_c_e           (int32_t x){ return ((2 - (x | 2)) + (x | (2 & (x >> 1)))); }
LANE GSB_0_10_20_30_40_50_70   (int32_t x){ return ((4 - (4 & ((x >> 5) + 1))) + (4 & (x - ((-x) >> 5)))); }
LANE GSA_0_2_4_8_a_c_e         (int32_t x){ return ((2 + (x & (x >> 2))) - (x & (2 + (((x - 2) - 1) >> 31)))); }
LANE GSB_10_20_30_50_60_70     (int32_t x){ return (4 - (4 & (x - (4 | (x >> 4))))); }
LANE GAGREE_2000               (int32_t x){ return (x >> 8); }
LANE GSC_80_100_180_280_300_380(int32_t x){ return (8 - (8 & (x - (8 | (x >> 6))))); }
LANE GSD_400_800_c00_1400_1800_1c00(int32_t x){ return (16 - (16 & (x - (16 | (x >> 8))))); }
LANE R_M1                      (int32_t x){ return (((x + 1) >> 6) + ((x + 1) >> 6)); }
LANE R_M2                      (int32_t x){ return ((1 | ((x + 1) >> 5)) + (1 | ((x - 63) >> 6))); }
LANE R_M3                      (int32_t x){ return (8 - (8 & ((x - 63) >> 6))); }
LANE R_M4                      (int32_t x){ return (16 - (16 & ((x - 63) >> 6))); }

int32_t am(int32_t n)
{   int32_t m = (I_HI(n & ~0x3FFF) & 1) |
        (R_M1((GKIND_0(n & 0x1) & 1) | (GSA_2_4_a_c_e(n & 0xE) & 2) | (GSB_0_10_20_40_50_60_70(n & 0x70) & 4) | 8 | 16 | 32) & 2) |
        (R_M1((GKIND_1(n & 0x1) & 1) | (GSA_2_4_6_a_c_e(n & 0xE) & 2) | (GSB_0_10_20_30_40_50_70(n & 0x70) & 4) | 8 | 16 | 32) & 2) |
        (R_M2(1 | (GSA_0_2_4_8_a_c_e(n & 0xE) & 2) | (GSB_10_20_30_50_60_70(n & 0x70) & 4) | 8 | 16 | (GAGREE_2000(n & 0x2000) & 32)) & 4) |
        (R_M3(1 | (GSA_0_2_4_8_a_c_e(n & 0xE) & 2) | (GSB_0_10_20_40_50_60_70(n & 0x70) & 4) | (GSC_80_100_180_280_300_380(n & 0x380) & 8) | 16 | 32) & 8) |
        (R_M4(1 | (GSA_0_2_4_8_a_c_e(n & 0xE) & 2) | (GSB_0_10_20_40_50_60_70(n & 0x70) & 4) | 8 | (GSD_400_800_c00_1400_1800_1c00(n & 0x1C00) & 16) | 32) & 16) | 32;
    return ACT_OF(__builtin_ctz((uint32_t)EMIT(m))); }
