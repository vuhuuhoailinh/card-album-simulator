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

def render_analytics_tab() -> None:
    st.header("📈 LiveOps Economy Simulator")
    st.markdown("Giả lập số lượng gói thẻ nhận được từ các sự kiện LiveOps dựa trên số ngày chơi và nỗ lực cày cuốc.")
    
    col1, col2 = st.columns([1, 1.5])
    
    with col1:
        st.subheader("🗓️ Thông số Cày cuốc")
        days = st.number_input("Số Ngày (Mùa giải)", min_value=1, max_value=365, value=60)
        
        st.markdown("**Số Level chơi mỗi ngày**")
        input_mode = st.radio("Chế độ nhập liệu:", ["Cố định (Fixed)", "Khoảng ngẫu nhiên (Range)"], horizontal=True, label_visibility="collapsed")
        
        if input_mode == "Khoảng ngẫu nhiên (Range)":
            levels_per_weekday = st.slider("Trong tuần (T2-T5)", min_value=0, max_value=100, value=(5, 7))
            levels_per_weekend = st.slider("Cuối tuần (T6-CN)", min_value=0, max_value=100, value=(12, 15))
        else:
            col_lvl1, col_lvl2 = st.columns(2)
            with col_lvl1:
                levels_per_weekday_val = st.number_input("Trong tuần (T2-T5)", min_value=0, max_value=100, value=5)
            with col_lvl2:
                levels_per_weekend_val = st.number_input("Cuối tuần (T6-CN)", min_value=0, max_value=100, value=15)
            levels_per_weekday = (levels_per_weekday_val, levels_per_weekday_val)
            levels_per_weekend = (levels_per_weekend_val, levels_per_weekend_val)
        
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
                        
                for tier in range(1, 6):
                    key = f"bulk_chest_{tier}"
                    st.session_state[key] = 0
                if chests_earned:
                    for tier, count in chests_earned.items():
                        key = f"bulk_chest_{tier}"
                        st.session_state[key] = count

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


