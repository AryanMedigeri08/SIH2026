"""Isolated live demand check with synthetic, frozen unit/price/capacity facts."""
import argparse
import json
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.app.main import app  # Configure application paths.
from app.core.chat_service import chat_service
from app.core.demand_forecast import recover_forecast, forecast_payload


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live', action='store_true', help='Use configured LLM providers with synthetic data only')
    parser.add_argument('--details', action='store_true')
    args = parser.parse_args()
    if not args.live:
        print('Pass --live to exercise the configured LLM using a synthetic demand-only fixture.')
        return
    context = {'idea':'A startup makes ice cream and sells 100 ml cups directly to local people',
        'business_category':'manufacturing', 'business_type':'manufacturing', 'sector':'dairy',
        'households':1000, 'population_projection':{'projected_population':4800},
        'location':{'village':'Synthetic village', 'state':'Maharashtra'},
        'amenities':{'power_supply_hours_per_day':12, 'source':'synthetic fixture'},
        'evidence_type':'synthetic test; no observed footfall, buyer records or verified market benchmark'}
    values = SimpleNamespace(product='Ice cream in 100 ml cups', output_unit='cups', selling_price_inr=20)
    conversion = SimpleNamespace(working_days_per_month=25, saleable_unit_definition='One 100 ml cup of ice cream')
    result, flags, reviewed, model = recover_forecast(context, values, conversion, 5000,
        None, 'Isolated demand-only validation. Unit, price and physical capacity are frozen synthetic fixtures.',
        chat_service._call_llm_chat_completion)
    if result is None:
        raise SystemExit('The demand model did not validate; production report fallback remains available.')
    payload = forecast_payload(result,flags,reviewed,model)
    summary = {key:payload[key] for key in ('business_model','method','buyer_base','output_unit','provisional','warnings','review_status','limitations','model')}
    summary['scenarios'] = {name:{key:row[key] for key in ('monthly_demand_units','realized_monthly_units','monthly_active_buyers','monthly_transactions','daily_unit_sales','monthly_revenue_inr')} for name,row in payload['scenarios'].items()}
    print(json.dumps(payload if args.details else summary, ensure_ascii=True))


if __name__ == '__main__':
    main()
