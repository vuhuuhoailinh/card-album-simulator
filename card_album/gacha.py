import random

from .config import (
    MAX_CARDS,
    PACK_ORDER,
    RARITY_LABELS,
    STAR_VALUES,
    TOTAL_CARDS,
    CARD_SETS,
    CHEST_CONFIG,
)
from .state import total_cards_collected

def rarity_label(rarity: int) -> str:
    return RARITY_LABELS[rarity]



def get_pity_bonus(session_state, pack_type: str) -> tuple[float, str]:
    if session_state.get("total_packs", 0) <= 5:
        return 1.0, "+100% (5 Gói Đầu Tiên)"

    pack_config = session_state["config_packs"][pack_type]
    threshold = pack_config.get("pity_threshold", 0)
    increment = pack_config.get("pity_increment", 0.0)
    misses = session_state["pack_pity"].get(pack_type, 0)
    
    if threshold > 0 and misses >= threshold:
        bonus = min(1.0, (misses - threshold + 1) * increment * session_state.get("pity_multiplier", 1.0))
        if bonus > 0:
            return bonus, f"+{int(bonus * 100)}% (Tạch {misses} gói)"

    return 0.0, "0% (Bình thường)"


def check_grand_album(session_state) -> None:
    if session_state.get("grand_album_enabled", False):
        if total_cards_collected(session_state) == TOTAL_CARDS:
            completions = session_state.get("grand_album_completions", 0)
            if completions < 1:
                session_state["inventory"] = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}
                session_state["owned_cards"] = set()
                session_state["grand_album_completions"] = completions + 1
                add_log(session_state, "🏆 CHÚC MỪNG! Đã hoàn thành Album. Chuyển sang vòng Grand Album!")
            elif completions == 1 and not session_state.get("grand_album_finished", False):
                session_state["grand_album_finished"] = True
                add_log(session_state, "🏆 CHÚC MỪNG! Đã hoàn thành toàn bộ Grand Album! Các thẻ tiếp theo sẽ biến thành Sao.")


def calculate_new_chance(session_state, rarity: int, pack_type: str) -> float:
    cards_owned = session_state["inventory"][rarity]
    max_cards = MAX_CARDS[rarity]
    if cards_owned >= max_cards:
        return 0.0

    base_new = (max_cards - cards_owned) / max_cards
    
    formula_type = session_state.get("new_card_formula_type", "document")
    power = session_state.get("new_card_power", 3.0)
    
    if formula_type == "document":
        pack_config = session_state["config_packs"].get(pack_type, {})
        y_val = pack_config.get("y_value", 0.0) if isinstance(pack_config, dict) else getattr(pack_config, "y_value", 0.0)
        final_power = power + y_val
    else:
        final_power = power
        
    return min(1.0, base_new ** final_power)


def pick_new_card(session_state, rarity: int):
    possible_cards = []
    from .config import CARD_SETS
    for set_id, set_info in CARD_SETS.items():
        if rarity in set_info["cards"]:
            count = set_info["cards"][rarity]
            for idx in range(count):
                possible_cards.append((set_id, rarity, idx))
                
    missing_cards = [c for c in possible_cards if c not in session_state["owned_cards"]]
    import random
    if missing_cards:
        chosen_card = random.choice(missing_cards)
        session_state["owned_cards"].add(chosen_card)
        return chosen_card
    return None

def pick_dup_card(session_state, rarity: int):
    owned = [c for c in session_state["owned_cards"] if c[1] == rarity]
    import random
    if owned:
        return random.choice(owned)
    possible_cards = []
    from .config import CARD_SETS
    for set_id, set_info in CARD_SETS.items():
        if rarity in set_info["cards"]:
            count = set_info["cards"][rarity]
            for idx in range(count):
                possible_cards.append((set_id, rarity, idx))
    return random.choice(possible_cards) if possible_cards else None

