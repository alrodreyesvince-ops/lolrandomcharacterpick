import json
from datetime import datetime, timezone
from pathlib import Path

output_path = Path("data/builds.json")

data = {
    "updated_at": datetime.now(timezone.utc).isoformat(),
    "source": "test",
    "champions": [
        {
            "name_ja": "アーリ",
            "name_en": "Ahri",
            "lane": "MID",
            "tier": "strong",
            "builds": [
                {
                    "name": "テスト用バーストメイジビルド",
                    "items": [
                        "ルーデン コンパニオン",
                        "シャドウフレイム",
                        "ラバドン デスキャップ"
                    ],
                    "runes": [
                        "電撃",
                        "血の味わい",
                        "目玉コレクター"
                    ],
                    "skills": "Q → W → E"
                }
            ]
        }
    ]
}

output_path.parent.mkdir(parents=True, exist_ok=True)

with output_path.open("w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("builds.json updated")
