import argparse
import io
import re
import time
from datetime import date
from pathlib import Path

import pandas as pd
import requests

HERE = Path(__file__).resolve().parent
COPI_CSV = HERE / 'data' / 'mauritius_copi.csv'
SITE = 'https://statsmauritius.govmu.org'
ROWS = {'LABOUR': 'labour', 'HIRE OF PLANT': 'plant', 'MATERIALS': 'materials', 'TRANSPORT': 'transport', 'TOTAL': 'total'}
INPUTS = ['labour', 'materials', 'plant', 'transport']
LETTERS = {'labour': 'L', 'materials': 'M', 'plant': 'H', 'transport': 'T'}
MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


def parse_release(content):
    for sheet in pd.read_excel(io.BytesIO(content), sheet_name=None, header=None).values():
        text = sheet.astype(str)
        if not text.apply(lambda c: c.str.contains('sub-indices by input category', case=False)).any().any():
            continue
        if not text.apply(lambda c: c.str.strip().str.upper().eq('LABOUR')).any().any():
            continue
        if not text.apply(lambda c: c.str.contains(r'Base: 1st Quarter\s+2018', case=False)).any().any():
            return pd.DataFrame()
        month = lambda v: str(v).strip()[:3].title()
        month_row = next(i for i in range(len(sheet)) if sum(month(v) in MONTHS for v in sheet.iloc[i]) >= 10)
        years = sheet.iloc[month_row - 1].ffill()
        cols = [c for c in sheet.columns if month(sheet.iat[month_row, c]) in MONTHS]
        dates = [pd.Timestamp(int(float(years[c])), MONTHS.index(month(sheet.iat[month_row, c])) + 1, 1) for c in cols]
        out = {}
        for i in range(month_row + 1, len(sheet)):
            label = re.sub(r'[^A-Z ]', '', str(sheet.iat[i, 0]).upper()).strip()
            if label in ROWS:
                out[ROWS[label]] = pd.to_numeric(sheet.loc[i, cols], errors='coerce').values
        return pd.DataFrame(out, index=pd.DatetimeIndex(dates, name='month'))
    return pd.DataFrame()


def fetch_copi(first_year=2020, pause=0.5):
    session = requests.Session()
    session.headers['User-Agent'] = 'Mozilla/5.0 (Task 5 internship assessment)'
    frames = []
    for year in range(first_year, date.today().year + 1):
        for quarter in range(1, 5):
            page = f'{SITE}/Pages/Statistics/ESI/CoPI/CoPI_{quarter}Qtr{year % 100:02d}.aspx'
            html = session.get(page, timeout=60).text
            link = re.search(r'href="([^"]*CoPI[^"]*\.xlsx?)"', html)
            time.sleep(pause)
            if link:
                frames.append(parse_release(session.get(SITE + link.group(1), timeout=60).content))
                time.sleep(pause)
    copi = pd.concat([f for f in frames if not f.empty]).groupby(level=0).last().sort_index()
    COPI_CSV.parent.mkdir(exist_ok=True)
    copi.to_csv(COPI_CSV)
    return copi


def load_copi():
    return pd.read_csv(COPI_CSV, index_col='month', parse_dates=True)


def annual_growth(copi, years):
    last = copi.index.max()
    start = last - pd.DateOffset(years=years)
    return (copi.loc[last] / copi.loc[start]) ** (1 / years) - 1


def index_path(copi, growth, months):
    last = copi.index.max()
    path = copi.reindex(months)
    for m in months[months > last]:
        step = (m.year - last.year) * 12 + m.month - last.month
        path.loc[m] = copi.loc[last] * (1 + growth) ** (step / 12)
    return path


def check(contract, copi, growth):
    start = pd.Timestamp(contract['start'] + '-01')
    months = pd.date_range(start, periods=int(contract['months']), freq='MS')
    path = index_path(copi, growth, months)
    base = copi.loc[start] if start in copi.index else index_path(copi, growth, pd.DatetimeIndex([start])).iloc[0]
    value = float(contract['value_mur'])
    margin = float(contract['target_margin'])
    shares = pd.Series({k: float(contract[k]) for k in INPUTS})
    bid_cost = value * (1 - margin)
    monthly = bid_cost / len(months)
    cost = sum(monthly * (1 - shares.sum() + (shares * path.loc[m, INPUTS] / base[INPUTS]).sum()) for m in months)
    weights = (shares * (1 - margin)).round(3)
    fixed = round(1 - weights.sum(), 3)
    formula = f'P = P0 x ({fixed}' + ''.join(
        f' + {weights[k]} x {LETTERS[k]}/{base[k]:.1f}' for k in INPUTS if weights[k] > 0) + ')'
    protected = str(contract.get('price_adjustment', 'no')).strip().lower() in ('yes', 'y', 'true', '1')
    revenue = value + (cost - bid_cost if protected else 0)
    return {
        'contract': contract['contract'],
        'value_mur': round(value),
        'months': int(contract['months']),
        'price_adjustment': 'yes' if protected else 'no',
        'cost_rise_pct': round((cost / bid_cost - 1) * 100, 2),
        'target_margin_pct': round(margin * 100, 2),
        'expected_margin_pct': round((1 - cost / revenue) * 100, 2),
        'margin_lost_mur': round(0 if protected else cost - bid_cost),
        'fixed_price_to_quote_mur': round(value if protected else cost / (1 - margin)),
        'clause': formula,
    }


def main():
    p = argparse.ArgumentParser(description='Margin at risk on fixed-price construction contracts in Mauritius')
    p.add_argument('contracts', help='CSV of contracts or bids')
    p.add_argument('--update', action='store_true', help='download the latest Construction Price Index first')
    p.add_argument('--years', type=int, default=3, help='years of index history used for the cost trend')
    p.add_argument('--out', default='escalation_results.csv', help='where to write the results')
    a = p.parse_args()
    copi = fetch_copi() if a.update or not COPI_CSV.exists() else load_copi()
    growth = annual_growth(copi, a.years)
    recent = annual_growth(copi, 1)
    print(f'Construction Price Index (Statistics Mauritius) to {copi.index.max():%B %Y}')
    print(f'  yearly trend used, last {a.years} years: ' + ', '.join(f'{k} {growth[k] * 100:.1f}%' for k in INPUTS))
    print('  for comparison, last 12 months: ' + ', '.join(f'{k} {recent[k] * 100:.1f}%' for k in INPUTS))
    results = pd.DataFrame([check(row, copi, growth) for _, row in pd.read_csv(a.contracts, dtype=str).iterrows()])
    results.to_csv(a.out, index=False)
    with pd.option_context('display.width', 200, 'display.max_colwidth', 80):
        print(results.drop(columns='clause').to_string(index=False))
    at_risk = results.loc[results.price_adjustment == 'no']
    print(f'\nMargin lost on contracts without a price adjustment clause: MUR {at_risk.margin_lost_mur.sum():,.0f}')
    print('Price adjustment clause for each contract (P0 = agreed price, L, M, H, T = index for the month invoiced):')
    for _, r in results.iterrows():
        print(f'  {r.contract}: {r.clause}')
    print(f'\nFull results written to {a.out}')


if __name__ == '__main__':
    main()
