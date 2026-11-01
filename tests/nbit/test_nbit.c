#include <assert.h>
#include <stddef.h>
#include <stdint.h>
#include "octavian/nbit.h"

int main(void) {
    octavian_nbit zero, one, value, tmp, all_ones, result;
    size_t i;
    octavian_nbit_zero(&zero);
    octavian_nbit_from_u64(&one, 1);
    assert(octavian_nbit_is_zero(&zero));
    assert(!octavian_nbit_is_zero(&one));
    assert(octavian_nbit_compare(&one, &zero) == 1);

    /* Bit N-1 is representable for any configured positive N. */
    value = zero;
    assert(octavian_nbit_set_bit(&value, OCTAVIAN_NBIT_WIDTH - 1u, 1) == 0);
    assert(octavian_nbit_get_bit(&value, OCTAVIAN_NBIT_WIDTH - 1u) == 1);
    assert(octavian_nbit_get_bit(&value, OCTAVIAN_NBIT_WIDTH) == 0);
    assert(octavian_nbit_set_bit(&value, OCTAVIAN_NBIT_WIDTH, 1) == -1);

    octavian_nbit_shr(&tmp, &value, OCTAVIAN_NBIT_WIDTH - 1u);
    assert(octavian_nbit_compare(&tmp, &one) == 0);
    octavian_nbit_shl(&result, &one, OCTAVIAN_NBIT_WIDTH - 1u);
    assert(octavian_nbit_compare(&result, &value) == 0);

    /* N-bit modular wrap: (2^N - 1) + 1 == 0 and 0 - 1 == 2^N - 1. */
    for (i = 0; i < OCTAVIAN_NBIT_LIMBS; ++i) all_ones.limb[i] = UINT64_MAX;
    octavian_nbit_normalize(&all_ones);
    octavian_nbit_add(&result, &all_ones, &one);
    assert(octavian_nbit_is_zero(&result));
    octavian_nbit_sub(&result, &zero, &one);
    assert(octavian_nbit_compare(&result, &all_ones) == 0);

    /* Aliasing is supported. */
    value = one;
    octavian_nbit_add(&value, &value, &one);
    octavian_nbit_from_u64(&tmp, 2);
    assert(octavian_nbit_compare(&value, &tmp) == 0);

    octavian_nbit_not(&result, &zero);
    assert(octavian_nbit_compare(&result, &all_ones) == 0);
    octavian_nbit_and(&result, &all_ones, &zero);
    assert(octavian_nbit_is_zero(&result));
    octavian_nbit_or(&result, &one, &zero);
    assert(octavian_nbit_compare(&result, &one) == 0);
    octavian_nbit_xor(&result, &one, &one);
    assert(octavian_nbit_is_zero(&result));

    octavian_nbit_shl(&result, &one, OCTAVIAN_NBIT_WIDTH);
    assert(octavian_nbit_is_zero(&result));
    octavian_nbit_shr(&result, &value, OCTAVIAN_NBIT_WIDTH);
    assert(octavian_nbit_is_zero(&result));
    return 0;
}
