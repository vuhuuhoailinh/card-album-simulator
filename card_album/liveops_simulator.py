import math
import re
from typing import Dict, Any, List
from .config import PACK_ORDER

def is_card_rush_day(day: int) -> bool:
    if day <= 0: return False
    week = (day - 1) // 7 + 1
    weekday = (day - 1) % 7 + 1
    if week <= 6: 
        return weekday == 6
    else: 
        return weekday in (3, 6)

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

def calculate_levels(daily_levels: List[int]) -> Dict[str, int]:
    total_levels = sum(daily_levels)
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

def simulate_core_gameplay(daily_levels: List[int], cr_enabled: bool, cr_detailed_logs: list, core_enabled: bool = True) -> Dict[str, Any]:
    packs = {"Bronze": 0, "Bronze+": 0, "Emerald": 0, "Emerald+": 0}
    logs = []
    
    bronze_count = 0
    emerald_count = 0
    bronze_plus = 0
    emerald_plus = 0
    
    level = 0
    for idx, lpd in enumerate(daily_levels):
        day = idx + 1
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

def simulate_win_streak(daily_levels: List[int], cr_enabled: bool, cr_detailed_logs: list, config_rewards: dict) -> Dict[str, Any]:
    packs = {"Bronze": 0, "Bronze+": 0, "Emerald": 0, "Emerald+": 0, "Silver": 0, "Silver+": 0, "Amethyst": 0, "Ruby": 0, "Gold": 0, "Rainbow": 0}
    logs = []
    
    total_level = 0
    event_count = 0
    event_wins = 0
    claimed_milestones = set()
    has_avatar = False
    
    for idx, lpd in enumerate(daily_levels):
        day = idx + 1
        weekday = (day - 1) % 7 + 1
        is_cr = cr_enabled and is_card_rush_day(day)
        
        # Reset event every Friday
        if weekday == 5:
            event_count += 1
            event_wins = 0
            claimed_milestones = set()
            
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

def simulate_key_collection(daily_levels: List[int], cr_enabled: bool, cr_detailed_logs: list, config_rewards: dict) -> Dict[str, Any]:
    packs = {"Bronze": 0, "Bronze+": 0, "Emerald": 0, "Emerald+": 0, "Silver": 0, "Silver+": 0, "Amethyst": 0, "Ruby": 0, "Gold": 0, "Rainbow": 0}
    logs = [f"**Lưu ý:** Sự kiện Key Collection diễn ra và reset hàng tuần vào mỗi Thứ 2."]
    
    stage_reqs = {1:3, 2:8, 3:15, 4:25, 5:33, 6:40, 7:52, 8:67, 9:77, 10:89, 11:99, 12:111, 13:126, 14:138, 15:154, 16:164, 17:176, 18:192, 19:204, 20:214, 21:229, 22:241, 23:259, 24:279, 25:304}
    total_keys_ever = 0
    event_keys = 0
    claimed_milestones = set()
    
    for idx, lpd in enumerate(daily_levels):
        day = idx + 1
        weekday = (day - 1) % 7 + 1
        is_cr = cr_enabled and is_card_rush_day(day)
        
        # Reset event every Monday
        if weekday == 1:
            event_keys = 0
            claimed_milestones = set()
            
        for _ in range(lpd):
            event_keys += 5
            total_keys_ever += 5
            
            for stage, req_keys in stage_reqs.items():
                if event_keys >= req_keys and stage not in claimed_milestones:
                    claimed_milestones.add(stage)
                    reward_str = config_rewards["key_collection_rewards"].get(stage, "")
                    
                    if "Pack" in reward_str:
                        cr_tag = " (Card Rush)" if is_cr else ""
                        logs.append(f"Tuần {(day - 1) // 7 + 1} - Stage {stage} ({req_keys} keys){cr_tag}: {reward_str}")
                    add_packs_from_string(reward_str, packs, is_cr, day, f"Key Collection Tuần {(day - 1) // 7 + 1} Stage {stage}", cr_detailed_logs)

    logs.insert(1, f"**Tổng số Keys kiếm được (cả mùa):** {total_keys_ever} Keys (Mỗi level qua bàn nhận mặc định 5 keys)")
    return {"packs": packs, "logs": logs}

