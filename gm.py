"""SDND-TRPG ゲームマスターシステム メインスクリプト"""

import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from ai_player import AIPlayer
from characters import PLAYABLE_CHARACTERS
from llm_backend import GeminiBackend
from scenarios import SCENARIOS
from spec_loader import load_specs

# 会話履歴の最大メッセージ数（API コスト節約）
MAX_HISTORY = 20

BANNER = """
╔══════════════════════════════════════╗
║   ⚔  SDND-TRPG  ゲームマスター  ⚔   ║
║     〜 エルディアの冒険へようこそ 〜    ║
╚══════════════════════════════════════╝
"""

GM_SYSTEM_PROMPT = """あなたはTRPGのゲームマスター（GM）です。
舞台はファンタジー世界「エルディア」。

# GMの心得
- プレイヤーの行動に対して、結果を臨場感ある描写で返す
- 行動の成否が不確定な場合、内部で1d20を振って判定する
  （DCはGMが状況に応じて設定。結果を 🎲 1d20 = X vs DC Y → 成功/失敗 の形式で示す）
- 戦闘・探索・交渉など、あらゆる行動に対応する
- プレイヤーの自由な発想を尊重する
- ただし「不変ルール」に違反する行動は、物語的に自然に失敗させる
  （「それはできません」ではなく、結果として失敗する描写をする）
- NPCは世界観に沿った一貫したロールプレイで演じる
- 伏線に触れる機会があれば自然に織り込む
- 1回の応答は200〜400文字程度。テンポよく進める
- 危険な状況では適切に警告を含める
- 楽しませることが最優先！

# パーティ構成
{party_section}

# 開始シナリオ
{scenario}

# 世界の不変ルール（絶対遵守）
{invariants}

# 魔法のルール
{magic}

# 世界設定
{world}

# 現在の正史（確定済みの出来事）
{canon}

# 未解決の伏線
{open_loops}"""


def select_character() -> tuple[str, str]:
    """キャラクター選択。(選択名, detail) のタプルを返す。"""
    print("\n🎭 キャラクターを選んでください:\n")
    names = list(PLAYABLE_CHARACTERS.keys())
    for i, name in enumerate(names, 1):
        char = PLAYABLE_CHARACTERS[name]
        print(f"  {i}. {name} — {char['summary']}")

    while True:
        choice = input("\n番号を入力 > ").strip()
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(names):
                break
        except ValueError:
            pass
        print(f"  1〜{len(names)} の番号で選んでください。")

    selected = names[idx]
    char = PLAYABLE_CHARACTERS[selected]

    if selected == "オリジナル":
        print("\n📝 キャラクターの設定を入力してください（名前、スキル、性格など）。")
        print("   入力が終わったら空行でEnterを押してください。\n")
        lines = []
        while True:
            line = input()
            if line == "":
                break
            lines.append(line)
        detail = "\n".join(lines)
        if not detail.strip():
            detail = "名前未設定の冒険者。特に際立った能力はないが、勇気だけは人一倍。"
            print(f"  （デフォルト設定を使用します）")
        print(f"\n✅ オリジナルキャラクターで開始します！")
        return ("オリジナル", detail)
    else:
        print(f"\n✅ {char['full_name']} を選択しました！")
        return (selected, char["detail"])


def select_party(human_char_name: str) -> list[tuple[str, str]]:
    """AI仲間を選択。[(name, detail), ...] のリストを返す。"""
    # 候補: 人間が選んだキャラ以外の名前付きキャラ
    candidates = {
        name: char for name, char in PLAYABLE_CHARACTERS.items()
        if name != human_char_name and name != "オリジナル"
    }

    if not candidates:
        return []

    max_ai = min(2, len(candidates))

    print(f"\n🤝 AI仲間の人数を選んでください:\n")
    print(f"  0. ソロ冒険（仲間なし）")
    for i in range(1, max_ai + 1):
        if i == len(candidates):
            print(f"  {i}. {i}人（残りのキャラ全員が仲間に）")
        else:
            print(f"  {i}. {i}人（残りのキャラから{i}人選択）")

    while True:
        choice = input("\n番号を入力 > ").strip()
        try:
            count = int(choice)
            if 0 <= count <= max_ai:
                break
        except ValueError:
            pass
        print(f"  0〜{max_ai} の番号で選んでください。")

    if count == 0:
        return []

    # 全員追加の場合は選択を省略
    if count == len(candidates):
        selected = [(name, char["detail"]) for name, char in candidates.items()]
        for name, _ in selected:
            print(f"\n✅ AI仲間: {PLAYABLE_CHARACTERS[name]['full_name']}")
        return selected

    # 1人ずつ選択
    remaining = dict(candidates)
    selected = []
    for i in range(count):
        names = list(remaining.keys())
        print(f"\nAI仲間を選んでください（{i + 1}人目）:")
        for j, name in enumerate(names, 1):
            print(f"  {j}. {name} — {remaining[name]['summary']}")

        while True:
            choice = input("\n番号を入力 > ").strip()
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(names):
                    break
            except ValueError:
                pass
            print(f"  1〜{len(names)} の番号で選んでください。")

        picked = names[idx]
        selected.append((picked, remaining[picked]["detail"]))
        print(f"\n✅ AI仲間: {PLAYABLE_CHARACTERS[picked]['full_name']}")
        del remaining[picked]

    return selected


