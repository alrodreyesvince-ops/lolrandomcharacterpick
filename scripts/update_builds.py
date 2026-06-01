import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

OUTPUT_PATH = Path("data/builds.json")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36",
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
}

DD_VERSION_URL = "https://ddragon.leagueoflegends.com/api/versions.json"

LANES = {
    "TOP": "top",
    "JG": "jungle",
    "MID": "mid",
    "ADC": "adc",
    "SUP": "support",
}

# U.GGのURL用に特殊な名前だけ調整
SLUG_OVERRIDES = {
    "AurelionSol": "aurelionsol",
    "Belveth": "belveth",
    "Chogath": "chogath",
    "DrMundo": "drmundo",
    "JarvanIV": "jarvaniv",
    "Kaisa": "kaisa",
    "Khazix": "khazix",
    "KogMaw": "kogmaw",
    "KSante": "ksante",
    "Leblanc": "leblanc",
    "LeeSin": "leesin",
    "MasterYi": "masteryi",
    "MissFortune": "missfortune",
    "MonkeyKing": "wukong",
    "Nunu": "nunu",
    "RekSai": "reksai",
    "TahmKench": "tahmkench",
    "TwistedFate": "twistedfate",
    "Velkoz": "velkoz",
    "XinZhao": "xinzhao",
}

# 主要レーン表。ここにあるチャンピオンだけ、そのレーンで取得します。
# 新チャンピオンなど表にない場合は Data Dragon のタグから自動で1レーン割り当てます。
MAIN_LANES = {
    "TOP": [
        "Aatrox", "Akali", "Ambessa", "Camille", "Chogath", "Darius", "DrMundo", "Fiora", "Gangplank",
        "Garen", "Gnar", "Gragas", "Gwen", "Heimerdinger", "Illaoi", "Irelia", "Jax", "Jayce", "Kayle",
        "Kennen", "Kled", "KSante", "Malphite", "Maokai", "Mordekaiser", "Nasus", "Olaf", "Ornn", "Pantheon",
        "Poppy", "Quinn", "Renekton", "Rengar", "Riven", "Rumble", "Ryze", "Sett", "Shen", "Singed", "Sion",
        "TahmKench", "Teemo", "Trundle", "Tryndamere", "Udyr", "Urgot", "Vayne", "Vladimir", "Volibear",
        "Warwick", "MonkeyKing", "Yasuo", "Yone", "Yorick", "Zac"
    ],
    "JG": [
        "Amumu", "Belveth", "Brand", "Briar", "Diana", "DrMundo", "Ekko", "Elise", "Evelynn", "Fiddlesticks",
        "Gragas", "Graves", "Gwen", "Hecarim", "Ivern", "JarvanIV", "Jax", "Karthus", "Kayn", "Khazix",
        "Kindred", "LeeSin", "Lillia", "Maokai", "MasterYi", "MonkeyKing", "Mordekaiser", "Morgana", "Naafiri",
        "Nidalee", "Nocturne", "Nunu", "Olaf", "Pantheon", "Poppy", "Qiyana", "Rammus", "RekSai", "Rengar",
        "Sejuani", "Shaco", "Shyvana", "Skarner", "Taliyah", "Talon", "Trundle", "Udyr", "Vi", "Viego",
        "Volibear", "Warwick", "XinZhao", "Zac", "Zed", "Zyra"
    ],
    "MID": [
        "Ahri", "Akali", "Akshan", "Ambessa", "Anivia", "Annie", "AurelionSol", "Aurora", "Azir", "Brand",
        "Cassiopeia", "Corki", "Diana", "Ekko", "Fizz", "Galio", "Hwei", "Irelia", "Jayce", "Kassadin",
        "Katarina", "Leblanc", "Lissandra", "Lux", "Malzahar", "Mel", "Naafiri", "Neeko", "Orianna", "Pantheon",
        "Qiyana", "Ryze", "Sylas", "Syndra", "Taliyah", "Talon", "Tristana", "TwistedFate", "Veigar", "Velkoz",
        "Vex", "Viktor", "Vladimir", "Xerath", "Yasuo", "Yone", "Zed", "Ziggs", "Zoe"
    ],
    "ADC": [
        "Aphelios", "Ashe", "Caitlyn", "Draven", "Ezreal", "Jhin", "Jinx", "Kaisa", "Kalista", "KogMaw",
        "Lucian", "MissFortune", "Nilah", "Samira", "Senna", "Sivir", "Smolder", "Tristana", "Twitch", "Varus",
        "Vayne", "Xayah", "Yasuo", "Zeri", "Ziggs"
    ],
    "SUP": [
        "Alistar", "Amumu", "Annie", "Ashe", "Bard", "Blitzcrank", "Brand", "Braum", "Camille", "Fiddlesticks",
        "Heimerdinger", "Janna", "Karma", "Leona", "Lulu", "Lux", "Maokai", "Milio", "Morgana", "Nami",
        "Nautilus", "Neeko", "Pantheon", "Poppy", "Pyke", "Rakan", "Rell", "Renata", "Senna", "Seraphine",
        "Shaco", "Sona", "Soraka", "Swain", "TahmKench", "Taric", "Thresh", "Velkoz", "Xerath", "Yuumi",
        "Zilean", "Zyra"
    ],
}

