#ifndef OCTAVIAN_NBIT_H
#define OCTAVIAN_NBIT_H

/*
 * OctavianOS compile-time N-bit unsigned register substrate.
 *
 * Default architectural register width: 8192 bits.
 * Override with -DOCTAVIAN_NBIT_WIDTH=N to build a different profile.
 *
 * This is a software-defined fixed-width value type, not a claim that the
 * physical CPU executes N-bit instructions directly. Physical backends must
 * lower, emulate, or reject operations they cannot execute natively.
 */
#include <stddef.h>
#include <stdint.h>

#ifndef OCTAVIAN_NBIT_WIDTH
#define OCTAVIAN_NBIT_WIDTH 8192
#endif

#if OCTAVIAN_NBIT_WIDTH < 1
#error "OCTAVIAN_NBIT_WIDTH must be greater than zero"
#endif

#define OCTAVIAN_NBIT_LIMBS ((OCTAVIAN_NBIT_WIDTH + 63u) / 64u)
#define OCTAVIAN_NBIT_TOP_BITS (OCTAVIAN_NBIT_WIDTH % 64u)

typedef struct octavian_nbit {
    uint64_t limb[OCTAVIAN_NBIT_LIMBS]; /* little-endian limbs */
} octavian_nbit;

static inline void octavian_nbit_zero(octavian_nbit *out) {
    size_t i;
    if (!out) return;
    for (i = 0; i < OCTAVIAN_NBIT_LIMBS; ++i) out->limb[i] = 0;
}

static inline void octavian_nbit_normalize(octavian_nbit *value) {
    if (!value) return;
#if OCTAVIAN_NBIT_TOP_BITS != 0
    value->limb[OCTAVIAN_NBIT_LIMBS - 1u] &=
        (UINT64_C(1) << OCTAVIAN_NBIT_TOP_BITS) - UINT64_C(1);
#endif
}

static inline void octavian_nbit_from_u64(octavian_nbit *out, uint64_t value) {
    size_t i;
    if (!out) return;
    for (i = 0; i < OCTAVIAN_NBIT_LIMBS; ++i) out->limb[i] = 0;
    out->limb[0] = value;
    octavian_nbit_normalize(out);
}

static inline int octavian_nbit_is_zero(const octavian_nbit *value) {
    size_t i;
    if (!value) return 1;
    for (i = 0; i < OCTAVIAN_NBIT_LIMBS; ++i)
        if (value->limb[i] != 0) return 0;
    return 1;
}

/* Returns -1, 0, or 1 for unsigned ordering. */
static inline int octavian_nbit_compare(const octavian_nbit *a,
                                        const octavian_nbit *b) {
    size_t i;
    if (!a || !b) return a ? 1 : (b ? -1 : 0);
    for (i = OCTAVIAN_NBIT_LIMBS; i > 0; --i) {
        uint64_t av = a->limb[i - 1u], bv = b->limb[i - 1u];
        if (av < bv) return -1;
        if (av > bv) return 1;
    }
    return 0;
}

/* Arithmetic is modulo 2^N; overflow/borrow is intentionally discarded. */
static inline void octavian_nbit_add(octavian_nbit *out,
                                     const octavian_nbit *a,
                                     const octavian_nbit *b) {
    octavian_nbit tmp;
    uint64_t carry = 0;
    size_t i;
    if (!out || !a || !b) return;
    for (i = 0; i < OCTAVIAN_NBIT_LIMBS; ++i) {
        uint64_t x = a->limb[i], y = b->limb[i];
        uint64_t s = x + y;
        uint64_t c1 = (s < x);
        uint64_t r = s + carry;
        uint64_t c2 = (r < s);
        tmp.limb[i] = r;
        carry = c1 | c2;
    }
    octavian_nbit_normalize(&tmp);
    *out = tmp;
}

static inline void octavian_nbit_sub(octavian_nbit *out,
                                     const octavian_nbit *a,
                                     const octavian_nbit *b) {
    octavian_nbit tmp;
    uint64_t borrow = 0;
    size_t i;
    if (!out || !a || !b) return;
    for (i = 0; i < OCTAVIAN_NBIT_LIMBS; ++i) {
        uint64_t x = a->limb[i], y = b->limb[i];
        uint64_t d = x - y;
        uint64_t b1 = (x < y);
        uint64_t r = d - borrow;
        uint64_t b2 = (d < borrow);
        tmp.limb[i] = r;
        borrow = b1 | b2;
    }
    octavian_nbit_normalize(&tmp);
    *out = tmp;
}

