import streamlit as st
import pandas as pd
import altair as alt
import copy

from .config import PACK_ORDER, MAX_CARDS, TOTAL_CARDS
from .gacha import open_bulk_packs
from .state import fresh_inventory, fresh_pack_counts

def render_monte_carlo_tab():
    st.header("📊 Monte Carlo Simulator")
    st.markdown("Chạy mô phỏng mở **Giỏ Hàng (Cart)** hàng ngàn lần để tính xác suất hoàn thành Album và sự phân bổ của Thẻ/Sao dư thừa.")
    
    # Check if cart is empty
    cart_packs = st.session_state.get("cart_packs", {})
    cart_chests = {
        1: st.session_state.get("bulk_chest_1", 0),
        2: st.session_state.get("bulk_chest_2", 0),
        3: st.session_state.get("bulk_chest_3", 0)
    }
    
    total_cart_packs = sum(cart_packs.values())
    total_cart_chests = sum(cart_chests.values())
    
    if total_cart_packs == 0 and total_cart_chests == 0:
        st.warning("Giỏ hàng của bạn đang trống! Hãy sang tab **LiveOps Economy**, **Mở Gói (Gacha)**, hoặc **Chest Drop** để thêm thẻ/rương vào giỏ.")
        return
        
    cart_pack_str = ', '.join([f'{v} {k}' for k, v in cart_packs.items() if v > 0])
    cart_chest_str = ', '.join([f'{v} Rương {k}-Sao' for k, v in cart_chests.items() if v > 0])
    
    if cart_pack_str and cart_chest_str:
        st.info(f"**Giỏ Hàng Pack:** {cart_pack_str}\n | 🛒 **Giỏ Hàng Chest:** {cart_chest_str}", icon="🛒")
    elif cart_pack_str:
        st.info(f"**Giỏ Hàng Pack:** {cart_pack_str}", icon="🛒")
    else:
        st.info(f"**Giỏ Hàng Chest:** {cart_chest_str}", icon="🛒")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        iterations = st.number_input("Số lần chạy mô phỏng (Iterations)", min_value=10, max_value=5000, value=100, step=10)
        simulate_from_scratch = st.checkbox("🔄 Bắt đầu từ Kho Thẻ Trống", value=True, help="Nếu bật, mỗi lần chạy sẽ bắt đầu với 0 thẻ và 0 sao (Mô phỏng từ đầu game). Nếu tắt, sẽ bốc tiếp trên số thẻ bạn đang có hiện tại.")
        auto_chest = st.checkbox("🔄 Tự động dùng sao dư để đổi Star Chest", value=True, help="Hệ thống sẽ tự động mua rương xịn nhất có thể (Vàng -> Bạc -> Đồng) cho đến khi không đủ sao (dưới 100 sao).")
        start_btn = st.button("🚀 BẮT ĐẦU MÔ PHỎNG", type="primary", use_container_width=True)
        
    if start_btn:
        with st.spinner(f"Đang giả lập {iterations} lần bóc..."):
            results = run_monte_carlo(st.session_state, cart_packs, cart_chests, iterations, simulate_from_scratch, auto_chest)
            st.session_state["mc_results"] = results
            
    if "mc_results" in st.session_state:
        res = st.session_state["mc_results"]
        render_monte_carlo_results(res, iterations, total_cart_packs, total_cart_chests, auto_chest)


