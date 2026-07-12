# Tổng quan ngữ cảnh LiveOps & Card Album

Tài liệu này tổng hợp chi tiết về tính năng Card Album và cách nó tương tác, tích hợp với toàn bộ hệ thống LiveOps trong game dựa trên file thiết kế và cập nhật.

---

## 1. Tổng quan Card Album
- **Mục đích:** Tạo mục tiêu dài hạn cho người chơi (Long-term goal), thúc đẩy Retention (D7/D30), Engagement (số lần mở game, thời gian chơi) và Monetization (doanh thu từ IAP, hiệu ứng FOMO).
- **Unlock:** Mở khóa sau khi người chơi hoàn thành Level 29 (từ Level 30).
- **Season (Mùa):** Mỗi mùa kéo dài 60 ngày (2 tháng, bắt đầu từ ngày đầu tháng đến cuối tháng tiếp theo).
- **Card Set (Bộ thẻ):** Mỗi mùa có 15 Set thẻ, mỗi Set 9 thẻ => Tổng cộng 135 thẻ.
- **Rarity (Độ hiếm):** Thẻ được chia thành 6 cấp: Common (⭐), Uncommon (⭐⭐), Rare (⭐⭐⭐), Epic (⭐⭐⭐⭐), Legendary (⭐⭐⭐⭐⭐), và Secret/Gold (⭐⭐⭐⭐⭐ - không thể giao dịch).
- **Star Conversion (Quy đổi sao):** Thẻ trùng lặp sẽ tự động chuyển thành Sao (Stars) dựa trên độ quý hiếm (từ +1 đến +15 Sao). Sao dùng để đổi Rương (Chest) lấy tài nguyên và thẻ. Cuối mùa, Sao thừa tự động đổi thành Coin (tỉ lệ 1:1).
- **Album Completion:** Sau khi sưu tập đủ 135 thẻ bản thường, người chơi nhận thưởng lớn, mở khóa "Grand Album" (reset số thẻ về 0 nhưng giữ nguyên Sao) để tiếp tục sưu tập vòng 2. Hoàn thành Grand Album sẽ nhận giải thưởng kim cương (Diamond Exclusive Badge).

---

## 2. Card Packs
Hệ thống bao gồm 10 loại Card Pack: 5 pack thường, 2 pack đặc biệt, và 3 pack bonus (trong sự kiện Card Rush).

| Loại Pack | Phân loại | Số thẻ | Bảo hiểm tối thiểu (Guarantee) |
| :--- | :--- | :---: | :--- |
| **Bronze** | Thường | 2 | Ít nhất 1 thẻ 1-Sao |
| **Emerald** | Thường | 3 | Ít nhất 1 thẻ 2-Sao |
| **Silver** | Thường | 4 | Ít nhất 1 thẻ 3-Sao |
| **Amethyst** | Thường | 5 | Ít nhất 1 thẻ 4-Sao |
| **Ruby** | Thường | 6 | Ít nhất 1 thẻ 5-Sao |
| **Gold** | Đặc biệt | 6 | Ít nhất 1 thẻ Gold (Mua IAP) |
| **Rainbow** | Đặc biệt | 6 | Ít nhất 1 thẻ Wild Card (Luôn ra 1 thẻ MỚI, ưu tiên Gold) |
| **Bronze+** | Bonus (Card Rush) | 3 | Ít nhất 1 thẻ 1-Sao |
| **Emerald+** | Bonus (Card Rush) | 5 | Ít nhất 1 thẻ 2-Sao |
| **Silver+** | Bonus (Card Rush) | 6 | Ít nhất 1 thẻ 3-Sao |

---

## 3. Tất cả LiveOps có thưởng Card Pack
Khi Card Album được mở khóa, các tính năng LiveOps sau sẽ lập tức được cập nhật phần thưởng để tặng kèm Card Pack:
1. **Master Pass**
2. **Win Streak** (Chuỗi thắng)
3. **Core Gameplay**: Hard Level & Super Hard Level
4. **Key Collection**
5. **Chain Offer**
6. **Super Out of Coins** (Gói cứu trợ khi hết Coin)
7. **Main Shop Bundles**
8. **Card Rush**
9. **Stamp Card**

---

