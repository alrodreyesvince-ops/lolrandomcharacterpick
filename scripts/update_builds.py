import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

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
        "Garen", "Gnar", "Gragas", "Gwen", "Illaoi", "Irelia", "Jax", "Jayce", "Kayle", "Kennen",
        "Kled", "KSante", "Malphite", "Maokai", "Mordekaiser", "Nasus", "Olaf", "Ornn", "Pantheon", "Poppy",
        "Quinn", "Renekton", "Riven", "Rumble", "Sett", "Shen", "Singed", "Sion", "TahmKench", "Teemo",
        "Trundle", "Tryndamere", "Udyr", "Urgot", "Vayne", "Vladimir", "Volibear", "Warwick", "MonkeyKing", "Yasuo",
        "Yone", "Yorick", "Zac"
    ],
    "JG": [
        "Amumu", "Belveth", "Brand", "Briar", "Diana", "DrMundo", "Ekko", "Elise", "Evelynn", "Fiddlesticks",
        "Gragas", "Graves", "Gwen", "Hecarim", "Ivern", "JarvanIV", "Jax", "Karthus", "Kayn", "Khazix",
        "Kindred", "LeeSin", "Lillia", "Maokai", "MasterYi", "MonkeyKing", "Mordekaiser", "Morgana", "Naafiri", "Nidalee",
        "Nocturne", "Nunu", "Olaf", "Pantheon", "Poppy", "Qiyana", "Rammus", "RekSai", "Rengar", "Sejuani",
        "Shaco", "Shyvana", "Skarner", "Taliyah", "Talon", "Trundle", "Udyr", "Vi", "Viego", "Volibear",
        "Warwick", "XinZhao", "Zac", "Zed", "Zyra"
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


def normalize(value):
    return re.sub(r"[^a-z0-9ぁ-んァ-ヶー一-龠]", "", str(value or "").lower())


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

    items = {}
    for item_id, item in item_en.items():
        ja_name = item_ja.get(item_id, {}).get("name", item["name"])
        obj = {"id": item_id, "name_en": item["name"], "name_ja": ja_name}
        items[normalize(item["name"])] = obj
        items[normalize(ja_name)] = obj

    spells = {}
    for key, spell in summ_en.items():
        ja_name = summ_ja.get(key, {}).get("name", spell["name"])
        obj = {"id": key, "name_en": spell["name"], "name_ja": ja_name}
        spells[normalize(spell["name"])] = obj
        spells[normalize(ja_name)] = obj

    runes = {}
    for tree_index, tree_en in enumerate(runes_en):
        tree_ja = runes_ja[tree_index]
        tree_obj = {"id": str(tree_en["id"]), "name_en": tree_en["name"], "name_ja": tree_ja["name"]}
        runes[normalize(tree_en["name"])] = tree_obj
        runes[normalize(tree_ja["name"])] = tree_obj
        for slot_index, slot_en in enumerate(tree_en["slots"]):
            slot_ja = tree_ja["slots"][slot_index]
            for rune_index, rune_en in enumerate(slot_en["runes"]):
                rune_ja = slot_ja["runes"][rune_index]
                obj = {"id": str(rune_en["id"]), "name_en": rune_en["name"], "name_ja": rune_ja["name"]}
                runes[normalize(rune_en["name"])] = obj
                runes[normalize(rune_ja["name"])] = obj
    return items, runes, spells


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
    if "Mage" in tags or "Assassin" in tags:
        return ["MID"]
    if "Tank" in tags or "Fighter" in tags:
        return ["TOP"]
    return ["MID"]


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


def first_percent_after(label, text):
    idx = text.lower().find(label.lower())
    if idx == -1:
        return None
    chunk = text[idx:idx + 120]
    m = re.search(r"([0-9]+(?:\.[0-9]+)?%)", chunk)
    return m.group(1) if m else None


def extract_stats(text):
    return {
        "win_rate": first_percent_after("Win Rate", text) or first_percent_after("勝率", text),
        "pick_rate": first_percent_after("Pick Rate", text) or first_percent_after("ピック", text),
        "ban_rate": first_percent_after("Ban Rate", text) or first_percent_after("BAN", text),
    }


def unique_append(arr, value):
    if value and value not in arr:
        arr.append(value)


def extract_names_from_page(page):
    names = []
    try:
        imgs = page.locator("img").evaluate_all("""
            imgs => imgs.map(img => img.alt || img.title || img.getAttribute('aria-label') || '').filter(Boolean)
        """)
        for name in imgs:
            clean = re.sub(r"^Image:\s*", "", str(name)).strip()
            unique_append(names, clean)
    except Exception:
        pass

    try:
        aria = page.locator("[aria-label]").evaluate_all("els => els.map(el => el.getAttribute('aria-label')).filter(Boolean)")
        for name in aria:
            clean = str(name).strip()
            unique_append(names, clean)
    except Exception:
        pass

    return names


def classify_names(names, maps):
    item_map, rune_map, spell_map = maps
    items, runes, spells = [], [], []
    for raw in names:
        key = normalize(raw)
        if key in item_map:
            unique_append(items, item_map[key]["name_ja"])
            continue
        if key in rune_map:
            unique_append(runes, rune_map[key]["name_ja"])
            continue
        if key in spell_map:
            unique_append(spells, spell_map[key]["name_ja"])
            continue
    return items[:6], runes[:9], spells[:2]


def extract_skill_order(text):
    patterns = [
        r"([QWER]\s*[>→]\s*[QWER]\s*[>→]\s*[QWER])",
        r"([QWER]\s+[QWER]\s+[QWER])",
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            order = m.group(1).upper().replace(">", "→")
            order = re.sub(r"\s+", " → ", order) if "→" not in order else re.sub(r"\s*→\s*", " → ", order)
            return order
    return None


def make_build(items, runes, spells, skills, lane_label):
    build = fallback_build(lane_label)
    got = False
    if len(items) >= 3:
        build["items"] = items[:6]
        got = True
    if len(runes) >= 3:
        build["runes"] = runes[:9]
        got = True
    if len(spells) >= 1:
        build["spells"] = spells[:2]
        got = True
    if skills:
        build["skills"] = skills
        got = True
    build["name"] = "U.GG自動取得ビルド" if got else "フォールバックビルド"
    return build


def fetch_one_with_playwright(page, champ, lane_label, maps):
    lane_key = LANES[lane_label]
    url = f"https://u.gg/lol/champions/{champ['slug']}/build/{lane_key}"

    stats = {"win_rate": None, "pick_rate": None, "ban_rate": None}
    build = fallback_build(lane_label)
    build["name"] = "フォールバックビルド"

    try:
        page.goto(url, wait_until="domcontentloaded", timeout=45000)
        try:
            page.wait_for_load_state("networkidle", timeout=12000)
        except PlaywrightTimeoutError:
            pass
        time.sleep(2.5)

        text = page.locator("body").inner_text(timeout=15000)
        stats = extract_stats(text)
        names = extract_names_from_page(page)
        items, runes, spells = classify_names(names, maps)
        skills = extract_skill_order(text)
        build = make_build(items, runes, spells, skills, lane_label)
        print(f"  got items={len(items)} runes={len(runes)} spells={len(spells)} stats={stats} build={build['name']}")
    except Exception as e:
        print(f"  PLAYWRIGHT FAILED: {champ['name_en']} {lane_label} - {e}")

    return url, stats, build


def main():
    version = get_latest_version()
    champions = get_champions(version)
    maps = get_data_maps(version)

    targets = []
    for champ in champions:
        for lane in lanes_for_champion(champ):
            targets.append((champ, lane))

    results = []
    print(f"Target pages: {len(targets)}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=HEADERS["User-Agent"],
            locale="ja-JP",
            viewport={"width": 1366, "height": 900},
        )
        page = context.new_page()

        for i, (champ, lane_label) in enumerate(targets, start=1):
            print(f"[{i}/{len(targets)}] {champ['name_en']} {lane_label}")
            source_url, stats, build = fetch_one_with_playwright(page, champ, lane_label, maps)

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

            time.sleep(0.6)

        context.close()
        browser.close()

    data = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "source": "ugg-playwright-main-lanes-v1",
        "ddragon_version": version,
        "total_entries": len(results),
        "note": "PlaywrightでU.GGを実ブラウザ表示し、表示後の画像alt/aria/textから統計・アイテム・ルーン・スペル・スキル順を抽出。取得失敗時はフォールバックビルド。",
        "champions": results,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"builds.json updated: {len(results)} entries")


if __name__ == "__main__":
    main()
