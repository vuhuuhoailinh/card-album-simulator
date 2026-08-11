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


