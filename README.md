# CGPLauncher

## Games.json エディター

games.jsonファイルを編集・管理するためのGUIツールです。

## 起動方法

### 簡単な方法（推奨）
1. `run_editor.bat` をダブルクリックして起動
   - エラーメッセージも表示される安全な起動方法

2. `start.bat` をダブルクリックして起動
   - 最もシンプルな起動方法

### 従来の方法
- `start_games_editor.bat` - フルパス指定版（環境変数未設定時用）
- `games_editor_simple.bat` - フルパス指定版（シンプル）

### コマンドライン
```bash
python games_editor.py
```

## 機能
- ゲーム情報の追加・編集・削除
- 検索機能
- バリデーション機能
- 自動バックアップ
- アルファベット順ソート

## 必要な環境
- Python 3.6以上
- tkinter（通常Pythonに標準で含まれています）