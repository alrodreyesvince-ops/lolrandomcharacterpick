import json
import re
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

OUTPUT_PATH = Path("data/builds.json")

CHAMPIONS = [
    {"name_en": "Ahri", "name_ja": "アーリ", "slug": "ahri", "lane": "mid", "lane_ja": "MID"},
    {"name_en": "Jinx", "name_ja": "ジンクス", "slug": "jinx", "lane": "adc", "lane_ja": "ADC"},
    {"name_en": "Thresh", "name_ja": "スレッシュ", "slug": "thresh", "lane": "support", "lane_ja": "SUP"},
]

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8"
}

DDRAGON_VERSION_URL = "https://ddragon.leagueoflegends.com/api/versions.json"


def get_latest_ddragon_version():
    res = requests.get(DDRAGON_VERSION_URL, headers=HEADERS, timeout=20)
    res.raise_for_status()
    return res.json()[0]


def get_item_name_map(version):
    url = f"https://ddragon.leagueoflegends.com/cdn/{version}/data/ja_JP/item.json"
    res = requests.get(url, headers=HEADERS, timeout=20)
    res.raise_for_status()
    data = res.json()["data"]

    item_map = {}
    for item_id, item_data in data.items():
        item_map[str(item_id)] = item_data["name"]

    return item_map


def fetch_ugg_page(champion):
    url = f"https://u.gg/lol/champions/{champion['slug']}/build/{champion['lane']}"
    res = requests.get(url, headers=HEADERS, timeout=30)
    res.raise_for_status()
    return url, res.text


def extract_stats(text):
    win_rate = None
    pick_rate = None
    ban_rate = None

    patterns = {
        "win_rate": r"Win Rate\\s*([0-9.]+%)",
        "pick_rate": r"Pick Rate\\s*([0-9.]+%)",
        "ban_rate": r"Ban Rate\\s*([0-9.]+%)",
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            if key == "win_rate":
                win_rate = match.group(1)
            elif key == "pick_rate":
                pick_rate = match.group(1)
            elif key == "ban_rate":
                ban_rate = match.group(1)

    return win_rate, pick_rate, ban_rate


def find_item_ids_from_html(html):
    found = []

    patterns = [
        r'"itemId"\\s*:\\s*(\\d+)',
        r'"item_id"\\s*:\\s*(\\d+)',
        r'"id"\\s*:\\s*(\\d{4})',
    ]

    for pattern in patterns:
        for match in re.findall(pattern, html):
            item_id = str(match)
            if item_id not in found:
                found.append(item_id)

    filtered = []
    for item_id in found:
        if len(item_id) == 4 and item_id not in filtered:
            filtered.append(item_id)

    return filtered[:6]


def make_fallback_build(champion):
    lane = champion["lane"]

    if lane == "mid":
        return {
            "name": "U.GG取得テストビルド",
            "items": ["ルーデン コンパニオン", "シャドウフレイム", "ラバドン デスキャップ"],
            "runes": ["電撃", "血の味わい", "目玉コレクター"],
            "skills": "Q → W → E"
        }

    if lane == "adc":
        return {
            "name": "U.GG取得テストビルド",
            "items": ["クラーケン スレイヤー", "ルナーン ハリケーン", "インフィニティ エッジ"],
            "runes": ["リーサルテンポ", "冷静沈着", "レジェンド: 血脈"],
            "skills": "Q → W → E"
        }

    return {
        "name": "U.GG取得テストビルド",
        "items": ["ソラリのロケット", "騎士の誓い", "リデンプション"],
        "runes": ["アフターショック", "生命の泉", "ボーンアーマー"],
        "skills": "Q → E → W"
    }


def make_build_from_ugg(item_ids, item_map, champion):
    items = []

    for item_id in item_ids:
        if item_id in item_map:
            item_name = item_map[item_id]
            if item_name not in items:
                items.append(item_name)

    if len(items) < 3:
        return make_fallback_build(champion)

    return {
        "name": "U.GG自動取得ビルド",
        "items": items[:6],
        "runes": make_fallback_build(champion)["runes"],
        "skills": make_fallback_build(champion)["skills"]
    }


def main():
    version = get_latest_ddragon_version()
    item_map = get_item_name_map(version)

    champions_data = []

    for champion in CHAMPIONS:
        try:
            url, html = fetch_ugg_page(champion)

            soup = BeautifulSoup(html, "html.parser")
            text = soup.get_text(" ", strip=True)

            win_rate, pick_rate, ban_rate = extract_stats(text)
            item_ids = find_item_ids_from_html(html)
            build = make_build_from_ugg(item_ids, item_map, champion)

            champions_data.append({
                "name_ja": champion["name_ja"],
                "name_en": champion["name_en"],
                "lane": champion["lane_ja"],
                "tier": "strong" if win_rate else "unknown",
                "source_url": url,
                "stats": {
                    "win_rate": win_rate,
                    "pick_rate": pick_rate,
                    "ban_rate": ban_rate
                },
                "builds": [build]
            })

            print(f"OK: {champion['name_en']} / items: {build['items']}")

        except Exception as e:
            print(f"FAILED: {champion['name_en']} - {e}")

    data = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "source": "ugg-test",
        "ddragon_version": version,
        "note": "U.GG取得テスト版。アイテム取得に失敗した場合はフォールバックビルドを使用。",
        "champions": champions_data
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("builds.json updated")


if __name__ == "__main__":
    main()
