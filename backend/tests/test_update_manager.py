from app.services.update_manager import status_payload, AUTO_INTERVAL_MINUTES
from app.services.source_hub import SOURCE_PROFILES

def test_update_manager_interval_is_six_hours():
    assert AUTO_INTERVAL_MINUTES == 360
    assert status_payload()["auto_interval_minutes"] == 360

def test_source_catalog_is_substantially_expanded():
    assert len(SOURCE_PROFILES) >= 20
    assert "Coolcard" in SOURCE_PROFILES
    assert "Aquitaz" in SOURCE_PROFILES
    assert "NordicSportsCards" in SOURCE_PROFILES
