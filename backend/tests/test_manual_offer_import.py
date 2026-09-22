from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import Product, ProductVariant, Store
from app.services.manual_offer_import import import_offer_csv

def db_session():
    engine=create_engine('sqlite:///:memory:'); Base.metadata.create_all(engine); return sessionmaker(bind=engine)()

def test_csv_import_creates_offer_and_history():
    db=db_session()
    s=Store(name='CSV Store', policy_status='manual_allowed', collection_method='manual')
    p=Product(slug='ud-s1',canonical_name='2025-26 Upper Deck Series 1',category='Hockey',manufacturer='Upper Deck',year_season='2025-26',series='Series 1')
    db.add_all([s,p]); db.flush(); db.add(ProductVariant(product_id=p.id,format='Hobby Box',language='English',region='Global',packs=12,cards_per_pack=12)); db.commit()
    text='external_id,title,price_sek,stock_status,url\nabc,2025-26 Upper Deck Series 1 Hobby Box,799,in_stock,https://example.test/a\n'
    r=import_offer_csv(db,s,text)
    assert r['rows']==1 and r['created']==1
    assert r['matched']+r['review']==1

def test_csv_import_rejects_missing_columns():
    db=db_session(); s=Store(name='CSV Store 2', policy_status='manual_allowed', collection_method='manual'); db.add(s); db.commit()
    try: import_offer_csv(db,s,'title,price_sek\nX,10\n')
    except ValueError as e: assert 'external_id' in str(e)
    else: assert False
