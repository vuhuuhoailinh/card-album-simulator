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

def render_grand_album_section() -> None:
    st.toggle(
        "🏆 Grand Album",
        key="grand_album_enabled",
        help="Khi bật, cho phép Album tự động reset khi cày đủ 135 thẻ (áp dụng cho cả Mở Pack và Mô Phỏng).",
    )
    if st.session_state.get("grand_album_enabled", True):
        st.caption("Grand Album: Khi đạt mốc 135 thẻ, kho thẻ tự reset về 0 (giữ nguyên Sao). Các thẻ tiếp theo rút được sẽ tính cho vòng Album mới.")


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
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🎴 Thẻ thu thập được", f"{total_cards} / {TOTAL_CARDS}")
        if completions > 0 or is_finished:
            st.markdown("<div style='margin-top:-15px; color:#FFD700; font-weight:bold;'>🏆 Grand Album</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='margin-top:-15px; color:#888; font-weight:bold;'>Thường</div>", unsafe_allow_html=True)
            
    col2.metric("⭐ Tổng Sao Hiện Có", f"{st.session_state['stars']}")
    total_new = st.session_state.get('new_cards_drawn', 0) + st.session_state.get('cd_new_cards_drawn', 0)
    total_dup = st.session_state.get('dup_cards_drawn', 0) + st.session_state.get('cd_dup_cards_drawn', 0)
    col3.metric("📈 Thẻ Mới / Thẻ Trùng", f"{total_new} / {total_dup}")
    
    total_drawn = total_new + total_dup
    dup_rate = (total_dup / total_drawn * 100) if total_drawn > 0 else 0
    col4.metric("♻️ Tỉ lệ Thẻ Trùng", f"{total_dup}/{total_drawn} ({dup_rate:.2f}%)")
    
    st.divider()
    st.subheader("Tiến độ theo Độ Hiếm")
    from ..config import MAX_CARDS
    
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
    from ..config import CARD_SETS
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


