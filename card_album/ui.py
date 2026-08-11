import pandas as pd
import streamlit as st
import altair as alt

from .config import (
    MAX_CARDS,
    PACK_ICONS,
    PACK_ORDER,
    PACKS,
    RARITIES,
    TOTAL_CARDS,
)
from .gacha import build_rate_rows, get_pity_bonus, open_bulk_packs, open_pack, open_chest, rarity_label
from .state import ensure_album_state, reset_progress, total_cards_collected
from .liveops_simulator import simulate_liveops


def run_app() -> None:
    st.set_page_config(page_title="Card Album Simulator", layout="wide")
    ensure_album_state(st.session_state)
    
    col_title, col_btn = st.columns([0.95, 0.05], vertical_alignment="bottom")
    with col_title:
        st.title("🎲 Card Album Simulator")
    with col_btn:
        st.markdown(
            """
            <span id="info-button-target"></span>
            <style>
            div.element-container:has(#info-button-target) + div.element-container button {
                border-radius: 50% !important;
                padding: 0 !important;
                min-width: 28px !important;
                width: 28px !important;
                min-height: 28px !important;
                height: 28px !important;
                font-weight: normal !important;
                font-size: 16px !important;
                font-style: italic !important;
                font-family: 'Times New Roman', serif !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                background-color: var(--background-color, white) !important;
                color: var(--text-color, black) !important;
                border: 1px solid var(--text-color, black) !important;
            }
            div.element-container:has(#info-button-target) + div.element-container button * {
                color: var(--text-color, black) !important;
            }
            </style>
            """, 
            unsafe_allow_html=True
        )
        if st.button("i", type="primary", help="Infomation"):
            show_logic_dialog()
    
    tab_inventory, tab_manual, tab_chestdrop, tab_auto, tab_mc, tab_config = st.tabs(["📚 Bộ Sưu Tập", "📦 Mở Pack", "🎮 Chest Drop", "📈 LiveOps Economy", "📊 Monte Carlo Simulator", "⚙️ Economy Tuning"])
    
    with tab_inventory:
        render_inventory_tab()
        
    with tab_manual:
        render_pack_opener_tab()
        
    with tab_chestdrop:
        render_chest_drop_tab()
        
    with tab_mc:
        from .monte_carlo import render_monte_carlo_tab
        render_monte_carlo_tab()
        
    with tab_auto:
        render_analytics_tab()
        
    with tab_config:
        from .config_ui import render_config_tab
        render_config_tab()


def render_grand_album_section() -> None:
    st.toggle(
        "🏆 Grand Album",
        key="grand_album_enabled",
        help="Khi bật, cho phép Album tự động reset khi cày đủ 135 thẻ (áp dụng cho cả Mở Pack và Mô Phỏng).",
    )
    if st.session_state.get("grand_album_enabled", True):
        st.caption("Grand Album: Khi đạt mốc 135 thẻ, kho thẻ tự reset về 0 (giữ nguyên Sao). Các thẻ tiếp theo rút được sẽ tính cho vòng Album mới.")


def render_pity_panel(selected_pack: str) -> None:
    st.subheader("🍀 Chỉ số Pity")
    _, pity_message = get_pity_bonus(st.session_state, selected_pack)
    st.markdown(f"**Gói đang chọn ({selected_pack}):** `{pity_message}`")
    # Lọc ra các gói đang bị tạch (misses > 0) và có cấu hình pity
    pity_data = {p: misses for p, misses in st.session_state["pack_pity"].items() if misses > 0}
    if pity_data:
        st.caption("Các gói đang tích lũy Pity (Số lần mở xịt liên tiếp):")
        cols = st.columns(4)
        for i, (pack, misses) in enumerate(pity_data.items()):
            cols[i % 4].metric(pack, f"{misses} tạch")
    else:
        st.caption("Hiện chưa có gói nào đang tích Pity!")

    pity_rules = []
    for pack_name, pack_config in st.session_state["config_packs"].items():
        if pack_config["pity_threshold"] > 0 and pack_config["pity_increment"] > 0:
            if "+" not in pack_name:
                incr_percent = int(pack_config["pity_increment"] * 100)
                pity_rules.append(f"{pack_name} ({pack_config['pity_threshold']} lần +{incr_percent}%)")
                
    if pity_rules:
        st.caption(f"*Cơ chế (Tạch liên tiếp): {', '.join(pity_rules)}*")


def format_card_name_ui(card):
    if not card: return "Unknown"
    from .config import CARD_SETS
    set_id, rarity, idx = card
    return f"{CARD_SETS[set_id]['name']} #{idx+1}"

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
        from .config import CARD_SETS
        from .gacha import STAR_VALUES
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


