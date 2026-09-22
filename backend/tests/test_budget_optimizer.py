from app.services.budget_optimizer import optimize_budget

PRODUCTS = [
    {'id':1,'name':'Hobby A','price':800,'box_value_score':86,'data_quality':90,'hit_density':70,'upside':88,'floor_score':55,'rookie_strength':80,'ev_low':500,'ev_high':700,'packs':12},
    {'id':2,'name':'Blaster B','price':300,'box_value_score':78,'data_quality':85,'hit_density':82,'upside':55,'floor_score':70,'rookie_strength':60,'ev_low':170,'ev_high':230,'packs':6},
    {'id':3,'name':'Booster C','price':100,'box_value_score':65,'data_quality':75,'hit_density':60,'upside':40,'floor_score':65,'rookie_strength':45,'ev_low':45,'ev_high':75,'packs':1},
]

def test_optimizer_stays_within_budget():
    recs = optimize_budget(PRODUCTS, 1000, 'balanced', 5)
    assert recs
    assert all(r.total_price <= 1000 for r in recs)


def test_fun_goal_can_reward_more_opening_volume():
    recs = optimize_budget(PRODUCTS, 600, 'fun', 3)
    assert recs
    assert any(sum(line.quantity for line in r.lines) >= 2 for r in recs)


def test_missing_ev_is_not_treated_as_zero():
    products = [dict(PRODUCTS[0], ev_low=None, ev_high=None)]
    rec = optimize_budget(products, 1000, 'value', 1)[0]
    assert rec.estimated_ev_low is None
    assert rec.data_coverage < 100
