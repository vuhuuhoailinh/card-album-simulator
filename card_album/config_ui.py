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
        st.session_state["draft_new_card_power"] = st.session_state.get("new_card_power", 3.0)
    if "draft_chest_drop_x" not in st.session_state:
        st.session_state["draft_chest_drop_x"] = st.session_state.get("config_chest_drop_x", 2.0)
    if "draft_config_chest_drop_tiers" not in st.session_state:
        st.session_state["draft_config_chest_drop_tiers"] = copy.deepcopy(st.session_state.get("config_chest_drop_tiers", {}))
    if "draft_config_chest_upgrade_matrix" not in st.session_state:
        st.session_state["draft_config_chest_upgrade_matrix"] = copy.deepcopy(st.session_state.get("config_chest_upgrade_matrix", {}))

def clear_draft_config():
    keys_to_clear = [
        "draft_config_packs", "draft_config_rewards", 
        "draft_new_card_formula_type", "draft_new_card_power",
        "draft_chest_drop_x", "draft_config_chest_drop_tiers", "draft_config_chest_upgrade_matrix",
        "draft_config_packs", "draft_config_rewards",
        "reward_editor_master_pass_free", "reward_editor_master_pass_premium", "reward_editor_win_streak_rewards",
        "reward_editor_key_collection_rewards", "chest_drop_tiers_editor", "chest_upgrade_matrix_editor"
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
            if st.session_state.get("last_uploaded_json") != content:
                st.session_state["last_uploaded_json"] = content
                if import_config_from_json(st.session_state, content):
                    clear_draft_config()
                    st.toast("✅ Tải Config thành công!")
                    st.rerun()
                else:
                    st.error("File Config không hợp lệ!")

    st.divider()

    with st.expander("📖 Hướng dẫn cấu hình Hệ thống & Công thức Tỉ lệ", expanded=False):
        st.markdown("""
        **1. Công thức tính cơ hội rớt Thẻ Mới:**
        Game hiện tại áp dụng công thức sau để tính tỉ lệ ra thẻ mới:
        
        `New Card Ratio = (Remaining New/Total)^(x+y) + Pity`
        - `x`: Base for all pack, default = 3
        - `y`: Base each pack (Cấu hình riêng trong từng gói thẻ giúp gói thẻ xịn dễ rớt thẻ mới hơn)
        
        **2. Giải thích Bảng Tỉ lệ Gói Thẻ (Packs Config):**
        - Bạn hoàn toàn có thể **chỉnh sửa tỉ lệ rớt thẻ** của từng Gói Thẻ ngay trong bảng bên dưới.
        - Tỉ lệ rớt được hệ thống tính toán dựa trên **Trọng số (Weights)** thay vì % tuyệt đối. (Bạn có thể rê chuột vào tiêu đề cột để xem chú thích).
        - **Quy tắc tính:** Cơ hội rớt của một độ hiếm = (Trọng số của độ hiếm đó) / (Tổng trọng số của tất cả các độ hiếm).
        - **Ví dụ rõ ràng:**
          > Nếu Gói Bronze được cấu hình Trọng số là: 1-Sao: `35`, 2-Sao: `26`, 3-Sao: `20`, 4-Sao: `11`, 5-Sao: `7`, Gold: `1`.
          > Khi đó, Tổng trọng số = 35 + 26 + 20 + 11 + 7 + 1 = 100.
          > 👉 Tỉ lệ rớt thẻ 1-Sao sẽ là `35 / 100 = 35%`. Tỉ lệ thẻ Gold là `1 / 100 = 1%`.
          > Nếu bạn sửa số thẻ Gold từ `1` thành `100`, Tổng trọng số sẽ tăng lên thành 199. Lúc này tỉ lệ rớt thẻ Gold cực cao, chiếm `100 / 199 ≈ 50%`!
        
        **3. Bảng Phần thưởng (Rewards):**
        - Bảng phần thưởng bao gồm các mốc thưởng trong Master Pass, Win Streak, và Key Collection (Chỉ đọc).
        - Hệ thống sẽ tự động quét từ khóa `Pack` và gắn icon 📦 để bạn dễ nhận biết đâu là mốc nhận thẻ.
        
        **4. Cơ chế Bảo hiểm (Pity System):**
        - Mỗi gói thẻ sẽ có bộ đếm bảo hiểm (Pity) chạy hoàn toàn ĐỘC LẬP với nhau.
        - Mỗi khi bạn mở một gói thẻ và tạch (không ra thẻ mới), bộ đếm của loại gói đó sẽ tăng lên 1.
        - Khi tạch đến ngưỡng `Pity Threshold` (vd: 3 lần), hệ thống sẽ buff thêm `Pity Incr` (vd: +20%) vào Tỉ lệ ra thẻ mới ở lần mở gói tiếp theo. Càng tạch nhiều, buff càng to (Tối đa +100%).
        
        **5. Cơ chế Tối ưu Bộ Sưu Tập (SS2):**
        Khi bật tính năng **SS2 Optimize Collection**, game sẽ kích hoạt 2 cơ chế:
        - **First Pack Luck**: Lần ĐẦU TIÊN mở bất kỳ Gói hoặc Rương ở các cấp, chắc chắn 100% rớt Thẻ Mới.
        - **Set Completion Pity**: Bàn tay vô hình nhét thẻ bạn thiếu vào set gần hoàn thành nhất. 
          *Xác suất = (Độ mót của Album) × (Độ rẻ của Thẻ)*.
          > **Độ mót (Pity Set)**: `S.Base + (S.Max - S.Base) * (1 - Số Set Xong / Tổng Set)`. 
          > Càng xong ít Set, xác suất nhét bài càng cao (Max bằng S.Max).
          > **Độ rẻ (Pity Rarity)**: `C.Base + (C.Max - C.Base) * (5 - Rarity) / 4`.
          > Thẻ càng rẻ (ít Sao) thì xác suất nhét vào set càng cao (Max bằng C.Max đối với thẻ 1-sao).
        """)

    # ----------------- SYSTEM CONFIG -----------------
    st.subheader("⚙️ Công Thức Rớt Thẻ Mới (New Card Ratio)")
    
    st.markdown("### 1. Gacha Cơ Bản (Mở Gói)")
    power = st.session_state["draft_new_card_power"]
    if "ui_new_power" not in st.session_state:
        st.session_state["ui_new_power"] = float(power)
    st.markdown("Hệ số Khó chung (x) theo công thức: **New Card Ratio = (Remaining New/Total)^(x+y) + Pity**", help="Hệ số lũy thừa x. Giá trị càng cao, khi bạn sưu tập được càng nhiều thẻ thì cơ hội ra thẻ mới càng nhỏ.")
    c1, _ = st.columns([1, 4])
    with c1:
        st.number_input("power_input", step=0.1, label_visibility="collapsed", key="ui_new_power")
    st.session_state["draft_new_card_formula_type"] = "document"
    st.caption("Lưu ý: Hệ số y sẽ phụ thuộc vào từng loại Pack (Cấu hình ở bảng bên dưới).")
    
    st.write("")
    st.markdown("### 2. Đập Rương (Chest Drop)")
    
    chest_x = st.session_state["draft_chest_drop_x"]
    if "ui_chest_x" not in st.session_state:
        st.session_state["ui_chest_x"] = float(chest_x)
    st.markdown("Hệ số Khó chung của Đập Rương (x): **New Card Ratio = (Remaining New/Total)^(x+y)**", help="Hệ số x cho Đập Rương. Hệ số y sẽ phụ thuộc trực tiếp vào độ hiếm của thẻ (1-Sao y=1.0, 2-Sao y=0.5, 3-Sao y=0.0, 4-Sao y=-0.5, 5-Sao y=-1.0, 6-Sao y=-1.5).")
    c2, _ = st.columns([1, 4])
    with c2:
        st.number_input("chest_power_input", step=0.1, label_visibility="collapsed", key="ui_chest_x")
    
    st.markdown("**Bảng Cấu Hình Tỉ Lệ Đập Rương (Chest Drop Tiers):**")
    st.caption("Cấu hình tỉ lệ thăng cấp, hệ số y_value và trọng số rớt thẻ (weights) cho từng cấp rương.")
    
    chest_tiers_data = []
    draft_tiers = st.session_state["draft_config_chest_drop_tiers"]
    
    for tier in range(1, 6):
        tier_str = str(tier)
        t_cfg = draft_tiers[tier_str]
        row = {
            "Cấp Rương": t_cfg["name"],
            "y_value": t_cfg["y_value"],
        }
        for i in range(1, 7):
            col_name = f"Star_{i}" if i < 6 else "Gold"
            row[col_name] = t_cfg["weights"].get(str(i), 0)
        chest_tiers_data.append(row)
        
    df_chest_tiers = pd.DataFrame(chest_tiers_data)
    
    chest_col_config = {
        "Cấp Rương": st.column_config.TextColumn("Cấp Rương", disabled=True),
        "y_value": st.column_config.NumberColumn("y_value", help="Hệ số độ khó (y) khi đập rương này."),
    }
    for i in range(1, 7):
        col_name = f"Star_{i}" if i < 6 else "Gold"
        label_help = f"{i}-Sao" if i < 6 else "Thẻ VÀNG (6-Sao)"
        chest_col_config[col_name] = st.column_config.NumberColumn(col_name, help=f"Trọng số bốc trúng độ hiếm {label_help}. Số càng to tỉ lệ càng cao.")
        
    edited_chest_tiers = st.data_editor(
        df_chest_tiers,
        hide_index=True,
        use_container_width=True,
        key="chest_drop_tiers_editor",
        column_config=chest_col_config
    )
    
    st.markdown("**Bảng Tỉ Lệ Thăng Cấp Rương:**")
    st.caption("Cấu hình tỉ lệ thăng cấp phụ thuộc vào rương khởi đầu. Dòng là rương khởi đầu, Cột là rương hiện tại.")
    
    matrix_data = []
    draft_matrix = st.session_state["draft_config_chest_upgrade_matrix"]
    for stier in range(1, 6):
        row = {"Rương Khởi Đầu": f"{stier}-Sao"}
        for ctier in range(1, 5):
            row[f"Lên {ctier+1}-Sao"] = float(draft_matrix[str(stier)].get(str(ctier), 0.0))
        matrix_data.append(row)
        
    df_matrix = pd.DataFrame(matrix_data)
    matrix_col_config = {"Rương Khởi Đầu": st.column_config.TextColumn("Rương Khởi Đầu", disabled=True)}
    for ctier in range(1, 5):
        col_name = f"Lên {ctier+1}-Sao"
        matrix_col_config[col_name] = st.column_config.NumberColumn(col_name, min_value=0.0, max_value=1.0, step=0.01)

    edited_matrix = st.data_editor(
        df_matrix,
        hide_index=True,
        use_container_width=True,
        key="chest_upgrade_matrix_editor",
        column_config=matrix_col_config
    )

    st.divider()
    
    st.write("")
    st.markdown("### 3. Tối ưu Bộ Sưu Tập (SS2 Optimize Collection)")
    st.caption("Cấu hình tỉ lệ rớt bù (Pity) khi mở thẻ mới, giúp người chơi dễ dàng hoàn thành Set đang dở.")
    
    if "ui_ss2_s_base" not in st.session_state:
        st.session_state["ui_ss2_s_base"] = float(st.session_state.get("config_ss2_s_base", 0.1))
        st.session_state["ui_ss2_s_max"] = float(st.session_state.get("config_ss2_s_max", 0.5))
        st.session_state["ui_ss2_c_base"] = float(st.session_state.get("config_ss2_c_base", 0.3))
        st.session_state["ui_ss2_c_max"] = float(st.session_state.get("config_ss2_c_max", 1.0))
        
    cc1, cc2, cc3, cc4 = st.columns(4)
    with cc1:
        st.number_input("S.Base (Độ mót Min)", step=0.01, key="ui_ss2_s_base", help="Hệ số bù thấp nhất khi đã xong nhiều Set")
    with cc2:
        st.number_input("S.Max (Độ mót Max)", step=0.01, key="ui_ss2_s_max", help="Hệ số bù cao nhất khi chưa xong Set nào")
    with cc3:
        st.number_input("C.Base (Độ rẻ Min)", step=0.01, key="ui_ss2_c_base", help="Hệ số buff đối với Thẻ khó ra (Thẻ 5-Sao)")
    with cc4:
        st.number_input("C.Max (Độ rẻ Max)", step=0.01, key="ui_ss2_c_max", help="Hệ số buff đối với Thẻ siêu dễ (Thẻ 1-Sao)")

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
    def render_reward_viewer(title: str, config_key: str, key_col: str):
        st.subheader(title)
        data_dict = st.session_state["config_rewards"][config_key]
        df = pd.DataFrame(list(data_dict.items()), columns=[key_col, "Reward"])
        # Add visual helper column for packs
        df["Có Pack?"] = df["Reward"].apply(lambda x: "📦" if "Pack" in str(x) else "")
        
        st.dataframe(df, hide_index=True, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        render_reward_viewer("🎁 Master Pass (Free)", "master_pass_free", "Level")
        render_reward_viewer("🔥 Win Streak", "win_streak_rewards", "Wins")
    with c2:
        render_reward_viewer("👑 Master Pass (Premium)", "master_pass_premium", "Level")
        render_reward_viewer("🔑 Key Collection", "key_collection_rewards", "Stage")

    if applied:
        # Apply System Config
        new_power = st.session_state["ui_new_power"]
        st.session_state["draft_new_card_power"] = new_power
        st.session_state["new_card_formula_type"] = "document"
        st.session_state["new_card_power"] = new_power
        
        new_chest_x = st.session_state["ui_chest_x"]
        st.session_state["draft_chest_drop_x"] = new_chest_x
        st.session_state["config_chest_drop_x"] = new_chest_x
        
        st.session_state["config_ss2_s_base"] = st.session_state["ui_ss2_s_base"]
        st.session_state["config_ss2_s_max"] = st.session_state["ui_ss2_s_max"]
        st.session_state["config_ss2_c_base"] = st.session_state["ui_ss2_c_base"]
        st.session_state["config_ss2_c_max"] = st.session_state["ui_ss2_c_max"]
        
        # Apply Chest Tiers Config
        for idx, row in edited_chest_tiers.iterrows():
            tier_str = str(idx + 1)
            t = st.session_state["draft_config_chest_drop_tiers"][tier_str]
            t["y_value"] = float(row["y_value"])
            for i in range(1, 7):
                col_name = f"Star_{i}" if i < 6 else "Gold"
                t["weights"][str(i)] = int(row[col_name])
        st.session_state["config_chest_drop_tiers"] = copy.deepcopy(st.session_state["draft_config_chest_drop_tiers"])
        
        # Apply Chest Upgrade Matrix
        for idx, row in edited_matrix.iterrows():
            stier_str = str(idx + 1)
            for ctier in range(1, 5):
                col_name = f"Lên {ctier+1}-Sao"
                st.session_state["draft_config_chest_upgrade_matrix"][stier_str][str(ctier)] = float(row[col_name])
            # Set ctier=5 to 0.0 implicitly since there is no UI for it
            st.session_state["draft_config_chest_upgrade_matrix"][stier_str]["5"] = 0.0
        st.session_state["config_chest_upgrade_matrix"] = copy.deepcopy(st.session_state["draft_config_chest_upgrade_matrix"])
        
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
        
        # Removed Rewards Config application because they are now read-only
        
        st.toast("✅ Cấu hình đã được lưu thành công!")
        st.session_state["show_config_success"] = True
        st.rerun()

