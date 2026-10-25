/* AM SPLITTER (s): 10-bit structure state in, the split out (0 CANNOT, 1 none, 2 cut, 3 parity, 4 mod3, 5 sign).  Every lane was
 * machine-authored by integer program synthesis, lane by lane, each lane verified; the glue is masks and ORs.  A number with a
 * bit above 9 answers CANNOT.  Built from proofs/lanes_split.json. */
#include <stdint.h>
#define LANE static inline int32_t

LANE I_HI      (int32_t x){ return ((1 + ((x - 1) >> 31)) - ((x + (x >> 31)) >> 31)); }
LANE EMIT      (int32_t x){ return (x & (-x)); }
LANE ACT_OF    (int32_t x){ return ((x & (1 - x)) ^ (x & (1 | (x >> 1)))); }
LANE GFN_1_2                   (int32_t x){ return ((x - (x >> 1)) - (x & (x + x))); }
LANE GFC_0_8_c                 (int32_t x){ return ((2 & (x >> 2)) + (2 & ((x - 1) >> 31))); }
LANE GFS_0_200_300             (int32_t x){ return ((16 & (x >> 5)) + (16 & ((x - 1) >> 31))); }
LANE GFN_1_2_3                 (int32_t x){ return ((x - x) - ((-x) >> 31)); }
LANE GFC_0_4_c                 (int32_t x){ return ((2 & (x >> 1)) + (2 & ((x - 1) >> 31))); }
LANE GFS_0_100_300             (int32_t x){ return ((16 & (x >> 4)) + (16 & ((x - 1) >> 31))); }
LANE GFC_0_4_8                 (int32_t x){ return ((2 & ((x - 1) >> 31)) + (2 & (x - (x >> 2)))); }
LANE GFP_0_10_30               (int32_t x){ return ((4 & (x >> 2)) + (4 & ((x - 1) >> 31))); }
LANE GFC_4                     (int32_t x){ return ((2 & (x >> 2)) ^ (2 & ((-x) >> 31))); }
LANE GFC_4_8                   (int32_t x){ return ((x | (x >> 1)) - (x + (2 & (x >> 2)))); }
LANE GFS_0_300                 (int32_t x){ return (16 - (16 & (x - (x >> 5)))); }
LANE GFC_4_8_c                 (int32_t x){ return ((x - ((-x) >> 31)) - (x + ((-x) >> 31))); }
LANE GFP_0_10                  (int32_t x){ return (4 - (4 & (x >> 3))); }
LANE GFS_0                     (int32_t x){ return (16 ^ (16 & ((-x) >> 31))); }
LANE GFN_0_1_3                 (int32_t x){ return ((x & 1) - ((x - 1) >> 31)); }
LANE GFP_10_20                 (int32_t x){ return (4 & (x - (x >> 3))); }
LANE GFS_100_200_300           (int32_t x){ return (16 & ((-x) >> 31)); }
LANE GFC_8                     (int32_t x){ return ((2 & (x >> 1)) ^ (2 & ((-x) >> 31))); }
LANE GFM_40_80_c0              (int32_t x){ return (8 & ((-x) >> 31)); }
LANE GFC_4_c                   (int32_t x){ return (2 & (x >> 1)); }
LANE GFP_0_10_20               (int32_t x){ return ((4 & ((x - 1) >> 31)) + (4 & (x - (x >> 3)))); }
LANE GFM_40_c0                 (int32_t x){ return (8 & (x >> 3)); }
LANE GFN_0_1                   (int32_t x){ return (1 - (x >> 1)); }
LANE GFC_0_8                   (int32_t x){ return (2 - (2 & (x >> 1))); }
LANE GFP_10_20_30              (int32_t x){ return (4 & ((-x) >> 31)); }
LANE GFC_0                     (int32_t x){ return (2 ^ (2 & ((-x) >> 31))); }
LANE R_M1                      (int32_t x){ return (((x + 1) >> 5) + ((x + 1) >> 5)); }
LANE R_M2                      (int32_t x){ return ((1 | ((x + 1) >> 4)) + (1 | ((x - 31) >> 5))); }
LANE R_M3                      (int32_t x){ return (8 - (8 & ((x - 31) >> 5))); }
LANE R_M4                      (int32_t x){ return ((x & 16) - (x & (16 & (x + 1)))); }
LANE R_M5                      (int32_t x){ return (32 & (x + 1)); }

int32_t am_split(int32_t n)
{   int32_t m = (I_HI(n & ~0x3FF) & 1) |
        (R_M1((GFN_1_2(n & 0x3) & 1) | (GFC_0_8_c(n & 0xC) & 2) | 4 | 8 | (GFS_0_200_300(n & 0x300) & 16)) & 2) |
        (R_M1((GFN_1_2_3(n & 0x3) & 1) | (GFC_0_4_c(n & 0xC) & 2) | 4 | 8 | (GFS_0_100_300(n & 0x300) & 16)) & 2) |
        (R_M1((GFN_1_2_3(n & 0x3) & 1) | (GFC_0_4_8(n & 0xC) & 2) | (GFP_0_10_30(n & 0x30) & 4) | 8 | 16) & 2) |
        (R_M2(1 | (GFC_4(n & 0xC) & 2) | 4 | 8 | (GFS_0_200_300(n & 0x300) & 16)) & 4) |
        (R_M2(1 | (GFC_4_8(n & 0xC) & 2) | (GFP_0_10_30(n & 0x30) & 4) | 8 | (GFS_0_300(n & 0x300) & 16)) & 4) |
        (R_M2(1 | (GFC_4_8_c(n & 0xC) & 2) | (GFP_0_10(n & 0x30) & 4) | 8 | (GFS_0(n & 0x300) & 16)) & 4) |
        (R_M2((GFN_0_1_3(n & 0x3) & 1) | (GFC_4_8_c(n & 0xC) & 2) | (GFP_10_20(n & 0x30) & 4) | 8 | (GFS_100_200_300(n & 0x300) & 16)) & 4) |
        (R_M2(1 | (GFC_8(n & 0xC) & 2) | (GFP_0_10_30(n & 0x30) & 4) | (GFM_40_80_c0(n & 0xC0) & 8) | (GFS_0_100_300(n & 0x300) & 16)) & 4) |
        (R_M2(1 | (GFC_4_c(n & 0xC) & 2) | (GFP_0_10_20(n & 0x30) & 4) | (GFM_40_c0(n & 0xC0) & 8) | 16) & 4) |
        (R_M3((GFN_0_1(n & 0x3) & 1) | 2 | (GFP_10_20(n & 0x30) & 4) | 8 | 16) & 8) |
        (R_M3((GFN_0_1(n & 0x3) & 1) | (GFC_0_8(n & 0xC) & 2) | (GFP_10_20_30(n & 0x30) & 4) | 8 | (GFS_0_100_300(n & 0x300) & 16)) & 8) |
        (R_M4(1 | (GFC_0(n & 0xC) & 2) | 4 | (GFM_40_80_c0(n & 0xC0) & 8) | 16) & 16) |
        (R_M5(1 | 2 | 4 | 8 | (GFS_100_200_300(n & 0x300) & 16)) & 32) | 64;
    return ACT_OF(__builtin_ctz((uint32_t)EMIT(m))); }
