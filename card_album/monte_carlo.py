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
    cart = st.session_state.get("cart_packs", {})
    total_cart_packs = sum(cart.values())
    
    if total_cart_packs == 0:
        st.warning("Giỏ hàng của bạn đang trống! Hãy sang tab **LiveOps Economy** để tính toán và lưu Packs vào giỏ, hoặc tự điền ở Sidebar bên trái.")
        return
        
    st.info(f"🛒 **Giỏ Hàng hiện tại:** {', '.join([f'{v} {k}' for k, v in cart.items() if v > 0])}")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        iterations = st.number_input("Số lần chạy mô phỏng (Iterations)", min_value=10, max_value=5000, value=100, step=10)
        start_btn = st.button("🚀 BẮT ĐẦU MÔ PHỎNG", type="primary", use_container_width=True)
        
    if start_btn:
        with st.spinner(f"Đang giả lập {iterations} lần bóc {total_cart_packs} pack..."):
            results = run_monte_carlo(st.session_state, cart, iterations)
            st.session_state["mc_results"] = results
            
    if "mc_results" in st.session_state:
        res = st.session_state["mc_results"]
        render_monte_carlo_results(res, iterations, total_cart_packs)


def run_monte_carlo(base_state, cart, iterations):
    cards_collected = []
    stars_collected = []
    grand_album_count = []
    
    for _ in range(iterations):
        # Create an isolated dummy state
        sim_state = {
            "inventory": copy.deepcopy(base_state["inventory"]),
            "stars": base_state["stars"],
            "total_packs": base_state["total_packs"],
            "pack_counts": copy.deepcopy(base_state["pack_counts"]),
            "pack_pity": copy.deepcopy(base_state["pack_pity"]),
            "log": [], # We don't care about logs in MC
            "card_rush_enabled": base_state["card_rush_enabled"],
            "grand_album_enabled": base_state["grand_album_enabled"],
            "grand_album_completions": base_state.get("grand_album_completions", 0),
            "grand_album_finished": base_state.get("grand_album_finished", False),
            "new_card_formula_type": base_state["new_card_formula_type"],
            "config_packs": base_state["config_packs"],
            "new_card_power": base_state.get("new_card_power", 1.0)
        }
        
        # Run the bulk open
        open_bulk_packs(sim_state, cart)
        
        # Record results
        total_cards = sim_state["grand_album_completions"] * TOTAL_CARDS + sum(sim_state["inventory"].values())
        cards_collected.append(total_cards)
        stars_collected.append(sim_state["stars"])
        grand_album_count.append(sim_state["grand_album_completions"])
        
    return {
        "cards": cards_collected,
        "stars": stars_collected,
        "grand_albums": grand_album_count
    }


def render_monte_carlo_results(res, iterations, total_cart_packs):
    st.divider()
    st.subheader(f"📈 Kết quả sau {iterations} lần chạy")
    
    df = pd.DataFrame(res)
    
    # Metrics
    avg_cards = df["cards"].mean()
    max_cards = df["cards"].max()
    min_cards = df["cards"].min()
    
    avg_stars = df["stars"].mean()
    
    # Calculate completions
    start_completions = st.session_state.get("grand_album_completions", 0)
    # A run is considered to have completed the album if its final completions > start_completions
    # OR if it was already finished, but we'll assume we care about new completions
    completions = df[df["grand_albums"] > start_completions]
    completion_rate = len(completions) / iterations * 100
    
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Hoàn thành Album", f"{completion_rate:.1f}%")
    c2.metric("Trung bình Thẻ", f"{avg_cards:.1f}")
    c3.metric("Max Thẻ (Hên)", f"{max_cards}")
    c4.metric("Min Thẻ (Xui)", f"{min_cards}")
    c5.metric("Trung bình Sao", f"{avg_stars:.0f} ⭐")
    
    # Charts
    st.info("💡 **Lưu ý:** Để biểu đồ hiển thị chuẩn xác và không bị gãy đoạn do cơ chế Reset của Grand Album, **Số Thẻ Cuối Cùng** sẽ được cộng dồn liên tục nếu bạn vượt quá 135 thẻ. (VD: Nếu bạn full album bị reset về 0, rồi bóc thêm được 10 thẻ nữa, hệ thống sẽ ghi nhận bạn có 145 thẻ).")
    st.subheader("Phân bổ Số lượng Thẻ thu thập được")
    chart_cards = alt.Chart(df).mark_bar(opacity=0.8, color="#4CAF50").encode(
        alt.X("cards", bin=alt.Bin(maxbins=30), title="Số Thẻ Cuối Cùng"),
        alt.Y('count()', title="Số Lần Lặp (Tần suất)"),
        tooltip=['count()']
    )
    st.altair_chart(chart_cards, use_container_width=True)
    
    st.subheader("Phân bổ Số Sao dư thừa")
    chart_stars = alt.Chart(df).mark_bar(opacity=0.8, color="#FFC107").encode(
        alt.X("stars", bin=alt.Bin(maxbins=30), title="Tổng số Sao"),
        alt.Y('count()', title="Số Lần Lặp (Tần suất)"),
        tooltip=['count()']
    )
    st.altair_chart(chart_stars, use_container_width=True)