STRONG_BY_LANE = {
    "TOP": ["Aatrox", "Ambessa", "Camille", "Darius", "Fiora", "Garen", "Gwen", "Jax", "KSante", "Malphite", "Mordekaiser", "Renekton", "Rumble", "Sett", "Yone"],
    "JG": ["Belveth", "Briar", "Diana", "Ekko", "Graves", "JarvanIV", "Kayn", "Khazix", "LeeSin", "Lillia", "Nocturne", "Viego", "Vi", "XinZhao"],
    "MID": ["Ahri", "Akali", "AurelionSol", "Aurora", "Hwei", "Leblanc", "Orianna", "Sylas", "Syndra", "Taliyah", "Vex", "Viktor", "Yone"],
    "ADC": ["Ashe", "Caitlyn", "Ezreal", "Jhin", "Jinx", "Kaisa", "Lucian", "MissFortune", "Varus", "Xayah", "Zeri"],
    "SUP": ["Bard", "Blitzcrank", "Janna", "Karma", "Leona", "Lulu", "Milio", "Nami", "Nautilus", "Pyke", "Rakan", "Rell", "Thresh"],
}


def get_json(url):
    res = requests.get(url, headers=HEADERS, timeout=30)
    res.raise_for_status()
    return res.json()


def get_latest_version():
    return get_json(DD_VERSION_URL)[0]


def get_champions(version):
    en = get_json(f"https://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/champion.json")
    ja = get_json(f"https://ddragon.leagueoflegends.com/cdn/{version}/data/ja_JP/champion.json")

    champions = []
    for champ_id, champ in en["data"].items():
        champions.append({
            "id": champ_id,
            "name_en": champ["name"],
            "name_ja": ja["data"].get(champ_id, {}).get("name", champ["name"]),
            "slug": SLUG_OVERRIDES.get(champ_id, champ_id.lower()),
            "tags": champ.get("tags", []),
        })
    return champions


def get_item_map(version):
    data = get_json(f"https://ddragon.leagueoflegends.com/cdn/{version}/data/ja_JP/item.json")["data"]
    return {str(item_id): item["name"] for item_id, item in data.items()}


def lanes_for_champion(champ):
    champ_id = champ["id"]
    lanes = [lane for lane, ids in MAIN_LANES.items() if champ_id in ids]

    if lanes:
        return lanes

    tags = set(champ.get("tags", []))

    # 表にない新チャンピオン向けの最低限フォールバック
    if "Marksman" in tags:
        return ["ADC"]
    if "Support" in tags:
        return ["SUP"]
    if "Mage" in tags:
        return ["MID"]
    if "Assassin" in tags:
        return ["MID"]
    if "Tank" in tags:
        return ["TOP"]
    if "Fighter" in tags:
        return ["TOP"]

    return ["MID"]


def fetch_ugg(champ_slug, lane_key):
    url = f"https://u.gg/lol/champions/{champ_slug}/build/{lane_key}"
    res = requests.get(url, headers=HEADERS, timeout=30)
    if res.status_code != 200:
        return url, None
    return url, res.text


def extract_stats(text):
    def find(label):
        match = re.search(label + r"\s*([0-9.]+%)", text, re.IGNORECASE)
        return match.group(1) if match else None

    return {
        "win_rate": find("Win Rate"),
        "pick_rate": find("Pick Rate"),
        "ban_rate": find("Ban Rate"),
    }


