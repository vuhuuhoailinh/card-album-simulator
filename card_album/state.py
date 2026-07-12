from .config import MAX_CARDS, PACK_ORDER


def fresh_inventory() -> dict[int, int]:
    return {rarity: 0 for rarity in MAX_CARDS}


def fresh_pack_counts() -> dict[str, int]:
    return {pack: 0 for pack in PACK_ORDER}


def ensure_album_state(session_state) -> None:
    if "config_packs" not in session_state:
        from .config_manager import load_config_to_state
        load_config_to_state(session_state)

    if "inventory" not in session_state:
        session_state["inventory"] = fresh_inventory()
    else:
        for rarity in MAX_CARDS:
            session_state["inventory"].setdefault(rarity, 0)

    if "stars" not in session_state:
        session_state["stars"] = 0
    if "total_packs" not in session_state:
        session_state["total_packs"] = 0

    if "pack_counts" not in session_state:
        session_state["pack_counts"] = fresh_pack_counts()
    else:
        for pack in PACK_ORDER:
            session_state["pack_counts"].setdefault(pack, 0)

    if "pack_pity" not in session_state:
        session_state["pack_pity"] = fresh_pack_counts()
    else:
        for pack in PACK_ORDER:
            session_state["pack_pity"].setdefault(pack, 0)

    if "log" not in session_state:
        session_state["log"] = []
    if "card_rush_enabled" not in session_state:
        session_state["card_rush_enabled"] = False
    if "grand_album_enabled" not in session_state:
        session_state["grand_album_enabled"] = True
    if "new_card_formula_type" not in session_state:
        session_state["new_card_formula_type"] = "simple"


def reset_progress(session_state) -> None:
    card_rush_enabled = session_state.get("card_rush_enabled", False)
    grand_album_enabled = session_state.get("grand_album_enabled", False)
    session_state.clear()
    ensure_album_state(session_state)
    session_state["card_rush_enabled"] = card_rush_enabled
    session_state["grand_album_enabled"] = grand_album_enabled


def total_cards_collected(session_state) -> int:
    return sum(session_state["inventory"].values())
