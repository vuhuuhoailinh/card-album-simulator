import streamlit as st
import random
import pandas as pd

# ==========================================
# 0. CONFIG BẮT BUỘC ĐỂ ĐẦU TIÊN
# ==========================================
st.set_page_config(page_title="Card Album Simulator", layout="wide")

# ==========================================
# 1. CẤU HÌNH THÔNG SỐ GAME DESIGN
# ==========================================
MAX_CARDS = {1: 33, 2: 28, 3: 23, 4: 18, 5: 15, 6: 18}
STAR_VALUES = {1: 1, 2: 2, 3: 3, 4: 5, 5: 10, 6: 15}

PACKS = {
    "Bronze":   {'size': 2, 'guar_tier': 1, 'weights': {1: 35, 2: 26, 3: 20, 4: 11, 5: 7, 6: 1}},
    "Emerald":  {'size': 3, 'guar_tier': 2, 'weights': {1: 32, 2: 24, 3: 20, 4: 12, 5: 10, 6: 2}},
    "Silver":   {'size': 4, 'guar_tier': 3, 'weights': {1: 28, 2: 22, 3: 19, 4: 15, 5: 11, 6: 5}},
    "Amethyst": {'size': 5, 'guar_tier': 4, 'weights': {1: 23, 2: 21, 3: 19, 4: 17, 5: 12, 6: 7}},
    "Ruby":     {'size': 6, 'guar_tier': 4, 'weights': {1: 18, 2: 18, 3: 19, 4: 20, 5: 15, 6: 10}},
    "Gold":     {'size': 6, 'guar_tier': 6, 'weights': {1: 18, 2: 18, 3: 19, 4: 20, 5: 15, 6: 10}}
}

PACK_ORDER = ["Bronze", "Emerald", "Silver", "Amethyst", "Ruby", "Gold", "Rainbow"]
PACK_ICONS = {"Bronze": "🟫", "Emerald": "🟩", "Silver": "⬜", "Amethyst": "🟪", "Ruby": "🟥", "Gold": "🟨", "Rainbow": "🌈"}

# ==========================================
# 2. KHỞI TẠO STATE
# ==========================================
def init_state():
    if 'inventory' not in st.session_state:
        st.session_state.inventory = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}
    if 'stars' not in st.session_state:
        st.session_state.stars = 0
    if 'total_packs' not in st.session_state:
        st.session_state.total_packs = 0
    if 'pack_counts' not in st.session_state:
        st.session_state.pack_counts = {p: 0 for p in PACK_ORDER}
    if 'silver_amethyst_pity' not in st.session_state:
        st.session_state.silver_amethyst_pity = 0
    if 'ruby_gold_pity' not in st.session_state:
        st.session_state.ruby_gold_pity = 0
    if 'log' not in st.session_state:
        st.session_state.log = []
        
init_state()

# ==========================================
# 3. LOGIC XỬ LÝ GACHA & PITY
# ==========================================
def get_pity_bonus(pack_type):
    if st.session_state.total_packs < 5:
        return 1.0, "+100% (5 Gói Đầu Tiên)"
        
    if pack_type in ["Silver", "Amethyst"]:
        misses = st.session_state.silver_amethyst_pity
        if misses >= 3:
            bonus = min(1.0, (misses - 2) * 0.20)
            return bonus, f"+{int(bonus*100)}% (Tạch {misses} gói)"
            
    elif pack_type in ["Ruby", "Gold"]:
        misses = st.session_state.ruby_gold_pity
        if misses >= 2:
            bonus = min(1.0, (misses - 1) * 0.33)
            return bonus, f"+{int(bonus*100)}% (Tạch {misses} gói)"
            
    return 0.0, "0% (Bình thường)"

def roll_card(rarity, pack_type, pity_bonus_val):
    cards_owned = st.session_state.inventory[rarity]
    max_c = MAX_CARDS[rarity]
    
    if cards_owned >= max_c:
        new_chance = 0.0
    else:
        base_new = (max_c - cards_owned) / max_c
        new_chance = min(1.0, base_new + pity_bonus_val)
        
    if random.random() < new_chance:
        st.session_state.inventory[rarity] += 1
        return "NEW", rarity
    else:
        st.session_state.stars += STAR_VALUES[rarity]
        return "DUP", rarity