def extract_item_ids(html):
    found = []
    patterns = [
        r'"itemId"\s*:\s*(\d+)',
        r'"item_id"\s*:\s*(\d+)',
        r'"id"\s*:\s*(\d{4})',
        r'/img/item/(\d+)\.png',
        r'/cdn/.+?/img/item/(\d+)\.png',
    ]

    for pattern in patterns:
        for item_id in re.findall(pattern, html):
            item_id = str(item_id)
            if len(item_id) == 4 and item_id not in found:
                found.append(item_id)

    return found[:6]


def fallback_build(lane_label):
    if lane_label == "TOP":
        return {
            "name": "フォールバックTOPビルド",
            "items": ["サンダード スカイ", "ブラック クリーバー", "ステラックの篭手"],
            "runes": ["征服者", "凱旋", "背水の陣"],
            "skills": "主力スキル優先",
        }

    if lane_label == "JG":
        return {
            "name": "フォールバックJGビルド",
            "items": ["赤月の刃", "ブラック クリーバー", "ガーディアン エンジェル"],
            "runes": ["征服者", "凱旋", "宇宙の英知"],
            "skills": "ファームスキル優先",
        }

    if lane_label == "MID":
        return {
            "name": "フォールバックMIDビルド",
            "items": ["ルーデン コンパニオン", "シャドウフレイム", "ラバドン デスキャップ"],
            "runes": ["電撃", "血の味わい", "目玉コレクター"],
            "skills": "主力ダメージスキル優先",
        }

    if lane_label == "ADC":
        return {
            "name": "フォールバックADCビルド",
            "items": ["クラーケン スレイヤー", "インフィニティ エッジ", "ドミニク リガード"],
            "runes": ["リーサルテンポ", "冷静沈着", "レジェンド: 血脈"],
            "skills": "主力攻撃スキル優先",
        }

    return {
        "name": "フォールバックSUPビルド",
        "items": ["ソラリのロケット", "騎士の誓い", "リデンプション"],
        "runes": ["アフターショック", "生命の泉", "ボーンアーマー"],
        "skills": "CC・補助スキル優先",
    }


def make_build(item_ids, item_map, lane_label):
    items = []
    for item_id in item_ids:
        name = item_map.get(item_id)
        if name and name not in items:
            items.append(name)

    build = fallback_build(lane_label)

    if len(items) >= 3:
        build["name"] = "U.GG自動取得ビルド"
        build["items"] = items[:6]
    else:
        build["name"] = "フォールバックビルド"

    return build


def main():
    version = get_latest_version()
    champions = get_champions(version)
    item_map = get_item_map(version)

    results = []
    fetch_count = 0

    total_targets = sum(len(lanes_for_champion(champ)) for champ in champions)
    print(f"Target pages: {total_targets}")

    for champ in champions:
        target_lanes = lanes_for_champion(champ)

        for lane_label in target_lanes:
            fetch_count += 1
            lane_key = LANES[lane_label]
            print(f"[{fetch_count}/{total_targets}] {champ['name_en']} {lane_label}")

            source_url = f"https://u.gg/lol/champions/{champ['slug']}/build/{lane_key}"
            stats = {"win_rate": None, "pick_rate": None, "ban_rate": None}
            build = fallback_build(lane_label)
            build["name"] = "フォールバックビルド"

            try:
                url, html = fetch_ugg(champ["slug"], lane_key)
                source_url = url

                if html:
                    soup = BeautifulSoup(html, "html.parser")
                    text = soup.get_text(" ", strip=True)
                    stats = extract_stats(text)
                    item_ids = extract_item_ids(html)
                    build = make_build(item_ids, item_map, lane_label)

                else:
                    print(f"SKIP HTML: {champ['name_en']} {lane_label}")

            except Exception as e:
                print(f"FAILED: {champ['name_en']} {lane_label} - {e}")

            results.append({
                "name_ja": champ["name_ja"],
                "name_en": champ["name_en"],
                "champion_id": champ["id"],
                "lane": lane_label,
                "tier": "strong" if champ["id"] in STRONG_BY_LANE.get(lane_label, []) else "normal",
                "source_url": source_url,
                "stats": stats,
                "builds": [build],
            })

            # アクセス制限対策。速くしすぎない。
            time.sleep(0.35)

    data = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "source": "ugg-main-lanes-all-champions",
        "ddragon_version": version,
        "total_entries": len(results),
        "note": "Data Dragonで全チャンピオン取得。各チャンピオンの主要レーンのみU.GGから取得。取得失敗時はフォールバックビルドを使用。",
        "champions": results,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"builds.json updated: {len(results)} entries")


if __name__ == "__main__":
    main()
