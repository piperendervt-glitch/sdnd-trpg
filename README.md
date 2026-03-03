# SDND-TRPG

AIゲームマスターによるテーブルトークRPGシステム。ファンタジー世界「エルディア」を舞台に、Gemini 2.5 Flash がGMを務める。

## 特徴

- **AI ゲームマスター** — Gemini がシナリオ進行・判定・NPC演出を担当
- **2人パーティ制** — 人間プレイヤー + AI仲間が自動で行動を宣言
- **ダイス判定** — 不確定な行動は GM が 1d20 で成否を判定（🎲 1d20 = X vs DC Y）
- **世界設定連携** — [sdnd-eldia](https://github.com/piperendervt-glitch/sdnd-eldia) の spec ファイルを読み込み、設定に沿ったプレイが可能
- **セッションログ保存** — プレイ内容を Markdown で自動保存

## セットアップ

### 1. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 2. API キーの設定

```bash
cp .env.example .env
```

`.env` を編集して Gemini API キーを設定:

```
GEMINI_API_KEY=your_gemini_api_key_here
```

API キーは https://aistudio.google.com/apikey で取得できる。

### 3. 世界設定（オプション）

`sdnd-eldia` プロジェクトがある場合、`.env` でパスを指定すると世界設定が自動読み込みされる:

```
SDND_PROJECT_PATH=../sdnd-eldia
```

なくても一般的なファンタジー設定でプレイ可能。

## 遊び方

```bash
python gm.py
```

1. **キャラクター選択** — アル、エラ、またはオリジナルキャラを選ぶ
2. **AI仲間が自動加入** — 選んだキャラに応じてパートナーが決まる
3. **シナリオ選択** — プリセットまたは自由入力
4. **冒険開始** — 行動を自由に入力。1ターンの流れ:
   - 🎮 あなたの行動 → 📖 GM の応答 → 🤖 AI仲間の行動 → 📖 GM の応答

### コマンド

| コマンド | 説明 |
|---------|------|
| `save`  | セッションログを `sessions/` に保存 |
| `quit`  | ゲーム終了（ログ保存の確認あり） |

## キャラクター

| 名前 | 説明 |
|------|------|
| アル＝ラグナ | 5歳の少年。前世は28歳のエンジニア。解析眼を持つ |
| エラ | Bランク冒険者。剣と探知魔法の使い手 |
| オリジナル | 自分でキャラクターを自由に作成 |

## プロジェクト構成

```
sdnd-trpg/
├── gm.py            # メインスクリプト（ゲームループ）
├── ai_player.py     # AIパーティメンバー
├── llm_backend.py   # LLMバックエンド抽象化
├── characters.py    # キャラクター定義
├── scenarios.py     # プリセットシナリオ
├── spec_loader.py   # 世界設定読み込み
├── requirements.txt
├── .env.example
└── sessions/        # セッションログ（git管理外）
```

## ⚠ API レート制限について

Gemini API の無料枠（Free Tier）は以下の制限があります（2026年3月時点）:

| モデル | RPM（分あたり） | RPD（日あたり） |
|--------|----------------|----------------|
| gemini-2.5-flash | 10 | 20 |
| gemini-2.5-flash-lite | 15 | 20 |

AI仲間ありのプレイでは 1ターンあたり 3〜5 APIコールが発生するため、
無料枠では数ターンで制限に達します。

### 推奨環境

以下のいずれかを推奨します:

- **Gemini 有料枠（Tier 1）**: Google AI Studio でクレジットカードを登録するだけで
  RPM 300 / RPD 無制限にアップグレード。コストはごく僅か（10ターンで数円程度）
- **Anthropic Claude API**: Haiku モデルで高品質な日本語RPが可能
- **OpenAI API**: GPT-5 mini 等で代替可能

ソロプレイ（AI仲間なし）であれば無料枠でもプレイ可能ですが、
リクエスト間隔に注意が必要です。