def roll_card(session_state, rarity: int, pity_bonus: float, pack_type: str) -> tuple[str, int, tuple]:
    session_state["total_cards_drawn"] += 1
    cards_owned = session_state["inventory"][rarity]
    max_cards = MAX_CARDS[rarity]
    
    if cards_owned >= max_cards:
        final_chance = 0.0
    else:
        new_chance = calculate_new_chance(session_state, rarity, pack_type)
        final_chance = min(1.0, new_chance + pity_bonus)

    if random.random() < final_chance:
        session_state["inventory"][rarity] += 1
        c = pick_new_card(session_state, rarity)
        session_state["new_cards_drawn"] += 1
        session_state["new_cards_by_rarity"][rarity] += 1
        check_grand_album(session_state)
        if "recent_draws" in session_state: session_state["recent_draws"].append(("NEW", rarity, c))
        return "NEW", rarity, c

    session_state["stars"] += STAR_VALUES[rarity]
    session_state["dup_cards_drawn"] += 1
    session_state["dup_cards_by_rarity"][rarity] += 1
    c = pick_dup_card(session_state, rarity)
    if "recent_draws" in session_state: session_state["recent_draws"].append(("DUP", rarity, c))
    return "DUP", rarity, c


def open_pack(session_state, pack_type: str) -> None:
    session_state["total_packs"] += 1
    session_state["pack_counts"][pack_type] += 1

    pity_bonus, pity_message = get_pity_bonus(session_state, pack_type)
    pack_config = session_state["config_packs"][pack_type]
    effective_size = pack_config["size"]
    
    got_new = False
    raw_results = []
    current_pity_bonus = pity_bonus

    for _ in range(effective_size - 1):
        rarity_str = random.choices(
            list(pack_config["weights"].keys()),
            weights=list(pack_config["weights"].values()),
        )[0]
        rarity = int(rarity_str)
        status, final_rarity, specific_card = roll_card(session_state, rarity, current_pity_bonus, pack_type)
        if status == "NEW":
            got_new = True
            if session_state.get("total_packs", 0) > 5:
                current_pity_bonus = 0.0 # Reset immediately when a new card is chosen
        raw_results.append((status, final_rarity, specific_card))

    is_rainbow = (pack_type == "Rainbow")
    if is_rainbow:
        wild_status, wild_rarity, wild_specific_card = open_rainbow_pack_guaranteed(session_state)
        if wild_status == "NEW":
            got_new = True
            current_pity_bonus = 0.0
        raw_results.append((wild_status, wild_rarity, wild_specific_card))
    else:
        guaranteed_tier = pack_config["guaranteed_tier"]
        guaranteed_rarity = guaranteed_tier
        status, final_rarity, specific_card = roll_card(session_state, guaranteed_rarity, current_pity_bonus, pack_type)
        if status == "NEW":
            got_new = True
            current_pity_bonus = 0.0
        raw_results.append((status, final_rarity, specific_card))

    # Sort by rarity ascending
    raw_results.sort(key=lambda x: x[1])

    pack_results = []
    tagged_guarantee = False
    
    for status, rarity, specific_card in raw_results:
        guaranteed = False
        if is_rainbow:
            # For Rainbow, just tag the first NEW one as the "guaranteed" if any
            if status == "NEW" and not tagged_guarantee:
                guaranteed = True
                tagged_guarantee = True
        else:
            # Tag the first card that matches the guaranteed tier exactly
            if rarity == pack_config["guaranteed_tier"] and not tagged_guarantee:
                guaranteed = True
                tagged_guarantee = True
                
        pack_results.append((status, rarity, specific_card, guaranteed))

    update_pity(session_state, pack_type, got_new)
    add_log(session_state, format_pack_log(session_state, pack_type, pack_results, pity_message, got_new))


def open_rainbow_pack_guaranteed(session_state) -> tuple[str, int, tuple]:
    session_state["total_cards_drawn"] += 1
    if session_state["inventory"][6] < MAX_CARDS[6]:
        session_state["inventory"][6] += 1
        c = pick_new_card(session_state, 6)
        session_state["new_cards_drawn"] += 1
        session_state["new_cards_by_rarity"][6] += 1
        check_grand_album(session_state)
        if "recent_draws" in session_state: session_state["recent_draws"].append(("NEW", 6, c))
        return "NEW", 6, c

    missing_rarities = [r for r in [1, 2, 3, 4, 5] if session_state["inventory"][r] < MAX_CARDS[r]]
    if missing_rarities:
        rarity = random.choice(missing_rarities)
        session_state["inventory"][rarity] += 1
        c = pick_new_card(session_state, rarity)
        session_state["new_cards_drawn"] += 1
        session_state["new_cards_by_rarity"][rarity] += 1
        check_grand_album(session_state)
        if "recent_draws" in session_state: session_state["recent_draws"].append(("NEW", rarity, c))
        return "NEW", rarity, c

    session_state["stars"] += STAR_VALUES[6]
    session_state["dup_cards_drawn"] += 1
    session_state["dup_cards_by_rarity"][6] += 1
    c = pick_dup_card(session_state, 6)
    if "recent_draws" in session_state: session_state["recent_draws"].append(("DUP", 6, c))
    return "DUP", 6, c