def build_party_section(character_detail: str, ai_members: list[tuple[str, str]]) -> str:
    """パーティ構成セクションを構築する。"""
    lines = ["## 人間プレイヤー", character_detail]

    if ai_members:
        lines.append("")
        lines.append("## AIパーティーメンバー")
        for name, detail in ai_members:
            lines.append(f"### {name}")
            lines.append(detail)
        party_size = 1 + len(ai_members)
        lines.append("")
        lines.append(f"{party_size}人パーティとして適切な場面展開を心がけてください。")
        lines.append("NPCとしてではなく、プレイヤーキャラクターとして扱ってください。")

    return "\n".join(lines)


def select_scenario() -> str:
    """シナリオ選択。選ばれたシナリオの説明文を返す。"""
    print("\n🗺️ シナリオを選んでください:\n")
    names = list(SCENARIOS.keys())
    for i, name in enumerate(names, 1):
        print(f"  {i}. {name} — {SCENARIOS[name][:40]}...")
    print(f"  {len(names) + 1}. 自由入力")

    while True:
        choice = input("\n番号を入力 > ").strip()
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(names):
                print(f"\n✅ 「{names[idx]}」を選択しました！")
                return SCENARIOS[names[idx]]
            elif idx == len(names):
                # 自由入力
                print("\n📝 シナリオの状況を自由に入力してください:")
                scenario = input("> ").strip()
                if not scenario:
                    scenario = "あなたは小さな村の広場に立っている。穏やかな朝だ。"
                    print("  （デフォルトシナリオを使用します）")
                return scenario
        except ValueError:
            pass
        print(f"  1〜{len(names) + 1} の番号で選んでください。")


def build_system_prompt(party_section: str, scenario: str, specs: dict[str, str]) -> str:
    """GMシステムプロンプトを構築する。"""
    return GM_SYSTEM_PROMPT.format(
        party_section=party_section,
        scenario=scenario,
        invariants=specs["invariants"] or "（ルール未読み込み。一般的なファンタジー世界のルールで運用）",
        magic=specs["magic"] or "（未読み込み。魔法にはコストとリスクが伴うものとして扱う）",
        world=specs["world"] or "（未読み込み。中世ヨーロッパ風ファンタジーとして運用）",
        canon=specs["canon"] or "（未読み込み）",
        open_loops=specs["open_loops"] or "（なし）",
    )


def save_session(
    messages: list[dict],
    character_detail: str,
    ai_members: list[tuple[str, str]],
    scenario: str,
) -> str:
    """セッションログを Markdown 形式で保存する。"""
    sessions_dir = Path(__file__).parent / "sessions"
    sessions_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = sessions_dir / f"session_{timestamp}.md"

    lines = [
        f"# SDND-TRPG セッションログ",
        f"",
        f"- 日時: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"",
        f"## 人間プレイヤー",
        f"```",
        character_detail,
        f"```",
        f"",
    ]

    if ai_members:
        lines.append("## AIパーティーメンバー")
        for name, detail in ai_members:
            lines.append(f"### {name}")
            lines.append("```")
            lines.append(detail)
            lines.append("```")
            lines.append("")

    lines.extend([
        f"## シナリオ",
        scenario,
        f"",
        f"## プレイログ",
        f"",
    ])

    for msg in messages:
        if msg.get("source") == "ai":
            name = msg.get("name", "AI仲間")
            lines.append(f"### 🤖 {name}")
            lines.append(msg["content"])
            lines.append("")
        elif msg["role"] == "user":
            lines.append(f"### 🎮 プレイヤー")
            lines.append(msg["content"])
            lines.append("")
        else:
            lines.append(f"### 🎲 GM")
            lines.append(msg["content"])
            lines.append("")

    filepath.write_text("\n".join(lines), encoding="utf-8")
    return str(filepath)


