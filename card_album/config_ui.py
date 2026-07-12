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
    for key in ["draft_config_packs", "draft_config_rewards", "draft_new_card_formula_type", "draft_new_card_power"]:
        st.session_state.pop(key, None)

def render_config_tab():
    init_draft_config()
    st.header("⚙️ Nền kinh tế (Economy Tuning)")
    st.markdown("Tab này cho phép tinh chỉnh toàn bộ hệ thống nền kinh tế, từ tỉ lệ rớt thẻ đến phần thưởng của các sự kiện.")
    
    col_apply, col1, col2, col3 = st.columns(4)
    
    with col_apply:
        if st.button("✅ Áp dụng Cấu hình", type="primary", use_container_width=True):
            st.session_state["config_packs"] = copy.deepcopy(st.session_state["draft_config_packs"])
            st.session_state["config_rewards"] = copy.deepcopy(st.session_state["draft_config_rewards"])
            st.session_state["new_card_formula_type"] = st.session_state["draft_new_card_formula_type"]
            st.session_state["new_card_power"] = st.session_state["draft_new_card_power"]
            st.success("Đã áp dụng cấu hình lên toàn hệ thống!")
            # Note: No need to clear draft here since draft is already equal to main state.
            st.rerun()
            
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
        **1. Công thức tính cơ hội rớt Thẻ Mới (Cốt lõi của Game):**
        Game hiện tại hỗ trợ 2 loại công thức để tính tỉ lệ ra thẻ mới. Bạn có thể chọn ở mục "Thông số Hệ thống". Cả 2 đều dựa trên số thẻ bạn còn thiếu.
        
        *   **Công thức Đơn giản (Tuyến tính / Mặc định):**
            `Cơ hội = [(Thẻ tối đa - Thẻ đang có) / Thẻ tối đa] ^ x + Pity`
            - `x` chính là **Hệ số Khó thẻ mới (new_card_power)**.
            - *Ví dụ:* Nếu bạn đã sưu tập 4/5 thẻ ở độ hiếm 1-Sao. Bạn còn thiếu 1 thẻ. Tỉ lệ còn thiếu = 1/5 = 20%.
                - Nếu `x = 1.0`: Tỉ lệ ra thẻ mới = 20% ^ 1 = 20%.
                - Nếu `x = 2.0`: Tỉ lệ ra thẻ mới = 20% ^ 2 = 4%.
                - **Nhận xét:** Công thức này áp dụng chung 1 hệ số `x` cho tất cả các gói thẻ.
                
        *   **Công thức Tài liệu (Nâng cao theo Game Design):**
            `Cơ hội = [(Thẻ tối đa - Thẻ đang có) / Thẻ tối đa] ^ (x + y) + Pity`
            - `x` là **Hệ số Khó chung (new_card_power)**.
            - `y` là **Hệ số Bù trừ riêng (y_value)** của từng Gói thẻ (Pack).
            - *Ví dụ:* Vẫn là 4/5 thẻ (tỉ lệ 20%). Nếu `x = 3.0` (cấu hình chung) và bạn mở gói Silver có `y = 0.0`:
                - Tỉ lệ = 20% ^ (3 + 0) = 20% ^ 3 = 0.8%.
                - Nhưng nếu bạn mở gói Ruby có `y = -1.0` (gói VIP, dễ ra thẻ hơn):
                - Tỉ lệ = 20% ^ (3 - 1) = 20% ^ 2 = 4%.
                - **Nhận xét:** Công thức này giúp các gói thẻ VIP (như Ruby, Gold) có khả năng rớt thẻ mới cao hơn hẳn các gói thường nhờ `y_value` âm.
        
        **2. Giải thích Bảng Tỉ lệ Gói Thẻ (Packs Config):**
        Bạn có thể rê chuột vào biểu tượng ❓ trên tiêu đề các cột trong bảng bên dưới để xem chú thích (tooltip) chi tiết.
        
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
    col_sys1, col_sys2 = st.columns(2)
    
    with col_sys1:
        current_formula = st.session_state["draft_new_card_formula_type"]
        formula_options = {
            "document": "Công thức Tài liệu (Lũy thừa x+y)",
            "simple": "Công thức Đơn giản (Lũy thừa x)"
        }
        formula_keys = list(formula_options.keys())
        default_index = formula_keys.index(current_formula) if current_formula in formula_keys else 0
        
        selected_formula_display = st.selectbox(
            "Loại công thức rớt thẻ mới",
            options=list(formula_options.values()),
            index=default_index,
            help="Đổi công thức tính tỉ lệ rớt thẻ mới. Xem phần Hướng dẫn để biết sự khác biệt."
        )
        
        selected_formula = [k for k, v in formula_options.items() if v == selected_formula_display][0]
        if selected_formula != current_formula:
            st.session_state["draft_new_card_formula_type"] = selected_formula
            
    with col_sys2:
        power = st.session_state["draft_new_card_power"]
        new_power = st.number_input(
            "Hệ số Khó chung (x / new_card_power)", 
            min_value=0.1, max_value=5.0, value=power, step=0.1, 
            help="Hệ số lũy thừa x. Giá trị càng cao, khi bạn sưu tập được càng nhiều thẻ thì cơ hội ra thẻ mới càng nhỏ."
        )
        if new_power != power:
            st.session_state["draft_new_card_power"] = new_power
        
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
            row[f"Star_{i}"] = p["weights"].get(str(i), 0)
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
        col_config[f"Star_{i}"] = st.column_config.NumberColumn(f"Star_{i}", help=f"Trọng số bốc trúng độ hiếm {i}-Sao. Số càng to tỉ lệ càng cao.")
        
    edited_packs = st.data_editor(df_packs, num_rows="fixed", hide_index=True, use_container_width=True, column_config=col_config)
    
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
            p["weights"][str(i)] = int(row[f"Star_{i}"])

    st.divider()

    # ----------------- REWARDS CONFIG -----------------
    def render_reward_editor(title: str, config_key: str, key_col: str):
        st.subheader(title)
        data_dict = st.session_state["draft_config_rewards"][config_key]
        df = pd.DataFrame(list(data_dict.items()), columns=[key_col, "Reward"])
        # Add visual helper column for packs
        df["Có Pack?"] = df["Reward"].apply(lambda x: "📦" if "Pack" in str(x) else "")
        
        # Configure columns so key_col and Có Pack? are non-editable
        col_config = {
            key_col: st.column_config.NumberColumn(key_col, disabled=True),
            "Có Pack?": st.column_config.TextColumn("Có Pack?", disabled=True)
        }
        
        edited_df = st.data_editor(df, num_rows="fixed", hide_index=True, use_container_width=True, column_config=col_config)
        st.session_state["draft_config_rewards"][config_key] = {int(row[key_col]): row["Reward"] for _, row in edited_df.iterrows()}

    c1, c2 = st.columns(2)
    with c1:
        render_reward_editor("🎁 Master Pass (Free)", "master_pass_free", "Level")
        render_reward_editor("🔥 Win Streak", "win_streak_rewards", "Wins")
    with c2:
        render_reward_editor("👑 Master Pass (Premium)", "master_pass_premium", "Level")
        render_reward_editor("🔑 Key Collection", "key_collection_rewards", "Stage")

