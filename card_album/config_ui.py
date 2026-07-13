import pandas as pd
import streamlit as st
from .config_manager import export_config_to_json, import_config_from_json, load_config_to_state
from .config import PACK_ICONS

import copy

def init_draft_config():
    if "draft_config_packs" not in st.session_state:
        st.session_state["draft_config_packs"] = copy.deepcopy(st.session_state["config_packs"])
    if "draft_config_rewards" not in st.session_state:
        st.session_state["draft_config_rewards"] = copy.deepcopy(st.session_state["config_rewards"])
    if "draft_new_card_formula_type" not in st.session_state:
        st.session_state["draft_new_card_formula_type"] = st.session_state.get("new_card_formula_type", "simple")
    if "draft_new_card_power" not in st.session_state:
        st.session_state["draft_new_card_power"] = st.session_state.get("new_card_power", 1.0)

def clear_draft_config():
    keys_to_clear = [
        "draft_config_packs", "draft_config_rewards", 
        "draft_new_card_formula_type", "draft_new_card_power",
        "pack_config_editor", "reward_editor_master_pass_free",
        "reward_editor_win_streak_rewards", "reward_editor_master_pass_premium",
        "reward_editor_key_collection_rewards"
    ]
    for key in keys_to_clear:
        st.session_state.pop(key, None)

