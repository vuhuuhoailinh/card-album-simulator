import math
import re
from typing import Dict, Any, List
from .config import PACK_ORDER

def is_card_rush_day(day: int) -> bool:
    if day <= 0: return False
    week = (day - 1) // 7 + 1
    weekday = (day - 1) % 7 + 1
    if week <= 2: return weekday == 6
    elif 3 <= week <= 5: return weekday in (3, 6)
    else: return weekday in (1, 3, 6)

def get_day_of_level(level: int, levels_per_weekday: int, levels_per_weekend: int) -> int:
    if levels_per_weekday <= 0 and levels_per_weekend <= 0: return 1
    total = 0
    day = 1
    while True:
        weekday = (day - 1) % 7 + 1
        total += levels_per_weekend if weekday in (5, 6, 7) else levels_per_weekday
        if level <= total:
            return day
        day += 1

def get_day_string(day: int) -> str:
    week = (day - 1) // 7 + 1
    weekday = (day - 1) % 7 + 1
    days_map = {1: "Thứ 2", 2: "Thứ 3", 3: "Thứ 4", 4: "Thứ 5", 5: "Thứ 6", 6: "Thứ 7", 7: "Chủ Nhật"}
    return f"Tuần {week} - {days_map[weekday]}"

def upgrade_pack(pack: str, is_cr: bool) -> str:
    if is_cr and pack in ("Bronze", "Emerald", "Silver"):
        return pack + "+"
    return pack

def add_packs_from_string(reward_str: str, packs_dict: dict, is_cr: bool, day: int = 0, source: str = "", cr_detailed_logs: list = None):
    if not isinstance(reward_str, str):
        reward_str = str(reward_str)
    for base in ["Bronze", "Emerald", "Silver", "Amethyst", "Ruby", "Gold", "Rainbow"]:
        matches = re.findall(rf"(?:(\d+)[xX]\s*)?[*]*\s*{base}", reward_str, re.IGNORECASE)
        total_to_add = 0
        for match in matches:
            total_to_add += int(match) if match else 1
            
        if total_to_add > 0:
            upgraded = upgrade_pack(base, is_cr)
            packs_dict[upgraded] += total_to_add
            if is_cr and upgraded != base and cr_detailed_logs is not None:
                cr_detailed_logs.append(f"Đã nâng cấp {total_to_add} gói {base} → {upgraded} (Từ {source} vào {get_day_string(day)})")

def calculate_levels(days: int, levels_per_weekday: int, levels_per_weekend: int) -> Dict[str, int]:
    total_levels = 0
    for day in range(1, days + 1):
        weekday = (day - 1) % 7 + 1
        total_levels += levels_per_weekend if weekday in (5, 6, 7) else levels_per_weekday
    full_cycles = total_levels // 9
    remainder = total_levels % 9
    
    normal = full_cycles * 6
    hard = full_cycles * 2
    super_hard = full_cycles * 1
    
    pattern = ['N', 'N', 'H', 'N', 'N', 'H', 'N', 'N', 'SH']
    for i in range(remainder):
        if pattern[i] == 'N': normal += 1
        elif pattern[i] == 'H': hard += 1
        elif pattern[i] == 'SH': super_hard += 1
            
    return {
        "total": total_levels,
        "normal": normal,
        "hard": hard,
        "super_hard": super_hard
    }

