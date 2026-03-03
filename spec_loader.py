"""sdnd-eldia プロジェクトからの spec 読み込みモジュール"""

import os
from pathlib import Path


def _read_file(path: Path, max_chars: int | None = None) -> str:
    """ファイルを読み込む。存在しなければ空文字を返す。"""
    try:
        text = path.read_text(encoding="utf-8")
        if max_chars is not None:
            text = text[:max_chars]
        return text
    except FileNotFoundError:
        return ""


def _find_and_read(base: Path, candidates: list[str], max_chars: int | None = None) -> str:
    """候補パスを順に探し、最初に見つかったファイルを読み込む。"""
    for candidate in candidates:
        path = base / candidate
        content = _read_file(path, max_chars)
        if content:
            return content
    return ""


def load_specs(project_path: str | None = None) -> dict[str, str]:
    """
    sdnd-eldia プロジェクトから spec ファイルを読み込む。

    Returns:
        dict with keys: invariants, characters, magic, world, canon, open_loops
        見つからないファイルは空文字列。
    """
    base = Path(project_path or os.getenv("SDND_PROJECT_PATH", "../sdnd-eldia"))
    base = base.resolve()

    if not base.exists():
        print(f"  ⚠ spec ディレクトリが見つかりません: {base}")
        print("    一般ファンタジー設定でプレイします。")
        return {k: "" for k in ["invariants", "characters", "magic", "world", "canon", "open_loops"]}

    specs = {}

    # 必須（全文読み込み）
    specs["invariants"] = _find_and_read(base, [
        "specs/core/invariants.md",
        "specs/invariants.md",
    ])
    if not specs["invariants"]:
        print("  ⚠ invariants.md が見つかりません")

    # 推奨（先頭3000文字）
    specs["characters"] = _find_and_read(base, [
        "specs/reference/characters_full.md",
        "specs/core/characters_full.md",
        "specs/characters.md",
    ], max_chars=3000)

    specs["magic"] = _find_and_read(base, [
        "specs/reference/magic_physics.md",
        "specs/magic_physics.md",
    ], max_chars=3000)

    specs["world"] = _find_and_read(base, [
        "specs/reference/world.md",
        "specs/reference/world_settings.md",
        "specs/world.md",
    ], max_chars=3000)

    # あれば読む（先頭1500文字）
    specs["canon"] = _find_and_read(base, [
        "canon/quick_ref.md",
    ], max_chars=1500)

    specs["open_loops"] = _find_and_read(base, [
        "meta/open_loops.md",
    ], max_chars=1500)

    # 読み込み結果のサマリー
    loaded = [k for k, v in specs.items() if v]
    if loaded:
        print(f"  📖 読み込み済み: {', '.join(loaded)}")
    else:
        print("  ⚠ spec ファイルが1つも見つかりませんでした")
        print("    一般ファンタジー設定でプレイします。")

    return specs
