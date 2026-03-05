import sys
import pathlib
import pandas as pd

# ensure project root is on sys.path so we can import local packages
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from analytics.transactions import accrint, price_from_yield
from datetime import datetime


def parse_number(val):
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip()
    if s == '':
        return None
    for token in ['LKR', 'Rs', 'Rs.', 'LKR.', ',','"']:
        s = s.replace(token, '')
    s = s.strip()
    if s.endswith('%'):
        try:
            return float(s[:-1]) / 100.0
        except:
            return None
    try:
        return float(s)
    except:
        return None


def main():
    df = pd.read_csv('data/Details.csv')
    today = pd.Timestamp.today().normalize()

    rows = []
    for _, r in df.iterrows():
        isin = r.get('ISIN')
        face = parse_number(r.get('Maturity Value ')) or 0.0
        coupon_raw = r.get('Coupon')
        coupon = parse_number(coupon_raw) or 0.0
        if coupon > 1:
            coupon = coupon / 100.0
        maturity = r.get('Maturity Date')
        try:
            maturity_dt = pd.to_datetime(maturity)
        except:
            maturity_dt = None
        y_raw = r.get('Yield') or r.get('YTM')
        y = parse_number(y_raw) or 0.0
        if y > 1:
            y = y / 100.0

        # accrued and market value
        ai = 0.0
        mv = 0.0
        try:
            if maturity_dt is not None:
                ai = accrint(today, maturity_dt, coupon, face=face, freq=2)
                clean_pct = parse_number(r.get('Market value'))
                if clean_pct is None:
                    # fallback to price_from_yield
                    clean_pct = price_from_yield(today, maturity_dt, coupon, y, face=face, freq=2)
                # if market value in file looks like absolute amount (has large value), use it directly
                if clean_pct and clean_pct > 1000:
                    mv = clean_pct
                else:
                    mv = (clean_pct / 100.0) * face + ai
        except Exception as e:
            # fallback
            mv = 0.0

        rows.append({'ISIN': isin, 'Face': face, 'Coupon': coupon, 'Yield': y, 'Maturity': maturity_dt, 'Accrued': ai, 'MarketValue': mv})

    pdf = pd.DataFrame(rows)
    g = pdf.groupby('ISIN').agg({'Face':'sum','MarketValue':'sum','Yield':lambda x: (x*pdf.loc[x.index,'Face']).sum()/pdf.loc[x.index,'Face'].sum() if pdf.loc[x.index,'Face'].sum()>0 else None,'Accrued':'sum'})
    g = g.reset_index()
    print('Per-ISIN aggregates:')
    print(g.head(20).to_string(index=False))


if __name__ == '__main__':
    main()
