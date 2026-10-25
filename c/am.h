/* AM and AM SPLITTER -- the two laws, machine-authored by integer program synthesis. */
#ifndef AM_H
#define AM_H
#include <stdint.h>
/* AM: 14-bit state in (kind, four sources, agreement), move out: 0 CANNOT, 1..4 answer with that source */
int32_t am(int32_t n);
/* AM SPLITTER: 10-bit structure state in (2 bits per family), split out: 0 CANNOT, 1 none, 2 cut, 3 parity, 4 mod3, 5 sign */
int32_t am_split(int32_t n);
#endif
