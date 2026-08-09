import re

with open('d:/Python/demo/card_album/gacha.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_pick = '''def pick_new_card(session_state, rarity: int):
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
'''

content = re.sub(r'def pick_new_card.*?session_state\["owned_cards"\].add\(chosen_card\)', new_pick.strip(), content, flags=re.DOTALL)

roll_card_orig = '''def roll_card(session_state, rarity: int, pity_bonus: float, pack_type: str) -> tuple[str, int]:
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
        pick_new_card(session_state, rarity)
        session_state["new_cards_drawn"] += 1
        check_grand_album(session_state)
        return "NEW", rarity

    session_state["stars"] += STAR_VALUES[rarity]
    session_state["dup_cards_drawn"] += 1
    return "DUP", rarity'''

roll_card_new = '''def roll_card(session_state, rarity: int, pity_bonus: float, pack_type: str) -> tuple[str, int, tuple]:
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
        check_grand_album(session_state)
        if "recent_draws" in session_state: session_state["recent_draws"].append(("NEW", rarity, c))
        return "NEW", rarity, c

    session_state["stars"] += STAR_VALUES[rarity]
    session_state["dup_cards_drawn"] += 1
    c = pick_dup_card(session_state, rarity)
    if "recent_draws" in session_state: session_state["recent_draws"].append(("DUP", rarity, c))
    return "DUP", rarity, c'''

content = content.replace(roll_card_orig, roll_card_new)

rainbow_orig = '''def open_rainbow_pack_guaranteed(session_state) -> tuple[str, int]:
    session_state["total_cards_drawn"] += 1
    if session_state["inventory"][6] < MAX_CARDS[6]:
        session_state["inventory"][6] += 1
        pick_new_card(session_state, 6)
        session_state["new_cards_drawn"] += 1
        check_grand_album(session_state)
        return "NEW", 6

    missing_rarities = [r for r in [1, 2, 3, 4, 5] if session_state["inventory"][r] < MAX_CARDS[r]]
    if missing_rarities:
        rarity = random.choice(missing_rarities)
        session_state["inventory"][rarity] += 1
        pick_new_card(session_state, rarity)
        session_state["new_cards_drawn"] += 1
        check_grand_album(session_state)
        return "NEW", rarity

    session_state["stars"] += STAR_VALUES[6]
    session_state["dup_cards_drawn"] += 1
    return "DUP", 6'''

rainbow_new = '''def open_rainbow_pack_guaranteed(session_state) -> tuple[str, int, tuple]:
    session_state["total_cards_drawn"] += 1
    if session_state["inventory"][6] < MAX_CARDS[6]:
        session_state["inventory"][6] += 1
        c = pick_new_card(session_state, 6)
        session_state["new_cards_drawn"] += 1
        check_grand_album(session_state)
        if "recent_draws" in session_state: session_state["recent_draws"].append(("NEW", 6, c))
        return "NEW", 6, c

    missing_rarities = [r for r in [1, 2, 3, 4, 5] if session_state["inventory"][r] < MAX_CARDS[r]]
    if missing_rarities:
        rarity = random.choice(missing_rarities)
        session_state["inventory"][rarity] += 1
        c = pick_new_card(session_state, rarity)
        session_state["new_cards_drawn"] += 1
        check_grand_album(session_state)
        if "recent_draws" in session_state: session_state["recent_draws"].append(("NEW", rarity, c))
        return "NEW", rarity, c

    session_state["stars"] += STAR_VALUES[6]
    session_state["dup_cards_drawn"] += 1
    c = pick_dup_card(session_state, 6)
    if "recent_draws" in session_state: session_state["recent_draws"].append(("DUP", 6, c))
    return "DUP", 6, c'''

content = content.replace(rainbow_orig, rainbow_new)

content = content.replace('status, final_rarity = roll_card(', 'status, final_rarity, specific_card = roll_card(')
content = content.replace('raw_results.append((status, final_rarity))', 'raw_results.append((status, final_rarity, specific_card))')
content = content.replace('wild_status, wild_rarity = open_rainbow_pack_guaranteed(', 'wild_status, wild_rarity, wild_specific_card = open_rainbow_pack_guaranteed(')
content = content.replace('raw_results.append((wild_status, wild_rarity))', 'raw_results.append((wild_status, wild_rarity, wild_specific_card))')
content = content.replace('for status, rarity in raw_results:', 'for status, rarity, specific_card in raw_results:')
content = content.replace('pack_results.append((status, rarity, guaranteed))', 'pack_results.append((status, rarity, specific_card, guaranteed))')

log_orig = '''def format_pack_log(session_state, pack_type: str, pack_results: list[tuple[str, int, bool]], pity_message: str, got_new: bool) -> str:
    result_parts = []
    for status, rarity, guaranteed in pack_results:
        label = f"{rarity}-Sao" if rarity < 6 else "Thẻ VÀNG"
        suffix = " [Bảo Hiểm]" if guaranteed else ""
        result_parts.append(f"{label} ({status}){suffix}")'''

log_new = '''def format_card_name(card):
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
        result_parts.append(f"{label} [{cname}] ({status}){suffix}")'''

content = content.replace(log_orig, log_new)

bulk_orig = '''    add_log(session_state, f"========== BẮT ĐẦU MỞ NHIỀU ({total_to_open} PACKS) ==========")
    
    start_new = session_state.get("new_cards_drawn", 0)'''

bulk_new = '''    add_log(session_state, f"========== BẮT ĐẦU MỞ NHIỀU ({total_to_open} PACKS) ==========")
    session_state["recent_draws"] = []
    start_new = session_state.get("new_cards_drawn", 0)'''
content = content.replace(bulk_orig, bulk_new)

bulk_orig2 = '''    new_drawn = session_state.get("new_cards_drawn", 0) - start_new
    dup_drawn = session_state.get("dup_cards_drawn", 0) - start_dup
    total_drawn = session_state.get("total_cards_drawn", 0) - start_total
    stars_diff = session_state.get("stars", 0) - start_stars
    
    return {
        "success": True, 
        "message": f"Đã mở thành công {total_to_open} pack!",
        "summary": summary,
        "new_cards": new_drawn,
        "dup_cards": dup_drawn,
        "total_cards": total_drawn,
        "stars_diff": stars_diff,
        "chests_opened": chests_opened
    }'''

bulk_new2 = '''    new_drawn = session_state.get("new_cards_drawn", 0) - start_new
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
    }'''
content = content.replace(bulk_orig2, bulk_new2)

with open('d:/Python/demo/card_album/gacha.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated successfully")