def get_tokens_for_level(level: int) -> int:
    if level % 9 == 0: return 3
    if level % 3 == 0: return 2
    return 1

def simulate_master_pass(daily_levels: List[int], is_premium: bool, cr_enabled: bool, cr_detailed_logs: list, config_rewards: dict) -> Dict[str, Any]:
    stage_tokens = [0, 1, 3, 6, 10, 18, 23, 29, 38, 45, 55, 63, 75, 86, 95, 110, 126, 136, 150, 168, 188, 203, 214, 233, 250, 270, 288, 309, 333, 355, 380]
    
    packs = {"Bronze": 0, "Bronze+": 0, "Emerald": 0, "Emerald+": 0, "Silver": 0, "Silver+": 0, "Amethyst": 0, "Ruby": 0, "Gold": 0, "Rainbow": 0}
    logs = [f"**Lưu ý:** Sự kiện Master Pass diễn ra và reset hàng tháng (mỗi 30 ngày)."]
    
    total_tokens_ever = 0
    event_tokens = 0
    claimed_milestones = set()
    global_level = 0
    
    for idx, lpd in enumerate(daily_levels):
        day = idx + 1
        weekday = (day - 1) % 7 + 1
        is_cr = cr_enabled and is_card_rush_day(day)
        
        # Reset event every 30 days (Monthly Battle Pass)
        if day % 30 == 1:
            event_tokens = 0
            claimed_milestones = set()
            
        for _ in range(lpd):
            global_level += 1
            tokens_earned = get_tokens_for_level(global_level)
            event_tokens += tokens_earned
            total_tokens_ever += tokens_earned
            
            for stage, req_tokens in enumerate(stage_tokens):
                if event_tokens >= req_tokens and stage not in claimed_milestones:
                    claimed_milestones.add(stage)
                    
                    free_r = config_rewards["master_pass_free"].get(stage, "")
                    prem_r = config_rewards["master_pass_premium"].get(stage, "")
                    
                    has_pack_free = "Pack" in free_r
                    has_pack_prem = is_premium and "Pack" in prem_r
                    
                    if has_pack_free or has_pack_prem:
                        cr_tag = " (Card Rush)" if is_cr else ""
                        log_line = f"Tháng {(day - 1) // 30 + 1} - Stage {stage} ({req_tokens} tokens){cr_tag}: "
                        if has_pack_free: log_line += f"[Free] {free_r} "
                        if has_pack_prem: log_line += f"| [Premium] {prem_r}"
                        logs.append(log_line)
                    
                    add_packs_from_string(free_r, packs, is_cr, day, f"Master Pass Tháng {(day - 1) // 30 + 1} Stage {stage} [Free]", cr_detailed_logs)
                    if is_premium:
                        add_packs_from_string(prem_r, packs, is_cr, day, f"Master Pass Tháng {(day - 1) // 30 + 1} Stage {stage} [Premium]", cr_detailed_logs)

    logs.insert(1, f"**Tổng số Token kiếm được (cả mùa):** {total_tokens_ever} Tokens (Thắng màn Normal = 1 Token, Hard = 2 Tokens, Super Hard = 3 Tokens)")
    return {"packs": packs, "logs": logs}

