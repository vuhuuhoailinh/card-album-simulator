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

from .inventory import render_inventory_tab
from .gacha import render_pack_opener_tab
from .chest_drop import render_chest_drop_tab
from .analytics import render_analytics_tab

def run_app() -> None:
    st.set_page_config(page_title="Card Album Simulator", layout="wide")
    ensure_album_state(st.session_state)
    
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
                background-color: var(--background-color, white) !important;
                color: var(--text-color, black) !important;
                border: 1px solid var(--text-color, black) !important;
            }
            div.element-container:has(#info-button-target) + div.element-container button * {
                color: var(--text-color, black) !important;
            }
            </style>
            """, 
            unsafe_allow_html=True
        )
        if st.button("i", type="primary", help="Infomation"):
            show_logic_dialog()
    
    tab_inventory, tab_manual, tab_chestdrop, tab_auto, tab_mc, tab_config = st.tabs(["📚 Bộ Sưu Tập", "📦 Mở Pack", "🎮 Chest Drop", "📈 LiveOps Economy", "📊 Monte Carlo Simulator", "⚙️ Economy Tuning"])
    
    with tab_inventory:
        render_inventory_tab()
        
    with tab_manual:
        render_pack_opener_tab()
        
    with tab_chestdrop:
        render_chest_drop_tab()
        
    with tab_mc:
        from ..monte_carlo import render_monte_carlo_tab
        render_monte_carlo_tab()
        
    with tab_auto:
        render_analytics_tab()
        
    with tab_config:
        from ..config_ui import render_config_tab
        render_config_tab()


@st.dialog("📖 TỔNG QUAN LOGIC HỆ THỐNG", width="large")
def show_logic_dialog():
    st.markdown("""
        <style>
            /* Hack to make the dialog wider on desktop screens */
            div[data-testid="stDialog"] div[role="dialog"] {
                width: 85vw !important;
                max-width: 1200px !important;
            }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
### 1. Cơ Chế Gacha Cơ Bản & Pity (Bảo hiểm)
- **Tỉ lệ Rớt Độ Hiếm (Drop Rates):** 
  - (VD: 28% ra 1-Sao, 1% ra Vàng) là **CỐ ĐỊNH** và luôn không đổi trong suốt quá trình mở gói.
- **Công thức Tỉ lệ Thẻ MỚI (New Chance):** 
  - Là tỉ lệ để lá thẻ vừa rớt ra rơi vào lá bạn CHƯA CÓ. Tỉ lệ này tự động trượt giảm dần theo công thức chung: 
  - `New Card Ratio = (Remaining New / Total) ^ (x + y) + Pity`
  - `x`: Hệ số Khó chung (Càng cao càng khó ra thẻ mới, tuỳ chỉnh trong Tuning).
  - `y`: Hệ số Khó riêng (Ở Gacha mở pack, y lấy theo loại Gói. Ở Chest Drop, y lấy theo Độ Hiếm của thẻ).
- **Thẻ Bảo Hiểm (Guaranteed):** Mỗi gói đều cam kết rớt 1 thẻ ở ĐÚNG độ hiếm cụ thể (Ví dụ gói Emerald chắc chắn có 1 thẻ 2-Sao).
- **Cơ Chế Pity (Đếm Tạch):** 
  - Hoạt động **độc lập** cho TỪNG LOẠI GÓI THẺ. (Pity của Silver KHÔNG chia sẻ cho Amethyst).
  - Mỗi khi mở một gói mà không ra bất kỳ thẻ **NEW** nào, số lần "Tạch" của gói đó tăng lên 1.
  - Khi tạch đến ngưỡng quy định, gói đó sẽ được **buff thêm % Tỉ lệ ra Thẻ Mới** ở lần mở sau. (Vd: Gói Silver tạch 3 lần sẽ buff +20%).
- **Ngắt Pity Giữa Chừng (Mid-Pack Reset):** Tỉ lệ buff Pity được cộng thẳng vào từng lá bài khi nó lật lên. Ngay khoảnh khắc lá bài đầu tiên nổ ra chữ **NEW**, lượng % buff này sẽ **lập tức bốc hơi (về 0%)**. Các lá bài lật sau đó trong cùng gói sẽ trở về tỉ lệ gốc, nhằm chống lạm phát thẻ mới.

### 2. Rainbow Pack & 5 Gói Tân Thủ
- **Tân Thủ:** 5 gói thẻ đầu tiên bạn nhận được trong Mùa (từ bất kỳ nguồn nào) sẽ được hệ thống buff **100% rớt toàn Thẻ Mới**.
- **Rainbow Pack:** Gói thẻ đặc quyền có 6 thẻ, trong đó chắc chắn rớt 1 Thẻ Mới (Wild Card). Thuật toán sẽ luôn ưu tiên rớt **Thẻ Vàng (6-Sao)** trước. 
  - *Clarification:* Trong game gốc, nếu Vàng đã full, Wild Card sẽ ưu tiên các "Bộ (Sets) chỉ còn thiếu 1 lá". Do Simulator này chỉ track tiến độ theo Độ Hiếm, hệ thống sẽ giả lập bằng cách rớt ngẫu nhiên 1 Thẻ Mới từ các độ hiếm còn thiếu.