def render_inventory_tab() -> None:
    col_ga, col_reset = st.columns([4, 1])
    with col_ga:
        render_grand_album_section()
    with col_reset:
        if st.button("🗑️ Reset Dữ Liệu", use_container_width=True, type="primary"):
            reset_progress(st.session_state)
            st.rerun()
    st.divider()
    
    total_cards = total_cards_collected(st.session_state)
    completions = st.session_state.get("grand_album_completions", 0)
    is_finished = st.session_state.get("grand_album_finished", False)
    
    st.subheader("Tiến độ Album")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("🎴 Thẻ thu thập được", f"{total_cards} / {TOTAL_CARDS}")
        if completions > 0 or is_finished:
            st.markdown("<div style='margin-top:-15px; color:#FFD700; font-weight:bold;'>🏆 Grand Album</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='margin-top:-15px; color:#888; font-weight:bold;'>Thường</div>", unsafe_allow_html=True)
            
    col2.metric("⭐ Tổng Sao Hiện Có", f"{st.session_state['stars']}")
    col3.metric("📈 Thẻ Mới / Thẻ Trùng", f"{st.session_state.get('new_cards_drawn', 0)} / {st.session_state.get('dup_cards_drawn', 0)}")
    
    st.divider()
    st.subheader("Tiến độ theo Độ Hiếm")
    from .config import MAX_CARDS
    
    rarity_colors = {
        1: "gray", 2: "#32CD32", 3: "#1E90FF",
        4: "#9370DB", 5: "#FFA500", 6: "#FF1493"
    }

    rarity_cols = st.columns(6)
    for r in range(1, 7):
        with rarity_cols[r-1]:
            if r < 6:
                icon_str = "⭐" * r
            else:
                icon_str = "<span style='font-size: 1.2em;'>🌟</span>"
            r_owned = st.session_state["inventory"][r]
            r_max = MAX_CARDS[r]
            color = rarity_colors[r]
            pct = int((r_owned / r_max) * 100) if r_max > 0 else 0
            
            html = f"""
            <div style='margin-bottom: 10px;'>
                <div style='font-weight: bold; color: {color}; margin-bottom: 8px;'>{icon_str}</div>
                <div style='width: 100%; background-color: rgba(128,128,128,0.2); border-radius: 5px; height: 10px; margin-bottom: 8px;'>
                    <div style='width: {pct}%; background-color: {color}; height: 100%; border-radius: 5px;'></div>
                </div>
                <div style='font-size: 0.85em; color: gray;'>{r_owned} / {r_max} thẻ</div>
            </div>
            """
            st.markdown(html, unsafe_allow_html=True)
    
    st.divider()
    st.subheader("Chi tiết 15 Set Thẻ")
    from .config import CARD_SETS
    cols = st.columns(3)
    
    set_colors_rgb = [
        "255, 99, 132", "54, 162, 235", "255, 206, 86", 
        "75, 192, 192", "153, 102, 255", "255, 159, 64", 
        "233, 30, 99", "0, 150, 136", "139, 195, 74", 
        "205, 220, 57", "121, 85, 72", "96, 125, 139", 
        "244, 67, 54", "33, 150, 243", "156, 39, 176"
    ]
    
    for idx, (set_id, set_info) in enumerate(CARD_SETS.items()):
        with cols[idx % 3]:
            total_in_set = sum(set_info["cards"].values())
            owned_in_set = [c for c in st.session_state["owned_cards"] if c[0] == set_id]
            owned_count = len(owned_in_set)
            
            rgb = set_colors_rgb[idx % len(set_colors_rgb)]
            pct = int((owned_count / total_in_set) * 100) if total_in_set > 0 else 0
            
            breakdown_html = ""
            for r in sorted(set_info["cards"].keys()):
                r_total = set_info["cards"][r]
                r_owned = len([c for c in owned_in_set if c[1] == r])
                icon = "⭐" * r if r < 6 else "🌟"
                if r_owned == r_total:
                    breakdown_html += f"<div style='font-size:0.85em; margin-top:2px;'>✅ {icon} {r_owned}/{r_total}</div>"
                else:
                    breakdown_html += f"<div style='font-size:0.85em; margin-top:2px; opacity:0.7;'>⬛ {icon} {r_owned}/{r_total}</div>"
            
            is_completed = (total_in_set > 0 and owned_count == total_in_set)
            border_style = f"2px solid rgb({rgb})" if is_completed else f"1px solid rgba({rgb}, 0.5)"
            shadow_style = f"box-shadow: 0 0 12px rgba({rgb}, 0.6);" if is_completed else ""
            title_prefix = "🏆 " if is_completed else ""
            
            set_html = f"""
            <div style='background-color: rgba({rgb}, 0.15); padding: 15px; border-radius: 10px; border: {border_style}; {shadow_style} margin-bottom: 15px;'>
                <div style='font-weight: bold; margin-bottom: 8px;'>{title_prefix}Set {set_id}: {set_info['name']}</div>
                <div style='width: 100%; background-color: rgba(128,128,128,0.2); border-radius: 5px; height: 8px; margin-bottom: 8px;'>
                    <div style='width: {pct}%; background-color: rgb({rgb}); height: 100%; border-radius: 5px;'></div>
                </div>
                <div style='font-size: 0.9em; margin-bottom: 10px;'>Đã có: <b>{owned_count} / {total_in_set}</b> thẻ</div>
                {breakdown_html}
            </div>
            """
            st.markdown(set_html, unsafe_allow_html=True)

