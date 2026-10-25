# AM SPLITTER, in Python with int32 wrapping: the same lanes, the same glue.
def _w(v):
    v &= 0xFFFFFFFF
    return v - (1 << 32) if v & 0x80000000 else v

def I_HI(x):
    return _w(((1 + ((x - 1) >> 31)) - ((x + (x >> 31)) >> 31)))

def EMIT(x):
    return _w((x & (-x)))

def ACT_OF(x):
    return _w(((x & (1 - x)) ^ (x & (1 | (x >> 1)))))

def GFN_1_2(x):
    return _w(((x - (x >> 1)) - (x & (x + x))))

def GFC_0_8_c(x):
    return _w(((2 & (x >> 2)) + (2 & ((x - 1) >> 31))))

def GFS_0_200_300(x):
    return _w(((16 & (x >> 5)) + (16 & ((x - 1) >> 31))))

def GFN_1_2_3(x):
    return _w(((x - x) - ((-x) >> 31)))

def GFC_0_4_c(x):
    return _w(((2 & (x >> 1)) + (2 & ((x - 1) >> 31))))

def GFS_0_100_300(x):
    return _w(((16 & (x >> 4)) + (16 & ((x - 1) >> 31))))

def GFC_0_4_8(x):
    return _w(((2 & ((x - 1) >> 31)) + (2 & (x - (x >> 2)))))

def GFP_0_10_30(x):
    return _w(((4 & (x >> 2)) + (4 & ((x - 1) >> 31))))

def GFC_4(x):
    return _w(((2 & (x >> 2)) ^ (2 & ((-x) >> 31))))

def GFC_4_8(x):
    return _w(((x | (x >> 1)) - (x + (2 & (x >> 2)))))

def GFS_0_300(x):
    return _w((16 - (16 & (x - (x >> 5)))))

def GFC_4_8_c(x):
    return _w(((x - ((-x) >> 31)) - (x + ((-x) >> 31))))

def GFP_0_10(x):
    return _w((4 - (4 & (x >> 3))))

def GFS_0(x):
    return _w((16 ^ (16 & ((-x) >> 31))))

def GFN_0_1_3(x):
    return _w(((x & 1) - ((x - 1) >> 31)))

def GFP_10_20(x):
    return _w((4 & (x - (x >> 3))))

def GFS_100_200_300(x):
    return _w((16 & ((-x) >> 31)))

def GFC_8(x):
    return _w(((2 & (x >> 1)) ^ (2 & ((-x) >> 31))))

def GFM_40_80_c0(x):
    return _w((8 & ((-x) >> 31)))

def GFC_4_c(x):
    return _w((2 & (x >> 1)))

def GFP_0_10_20(x):
    return _w(((4 & ((x - 1) >> 31)) + (4 & (x - (x >> 3)))))

def GFM_40_c0(x):
    return _w((8 & (x >> 3)))

def GFN_0_1(x):
    return _w((1 - (x >> 1)))

def GFC_0_8(x):
    return _w((2 - (2 & (x >> 1))))

def GFP_10_20_30(x):
    return _w((4 & ((-x) >> 31)))

def GFC_0(x):
    return _w((2 ^ (2 & ((-x) >> 31))))

def R_M1(x):
    return _w((((x + 1) >> 5) + ((x + 1) >> 5)))

def R_M2(x):
    return _w(((1 | ((x + 1) >> 4)) + (1 | ((x - 31) >> 5))))

def R_M3(x):
    return _w((8 - (8 & ((x - 31) >> 5))))

def R_M4(x):
    return _w(((x & 16) - (x & (16 & (x + 1)))))

def R_M5(x):
    return _w((32 & (x + 1)))

def am_split(n):
    n = _w(n)
    m = (I_HI(_w(n & ~0x3FF)) & 1) | (R_M1((GFN_1_2(n & 0x3) & 1) | (GFC_0_8_c(n & 0xC) & 2) | 4 | 8 | (GFS_0_200_300(n & 0x300) & 16)) & 2) | (R_M1((GFN_1_2_3(n & 0x3) & 1) | (GFC_0_4_c(n & 0xC) & 2) | 4 | 8 | (GFS_0_100_300(n & 0x300) & 16)) & 2) | (R_M1((GFN_1_2_3(n & 0x3) & 1) | (GFC_0_4_8(n & 0xC) & 2) | (GFP_0_10_30(n & 0x30) & 4) | 8 | 16) & 2) | (R_M2(1 | (GFC_4(n & 0xC) & 2) | 4 | 8 | (GFS_0_200_300(n & 0x300) & 16)) & 4) | (R_M2(1 | (GFC_4_8(n & 0xC) & 2) | (GFP_0_10_30(n & 0x30) & 4) | 8 | (GFS_0_300(n & 0x300) & 16)) & 4) | (R_M2(1 | (GFC_4_8_c(n & 0xC) & 2) | (GFP_0_10(n & 0x30) & 4) | 8 | (GFS_0(n & 0x300) & 16)) & 4) | (R_M2((GFN_0_1_3(n & 0x3) & 1) | (GFC_4_8_c(n & 0xC) & 2) | (GFP_10_20(n & 0x30) & 4) | 8 | (GFS_100_200_300(n & 0x300) & 16)) & 4) | (R_M2(1 | (GFC_8(n & 0xC) & 2) | (GFP_0_10_30(n & 0x30) & 4) | (GFM_40_80_c0(n & 0xC0) & 8) | (GFS_0_100_300(n & 0x300) & 16)) & 4) | (R_M2(1 | (GFC_4_c(n & 0xC) & 2) | (GFP_0_10_20(n & 0x30) & 4) | (GFM_40_c0(n & 0xC0) & 8) | 16) & 4) | (R_M3((GFN_0_1(n & 0x3) & 1) | 2 | (GFP_10_20(n & 0x30) & 4) | 8 | 16) & 8) | (R_M3((GFN_0_1(n & 0x3) & 1) | (GFC_0_8(n & 0xC) & 2) | (GFP_10_20_30(n & 0x30) & 4) | 8 | (GFS_0_100_300(n & 0x300) & 16)) & 8) | (R_M4(1 | (GFC_0(n & 0xC) & 2) | 4 | (GFM_40_80_c0(n & 0xC0) & 8) | 16) & 16) | (R_M5(1 | 2 | 4 | 8 | (GFS_100_200_300(n & 0x300) & 16)) & 32) | 64
    e = EMIT(m) & 0xFFFFFFFF
    return ACT_OF((e & -e).bit_length() - 1)