## 4. Chi tiết từng LiveOps

### 4.1. Master Pass
- **Mục đích:** Tặng thưởng theo tiến trình chơi (Pass). Cập nhật cả đường Free và Premium khi tính năng Card Album mở.
- **Bảng chi tiết các mốc thưởng:**

| Stage | Token Yêu cầu | Quà Free (Thường) | Quà Premium (VIP) |
|:---|:---|:---|:---|
| 0 | 0 | 1x Hammer | 8-Heart Limit + 600 Coins |
| 1 | 1 | 15m Heart | 30m Heart |
| 2 | 2 | **1x Bronze Pack** | **1x Emerald Pack** |
| 3 | 3 | 40 Coins | 1x Scissors |
| 4 | 4 | 1x Scissors | 1x Hammer |
| 5 | 8 | Chest: 1x Scissors + **1x Bronze Pack** | Chest: 100 Coins + 1x Broom + **1x Emerald Pack** |
| 6 | 5 | 60 Coins | 1x Scissors |
| 7 | 6 | 15m Heart | 30m Heart |
| 8 | 9 | 1x Hammer | 1x Hammer |
| 9 | 7 | 1x Broom | 1x Broom |
| 10 | 10 | Chest: 1x Scissors + 1x Hammer + **1x Emerald Pack** | Chest: 150 Coins + 1x Hammer + 1x Broom + **1x Silver Pack** |
| 11 | 8 | 1x Hammer | 2x Scissors |
| 12 | 12 | **1x Silver Pack** | **1x Amethyst Pack** |
| 13 | 11 | 30m Heart | 60m Heart |
| 14 | 9 | 1x Scissors | 1x Broom |
| 15 | 15 | Chest: 1x Scissors + 1x Broom + **1x Silver Pack** | Chest: 200 Coins + 1x Boosters Set + **1x Silver Pack** |
| 16 | 16 | 80 Coins | 2x Hammer |
| 17 | 10 | **1x Emerald Pack** | **1x Silver Pack** |
| 18 | 14 | 1x Scissors | 2x Scissors |
| 19 | 18 | 30m Heart | 60m Heart |
| 20 | 20 | Chest: 1x Hammer + 1x Broom + **1x Amethyst Pack** | Chest: 300 Coins + 60m Heart + 1x Boosters Set + **1x Amethyst Pack** |
| 21 | 15 | 1x Hammer | 2x Hammer |
| 22 | 11 | 100 Coins | 2x Broom |
| 23 | 19 | 30m Heart | 60m Heart |
| 24 | 17 | **1x Emerald Pack** | **1x Silver Pack** |
| 25 | 20 | Chest: 1x Boosters Set + **1x Silver Pack** | Chest: 500 Coins + 60m Heart + 2x Boosters Set + **1x Ruby Pack** |
| 26 | 18 | 1x Hammer | 3x Hammer |
| 27 | 21 | 1x Scissors | 3x Scissors |
| 28 | 24 | **1x Silver Pack** | **1x Amethyst Pack** |
| 29 | 22 | 1x Broom | 3x Broom |
| 30 | 25 | Chest: 200 Coins + 1x Boosters Set + **1x Ruby Pack** | Chest: 750 Coins + 60m Heart + 3x Boosters Set + **1x Rainbow Pack** |
| 30+ | | | Bonus Bank: Lên đến 3000 Coins (150 Coins mỗi 10 Keys) |

### 4.2. Win Streak (Chuỗi Thắng)
- **Mục đích:** Thưởng người chơi giữ chuỗi thắng liên tục, kích thích việc không muốn thua (phải dùng Coin hồi sinh).
- **Chi tiết bảng chuỗi thắng (Sau khi cập nhật Card Album):**

| Mốc Thắng (Wins) | Phần Thưởng Chính |
|:---|:---|
| 2 | 40 Coins |
| 5 | 1x Scissors + **1x Bronze Pack** |
| 8 | 15m Heart + 1x Hammer |
| 11 | 80 Coins + **1x Emerald Pack** |
| 15 | 1x Broom |
| 20 | 30m Heart + **1x Silver Pack** |
| 25 | 160 Coins |
| 30 | 2x Scissors + **1x Amethyst Pack** |
| 35 | 1h Heart + 1x Hammer + 1x Broom |
| 45 | 500 Coins + 1x Boosters Set + Avatar (Hoặc **1x Ruby Pack** nếu đã sở hữu Avatar) |

