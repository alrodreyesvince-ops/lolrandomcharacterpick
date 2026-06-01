import json
import re
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

OUTPUT_PATH = Path("data/builds.json")

CHAMPIONS = [
    {"name_en": "Ahri", "name_ja": "アーリ", "slug": "ahri", "lane": "mid"},
    {"name_en": "Jinx", "name_ja": "ジンクス", "slug": "jinx", "lane": "bottom"},
    {"name_en": "Thresh", "name_ja": "スレッシュ", "slug": "thresh", "lane": "support"},
]

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def fetch_opgg_page(champion):
    url = f"https://op.gg/lol/champions/{champion['slug']}/build/{champion['lane']}"
    res = requests.get(url, headers=HEADERS, timeout=20)
    res.raise_for_status()
    return url, res.text

def extract_stats(text):
    win_rate = None
    pick_rate = None
    ban_rate = None

    win_match = re.search(r"Win rate\\s*([0-9.]+%)", text)
    pick_match = re.search(r"Pick rate\\s*([0-9.]+%)", text)
    ban_match = re.search(r"Ban rate\\s*([0-9.]+%)", text)

    if win_match:
        win_rate = win_match.group(1)
    if pick_match:
        pick_rate = pick_match.group(1)
    if ban_match:
        ban_rate = ban_match.group(1)

    return win_rate, pick_rate, ban_rate

def make_fallback_build(champion):
    lane = champion["lane"]

    if lane == "mid":
        items = ["ルーデン コンパニオン", "シャドウフレイム", "ラバドン デスキャップ"]
        runes = ["電撃", "血の味わい", "目玉コレクター"]
        skills = "Q → W → E"
    elif lane == "bottom":
        items = ["クラーケン スレイヤー", "ルナーン ハリケーン", "インフィニティ エッジ"]
        runes = ["リーサルテンポ", "冷静沈着", "レジェンド: 血脈"]
        skills = "Q → W → E"
    else:
        items = ["ソラリのロケット", "騎士の誓い", "リデンプション"]
        runes = ["アフターショック", "生命の泉", "ボーンアーマー"]
        skills = "Q → E → W"

    return {
        "name": "OP.GG取得テストビルド",
        "items": items,
        "runes": runes,
        "skills": skills
    }

def main():
    champions_data = []

    for champion in CHAMPIONS:
        try:
            url, html = fetch_opgg_page(champion)
            soup = BeautifulSoup(html, "html.parser")
            text = soup.get_text(" ", strip=True)

            win_rate, pick_rate, ban_rate = extract_stats(text)

            champions_data.append({
                "name_ja": champion["name_ja"],
                "name_en": champion["name_en"],
                "lane": champion["lane"].upper(),
                "tier": "strong" if win_rate else "unknown",
                "source_url": url,
                "stats": {
                    "win_rate": win_rate,
                    "pick_rate": pick_rate,
                    "ban_rate": ban_rate
                },
                "builds": [
                    make_fallback_build(champion)
                ]
            })

            print(f"OK: {champion['name_en']}")

        except Exception as e:
            print(f"FAILED: {champion['name_en']} - {e}")

    data = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "source": "opgg-test",
        "note": "OP.GGのページから勝率などを取得するテスト版。ビルド詳細は現在フォールバック値。",
        "champions": champions_data
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("builds.json updated")

if __name__ == "__main__":
    main()
