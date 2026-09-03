import math

import pytest

from eca_qca_lab.core import PROFILE_SPECS
from eca_qca_lab.experiment import FAMILYWISE_ALPHA, _noise


def test_confirmatory_seeds_are_disjoint_from_pilot():
    pilot = {20260903, 20260917, 20261001, 20261015, 20261029}
    confirmatory = set(PROFILE_SPECS["paper"].base_seeds)
    assert len(confirmatory) == 5
    assert confirmatory.isdisjoint(pilot)


def test_noise_uses_simultaneous_hoeffding_band():
    spec = PROFILE_SPECS["smoke"]
    _, rows = _noise(spec)
    expected_checks = 2 * 3 * len(spec.rules) * len(spec.bitflip_probabilities)
    assert rows
    assert {row["simultaneous_checks"] for row in rows} == {expected_checks}
    assert {row["familywise_alpha"] for row in rows} == {FAMILYWISE_ALPHA}
    for row in rows:
        ber_width = math.sqrt(
            math.log(2 * expected_checks / FAMILYWISE_ALPHA)
            / (2 * row["ber_trials"])
        )
        exact_width = math.sqrt(
            math.log(2 * expected_checks / FAMILYWISE_ALPHA)
            / (2 * row["exact_trials"])
        )
        assert row["ber_hoeffding_half_width"] == pytest.approx(ber_width)
        assert row["exact_hoeffding_half_width"] == pytest.approx(exact_width)


def test_smoke_does_not_reuse_random_streams():
    spec = PROFILE_SPECS["smoke"]
    raw, _ = _noise(spec)
    units = {
        (row["rule"], row["state_id"], row["bitflip_probability"], row["base_seed"]):
        row["simulator_seed"]
        for row in raw
    }
    assert len(units) == 36
    assert len(set(units.values())) == 36