def simulate_core_gameplay(days: int, levels_per_weekday: int, levels_per_weekend: int, cr_enabled: bool, cr_detailed_logs: list, core_enabled: bool = True) -> Dict[str, Any]:
    packs = {"Bronze": 0, "Bronze+": 0, "Emerald": 0, "Emerald+": 0}
    logs = []
    
    bronze_count = 0
    emerald_count = 0
    bronze_plus = 0
    emerald_plus = 0
    
    level = 0
    for day in range(1, days + 1):
        weekday = (day - 1) % 7 + 1
        lpd = levels_per_weekend if weekday in (5, 6, 7) else levels_per_weekday
        is_cr = cr_enabled and is_card_rush_day(day)
        
        for _ in range(lpd):
            level += 1
            if level % 3 == 0 and level % 9 != 0:
                if is_cr and core_enabled: 
                    bronze_plus += 1
                    cr_detailed_logs.append(f"Đã nâng cấp 1 gói Bronze → Bronze+ (Từ Cày Cuốc [Màn Hard] vào {get_day_string(day)})")
                elif core_enabled:
                    bronze_count += 1
            elif level % 9 == 0:
                if is_cr and core_enabled: 
                    emerald_plus += 1
                    cr_detailed_logs.append(f"Đã nâng cấp 1 gói Emerald → Emerald+ (Từ Cày Cuốc [Màn Super Hard] vào {get_day_string(day)})")
                elif core_enabled:
                    emerald_count += 1
            
    packs["Bronze"] = bronze_count
    packs["Bronze+"] = bronze_plus
    packs["Emerald"] = emerald_count
    packs["Emerald+"] = emerald_plus
    
    tot_bronze = bronze_count + bronze_plus
    tot_emerald = emerald_count + emerald_plus
    logs.append(f"**Tổng kết:** Chiến thắng {tot_bronze} màn Hard, {tot_emerald} màn Super Hard")
    logs.append(f"- Màn Hard: {bronze_count} Bronze, {bronze_plus} Bronze+")
    logs.append(f"- Màn Super Hard: {emerald_count} Emerald, {emerald_plus} Emerald+")
    
    return {"packs": packs, "logs": logs}

def simulate_win_streak(days: int, levels_per_weekday: int, levels_per_weekend: int, cr_enabled: bool, cr_detailed_logs: list, config_rewards: dict) -> Dict[str, Any]:
    packs = {"Bronze": 0, "Bronze+": 0, "Emerald": 0, "Emerald+": 0, "Silver": 0, "Silver+": 0, "Amethyst": 0, "Ruby": 0, "Gold": 0, "Rainbow": 0}
    logs = []
    
    total_level = 0
    event_count = 0
    event_wins = 0
    claimed_milestones = set()
    has_avatar = False
    
    for day in range(1, days + 1):
        weekday = (day - 1) % 7 + 1
        is_cr = cr_enabled and is_card_rush_day(day)
        
        # Reset event every Friday
        if weekday == 5:
            event_count += 1
            event_wins = 0
            claimed_milestones = set()
            
        lpd = levels_per_weekend if weekday in (5, 6, 7) else levels_per_weekday
        for _ in range(lpd):
            total_level += 1
            # Event is active Friday, Saturday, Sunday
            if weekday in (5, 6, 7):
                event_wins += 1
                
                # Check milestones immediately upon winning a level
                for req_wins, reward_str in config_rewards["win_streak_rewards"].items():
                    if event_wins == req_wins and req_wins not in claimed_milestones:
                        claimed_milestones.add(req_wins)
                        
                        reward_str_to_process = reward_str
                        if "Avatar" in reward_str:
                            if not has_avatar:
                                has_avatar = True
                                reward_str_to_process = reward_str.split("(Hoặc")[0].strip()
                            else:
                                reward_str_to_process = "500 Coins + 1x Boosters Set + **1x Ruby Pack**"
                        
                        if "Pack" in reward_str_to_process:
                            cr_tag = " (Card Rush)" if is_cr else ""
                            logs.append(f"Tuần {(day - 1) // 7 + 1} - Mốc {req_wins} Win{cr_tag}: {reward_str_to_process}")
                            
                        add_packs_from_string(reward_str_to_process, packs, is_cr, day, f"Win Streak Tuần {(day - 1) // 7 + 1} Mốc {req_wins}", cr_detailed_logs)
                        
    return {"packs": packs, "logs": logs}

