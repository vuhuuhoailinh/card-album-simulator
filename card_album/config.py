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
    y_value: float
    pity_threshold: int
    pity_increment: float


PACKS = {
    "Bronze": PackConfig("Bronze", 2, 1, {1: 35, 2: 26, 3: 20, 4: 11, 5: 7, 6: 1}, 1.0, 0, 0.0),
    "Bronze+": PackConfig("Bronze+", 3, 1, {1: 35, 2: 26, 3: 20, 4: 11, 5: 7, 6: 1}, 1.0, 0, 0.0),
    "Emerald": PackConfig("Emerald", 3, 2, {1: 32, 2: 24, 3: 20, 4: 12, 5: 10, 6: 2}, 0.5, 0, 0.0),
    "Emerald+": PackConfig("Emerald+", 5, 2, {1: 32, 2: 24, 3: 20, 4: 12, 5: 10, 6: 2}, 0.5, 0, 0.0),
    "Silver": PackConfig("Silver", 4, 3, {1: 28, 2: 22, 3: 19, 4: 15, 5: 11, 6: 5}, 0.0, 3, 0.20),
    "Silver+": PackConfig("Silver+", 6, 3, {1: 28, 2: 22, 3: 19, 4: 15, 5: 11, 6: 5}, 0.0, 3, 0.20),
    "Amethyst": PackConfig("Amethyst", 5, 4, {1: 23, 2: 21, 3: 19, 4: 17, 5: 12, 6: 7}, -0.5, 3, 0.20),
    "Ruby": PackConfig("Ruby", 6, 5, {1: 18, 2: 18, 3: 19, 4: 20, 5: 15, 6: 10}, -1.0, 2, 0.33),
    "Gold": PackConfig("Gold", 6, 6, {1: 18, 2: 18, 3: 19, 4: 20, 5: 15, 6: 10}, -1.0, 2, 0.33),
    "Rainbow": PackConfig("Rainbow", 6, 6, {1: 18, 2: 18, 3: 19, 4: 20, 5: 15, 6: 10}, -1.0, 0, 0.0),
}

# The actual distribution of 135 cards into 15 sets, based on their rarities.
# Key: Set ID (1-15), Value: Dict of {rarity: count}
CARD_SETS = {
    1: {"name": "Items", "cards": {1: 8, 2: 1}},
    2: {"name": "Transport", "cards": {1: 7, 2: 2}},
    3: {"name": "Souvenirs", "cards": {1: 7, 2: 1, 3: 1}},
    4: {"name": "Cuisine", "cards": {1: 5, 2: 3, 3: 1}},
    5: {"name": "Camping", "cards": {1: 3, 2: 4, 3: 1, 4: 1}},
    6: {"name": "Beach", "cards": {1: 2, 2: 4, 3: 1, 4: 1, 5: 1}},
    7: {"name": "Retreat", "cards": {1: 1, 2: 3, 3: 2, 4: 1, 5: 1, 6: 1}},
    8: {"name": "Theme Park", "cards": {2: 4, 3: 2, 4: 1, 5: 1, 6: 1}},
    9: {"name": "Nature", "cards": {2: 3, 3: 2, 4: 1, 5: 2, 6: 1}},
    10: {"name": "Ice Nature", "cards": {2: 2, 3: 2, 4: 2, 5: 1, 6: 2}},
    11: {"name": "Museum", "cards": {2: 1, 3: 3, 4: 1, 5: 2, 6: 2}},
    12: {"name": "Culture", "cards": {3: 3, 4: 2, 5: 2, 6: 2}},
    13: {"name": "Landmark", "cards": {3: 3, 4: 2, 5: 1, 6: 3}},
    14: {"name": "Festivals", "cards": {3: 2, 4: 2, 5: 2, 6: 3}},
    15: {"name": "Wonders", "cards": {4: 4, 5: 2, 6: 3}},
}

CHEST_CONFIG = {
    "Bronze": {"cost": 100, "packs": ["Silver"]},
    "Silver": {"cost": 250, "packs": ["Amethyst", "Silver"]},
    "Gold": {"cost": 500, "packs": ["Rainbow", "Amethyst", "Silver"]}
}

PACK_ORDER = ["Bronze", "Bronze+", "Emerald", "Emerald+", "Silver", "Silver+", "Amethyst", "Ruby", "Gold", "Rainbow"]
PACK_ICONS = {
    "Bronze": "🟫",
    "Bronze+": "🟫",
    "Emerald": "🟩",
    "Emerald+": "🟩",
    "Silver": "⬜",
    "Silver+": "⬜",
    "Amethyst": "🟪",
    "Ruby": "🟥",
    "Gold": "🟨",
    "Rainbow": "🌈",
}


# Configuration for the new Chest Drop (Win Streak) mini-game
@dataclass(frozen=True)
class ChestTierConfig:
    name: str
    upgrade_chance: float
    y_value: float
    weights: dict[int, int]

CHEST_DROP_TIERS = {
    1: ChestTierConfig("1-Sao", 0.35, 1.0, {1: 100, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}),
    2: ChestTierConfig("2-Sao", 0.35, 0.5, {1: 0, 2: 100, 3: 0, 4: 0, 5: 0, 6: 0}),
    3: ChestTierConfig("3-Sao", 0.20, 0.0, {1: 0, 2: 0, 3: 100, 4: 0, 5: 0, 6: 0}),
    4: ChestTierConfig("4-Sao", 0.15, -0.5, {1: 0, 2: 0, 3: 0, 4: 100, 5: 0, 6: 0}),
    5: ChestTierConfig("5-Sao", 0.0, -1.0, {1: 0, 2: 0, 3: 0, 4: 0, 5: 60, 6: 40})
}