def run_monte_carlo(base_state, cart_packs, cart_chests, iterations, simulate_from_scratch=True, auto_chest=False):
    cards_collected = []
    stars_collected = []
    grand_album_count = []
    total_dups = []
    total_stars_earned = []
    
    for _ in range(iterations):
        # Create an isolated dummy state
        sim_state = {
            "inventory": fresh_inventory() if simulate_from_scratch else copy.deepcopy(base_state["inventory"]),
            "stars": 0 if simulate_from_scratch else base_state["stars"],
            "total_packs": 0 if simulate_from_scratch else base_state["total_packs"],
            "pack_counts": fresh_pack_counts() if simulate_from_scratch else copy.deepcopy(base_state["pack_counts"]),
            "pack_pity": fresh_pack_counts() if simulate_from_scratch else copy.deepcopy(base_state["pack_pity"]),
            "log": [], # We don't care about logs in MC
            "card_rush_enabled": base_state["card_rush_enabled"],
            "grand_album_enabled": base_state["grand_album_enabled"],
            "grand_album_completions": 0 if simulate_from_scratch else base_state.get("grand_album_completions", 0),
            "grand_album_finished": False if simulate_from_scratch else base_state.get("grand_album_finished", False),
            "new_card_formula_type": base_state["new_card_formula_type"],
            "config_packs": base_state["config_packs"],
            "new_card_power": base_state.get("new_card_power", 1.0),
            "pity_multiplier": base_state.get("pity_multiplier", 1.0),
            "owned_cards": set() if simulate_from_scratch else copy.deepcopy(base_state.get("owned_cards", set())),
            "total_cards_drawn": 0 if simulate_from_scratch else base_state.get("total_cards_drawn", 0),
            "new_cards_drawn": 0 if simulate_from_scratch else base_state.get("new_cards_drawn", 0),
            "dup_cards_drawn": 0 if simulate_from_scratch else base_state.get("dup_cards_drawn", 0),
            "new_cards_by_rarity": {r: 0 for r in range(1, 7)} if simulate_from_scratch else copy.deepcopy(base_state.get("new_cards_by_rarity", {r: 0 for r in range(1, 7)})),
            "dup_cards_by_rarity": {r: 0 for r in range(1, 7)} if simulate_from_scratch else copy.deepcopy(base_state.get("dup_cards_by_rarity", {r: 0 for r in range(1, 7)})),
            "pack_stars_gained": 0 if simulate_from_scratch else base_state.get("pack_stars_gained", 0),
            "cd_total_cards_drawn": 0 if simulate_from_scratch else base_state.get("cd_total_cards_drawn", 0),
            "cd_new_cards_drawn": 0 if simulate_from_scratch else base_state.get("cd_new_cards_drawn", 0),
            "cd_dup_cards_drawn": 0 if simulate_from_scratch else base_state.get("cd_dup_cards_drawn", 0),
            "cd_stars_gained": 0 if simulate_from_scratch else base_state.get("cd_stars_gained", 0),
            "chest_drop_counts": {r: 0 for r in range(1, 6)} if simulate_from_scratch else copy.deepcopy(base_state.get("chest_drop_counts", {r: 0 for r in range(1, 6)})),
            "config_chest_drop_tiers": base_state.get("config_chest_drop_tiers", {}),
            "config_chest_drop_x": base_state.get("config_chest_drop_x", 2.0),
            "cd_new_cards_by_rarity": {r: 0 for r in range(1, 7)} if simulate_from_scratch else copy.deepcopy(base_state.get("cd_new_cards_by_rarity", {r: 0 for r in range(1, 7)})),
            "cd_dup_cards_by_rarity": {r: 0 for r in range(1, 7)} if simulate_from_scratch else copy.deepcopy(base_state.get("cd_dup_cards_by_rarity", {r: 0 for r in range(1, 7)})),
        }
        
        # Run the bulk open packs (without auto_chest yet)
        open_bulk_packs(sim_state, cart_packs, auto_chest=False)
        
        # Run the bulk open chests
        from .gacha import process_chest_drop_hit
        for start_tier, count in cart_chests.items():
            for _ in range(count):
                current_t = start_tier
                drawn_in_batch = set()
                for _ in range(5):
                    res = process_chest_drop_hit(sim_state, start_tier, current_t, drawn_in_batch)
                    current_t = res["next_tier"]
                    
        # NOW run auto chest with combined stars
        if auto_chest:
            from .gacha import run_auto_chests
            run_auto_chests(sim_state)
            
        # Record results
        total_cards = sim_state["grand_album_completions"] * TOTAL_CARDS + sum(sim_state["inventory"].values())
        cards_collected.append(total_cards)
        stars_collected.append(sim_state["stars"])
        grand_album_count.append(sim_state["grand_album_completions"])
        total_dups.append(sim_state.get("dup_cards_drawn", 0) + sim_state.get("cd_dup_cards_drawn", 0))
        total_stars_earned.append(sim_state.get("pack_stars_gained", 0) + sim_state.get("cd_stars_gained", 0))
        
    return {
        "cards": cards_collected,
        "stars": stars_collected,
        "grand_albums": grand_album_count,
        "total_dups": total_dups,
        "total_stars_earned": total_stars_earned
    }


