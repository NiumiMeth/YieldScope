import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
from portfolio.normalizer import normalize_portfolio
from analytics.transactions import accrint, price_from_yield


def main():
    path = Path('data') / 'Details.csv'
    if not path.exists():
        print('Details.csv not found in data/ — aborting')
        return
    df = pd.read_csv(path)
    ndf = normalize_portfolio(df)
    today = pd.Timestamp.today().normalize()

    rows = []
    for _, r in ndf.iterrows():
        isin = r.get('ISIN')
        face = r.get('Face') or 0.0
        coupon = r.get('Coupon') or 0.0
        maturity = r.get('Maturity Date')
        y = r.get('Yield') or 0.0
        ai = 0.0
        mv = 0.0
        try:
            if pd.notna(maturity):
                ai = accrint(today, maturity, coupon, face=face, freq=2)
                clean_pct = r.get('Market value')
                if clean_pct is None:
                    clean_pct = price_from_yield(today, maturity, coupon, y, face=face, freq=2)
                if clean_pct and clean_pct > 1000:
                    mv = clean_pct
                else:
                    mv = (clean_pct / 100.0) * face + ai
        except Exception:
            mv = 0.0
        rows.append({'ISIN': isin, 'Face': face, 'Coupon': coupon, 'Yield': y, 'Accrued': ai, 'MarketValue': mv})

    pdf = pd.DataFrame(rows)
    g = pdf.groupby('ISIN').agg({'Face':'sum','MarketValue':'sum','Yield':lambda x: (x*pdf.loc[x.index,'Face']).sum()/pdf.loc[x.index,'Face'].sum() if pdf.loc[x.index,'Face'].sum()>0 else None,'Accrued':'sum'})
    g = g.reset_index()
    print(g.to_string(index=False))


if __name__ == '__main__':
    main()
