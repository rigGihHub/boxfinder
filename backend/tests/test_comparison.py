from app.services.comparison import compare_items


def item(i, price, score, data=80, ev=(50,60), rookie=50, hit=50, upside=50, floor=50, risk="Medel"):
    return {"id":i,"name":f"P{i}","price":price,"box_value_score":score,"data_quality":data,
            "ev_low":ev[0] if ev else None,"ev_high":ev[1] if ev else None,"rookie_strength":rookie,
            "hit_density":hit,"upside":upside,"floor_score":floor,"risk":risk}


def test_compare_marks_category_winners():
    out = compare_items([item(1,100,80), item(2,120,90, rookie=95)])
    assert out["winners"]["price"]["winner_ids"] == [1]
    assert out["winners"]["box_value"]["winner_ids"] == [2]
    assert out["winners"]["rookies"]["winner_ids"] == [2]


def test_compare_refuses_low_quality_ev_winner():
    a = item(1,100,80,data=20,ev=(500,600))
    b = item(2,120,70,data=70,ev=(80,100))
    out = compare_items([a,b])
    assert out["winners"]["ev_ratio"]["winner_ids"] == [2]


def test_compare_can_report_insufficient_data():
    a = item(1,100,80,data=20,ev=None)
    b = item(2,120,70,data=20,ev=None)
    out = compare_items([a,b])
    assert out["winners"]["ev_ratio"]["reason"] == "insufficient_data"
