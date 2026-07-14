import json
import copy
from .config import PACKS, PACK_ORDER
from .rewards_data import (
    MASTER_PASS_FREE,
    MASTER_PASS_PREMIUM,
    WIN_STREAK_REWARDS,
    KEY_COLLECTION_REWARDS,
)


def get_default_config() -> dict:
    """Returns the default configuration as a dictionary."""
    # Convert PACKS to dict
    packs_dict = {}
    for name in PACK_ORDER:
        if name in PACKS:
            p = PACKS[name]
            packs_dict[name] = {
                "size": p.size,
                "guaranteed_tier": p.guaranteed_tier,
                "y_value": p.y_value,
                "pity_threshold": p.pity_threshold,
                "pity_increment": p.pity_increment,
                "weights": {str(k): v for k, v in p.weights.items()},
            }

    return {
        "packs": packs_dict,
        "rewards": {
            "master_pass_free": copy.deepcopy(MASTER_PASS_FREE),
            "master_pass_premium": copy.deepcopy(MASTER_PASS_PREMIUM),
            "win_streak_rewards": copy.deepcopy(WIN_STREAK_REWARDS),
            "key_collection_rewards": copy.deepcopy(KEY_COLLECTION_REWARDS),
        },
        "system": {
            "new_card_power": 3.0,
            "new_card_formula_type": "document"
        }
    }


def load_config_to_state(session_state, config_dict=None) -> None:
    """Loads a configuration dictionary into session state."""
    if config_dict is None:
        config_dict = get_default_config()

    # Load packs
    session_state["config_packs"] = config_dict["packs"]

    # Load rewards (convert keys back to int if they were strings from JSON)
    rewards = config_dict["rewards"]
    session_state["config_rewards"] = {
        "master_pass_free": {int(k): v for k, v in rewards["master_pass_free"].items()},
        "master_pass_premium": {int(k): v for k, v in rewards["master_pass_premium"].items()},
        "win_streak_rewards": {int(k): v for k, v in rewards["win_streak_rewards"].items()},
        "key_collection_rewards": {int(k): v for k, v in rewards["key_collection_rewards"].items()},
    }
    
    if "system" in config_dict:
        session_state["new_card_power"] = config_dict["system"].get("new_card_power", 3.0)
        session_state["new_card_formula_type"] = config_dict["system"].get("new_card_formula_type", "simple")


def export_config_to_json(session_state) -> str:
    """Exports current session state config to JSON string."""
    config_dict = {
        "packs": session_state["config_packs"],
        "rewards": session_state["config_rewards"],
        "system": {
            "new_card_power": session_state.get("new_card_power", 3.0),
            "new_card_formula_type": session_state.get("new_card_formula_type", "simple")
        }
    }
    return json.dumps(config_dict, indent=4, ensure_ascii=False)


def import_config_from_json(session_state, json_str: str) -> bool:
    """Imports configuration from a JSON string into session state. Returns True if successful."""
    try:
        config_dict = json.loads(json_str)
        if "packs" not in config_dict or "rewards" not in config_dict:
            return False
        load_config_to_state(session_state, config_dict)
        return True
    except Exception:
        return False
