import math
from typing import Dict, Any, List

def is_card_rush_day(day: int) -> bool:
    if day <= 0: return False
    week = (day - 1) // 7 + 1
    weekday = (day - 1) % 7 + 1
    if week <= 2: return weekday == 6
    elif 3 <= week <= 5: return weekday in (3, 6)
    else: return weekday in (1, 3, 6)

def get_day_of_level(level: int, levels_per_day: int) -> int:
    if levels_per_day <= 0: return 1
    return math.ceil(level / levels_per_day)

def upgrade_pack(pack: str, is_cr: bool) -> str:
    if is_cr and pack in ("Bronze", "Emerald", "Silver"):
        return pack + "+"
    return pack

def test():
    for d in range(1, 40):
        print(f"Day {d} (Week {(d-1)//7+1}, Day {(d-1)%7+1}): CR? {is_card_rush_day(d)}")
test()