def simulate_key_collection(total_levels: int, levels_per_weekday: int, levels_per_weekend: int, cr_enabled: bool, cr_detailed_logs: list, config_rewards: dict) -> Dict[str, Any]:
    total_keys = total_levels * 5
    packs = {"Bronze": 0, "Bronze+": 0, "Emerald": 0, "Emerald+": 0, "Silver": 0, "Silver+": 0, "Amethyst": 0, "Ruby": 0, "Gold": 0, "Rainbow": 0}
    logs = [f"**Tổng số Keys kiếm được:** {total_keys} Keys (Mỗi level qua bàn nhận mặc định 5 keys)"]
    
    for stage, req_keys in {1:3, 2:8, 3:15, 4:25, 5:33, 6:40, 7:52, 8:67, 9:77, 10:89, 11:99, 12:111, 13:126, 14:138, 15:154, 16:164, 17:176, 18:192, 19:204, 20:214, 21:229, 22:241, 23:259, 24:279, 25:304}.items():
        if total_keys >= req_keys:
            reward_str = config_rewards["key_collection_rewards"].get(stage, "")
            level_earned = math.ceil(req_keys / 5)
            day = get_day_of_level(level_earned, levels_per_weekday, levels_per_weekend)
            is_cr = cr_enabled and is_card_rush_day(day)
            
            if "Pack" in reward_str:
                cr_tag = " (Card Rush)" if is_cr else ""
                logs.append(f"Stage {stage} (Cần {req_keys} keys){cr_tag}: {reward_str}")
            add_packs_from_string(reward_str, packs, is_cr, day, f"Key Collection Stage {stage}", cr_detailed_logs)
        else:
            logs.append(f"❌ Dừng lại ở Stage {stage} (Cần {req_keys} keys, bạn có {total_keys})")
            break
            
    return {"packs": packs, "logs": logs}

def get_tokens_at_level(level: int) -> int:
    cycles = level // 9
    rem = level % 9
    tokens = cycles * 13
    pattern = [1, 1, 2, 1, 1, 2, 1, 1, 3]
    for i in range(rem):
        tokens += pattern[i]
    return tokens

def simulate_master_pass(total_levels: int, levels_per_weekday: int, levels_per_weekend: int, is_premium: bool, cr_enabled: bool, cr_detailed_logs: list, config_rewards: dict) -> Dict[str, Any]:
    total_tokens = get_tokens_at_level(total_levels)
    stage_tokens = [0, 1, 3, 6, 10, 18, 23, 29, 38, 45, 55, 63, 75, 86, 95, 110, 126, 136, 150, 168, 188, 203, 214, 233, 250, 270, 288, 309, 333, 355, 380]
    
    packs = {"Bronze": 0, "Bronze+": 0, "Emerald": 0, "Emerald+": 0, "Silver": 0, "Silver+": 0, "Amethyst": 0, "Ruby": 0, "Gold": 0, "Rainbow": 0}
    logs = [f"**Tổng số Token kiếm được:** {total_tokens} Tokens (Thắng màn Normal = 1 Token, Hard = 2 Tokens, Super Hard = 3 Tokens)"]
    
    current_stage = -1
    for i, req in enumerate(stage_tokens):
        if total_tokens >= req:
            current_stage = i
        else:
            logs.append(f"❌ Dừng lại ở Stage {i} (Cần {req} tokens, bạn có {total_tokens})")
            break
            
    for s in range(0, current_stage + 1):
        req_tokens = stage_tokens[s]
        level_earned = 1
        for l in range(1, total_levels + 2):
            if get_tokens_at_level(l) >= req_tokens:
                level_earned = l
                break
        
        day = get_day_of_level(level_earned, levels_per_weekday, levels_per_weekend)
        is_cr = cr_enabled and is_card_rush_day(day)
        
        free_r = config_rewards["master_pass_free"].get(s, "")
        prem_r = config_rewards["master_pass_premium"].get(s, "")
        
        has_pack_free = "Pack" in free_r
        has_pack_prem = is_premium and "Pack" in prem_r
        
        if has_pack_free or has_pack_prem:
            cr_tag = " (Card Rush)" if is_cr else ""
            log_line = f"Stage {s} (Cần {req_tokens} tokens){cr_tag}: "
            if has_pack_free: log_line += f"[Free] {free_r} "
            if has_pack_prem: log_line += f"| [Premium] {prem_r}"
            logs.append(log_line)
        
        add_packs_from_string(free_r, packs, is_cr, day, f"Master Pass Stage {s} [Free]", cr_detailed_logs)
        if is_premium:
            add_packs_from_string(prem_r, packs, is_cr, day, f"Master Pass Stage {s} [Premium]", cr_detailed_logs)
            
    return {"packs": packs, "logs": logs}