### 3. Grand Album & Thẻ Trùng (Duplicated)
- **Hoàn thành Album:** Sau khi sưu tập đủ 135 thẻ, bạn sẽ hoàn thành vòng Album và được thăng cấp sang "Grand Album".
- **Luật Reset:** Khi thăng cấp, kho thẻ sẽ **bị Reset toàn bộ về 0**, nhưng lượng **Sao (Stars)** bạn tích lũy được sẽ **giữ nguyên vẹn** (Dùng để mua các rương sao sau này).
- **Thẻ Trùng:** Mọi thẻ trùng lặp quay ra sẽ tự động phân rã thành **Sao**. Thẻ càng hiếm, số Sao thu được càng cao (Từ 1 Sao cho thẻ 1-Sao lên tới 15 Sao cho Thẻ Vàng).

### 4. Hệ Sinh Thái LiveOps (Sự kiện & Nền kinh tế)
Trong tab `📈 LiveOps Simulator`, hệ thống sử dụng thuật toán giả lập để ước tính số Pack và Rương (Chest) bạn nhận được dựa trên giả định bạn chơi hoàn hảo (perfect play) theo số ngày và **khoảng số level ngẫu nhiên** mỗi ngày đã cấu hình:
- **Core Gameplay (Thắng màn Khó):** Cứ thắng màn Hard sẽ thưởng gói Bronze, thắng Super Hard thưởng gói Emerald. Tiến trình Level diễn ra theo chu kỳ cố định: N-N-H, N-N-H, N-N-SH (sau 2 Normal tới 1 Hard, sau 2 Hard tới 1 Super Hard).
- **Win Streak:** Giữ chuỗi thắng liên tiếp để càn quét các phần thưởng dọc đường. Sự kiện tự động kích hoạt vào mỗi cuối tuần (Thứ 6 đến Chủ Nhật). Chuỗi thắng bị reset về 0 mỗi đầu sự kiện. Từ lần đạt mốc cao nhất (Mốc 45) thứ 2 trở đi, phần thưởng Avatar sẽ được quy đổi thành Ruby Pack. *(Có thể xem chi tiết các phần thưởng ở tab Economy Tuning)*
- **Master Pass (Battle Pass):** Hệ thống Battle Pass của game. Thu thập token từ các màn chơi (Thắng Normal: 1 Token, Hard: 2 Tokens, Super Hard: 3 Tokens) để thăng cấp (tối đa 30) và nhận thưởng. Nhánh Premium (trả phí) sẽ mở khóa nhiều phần thưởng hấp dẫn hơn. Sự kiện được reset tiến trình và lặp lại mỗi tháng (30 ngày). *(Có thể xem chi tiết các phần thưởng ở tab Economy Tuning)*
- **Key Collection:** Cày chìa khóa theo tiến độ để mở khóa các phần thưởng theo mốc. Mỗi level qua màn nhận mặc định 5 keys bất kể độ khó. Sự kiện được reset tiến trình và lặp lại vào mỗi đầu tuần (Thứ 2). *(Có thể xem chi tiết các phần thưởng ở tab Economy Tuning)*
- **Chain Offer & IAP:** Các sự kiện bán gói ưu đãi theo chuỗi. Simulator cho phép bạn giả lập "tiêu tiền" vào các mốc Chain (VD: Mua OOC, Mua Shop) để tính toán tổng lợi nhuận Pack thu về so với số USD đã bỏ ra. Mặc định mua các gói này nhận Pack thường (Không áp dụng thưởng sự kiện Card Rush).
- **⚡ Card Rush:** Sự kiện đặc biệt mở theo lịch tuần (Tuần 1-6: Thứ 7 | Tuần 7 trở đi: Thứ 4, 7). Khi kích hoạt, các gói thẻ thường (Bronze, Emerald, Silver) sẽ chuyển thành **Plus (+), thêm 50% số lượng thẻ** vào từng gói (VD: Bronze từ 2 lên 3 thẻ, Emerald từ 3 lên 5 thẻ, Silver từ 4 lên 6 thẻ...). Mua gói từ Shop/IAP sẽ KHÔNG được cộng dồn Card Rush.

### 5. Minigame Đập Rương (Chest Drop)
- **Thu thập:** Nhận được từ việc cày cuốc (đạt mốc 3, 7, 12 level trong cùng 1 ngày sẽ nhận lần lượt rương 1-Sao, 2-Sao, 3-Sao).
- **Thăng Cấp Rương (Upgrade):** Khi mở rương, có xác suất rương sẽ tự động nâng cấp lên sao cao hơn (tối đa 5-Sao). Tỉ lệ thăng cấp phụ thuộc vào rương khởi đầu (Rương 3-Sao khởi đầu sẽ dễ nổ ra 5-Sao hơn rương 1-Sao).
- **Tránh trùng lặp (No-Dup):** Khi mở 1 Gói Thẻ hoặc 1 Rương bất kỳ, hệ thống đảm bảo các lá thẻ rớt ra trong **chính Gói/Rương đó** sẽ hoàn toàn khác nhau và không bị trùng lặp (nếu số lượng thẻ rớt ra vượt quá số lượng thẻ của game thì mới bắt buộc phải trùng).
    """)