@st.dialog("BẠN VỪA NHẬN ĐƯỢC!", width="large")
def show_draw_result_dialog(res: dict):
    st.markdown("""
        <style>
            /* Hack to make the dialog wider on desktop screens */
            div[data-testid="stDialog"] div[role="dialog"] {
                width: 85vw !important;
                max-width: 1200px !important;
            }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown(f"**🌟 MỞ THÀNH CÔNG: {res.get('summary', '')}**")
    if "bulk_summary" in res:
        bs = res["bulk_summary"]
        st.info(f"🏆 Tổng kết Mở Bulk Rương: Rương đã thăng cấp tối đa lên: 2-Sao ({bs.get(2,0)} lần), 3-Sao ({bs.get(3,0)} lần), 4-Sao ({bs.get(4,0)} lần), 5-Sao ({bs.get(5,0)} lần)")
    else:
        st.info(f"📦 Tổng thẻ rút được: +{res.get('total_cards', 0)} | ⭐ Sao Nhận Về: +{res.get('stars_diff', 0)}")
    
    rarity_colors = {
        1: "#B0C4DE", 2: "#32CD32", 3: "#1E90FF",
        4: "#9370DB", 5: "#FFA500", 6: "#FFD700"
    }
    
    def render_card_html(card, is_new):
        from .config import CARD_SETS
        from .gacha import STAR_VALUES
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




def render_pack_opener_tab() -> None:
    with st.container(border=True):
        st.subheader("📊 Tổng Quan Mở Pack")
        col_stats1, col_stats2, col_stats3, col_stats4 = st.columns(4)
        
        rarity_colors = {
            1: "gray", 2: "#32CD32", 3: "#1E90FF",
            4: "#9370DB", 5: "#FFA500", 6: "#FF1493"
        }
        
        def st_color_tier(r):
            colors = {1: "gray", 2: "green", 3: "blue", 4: "violet", 5: "orange", 6: "red"}
            c = colors.get(int(r), "gray")
            label = f"{r}-Sao" if int(r) < 6 else "VÀNG"
            return f":{c}[{label}]"

        
        new_total = st.session_state.get('new_cards_drawn', 0)
        new_dict = st.session_state.get('new_cards_by_rarity', {})
        new_parts = []
        for r in range(1, 7):
            if new_dict.get(r, 0) > 0:
                icon = "⭐" if r < 6 else "🌟"
                new_parts.append(f"<span style='color:{rarity_colors[r]}'>{r}{icon}: {new_dict[r]}</span>")
        new_detail = f"<div style='font-size:0.85em; margin-top:-10px; color:#aaa'>({', '.join(new_parts)})</div>" if new_parts else ""

        dup_total = st.session_state.get('dup_cards_drawn', 0)
        dup_dict = st.session_state.get('dup_cards_by_rarity', {})
        dup_parts = []
        for r in range(1, 7):
            if dup_dict.get(r, 0) > 0:
                icon = "⭐" if r < 6 else "🌟"
                dup_parts.append(f"<span style='color:{rarity_colors[r]}'>{r}{icon}: {dup_dict[r]}</span>")
        dup_detail = f"<div style='font-size:0.85em; margin-top:-10px; color:#aaa'>({', '.join(dup_parts)})</div>" if dup_parts else ""
        
        with col_stats1:
            st.metric("🃏 Tổng Thẻ Rút Ra", f"{st.session_state['total_cards_drawn']}")
        with col_stats2:
            st.metric("🎴 Thẻ Mới Nhận", f"{new_total}")
            if new_detail: st.markdown(new_detail, unsafe_allow_html=True)
        with col_stats3:
            pack_stars = st.session_state.get('pack_stars_gained', 0)
            st.metric("♻️ Thẻ Trùng (Sao Nhận)", f"{dup_total} (+{pack_stars}⭐)")
            if dup_detail: st.markdown(dup_detail, unsafe_allow_html=True)
        with col_stats4:
            st.metric("📦 Tổng Pack Đã Mở", f"{st.session_state['total_packs']}")
        
        st.markdown("<hr style='margin: 10px 0px; opacity: 0.3'>", unsafe_allow_html=True)
        st.caption("Chi tiết số lượng từng gói đã mở:")
        pack_cols = st.columns(5)
        for i, pack in enumerate(PACK_ORDER):
            with pack_cols[i % 5]:
                st.markdown(f"**{PACK_ICONS[pack]} {pack}**: {st.session_state['pack_counts'][pack]}")
            
    st.markdown("<hr style='margin: 15px 0px; opacity: 0.3'>", unsafe_allow_html=True)
    
    col_left, col_right = st.columns([1, 1.2])
    with col_left:
        st.subheader("🛒 Giỏ Hàng")
        st.caption("Nhập số lượng gói bạn muốn mở.")
        shop_cols = st.columns(2)
        for i, pack in enumerate(PACK_ORDER):
            with shop_cols[i % 2]:
                if f"cart_input_{pack}" not in st.session_state:
                    st.session_state[f"cart_input_{pack}"] = st.session_state["cart_packs"].get(pack, 0)
                st.number_input(f"{PACK_ICONS[pack]} {pack}", min_value=0, max_value=10000, step=1, key=f"cart_input_{pack}")
                st.session_state["cart_packs"][pack] = st.session_state[f"cart_input_{pack}"]

        st.markdown("<br>", unsafe_allow_html=True)
        auto_chest = st.checkbox("🔄 Tự động dùng sao dư để đổi Star Chest", key="auto_chest_chk", help="Hệ thống sẽ tự động mua rương xịn nhất có thể (Vàng -> Bạc -> Đồng) cho đến khi không đủ sao (dưới 100 sao).")
        def execute_cart():
            res = open_bulk_packs(st.session_state, st.session_state["cart_packs"], st.session_state.get("auto_chest_chk", False))
            if not res["success"]:
                st.session_state["cart_error"] = res["message"]
            else:
                st.session_state["cart_success"] = res
        def reset_cart():
            for p in PACK_ORDER:
                st.session_state[f"cart_input_{p}"] = 0
                st.session_state["cart_packs"][p] = 0

        col_exec, col_reset = st.columns([3, 1])
        col_exec.button("🚀 MỞ CÁC GÓI ĐÃ CHỌN", type="primary", use_container_width=True, on_click=execute_cart)
        col_reset.button("🗑️ Xóa Giỏ Hàng", use_container_width=True, on_click=reset_cart)
        if "cart_error" in st.session_state:
            st.error(st.session_state.pop("cart_error"))
        if "cart_success" in st.session_state:
            show_draw_result_dialog(st.session_state.pop("cart_success"))

        st.markdown("<hr style='margin: 15px 0px; opacity: 0.3'>", unsafe_allow_html=True)
        st.subheader(f"🌟 Đổi Rương Sao (Hiện có {st.session_state['stars']} ⭐)")
        st.caption("Dùng Sao để đổi lấy rương thưởng đặc biệt.")
        
        def execute_chest(chest_type):
            res = open_chest(st.session_state, chest_type)
            if res["success"]:
                st.session_state["chest_success"] = res
            else:
                st.session_state["chest_error"] = res["message"]

        chest_col1, chest_col2, chest_col3 = st.columns(3)
        chest_col1.button("🥉 Bronze Chest (100⭐)", use_container_width=True, on_click=execute_chest, args=("Bronze",))
        chest_col2.button("🥈 Silver Chest (250⭐)", use_container_width=True, on_click=execute_chest, args=("Silver",))
        chest_col3.button("🥇 Gold Chest (500⭐)", use_container_width=True, on_click=execute_chest, args=("Gold",))
        
        if "chest_error" in st.session_state:
            st.error(st.session_state.pop("chest_error"))
        if "chest_success" in st.session_state:
            show_draw_result_dialog(st.session_state.pop("chest_success"))

    with col_right:
        selected_pack = st.selectbox("🔍 Chọn Pack:", PACK_ORDER)
        
        def execute_multi_pack(pack, count):
            res = open_bulk_packs(st.session_state, {pack: count}, False)
            if res["success"]:
                st.session_state["single_success"] = res
                st.session_state["single_success_count"] = count
                st.session_state["single_success_pack"] = pack
            else:
                st.session_state["single_error"] = res["message"]
                
        col_btn1, col_btn10 = st.columns(2)
        col_btn1.button(f"🎟️ Mở 1 gói", type="primary", use_container_width=True, on_click=execute_multi_pack, args=(selected_pack, 1))
        col_btn10.button(f"🎟️ Mở 10 gói", type="primary", use_container_width=True, on_click=execute_multi_pack, args=(selected_pack, 10))
        
        if "single_error" in st.session_state:
            st.error(st.session_state.pop("single_error"))
        if "single_success" in st.session_state:
            res = st.session_state.pop("single_success")
            count = st.session_state.pop("single_success_count")
            pack = st.session_state.pop("single_success_pack")
            res["summary"] = f"{count} gói {pack}"
            show_draw_result_dialog(res)
            
        st.markdown("<hr style='margin: 10px 0px; opacity: 0.3'>", unsafe_allow_html=True)
        render_rate_panel(selected_pack)

    st.divider()
    render_log_panel()


def render_log_panel() -> None:
    st.subheader("📝 Kết Quả Mở Pack")
    if st.session_state["log"]:
        latest = st.session_state["log"][0]
        if is_positive_log(latest):
            st.success(f"**[MỚI NHẤT]** {latest}")
        else:
            st.warning(f"**[MỚI NHẤT]** {latest}")

    with st.expander("📜 Xem toàn bộ lịch sử", expanded=True):
        log_container = st.container(height=400)
        for entry in st.session_state["log"][1:]:
            if is_positive_log(entry):
                log_container.success(entry)
            elif "====" in entry:
                log_container.markdown(f"**{entry}**")
            else:
                log_container.warning(entry)

        if not st.session_state["log"]:
            log_container.info("Chưa mở gói nào. Hãy sử dụng chức năng ở cột trái!")


def render_rate_panel(selected_pack: str) -> None:
    st.subheader(f"🔍 Tỉ Lệ Động: Gói {selected_pack}")

    if selected_pack == "Rainbow":
        st.info(
            "**Cơ chế Rainbow:**\n"
            "- Gói có tổng cộng 6 thẻ (5 thẻ đầu random theo tỉ lệ cao).\n"
            "- Thẻ thứ 6 (bảo hiểm) 100% ra thẻ MỚI.\n"
            "- Ưu tiên lấp đầy Thẻ Vàng trước.\n"
            "- Nếu đã có đủ 18 Thẻ Vàng, lấp ngẫu nhiên các thẻ còn thiếu."
        )
        return

    effective_size = PACKS[selected_pack].size
    rows = build_rate_rows(st.session_state, selected_pack)
    st.dataframe(
        pd.DataFrame(rows), 
        use_container_width=True, 
        hide_index=True,
        column_config={
            "Thẻ MỚI": st.column_config.Column(
                "Thẻ MỚI",
                help="Tỉ lệ bốc được thẻ mà bạn CHƯA CÓ trong Album. Được cộng dồn với Buff Pity. Sẽ về 0% nếu đã sưu tập đủ độ hiếm đó."
            ),
            "Thẻ TRÙNG": st.column_config.Column(
                "Thẻ TRÙNG",
                help="Công thức: 100% - Tỉ lệ Thẻ MỚI.\nThẻ trùng sẽ tự động được phân rã thành số Sao tương ứng với độ hiếm."
            )
        }
    )
        
    guaranteed_tier = PACKS[selected_pack].guaranteed_tier
    guaranteed_label = f"{guaranteed_tier}-Sao" if guaranteed_tier < 6 else "Thẻ VÀNG"
    caption = f"Gói này gồm **{effective_size} thẻ**. Chắc chắn có ít nhất 1 **{guaranteed_label}**."
    st.caption(caption)
    
    st.divider()
    render_pity_panel(selected_pack)


def is_positive_log(entry: str) -> bool:
    return "✅" in entry or "🌈" in entry or "🌟" in entry


def render_analytics_tab() -> None:
    st.header("📈 LiveOps Economy Simulator")
    st.markdown("Giả lập số lượng gói thẻ nhận được từ các sự kiện LiveOps dựa trên số ngày chơi và nỗ lực cày cuốc.")
    
    col1, col2 = st.columns([1, 1.5])
    
    with col1:
        st.subheader("🗓️ Thông số Cày cuốc")
        days = st.number_input("Số Ngày (Mùa giải)", min_value=1, max_value=365, value=60)
        
        col_lvl1, col_lvl2 = st.columns(2)
        with col_lvl1:
            levels_per_weekday = st.number_input("Level chơi trong tuần (T2-T5)", min_value=0, max_value=100, value=5)
        with col_lvl2:
            levels_per_weekend = st.number_input("Level chơi cuối tuần (T6-CN)", min_value=0, max_value=100, value=15)
        
        st.subheader("🎯 Bật/Tắt LiveOps")
        toggles = {}
        toggles["core_gameplay"] = st.toggle(
            "⚔️ Core Gameplay (Thưởng Level Khó)",
            value=True,
            help="Thưởng 1 Bronze khi thắng Hard, 1 Emerald khi thắng Super Hard."
        )
        toggles["win_streak"] = st.toggle("Win Streak", value=True,
            help="Nhận phần thưởng khi đạt các chuỗi thắng liên tiếp (Sự kiện diễn ra từ T6-CN hàng tuần, reset mỗi đầu sự kiện).")
        toggles["key_collection"] = st.toggle(
            "🔑 Key Collection", 
            value=True,
            help="Tích lũy chìa khóa qua các màn chơi để mở khóa phần thưởng."
        )
        toggles["master_pass"] = st.toggle(
            "🎟️ Master Pass", 
            value=True,
            help="Hệ thống Battle Pass của game, gồm nhánh Free và Premium."
        )
        
        if toggles["master_pass"]:
            toggles["master_pass_premium"] = st.checkbox("Mở khóa nhánh Premium (Yarn Pass) - $9.99", value=False)
        else:
            toggles["master_pass_premium"] = False
            
        toggles["card_rush"] = st.toggle(
            "⚡ Card Rush", 
            value=True,
            help="Nhân thêm số lượng thẻ cho các gói nhận được vào ngày sự kiện."
        )
        toggles["chest_drop"] = st.toggle(
            "🎮 Chest Drop",
            value=True,
            help="Nhận Rương 1-Sao (3 win), 2-Sao (7 win), 3-Sao (12 win) hàng ngày."
        )
            
        st.subheader("🛒 Cửa Hàng & IAP")
        iap_selections = {}
        
        with st.expander("🛍️ Main Shop Bundles", expanded=False):
            iap_selections["shop_9.99"] = st.number_input("$9.99 (Decorated Pouch): +1 Silver Pack", min_value=0, value=0)
            iap_selections["shop_19.99"] = st.number_input("$19.99 (Artisan Satchel): +1 Amethyst Pack", min_value=0, value=0)
            iap_selections["shop_29.99"] = st.number_input("$29.99 (Exquisite Basket): +1 Ruby Pack", min_value=0, value=0)
            iap_selections["shop_49.99"] = st.number_input("$49.99 (Overflowing Chest): +1 Rainbow Pack", min_value=0, value=0)
            iap_selections["shop_99.99"] = st.number_input("$99.99 (Royal Vault): +3 Rainbow Pack", min_value=0, value=0)
            
        with st.expander("💸 Out Of Coins", expanded=False):
            iap_selections["ooc_4"] = st.number_input("Super OOC 4 ($6.99): 2000 Coins + 2x Scissors + 1x Emerald Pack", min_value=0, value=0)
            iap_selections["ooc_5"] = st.number_input("OOC 5 ($14.99): 5000 Coins + 3x Scissors + 2x Hammer + 1x Silver Pack", min_value=0, value=0)
            iap_selections["ooc_6"] = st.number_input("OOC 6 ($29.99): 11000 Coins + 4x Scissors + 3x Hammer + 2x Broom + 1x Amethyst Pack", min_value=0, value=0)
        
        with st.expander("🔗 Chain Offer", expanded=False):
            st.info("💡 Part 1 (Miễn phí) luôn được tự động nhận: **1x Bronze Pack** + 1x Scissors + 15m Heart.")
            iap_selections["chain_part_2"] = st.checkbox("Mua Part 2 ($2.49) -> Nhận toàn bộ Part 2: **1x Emerald, 1x Bronze**, 900 Coins, 1x Scissors, 1x Hammer, 30m Heart", value=False)
            iap_selections["chain_part_3"] = st.checkbox("Mua Part 3 ($4.99) -> Nhận toàn bộ Part 3: **1x Silver, 1x Emerald**, 1800 Coins, 1x Scissors, 1x Hammer, 1x Broom, 60m Heart", value=False)
            iap_selections["chain_part_4"] = st.checkbox("Mua Part 4 ($10.99) -> Nhận toàn bộ Part 4: **1x Amethyst, 1x Emerald, 1x Silver**, 4000 Coins, 3x Scissors, 3x Hammer, 1x Broom, 1h Heart", value=False)
            iap_selections["chain_part_5"] = st.checkbox("Mua Part 5 ($18.99) -> Nhận toàn bộ Part 5: **1x Ruby, 1x Amethyst, 1x Silver**, 8300 Coins, 2x Scissors, 2x Hammer, 2x Broom, 4h Heart", value=False)
            iap_selections["chain_part_6"] = st.checkbox("Mua Part 6 ($27.99) -> Nhận toàn bộ Part 6: **1x Gold, 1x Silver, 1x Amethyst**, 13200 Coins, 4x Scissors, 4x Hammer, 3x Broom, 6h Heart", value=False)
            iap_selections["chain_part_7"] = st.checkbox("Mua Part 7 ($49.99) -> Nhận toàn bộ Part 7: **1x Rainbow, 1x Ruby, 1x Emerald, 1x Silver, 1x Amethyst**, 25500 Coins, 4x Scissors, 4x Hammer, 4x Broom, 12h Heart", value=False)
            
    with col2:
        if st.button("🧮 TÍNH TOÁN PHẦN THƯỞNG", type="primary", use_container_width=True):
            res = simulate_liveops(days, levels_per_weekday, levels_per_weekend, toggles, iap_selections, st.session_state["config_rewards"])
            st.session_state["liveops_result"] = res
            
        if "liveops_result" in st.session_state:
            res = st.session_state["liveops_result"]
            st.success("✅ **Đã tính toán xong**")
            
            with st.expander("⚙️ Các giả định (Assumptions) của hệ thống", expanded=True):
                for asm in res.get("assumptions", []):
                    st.markdown(f"- {asm}")
            
            lvl = res["levels_info"]
            st.markdown(f"**Tổng quan Level:** Chơi {lvl['total']} màn (Thắng: {lvl['normal']} Normal, {lvl['hard']} Hard, {lvl['super_hard']} Super Hard)")
            
            st.subheader("📦 Tổng số Gói (Packs) Nhận Được")
            total = res["total_packs"]
            c1, c2, c3, c4 = st.columns(4)
            c1.metric(f"{PACK_ICONS['Bronze']} Bronze", total["Bronze"])
            c2.metric(f"{PACK_ICONS['Emerald']} Emerald", total["Emerald"])
            c3.metric(f"{PACK_ICONS['Silver']} Silver", total["Silver"])
            c4.metric(f"{PACK_ICONS['Amethyst']} Amethyst", total["Amethyst"])
            
            if total.get("Bronze+") or total.get("Emerald+") or total.get("Silver+"):
                cp1, cp2, cp3, _ = st.columns(4)
                cp1.metric(f"{PACK_ICONS['Bronze+']} Bronze+", total.get("Bronze+", 0))
                cp2.metric(f"{PACK_ICONS['Emerald+']} Emerald+", total.get("Emerald+", 0))
                cp3.metric(f"{PACK_ICONS['Silver+']} Silver+", total.get("Silver+", 0))
            
            c5, c6, c7, c8 = st.columns(4)
            c5.metric(f"{PACK_ICONS['Ruby']} Ruby", total["Ruby"])
            c6.metric(f"{PACK_ICONS['Gold']} Gold", total["Gold"])
            c7.metric(f"{PACK_ICONS['Rainbow']} Rainbow", total["Rainbow"])
            c8.metric("💸 Tổng chi (IAP)", f"${res.get('total_spent', 0.0):.2f}")
            
            st.write("")
            if res.get("chest_drop_chests"):
                chests = res["chest_drop_chests"]
                if sum(chests.values()) > 0:
                    st.subheader("📦 Tổng số Rương Chest Drop Nhận Được")
                    cc1, cc2, cc3 = st.columns(3)
                    cc1.metric("Rương 1-Sao", chests.get(1, 0))
                    cc2.metric("Rương 2-Sao", chests.get(2, 0))
                    cc3.metric("Rương 3-Sao", chests.get(3, 0))
                    st.write("")
            def add_packs_to_cart(total_packs, chests_earned):
                for pack in PACK_ORDER:
                    st.session_state[f"cart_input_{pack}"] = 0
                    st.session_state["cart_packs"][pack] = 0
                for pack, count in total_packs.items():
                    if pack in PACK_ORDER and count > 0:
                        st.session_state[f"cart_input_{pack}"] = count
                        st.session_state["cart_packs"][pack] = count
                        
                if chests_earned:
                    for tier, count in chests_earned.items():
                        key = f"bulk_chest_{tier}"
                        if key not in st.session_state:
                            st.session_state[key] = 0
                        st.session_state[key] += count

                st.session_state["show_cart_success"] = True
                        
            st.button("📥 LƯU TOÀN BỘ PACKS & RƯƠNG VÀO GIỎ HÀNG", type="primary", on_click=add_packs_to_cart, args=(total, res.get("chest_drop_chests", {})))
            
            if st.session_state.get("show_cart_success"):
                st.success("✅ Đã thêm Packs vào Giỏ Hàng! Bạn có thể sang tab **Mở Gói (Gacha)** hoặc **Monte Carlo Simulator** để tiến hành mở.")
                st.session_state["show_cart_success"] = False
            
            st.divider()
            st.subheader("🔎 Chi tiết Nguồn nhận & Phần thưởng khác")
            
            import pandas as pd
            import altair as alt
            source_df = pd.DataFrame(list(res["source_breakdown"].items()), columns=["Source", "Total"])
            source_df = source_df[source_df["Total"] > 0]
            if not source_df.empty:
                chart = alt.Chart(source_df).mark_arc().encode(
                    theta=alt.Theta(field="Total", type="quantitative"),
                    color=alt.Color(field="Source", type="nominal", legend=alt.Legend(title="Nguồn", orient="right")),
                    tooltip=["Source", "Total"]
                ).properties(height=300)
                st.altair_chart(chart, use_container_width=True)
            else:
                st.info("Chưa có dữ liệu nguồn nhận")
                
            st.write("")
            
            with st.expander("⚔️ Thắng Level Hard/Super Hard (Core Gameplay)"):
                for l in res["logs"]["core"]: st.markdown(f"- {l}")
                
            if toggles["win_streak"]:
                with st.expander("🔥 Win Streak"):
                    for l in res["logs"]["win_streak"]: st.markdown(f"- {l}")
                    
            if toggles.get("chest_drop", True):
                with st.expander("🎮 Chest Drop Hàng Ngày"):
                    if "chest_drop" in res["logs"]:
                        for l in res["logs"]["chest_drop"]: st.markdown(f"- {l}")
                    
            if toggles["key_collection"]:
                with st.expander("🔑 Key Collection"):
                    for l in res["logs"]["key_collection"]: st.markdown(f"- {l}")
                    
            if toggles["master_pass"]:
                with st.expander("🎟️ Master Pass (Yarn Pass)"):
                    for l in res["logs"]["master_pass"]: st.markdown(f"- {l}")
            
            with st.expander("🛒 IAP / Mua sắm"):
                iap_str = ", ".join([f"**{p}:** {v}" for p, v in res["iap_packs"].items() if v > 0])
                if not iap_str: iap_str = "Chưa mua/nhận gói nào"
                st.write(f"**Tổng kết Pack từ IAP:** {iap_str}")
                for l in res["logs"]["iap"]: st.markdown(f"- {l}")
                
            if toggles["card_rush"]:
                with st.expander("⚡ Card Rush Bonus"):
                    if res["logs"].get("card_rush"):
                        for l in res["logs"]["card_rush"]: st.markdown(f"- {l}")
                    else:
                        st.markdown("- Chưa có thông tin Card Rush.")

@st.dialog("📖 TỔNG QUAN LOGIC HỆ THỐNG", width="large")
def show_logic_dialog():
    st.markdown("""
        <style>
            /* Hack to make the dialog wider on desktop screens */
            div[data-testid="stDialog"] div[role="dialog"] {
                width: 85vw !important;
                max-width: 1200px !important;
            }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
### 1. Cơ Chế Gacha Cơ Bản & Pity (Bảo hiểm)
- **Tỉ lệ Rớt Độ Hiếm (Drop Rates):** 
  - (VD: 28% ra 1-Sao, 1% ra Vàng) là **CỐ ĐỊNH** và luôn không đổi trong suốt quá trình mở gói.
- **Công thức Tỉ lệ Thẻ MỚI (New Chance):** 
  - Là tỉ lệ để lá thẻ vừa rớt ra rơi vào lá bạn CHƯA CÓ. Tỉ lệ này tự động trượt giảm dần theo công thức chung: 
  - `New Card Ratio = (Remaining New / Total) ^ (x + y) + Pity`
  - `x`: Hệ số Khó chung (Càng cao càng khó ra thẻ mới, tuỳ chỉnh trong Tuning).
  - `y`: Hệ số Khó riêng (Ở Gacha mở pack, y lấy theo loại Gói. Ở Chest Drop, y lấy theo Độ Hiếm của thẻ).
- **Thẻ Bảo Hiểm (Guaranteed):** Mỗi gói đều cam kết rớt 1 thẻ ở ĐÚNG độ hiếm cụ thể (Ví dụ gói Emerald chắc chắn có 1 thẻ 2-Sao).
- **Cơ Chế Pity (Đếm Tạch):** 
  - Hoạt động **độc lập** cho TỪNG LOẠI GÓI THẺ. (Pity của Silver KHÔNG chia sẻ cho Amethyst).
  - Mỗi khi mở một gói mà không ra bất kỳ thẻ **NEW** nào, số lần "Tạch" của gói đó tăng lên 1.
  - Khi tạch đến ngưỡng quy định, gói đó sẽ được **buff thêm % Tỉ lệ ra Thẻ Mới** ở lần mở sau. (Vd: Gói Silver tạch 3 lần sẽ buff +20%).
- **Ngắt Pity Giữa Chừng (Mid-Pack Reset):** Tỉ lệ buff Pity được cộng thẳng vào từng lá bài khi nó lật lên. Ngay khoảnh khắc lá bài đầu tiên nổ ra chữ **NEW**, lượng % buff này sẽ **lập tức bốc hơi (về 0%)**. Các lá bài lật sau đó trong cùng gói sẽ trở về tỉ lệ gốc, nhằm chống lạm phát thẻ mới.

### 2. Rainbow Pack & 5 Gói Tân Thủ
- **Tân Thủ:** 5 gói thẻ đầu tiên bạn nhận được trong Mùa (từ bất kỳ nguồn nào) sẽ được hệ thống buff **100% rớt toàn Thẻ Mới**.
- **Rainbow Pack:** Gói thẻ đặc quyền có 6 thẻ, trong đó chắc chắn rớt 1 Thẻ Mới (Wild Card). Thuật toán sẽ luôn ưu tiên rớt **Thẻ Vàng (6-Sao)** trước. 
  - *Clarification:* Trong game gốc, nếu Vàng đã full, Wild Card sẽ ưu tiên các "Bộ (Sets) chỉ còn thiếu 1 lá". Do Simulator này chỉ track tiến độ theo Độ Hiếm, hệ thống sẽ giả lập bằng cách rớt ngẫu nhiên 1 Thẻ Mới từ các độ hiếm còn thiếu.

### 3. Grand Album & Thẻ Trùng (Duplicated)
- **Hoàn thành Album:** Sau khi sưu tập đủ 135 thẻ, bạn sẽ hoàn thành vòng Album và được thăng cấp sang "Grand Album".
- **Luật Reset:** Khi thăng cấp, kho thẻ sẽ **bị Reset toàn bộ về 0**, nhưng lượng **Sao (Stars)** bạn tích lũy được sẽ **giữ nguyên vẹn** (Dùng để mua các rương sao sau này).
- **Thẻ Trùng:** Mọi thẻ trùng lặp quay ra sẽ tự động phân rã thành **Sao**. Thẻ càng hiếm, số Sao thu được càng cao (Từ 1 Sao cho thẻ 1-Sao lên tới 15 Sao cho Thẻ Vàng).

### 4. Hệ Sinh Thái LiveOps (Sự kiện & Nền kinh tế)
Trong tab `📈 LiveOps Simulator`, hệ thống sử dụng thuật toán giả lập để ước tính số Pack bạn nhận được dựa trên giả định bạn chơi hoàn hảo (perfect play) theo số ngày và số level đã cấu hình:
- **Core Gameplay (Thắng màn Khó):** Cứ thắng màn Hard sẽ thưởng gói Bronze, thắng Super Hard thưởng gói Emerald. Tiến trình Level diễn ra theo chu kỳ cố định: N-N-H, N-N-H, N-N-SH (sau 2 Normal tới 1 Hard, sau 2 Hard tới 1 Super Hard).
- **Win Streak:** Giữ chuỗi thắng liên tiếp để càn quét các phần thưởng dọc đường. Sự kiện tự động kích hoạt vào mỗi cuối tuần (Thứ 6 đến Chủ Nhật). Chuỗi thắng bị reset về 0 mỗi đầu sự kiện. Từ lần đạt mốc cao nhất (Mốc 45) thứ 2 trở đi, phần thưởng Avatar sẽ được quy đổi thành Ruby Pack. *(Có thể xem chi tiết các phần thưởng ở tab Economy Tuning)*
- **Master Pass (Battle Pass):** Hệ thống Battle Pass của game. Thu thập token từ các màn chơi (Thắng Normal: 1 Token, Hard: 2 Tokens, Super Hard: 3 Tokens) để thăng cấp (tối đa 30) và nhận thưởng. Nhánh Premium (trả phí) sẽ mở khóa nhiều phần thưởng hấp dẫn hơn. Sự kiện được reset tiến trình và lặp lại mỗi tháng (30 ngày). *(Có thể xem chi tiết các phần thưởng ở tab Economy Tuning)*
- **Key Collection:** Cày chìa khóa theo tiến độ để mở khóa các phần thưởng theo mốc. Mỗi level qua màn nhận mặc định 5 keys bất kể độ khó. Sự kiện được reset tiến trình và lặp lại vào mỗi đầu tuần (Thứ 2). *(Có thể xem chi tiết các phần thưởng ở tab Economy Tuning)*
- **Chain Offer & IAP:** Các sự kiện bán gói ưu đãi theo chuỗi. Simulator cho phép bạn giả lập "tiêu tiền" vào các mốc Chain (VD: Mua OOC, Mua Shop) để tính toán tổng lợi nhuận Pack thu về so với số USD đã bỏ ra. Mặc định mua các gói này nhận Pack thường (Không áp dụng thưởng sự kiện Card Rush).
- **⚡ Card Rush:** Sự kiện đặc biệt mở theo lịch tuần (Tuần 1-2: Thứ 7 | Tuần 3-5: Thứ 4, 7 | Tuần 6-9: Thứ 2, 4, 7). Khi kích hoạt, các gói thẻ thường (Bronze, Emerald, Silver) sẽ chuyển thành **Plus (+), thêm 50% số lượng thẻ** vào từng gói (VD: Bronze từ 2 lên 3 thẻ, Emerald từ 3 lên 5 thẻ, Silver từ 4 lên 6 thẻ...). Mua gói từ Shop/IAP sẽ KHÔNG được cộng dồn Card Rush.
    """)


def render_chest_drop_tab() -> None:
    import streamlit as st
    import pandas as pd
    import time
    
    with st.container(border=True):
        st.subheader("📊 Tổng Quan Chest Drop")
        col_stats1, col_stats2, col_stats3, col_stats4 = st.columns(4)
        
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
            st.metric("📦 Tổng Chest Đã Mở", f"{total_chests}")
        
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
        
    def get_upgrade_str(tier_str):
        if tier_str not in upgrade_cfg: return "0%"
        return f"{upgrade_cfg[tier_str]['upgrade_chance']*100:.0f}%"

    from .gacha import calculate_chest_drop_new_chance, add_log
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

    df_upgrade = pd.DataFrame([
        {"Rương": "1-Sao", "Phần thưởng (Mỗi hit)": get_reward_str("1"), "Thẻ MỚI": get_new_chance_str("1"), "Tỉ lệ thăng cấp": get_upgrade_str("1")},
        {"Rương": "2-Sao", "Phần thưởng (Mỗi hit)": get_reward_str("2"), "Thẻ MỚI": get_new_chance_str("2"), "Tỉ lệ thăng cấp": get_upgrade_str("2")},
        {"Rương": "3-Sao", "Phần thưởng (Mỗi hit)": get_reward_str("3"), "Thẻ MỚI": get_new_chance_str("3"), "Tỉ lệ thăng cấp": get_upgrade_str("3")},
        {"Rương": "4-Sao", "Phần thưởng (Mỗi hit)": get_reward_str("4"), "Thẻ MỚI": get_new_chance_str("4"), "Tỉ lệ thăng cấp": get_upgrade_str("4")},
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
                    "upgraded_last_hit": False
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
                    from .gacha import process_chest_drop_hit
                    res = process_chest_drop_hit(st.session_state, current_tier)
                    
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
                        from .gacha import format_card_name
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
                        "upgraded_last_hit": False
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
                from .gacha import STAR_VALUES
                from .config import CARD_SETS
                
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
        
        if col_exec.button('💥 MỞ TOÀN BỘ GIỎ HÀNG', type='primary', use_container_width=True, disabled=(total_bulk==0)):
            from .gacha import process_chest_drop_hit
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
            
            from .gacha import format_card_name
            for start_tier, count in cart_to_open.items():
                for i in range(count):
                    current_t = start_tier
                    hit_logs = []
                    chest_has_new = False
                    for _ in range(5):
                        res = process_chest_drop_hit(st.session_state, current_t)
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
            
        col_reset.button("🗑️ Xoá giỏ hàng", use_container_width=True, on_click=reset_cart_cd)
                
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
        st.subheader("🔎 Bảng Tỉ Lệ Động")
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