def render_config_tab():
    init_draft_config()
    st.header("⚙️ Economy Tuning")
    if st.session_state.pop("show_config_success", False):
        st.success("✅ Đã áp dụng các thay đổi cấu hình lên hệ thống!")

    st.markdown("Tab này cho phép tinh chỉnh toàn bộ hệ thống nền kinh tế, từ tỉ lệ rớt thẻ đến phần thưởng của các sự kiện.")
    
    col_apply, col1, col2, col3 = st.columns(4)
    
    with col_apply:
        applied = st.button("✅ Áp dụng Cấu hình", type="primary", use_container_width=True)
            
    with col1:
        if st.button("🔄 Khôi phục (Reset)", use_container_width=True):
            load_config_to_state(st.session_state, None)
            clear_draft_config()
            st.success("Đã khôi phục cài đặt gốc!")
            st.rerun()

    with col2:
        json_str = export_config_to_json(st.session_state)
        st.download_button(
            label="💾 Tải (Export JSON)",
            data=json_str,
            file_name="economy_config.json",
            mime="application/json",
            use_container_width=True
        )
    
    with col3:
        uploaded_file = st.file_uploader("📂 Tải lên (Import JSON)", type=["json"], label_visibility="collapsed")
        if uploaded_file is not None:
            content = uploaded_file.getvalue().decode("utf-8")
            if import_config_from_json(st.session_state, content):
                clear_draft_config()
                st.success("Tải Config thành công!")
                st.rerun()
            else:
                st.error("File Config không hợp lệ!")

    st.divider()

    with st.expander("📖 Hướng dẫn cấu hình Hệ thống & Công thức Tỉ lệ", expanded=False):
        st.markdown("""
        **1. Công thức tính cơ hội rớt Thẻ Mới:**
        Game hiện tại áp dụng công thức sau để tính tỉ lệ ra thẻ mới:
        
        `New Card Ratio = (Remaining New/Total)^(x+y) + Pity`
        - `x`: Base for all pack, default = 1
        - `y`: Base each pack (Cấu hình riêng trong từng gói thẻ giúp gói thẻ xịn dễ rớt thẻ mới hơn)
        
        **2. Giải thích Bảng Tỉ lệ Gói Thẻ (Packs Config):**
        Bạn có thể rê chuột vào tiêu đề các cột trong bảng bên dưới để xem chú thích (tooltip) chi tiết.
        
        **3. Chỉnh sửa Phần thưởng:**
        - Chỉ có thể chỉnh sửa cột **Reward** (Nội dung phần thưởng).
        - Hệ thống sẽ tự động quét từ khóa `Pack` và gắn icon 📦 để bạn dễ nhận biết đâu là mốc nhận thẻ.
        
        **4. Cơ chế Bảo hiểm (Pity System):**
        - Mỗi gói thẻ sẽ có bộ đếm bảo hiểm (Pity) chạy hoàn toàn ĐỘC LẬP với nhau.
        - **Pity Threshold**: Số lần mở gói xịt (không ra thẻ mới) liên tiếp để KÍCH HOẠT bảo hiểm. (VD: Nếu = 3, thì mở xịt đúng 3 lần sẽ được cộng % bảo hiểm).
        - **Pity Incr**: % cơ hội ra thẻ mới được cộng thêm mỗi lần xịt tính từ mốc Threshold. (Ví dụ: 0.2 = +20% cơ hội).
        """)

    # ----------------- SYSTEM CONFIG -----------------
    st.subheader("⚙️ Thông số Hệ thống")
    power = st.session_state["draft_new_card_power"]
    new_power = st.slider(
        "Hệ số Khó chung (x) theo công thức tính tỉ lệ rớt thẻ MỚI: **New Card Ratio = (Remaining New/Total)^(x+y) + Pity**", 
        min_value=0.1, max_value=5.0, value=float(power), step=0.1, 
        help="Hệ số lũy thừa x. Giá trị càng cao, khi bạn sưu tập được càng nhiều thẻ thì cơ hội ra thẻ mới càng nhỏ."
    )
    st.session_state["draft_new_card_formula_type"] = "document"
            
    st.divider()
    
    # ----------------- PACKS CONFIG -----------------
    st.subheader("🎲 Tỉ lệ rớt của các Gói Thẻ")
    st.caption("Cấu hình số thẻ trong mỗi gói, thẻ bảo hiểm, hệ số rớt (y_value) và trọng số (weights) của từng độ hiếm.")
    packs_data = []
    
    # Store mapping to retrieve pack name cleanly from iconified name
    pack_name_mapping = {}
    
    for pack_name, p in st.session_state["draft_config_packs"].items():
        icon = PACK_ICONS.get(pack_name, "")
        display_name = f"{icon} {pack_name}"
        pack_name_mapping[display_name] = pack_name
        
        row = {
            "Pack": display_name,
            "Size": p["size"],
            "Guaranteed": p["guaranteed_tier"],
            "y_value": p["y_value"],
            "Pity Threshold": p.get("pity_threshold", 0),
            "Pity Incr": p.get("pity_increment", 0.0),
        }
        for i in range(1, 7):
            col_name = f"Star_{i}" if i < 6 else "Gold"
            row[col_name] = p["weights"].get(str(i), 0)
        packs_data.append(row)
        
    df_packs = pd.DataFrame(packs_data)
    
    # Configure columns with tooltips
    col_config = {
        "Pack": st.column_config.TextColumn("Tên Gói", disabled=True),
        "Size": st.column_config.NumberColumn("Size", help="Số lượng thẻ rút ra từ gói này."),
        "Guaranteed": st.column_config.NumberColumn("Guaranteed", help="Độ hiếm tối thiểu được bảo đảm (Ví dụ: 3 là có ít nhất 1 thẻ 3-Sao)."),
        "y_value": st.column_config.NumberColumn("y_value", help="Hệ số độ khó riêng (y) của gói (Chỉ dùng cho Công thức Tài liệu). Âm = rớt thẻ dễ hơn."),
        "Pity Threshold": st.column_config.NumberColumn("Pity Threshold", help="Số lần mở gói xịt liên tiếp để kích hoạt Pity."),
        "Pity Incr": st.column_config.NumberColumn("Pity Incr", help="% cơ hội cộng thêm khi đạt ngưỡng Pity (VD: 0.2 = +20%)."),
    }
    for i in range(1, 7):
        col_name = f"Star_{i}" if i < 6 else "Gold"
        label_help = f"{i}-Sao" if i < 6 else "Thẻ VÀNG (6-Sao)"
        col_config[col_name] = st.column_config.NumberColumn(col_name, help=f"Trọng số bốc trúng độ hiếm {label_help}. Số càng to tỉ lệ càng cao.")
        
    edited_packs = st.data_editor(df_packs, num_rows="fixed", hide_index=True, use_container_width=True, column_config=col_config, key="pack_config_editor")

    st.divider()

    # ----------------- REWARDS CONFIG -----------------
    def render_reward_editor(title: str, config_key: str, key_col: str):
        st.subheader(title)
        data_dict = st.session_state["draft_config_rewards"][config_key]
        df = pd.DataFrame(list(data_dict.items()), columns=[key_col, "Reward"])
        # Add visual helper column for packs
        df["Có Pack?"] = df["Reward"].apply(lambda x: "📦" if "Pack" in str(x) else "")
        
        # Configure columns so key_col and Có Pack? are non-editable
        reward_col_config = {
            key_col: st.column_config.NumberColumn(key_col, disabled=True),
            "Có Pack?": st.column_config.TextColumn("Có Pack?", disabled=True)
        }
        
        edited_df = st.data_editor(df, num_rows="fixed", hide_index=True, use_container_width=True, column_config=reward_col_config, key=f"reward_editor_{config_key}")
        return edited_df

    c1, c2 = st.columns(2)
    with c1:
        edited_mp_free = render_reward_editor("🎁 Master Pass (Free)", "master_pass_free", "Level")
        edited_ws = render_reward_editor("🔥 Win Streak", "win_streak_rewards", "Wins")
    with c2:
        edited_mp_prem = render_reward_editor("👑 Master Pass (Premium)", "master_pass_premium", "Level")
        edited_kc = render_reward_editor("🔑 Key Collection", "key_collection_rewards", "Stage")

    if applied:
        # Apply System Config
        st.session_state["draft_new_card_power"] = new_power
        st.session_state["new_card_formula_type"] = "document"
        st.session_state["new_card_power"] = new_power
        
        # Apply Packs Config
        for idx, row in edited_packs.iterrows():
            display_name = row["Pack"]
            pack_name = pack_name_mapping.get(display_name, display_name)
            p = st.session_state["draft_config_packs"][pack_name]
            p["size"] = int(row["Size"])
            p["guaranteed_tier"] = int(row["Guaranteed"])
            p["y_value"] = float(row["y_value"])
            p["pity_threshold"] = int(row["Pity Threshold"])
            p["pity_increment"] = float(row["Pity Incr"])
            for i in range(1, 7):
                col_name = f"Star_{i}" if i < 6 else "Gold"
                p["weights"][str(i)] = int(row[col_name])
        st.session_state["config_packs"] = copy.deepcopy(st.session_state["draft_config_packs"])
        
        # Apply Rewards Config
        st.session_state["draft_config_rewards"]["master_pass_free"] = {int(row["Level"]): row["Reward"] for _, row in edited_mp_free.iterrows()}
        st.session_state["draft_config_rewards"]["win_streak_rewards"] = {int(row["Wins"]): row["Reward"] for _, row in edited_ws.iterrows()}
        st.session_state["draft_config_rewards"]["master_pass_premium"] = {int(row["Level"]): row["Reward"] for _, row in edited_mp_prem.iterrows()}
        st.session_state["draft_config_rewards"]["key_collection_rewards"] = {int(row["Stage"]): row["Reward"] for _, row in edited_kc.iterrows()}
        st.session_state["config_rewards"] = copy.deepcopy(st.session_state["draft_config_rewards"])
        
        st.toast("✅ Cấu hình đã được lưu thành công!")
        st.session_state["show_config_success"] = True
        st.rerun()

