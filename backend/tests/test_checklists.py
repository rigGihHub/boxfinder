from app.services.checklists import classify_outcome, odds_to_box_probability, parse_checklist_csv

class C:
    is_case_hit=False; serial_numbered_to=None; is_autograph=False; parallel=None; is_memorabilia=False; is_rookie=False

def test_csv_import_recognizes_flags():
    rows = parse_checklist_csv("card_number,subject,team,subset,parallel,serial_numbered_to,is_rookie,is_autograph\n1,Test Rookie,Club,Base,Gold,50,true,false")
    assert len(rows) == 1
    assert rows[0].subject == "Test Rookie"
    assert rows[0].serial_numbered_to == 50
    assert rows[0].is_rookie is True


def test_one_in_packs_converts_to_box_probability():
    p = odds_to_box_probability(packs_per_box=12, one_in_packs=24)
    assert 0.39 < p < 0.41


def test_hit_classification_prefers_low_numbered_as_jackpot():
    c=C(); c.serial_numbered_to=10
    assert classify_outcome(c) == "jackpot"