### 4.3. Key Collection
- **Mục đích:** Người chơi thu thập chìa khóa (Keys) thông qua việc vượt level để mở các mốc thưởng. Có tổng cộng 25 Stage với tổng 304 Keys yêu cầu.
- **Lưu ý số lượng Key/Level:** Mỗi khi vượt qua một Level, người chơi sẽ nhận được mặc định **5 Keys** (Token).
- **Bảng chi tiết các mốc thưởng:**

| Stage | Token Yêu cầu (Keys) | Tổng Token Cộng dồn | Số Level Tương đương | Phần thưởng (Reward) |
|:---|:---|:---|:---|:---|
| 1 | 3 | 3 | 0.6 | 15m Heart |
| 2 | 5 | 8 | 1.6 | 1x Scissors |
| 3 | 7 | 15 | 3.0 | 15m x2 Key |
| 4 | 10 | 25 | 5.0 | **1x Bronze Pack** |
| 5 | 8 | 33 | 6.6 | 1x Hammer |
| 6 | 7 | 40 | 8.0 | 1x Broom |
| 7 | 12 | 52 | 10.4 | **1x Bronze Pack** |
| 8 | 15 | 67 | 13.4 | 30m x2 Key |
| 9 | 10 | 77 | 15.4 | 1x Scissors |
| 10 | 12 | 89 | 17.8 | **1x Emerald Pack** |
| 11 | 10 | 99 | 19.8 | 30m Heart |
| 12 | 12 | 111 | 22.2 | 80 Coins |
| 13 | 15 | 126 | 25.2 | **1x Emerald Pack** |
| 14 | 12 | 138 | 27.6 | 1x Broom |
| 15 | 16 | 154 | 30.8 | 30m x2 Key |
| 16 | 10 | 164 | 32.8 | 120 Coins |
| 17 | 12 | 176 | 35.2 | **1x Silver Pack** |
| 18 | 16 | 192 | 38.4 | 1x Scissors |
| 19 | 12 | 204 | 40.8 | 1h Heart |
| 20 | 10 | 214 | 42.8 | 200 Coins |
| 21 | 15 | 229 | 45.8 | **1x Amethyst Pack** |
| 22 | 12 | 241 | 48.2 | 1x Hammer |
| 23 | 18 | 259 | 51.8 | 1h x2 Key |
| 24 | 20 | 279 | 55.8 | **1x Ruby Pack** |
| 25 | 25 | 304 | 60.8 | 1000 Coins |

### 4.4. Chain Offer
- **Mục đích:** Chuỗi ưu đãi tuần tự, bao gồm các mốc Free để "nhử" và các mốc IAP (trả phí) xen kẽ.
- **Bảng chi tiết các mốc Offer:**

