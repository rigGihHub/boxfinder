import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest


@pytest.fixture(autouse=True)
def historical_snapshot_regressions(request, monkeypatch):
    """Versioned snapshot assertions retain their original prices and evidence.

The complete refresh and migration are exercised against current data in
test_two_shops_inventory; old imports still verify their own historical facts.
"""
    if request.path.name in {
        'test_real_snapshot.py', 'test_october_03_expansion.py',
        'test_october_04_depth.py', 'test_october_04_products.py',
        'test_kantovault_inventory.py',
    }:
        from app import seed
        monkeypatch.setattr(seed, 'REAL_SNAPSHOT', seed.PRE_TWO_SHOPS_SNAPSHOT)
        monkeypatch.setattr(seed, 'CHASE_PROFILES', seed.PRE_TWO_SHOPS_PROFILES)

    if request.path.name == 'test_two_shops_inventory.py':
        from app import seed
        monkeypatch.setattr(seed, 'REAL_SNAPSHOT', seed.PRE_NEW_RETAILERS_SNAPSHOT)
        monkeypatch.setattr(seed, 'CHASE_PROFILES', seed.PRE_NEW_RETAILERS_PROFILES)