def update_pity(session_state, pack_type: str, got_new: bool) -> None:
    if got_new:
        session_state["pack_pity"][pack_type] = 0
    else:
        session_state["pack_pity"].setdefault(pack_type, 0)
        session_state["pack_pity"][pack_type] += 1


def format_card_name(card):
    from .config import CARD_SETS
    if not card: return "?"
    set_id, rarity, idx = card
    return f"{CARD_SETS[set_id]['name']} #{idx+1}"

def format_pack_log(session_state, pack_type: str, pack_results: list[tuple[str, int, tuple, bool]], pity_message: str, got_new: bool) -> str:
    result_parts = []
    for status, rarity, specific_card, guaranteed in pack_results:
        label = f"{rarity}-Sao" if rarity < 6 else "Thẻ VÀNG"
        cname = format_card_name(specific_card)
        suffix = " [Bảo Hiểm]" if guaranteed else ""
        result_parts.append(f"{label} [{cname}] ({status}){suffix}")

    card_rush_note = ", Card Rush" if "+" in pack_type else ""

    prefix = "✅" if got_new else "❌"
    pack_count = session_state["pack_counts"][pack_type]
    return (
        f"{prefix} 📦 {pack_type} Pack #{pack_count}"
        f" (Buff: {pity_message}{card_rush_note}) | "
        f"Mở ra: {', '.join(result_parts)}"
    )


def open_chest(session_state, chest_type: str) -> dict:
    if chest_type not in CHEST_CONFIG:
        return {"success": False, "message": f"⚠️ Không tìm thấy rương {chest_type}!"}
    cost = CHEST_CONFIG[chest_type]["cost"]
    if session_state["stars"] < cost:
        return {"success": False, "message": f"⚠️ Không đủ Sao! Cần {cost}⭐ để mở Rương {chest_type}."}
    
    start_total = session_state.get("total_cards_drawn", 0)
    start_stars = session_state.get("stars", 0)
    
    session_state["stars"] -= cost
    add_log(session_state, f"🌟 Đổi {cost}⭐ để mở {chest_type} Chest!")
    packs_to_open = CHEST_CONFIG[chest_type]["packs"]
    
    # Check if card rush is enabled and apply +
    is_cr = session_state.get("card_rush_enabled", False)
    
    has_recent = "recent_draws" in session_state
    if not has_recent:
        session_state["recent_draws"] = []
        
    opened_packs = []
    for base_pack in packs_to_open:
        pack_type = f"{base_pack}+" if is_cr and f"{base_pack}+" in session_state["config_packs"] else base_pack
        open_pack(session_state, pack_type)
        opened_packs.append(pack_type)
        
    total_drawn = session_state.get("total_cards_drawn", 0) - start_total
    stars_diff = session_state.get("stars", 0) - start_stars
    
    # We only slice the recent_draws added during THIS chest if has_recent was True, but actually returning everything is fine if it's ignored by open_bulk_packs
    new_cards_list = [c for s, r, c in session_state.get("recent_draws", []) if s == "NEW"]
    dup_cards_list = [c for s, r, c in session_state.get("recent_draws", []) if s == "DUP"]
    
    if not has_recent:
        del session_state["recent_draws"]
    
    return {
        "success": True,
        "chest_type": chest_type,
        "message": f"Mở thành công {chest_type} Chest!",
        "summary": ", ".join(opened_packs),
        "total_cards": total_drawn,
        "stars_diff": stars_diff,
        "new_cards_list": new_cards_list,
        "dup_cards_list": dup_cards_list
    }