| Stage | Phần (Part) | Mốc (No.) | Giá (Price) | Phần thưởng |
|:---|:---|:---|:---|:---|
| 1 | 1 | 1 | FREE | 1x Scissors |
| 2 | 1 | 2 | FREE | 15m Heart |
| 3 | 1 | 3 | FREE | **1x Bronze Pack** |
| 4 | 2 | 1 | $2.49 | 800 Coins + **1x Emerald Pack** |
| 5 | 2 | 2 | FREE | 1x Scissors |
| 6 | 2 | 3 | FREE | 100 Coins |
| 7 | 2 | 4 | FREE | **1x Bronze Pack** |
| 8 | 2 | 5 | FREE | Chest: 30m Heart + 1x Hammer |
| 9 | 3 | 1 | $4.99 | 1800 Coins + **1x Silver Pack** |
| 10 | 3 | 2 | FREE | 30m Heart |
| 11 | 3 | 3 | FREE | 1x Scissors |
| 12 | 3 | 4 | FREE | **1x Emerald Pack** |
| 13 | 3 | 5 | FREE | 1x Hammer |
| 14 | 3 | 6 | FREE | Chest: 30m Heart + 1x Broom |
| 15 | 4 | 1 | $10.99 | 4000 Coins + **1x Amethyst Pack** |
| 16 | 4 | 2 | FREE | 2x Scissors |
| 17 | 4 | 3 | FREE | 1h Heart |
| 18 | 4 | 4 | FREE | Chest: 1x Hammer + 1x Scissors + 1x Broom |
| 19 | 4 | 5 | FREE | **1x Emerald Pack** + **1x Silver Pack** |
| 20 | 4 | 6 | FREE | 2x Hammer |
| 21 | 5 | 1 | $18.99 | 8000 Coins + **1x Ruby Pack** |
| 22 | 5 | 2 | FREE | Chest: 2x Scissors + 2x Hammer + 2x Broom |
| 23 | 5 | 3 | FREE | **1x Amethyst Pack** |
| 24 | 5 | 4 | FREE | 3h Heart |
| 25 | 5 | 5 | FREE | 300 Coins |
| 26 | 5 | 6 | FREE | Chest: 1h Heart + **1x Silver Pack** |
| 27 | 6 | 1 | $27.99 | 12000 Coins + **1x Gold Pack** |
| 28 | 6 | 2 | FREE | **1x Silver Pack** + **1x Amethyst Pack** |
| 29 | 6 | 3 | FREE | Chest: 3x Scissors + 3x Hammer + 3x Broom |
| 30 | 6 | 4 | FREE | 6h Heart |
| 31 | 6 | 5 | FREE | 1200 Coins |
| 32 | 6 | 6 | FREE | 1x Scissors + 1x Hammer |
| 33 | 7 | 1 | $49.99 | 24000 Coins + **1x Rainbow Pack** |
| 34 | 7 | 2 | FREE | Chest: 4x Scissors + 4x Hammer + 4x Broom |
| 35 | 7 | 3 | FREE | **1x Ruby Pack** |
| 36 | 7 | 4 | FREE | 1500 Coins |
| 37 | 7 | 5 | FREE | 12h Heart |
| 38 | 7 | 6 | FREE | Chest: **1x Emerald Pack** + **1x Silver Pack** + **1x Amethyst Pack** |

### 4.5. Core Gameplay (Hard / Super Hard Level)
- **Trigger:** Chiến thắng màn chơi có gắn tag Hard hoặc Super Hard.
- **Reward:** Thắng Hard Level được thưởng 1 **Bronze Pack**. Thắng Super Hard Level thưởng 1 **Emerald Pack**.
- **Popup/Flow:** Thông báo ở màn hình Home khi tiến tới Level Khó. Nếu người chơi thua/thoát (Quit), sẽ có popup nhắc nhở "Sẽ mất Card Pack nếu bỏ cuộc".

### 4.6. Main Shop Bundles & Super Out Of Coins (IAP)
- **Reward (Main Shop Bundles):**
  - $9.99 (Decorated Pouch): +1 Silver Pack
  - $19.99 (Artisan Satchel): +1 Amethyst Pack
  - $29.99 (Exquisite Basket): +1 Ruby Pack
  - $49.99 (Overflowing Chest): +1 Rainbow Pack
  - $99.99 (Royal Vault): +3 Rainbow Pack

- **Bảng chi tiết phần thưởng (Out of Coins Adjusted):**

| Gói | Giá | Chi tiết phần thưởng |
|:---|:---|:---|
| Out of Coins 1 | $2.99 | 900 Coins + 1x Scissors |
| Out of Coins 2 | $5.99 | 1800 Coins + 1x Hammer + 1x Broom |
| Out of Coins 3 | $11.99| 3600 Coins + 2x Scissors + 2x Hammer + 2x Broom |
| Super Out of Coins 4 | $6.99 | 2000 Coins + 2x Scissors + **1x Emerald Pack** |
| Out of Coins 5 | $14.99| 5000 Coins + 3x Scissors + 2x Hammer + **1x Silver Pack** |
| Out of Coins 6 | $29.99| 11000 Coins + 4x Scissors + 3x Hammer + 2x Broom + **1x Amethyst Pack** |

---

