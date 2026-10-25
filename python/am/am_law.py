# AM, in Python with int32 wrapping: the same lanes, the same glue.
def _w(v):
    v &= 0xFFFFFFFF
    return v - (1 << 32) if v & 0x80000000 else v

def I_HI(x):
    return _w(((1 + ((x - 1) >> 31)) - ((x + (x >> 31)) >> 31)))

def EMIT(x):
    return _w((x & (-x)))

def ACT_OF(x):
    return _w(((x & 4) ^ (x & (x - (x >> 2)))))

def GKIND_0(x):
    return _w((x ^ 1))

def GSA_2_4_a_c_e(x):
    return _w(((x & ((x + 2) >> 3)) + (2 & (x + (x >> 1)))))

def GSB_0_10_20_40_50_60_70(x):
    return _w(((4 + (4 & (x >> 4))) - (4 & (x - ((x - 4) >> 5)))))

def GKIND_1(x):
    return _w(x)

def GSA_2_4_6_a_c_e(x):
    return _w(((2 - (x | 2)) + (x | (2 & (x >> 1)))))

def GSB_0_10_20_30_40_50_70(x):
    return _w(((4 - (4 & ((x >> 5) + 1))) + (4 & (x - ((-x) >> 5)))))

def GSA_0_2_4_8_a_c_e(x):
    return _w(((2 + (x & (x >> 2))) - (x & (2 + (((x - 2) - 1) >> 31)))))

def GSB_10_20_30_50_60_70(x):
    return _w((4 - (4 & (x - (4 | (x >> 4))))))

def GAGREE_2000(x):
    return _w((x >> 8))

def GSC_80_100_180_280_300_380(x):
    return _w((8 - (8 & (x - (8 | (x >> 6))))))

def GSD_400_800_c00_1400_1800_1c00(x):
    return _w((16 - (16 & (x - (16 | (x >> 8))))))

def R_M1(x):
    return _w((((x + 1) >> 6) + ((x + 1) >> 6)))

def R_M2(x):
    return _w(((1 | ((x + 1) >> 5)) + (1 | ((x - 63) >> 6))))

def R_M3(x):
    return _w((8 - (8 & ((x - 63) >> 6))))

def R_M4(x):
    return _w((16 - (16 & ((x - 63) >> 6))))

def am(n):
    n = _w(n)
    m = (I_HI(_w(n & ~0x3FFF)) & 1) | (R_M1((GKIND_0(n & 0x1) & 1) | (GSA_2_4_a_c_e(n & 0xE) & 2) | (GSB_0_10_20_40_50_60_70(n & 0x70) & 4) | 8 | 16 | 32) & 2) | (R_M1((GKIND_1(n & 0x1) & 1) | (GSA_2_4_6_a_c_e(n & 0xE) & 2) | (GSB_0_10_20_30_40_50_70(n & 0x70) & 4) | 8 | 16 | 32) & 2) | (R_M2(1 | (GSA_0_2_4_8_a_c_e(n & 0xE) & 2) | (GSB_10_20_30_50_60_70(n & 0x70) & 4) | 8 | 16 | (GAGREE_2000(n & 0x2000) & 32)) & 4) | (R_M3(1 | (GSA_0_2_4_8_a_c_e(n & 0xE) & 2) | (GSB_0_10_20_40_50_60_70(n & 0x70) & 4) | (GSC_80_100_180_280_300_380(n & 0x380) & 8) | 16 | 32) & 8) | (R_M4(1 | (GSA_0_2_4_8_a_c_e(n & 0xE) & 2) | (GSB_0_10_20_40_50_60_70(n & 0x70) & 4) | 8 | (GSD_400_800_c00_1400_1800_1c00(n & 0x1C00) & 16) | 32) & 16) | 32
    e = EMIT(m) & 0xFFFFFFFF
    return ACT_OF((e & -e).bit_length() - 1)
