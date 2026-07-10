import pandas as pd
import streamlit as st
import altair as alt

from .config import (
    CARD_RUSH_PACK_SIZES,
    MAX_CARDS,
    PACK_ICONS,
    PACK_ORDER,
    PACKS,
    RARITIES,
    TOTAL_CARDS,
)
from .gacha import build_rate_rows, get_effective_pack_size, get_pity_bonus, open_bulk_packs, open_pack, rarity_label
from .state import ensure_album_state, reset_progress, total_cards_collected
from .simulation import run_monte_carlo


def run_app() -> None:
    st.set_page_config(page_title="Card Album Simulator", layout="wide")
    ensure_album_state(st.session_state)

    selected_pack = render_sidebar()
    st.title("🎲 Card Album Simulator")
    
    tab_manual, tab_auto = st.tabs(["🎮 Mở Pack", "📊 Mô Phỏng (Analytics Sandbox)"])
    
    with tab_manual:
        render_album_dashboard()
        st.divider()
        render_main_content(selected_pack)
        
    with tab_auto:
        render_analytics_tab()


def render_sidebar() -> str:
    with st.sidebar:
        inject_sidebar_toggle_style()
        st.title("🎮GACHA MENU")

        render_card_rush_section()
        st.divider()
        st.subheader("🛒 Mở Từng Pack")
        selected_pack = st.selectbox("Chọn Pack:", PACK_ORDER, key="single_pack_select")

        if st.button(f"MỞ 1 GÓI {selected_pack.upper()}", type="primary", use_container_width=True):
            open_pack(st.session_state, selected_pack)
            st.rerun()

        st.subheader("📦 Mở Nhiều Pack")
        with st.expander("⚙️ Cài đặt số lượng Packs", expanded=False):
            bulk_inputs = {}
            for pack in PACK_ORDER:
                bulk_inputs[pack] = st.number_input(
                    f"{PACK_ICONS[pack]} {pack}",
                    min_value=0,
                    max_value=1000,
                    value=0,
                    step=1,
                    key=f"bulk_{pack}",
                )

            if st.button("🚀 BẮT ĐẦU MỞ HÀNG LOẠT", type="primary", use_container_width=True):
                success, message = open_bulk_packs(st.session_state, bulk_inputs)
                st.toast(message, icon="🎉" if success else "⚠️")
                if success:
                    st.rerun()

        st.markdown("___________________")
        if st.button("🗑️ Reset Toàn Bộ Dữ Liệu", use_container_width=True):
            reset_progress(st.session_state)
            st.rerun()

    return selected_pack


def render_card_rush_section() -> None:
    st.toggle(
        "⚡ Sự kiện Card Rush",
        key="card_rush_enabled",
        help="Khi bật, Bronze/Emerald/Silver có nhiều hơn 50% thẻ theo event Card Rush.",
    )
    if st.session_state.get("card_rush_enabled", False):
        st.caption("Card Rush đang bật: Bronze rớt 3 thẻ, Emerald rớt 5 thẻ, Silver rớt 6 thẻ.")
        
    st.toggle(
        "🏆 Grand Album",
        key="grand_album_enabled",
        help="Khi bật, cho phép Album tự động reset khi cày đủ 135 thẻ (áp dụng cho cả Mở Pack và Mô Phỏng).",
    )
    if st.session_state.get("grand_album_enabled", False):
        st.caption("Grand Album Mode: Khi đạt mốc 135 thẻ, kho thẻ tự reset về 0 (giữ nguyên Sao). Các thẻ tiếp theo rút được sẽ tính cho vòng Album mới.")


