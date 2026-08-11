import pandas as pd
import streamlit as st
import altair as alt

from ..config import (
    MAX_CARDS,
    PACK_ICONS,
    PACK_ORDER,
    PACKS,
    RARITIES,
    TOTAL_CARDS,
)
from ..gacha import build_rate_rows, get_pity_bonus, open_bulk_packs, open_pack, open_chest, rarity_label
from ..state import ensure_album_state, reset_progress, total_cards_collected
from ..liveops_simulator import simulate_liveops

def format_card_name_ui(card):
    if not card: return "Unknown"
    from ..config import CARD_SETS
    set_id, rarity, idx = card
    return f"{CARD_SETS[set_id]['name']} #{idx+1}"


