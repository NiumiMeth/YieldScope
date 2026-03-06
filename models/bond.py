from dataclasses import dataclass


@dataclass
class Bond:
    id: str
    issuer: str
    coupon: float
    years_to_maturity: float
    par: float
    yield_: float

    @staticmethod
    def from_series(s):
        return Bond(
            id=str(s['id']),
            issuer=str(s['issuer']),
            coupon=float(s['coupon']),
            years_to_maturity=float(s['years_to_maturity']),
            par=float(s['par']),
            yield_=float(s['yield'])
        )
