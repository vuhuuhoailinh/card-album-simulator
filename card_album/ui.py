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
from .gacha import build_rate_rows, get_pity_bonus, open_bulk_packs, open_pack, rarity_label
from .state import ensure_album_state, reset_progress, total_cards_collected
from .liveops_simulator import simulate_liveops


def run_app() -> None:
    st.set_page_config(page_title="Card Album Simulator", layout="wide")
    ensure_album_state(st.session_state)

    selected_pack = render_sidebar()
    
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
                background-color: white !important;
                color: black !important;
                border: 1px solid black !important;
            }
            div.element-container:has(#info-button-target) + div.element-container button * {
                color: black !important;
            }
            </style>
            """, 
            unsafe_allow_html=True
        )
        if st.button("i", type="primary", help="Infomation"):
            show_logic_dialog()
    
    tab_manual, tab_auto, tab_config = st.tabs(["🎮 Mở Pack", "📈 LiveOps Economy Simulator", "⚙️ Economy Tuning"])
    
    with tab_manual:
        render_album_dashboard()
        st.divider()
        render_main_content(selected_pack)
        
    with tab_auto:
        render_analytics_tab()
        
    with tab_config:
        from .config_ui import render_config_tab
        render_config_tab()


def render_sidebar() -> str:
    with st.sidebar:
        inject_sidebar_toggle_style()
        st.title("🎮GACHA MENU")

        render_grand_album_section()
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

            if st.button("BẮT ĐẦU MỞ HÀNG LOẠT", type="primary", use_container_width=True):
                success, message = open_bulk_packs(st.session_state, bulk_inputs)
                st.toast(message, icon="🎉" if success else "⚠️")
                if success:
                    st.rerun()

        st.markdown("___________________")
        if st.button("🗑️ Reset Dữ Liệu Mở Pack", use_container_width=True):
            reset_progress(st.session_state)
            st.rerun()

    return selected_pack


def render_grand_album_section() -> None:
    st.toggle(
        "🏆 Grand Album",
        key="grand_album_enabled",
        help="Khi bật, cho phép Album tự động reset khi cày đủ 135 thẻ (áp dụng cho cả Mở Pack và Mô Phỏng).",
    )
    if st.session_state.get("grand_album_enabled", True):
        st.caption("Grand Album: Khi đạt mốc 135 thẻ, kho thẻ tự reset về 0 (giữ nguyên Sao). Các thẻ tiếp theo rút được sẽ tính cho vòng Album mới.")


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
        days = st.number_input("Số ngày chơi (Days)", min_value=1, max_value=60, value=60)
        levels_per_day = st.number_input("Số Level qua mỗi ngày", min_value=1, max_value=100, value=5)
        
        st.subheader("🎯 Bật/Tắt LiveOps")
        toggles = {}
        toggles["win_streak"] = st.toggle(
            "🔥 Win Streak (Mặc định tỉ lệ thắng 100%)", 
            value=True,
            help="Nhận phần thưởng khi đạt các chuỗi thắng liên tiếp (Assume 1 lần/mùa)."
        )
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
            res = simulate_liveops(days, levels_per_day, toggles, iap_selections, st.session_state["config_rewards"])
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
            
            st.divider()
            st.subheader("🔎 Chi tiết Nguồn nhận & Phần thưởng khác")
            
            with st.expander("⚔️ Thắng Level Hard/Super Hard (Core Gameplay)"):
                for l in res["logs"]["core"]: st.markdown(f"- {l}")
                
            if toggles["win_streak"]:
                with st.expander("🔥 Win Streak"):
                    for l in res["logs"]["win_streak"]: st.markdown(f"- {l}")
                    
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
                
            st.divider()
            st.subheader("🎲 Mở thử đống Pack này!")
            if st.button("Mở hàng loạt (Feed into Gacha)"):
                bulk_inputs = {k: v for k, v in total.items() if v > 0}
                success, message = open_bulk_packs(st.session_state, bulk_inputs)
                st.toast(message, icon="🎉" if success else "⚠️")
                if success:
                    st.rerun()

@st.dialog("📖 TỔNG QUAN LOGIC HỆ THỐNG", width="large")
def show_logic_dialog():
    st.markdown('''
### 1. Cơ Chế Gacha Cơ Bản & Pity (Bảo hiểm)
- **Tỉ lệ rớt (Drop Rates):** Mỗi gói thẻ có số lượng thẻ và tỉ lệ rớt các độ hiếm khác nhau. Tỉ lệ này tự động trượt theo số lượng thẻ bạn còn thiếu (càng gần full album, tỉ lệ rớt thẻ Mới càng thấp). Bạn có thể xem và chỉnh sửa Tỉ Lệ Động ở tab `⚙️ Economy Tuning`.
- **Thẻ Bảo Hiểm:** Mỗi gói đều cam kết rớt ít nhất 1 thẻ từ 1 độ hiếm cụ thể trở lên (Ví dụ gói Emerald chắc chắn có ít nhất 1 thẻ 2-Sao).
- **Cơ Chế Pity (Đếm Tạch):** 
  - Hoạt động **độc lập** cho TỪNG LOẠI GÓI THẺ. (Tạch Silver không cộng dồn cho Amethyst).
  - Mỗi khi mở một gói và không ra bất kỳ thẻ **NEW** nào, số lần "Tạch" của gói đó tăng lên 1.
  - Khi tạch đến ngưỡng quy định, gói đó sẽ được **buff thêm % Tỉ lệ ra Thẻ Mới** ở lần mở sau. (Vd: Gói Silver tạch 3 lần sẽ buff +20%).
- **Ngắt Pity Giữa Chừng (Mid-Pack Reset):** Tuy % Pity được buff cho *toàn bộ* các thẻ trong gói, nhưng ngay khoảnh khắc thẻ đầu tiên nổ ra chữ **NEW**, lượng % buff này sẽ lập tức bốc hơi (về 0%) để các thẻ còn lại không bị lạm phát phi lý.

### 2. Rainbow Pack & 5 Gói Tân Thủ
- **Tân Thủ:** 5 gói thẻ đầu tiên bạn nhận được trong Mùa (từ bất kỳ nguồn nào) sẽ được hệ thống buff **100% rớt toàn Thẻ Mới**.
- **Rainbow Pack:** Gói thẻ đặc quyền có 6 thẻ, trong đó chắc chắn 100% rớt 1 Thẻ Mới. Thuật toán sẽ luôn ưu tiên rớt **Thẻ Vàng (6-Sao)** trước. Nếu thẻ Vàng đã đầy, hệ thống sẽ rớt ngẫu nhiên các độ hiếm còn thiếu khác.

### 3. Grand Album & Thẻ Trùng (Duplicated)
- **Hoàn thành Album:** Sau khi sưu tập đủ 135 thẻ, bạn sẽ hoàn thành vòng Album và được thăng cấp sang "Grand Album".
- **Luật Reset:** Khi thăng cấp, kho thẻ sẽ **bị Reset về 0**, nhưng lượng **Sao (Stars)** tích lũy được giữ nguyên vẹn.
- **Thẻ Trùng:** Mọi thẻ trùng lặp khi quay ra sẽ tự động phân rã thành **Sao**. Thẻ càng hiếm, số Sao thu được càng cao (Từ 1 Sao lên tới 15 Sao).

### 4. Hệ Sinh Thái LiveOps (Sự kiện & Nền kinh tế)
Trong tab `📈 LiveOps Simulator`, bạn có thể giả lập hành trình cày cuốc theo ngày thông qua các hệ thống sau:
- **Core Gameplay (Vượt Ải):** Thắng màn Hard được thưởng gói Bronze, thắng Super Hard thưởng gói Emerald.
- **Win Streak:** Giữ chuỗi thắng liên tiếp để càn quét các phần thưởng dọc đường (Gói Bronze đến tận Ruby).
- **Master Pass (Battle Pass):** Thu thập token từ các màn chơi. Nhánh Premium (trả phí) sẽ cung cấp số lượng Pack khổng lồ.
- **Key Collection:** Cày chìa khóa theo tiến độ để mở Rương chặng.
- **Chain Offer & IAP:** Các sự kiện bán gói ưu đãi theo chuỗi (nhận phần đầu miễn phí, các phần sau dùng tiền thật để tối đa hoá thẻ cao cấp).
- **⚡ Card Rush:** Sự kiện đặc biệt xuất hiện vào các ngày cuối tuần hoặc thứ 4. Khi kích hoạt, các gói thẻ thường (Bronze, Emerald, Silver) sẽ thức tỉnh thành dạng **Plus (+)**, nhồi thêm số lượng thẻ rớt ra nhưng vẫn giữ nguyên tỉ lệ hiếm, giúp bạn sưu tập thần tốc!
    ''')
