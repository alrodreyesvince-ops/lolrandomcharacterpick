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


def normalize_name(value):
    return str(value or "").lower().replace("’", "'").replace("'", "").replace(".", "").replace(",", "").replace(" ", "").replace("-", "").replace(":", "")


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


def get_data_maps(version):
    item_en = get_json(f"https://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/item.json")["data"]
    item_ja = get_json(f"https://ddragon.leagueoflegends.com/cdn/{version}/data/ja_JP/item.json")["data"]
    summ_en = get_json(f"https://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/summoner.json")["data"]
    summ_ja = get_json(f"https://ddragon.leagueoflegends.com/cdn/{version}/data/ja_JP/summoner.json")["data"]
    runes_en = get_json(f"https://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/runesReforged.json")
    runes_ja = get_json(f"https://ddragon.leagueoflegends.com/cdn/{version}/data/ja_JP/runesReforged.json")

    item_by_en = {}
    item_by_ja = {}
    for item_id, item in item_en.items():
        ja_name = item_ja.get(item_id, {}).get("name", item["name"])
        obj = {"id": item_id, "name_en": item["name"], "name_ja": ja_name}
        item_by_en[normalize_name(item["name"])] = obj
        item_by_ja[normalize_name(ja_name)] = obj

    spell_by_en = {}
    spell_by_ja = {}
    for spell_key, spell in summ_en.items():
        ja_name = summ_ja.get(spell_key, {}).get("name", spell["name"])
        obj = {"id": spell_key, "name_en": spell["name"], "name_ja": ja_name}
        spell_by_en[normalize_name(spell["name"])] = obj
        spell_by_ja[normalize_name(ja_name)] = obj

    rune_by_en = {}
    rune_by_ja = {}
    for tree_en, tree_ja in zip(runes_en, runes_ja):
        tree_obj = {"id": str(tree_en["id"]), "name_en": tree_en["name"], "name_ja": tree_ja["name"]}
        rune_by_en[normalize_name(tree_en["name"])] = tree_obj
        rune_by_ja[normalize_name(tree_ja["name"])] = tree_obj
        for slot_index, slot in enumerate(tree_en["slots"]):
            ja_slot = tree_ja["slots"][slot_index]
            for rune_index, rune in enumerate(slot["runes"]):
                ja_rune = ja_slot["runes"][rune_index]
                obj = {"id": str(rune["id"]), "name_en": rune["name"], "name_ja": ja_rune["name"]}
                rune_by_en[normalize_name(rune["name"])] = obj
                rune_by_ja[normalize_name(ja_rune["name"])] = obj

    return item_by_en, item_by_ja, rune_by_en, rune_by_ja, spell_by_en, spell_by_ja


def lanes_for_champion(champ):
    champ_id = champ["id"]
    lanes = [lane for lane, ids in MAIN_LANES.items() if champ_id in ids]
    if lanes:
        return lanes

    tags = set(champ.get("tags", []))
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
    # 日本語ページの方が検索テキストに勝率・ピック率などが出やすい
    url = f"https://u.gg/lol/ja_jp/champions/{champ_slug}/build/{lane_key}"
    res = requests.get(url, headers=HEADERS, timeout=35)
    if res.status_code != 200:
        return url, None
    return url, res.text


def extract_stats(text):
    def find_jp(label):
        m = re.search(label + r"\s*([0-9.]+%)", text, re.IGNORECASE)
        return m.group(1) if m else None

    def find_en(label):
        m = re.search(label + r"\s*([0-9.]+%)", text, re.IGNORECASE)
        return m.group(1) if m else None

    return {
        "win_rate": find_jp("勝率") or find_en("Win Rate"),
        "pick_rate": find_jp("ピックレート") or find_en("Pick Rate"),
        "ban_rate": find_jp("BAN率") or find_en("Ban Rate"),
    }


def extract_image_names(soup, text):
    names = []

    for img in soup.find_all("img"):
        for attr in ["alt", "title", "aria-label"]:
            value = img.get(attr)
            if value:
                value = re.sub(r"^Image:\s*", "", value).strip()
                if value and value not in names:
                    names.append(value)

    for m in re.findall(r"Image:\s*([^\n|]+?)(?=\s+Image:|\s+トップ|\s+ジャングル|\s+ミッド|\s+ボット|\s+サポート|$)", text):
        value = m.strip()
        if value and value not in names:
            names.append(value)

    return names


def classify_names(names, maps):
    item_by_en, item_by_ja, rune_by_en, rune_by_ja, spell_by_en, spell_by_ja = maps
    items = []
    runes = []
    spells = []

    def add_unique(arr, value):
        if value and value not in arr:
            arr.append(value)

    for raw in names:
        key = normalize_name(raw)

        item = item_by_en.get(key) or item_by_ja.get(key)
        if item:
            add_unique(items, item["name_ja"])
            continue

        rune = rune_by_en.get(key) or rune_by_ja.get(key)
        if rune:
            add_unique(runes, rune["name_ja"])
            continue

        spell = spell_by_en.get(key) or spell_by_ja.get(key)
        if spell:
            add_unique(spells, spell["name_ja"])
            continue

    # U.GGの画像列には重複や候補アイテムが混ざるため、上から実用範囲で切る
    return items[:6], runes[:9], spells[:2]


