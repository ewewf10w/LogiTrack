from dataclasses import dataclass


@dataclass(frozen=True)
class Dimensions:
    width: int
    height: int
    length: int

    @property
    def volume_m3(self) -> float:
        return (self.width * self.height * self.length) / 1_000_000


@dataclass(frozen=True)
class Weight:
    grams: int

    @property
    def kg(self) -> float:
        return self.grams / 1000
