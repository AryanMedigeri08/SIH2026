import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, 'backend')
from app.core.odop_matcher import find_district_odop

test_cases = [
    ('Gujarat', 'Gir Somnath'),
    ('Gujarat', 'Gir-Somnath'),
    ('', 'Gir Somnath'),
    ('West Bengal', 'Bankura'),
    ('WB', 'Bankura District'),
    ('Maharashtra', 'Pune'),
    ('UP', 'Varanasi'),
    ('Uttar Pradesh', 'Moradabad'),
    ('', 'Gandhinagar'),
]

for s, d in test_cases:
    res = find_district_odop(s, d)
    m_name = res.get('matched_district_name') if res else 'None'
    m_state = res.get('matched_state_name') if res else 'None'
    prod = res.get('official_odop_product') if res else 'None'
    scheme = res.get('scheme_name') if res else 'None'
    sub = res.get('subsidy_summary') if res else 'None'
    print(f"{s or 'None'} / {d} -> {m_name} ({m_state}):")
    print(f"   ODOP: {prod}")
    print(f"   Scheme: {scheme} | Subsidy: {sub}")