def simulate_liveops(days: int, levels_per_weekday: tuple, levels_per_weekend: tuple, toggles: Dict[str, bool], iap: Dict[str, Any], config_rewards: Dict[str, Any]) -> Dict[str, Any]:
    import random
    daily_levels = []
    for day in range(1, days + 1):
        weekday = (day - 1) % 7 + 1
        if weekday in (5, 6, 7):
            daily_levels.append(random.randint(levels_per_weekend[0], levels_per_weekend[1]))
        else:
            daily_levels.append(random.randint(levels_per_weekday[0], levels_per_weekday[1]))
            
    levels_info = calculate_levels(daily_levels)
    total_levels = levels_info["total"]
    cr_enabled = toggles.get("card_rush", False)
    core_enabled = toggles.get("core_gameplay", True)
    
    result_packs = {p: 0 for p in PACK_ORDER}
    all_logs = {}
    cr_detailed_logs = []
    
    core = simulate_core_gameplay(daily_levels, cr_enabled, cr_detailed_logs, core_enabled)
    for p, v in core["packs"].items(): result_packs[p] += v
    all_logs["core"] = core["logs"]
    
    if toggles.get("win_streak"):
        ws = simulate_win_streak(daily_levels, cr_enabled, cr_detailed_logs, config_rewards)
        for p, v in ws["packs"].items(): result_packs[p] += v
        all_logs["win_streak"] = ws["logs"]
        
    if toggles.get("key_collection"):
        kc = simulate_key_collection(daily_levels, cr_enabled, cr_detailed_logs, config_rewards)
        for p, v in kc["packs"].items(): result_packs[p] += v
        all_logs["key_collection"] = kc["logs"]
        
    if toggles.get("master_pass"):
        mp = simulate_master_pass(daily_levels, toggles.get("master_pass_premium", False), cr_enabled, cr_detailed_logs, config_rewards)
        for p, v in mp["packs"].items(): result_packs[p] += v
        all_logs["master_pass"] = mp["logs"]
        
    chest_drop_res = {"chests": {1: 0, 2: 0, 3: 0}, "logs": []}
    if toggles.get("chest_drop", True):
        from .liveops_simulator import simulate_chest_drop
        chest_drop_res = simulate_chest_drop(daily_levels)
        all_logs["chest_drop"] = chest_drop_res["logs"]
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
        "Mặc định người chơi đã mở khóa tất cả LiveOps. Key Collection reset mỗi đầu tuần (Thứ 2). Master Pass reset mỗi tháng (30 ngày).",
        "Người chơi bắt đầu chu kỳ 60 ngày kể từ Thứ Hai đầu tuần và chơi đều đặn mỗi ngày (không cách ngày).",
        "Toàn bộ các gói Pack mua từ IAP/Cửa hàng đều mặc định là gói Thường (Không áp dụng thưởng sự kiện Card Rush)."
    ]
    if cr_enabled:
        if not cr_detailed_logs: 
            cr_detailed_logs.append("Không nhận được gói Plus (+) nào trong thời gian diễn ra Card Rush.")
        cr_detailed_logs.insert(0, "**Lịch mở sự kiện:** Tuần 1-6 (Thứ 7), Tuần 7 trở đi (Thứ 4, Thứ 7).")
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
        "chest_drop_chests": chest_drop_res["chests"] if 'chest_drop_res' in locals() else {1:0, 2:0, 3:0},
        "total_spent": total_spent,
        "bonus_cards": bonus_cards,
        "source_breakdown": source_breakdown
    }


def simulate_chest_drop(daily_levels: List[int]) -> dict:
    chests = {1: 0, 2: 0, 3: 0}
    logs = ["**Lưu ý:** Chest Drop tính năng chạy và reset vào 0h mỗi ngày."]
    for idx, lpd in enumerate(daily_levels):
        day = idx + 1
        daily_chests = []
        if lpd >= 3: 
            chests[1] += 1
            daily_chests.append("1-Sao")
        if lpd >= 7: 
            chests[2] += 1
            daily_chests.append("2-Sao")
        if lpd >= 12: 
            chests[3] += 1
            daily_chests.append("3-Sao")
            
        if daily_chests:
            logs.append(f"Ngày {day} ({get_day_string(day)}) - Cày {lpd} màn: Nhận Rương {', '.join(daily_chests)}")
            
    logs.insert(1, f"**Sau {len(daily_levels)} ngày, tích lũy được:** {chests[1]} Rương 1-Sao, {chests[2]} Rương 2-Sao, {chests[3]} Rương 3-Sao.")
    return {"chests": chests, "logs": logs}