def simulate_liveops(days: int, levels_per_weekday: int, levels_per_weekend: int, toggles: Dict[str, bool], iap: Dict[str, Any], config_rewards: Dict[str, Any]) -> Dict[str, Any]:
    levels_info = calculate_levels(days, levels_per_weekday, levels_per_weekend)
    total_levels = levels_info["total"]
    cr_enabled = toggles.get("card_rush", False)
    core_enabled = toggles.get("core_gameplay", True)
    
    result_packs = {p: 0 for p in PACK_ORDER}
    all_logs = {}
    cr_detailed_logs = []
    
    core = simulate_core_gameplay(days, levels_per_weekday, levels_per_weekend, cr_enabled, cr_detailed_logs, core_enabled)
    for p, v in core["packs"].items(): result_packs[p] += v
    all_logs["core"] = core["logs"]
    
    if toggles.get("win_streak"):
        ws = simulate_win_streak(days, levels_per_weekday, levels_per_weekend, cr_enabled, cr_detailed_logs, config_rewards)
        for p, v in ws["packs"].items(): result_packs[p] += v
        all_logs["win_streak"] = ws["logs"]
        
    if toggles.get("key_collection"):
        kc = simulate_key_collection(total_levels, levels_per_weekday, levels_per_weekend, cr_enabled, cr_detailed_logs, config_rewards)
        for p, v in kc["packs"].items(): result_packs[p] += v
        all_logs["key_collection"] = kc["logs"]
        
    if toggles.get("master_pass"):
        mp = simulate_master_pass(total_levels, levels_per_weekday, levels_per_weekend, toggles.get("master_pass_premium", False), cr_enabled, cr_detailed_logs, config_rewards)
        for p, v in mp["packs"].items(): result_packs[p] += v
        all_logs["master_pass"] = mp["logs"]        
    iap_summary = {p: 0 for p in PACK_ORDER}
    total_spent = 0.0
    total_iap_bought = 0
    
    if toggles.get("master_pass") and toggles.get("master_pass_premium"):
        total_spent += 9.99
        
    # Always give Part 1 Free
    iap_summary["Bronze"] += 1
    
    for item, val in iap.items():
        if isinstance(val, bool):
            if val:
                total_iap_bought += 1
                if item == "chain_part_2":
                    iap_summary["Emerald"] += 1
                    iap_summary["Bronze"] += 1
                    total_spent += 2.49
                elif item == "chain_part_3":
                    iap_summary["Silver"] += 1
                    iap_summary["Emerald"] += 1
                    total_spent += 4.99
                elif item == "chain_part_4":
                    iap_summary["Amethyst"] += 1
                    iap_summary["Emerald"] += 1
                    iap_summary["Silver"] += 1
                    total_spent += 10.99
                elif item == "chain_part_5":
                    iap_summary["Ruby"] += 1
                    iap_summary["Amethyst"] += 1
                    iap_summary["Silver"] += 1
                    total_spent += 18.99
                elif item == "chain_part_6":
                    iap_summary["Gold"] += 1
                    iap_summary["Silver"] += 1
                    iap_summary["Amethyst"] += 1
                    total_spent += 27.99
                elif item == "chain_part_7":
                    iap_summary["Rainbow"] += 1
                    iap_summary["Ruby"] += 1
                    iap_summary["Emerald"] += 1
                    iap_summary["Silver"] += 1
                    iap_summary["Amethyst"] += 1
                    total_spent += 49.99
        elif isinstance(val, (int, float)) and val > 0:
            qty = int(val)
            total_iap_bought += qty
            if item == "ooc_4": 
                iap_summary["Emerald"] += 1 * qty
                total_spent += 6.99 * qty
            elif item == "ooc_5": 
                iap_summary["Silver"] += 1 * qty
                total_spent += 14.99 * qty
            elif item == "ooc_6": 
                iap_summary["Amethyst"] += 1 * qty
                total_spent += 29.99 * qty
            elif item == "shop_9.99": 
                iap_summary["Silver"] += 1 * qty
                total_spent += 9.99 * qty
            elif item == "shop_19.99": 
                iap_summary["Amethyst"] += 1 * qty
                total_spent += 19.99 * qty
            elif item == "shop_29.99": 
                iap_summary["Ruby"] += 1 * qty
                total_spent += 29.99 * qty
            elif item == "shop_49.99": 
                iap_summary["Rainbow"] += 1 * qty
                total_spent += 49.99 * qty
            elif item == "shop_99.99": 
                iap_summary["Rainbow"] += 3 * qty
                total_spent += 99.99 * qty

    for p, v in iap_summary.items(): result_packs[p] += v
    
    all_logs["iap"] = ["**Tự động nhận Part 1 Chain Offer (Miễn phí)**"]
    if total_iap_bought > 0:
        all_logs["iap"].append(f"Đã mua/nhận tổng cộng {total_iap_bought} gói IAP/Chain Offer")
    
    assumptions = [
        "Tỉ lệ thắng (Win-rate) là 100%.",
        "Tiến trình Level: N-N-H, N-N-H, N-N-SH (sau 2 Normal - 1 Hard, sau 2 Hard - 1 Super Hard)).",
        "Mặc định người chơi đã mở khóa tất cả LiveOps.",
        "Người chơi bắt đầu chu kỳ 60 ngày kể từ Thứ Hai đầu tuần và chơi đều đặn mỗi ngày (không cách ngày).",
        "Toàn bộ các gói Pack mua từ IAP/Cửa hàng đều mặc định là gói Thường (Không áp dụng thưởng sự kiện Card Rush)."
    ]
    if cr_enabled:
        if not cr_detailed_logs: 
            cr_detailed_logs.append("Không nhận được gói Plus (+) nào trong thời gian diễn ra Card Rush.")
        cr_detailed_logs.insert(0, "**Lịch mở sự kiện:** Tuần 1-2 (Thứ 7), Tuần 3-5 (Thứ 4, 7), Tuần 6-9 (Thứ 2, 4, 7).")
        all_logs["card_rush"] = cr_detailed_logs

    # Calculate Bonus Cards
    bonus_cards = (result_packs["Bronze+"] * 1) + (result_packs["Emerald+"] * 2) + (result_packs["Silver+"] * 2)

    source_breakdown = {
        "Core Gameplay": sum(core["packs"].values()),
        "Win Streak": sum(ws["packs"].values()) if toggles.get("win_streak") else 0,
        "Key Collection": sum(kc["packs"].values()) if toggles.get("key_collection") else 0,
        "Master Pass": sum(mp["packs"].values()) if toggles.get("master_pass") else 0,
        "IAP / Mua sắm": sum(iap_summary.values())
    }

    return {
        "assumptions": assumptions,
        "levels_info": levels_info,
        "logs": all_logs,
        "iap_packs": iap_summary,
        "total_packs": result_packs,
        "total_spent": total_spent,
        "bonus_cards": bonus_cards,
        "source_breakdown": source_breakdown
    }
