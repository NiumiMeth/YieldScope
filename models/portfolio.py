from typing import List
from .bond import Bond


class Portfolio:
    def __init__(self, bonds: List[Bond]):
        self.bonds = bonds

    @staticmethod
    def from_dataframe(df):
        bonds = [Bond.from_series(row) for _, row in df.iterrows()]
        return Portfolio(bonds)

    def total_par(self):
        return sum(b.par for b in self.bonds)

    def summary(self):
        return {
            'count': len(self.bonds),
            'total_par': self.total_par()
        }