def open_pack(pack_type):
    st.session_state.total_packs += 1
    st.session_state.pack_counts[pack_type] += 1
    
    pity_bonus_val, pity_msg = get_pity_bonus(pack_type)
    
    if pack_type == "Rainbow":
        if st.session_state.inventory[6] < MAX_CARDS[6]:
            st.session_state.inventory[6] += 1
            st.session_state.log.insert(0, f"✅ 🌈 Rainbow Pack (Gói #{st.session_state.total_packs}): Ra Thẻ VÀNG (NEW)")
        else:
            found = False
            for r in [5,4,3,2,1]:
                if st.session_state.inventory[r] < MAX_CARDS[r]:
                    st.session_state.inventory[r] += 1
                    st.session_state.log.insert(0, f"✅ 🌈 Rainbow Pack (Gói #{st.session_state.total_packs}): Ra Thẻ {r}-Sao (NEW)")
                    found = True
                    break
            if not found:
                st.session_state.stars += 15
                st.session_state.log.insert(0, f"⚠️ 🌈 Rainbow Pack (Gói #{st.session_state.total_packs}): Đã Full Album! Đổi thành 15 Sao.")
        return

    p_data = PACKS[pack_type]
    got_new = False
    pack_results = []
    guar_weights = {k: v for k, v in p_data['weights'].items() if k >= p_data['guar_tier']}
    
    for _ in range(p_data['size'] - 1):
        r = random.choices(list(p_data['weights'].keys()), weights=list(p_data['weights'].values()))[0]
        res, final_r = roll_card(r, pack_type, pity_bonus_val)
        if res == "NEW": got_new = True
        pack_results.append((res, final_r))
        
    r_guar = random.choices(list(guar_weights.keys()), weights=list(guar_weights.values()))[0]
    res, final_r = roll_card(r_guar, pack_type, pity_bonus_val)
    if res == "NEW": got_new = True
    pack_results.append((res, final_r, "[Bảo Hiểm]"))
    
    if got_new:
        if pack_type in ["Silver", "Amethyst"]: st.session_state.silver_amethyst_pity = 0
        if pack_type in ["Ruby", "Gold"]: st.session_state.ruby_gold_pity = 0
    else:
        if pack_type in ["Silver", "Amethyst"]: st.session_state.silver_amethyst_pity += 1
        if pack_type in ["Ruby", "Gold"]: st.session_state.ruby_gold_pity += 1

    # Đã fix lỗi hiển thị 6-Sao thành Thẻ VÀNG tại đây
    res_str = ", ".join([f"{r}-Sao ({status})" if r < 6 else f"Thẻ VÀNG ({status})" for status, r, *g in pack_results])
    log_entry = f"📦 {pack_type} Pack #{st.session_state.pack_counts[pack_type]} (Buff: {pity_msg}) | Mở ra: {res_str}"
    st.session_state.log.insert(0, "✅ " + log_entry if got_new else "❌ " + log_entry)

def open_bulk_packs(bulk_settings):
    total_to_open = sum(bulk_settings.values())
    if total_to_open == 0:
        st.toast("⚠️ Vui lòng chọn ít nhất 1 pack để mở!", icon="⚠️")
        return

    st.session_state.log.insert(0, f"========== BẮT ĐẦU MỞ NHIỀU ({total_to_open} PACKS) ==========")
    for pack_type in PACK_ORDER:
        count = bulk_settings.get(pack_type, 0)
        for _ in range(count):
            open_pack(pack_type)
    
    summary_str = ", ".join([f"{v} {k}" for k, v in bulk_settings.items() if v > 0])
    st.session_state.log.insert(0, f"🌟 HOÀN THÀNH MỞ: {summary_str}")
    st.toast(f"Đã mở thành công {total_to_open} pack!", icon="🎉")

# ==========================================
# 4. GIAO DIỆN NGƯỜI DÙNG CHUNG
# ==========================================
def render_album_dashboard():
    total_cards = sum(st.session_state.inventory.values())
    col_left, col_right = st.columns([1.2, 5])

    with col_left:
        st.metric("🎯 Tiến độ Album", f"{total_cards} / 135")
        st.markdown("<br>", unsafe_allow_html=True) 
        st.metric("⭐ Sao Tích Luỹ", f"{st.session_state.stars}")
        st.caption(f"Tổng đã mở: **{st.session_state.total_packs}** gói")

    with col_right:
        card_cols = st.columns(6)
        for rarity, col in zip(range(1, 7), card_cols):
            current = st.session_state.inventory[rarity]
            maximum = MAX_CARDS[rarity]
            progress = current / maximum if maximum > 0 else 0
            with col:
                label = f"Thẻ {rarity}-Sao" if rarity < 6 else "Thẻ VÀNG"
                st.markdown(f"**{label}**")
                st.progress(progress)
                st.caption(f"{current} / {maximum} lá")
                
        st.markdown("<hr style='margin: 15px 0px; opacity: 0.3'>", unsafe_allow_html=True)
        pack_cols = st.columns(7)
        for p, col in zip(PACK_ORDER, pack_cols):
            with col:
                st.markdown(f"**{PACK_ICONS[p]} {p}**")
                st.caption(f"{st.session_state.pack_counts[p]} gói")

