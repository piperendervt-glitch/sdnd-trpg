"""LLM バックエンド抽象化モジュール"""

from google import genai
from google.genai import types


class LLMBackend:
    """LLM バックエンドの抽象インターフェース"""

    def chat(self, system: str, messages: list[dict], max_output_tokens: int = 1024) -> str:
        """
        チャット応答を生成する。

        Args:
            system: システムプロンプト
            messages: 会話履歴 [{"role": "user"|"assistant", "content": "..."}]
            max_output_tokens: 最大出力トークン数

        Returns:
            アシスタントの応答テキスト
        """
        raise NotImplementedError


class GeminiBackend(LLMBackend):
    """Gemini 2.5 Flash バックエンド"""

    MODEL = "gemini-2.5-flash-lite"

    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)

    def chat(self, system: str, messages: list[dict], max_output_tokens: int = 1024) -> str:
        # 会話履歴を Gemini の Content 形式に変換
        # Gemini は "model" ロールを使う（"assistant" ではない）
        contents = []
        for msg in messages:
            role = "model" if msg["role"] == "assistant" else msg["role"]
            contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=msg["content"])],
                )
            )

        response = self.client.models.generate_content(
            model=self.MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system,
                max_output_tokens=max_output_tokens,
            ),
        )
        return response.text
