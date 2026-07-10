import pandas as pd
from .state import ensure_album_state, total_cards_collected
from .gacha import open_pack
from .config import TOTAL_CARDS

class DummyLog(list):
    def insert(self, index, object):
        pass

def simulate_combo(bulk_settings: dict[str, int], card_rush: bool, grand_album: bool, power: float, pity_multiplier: float) -> dict:
    state = {}
    ensure_album_state(state)
    state["log"] = DummyLog()
    state["card_rush_enabled"] = card_rush
    state["new_card_power"] = power
    state["pity_multiplier"] = pity_multiplier
    
    grand_album_resets = 0
    
    for pack_type, count in bulk_settings.items():
        for _ in range(count):
            open_pack(state, pack_type)
            if grand_album and total_cards_collected(state) == TOTAL_CARDS:
                if grand_album_resets < 1:
                    grand_album_resets += 1
                    # Reset inventory for the next Grand Album run
                    state["inventory"] = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}
            
    return {
        "new_cards": (grand_album_resets * TOTAL_CARDS) + total_cards_collected(state),
        "stars_earned": state["stars"],
    }

def run_monte_carlo(num_players: int, bulk_settings: dict[str, int], card_rush: bool, grand_album: bool, power: float, pity_multiplier: float) -> pd.DataFrame:
    results = []
    for _ in range(num_players):
        results.append(simulate_combo(bulk_settings, card_rush, grand_album, power, pity_multiplier))
    return pd.DataFrame(results)