# ==========================================
# 5. SIDEBAR: ĐIỀU KHIỂN & MỞ BULK
# ==========================================
with st.sidebar:
    st.title("🎮 ĐIỀU KHIỂN GACHA")
    
    # --- TÍNH NĂNG 1: MỞ LẺ ---
    st.subheader("🛒 Mở Từng Gói")
    selected_pack = st.selectbox("Chọn Pack để mở/xem tỉ lệ:", PACK_ORDER, key="single_pack_select")
    
    if st.button(f"MỞ 1 GÓI {selected_pack.upper()}", type="primary", use_container_width=True):
        open_pack(selected_pack)
        st.rerun()

    st.divider()

    # --- TÍNH NĂNG 2: MỞ NHIỀU PACK CÙNG LÚC ---
    st.subheader("📦 Mở Nhiều Gói Cùng Lúc")
    with st.expander("⚙️ Cài đặt số lượng Packs", expanded=False):
        bulk_inputs = {}
        for p in PACK_ORDER:
            bulk_inputs[p] = st.number_input(f"{PACK_ICONS[p]} {p}", min_value=0, max_value=1000, value=0, step=1)
            
        if st.button("🚀 BẮT ĐẦU MỞ HÀNG LOẠT", type="primary", use_container_width=True):
            open_bulk_packs(bulk_inputs)
            st.rerun()

    st.divider()
    
    # --- CHỈ SỐ PITY ---
    st.subheader("🍀 Chỉ Số Pity (Xui xẻo)")
    pity_val, pity_msg = get_pity_bonus(selected_pack)
    st.markdown(f"**Hiệu ứng gói đang chọn ({selected_pack}):** `{pity_msg}`")
    col_p1, col_p2 = st.columns(2)
    col_p1.metric("Silver/Amethyst", f"{st.session_state.silver_amethyst_pity} tạch")
    col_p2.metric("Ruby/Gold", f"{st.session_state.ruby_gold_pity} tạch")
    st.caption("*Tạch 3 lần Silver/Amethyst (+20%). Tạch 2 lần Ruby/Gold (+33%).*")
    
    st.divider()
    if st.button("🗑️ Reset Toàn Bộ Dữ Liệu", use_container_width=True):
        st.session_state.clear()
        init_state()
        st.rerun()

# ==========================================
# 6. MAIN ÁREA: DASHBOARD & LỊCH SỬ
# ==========================================
st.title("🎲 Card Album Simulator")
render_album_dashboard()
st.divider()

left_log, right_rate = st.columns([1.2, 1])

with left_log:
    st.subheader("📝 Kết Quả Mở Gói")
    if st.session_state.log:
        latest = st.session_state.log[0]
        if "✅" in latest or "🌟" in latest:
            st.success(f"**[MỚI NHẤT]** {latest}")
        else:
            st.warning(f"**[MỚI NHẤT]** {latest}")
            
    with st.expander("📜 Xem toàn bộ lịch sử", expanded=True):
        log_container = st.container(height=400)
        for entry in st.session_state.log[1:]: 
            if "✅" in entry or "🌈" in entry or "🌟" in entry:
                log_container.success(entry)
            elif "====" in entry:
                log_container.markdown(f"**{entry}**")
            else:
                log_container.warning(entry)
        if not st.session_state.log:
            log_container.info("Chưa mở gói nào. Hãy sử dụng chức năng ở cột trái!")

with right_rate:
    st.subheader(f"🔍 Tỉ Lệ Động: Gói {selected_pack}")
    if selected_pack == "Rainbow":
        st.info("**Cơ chế Rainbow:**\n- 100% ra thẻ MỚI.\n- Ưu tiên lấp đầy Thẻ Vàng trước.\n- Nếu đã có đủ 18 Thẻ Vàng, lấp ngẫu nhiên các thẻ còn thiếu.")
    else:
        pack_data = PACKS[selected_pack]
        total_weight = sum(pack_data['weights'].values())
        table_data = []
        
        for r in range(1, 7):
            if r in pack_data['weights']:
                drop_rate = pack_data['weights'][r] / total_weight
                owned = st.session_state.inventory[r]
                max_c = MAX_CARDS[r]
                
                if owned >= max_c:
                    new_chance = 0.0
                else:
                    base_new = (max_c - owned) / max_c
                    new_chance = min(1.0, base_new + pity_val)
                    
                dup_chance = 1.0 - new_chance
                star_val = STAR_VALUES[r]
                new_str = f"{new_chance*100:.1f}%"
                if pity_val > 0 and owned < max_c:
                    new_str += f" (+{pity_val*100:.0f}%)"
                    
                table_data.append({
                    "Độ hiếm": f"{r}-Sao" if r < 6 else "VÀNG",
                    "Khả năng Rớt": f"{drop_rate*100:.1f}%",
                    "Thẻ MỚI": new_str,
                    "Thẻ TRÙNG": f"{dup_chance*100:.1f}% (+{star_val}⭐)"
                })
                
        st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)
        
        # Đã fix lỗi hiển thị 6-Sao ở phần caption thành Thẻ VÀNG
        guar_label = f"{pack_data['guar_tier']}-Sao" if pack_data['guar_tier'] < 6 else "Thẻ VÀNG"
        st.caption(f"Gói này gồm **{pack_data['size']} lá**. Chắc chắn có 1 lá **{guar_label}** trở lên.")