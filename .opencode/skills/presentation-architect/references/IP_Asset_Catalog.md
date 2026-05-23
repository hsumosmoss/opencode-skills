# 個人 IP 圖庫清單 v2.0
> **用途**：供 AI 工具自動配圖使用
> **總數**：100 組
> **版本**：2.0（語義標準化 + 去重 + 擴充至 100 組）
> **規則**：AI 應依據當前頁面的 `mood`、`trigger_keywords`、`use_case` 進行最佳匹配，並迴避 `negative_use` 所列場景。

---

## 欄位說明

| 欄位 | 說明 |
|------|------|
| `id` | 圖片唯一識別碼 |
| `pose` | 姿勢與動作描述（用於圖片生成或對照查找）|
| `mood` | 情緒基調（英文關鍵詞，便於跨語言 AI 推理）|
| `trigger_keywords` | AI 看到這些詞時應優先選用此張 |
| `use_case` | 適合放置的內容區塊或頁面類型 |
| `negative_use` | 不適合使用的場景（防止誤配）|

---

## IP 圖庫總表

| id | pose | mood | trigger_keywords | use_case | negative_use |
|----|------|------|-----------------|----------|--------------|
| IP_01_greet | 右手友好舉起揮手，笑容燦爛 | warm / welcoming | 開場、歡迎、你好、自我介紹、打招呼、首頁 | 封面頁、自我介紹頁、課程開場、活動歡迎頁 | 警告頁、數據分析頁、危機說明頁 |
| IP_02_think | 單手托腮思考，眉頭微皺 | analytical / contemplative | 分析、思考、策略、為什麼、原因、痛點、問題 | 問題分析頁、策略規劃頁、對比區塊 | 慶祝頁、開場頁、輕鬆過場頁 |
| IP_03_shock | 雙手抱頭，驚訝睜大眼睛 | alarmed / shocked | 警告、危險、驚人、沒想到、錯誤、避雷、迷思 | 警告區塊、錯誤示範頁、驚人數據頁 | 成功案例頁、輕鬆頁、結論頁 |
| IP_04_point_right | 側身指向右方平板電腦上的圖表 | precise / guiding | 數據、圖表、指標、佐證、關鍵數字、統計 | 數據佐證頁、KPI 展示頁、關鍵指標區塊 | 情感共鳴頁、開場頁、感謝頁 |
| IP_05_deep_read | 坐姿專注閱讀厚實實體書 | focused / scholarly | 研究、閱讀、報告、文獻、深度學習、知識 | 研究報告頁、深度內容區塊、背景說明頁 | 快速行動頁、輕鬆過場頁、CTA 頁 |
| IP_06_code_hologram | 坐在全息鍵盤前快速打字，眼鏡反光 | technical / immersed | 程式、技術、開發、AI、自動化、系統、工程 | 技術細節頁、程式開發展示、工具介紹頁 | 情感頁、輕鬆頁、感謝頁 |
| IP_07_explain_diagram | 站在全息架構模型前，雙手打開解釋 | teaching / systematic | 流程、架構、步驟、說明、解釋、系統設計 | 流程圖頁、架構說明頁、教學步驟頁 | 情緒渲染頁、警告頁 |
| IP_08_award_trophy | 站立高舉金色獎盃，自信微笑 | triumphant / proud | 成功、成就、獲獎、榮譽、冠軍、里程碑 | 成功案例頁、榮譽牆、結論收尾頁 | 問題分析頁、警告頁、開場頁 |
| IP_09_run_dynamic | 全速跑步動態姿勢，西裝外套飄動 | energetic / action-driven | 行動、執行、快速、衝刺、啟動、推進 | 行動方案頁、市場推廣頁、執行力展示 | 靜態分析頁、沉靜思考頁 |
| IP_10_security_shield | 雙手向前推，出現數位護盾 | protective / serious | 安全、防護、資安、規範、避險、保護、合規 | 資安說明頁、數據保護區塊、風險防範頁 | 慶祝頁、輕鬆頁、開場頁 |
| IP_11_call | 單手拿手機貼耳，另一手插口袋微笑 | conversational / approachable | 聯繫、對話、客服、商務、洽談、聯絡我 | 聯繫資訊頁、商務洽談區塊、CTA 行動頁 | 技術展示頁、警告頁 |
| IP_12_code_standing | 站姿操作全息介面打字，表情專注 | focused / technical | 操作、介面、工具、平台、設定、配置 | 操作說明頁、工具展示頁、SaaS 功能頁 | 情緒頁、感謝頁、輕鬆頁 |
| IP_13_tablet_read | 坐姿專注閱讀平板，手指滑動 | analytical / modern | 數位閱讀、報告、數據、現代研究、平板工作 | 數位報告頁、線上資料說明、輕量研究區塊 | 行動頁、歡迎頁、慶祝頁 |
| IP_14_pain | 雙手抱頭表情沮喪，桌面文件凌亂 | frustrated / overwhelmed | 痛點、失敗、困境、問題、掙扎、壓力、挑戰 | 痛點描述頁、問題共鳴區塊、Before 頁面 | 成功頁、慶祝頁、開場頁 |
| IP_15_direct | 單手指向右側，引導視線 | directing / confident | 下一步、繼續、前進、引導、這裡、看這邊 | CTA 指引頁、步驟引導區塊、前進方向頁 | 感謝頁、問題分析頁 |
| IP_16_relax_inspiration | 靠牆雙手抱胸，微笑向上看，若有所思 | inspired / relaxed | 靈感、創意、想法、發想、brainstorm、思考 | 創意發想區塊、品牌故事頁、輕鬆過場 | 警告頁、技術頁、數據頁 |
| IP_17_award_sit | 坐姿捧著獎盃，謙遜而自信地微笑 | humble / accomplished | 成就、認可、里程碑、感謝肯定、獲獎感言 | 案例展示頁、見證區塊、學員成果頁 | 警告頁、問題頁、開場頁 |
| IP_18_presentation_screen | 站在發光虛擬螢幕前操作，講解功能 | professional / demonstrating | 演示、展示、報告、功能介紹、產品說明 | 功能匯報頁、產品 Demo 區塊、技術說明頁 | 輕鬆頁、感謝頁、情緒頁 |
| IP_19_run_casual | 輕快慢跑姿勢，表情輕鬆積極 | motivated / casual | 前進、開始、試試看、輕鬆上手、入門 | 新手引導頁、輕量行動 CTA、課程開始頁 | 技術細節頁、嚴肅分析頁 |
| IP_20_conclusion_sit | 坐在舒適椅子上，微笑面對觀眾，雙手交疊 | warm / closing | 總結、結語、感謝聆聽、Q&A、再見、結束 | 結論頁、Q&A 頁、課程結束頁 | 開場頁、警告頁、數據頁 |
| IP_21_handshake | 伸出右手準備握手，表情誠懇 | trustworthy / collaborative | 合作、夥伴、信任、協議、B2B、商業合作 | B2B 提案結尾、合作夥伴頁、達成協議頁 | 個人品牌頁、技術頁、警告頁 |
| IP_22_stop | 單手掌心向前做出停止手勢，表情認真 | warning / firm | 停、注意、別這樣做、常見錯誤、迷思破解 | 警告區塊、迷思破解頁、常見錯誤說明 | 歡迎頁、慶祝頁、輕鬆頁 |
| IP_23_idea_bulb | 食指向上，頭頂出現燈泡光芒 | insightful / eureka | 靈感、解法、亮點、創新、Aha moment、秘訣 | 創新策略頁、洞見區塊、解決方案揭示頁 | 警告頁、痛點頁、技術細節頁 |
| IP_24_chart_growth | 沿著向上綠色箭頭滑動，表情興奮 | optimistic / growth-driven | 成長、增長、ROI、業績、正向、趨勢向上 | 成長數據頁、ROI 展示頁、未來展望頁 | 風險頁、警告頁、痛點頁 |
| IP_25_chart_decline | 看著向下紅色圖表，表情凝重嚴肅 | concerned / serious | 衰退、風險、下滑、問題、危機、競品劣勢 | 危機分析頁、風險說明頁、競品對比頁 | 慶祝頁、成功頁、輕鬆頁 |
| IP_26_balance_scale | 雙手平舉如衡量天平，表情中立 | balanced / objective | 比較、權衡、A/B 測試、利弊、選擇、對比 | 方案比較頁、優缺點分析、A/B 測試說明 | 單一結論頁、慶祝頁 |
| IP_27_magnifying_search | 持巨大放大鏡看向鏡頭，表情專注 | investigative / detail-oriented | 深挖、審查、細節、調查、合約、審視、檢視 | 技術拆解頁、合約說明頁、深度審視區塊 | 輕鬆頁、開場頁、行動頁 |
| IP_28_target_hit | 指著正中紅心的標靶，表情自信 | precise / goal-oriented | 精準、達標、KPI、目標、命中、績效 | KPI 達成頁、精準行銷說明、目標設定頁 | 問題頁、過場頁、情感頁 |
| IP_29_puzzle_solver | 將最後一塊拼圖嵌入完整拼圖板，表情滿足 | completing / integrating | 整合、完成、最後一哩路、生態系、全貌 | 系統整合頁、解決方案總結、完整方案展示 | 開場頁、問題頁 |
| IP_30_time_urgent | 敲擊手錶，表情帶有緊迫感 | urgent / time-pressured | 時間、限時、截止、急迫、倒數、把握機會 | 限時優惠頁、敏捷說明頁、緊迫 CTA 區塊 | 輕鬆頁、沉靜頁、感謝頁 |
| IP_31_zen_meditate | 盤坐懸浮，雙手結印，表情平靜 | calm / centered | 冷靜、沉澱、心態、穩定、修煉、內功 | 職場心理學頁、心態管理區塊、過場緩衝頁 | 行動頁、警告頁、數據頁 |
| IP_32_megaphone_shout | 持大聲公廣播，表情興奮積極 | announcing / high-energy | 宣佈、重大消息、行銷、呼籲、注意看、發布 | 活動預告頁、強烈 CTA 頁、重大宣佈區塊 | 沉靜頁、分析頁、感謝頁 |
| IP_33_coffee_break | 持咖啡靠桌邊，輕鬆微笑 | relaxed / humanizing | 休息、文化、輕鬆、日常、幕後、團隊 | 團隊介紹頁、品牌文化頁、輕鬆過場頁 | 技術頁、警告頁、嚴肅分析頁 |
| IP_34_vr_metaverse | 戴 VR 頭盔操作虛擬介面 | futuristic / immersive | 未來、趨勢、元宇宙、VR、沉浸式、前沿科技 | 技術願景頁、未來趨勢說明頁、科技展示 | 傳統商務頁、感謝頁、輕鬆頁 |
| IP_35_multitask_juggling | 空中拋接多個圖示（齒輪、報表等）| dynamic / multi-skilled | 多工、管理、效率、同步、專案管理、流程 | 工作流優化頁、管理工具介紹、多任務說明 | 沉靜頁、輕鬆頁 |
| IP_36_high_five | 向鏡頭準備擊掌，表情開心 | celebratory / engaging | 慶祝、互動、激勵、一起、達成、見證 | 學員見證頁、互動結語、成果慶祝區塊 | 技術頁、警告頁、分析頁 |
| IP_37_taking_notes | 拿著寫字板認真記錄，表情專注 | attentive / diligent | 記錄、筆記、聆聽、客戶反饋、重點整理 | 客戶反饋頁、重點摘要頁、聆聽說明區塊 | 行動 CTA 頁、輕鬆頁 |
| IP_38_rocket_launch | 單手直指天空，背景火箭升空 | ambitious / launching | 起飛、發布、成長、啟動、指數、爆發 | 產品發布頁、業績起飛說明、成長展望頁 | 沉靜分析頁、感謝頁、過場頁 |
| IP_39_whisper_secret | 嘴邊說悄悄話，表情神秘 | exclusive / intimate | 秘訣、獨家、內部、Pro tips、只告訴你 | 進階教學頁、獨家內容揭示、秘密策略頁 | 公開宣告頁、警告頁 |
| IP_40_respectful_bow | 身體前傾 30 度鞠躬，表情誠摯 | grateful / closing | 感謝、致謝、再見、感恩、特別感謝 | 簡報最後一頁、特別感謝頁、課程結語 | 開場頁、行動頁、警告頁 |
| IP_41_thumbs_up | 豎起大拇指，笑容燦爛，直視鏡頭 | approving / affirming | 讚、認可、好的、正確、推薦、沒錯 | 認可說明頁、推薦理由頁、正面肯定區塊 | 警告頁、問題頁、嚴肅頁 |
| IP_42_arms_crossed_confident | 雙手交叉胸前，表情自信沉穩 | authoritative / composed | 專家、權威、立場、我認為、堅定、主張 | 專家觀點頁、強烈立場陳述、品牌主張頁 | 輕鬆頁、歡迎頁 |
| IP_43_sit_laptop | 坐姿操作筆電，表情專注輕鬆 | productive / everyday | 工作、日常、辦公、效率、平台操作 | 工具使用頁、日常工作流說明、SaaS 操作頁 | 慶祝頁、感謝頁 |
| IP_44_point_up | 食指向上方指，表情強調 | emphasizing / pointing | 重點、關鍵、注意、最重要的是、第一點 | 重點強調頁、關鍵洞見區塊、條列說明頁 | 輕鬆頁、感謝頁 |
| IP_45_look_left_thoughtful | 側身看向左方，陷入思考 | reflective / pondering | 回顧、過去、以前、比較、Before、歷史 | 歷史回顧頁、Before/After 左側、對比說明 | 未來展望頁、行動 CTA 頁 |
| IP_46_look_right_forward | 側身看向右方，表情期待 | forward-looking / hopeful | 未來、展望、After、接下來、下一步 | 未來展望頁、Before/After 右側、成果頁 | 回顧頁、問題頁 |
| IP_47_open_arms_welcome | 雙手向外展開，歡迎姿態 | inclusive / open | 歡迎加入、社群、開放、一起來、邀請 | 社群邀請頁、會員招募頁、開放報名頁 | 警告頁、技術細節頁 |
| IP_48_facepalm | 手掌摀臉，搖頭苦笑 | self-deprecating / relatable | 踩過坑、我也犯過、老實說、其實當初 | 真實故事頁、反思區塊、經驗分享頁 | 成功頁、技術頁、CTA 頁 |
| IP_49_write_whiteboard | 站在白板前書寫，背對鏡頭微側身 | teaching / planning | 規劃、列清單、白板、教學、步驟拆解 | 教學規劃頁、步驟說明頁、課程架構頁 | 輕鬆頁、感謝頁 |
| IP_50_show_phone_screen | 將手機螢幕朝向鏡頭，展示畫面 | demonstrating / showcasing | App、手機、操作畫面、介面展示、截圖說明 | App 介紹頁、行動裝置功能頁、UI 展示頁 | 感謝頁、過場頁 |
| IP_51_stand_podium | 站在講台發表，表情自信有力 | authoritative / presenting | 演講、發表、站台、分享、上台、主講 | 演講開場頁、重要宣言頁、主題發表頁 | 輕鬆頁、感謝頁、問題頁 |
| IP_52_team_virtual | 虛擬視訊會議畫面，多個頭像圍繞 | collaborative / remote | 遠端、線上會議、團隊協作、Zoom、遠距 | 遠端工作說明頁、團隊協作頁、線上課程頁 | 個人品牌頁、感謝頁 |
| IP_53_checklist | 拿著清單逐項打勾，表情滿足 | methodical / completing | 清單、逐步、完成、核對、SOP、流程確認 | SOP 說明頁、操作清單頁、完成確認頁 | 創意發想頁、情感頁 |
| IP_54_money_rain | 雙手接住飄落的金幣，表情驚喜 | rewarding / prosperity | 收益、賺錢、獲利、報酬、金錢、財務成果 | 獲利說明頁、收益展示頁、投資回報頁 | 警告頁、技術頁、問題頁 |
| IP_55_thumbs_down | 豎起拇指向下，表情搖頭 | disapproving / cautionary | 不建議、錯誤做法、這樣不行、踩雷、別學 | 錯誤示範頁、避雷指南、反例說明頁 | 成功頁、慶祝頁、開場頁 |
| IP_56_reading_glasses | 戴上眼鏡仔細看文件，表情嚴謹 | meticulous / scrutinizing | 細讀、條款、合約、仔細看、注意細節 | 合約說明頁、條款提醒頁、注意事項頁 | 輕鬆頁、慶祝頁 |
| IP_57_back_to_back | 背對背站立，旁邊有競品人物（示意）| competitive / differentiated | 對比、競品、差異化、為什麼選我、PK | 競品比較頁、差異化說明頁、選擇理由頁 | 合作夥伴頁、感謝頁 |
| IP_58_heart_hands | 雙手比出愛心形狀，笑容真誠 | loving / authentic | 熱愛、使命、初心、為什麼做這件事、情感 | 品牌故事頁、使命說明頁、情感連結區塊 | 技術頁、數據頁、警告頁 |
| IP_59_sit_crosslegged_casual | 盤腿坐在地上，輕鬆自然微笑 | casual / authentic | 輕鬆聊、真實、日常、幕後花絮、個人分享 | 個人故事頁、幕後頁、品牌文化過場 | 正式商務頁、技術展示頁 |
| IP_60_point_to_list | 指著浮空條列清單，引導閱讀 | structured / guiding | 條列、清單、三個重點、步驟、幾件事 | 重點整理頁、步驟說明頁、三大優勢區塊 | 情感頁、輕鬆過場頁 |
| IP_61_hands_up_excited | 雙手高舉歡呼，表情極度興奮 | ecstatic / celebratory | 突破、超標、爆發、今天很開心、太棒了 | 里程碑慶祝頁、超越目標頁、爆發性成果頁 | 沉靜頁、分析頁、警告頁 |
| IP_62_confused_shrug | 雙手攤開聳肩，一臉困惑 | confused / questioning | 不確定、到底、搞不懂、很多人問、為什麼 | 常見問題頁（Q 端）、疑惑引出頁 | 專業說明頁、成果頁 |
| IP_63_finger_snap | 手指輕彈，表情靈光一閃 | decisive / snappy | 就是這樣、對了、馬上、立刻、決定了 | 結論確認頁、快速決策頁、重點收斂頁 | 深度分析頁、長篇說明頁 |
| IP_64_lean_forward_desk | 身體前傾靠在桌上，認真看著鏡頭 | engaged / serious | 說真的、認真說、我要講重點、聽好了 | 嚴肅重點頁、核心訊息頁、強調轉折頁 | 輕鬆頁、慶祝頁 |
| IP_65_walk_and_talk | 邊走邊說話，表情自信從容 | dynamic / thought-leadership | 領導力、思維、觀點、邊走邊談、日常智慧 | Thought Leadership 頁、個人觀點分享 | 靜態分析頁、數據頁 |
| IP_66_back_view_horizon | 背影望向遠方地平線，充滿期待 | visionary / aspirational | 願景、未來、藍圖、我想帶你去的地方 | 願景頁、品牌使命收尾、長期規劃頁 | 警告頁、數據頁、過場頁 |
| IP_67_sit_think_outdoors | 戶外坐著望向遠方，若有所思 | reflective / free | 思考、自由、創業、人生、選擇、方向 | 個人故事頁、職涯轉換頁、生活方式品牌 | 技術頁、數據頁 |
| IP_68_present_two_options | 雙手各持一個選項圖示，引導選擇 | offering / comparative | 選哪個、A or B、方案一、方案二、怎麼選 | 方案選擇頁、套餐比較頁、決策引導頁 | 單一結論頁、感謝頁 |
| IP_69_wink_point | 眨眼並指向旁邊，表情俏皮 | playful / insider | 小提示、你知道嗎、順帶一提、彩蛋 | 彩蛋資訊頁、輕量 Pro tip、幽默補充說明 | 嚴肅警告頁、正式商務頁 |
| IP_70_cross_arms_skeptical | 雙手交叉，眉頭微皺表示質疑 | skeptical / challenging | 真的嗎、值得懷疑、你確定、反思、挑戰假設 | 批判性思考頁、挑戰現狀區塊、問題深挖頁 | 歡迎頁、慶祝頁 |
| IP_71_sit_interview | 坐姿受訪姿態，輕鬆自信說話 | candid / storytelling | 訪談、故事、分享、我的經歷、案例故事 | 案例故事頁、創辦人訪談、客戶見證引言 | 技術說明頁、數據頁 |
| IP_72_carry_stack_books | 雙手抱著一疊書籍，表情認真 | knowledgeable / studious | 知識、學習、備考、資料、準備、充電 | 課程說明頁、知識型內容開場、資源推薦頁 | 輕鬆頁、CTA 行動頁 |
| IP_73_phone_selfie | 拿手機自拍，笑容親切自然 | relatable / social | 社群、IG、打卡、個人動態、幕後、生活感 | IG 貼文配圖、社群幕後頁、個人品牌輕量頁 | 正式商務頁、技術頁 |
| IP_74_give_document | 雙手遞出文件，表情誠懇 | delivering / professional | 提案、報告、遞交、合約、文件說明 | 提案遞送頁、文件說明區塊、報告呈現頁 | 輕鬆頁、慶祝頁 |
| IP_75_celebrate_confetti | 站在彩帶飛舞中，雙手高舉慶祝 | joyful / festive | 慶祝、周年、活動、節日、紀念、特別日子 | 活動慶祝頁、周年感謝頁、節日特輯頁 | 嚴肅頁、技術頁、警告頁 |
| IP_76_draw_mindmap | 在空中繪製心智圖，表情投入 | creative / mapping | 心智圖、思維發散、架構規劃、腦力激盪 | 規劃框架頁、思維導圖說明、策略地圖 | 結論頁、輕鬆頁 |
| IP_77_nod_agreement | 點頭微笑，表情認同 | agreeable / validating | 我懂、你說得對、確實如此、感同身受 | 共鳴段落、客戶痛點認同頁、共情區塊 | 強烈 CTA 頁、技術頁 |
| IP_78_money_calculator | 操作計算機，表情認真計算 | calculated / financial | 計算、成本、預算、報酬、數字、財務規劃 | 費用說明頁、ROI 計算頁、財務分析頁 | 輕鬆頁、情感頁 |
| IP_79_stand_arms_behind | 雙手背在身後，表情從容自信 | composed / leader | 領導者、沉穩、自信、掌控全局、專家感 | 個人品牌強調頁、專家形象頁、Authority 頁 | 輕鬆頁、社群幕後頁 |
| IP_80_hand_on_chin_listen | 手托下巴，側耳傾聽，表情專注 | empathetic / listening | 傾聽、理解你、我明白、用戶聲音、需求 | 客戶需求頁、共情說明、服務態度展示頁 | 行動頁、數據頁 |
| IP_81_staircase_climb | 一步步走上階梯，表情堅定 | progressive / persevering | 進步、成長、一步一步、長期、慢慢來 | 學習歷程頁、長期策略頁、成長曲線說明 | 快速成功頁、輕鬆頁 |
| IP_82_open_laptop_new | 打開全新筆電，表情期待興奮 | new beginning / fresh start | 開始、新專案、啟動、第一天、全新出發 | 新課程開場頁、新產品發布頁、重新出發頁 | 結論頁、感謝頁 |
| IP_83_virtual_meeting_host | 主持線上會議，多視窗環繞 | leading / coordinating | 主持、會議、線上、協作、帶領、統籌 | 線上課程主持頁、會議說明頁、工作坊介紹 | 個人故事頁、輕鬆頁 |
| IP_84_receive_feedback | 手持反饋表單，表情開放接受 | receptive / growth-minded | 回饋、意見、建議、學員心聲、評價 | 學員回饋頁、評價展示區塊、持續改進頁 | 技術頁、警告頁 |
| IP_85_read_roadmap | 展開長型路線圖卷軸，認真閱讀 | strategic / long-term | 路線圖、Roadmap、計畫、時間線、規劃 | 產品路線圖頁、長期計畫說明頁、時間軸頁 | 輕鬆頁、感謝頁 |
| IP_86_teach_small_group | 對著小組學員解說，氛圍熱絡 | mentoring / community | 教學、帶領、輔導、社群、一起成長、陪伴 | 課程社群頁、教練方案說明、學習社群介紹 | 技術頁、個人品牌頁 |
| IP_87_data_dashboard | 站在多螢幕數據儀表板前，指著數字 | data-driven / analytical | 數據看板、Dashboard、監控、指標追蹤 | 數據分析頁、績效監控說明、指標儀表頁 | 情感頁、輕鬆頁 |
| IP_88_journal_writing | 坐著在實體筆記本上書寫，沉靜投入 | reflective / personal | 日記、紀錄、覆盤、個人反思、每日習慣 | 個人成長頁、習慣建立頁、覆盤說明頁 | 技術展示頁、行動 CTA 頁 |
| IP_89_ai_robot_interact | 與 AI 機器人圖示互動，表情好奇 | curious / innovative | AI 工具、ChatGPT、自動化、AI 協作 | AI 工具介紹頁、自動化說明頁、科技應用頁 | 傳統商務頁、感謝頁 |
| IP_90_hand_gift_box | 雙手捧出禮盒，表情真誠 | generous / gifting | 贈品、禮物、免費資源、額外福利、附贈 | 贈品說明頁、加碼福利頁、免費資源提供頁 | 警告頁、技術頁 |
| IP_91_countdown_fingers | 用手指倒數（3-2-1），表情期待 | anticipating / counting-down | 倒數、即將、準備好了嗎、快開始了 | 活動倒數頁、發布前預告、課程開始前頁 | 結論頁、感謝頁 |
| IP_92_explain_with_props | 手持小道具模型解釋，表情生動 | illustrative / engaging | 舉例、比喻、道具、這就像、讓我解釋 | 比喻說明頁、概念解釋頁、生動教學區塊 | 嚴肅技術頁、數據頁 |
| IP_93_look_down_empathy | 俯視低頭，表情充滿同理心 | empathetic / compassionate | 我知道很難、辛苦了、不容易、陪伴 | 情感共鳴開場、痛點共情段落、安慰區塊 | 成功慶祝頁、技術頁 |
| IP_94_two_thumbs_up | 雙手比出大拇指，笑容滿面 | strongly approving / enthusiastic | 強推、超讚、大力推薦、完全支持、5星 | 強力推薦頁、口碑區塊、超高評價頁 | 警告頁、問題頁 |
| IP_95_hold_speech_notes | 手持演講稿，整理思路中 | prepared / professional | 準備好了、今天要講、主題是、提綱 | 演講開場準備頁、議程說明頁、主題引入 | 輕鬆頁、社群幕後頁 |
| IP_96_point_self | 用手指指著自己，表情自信 | self-referencing / first-person | 我、我的方法、我的故事、我親身經歷 | 個人見證頁、創辦人故事頁、第一人稱說明 | 客觀分析頁、數據頁 |
| IP_97_stand_cityscape | 站在城市天際線前，表情意氣風發 | ambitious / big-picture | 格局、市場、宏觀、城市、商業版圖 | 市場規模頁、商業願景頁、宏觀布局說明 | 輕鬆頁、個人日常頁 |
| IP_98_unbox_product | 打開產品箱子，表情驚喜期待 | excited / unveiling | 開箱、新品、發布、揭曉、來了 | 新品發布頁、課程揭曉頁、功能開箱頁 | 感謝頁、分析頁 |
| IP_99_question_marks_surround | 被問號圍繞，表情困惑但微笑 | questioning / curious | 常見問題、FAQ、你可能在想、問題集 | FAQ 頁、問題集說明、疑惑解答引入頁 | 成功頁、CTA 頁 |
| IP_100_final_bow_spotlight | 站在聚光燈下，深深一鞠躬，謝幕姿態 | graceful / closing | 謝謝、再見、完結、感謝全程陪伴、圓滿 | 最終結語頁、課程完結頁、感謝所有人頁 | 開場頁、行動頁、警告頁 |

---

## AI 配圖使用指南

```
當頁面內容包含 trigger_keywords 中的關鍵詞時，優先選用對應 id 的圖片。
若有多張符合，以 mood 與整體頁面情緒基調做最終判斷。
負面排除：若頁面類型符合 negative_use，即使 trigger_keywords 匹配，也應避免選用。
```

---
*版本：2.0 ｜ 總數：100 組 ｜ 最後更新：2026*
