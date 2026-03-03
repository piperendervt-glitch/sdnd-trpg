"""AIパーティメンバーモジュール"""

from llm_backend import LLMBackend

AI_PLAYER_SYSTEM_PROMPT = """あなたはTRPGのプレイヤーキャラクターです。
GMの描写に対して、あなたのキャラクターらしい行動を1つ宣言してください。

# あなたのキャラクター
{character_detail}

# 行動ルール
- 1回の行動は1〜2文の短い宣言にする
- キャラクターの性格・能力に合った行動をする
- パーティの仲間と協力する
- GMの描写をよく読み、状況に適した行動を選ぶ
- 戦闘中は攻撃・防御・支援など具体的な行動を宣言する
- 探索中は調査・警戒・交渉など状況に応じた行動を宣言する
"""

TRIGGER_MESSAGE = "あなたのターンです。パーティの状況を踏まえて、あなたの行動を1つ宣言してください。"


class AIPlayer:
    """AIが操作するパーティメンバー"""

    def __init__(self, backend: LLMBackend, char_name: str, char_detail: str):
        self.backend = backend
        self.char_name = char_name
        self.system_prompt = AI_PLAYER_SYSTEM_PROMPT.format(character_detail=char_detail)

    def decide_action(self, messages: list[dict]) -> str:
        """GM会話履歴を受け取り、AI仲間の行動を生成する。"""
        # 元のリストを変更しないようshallow copy
        ai_messages = list(messages)
        ai_messages.append({"role": "user", "content": TRIGGER_MESSAGE})

        return self.backend.chat(
            self.system_prompt,
            ai_messages,
            max_output_tokens=256,
        )