def render_monte_carlo_results(res, iterations, total_cart_packs, total_cart_chests, auto_chest):
    st.divider()
    st.subheader(f"📈 Kết quả sau {iterations} lần chạy")
    
    df = pd.DataFrame(res)
    
    # Calculate completions
    start_completions = 0 if st.session_state.get("simulate_from_scratch", True) else st.session_state.get("grand_album_completions", 0)
    start_inventory = 0 if st.session_state.get("simulate_from_scratch", True) else sum(st.session_state["inventory"].values())
    start_total_cards = start_completions * TOTAL_CARDS + start_inventory
    start_stars = 0 if st.session_state.get("simulate_from_scratch", True) else st.session_state.get("stars", 0)
    
    # Metrics (Deltas)
    avg_cards_gained = df["cards"].mean() - start_total_cards
    max_cards_gained = df["cards"].max() - start_total_cards
    min_cards_gained = df["cards"].min() - start_total_cards
    
    completions = df[df["grand_albums"] > start_completions]
    completion_rate = len(completions) / iterations * 100
    
    avg_dups = df.get("total_dups", pd.Series([0])).mean()
    
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Hoàn thành Album", f"{completion_rate:.1f}%")
    c2.metric("Thẻ Mới Thu Thập", f"{avg_cards_gained:.1f}")
    c3.metric("Thẻ Trùng (Dups)", f"{avg_dups:.1f}")
    c4.metric("Max Thẻ Mới", f"{max_cards_gained}")
    c5.metric("Min Thẻ Mới", f"{min_cards_gained}")
    
    st.write("")
    c6, c7, c8, c9, c10 = st.columns(5)
    
    if auto_chest:
        avg_stars = df["stars"].mean()
        c6.metric("Trung bình Sao Dư Thừa", f"{avg_stars:.0f} ⭐")
    else:
        avg_stars_gained = df["stars"].mean() - start_stars
        c6.metric("Trung bình Sao Nhận Được", f"{avg_stars_gained:.0f} ⭐")
        
    c7.empty()
    c8.empty()
    c9.empty()
    c10.empty()
    
    # Charts
    st.info("💡 **Lưu ý:** Để biểu đồ hiển thị chuẩn xác và không bị gãy đoạn do cơ chế Reset của Grand Album, **Số Thẻ Cuối Cùng** sẽ được cộng dồn liên tục nếu bạn vượt quá 135 thẻ. (VD: Nếu bạn full album bị reset về 0, rồi bóc thêm được 10 thẻ nữa, hệ thống sẽ ghi nhận bạn có 145 thẻ).")
    
    def bin_data(series, num_bins=20):
        min_val = int(series.min())
        max_val = int(series.max())
        if max_val == min_val:
            return pd.Series([str(min_val)] * len(series), index=series.index)
            
        step = max(1, (max_val - min_val) // num_bins + 1)
        bins = list(range(min_val, max_val + step + 1, step))
        labels = []
        for i in range(len(bins)-1):
            start = bins[i]
            end = bins[i+1] - 1
            if start == end:
                labels.append(str(start))
            else:
                labels.append(f"{start} - {end}")
        return pd.cut(series, bins=bins, right=False, labels=labels, include_lowest=True)

    df["cards_group"] = bin_data(df["cards"], 20)
    df["stars_group"] = bin_data(df["stars"], 20)
    
    cards_summary = df.groupby("cards_group", observed=True).size().reset_index(name="count")
    stars_summary = df.groupby("stars_group", observed=True).size().reset_index(name="count")

    st.subheader("Phân bổ Số lượng Thẻ thu thập được")
    chart_cards = alt.Chart(cards_summary).mark_bar(opacity=0.8, color="#4CAF50").encode(
        alt.X("cards_group:O", title="Số Thẻ Cuối Cùng", axis=alt.Axis(labelAngle=-45), sort=cards_summary["cards_group"].tolist()),
        alt.Y('count:Q', title="Số Lần Lặp (Tần suất)"),
        tooltip=[alt.Tooltip('cards_group:O', title='Số Thẻ'), alt.Tooltip('count:Q', title='Số Lần Lặp')]
    )
    st.altair_chart(chart_cards, use_container_width=True)
    
    st.subheader("Phân bổ Số Sao dư thừa")
    chart_stars = alt.Chart(stars_summary).mark_bar(opacity=0.8, color="#FFC107").encode(
        alt.X("stars_group:O", title="Tổng số Sao", axis=alt.Axis(labelAngle=-45), sort=stars_summary["stars_group"].tolist()),
        alt.Y('count:Q', title="Số Lần Lặp (Tần suất)"),
        tooltip=[alt.Tooltip('stars_group:O', title='Tổng số Sao'), alt.Tooltip('count:Q', title='Số Lần Lặp')]
    )
    st.altair_chart(chart_stars, use_container_width=True)