def open_bulk_packs(session_state, bulk_settings: dict[str, int], auto_chest: bool = False) -> dict:
    total_to_open = sum(bulk_settings.values())
    if total_to_open == 0:
        return {"success": False, "message": "⚠️ Vui lòng chọn ít nhất 1 pack để mở!"}

    if total_to_open > 1:
        add_log(session_state, f"========== BẮT ĐẦU MỞ NHIỀU ({total_to_open} PACKS) ==========")
    session_state["recent_draws"] = []
    start_new = session_state.get("new_cards_drawn", 0)
    start_dup = session_state.get("dup_cards_drawn", 0)
    start_total = session_state.get("total_cards_drawn", 0)
    start_stars = session_state.get("stars", 0)
    chests_opened = 0
    chests_breakdown = {"Gold": 0, "Silver": 0, "Bronze": 0}
    
    for pack_type, count in bulk_settings.items():
        for _ in range(count):
            open_pack(session_state, pack_type)

    if auto_chest:
        max_auto_chests = 500
        while session_state["stars"] >= 100 and chests_opened < max_auto_chests:
            if session_state["stars"] >= 500:
                open_chest(session_state, "Gold")
                chests_opened += 1
                chests_breakdown["Gold"] += 1
            elif session_state["stars"] >= 250:
                open_chest(session_state, "Silver")
                chests_opened += 1
                chests_breakdown["Silver"] += 1
            elif session_state["stars"] >= 100:
                open_chest(session_state, "Bronze")
                chests_opened += 1
                chests_breakdown["Bronze"] += 1
                
        if session_state["stars"] >= 100 and chests_opened >= max_auto_chests:
            add_log(session_state, "⚠️ Dừng tự động mở rương do đạt giới hạn an toàn (500 rương) để tránh treo máy!")

    summary = ", ".join(f"{count} {pack_type}" for pack_type, count in bulk_settings.items() if count > 0)
    chest_parts = []
    if chests_breakdown["Gold"] > 0: chest_parts.append(f"{chests_breakdown['Gold']} Rương Vàng")
    if chests_breakdown["Silver"] > 0: chest_parts.append(f"{chests_breakdown['Silver']} Rương Bạc")
    if chests_breakdown["Bronze"] > 0: chest_parts.append(f"{chests_breakdown['Bronze']} Rương Đồng")
    
    if chest_parts:
        chest_str = " + ".join(chest_parts)
        if summary: summary += f" + {chest_str}"
        else: summary = chest_str
    
    if total_to_open > 1 or chests_opened > 0:
        add_log(session_state, f"🌟 HOÀN THÀNH MỞ: {summary}")
    
    new_drawn = session_state.get("new_cards_drawn", 0) - start_new
    dup_drawn = session_state.get("dup_cards_drawn", 0) - start_dup
    total_drawn = session_state.get("total_cards_drawn", 0) - start_total
    stars_diff = session_state.get("stars", 0) - start_stars
    
    new_cards_list = [c for s, r, c in session_state.get("recent_draws", []) if s == "NEW"]
    dup_cards_list = [c for s, r, c in session_state.get("recent_draws", []) if s == "DUP"]
    if "recent_draws" in session_state: del session_state["recent_draws"]

    return {
        "success": True, 
        "message": f"Đã mở thành công {total_to_open} pack!",
        "summary": summary,
        "new_cards": new_drawn,
        "dup_cards": dup_drawn,
        "total_cards": total_drawn,
        "stars_diff": stars_diff,
        "chests_opened": chests_opened,
        "new_cards_list": new_cards_list,
        "dup_cards_list": dup_cards_list
    }


def add_log(session_state, entry: str) -> None:
    session_state["log"].insert(0, entry)
    if len(session_state["log"]) > 300:
        session_state["log"] = session_state["log"][:300]


def build_rate_rows(session_state, pack_type: str) -> list[dict]:
    if pack_type == "Rainbow":
        return []

    pack_config = session_state["config_packs"][pack_type]
    total_weight = sum(pack_config["weights"].values())
    pity_bonus, _ = get_pity_bonus(session_state, pack_type)
    rows = []

    for rarity_str, weight in pack_config["weights"].items():
        rarity = int(rarity_str)
        drop_rate = weight / total_weight
        new_chance = calculate_new_chance(session_state, rarity, pack_type)
        duplicate_chance = 1.0 - new_chance
        new_value = f"{new_chance * 100:.1f}%"
        if pity_bonus > 0 and session_state["inventory"][rarity] < MAX_CARDS[rarity]:
            new_value += f" (+{pity_bonus * 100:.0f}%)"

        rows.append(
            {
                "Độ hiếm": f"{rarity}-Sao" if rarity < 6 else "VÀNG",
                "Khả năng Rớt": f"{drop_rate * 100:.1f}%",
                "Thẻ MỚI": new_value,
                "Thẻ TRÙNG": f"{duplicate_chance * 100:.1f}% (+{STAR_VALUES[rarity]}⭐)",
            }
        )

    return rows