def main():
    print(BANNER)

    # 1. 環境設定
    load_dotenv()

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY が設定されていません。")
        print("")
        print("   以下の手順で設定してください:")
        print("   1. https://aistudio.google.com/apikey でAPIキーを取得")
        print("   2. .env.example を .env にコピー")
        print("   3. .env の GEMINI_API_KEY にキーを貼り付け")
        sys.exit(1)

    # 2. specs 読み込み
    print("📖 世界設定を読み込み中...")
    specs = load_specs()

    # 3. LLM バックエンド初期化
    print("\n🤖 GM を起動中...")
    try:
        backend = GeminiBackend(api_key)
    except Exception as e:
        print(f"❌ LLM バックエンドの初期化に失敗しました: {e}")
        sys.exit(1)

    # 4. キャラクター選択
    human_char_name, character_detail = select_character()

    # 5. パーティ編成
    ai_members = select_party(human_char_name)
    ai_players = [
        AIPlayer(backend, name, detail) for name, detail in ai_members
    ]

    # パーティ編成を表示
    human_full = PLAYABLE_CHARACTERS.get(human_char_name, {}).get("full_name") or human_char_name
    print(f"\n⚔ パーティ編成:")
    print(f"  🧑 {human_full}（あなた）")
    for name, _ in ai_members:
        print(f"  🤖 {PLAYABLE_CHARACTERS[name]['full_name']}")

    # 6. シナリオ選択
    scenario = select_scenario()

    # 7. システムプロンプト構築
    party_section = build_party_section(character_detail, ai_members)
    system_prompt = build_system_prompt(party_section, scenario, specs)

    # 8. オープニング生成
    print("\n" + "=" * 40)
    print("🎲 冒険が始まります...")
    print("=" * 40 + "\n")

    messages: list[dict] = [
        {"role": "user", "content": "ゲーム開始。シナリオの状況を描写して、最初の場面を演出してください。"}
    ]

    try:
        opening = backend.chat(system_prompt, messages)
    except Exception as e:
        _handle_api_error(e)
        sys.exit(1)

    messages.append({"role": "assistant", "content": opening})
    print(opening)

    # 9. ゲームループ
    print("\n💡 ヒント: 行動を自由に入力してください。")
    print("   「save」でログ保存、「quit」で終了。\n")

    # 人間の行動にキャラ名プレフィックスを付ける（オリジナル以外）
    human_prefix = f"【{human_char_name}】" if human_char_name != "オリジナル" else ""

    while True:
        try:
            action = input("🎮 > ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            action = "quit"

        if not action:
            continue

        # 特殊コマンド
        if action.lower() == "save":
            path = save_session(messages, character_detail, ai_members, scenario)
            print(f"\n📝 セッションログを保存しました: {path}\n")
            continue

        if action.lower() == "quit":
            confirm = input("本当に終了しますか？ (y/n) > ").strip().lower()
            if confirm in ("y", "yes", "はい"):
                save_q = input("ログを保存しますか？ (y/n) > ").strip().lower()
                if save_q in ("y", "yes", "はい"):
                    path = save_session(messages, character_detail, ai_members, scenario)
                    print(f"\n📝 セッションログを保存しました: {path}")
                print("\n⚔ お疲れさまでした！またエルディアでお会いしましょう。\n")
                break
            continue

        # 1. 人間プレイヤーの行動を追加
        human_content = f"{human_prefix}{action}" if human_prefix else action
        messages.append({"role": "user", "content": human_content})

        # 会話履歴を制限
        if len(messages) > MAX_HISTORY:
            messages = messages[-MAX_HISTORY:]

        # 2. GM の応答（人間の行動に対して）
        print()
        try:
            response = backend.chat(system_prompt, messages)
        except Exception as e:
            messages.pop()  # 失敗した入力を履歴から除去
            _handle_api_error(e)
            continue

        messages.append({"role": "assistant", "content": response})
        print(f"📖 GM: {response}")
        print()

        # 3. 各AI仲間が順番に行動
        for ai_player in ai_players:
            # AI仲間の行動を生成
            try:
                ai_action = ai_player.decide_action(messages)
            except Exception as e:
                print(f"⚠ {ai_player.char_name}の行動生成に失敗しました: {e}")
                print()
                continue

            print(f"🤖 {ai_player.char_name}: {ai_action}")
            print()

            # AI仲間の行動をmessagesに追加（source メタデータ付き）
            messages.append({
                "role": "user",
                "content": f"【{ai_player.char_name}】{ai_action}",
                "source": "ai",
                "name": ai_player.char_name,
            })

            # 会話履歴を制限
            if len(messages) > MAX_HISTORY:
                messages = messages[-MAX_HISTORY:]

            # GM の応答（AI仲間の行動に対して）
            try:
                ai_response = backend.chat(system_prompt, messages)
            except Exception as e:
                messages.pop()  # 失敗したAI行動を履歴から除去
                _handle_api_error(e)
                continue

            messages.append({"role": "assistant", "content": ai_response})
            print(f"📖 GM: {ai_response}")
            print()


def _handle_api_error(e: Exception):
    """API エラーを分類して親切なメッセージを表示する。"""
    error_str = str(e).lower()
    if "api key" in error_str or "unauthorized" in error_str or "403" in error_str:
        print("❌ APIキーが無効です。.env の GEMINI_API_KEY を確認してください。")
    elif "rate" in error_str or "429" in error_str or "quota" in error_str:
        print("⏳ APIのレート制限に達しました。しばらく待ってから再試行してください。")
    elif "network" in error_str or "connection" in error_str or "timeout" in error_str:
        print("🌐 ネットワークエラーです。インターネット接続を確認してください。")
    else:
        print(f"❌ GMの応答生成に失敗しました: {e}")


if __name__ == "__main__":
    main()
