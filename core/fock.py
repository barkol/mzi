"""Fock state beam-splitter transformation utilities.

Provides the exact quantum-mechanical amplitudes and probability
distributions for n-photon Fock states passing through a beam splitter.

Convention
----------
The 2×2 beam-splitter unitary is::

    ĉ† = t â† + r' b̂†      (output mode c from inputs a, b)
    d̂† = r â† + t  b̂†      (output mode d)

with |t|² + |r|² = 1 and r' = −r*.  Port mapping to the 4-port
scattering matrix used elsewhere in the code-base:

    For a '\\' beam splitter the relevant 2×2 sub-matrices are
    (A,D) → (B,C)  and  (B,C) → (A,D).
"""

import math
import cmath
from functools import lru_cache
from typing import Dict, Tuple


@lru_cache(maxsize=256)
def _comb(n: int, k: int) -> int:
    """Binomial coefficient C(n, k)."""
    if k < 0 or k > n:
        return 0
    return math.comb(n, k)


def fock_bs_amplitude(n: int, m: int, p: int,
                      t: complex, r: complex, r_prime: complex) -> complex:
    """Amplitude ⟨p, q | n, m⟩ for a beam splitter in the Fock basis.

    Parameters
    ----------
    n, m : int
        Input photon numbers at ports a and b.
    p : int
        Output photon number at port c (q = n + m − p is implicit).
    t, r, r_prime : complex
        Beam-splitter coefficients (see module docstring).

    Returns
    -------
    complex
        The transition amplitude.
    """
    total = n + m
    q = total - p
    if p < 0 or q < 0:
        return 0j

    prefactor = math.sqrt(math.factorial(p) * math.factorial(q)
                          / (math.factorial(n) * math.factorial(m)))

    s_min = max(0, p - m)
    s_max = min(n, p)

    amp = 0j
    for s in range(s_min, s_max + 1):
        k = p - s  # number of b-photons routed to c
        amp += (_comb(n, s) * _comb(m, k)
                * t ** s * r ** (n - s)
                * r_prime ** k * t ** (m - k))

    return prefactor * amp


def fock_bs_probabilities(n: int, m: int,
                          t: complex, r: complex,
                          r_prime: complex = None) -> Dict[Tuple[int, int], float]:
    """Output photon-number probability distribution for |n, m⟩ input.

    Parameters
    ----------
    n, m : int
        Input photon numbers.
    t, r : complex
        Beam-splitter transmission and reflection coefficients.
    r_prime : complex, optional
        Second reflection coefficient.  Defaults to −conj(r).

    Returns
    -------
    dict
        Mapping (p, q) → probability for every non-negligible outcome.
    """
    if r_prime is None:
        import numpy as np
        r_prime = -np.conj(r)

    total = n + m
    probs: Dict[Tuple[int, int], float] = {}
    for p in range(total + 1):
        q = total - p
        amp = fock_bs_amplitude(n, m, p, t, r, r_prime)
        prob = abs(amp) ** 2
        if prob > 1e-12:
            probs[(p, q)] = prob
    return probs


def sample_fock_bs(n: int, m: int,
                   t: complex, r: complex,
                   r_prime: complex = None) -> Tuple[int, int]:
    """Sample one outcome from |n, m⟩ through a beam splitter.

    Returns (p, q) drawn from the exact quantum distribution.
    """
    import random
    dist = fock_bs_probabilities(n, m, t, r, r_prime)
    r_val = random.random()
    cumulative = 0.0
    for (p, q), prob in dist.items():
        cumulative += prob
        if r_val <= cumulative:
            return (p, q)
    # Fallback (rounding)
    return list(dist.keys())[-1]
