# -*- coding: utf-8 -*-
from typing import List, Callable


def arrival_fn_factory(cycle: int, arrival_list: List[float] = None) -> Callable[[int], float]:
    def a(t: int) -> float:
        if t < 0:
            return 0.0
        else:
            return arrival_list[t % cycle]

    return a


def departure_fn_factory(cycle: int, green_split: float) -> Callable[[int], bool]:
    red = cycle - int(round(cycle * green_split))

    def d(t: int) -> bool:
        if t % cycle >= red:
            return True
        else:
            return False

    return d
