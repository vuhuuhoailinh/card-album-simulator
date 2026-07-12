import random

from .config import (
    MAX_CARDS,
    PACK_ORDER,
    RARITY_LABELS,
    STAR_VALUES,
    TOTAL_CARDS,
)
from .state import total_cards_collected

def rarity_label(rarity: int) -> str:
    return RARITY_LABELS[rarity]


def get_pity_bonus(session_state, pack_type: str) -> tuple[float, str]:
    if session_state["total_packs"] < 5:
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
                session_state["grand_album_completions"] = completions + 1
                add_log(session_state, "🏆 CHÚC MỪNG! Đã hoàn thành Album. Chuyển sang vòng Grand Album!")
            elif completions == 1 and not session_state.get("grand_album_finished", False):
                session_state["grand_album_finished"] = True
                add_log(session_state, "🏆 CHÚC MỪNG! Đã hoàn thành toàn bộ Grand Album! Các thẻ tiếp theo sẽ biến thành Sao.")


def calculate_new_chance(session_state, rarity: int, pity_bonus: float, pack_type: str) -> float:
    cards_owned = session_state["inventory"][rarity]
    max_cards = MAX_CARDS[rarity]
    if cards_owned >= max_cards:
        return 0.0

    base_new = (max_cards - cards_owned) / max_cards
    
    formula_type = session_state.get("new_card_formula_type", "document")
    power = session_state.get("new_card_power", 1.0)
    
    if formula_type == "document":
        pack_config = session_state["config_packs"].get(pack_type, {})
        y_val = pack_config.get("y_value", 0.0) if isinstance(pack_config, dict) else getattr(pack_config, "y_value", 0.0)
        final_power = power + y_val
    else:
        final_power = power
        
    base_new = base_new ** final_power
    return min(1.0, base_new + pity_bonus)


def roll_card(session_state, rarity: int, pity_bonus: float, pack_type: str) -> tuple[str, int]:
    new_chance = calculate_new_chance(session_state, rarity, pity_bonus, pack_type)

    if random.random() < new_chance:
        session_state["inventory"][rarity] += 1
        check_grand_album(session_state)
        return "NEW", rarity

    session_state["stars"] += STAR_VALUES[rarity]
    return "DUP", rarity


def open_pack(session_state, pack_type: str) -> None:
    session_state["total_packs"] += 1
    session_state["pack_counts"][pack_type] += 1

    pity_bonus, pity_message = get_pity_bonus(session_state, pack_type)
    pack_config = session_state["config_packs"][pack_type]
    effective_size = pack_config["size"]
    
    got_new = False
    raw_results = []

    for _ in range(effective_size - 1):
        rarity_str = random.choices(
            list(pack_config["weights"].keys()),
            weights=list(pack_config["weights"].values()),
        )[0]
        rarity = int(rarity_str)
        status, final_rarity = roll_card(session_state, rarity, pity_bonus, pack_type)
        got_new = got_new or status == "NEW"
        raw_results.append((status, final_rarity))

    is_rainbow = (pack_type == "Rainbow")
    if is_rainbow:
        wild_status, wild_rarity = open_rainbow_pack_guaranteed(session_state)
        got_new = got_new or (wild_status == "NEW")
        raw_results.append((wild_status, wild_rarity))
    else:
        guaranteed_tier = pack_config["guaranteed_tier"]
        guaranteed_rarity = guaranteed_tier
        status, final_rarity = roll_card(session_state, guaranteed_rarity, pity_bonus, pack_type)
        got_new = got_new or status == "NEW"
        raw_results.append((status, final_rarity))

    # Sort by rarity ascending
    raw_results.sort(key=lambda x: x[1])

    pack_results = []
    tagged_guarantee = False
    
    for status, rarity in raw_results:
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
                
        pack_results.append((status, rarity, guaranteed))

    update_pity(session_state, pack_type, got_new)
    add_log(session_state, format_pack_log(session_state, pack_type, pack_results, pity_message, got_new))


def open_rainbow_pack_guaranteed(session_state) -> tuple[str, int]:
    if session_state["inventory"][6] < MAX_CARDS[6]:
        session_state["inventory"][6] += 1
        check_grand_album(session_state)
        return "NEW", 6

    missing_rarities = [r for r in [1, 2, 3, 4, 5] if session_state["inventory"][r] < MAX_CARDS[r]]
    if missing_rarities:
        rarity = random.choice(missing_rarities)
        session_state["inventory"][rarity] += 1
        check_grand_album(session_state)
        return "NEW", rarity

    session_state["stars"] += STAR_VALUES[6]
    return "DUP", 6


def update_pity(session_state, pack_type: str, got_new: bool) -> None:
    if got_new:
        session_state["pack_pity"][pack_type] = 0
    else:
        session_state["pack_pity"].setdefault(pack_type, 0)
        session_state["pack_pity"][pack_type] += 1


def format_pack_log(session_state, pack_type: str, pack_results: list[tuple[str, int, bool]], pity_message: str, got_new: bool) -> str:
    result_parts = []
    for status, rarity, guaranteed in pack_results:
        label = f"{rarity}-Sao" if rarity < 6 else "Thẻ VÀNG"
        suffix = " [Bảo Hiểm]" if guaranteed else ""
        result_parts.append(f"{label} ({status}){suffix}")

    card_rush_note = ", Card Rush" if "+" in pack_type else ""

    prefix = "✅" if got_new else "❌"
    pack_count = session_state["pack_counts"][pack_type]
    return (
        f"{prefix} 📦 {pack_type} Pack #{pack_count}"
        f" (Buff: {pity_message}{card_rush_note}) | "
        f"Mở ra: {', '.join(result_parts)}"
    )


def open_bulk_packs(session_state, bulk_settings: dict[str, int]) -> tuple[bool, str]:
    total_to_open = sum(bulk_settings.values())
    if total_to_open == 0:
        return False, "⚠️ Vui lòng chọn ít nhất 1 pack để mở!"

    add_log(session_state, f"========== BẮT ĐẦU MỞ NHIỀU ({total_to_open} PACKS) ==========")
    for pack_type, count in bulk_settings.items():
        for _ in range(count):
            open_pack(session_state, pack_type)

    summary = ", ".join(f"{count} {pack_type}" for pack_type, count in bulk_settings.items() if count > 0)
    add_log(session_state, f"🌟 HOÀN THÀNH MỞ: {summary}")
    return True, f"Đã mở thành công {total_to_open} pack!"


def add_log(session_state, entry: str) -> None:
    session_state["log"].insert(0, entry)


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
        new_chance = calculate_new_chance(session_state, rarity, pity_bonus, pack_type)
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
