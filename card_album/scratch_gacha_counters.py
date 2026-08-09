import re

with open('d:/Python/demo/card_album/gacha.py', 'r', encoding='utf-8') as f:
    content = f.read()

# roll_card
content = content.replace(
    'session_state["new_cards_drawn"] += 1\n        check_grand_album',
    'session_state["new_cards_drawn"] += 1\n        session_state["new_cards_by_rarity"][rarity] += 1\n        check_grand_album'
)

content = content.replace(
    'session_state["dup_cards_drawn"] += 1\n    c = pick_dup_card',
    'session_state["dup_cards_drawn"] += 1\n    session_state["dup_cards_by_rarity"][rarity] += 1\n    c = pick_dup_card'
)

# open_rainbow_pack_guaranteed
content = content.replace(
    'session_state["new_cards_drawn"] += 1\n        check_grand_album(session_state)\n        if "recent_draws" in session_state: session_state["recent_draws"].append(("NEW", 6, c))',
    'session_state["new_cards_drawn"] += 1\n        session_state["new_cards_by_rarity"][6] += 1\n        check_grand_album(session_state)\n        if "recent_draws" in session_state: session_state["recent_draws"].append(("NEW", 6, c))'
)

content = content.replace(
    'session_state["new_cards_drawn"] += 1\n        check_grand_album(session_state)\n        if "recent_draws" in session_state: session_state["recent_draws"].append(("NEW", rarity, c))',
    'session_state["new_cards_drawn"] += 1\n        session_state["new_cards_by_rarity"][rarity] += 1\n        check_grand_album(session_state)\n        if "recent_draws" in session_state: session_state["recent_draws"].append(("NEW", rarity, c))'
)

content = content.replace(
    'session_state["dup_cards_drawn"] += 1\n    c = pick_dup_card(session_state, 6)',
    'session_state["dup_cards_drawn"] += 1\n    session_state["dup_cards_by_rarity"][6] += 1\n    c = pick_dup_card(session_state, 6)'
)

with open('d:/Python/demo/card_album/gacha.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated successfully")