## 5. Sự kiện Card Rush
- **Mục đích:** Tăng giá trị các gói pack nhỏ (thêm thẻ 50%) để kích cầu tiêu dùng và chơi game.
- **Lifecycle (Schedule):** Bắt đầu diễn ra từ 00:00 - 23:59.
  - Tuần 1, 2 của Mùa: Chỉ mở vào Thứ 7.
  - Tuần 3, 4, 5: Mở Thứ 4, Thứ 7.
  - Tuần 6 trở đi: Mở Thứ 2, Thứ 4, Thứ 7.
- **Cơ chế:** Gói Bronze, Emerald, Silver tự động biến thành **Bronze+, Emerald+, Silver+** (tỉ lệ rớt thẻ giữ nguyên, số lượng thẻ tăng lên).
- **Birthday Version:** Sẽ có một giao diện/theme Sinh nhật thay thế nếu event rơi vào chuỗi ngày sinh nhật game (VD: 18, 20, 22/6).
- **Remote Config:** `card_rush_event` (True/False), `card_rush_bd_event`, `card_rush_bd_lifecycle`.

---

## 6. Sự kiện Stamp Card
- **Mục đích:** Kích thích người chơi thu thập các Pack cao cấp (Amethyst, Ruby) để lấy Stamp đổi quà.
- **Chu kỳ:** Thỉnh thoảng xuất hiện trong mùa, xuất hiện dày đặc hơn về cuối mùa.
- **Cơ chế:** Thu thập đủ số lượng Stamp yêu cầu để lấy thưởng.

---

## 7. Tương tác giữa Card Album và toàn bộ LiveOps
- **Dependency (Sự phụ thuộc):** Card Album hoạt động như một "Feature Hub". Khi biến `turn_on_card_album = True` và người chơi đạt Lv30, nó sẽ gửi tín hiệu (Broadcast) đến toàn bộ các LiveOps khác để "bật" phần thưởng chứa Card Pack.
- **Time/Season Sync:** Nếu người chơi offline (Cheat time), event sẽ ghi nhận mốc thời gian cao nhất trong session. Nếu cheat vượt quá thời gian event kết thúc, tính năng bị vô hiệu hóa ("Please update game...").
- **Popup Queueing:** Khi mua bundle qua pop-up In-game (Revive), pack thẻ đập ra ngay lập tức, nhưng nếu thu thập trọn bộ (Set/Album Complete), các popup trao thưởng siêu bự sẽ được đưa vào "Hàng đợi (Queue)" và chỉ hiển thị khi người chơi quay về Màn hình Home.

---

## 8. Bảng tổng hợp LiveOps & Thưởng

| LiveOps / Feature | Khi nào xuất hiện | Thưởng Pack gì? | Có giới hạn không? | Chu kỳ | Remote Config |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Hard Level** | Thắng màn Hard | **Bronze** | Không | Xuyên suốt | `card_collection_feature` |
| **Super Hard Level**| Thắng màn Super Hard | **Emerald** | Không | Xuyên suốt | `card_collection_feature` |
| **Win Streak** | Chuỗi thắng 5, 11, 20, 30, 45 | Bronze -> Ruby | Theo cấp chuỗi thắng | Xuyên suốt | `card_collection_feature` |
| **Master Pass** | Đạt mốc Pass tương ứng | Bronze -> Rainbow | Có (Theo mốc pass) | Theo mùa Pass | `card_collection_feature` |
| **Key Collection**| Đạt mốc 4, 7, 10, 13 | Bronze, Emerald | Theo mùa | Theo mùa | `card_collection_feature` |
| **Chain Offer** | Hoàn thành phần/Free | Bronze -> Amethyst| Theo mốc/gói | Xuyên suốt | `card_collection_feature` |
| **Shop Bundles** | Mua IAP ($9.99 - $99.99) | Silver -> 3x Rainbow | Không giới hạn | Xuyên suốt | `card_collection_feature` |
| **Out of Coins** | Khi hết xu, hiện Popup | Emerald -> Amethyst | Không giới hạn | Xuyên suốt | `card_collection_feature` |
| **Card Rush** | Ngày chỉ định trong tuần | Nâng thành **Plus (+)** | Có hạn (24h) | Tăng dần cuối mùa| `card_rush_event` |
| **Stamp Card** | Mở gói Amethyst/Ruby | Quà sự kiện | Có hạn | Random/Cuối mùa | N/A |
