import asyncio
import edge_tts
from pathlib import Path

OUT = Path(__file__).parent / "assets" / "narration"
OUT.mkdir(parents=True, exist_ok=True)

VOICE = "zh-TW-YunJheNeural"
RATE = "-10%"
PITCH = "-2Hz"

SCRIPT = [
    (1,  "AI Agent——人工智慧代理。你今天已經用它好幾次了，只是你不知道。"),
    (2,  "你有沒有想過，掃地機器人怎麼知道哪裡掃過了？Netflix 怎麼知道你想看什麼？這不是魔法，是 AI Agent。"),
    (3,  "AI Agent，中文叫人工智慧代理，是一種能感知環境、做出決策、然後採取行動的程式。"),
    (4,  "所有 AI Agent 都遵循同一個循環：感知——用感測器接收資訊；決策——用邏輯判斷下一步；行動——執行動作改變環境。"),
    (5,  "AI Agent 有三種型態，從簡單到複雜。它們的差別在於——腦袋裡裝了多少資訊。"),
    (6,  "第一種：反射型 Agent。它只看當下，不記過去。就像恆溫器——太冷就開暖氣，太熱就關。簡單、快速、可靠。"),
    (7,  "第二種：基於模型型 Agent。它會記住過去的狀態。掃地機器人就是這樣——它記得哪裡掃過了、哪裡還沒掃，不會在同一個地方繞圈。"),
    (8,  "第三種：目標導向型 Agent。它不只記住過去，還會規劃未來。自動駕駛汽車就是最好的例子——它知道要去哪裡，會根據路況即時調整路線。"),
    (9,  "AI Agent 不是 ChatGPT——ChatGPT 是語言模型，不是一個完整的 agent。AI Agent 也不一定要很複雜，最簡單的恆溫器就是一種 agent。"),
    (10, "從 Google 地圖導航、YouTube 推薦影片、到智慧音箱——你身邊到處都是 AI Agent。只是它們藏得太好了。"),
    (11, "AI Agent = 能感知、能決策、能行動。這三個能力加起來，就是人工智慧代理的全部。"),
    (12, "下次打開掃地機器人、或讓 Google 地圖帶你回家——想想它背後的那個 agent。它正在看、在想、在行動。"),
]

async def synth(i, text):
    out = OUT / f"page-{i:02d}.mp3"
    communicate = edge_tts.Communicate(text, VOICE, rate=RATE, pitch=PITCH)
    await communicate.save(str(out))
    print(f"OK page-{i:02d}.mp3")

async def main():
    for i, t in SCRIPT:
        for attempt in range(3):
            try:
                await synth(i, t)
                break
            except Exception as e:
                print(f"retry {i} ({attempt+1}): {e}")
                await asyncio.sleep(2)
    print("All done.")

if __name__ == "__main__":
    asyncio.run(main())
