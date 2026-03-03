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