static inline void octavian_nbit_and(octavian_nbit *out,
                                     const octavian_nbit *a,
                                     const octavian_nbit *b) {
    octavian_nbit tmp; size_t i;
    if (!out || !a || !b) return;
    for (i = 0; i < OCTAVIAN_NBIT_LIMBS; ++i) tmp.limb[i] = a->limb[i] & b->limb[i];
    octavian_nbit_normalize(&tmp);
    *out = tmp;
}

static inline void octavian_nbit_or(octavian_nbit *out,
                                    const octavian_nbit *a,
                                    const octavian_nbit *b) {
    octavian_nbit tmp; size_t i;
    if (!out || !a || !b) return;
    for (i = 0; i < OCTAVIAN_NBIT_LIMBS; ++i) tmp.limb[i] = a->limb[i] | b->limb[i];
    octavian_nbit_normalize(&tmp); *out = tmp;
}

static inline void octavian_nbit_xor(octavian_nbit *out,
                                     const octavian_nbit *a,
                                     const octavian_nbit *b) {
    octavian_nbit tmp; size_t i;
    if (!out || !a || !b) return;
    for (i = 0; i < OCTAVIAN_NBIT_LIMBS; ++i) tmp.limb[i] = a->limb[i] ^ b->limb[i];
    octavian_nbit_normalize(&tmp); *out = tmp;
}

static inline void octavian_nbit_not(octavian_nbit *out,
                                     const octavian_nbit *value) {
    octavian_nbit tmp; size_t i;
    if (!out || !value) return;
    for (i = 0; i < OCTAVIAN_NBIT_LIMBS; ++i) tmp.limb[i] = ~value->limb[i];
    octavian_nbit_normalize(&tmp); *out = tmp;
}

static inline int octavian_nbit_get_bit(const octavian_nbit *value, size_t bit) {
    if (!value || bit >= (size_t)OCTAVIAN_NBIT_WIDTH) return 0;
    return (int)((value->limb[bit / 64u] >> (bit % 64u)) & UINT64_C(1));
}

static inline int octavian_nbit_set_bit(octavian_nbit *value, size_t bit, int set) {
    uint64_t mask;
    if (!value || bit >= (size_t)OCTAVIAN_NBIT_WIDTH) return -1;
    mask = UINT64_C(1) << (bit % 64u);
    if (set) value->limb[bit / 64u] |= mask;
    else value->limb[bit / 64u] &= ~mask;
    return 0;
}

static inline void octavian_nbit_shl(octavian_nbit *out,
                                     const octavian_nbit *value,
                                     size_t amount) {
    octavian_nbit tmp;
    size_t i, words;
    unsigned bits;
    if (!out || !value) return;
    octavian_nbit_zero(&tmp);
    if (amount < (size_t)OCTAVIAN_NBIT_WIDTH) {
        words = amount / 64u;
        bits = (unsigned)(amount % 64u);
        for (i = OCTAVIAN_NBIT_LIMBS; i > words; --i) {
            size_t dst = i - 1u, src = dst - words;
            tmp.limb[dst] |= value->limb[src] << bits;
            if (bits && src > 0)
                tmp.limb[dst] |= value->limb[src - 1u] >> (64u - bits);
        }
    }
    octavian_nbit_normalize(&tmp);
    *out = tmp;
}

static inline void octavian_nbit_shr(octavian_nbit *out,
                                     const octavian_nbit *value,
                                     size_t amount) {
    octavian_nbit tmp;
    size_t i, words;
    unsigned bits;
    if (!out || !value) return;
    octavian_nbit_zero(&tmp);
    if (amount < (size_t)OCTAVIAN_NBIT_WIDTH) {
        words = amount / 64u;
        bits = (unsigned)(amount % 64u);
        for (i = 0; i + words < OCTAVIAN_NBIT_LIMBS; ++i) {
            size_t src = i + words;
            tmp.limb[i] |= value->limb[src] >> bits;
            if (bits && src + 1u < OCTAVIAN_NBIT_LIMBS)
                tmp.limb[i] |= value->limb[src + 1u] << (64u - bits);
        }
    }
    octavian_nbit_normalize(&tmp);
    *out = tmp;
}

#endif /* OCTAVIAN_NBIT_H */
