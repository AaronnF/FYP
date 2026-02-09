import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__)))

from core.dilithium_challenge import sample_challenge, DILITHIUM2_N, DILITHIUM2_TAU


def test_basic_properties():
    mu_w1 = b"dilithium-challenge-seed"
    c = sample_challenge(mu_w1)

    assert len(c) == DILITHIUM2_N, "Incorrect challenge length"
    non_zero = [x for x in c if x != 0]
    assert len(non_zero) == DILITHIUM2_TAU, "Incorrect number of non-zero coefficients"
    assert all(x in (-1, 1) for x in non_zero), "Non-zero coefficients must be +/-1"

    c2 = sample_challenge(mu_w1)
    assert c == c2, "Challenge sampler must be deterministic for the same input"


def run_all_tests():
    test_basic_properties()
    print("PASS: Dilithium challenge sampler basic properties")


if __name__ == "__main__":
    run_all_tests()
