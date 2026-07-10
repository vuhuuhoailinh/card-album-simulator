from dataclasses import dataclass


RARITIES = [1, 2, 3, 4, 5, 6]

MAX_CARDS = {1: 33, 2: 28, 3: 23, 4: 18, 5: 15, 6: 18}
STAR_VALUES = {1: 1, 2: 2, 3: 3, 4: 5, 5: 10, 6: 15}
TOTAL_CARDS = sum(MAX_CARDS.values())

RARITY_LABELS = {
    1: "Thẻ 1-Sao",
    2: "Thẻ 2-Sao",
    3: "Thẻ 3-Sao",
    4: "Thẻ 4-Sao",
    5: "Thẻ 5-Sao",
    6: "Thẻ VÀNG",
}


@dataclass(frozen=True)
class PackConfig:
    name: str
    size: int
    guaranteed_tier: int
    weights: dict[int, int]


PACKS = {
    "Bronze": PackConfig("Bronze", 2, 1, {1: 35, 2: 26, 3: 20, 4: 11, 5: 7, 6: 1}),
    "Emerald": PackConfig("Emerald", 3, 2, {1: 32, 2: 24, 3: 20, 4: 12, 5: 10, 6: 2}),
    "Silver": PackConfig("Silver", 4, 3, {1: 28, 2: 22, 3: 19, 4: 15, 5: 11, 6: 5}),
    "Amethyst": PackConfig("Amethyst", 5, 4, {1: 23, 2: 21, 3: 19, 4: 17, 5: 12, 6: 7}),
    "Ruby": PackConfig("Ruby", 6, 4, {1: 18, 2: 18, 3: 19, 4: 20, 5: 15, 6: 10}),
    "Gold": PackConfig("Gold", 6, 6, {1: 18, 2: 18, 3: 19, 4: 20, 5: 15, 6: 10}),
}

PACK_ORDER = ["Bronze", "Emerald", "Silver", "Amethyst", "Ruby", "Gold", "Rainbow"]
PACK_ICONS = {
    "Bronze": "🟫",
    "Emerald": "🟩",
    "Silver": "⬜",
    "Amethyst": "🟪",
    "Ruby": "🟥",
    "Gold": "🟨",
    "Rainbow": "🌈",
}

# Card Rush uses the "More!" pack sizes from the specification.
CARD_RUSH_PACK_SIZES = {"Bronze": 3, "Emerald": 5, "Silver": 6}
CARD_RUSH_PACKS = tuple(CARD_RUSH_PACK_SIZES.keys())
