import pandas as pd
import streamlit as st
import altair as alt

from ..config import (
    MAX_CARDS,
    PACK_ICONS,
    PACK_ORDER,
    PACKS,
    RARITIES,
    TOTAL_CARDS,
)
from ..gacha import build_rate_rows, get_pity_bonus, open_bulk_packs, open_pack, open_chest, rarity_label
from ..state import ensure_album_state, reset_progress, total_cards_collected
from ..liveops_simulator import simulate_liveops

from .utils import format_card_name_ui

@st.dialog("BẠN VỪA NHẬN ĐƯỢC!", width="large")
def show_chest_drop_bulk_result_dialog(res: dict):
    st.markdown("""
        <style>
            div[data-testid="stDialog"] div[role="dialog"] {
                width: 85vw !important;
                max-width: 1200px !important;
            }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown(f"**🌟 MỞ THÀNH CÔNG: {res.get('total_chests', 0)} RƯƠNG**")
    
    us = res.get("upgrade_summary", {})
    summary_html = ""
    for start_tier, tier_stats in us.items():
        total_started = sum(tier_stats.values())
        if total_started > 0:
            summary_html += f"<div style='margin-bottom: 5px;'><b>📦 Rương {start_tier}-Sao (Tổng: {total_started}):</b> "
            parts = []
            for t in sorted(tier_stats.keys()):
                count = tier_stats[t]
                if count > 0:
                    if t == start_tier:
                        parts.append(f"{count} rương giữ nguyên")
                    else:
                        parts.append(f"<b><span style='color: #32CD32;'>{count} rương lên {t}-Sao</span></b>")
            summary_html += ", ".join(parts) + "</div>"
            
    if summary_html:
        st.info("🏆 **Thống Kê Thăng Cấp (Upgrade Summary):**")
        st.markdown(summary_html, unsafe_allow_html=True)
        
    rarity_colors = {
        1: "#B0C4DE", 2: "#32CD32", 3: "#1E90FF",
        4: "#9370DB", 5: "#FFA500", 6: "#FFD700"
    }
    
    def render_card_html(card, is_new):
        from ..config import CARD_SETS
        from ..gacha import STAR_VALUES
        if not card: return ""
        set_id, r, idx = card
        cname = f"{CARD_SETS[set_id]['name']} #{idx+1}"
        color = rarity_colors.get(r, "gray")
        icon = "⭐" * r if r < 6 else "🌟"
        
        box_shadow = f"box-shadow: 0 0 15px {color};" if is_new else ""
        opacity = "1.0" if is_new else "0.6"
        
        if color.startswith("#") and len(color) == 7:
            r_val, g_val, b_val = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
            bg = f"rgba({r_val}, {g_val}, {b_val}, 0.15)"
        else:
            bg = "rgba(128, 128, 128, 0.15)"
            
        badge = f"<div style='position:absolute; top:-10px; right:-10px; background:red; color:white; font-size:0.7em; padding:2px 6px; border-radius:10px; font-weight:bold; box-shadow: 0 0 5px red;'>NEW</div>" if is_new else f"<div style='position:absolute; top:-10px; right:-10px; background:gray; color:white; font-size:0.7em; padding:2px 6px; border-radius:10px; font-weight:bold;'>+{STAR_VALUES[r]}⭐</div>"
        
        return f"<div style='position:relative; width: 100px; height: 130px; border: 2px solid {color}; border-radius: 8px; padding: 5px; text-align: center; background: {bg}; {box_shadow} opacity: {opacity}; display: flex; flex-direction: column; justify-content: space-between;'>{badge}<div style='font-size: 0.8em; margin-top: 10px;'>{icon}</div><div style='font-size: 0.75em; font-weight: bold; line-height: 1.2; word-wrap: break-word; margin-bottom: 5px;'>{cname}</div></div>"
        
    new_cards = res.get("new_cards_list", [])
    dup_cards = res.get("dup_cards_list", [])
    
    if new_cards:
        st.markdown("<h3>✨ THẺ MỚI NHẬN</h3>", unsafe_allow_html=True)
        html_parts = [render_card_html(c, True) for c in new_cards]
        st.markdown("<div style='display: flex; flex-wrap: wrap; justify-content: center; gap: 15px; margin-bottom: 20px;'>" + "".join(html_parts) + "</div>", unsafe_allow_html=True)
        
    if dup_cards:
        st.markdown("<h3>♻️ THẺ TRÙNG (Đổi thành Sao)</h3>", unsafe_allow_html=True)
        html_parts = [render_card_html(c, False) for c in dup_cards]
        st.markdown("<div style='display: flex; flex-wrap: wrap; justify-content: center; gap: 15px;'>" + "".join(html_parts) + "</div>", unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("THU THẬP", use_container_width=True, type="primary"):
        st.rerun()


def render_chest_drop_tab() -> None:
    import streamlit as st
    import pandas as pd
    import time
    
    with st.container(border=True):
        st.subheader("📊 Tổng Quan Chest Drop")
        col_stats1, col_stats2, col_stats3, col_stats4, col_stats5 = st.columns(5)
        
        rarity_colors = {
            1: "gray", 2: "#32CD32", 3: "#1E90FF",
            4: "#9370DB", 5: "#FFA500", 6: "#FF1493"
        }
        
        def st_color_tier(r):
            colors = {1: "gray", 2: "green", 3: "blue", 4: "violet", 5: "orange", 6: "red"}
            c = colors.get(int(r), "gray")
            label = f"{r}-Sao" if int(r) < 6 else "VÀNG"
            return f":{c}[{label}]"

        
        new_total = st.session_state.get('cd_new_cards_drawn', 0)
        new_dict = st.session_state.get('cd_new_cards_by_rarity', {})
        new_parts = []
        for r in range(1, 7):
            if new_dict.get(r, 0) > 0:
                icon = "⭐" if r < 6 else "🌟"
                new_parts.append(f"<span style='color:{rarity_colors[r]}'>{r}{icon}: {new_dict[r]}</span>")
        new_detail = f"<div style='font-size:0.85em; margin-top:-10px; color:#aaa'>({', '.join(new_parts)})</div>" if new_parts else ""

        dup_total = st.session_state.get('cd_dup_cards_drawn', 0)
        dup_dict = st.session_state.get('cd_dup_cards_by_rarity', {})
        dup_parts = []
        for r in range(1, 7):
            if dup_dict.get(r, 0) > 0:
                icon = "⭐" if r < 6 else "🌟"
                dup_parts.append(f"<span style='color:{rarity_colors[r]}'>{r}{icon}: {dup_dict[r]}</span>")
        dup_detail = f"<div style='font-size:0.85em; margin-top:-10px; color:#aaa'>({', '.join(dup_parts)})</div>" if dup_parts else ""
        
        with col_stats1:
            total_cd_cards = st.session_state.get('cd_total_cards_drawn', 0)
            st.metric("🃏 Tổng Thẻ Rút Ra", f"{total_cd_cards}")
        with col_stats2:
            st.metric("🎴 Thẻ Mới Nhận", f"{new_total}")
            if new_detail: st.markdown(new_detail, unsafe_allow_html=True)
        with col_stats3:
            cd_stars = st.session_state.get('cd_stars_gained', 0)
            st.metric("♻️ Thẻ Trùng (Sao Nhận)", f"{dup_total} (+{cd_stars}⭐)")
            if dup_detail: st.markdown(dup_detail, unsafe_allow_html=True)
        with col_stats4:
            total_chests = sum(st.session_state.get('chest_drop_counts', {1:0,2:0,3:0,4:0,5:0}).values())
            st.metric("📦 Tổng Rương Đã Mở", f"{total_chests}")
        with col_stats5:
            rate = (dup_total / total_cd_cards * 100) if total_cd_cards > 0 else 0
            st.metric("♻️ Tỉ lệ Thẻ Trùng", f"{dup_total}/{total_cd_cards} ({rate:.2f}%)")
        
        st.markdown("<hr style='margin: 10px 0px; opacity: 0.3'>", unsafe_allow_html=True)
        st.caption("Chi tiết số lượng Chest đã mở từ giỏ:")
        pack_cols = st.columns(5)
        cd_counts = st.session_state.get("chest_drop_counts", {1:0,2:0,3:0,4:0,5:0})
        for i in range(1, 6):
            with pack_cols[i - 1]:
                st.markdown(f"**Rương {st_color_tier(i)}**: {cd_counts.get(i, 0)}")
    
    upgrade_cfg = st.session_state.get('config_chest_drop_tiers', {})
    
    def get_reward_str(tier_str):
        if tier_str not in upgrade_cfg: return "Unknown"
        w = upgrade_cfg[tier_str]["weights"]
        total = sum(w.values())
        if total == 0: return "Không có phần thưởng"
        parts = []
        for r_str, weight in w.items():
            if weight > 0:
                parts.append(f"{weight/total*100:.0f}% Thẻ {r_str}-Sao" if r_str != "6" else f"{weight/total*100:.0f}% VÀNG")
        return ", ".join(parts)
        
    def get_upgrade_str(tier_str, start_tier_str="1"):
        matrix = st.session_state.get('config_chest_upgrade_matrix', {})
        if start_tier_str not in matrix or tier_str not in matrix[start_tier_str]: return "0%"
        val = matrix[start_tier_str][tier_str]
        if int(tier_str) < int(start_tier_str): return "Không khả dụng"
        if val == 0: return "Không thăng cấp"
        return f"{val*100:.0f}%"

    from ..gacha import calculate_chest_drop_new_chance, add_log
    def get_new_chance_str(tier_str):
        if tier_str not in upgrade_cfg: return "0%"
        t_cfg = upgrade_cfg[tier_str]
        w = t_cfg["weights"]
        y_val = float(t_cfg["y_value"])
        total = sum(w.values())
        if total == 0: return "0%"
        parts = []
        for r_str, weight in w.items():
            if weight > 0:
                rarity = int(r_str)
                new_chance = calculate_chest_drop_new_chance(st.session_state, rarity, y_val)
                label = f"{r_str}-Sao" if r_str != "6" else "VÀNG"
                if len([v for v in w.values() if v > 0]) > 1:
                    parts.append(f"{new_chance*100:.1f}% ({label})")
                else:
                    parts.append(f"{new_chance*100:.1f}%")
        return ", ".join(parts)

    current_sandbox_tier = st.session_state.get("sandbox_chest_tier", 1)
    
    df_upgrade = pd.DataFrame([
        {"Rương": "1-Sao", "Phần thưởng (Mỗi hit)": get_reward_str("1"), "Thẻ MỚI": get_new_chance_str("1"), "Tỉ lệ thăng cấp": get_upgrade_str("1", str(current_sandbox_tier))},
        {"Rương": "2-Sao", "Phần thưởng (Mỗi hit)": get_reward_str("2"), "Thẻ MỚI": get_new_chance_str("2"), "Tỉ lệ thăng cấp": get_upgrade_str("2", str(current_sandbox_tier))},
        {"Rương": "3-Sao", "Phần thưởng (Mỗi hit)": get_reward_str("3"), "Thẻ MỚI": get_new_chance_str("3"), "Tỉ lệ thăng cấp": get_upgrade_str("3", str(current_sandbox_tier))},
        {"Rương": "4-Sao", "Phần thưởng (Mỗi hit)": get_reward_str("4"), "Thẻ MỚI": get_new_chance_str("4"), "Tỉ lệ thăng cấp": get_upgrade_str("4", str(current_sandbox_tier))},
        {"Rương": "5-Sao", "Phần thưởng (Mỗi hit)": get_reward_str("5"), "Thẻ MỚI": get_new_chance_str("5"), "Tỉ lệ thăng cấp": "Không thăng cấp"},
    ])

    cart = st.session_state.get("cart_chests", {1:0, 2:0, 3:0})
    # --- SANDBOX SIMULATOR ---
    st.subheader("🎮 Sandbox Chest Drop")
    st.markdown("Giả lập đập rương hoàn toàn miễn phí, không tốn rương trong giỏ hàng. Bạn có thể tự do test nhân phẩm!")
    
    col_ctrl, col_reward = st.columns([1, 2])
    
    active_session = st.session_state.get("cd_active_session")
    
    with col_ctrl:
        with st.container(border=True):
            tier = st.selectbox(
                "Chọn rương:",
                [1, 2, 3],
                format_func=lambda x: f"Rương {x}-Sao",
                key="sandbox_chest_tier"
            )
            
            # Auto init or reset if tier changed
            if active_session is None or active_session.get("start_tier") != tier:
                active_session = {
                    "start_tier": tier,
                    "current_tier": tier,
                    "hits_done": 0,
                    "rewards": [],
                    "max_tier": tier,
                    "upgraded_last_hit": False,
                    "drawn_in_batch": set()
                }
                st.session_state["cd_active_session"] = active_session
                
            hits_done = active_session["hits_done"]
            current_tier = active_session["current_tier"]
            upgraded = active_session.get("upgraded_last_hit", False)
            
            st.markdown(f"**Đang mở: Rương {st_color_tier(active_session['start_tier'])}**")
            
            st.progress(hits_done / 5.0)
            st.caption(f"Tiến độ: **Hit {hits_done}/5**")
            
            if hits_done > 0:
                st.write("")
            
            if hits_done < 5:
                if st.button(f"🔨 Đập! (Hit {hits_done+1})", key="sandbox_hit", type="primary", use_container_width=True):
                    from ..gacha import process_chest_drop_hit
                    res = process_chest_drop_hit(st.session_state, active_session["start_tier"], current_tier, active_session["drawn_in_batch"])
                    
                    active_session["rewards"].append({
                        "status": res["status"],
                        "card": res["card"],
                        "upgraded": res["upgraded"],
                        "next_tier": res["next_tier"]
                    })
                    active_session["upgraded_last_hit"] = res["upgraded"]
                    active_session["current_tier"] = res["next_tier"]
                    if res["next_tier"] > active_session["max_tier"]:
                        active_session["max_tier"] = res["next_tier"]
                    active_session["hits_done"] += 1
                    
                    if active_session["hits_done"] == 5:
                        def add_cd_log(session_state, msg):
                            if "cd_log" not in session_state: session_state["cd_log"] = []
                            session_state["cd_log"].insert(0, msg)
                            if len(session_state["cd_log"]) > 300: session_state["cd_log"] = session_state["cd_log"][:300]
                        
                        hit_logs = []
                        from ..gacha import format_card_name
                        for item in active_session["rewards"]:
                            if not item.get("card"): continue
                            card_r = item["card"][1]
                            cname = format_card_name(item["card"])
                            status_str = f"({item['status']})"
                            card_str = f"{card_r}-Sao [{cname}] {status_str}"
                            if item["upgraded"]:
                                hit_logs.append(f"{card_str} ✨Lên {item['next_tier']}-Sao")
                            else:
                                hit_logs.append(card_str)
                            
                        has_new = any(item["status"] == "NEW" for item in active_session["rewards"])
                        prefix = "✅" if has_new else "❌"
                        log_msg = f"{prefix} 📦 Mở Rương {active_session['start_tier']}-Sao | Mở ra: " + ", ".join(hit_logs)
                        add_cd_log(st.session_state, log_msg)
                    
                    st.rerun()
            else:
                if st.button("THU THẬP", key="sandbox_reset", type="primary", use_container_width=True):
                    st.session_state["cd_active_session"] = {
                        "start_tier": tier,
                        "current_tier": tier,
                        "hits_done": 0,
                        "rewards": [],
                        "max_tier": tier,
                        "upgraded_last_hit": False,
                        "drawn_in_batch": set()
                    }
                    st.rerun()
                        
    with col_reward:
        with st.container(border=True):
            st.markdown("**Phần Thưởng Nhận Được:**")
            if active_session is None or len(active_session["rewards"]) == 0:
                st.caption("Chưa đập hit nào... Hãy bắt đầu đập để xem kết quả!")
            else:
                rarity_colors = {
                    1: "#B0C4DE", 2: "#32CD32", 3: "#1E90FF",
                    4: "#9370DB", 5: "#FFA500", 6: "#FFD700"
                }
                from ..gacha import STAR_VALUES
                from ..config import CARD_SETS
                
                html_parts = []
                for item in active_session["rewards"]:
                    is_new = (item["status"] == "NEW")
                    card = item["card"]
                    if not card: continue
                    set_id, r, idx = card
                    cname = f"{CARD_SETS[set_id]['name']} #{idx+1}"
                    color = rarity_colors.get(r, "gray")
                    icon = "⭐" * r if r < 6 else "🌟"
                    
                    box_shadow = f"box-shadow: 0 0 15px {color};" if is_new else ""
                    opacity = "1.0" if is_new else "0.6"
                    
                    if color.startswith("#") and len(color) == 7:
                        r_val, g_val, b_val = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
                        bg = f"rgba({r_val}, {g_val}, {b_val}, 0.15)"
                    else:
                        bg = "rgba(128, 128, 128, 0.15)"
                        
                    badge = f"<div style='position:absolute; top:-10px; right:-10px; background:red; color:white; font-size:0.7em; padding:2px 6px; border-radius:10px; font-weight:bold; box-shadow: 0 0 5px red;'>NEW</div>" if is_new else f"<div style='position:absolute; top:-10px; right:-10px; background:gray; color:white; font-size:0.7em; padding:2px 6px; border-radius:10px; font-weight:bold;'>+{STAR_VALUES[r]}⭐</div>"
                    html_parts.append(f"<div style='position:relative; width: 100px; height: 130px; border: 2px solid {color}; border-radius: 8px; padding: 5px; text-align: center; background: {bg}; {box_shadow} opacity: {opacity}; display: flex; flex-direction: column; justify-content: space-between; margin-right: 10px; margin-bottom: 15px;'>{badge}<div style='font-size: 0.8em; margin-top: 10px;'>{icon}</div><div style='font-size: 0.75em; font-weight: bold; line-height: 1.2; word-wrap: break-word; margin-bottom: 5px;'>{cname}</div></div>")
                    
                    if item.get("upgraded"):
                        n_tier = item.get("next_tier")
                        html_parts.append(f"<div style='position:relative; width: 100px; height: 130px; border: 2px dashed #32CD32; border-radius: 8px; padding: 5px; text-align: center; background: rgba(50,205,50,0.1); display: flex; flex-direction: column; justify-content: center; margin-right: 10px; margin-bottom: 15px;'><div style='font-size: 1.5em; margin-bottom:5px;'>✨</div><div style='font-size: 0.85em; font-weight: bold; color: #32CD32;'>LÊN<br>{n_tier}-SAO!</div></div>")
                    
                st.markdown("<div style='display: flex; flex-wrap: wrap;'>" + "".join(html_parts) + "</div>", unsafe_allow_html=True)


    st.divider()
    col_left, col_right = st.columns([1, 2])
    
    with col_left:
        st.subheader('🛒 Giỏ Hàng')
        st.caption("Nhập số lượng rương bạn muốn mở.")
        
        qty_1 = st.number_input("Rương 1-Sao", min_value=0, max_value=9999, step=1, key="bulk_chest_1")
        qty_2 = st.number_input("Rương 2-Sao", min_value=0, max_value=9999, step=1, key="bulk_chest_2")
        qty_3 = st.number_input("Rương 3-Sao", min_value=0, max_value=9999, step=1, key="bulk_chest_3")
            
        total_bulk = qty_1 + qty_2 + qty_3
        
        st.write("")
        def reset_cart_cd():
            st.session_state["bulk_chest_1"] = 0
            st.session_state["bulk_chest_2"] = 0
            st.session_state["bulk_chest_3"] = 0
            
        col_exec, col_reset = st.columns([3, 1])
        
        if col_exec.button('💥 MỞ TOÀN BỘ GIỎ HÀNG', type='primary', use_container_width=True):
            if total_bulk == 0:
                st.error("Giỏ hàng đang trống!")
            else:
                from ..gacha import process_chest_drop_hit
                all_new = []
                all_dup = []
                
                def add_cd_log(session_state, msg):
                    if "cd_log" not in session_state: session_state["cd_log"] = []
                    session_state["cd_log"].insert(0, msg)
                    if len(session_state["cd_log"]) > 300: session_state["cd_log"] = session_state["cd_log"][:300]
                    
                add_cd_log(st.session_state, f"========== BẮT ĐẦU MỞ HÀNG LOẠT ({total_bulk} RƯƠNG) ==========")
                
                upgrade_summary = {
                    1: {1:0, 2:0, 3:0, 4:0, 5:0},
                    2: {2:0, 3:0, 4:0, 5:0},
                    3: {3:0, 4:0, 5:0}
                }
            
                cart_to_open = {1: qty_1, 2: qty_2, 3: qty_3}
                
                from ..gacha import format_card_name
                for start_tier, count in cart_to_open.items():
                    for i in range(count):
                        current_t = start_tier
                        hit_logs = []
                        chest_has_new = False
                        drawn_in_batch = set()
                        for _ in range(5):
                            res = process_chest_drop_hit(st.session_state, start_tier, current_t, drawn_in_batch)
                            if res["status"] == "NEW": 
                                all_new.append(res["card"])
                                chest_has_new = True
                            else: 
                                all_dup.append(res["card"])
                            
                            card_r = res["card"][1] if res["card"] else 0
                            cname = format_card_name(res["card"]) if res["card"] else ""
                            status_str = f"({res['status']})"
                            card_str = f"{st_color_tier(card_r)} [{cname}] {status_str}"
                            if res["upgraded"]:
                                hit_logs.append(f"{card_str} ✨Lên {st_color_tier(res['next_tier'])}")
                            else:
                                hit_logs.append(card_str)
                                
                            current_t = res["next_tier"]
                        upgrade_summary[start_tier][current_t] += 1
                        
                        prefix = "✅" if chest_has_new else "❌"
                        log_msg = f"{prefix} 📦 Mở Rương {st_color_tier(start_tier)} #{i+1} | Mở ra: " + ", ".join(hit_logs)
                        add_cd_log(st.session_state, log_msg)
                
                summary_html = ""
                for start_tier, tier_stats in upgrade_summary.items():
                    total_started = sum(tier_stats.values())
                    if total_started > 0:
                        parts = []
                        for t in sorted(tier_stats.keys()):
                            count = tier_stats[t]
                            if count > 0:
                                if t == start_tier:
                                    parts.append(f"{count} rương giữ nguyên")
                                else:
                                    parts.append(f"{count} rương thăng cấp {st_color_tier(t)}")
                        summary_html += f"[{st_color_tier(start_tier)}: " + ", ".join(parts) + "] "
                
                add_cd_log(st.session_state, f"🌟 HOÀN THÀNH MỞ HÀNG LOẠT: Thêm {len(all_new)} thẻ mới, {len(all_dup)} thẻ trùng. {summary_html}")
                        
                st.session_state.cd_show_bulk_result = True
                st.session_state.cd_new_cards = all_new
                st.session_state.cd_dup_cards = all_dup
                st.session_state.cd_upgrade_summary = upgrade_summary
                st.session_state.cd_total_bulk_opened = total_bulk
                st.rerun()
            
        col_reset.button("🗑️ Xoá giỏ", use_container_width=True, on_click=reset_cart_cd)
                
        if st.session_state.get('cd_show_bulk_result', False):
            st.session_state.cd_show_bulk_result = False
            res_dict = {
                "new_cards_list": st.session_state.get("cd_new_cards", []),
                "dup_cards_list": st.session_state.get("cd_dup_cards", []),
                "upgrade_summary": st.session_state.get("cd_upgrade_summary", {}),
                "total_chests": st.session_state.get("cd_total_bulk_opened", 0)
            }
            show_chest_drop_bulk_result_dialog(res_dict)
            
    with col_right:
        st_colors = {1: "gray", 2: "green", 3: "blue", 4: "violet", 5: "orange", 6: "red"}
        color_name = st_colors.get(int(current_sandbox_tier), "gray")
        st.subheader(f"🔎 Bảng Tỉ Lệ Động: :{color_name}[Rương {current_sandbox_tier}-Sao]")
        st.markdown("**Tỉ lệ thăng cấp và phần thưởng rương sau mỗi hit:**")
        st.dataframe(df_upgrade, hide_index=True)

    st.divider()
    render_cd_log_panel()


def render_cd_log_panel() -> None:
    st.subheader("📝 Kết Quả Mở Chest")
    cd_log = st.session_state.get("cd_log", [])
    if not cd_log:
        st.caption("Chưa có dữ liệu lịch sử mở chest.")
        return
        
    latest = cd_log[0]
    if "MỚI" in latest or "✨" in latest or "🌟" in latest:
        st.success(f"**[MỚI NHẤT]** {latest}")
    else:
        st.warning(f"**[MỚI NHẤT]** {latest}")

    with st.expander("📜 Xem toàn bộ lịch sử", expanded=True):
        log_container = st.container(height=400)
        for entry in cd_log[1:]:
            if "MỚI" in entry or "✨" in entry or "🌟" in entry:
                log_container.success(entry)
            elif "====" in entry:
                log_container.markdown(f"**{entry}**")
            else:
                log_container.warning(entry)