def extract_skill_order(text):
    # U.GGページに "Q W E" のような形で出る場合を拾う
    patterns = [
        r"Skill Priority\s*([QWER]\s*[>→]\s*[QWER]\s*[>→]\s*[QWER])",
        r"スキル優先\s*([QWER]\s*[>→]\s*[QWER]\s*[>→]\s*[QWER])",
        r"([QWER]\s*[>→]\s*[QWER]\s*[>→]\s*[QWER])",
    ]
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            order = m.group(1).replace(">", "→")
            order = re.sub(r"\s+", " ", order)
            return order.strip()
    return None


def fallback_build(lane_label):
    if lane_label == "TOP":
        return {"name": "フォールバックTOPビルド", "items": ["サンダード スカイ", "ブラック クリーバー", "ステラックの篭手", "デス ダンス", "スピリット ビサージュ"], "runes": ["征服者", "凱旋", "背水の陣"], "skills": "主力スキル優先", "spells": ["フラッシュ", "テレポート"]}
    if lane_label == "JG":
        return {"name": "フォールバックJGビルド", "items": ["赤月の刃", "ブラック クリーバー", "サンダード スカイ", "デス ダンス", "ガーディアン エンジェル"], "runes": ["征服者", "凱旋", "宇宙の英知"], "skills": "ファームスキル優先", "spells": ["フラッシュ", "スマイト"]}
    if lane_label == "MID":
        return {"name": "フォールバックMIDビルド", "items": ["ルーデン コンパニオン", "シャドウフレイム", "ゾーニャの砂時計", "ラバドン デスキャップ", "ヴォイド スタッフ"], "runes": ["電撃", "血の味わい", "目玉コレクター"], "skills": "主力ダメージスキル優先", "spells": ["フラッシュ", "イグナイト"]}
    if lane_label == "ADC":
        return {"name": "フォールバックADCビルド", "items": ["クラーケン スレイヤー", "ルナーン ハリケーン", "インフィニティ エッジ", "ドミニク リガード", "ガーディアン エンジェル"], "runes": ["リーサルテンポ", "冷静沈着", "レジェンド: 血脈"], "skills": "主力攻撃スキル優先", "spells": ["フラッシュ", "ヒール"]}
    return {"name": "フォールバックSUPビルド", "items": ["ソラリのロケット", "騎士の誓い", "リデンプション", "ミカエルの祝福", "ジーク コンバージェンス"], "runes": ["アフターショック", "生命の泉", "ボーンアーマー"], "skills": "CC・補助スキル優先", "spells": ["フラッシュ", "イグナイト"]}


def make_build(items, runes, spells, skill_order, lane_label):
    build = fallback_build(lane_label)
    got_any = False

    if len(items) >= 3:
        build["items"] = items[:6]
        got_any = True

    if len(runes) >= 3:
        build["runes"] = runes[:9]
        got_any = True

    if len(spells) >= 2:
        build["spells"] = spells[:2]
        got_any = True

    if skill_order:
        build["skills"] = skill_order
        got_any = True

    build["name"] = "U.GG自動取得ビルド" if got_any else "フォールバックビルド"
    return build


def main():
    version = get_latest_version()
    champions = get_champions(version)
    maps = get_data_maps(version)

    results = []
    fetch_count = 0
    total_targets = sum(len(lanes_for_champion(champ)) for champ in champions)
    print(f"Target pages: {total_targets}")

    for champ in champions:
        for lane_label in lanes_for_champion(champ):
            fetch_count += 1
            lane_key = LANES[lane_label]
            print(f"[{fetch_count}/{total_targets}] {champ['name_en']} {lane_label}")

            source_url = f"https://u.gg/lol/ja_jp/champions/{champ['slug']}/build/{lane_key}"
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
                    image_names = extract_image_names(soup, text)
                    items, runes, spells = classify_names(image_names, maps)
                    skill_order = extract_skill_order(text)
                    build = make_build(items, runes, spells, skill_order, lane_label)
                    print(f"  items={len(items)} runes={len(runes)} spells={len(spells)} stats={stats}")
                else:
                    print(f"  SKIP HTML: {champ['name_en']} {lane_label}")
            except Exception as e:
                print(f"  FAILED: {champ['name_en']} {lane_label} - {e}")

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

            time.sleep(0.45)

    data = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "source": "ugg-main-lanes-detailed-v2",
        "ddragon_version": version,
        "total_entries": len(results),
        "note": "U.GG日本語ページから統計・画像altを解析し、Data Dragonでアイテム/ルーン/サモナースペル名に変換。取得失敗時はフォールバックビルドを使用。",
        "champions": results,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"builds.json updated: {len(results)} entries")


if __name__ == "__main__":
    main()
