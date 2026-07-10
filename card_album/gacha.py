import random

from .config import (
    CARD_RUSH_PACK_SIZES,
    MAX_CARDS,
    PACKS,
    RARITY_LABELS,
    STAR_VALUES,
    TOTAL_CARDS,
)
from .state import total_cards_collected

SILVER_AMETHYST_PITY_PACKS = {"Silver", "Amethyst"}
RUBY_GOLD_PITY_PACKS = {"Ruby", "Gold"}


def rarity_label(rarity: int) -> str:
    return RARITY_LABELS[rarity]


def get_effective_pack_size(pack_type: str, card_rush_enabled: bool) -> int:
    if card_rush_enabled and pack_type in CARD_RUSH_PACK_SIZES:
        return CARD_RUSH_PACK_SIZES[pack_type]
    if pack_type == "Rainbow":
        return 1
    return PACKS[pack_type].size


def get_pity_bonus(session_state, pack_type: str) -> tuple[float, str]:
    if session_state["total_packs"] < 5:
        return 1.0, "+100% (5 Gói Đầu Tiên)"

    if pack_type in SILVER_AMETHYST_PITY_PACKS:
        misses = session_state["silver_amethyst_pity"]
        if misses >= 3:
            bonus = min(1.0, (misses - 2) * 0.20 * session_state.get("pity_multiplier", 1.0))
            return bonus, f"+{int(bonus * 100)}% (Tạch {misses} gói)"

    if pack_type in RUBY_GOLD_PITY_PACKS:
        misses = session_state["ruby_gold_pity"]
        if misses >= 2:
            bonus = min(1.0, (misses - 1) * 0.33 * session_state.get("pity_multiplier", 1.0))
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


def calculate_new_chance(session_state, rarity: int, pity_bonus: float) -> float:
    cards_owned = session_state["inventory"][rarity]
    max_cards = MAX_CARDS[rarity]
    if cards_owned >= max_cards:
        return 0.0

    base_new = (max_cards - cards_owned) / max_cards
    power = session_state.get("new_card_power", 1.0)
    base_new = base_new ** power
    return min(1.0, base_new + pity_bonus)


def roll_card(session_state, rarity: int, pity_bonus: float) -> tuple[str, int]:
    new_chance = calculate_new_chance(session_state, rarity, pity_bonus)

    if random.random() < new_chance:
        session_state["inventory"][rarity] += 1
        check_grand_album(session_state)
        return "NEW", rarity

    session_state["stars"] += STAR_VALUES[rarity]
    return "DUP", rarity


def open_pack(session_state, pack_type: str) -> None:
    session_state["total_packs"] += 1
    session_state["pack_counts"][pack_type] += 1

    if pack_type == "Rainbow":
        open_rainbow_pack(session_state)
        return

    pity_bonus, pity_message = get_pity_bonus(session_state, pack_type)
    pack_config = PACKS[pack_type]
    effective_size = get_effective_pack_size(
        pack_type,
        session_state.get("card_rush_enabled", False),
    )
    got_new = False
    pack_results = []

    for _ in range(effective_size - 1):
        rarity = random.choices(
            list(pack_config.weights.keys()),
            weights=list(pack_config.weights.values()),
        )[0]
        status, final_rarity = roll_card(session_state, rarity, pity_bonus)
        got_new = got_new or status == "NEW"
        pack_results.append((status, final_rarity, False))

    guaranteed_weights = {
        rarity: weight
        for rarity, weight in pack_config.weights.items()
        if rarity >= pack_config.guaranteed_tier
    }
    guaranteed_rarity = random.choices(
        list(guaranteed_weights.keys()),
        weights=list(guaranteed_weights.values()),
    )[0]
    status, final_rarity = roll_card(session_state, guaranteed_rarity, pity_bonus)
    got_new = got_new or status == "NEW"
    pack_results.append((status, final_rarity, True))

    update_pity(session_state, pack_type, got_new)
    add_log(session_state, format_pack_log(session_state, pack_type, pack_results, pity_message, got_new))


def open_rainbow_pack(session_state) -> None:
    total_packs = session_state["total_packs"]
    if session_state["inventory"][6] < MAX_CARDS[6]:
        session_state["inventory"][6] += 1
        add_log(session_state, f"✅ 🌈 Rainbow Pack (Gói #{total_packs}): Ra Thẻ VÀNG (NEW)")
        check_grand_album(session_state)
        return

    for rarity in [5, 4, 3, 2, 1]:
        if session_state["inventory"][rarity] < MAX_CARDS[rarity]:
            session_state["inventory"][rarity] += 1
            add_log(session_state, f"✅ 🌈 Rainbow Pack (Gói #{total_packs}): Ra Thẻ {rarity}-Sao (NEW)")
            check_grand_album(session_state)
            return

    session_state["stars"] += STAR_VALUES[6]
    add_log(session_state, f"⚠️ 🌈 Rainbow Pack (Gói #{total_packs}): Đã Full Album! Đổi thành {STAR_VALUES[6]} Sao.")


def update_pity(session_state, pack_type: str, got_new: bool) -> None:
    if pack_type in SILVER_AMETHYST_PITY_PACKS:
        session_state["silver_amethyst_pity"] = 0 if got_new else session_state["silver_amethyst_pity"] + 1
    if pack_type in RUBY_GOLD_PITY_PACKS:
        session_state["ruby_gold_pity"] = 0 if got_new else session_state["ruby_gold_pity"] + 1


def format_pack_log(session_state, pack_type: str, pack_results: list[tuple[str, int, bool]], pity_message: str, got_new: bool) -> str:
    result_parts = []
    for status, rarity, guaranteed in pack_results:
        label = f"{rarity}-Sao" if rarity < 6 else "Thẻ VÀNG"
        suffix = " [Bảo Hiểm]" if guaranteed else ""
        result_parts.append(f"{label} ({status}){suffix}")

    card_rush_note = ""
    if session_state.get("card_rush_enabled", False) and pack_type in CARD_RUSH_PACK_SIZES:
        card_rush_note = ", Card Rush"

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


def build_rate_rows(session_state, pack_type: str) -> list[dict[str, str]]:
    if pack_type == "Rainbow":
        return []

    pack_config = PACKS[pack_type]
    total_weight = sum(pack_config.weights.values())
    pity_bonus, _ = get_pity_bonus(session_state, pack_type)
    rows = []

    for rarity, weight in pack_config.weights.items():
        drop_rate = weight / total_weight
        new_chance = calculate_new_chance(session_state, rarity, pity_bonus)
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