def inject_sidebar_toggle_style() -> None:
    st.markdown(
        """
        <style>
        section[data-testid="stSidebar"] div[data-testid="stToggle"],
        section[data-testid="stSidebar"] div[data-testid="stCheckbox"] {
            margin: 0.2rem 0 0.35rem;
        }
        section[data-testid="stSidebar"] div[data-testid="stToggle"] label,
        section[data-testid="stSidebar"] div[data-testid="stCheckbox"] label {
            align-items: center;
            gap: 1.2rem;
            min-height: 3.1rem;
            width: 100%;
        }
        section[data-testid="stSidebar"] div[data-testid="stToggle"] label p,
        section[data-testid="stSidebar"] div[data-testid="stCheckbox"] label p {
            font-size: 1.25rem;
            font-weight: 600;
            line-height: 1.2;
            text-transform: none;
        }
        section[data-testid="stSidebar"] div[data-testid="stToggle"] [role="switch"],
        section[data-testid="stSidebar"] div[data-testid="stCheckbox"] [role="switch"] {
            min-width: 3.25rem !important;
            width: 3.25rem !important;
            min-height: 1.8rem !important;
            height: 1.8rem !important;
            transform: scale(1.28);
            transform-origin: left center;
        }
        section[data-testid="stSidebar"] div[data-testid="stToggle"] [role="switch"] *,
        section[data-testid="stSidebar"] div[data-testid="stCheckbox"] [role="switch"] * {
            transition: all 120ms ease;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_pity_panel(selected_pack: str) -> None:
    st.subheader("🍀 Chỉ số Pity")
    _, pity_message = get_pity_bonus(st.session_state, selected_pack)
    st.markdown(f"**Hiệu ứng gói đang chọn ({selected_pack}):** `{pity_message}`")
    col_left, col_right = st.columns(2)
    col_left.metric("Silver/Amethyst", f"{st.session_state['silver_amethyst_pity']} tạch")
    col_right.metric("Ruby/Gold", f"{st.session_state['ruby_gold_pity']} tạch")
    st.caption("*Tạch 3 lần Silver/Amethyst (+20%). Tạch 2 lần Ruby/Gold (+33%).*")


def render_album_dashboard() -> None:
    col_left, col_right = st.columns([1.2, 5])
    with col_left:
        total_cards = total_cards_collected(st.session_state)
        completions = st.session_state.get("grand_album_completions", 0)
        is_finished = st.session_state.get("grand_album_finished", False)
        
        if is_finished:
            st.metric("🎯 Tiến độ Album", f"{total_cards} / {TOTAL_CARDS}", delta="🏆 Đã hoàn thành Grand Album")
        elif completions > 0:
            st.metric("🎯 Tiến độ Album", f"{total_cards} / {TOTAL_CARDS}", delta="🏆 Đang ở vòng Grand Album")
        else:
            st.metric("🎯 Tiến độ Album", f"{total_cards} / {TOTAL_CARDS}")
        st.markdown("<br>", unsafe_allow_html=True)
        st.metric("⭐ Sao Tích Luỹ", f"{st.session_state['stars']}")
        st.caption(f"Tổng đã mở: **{st.session_state['total_packs']}** gói")

    with col_right:
        card_cols = st.columns(len(RARITIES))
        for rarity, col in zip(RARITIES, card_cols):
            current = st.session_state["inventory"][rarity]
            maximum = MAX_CARDS[rarity]
            progress = current / maximum if maximum > 0 else 0
            with col:
                st.markdown(f"**{rarity_label(rarity)}**")
                st.progress(progress)
                st.caption(f"{current} / {maximum} thẻ")

        st.markdown("<hr style='margin: 15px 0px; opacity: 0.3'>", unsafe_allow_html=True)
        pack_cols = st.columns(len(PACK_ORDER))
        for pack, col in zip(PACK_ORDER, pack_cols):
            with col:
                st.markdown(f"**{PACK_ICONS[pack]} {pack}**")
                st.caption(f"{st.session_state['pack_counts'][pack]} gói")


def render_main_content(selected_pack: str) -> None:
    left_log, right_rate = st.columns([1.2, 1])

    with left_log:
        render_log_panel()

    with right_rate:
        render_rate_panel(selected_pack)


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
            "- 100% ra thẻ MỚI.\n"
            "- Ưu tiên lấp đầy Thẻ Vàng trước.\n"
            "- Nếu đã có đủ 18 Thẻ Vàng, lấp ngẫu nhiên các thẻ còn thiếu."
        )
        return

    card_rush_enabled = st.session_state.get("card_rush_enabled", False)
    base_size = PACKS[selected_pack].size
    effective_size = get_effective_pack_size(selected_pack, card_rush_enabled)
    rows = build_rate_rows(st.session_state, selected_pack)
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    guaranteed_tier = PACKS[selected_pack].guaranteed_tier
    guaranteed_label = f"{guaranteed_tier}-Sao" if guaranteed_tier < 6 else "Thẻ VÀNG"
    caption = f"Gói này gồm **{effective_size} thẻ**. Chắc chắn có 1 thẻ **{guaranteed_label}** trở lên."
    if card_rush_enabled and selected_pack in CARD_RUSH_PACK_SIZES:
        caption += f" Card Rush đang đổi từ {base_size} thẻ lên {effective_size} thẻ."
    st.caption(caption)
    
    st.divider()
    render_pity_panel(selected_pack)


def is_positive_log(entry: str) -> bool:
    return "✅" in entry or "🌈" in entry or "🌟" in entry


def render_analytics_tab() -> None:
    st.header("🔬 Auto-Simulation (Analytics Sandbox)")
    st.markdown("Giả lập mở gói thẻ nhiều lần để đánh giá độ khó và sự phân phối thẻ mới thu được.")
    
    if "simulation_combo" not in st.session_state:
        st.session_state["simulation_combo"] = {}
        
    with st.container(border=True):
        st.markdown("🎯 **HƯỚNG DẪN**")
        st.markdown("1. Thiết lập số lượng gói muốn thử nghiệm tại cột **📦 Mở Nhiều Pack** (Sidebar), có thể bật mode **Card Rush** hoặc **Grand Album**.")
        st.markdown("2. Nhấn nút bên dưới để chốt cấu hình Combo và bắt đầu phân tích.")
        
        col_btn, col_msg = st.columns([1, 2])
        with col_btn:
            if st.button("🔄 LOAD DATA TỪ SIDEBAR", use_container_width=True):
                fetched_settings = {}
                for pack in PACK_ORDER:
                    val = st.session_state.get(f"bulk_{pack}", 0)
                    if val > 0:
                        fetched_settings[pack] = val
                st.session_state["simulation_combo"] = fetched_settings
                st.session_state["sim_card_rush"] = st.session_state.get("card_rush_enabled", False)
                st.session_state["sim_grand_album"] = st.session_state.get("grand_album_enabled", False)
                if not fetched_settings:
                    st.error("⚠️ Bạn chưa nhập số lượng nào ở Sidebar")
        
        bulk_settings = st.session_state["simulation_combo"]
        with col_msg:
            if not bulk_settings:
                st.info("💡 Hệ thống đang chờ dữ liệu...")
            else:
                summary_text = ", ".join(f"{v} {k}" for k, v in bulk_settings.items())
                is_rush = st.session_state.get("sim_card_rush", False)
                is_grand = st.session_state.get("sim_grand_album", False)
                
                buffs = []
                if is_rush:
                    buffs.append("Card Rush")
                if is_grand:
                    buffs.append("Grand Album Mode")
                    
                if buffs:
                    summary_text += f" ({' + '.join(buffs)})"
                    
                st.success(f"**Combo Đang Phân Tích:** {summary_text}")

    if not bulk_settings:
        return
    
    with st.form("simulation_form"):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**1. Cài đặt vòng lặp**")
            num_players = st.selectbox("Số lần lặp (Iterations / Virtual Players)", [100, 500, 1000, 2000, 5000], index=2, help="Lặp lại việc mở combo thẻ trên cho N người chơi ảo.")
        
        with col2:
            st.markdown("**2. Bắt đầu mô phỏng**")
            st.caption("Khởi tạo 0 thẻ ở mỗi lần lặp, mở Combo trên và ghi nhận kết quả.")
            submit_sim = st.form_submit_button("🚀 CHẠY MÔ PHỎNG", type="primary", use_container_width=True)
            power = 1.0
            pity_multiplier = 1.0
            
    if submit_sim:
        card_rush = st.session_state.get("sim_card_rush", False)
        grand_album = st.session_state.get("sim_grand_album", False)
        with st.spinner(f"Đang phân tích {num_players} kịch bản..."):
            df = run_monte_carlo(num_players, bulk_settings, card_rush, grand_album, power, pity_multiplier)
            
        st.success("✅ Phân tích hoàn tất!")
        
        # Thống kê
        avg_cards = df["new_cards"].mean()
        max_cards = df["new_cards"].max()
        min_cards = df["new_cards"].min()
        avg_stars = df["stars_earned"].mean()
        
        st.subheader("📊 Báo cáo Chỉ số")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Thẻ Mới Trung Bình", f"{avg_cards:,.1f} thẻ")
        c2.metric("May Mắn Nhất (Max)", f"{max_cards} thẻ")
        c3.metric("Xui Xẻo Nhất (Min)", f"{min_cards} thẻ")
        c4.metric("Sao dư Trung Bình", f"{avg_stars:,.0f} ⭐")
        
        st.divider()
        st.subheader("📈Visualizations")
        
        # Phân phối Thẻ Mới (Quan trọng nhất)
        st.markdown("**1. Đa số người chơi sẽ nhận được bao nhiêu Thẻ Mới? (Histogram)**")
        chart_data_new = df["new_cards"].value_counts().reset_index()
        chart_data_new.columns = ["Số Thẻ Mới", "Số Người Chơi"]
        bar_chart_new = alt.Chart(chart_data_new).mark_bar(color="#4c78a8").encode(
            x=alt.X("Số Thẻ Mới:O", title="Số lượng Thẻ Mới nhận được", axis=alt.Axis(labelAngle=0)),
            y=alt.Y("Số Người Chơi:Q", title="Số lượng Người Chơi Ảo đạt được"),
            tooltip=[alt.Tooltip("Số Thẻ Mới:O", title="Thẻ Mới"), alt.Tooltip("Số Người Chơi:Q", title="Số Người")]
        ).properties(height=350)
        st.altair_chart(bar_chart_new, use_container_width=True)
        
        # Phân phối Sao
        st.markdown("**2. Số sao dư qua các vòng lặp**")
        chart_data_stars = df["stars_earned"].value_counts().reset_index()
        chart_data_stars.columns = ["Số Sao", "Số Người Chơi"]
        bar_chart_stars = alt.Chart(chart_data_stars).mark_bar(color="#f58518").encode(
            x=alt.X("Số Sao:Q", title="Lượng Sao thừa", bin=alt.Bin(maxbins=30)),
            y=alt.Y("sum(Số Người Chơi):Q", title="Số lượng Người Chơi Ảo đạt được"),
            tooltip=[alt.Tooltip("Số Sao:Q", bin=alt.Bin(maxbins=30), title="Khoảng Sao"), alt.Tooltip("sum(Số Người Chơi):Q", title="Số Người")]
        ).properties(height=350)
        st.altair_chart(bar_chart_stars, use_container_width=True)
        
        with st.expander("📄 Dữ liệu thô (Raw Data)"):
            st.dataframe(df)
