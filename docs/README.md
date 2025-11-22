# OPHChecker

眼科手術データ処理用の Python アプリケーション。手術予定、検索データ、エラーデータを一元的に処理し、データ品質を確保します。

## 主な機能

- **手術予定表変換**: Excel ファイルを CSV 形式に変換し、統一されたカラム構造に整形
- **眼科手術検索データ変換**: CSV ファイルを変換し、統一されたカラム構造に整形
- **手術データ比較**: 手術予定表と眼科手術検索データの突合、差分確認
- **エラー抽出・レポート**: 不正なレコードを自動検出し、Excel レポート生成

**現在のバージョン**: 1.0.3
**最終更新日**: 2025年11月22日

## システム要件

- **Python**: 3.12 以上
- **OS**: Windows 11
- **メモリ**: 最小 2GB

### 必須ライブラリ

- pandas (1.5.3) - データ処理
- openpyxl (3.1.5) - Excel ファイル操作

詳細は `requirements.txt` を参照してください。

## セットアップ手順

### 1. リポジトリをクローン

```bash
git clone <repository-url>
cd OPHChecker
```

### 2. 仮想環境を作成・有効化

```bash
# 仮想環境作成
python -m venv .venv

# 仮想環境有効化
.venv\Scripts\activate
```

### 3. 依存パッケージをインストール

```bash
pip install -r requirements.txt
```

### 4. 設定ファイルを確認

`utils/config.ini` に手術データファイルのパスを設定します。実際の環境に合わせてパスを修正してください。

### 5. インストール確認

```bash
# 型チェック実行
pyright

# テスト実行
python -m pytest tests/ -v
```

## 使用方法

### 基本的な処理フロー

#### 1. 手術予定処理 (Excel → CSV)

```python
from service.surgery_schedule_processor import process_surgery_schedule

process_surgery_schedule('入力.xls', '出力.csv')
```

#### 2. 眼科手術検索データクリーニング

```python
from service.surgery_search_processor import process_eye_surgery_data

process_eye_surgery_data('入力.csv', '出力.csv')
```

#### 3. 手術データ比較

```python
from service.surgery_comparator import compare_surgery_data

compare_surgery_data('検索データ.csv', '予定表.csv', '比較結果.csv')
```

#### 4. エラーデータ抽出

```python
from service.surgery_error_extractor import surgery_error_extractor

surgery_error_extractor('比較結果.csv', '出力ディレクトリ', 'テンプレート.xlsx')
```

### CLI から実行

```bash
python main.py
```

## プロジェクト構造

```
OPHChecker/
├── app/
│   ├── __init__.py              # バージョン・日付管理
│   └── main_window.py           # メイン画面UI
│
├── assets/                       # アプリケーションリソース
│   ├── OPHChecker.ico           # アイコンファイル
│   └── OPHChecker.png           # 画像ファイル
│
├── service/                      # データ処理サービス層
│   ├── surgery_schedule_processor.py    # Excel手術予定処理
│   ├── surgery_search_processor.py      # CSV眼科データクリーニング
│   ├── surgery_comparator.py            # データ突合比較
│   ├── surgery_error_extractor.py       # エラーレコード抽出・レポート
│   └── __init__.py
│
├── utils/                        # ユーティリティ・設定管理
│   ├── config_manager.py        # 設定読込・保存
│   ├── config.ini               # 設定ファイル
│   ├── log_rotation.py          # ログローテーション管理
│   └── __init__.py
│
├── widgets/                      # UI コンポーネント
│   ├── exclude_items_dialog.py  # 除外項目設定ダイアログ
│   ├── replacements_dialog.py   # 置換設定ダイアログ
│   └── __init__.py
│
├── tests/                        # テストスイート
│
├── scripts/
│   ├── version_manager.py       # バージョン・日付自動更新
│   └── __init__.py
│
├── docs/
│   ├── README.md                # 本ファイル
│   ├── CHANGELOG.md             # 変更履歴
│   └── LICENSE
│
├── main.py                       # アプリケーション エントリーポイント
├── build.py                      # PyInstaller ビルドスクリプト
├── requirements.txt              # Python 依存パッケージ
├── pyrightconfig.json            # 型チェック設定
├── CLAUDE.md                     # 開発ガイドライン
└── .gitignore
```

## 主要モジュール

### surgery_schedule_processor.py

Excel 形式の手術予定表を CSV 形式に変換します。

**処理内容**:
- 手術日時の解析・変換
- 患者情報の正規化
- 術式・医師名の統一
- 左右眼別の術式分割

**使用例**:
```python
from service.surgery_schedule_processor import process_surgery_schedule

process_surgery_schedule('手術予定表.xls', 'output.csv', sheet_name='南眼2')
```

### surgery_search_processor.py

眼科システムから出力された CSV を清掃・標準化します。複数のヘルパー関数で段階的にデータを処理します。

**主要処理**:
- `_select_required_columns()`: 必須カラムのみ抽出
- `_convert_surgery_date_format()`: 日付形式統一
- `_apply_replacements()`: 麻酔・入院・医師名の標準化
- `_remove_surgery_strings()`: 不要な術式情報削除
- `_filter_exclusion_keywords()`: 除外キーワード行を削除
- `_normalize_surgery_text()`: 術式テキスト正規化
- `_create_eye_side_column()`: 左右眼別カラム生成
- `_handle_duplicates()`: 重複レコード処理
- `_reorder_and_sort()`: カラム並び替え・ソート

**使用例**:
```python
from service.surgery_search_processor import process_eye_surgery_data

process_eye_surgery_data('眼科システム手術検索.csv', 'processed_search.csv')
```

### surgery_comparator.py

手術予定データと眼科手術検索データを突き合わせて差分を確認します。

**処理内容**:
- 2 つのデータセット間の差分抽出
- 入院/術式/医師/麻酔の一致判定
- 予定未入力レコード検出
- 比較結果を CSV で出力

**使用例**:
```python
from service.surgery_comparator import compare_surgery_data

compare_surgery_data('processed_search.csv', 'processed_schedule.csv', 'comparison.csv')
```

### surgery_error_extractor.py

比較結果から不正・不一致レコードを抽出し、Excel レポートを生成します。

**処理内容**:
- FALSE または「未入力」を含むレコード抽出
- Template Excel ファイルにデータを書き込み
- タイムスタンプ付きレポート生成

**使用例**:
```python
from service.surgery_error_extractor import surgery_error_extractor

surgery_error_extractor('comparison.csv', 'output/', 'template.xlsx')
```

### config_manager.py

設定ファイル (`config.ini`) の読込・保存・管理を行います。PyInstaller でビルドした実行ファイルでも、通常の Python 実行でも、正しく config.ini を読み込めます。

**主要関数**:
- `load_config()`: config.ini から設定を読み込む
- `save_config()`: 設定を保存
- `get_paths()`: ファイルパスを取得
- `get_exclusion_line_keywords()`: 除外キーワード一覧を取得
- `get_surgery_strings_to_remove()`: 削除対象術式文字列を取得
- `get_replacement_dict()`: 置換辞書を取得

## 設定ファイル (config.ini)

### [Appearance]

UI フォント・ウィンドウサイズの設定

```ini
font_size = 11                    # メインウィンドウ フォントサイズ
log_font_size = 11                # ログ表示 フォントサイズ
window_width = 600                # ウィンドウ幅
window_height = 500               # ウィンドウ高さ
```

### [DialogSize]

ダイアログサイズの設定

```ini
folder_dialog_width = 600         # フォルダ選択ダイアログ幅
folder_dialog_height = 200        # フォルダ選択ダイアログ高さ
```

### [ExcludeItems]

除外キーワード・削除対象文字列の設定 (カンマ区切り)

```ini
exclusion_line_keywords = ★,霰粒腫,術式未定,先天性鼻涙管閉塞開放術
surgery_strings_to_remove = (クラレオントーリック),(クラレオンパンオプティクス)
```

### [LOGGING]

ログ出力設定

```ini
log_directory = logs              # ログ出力ディレクトリ
log_retention_days = 7            # ログ保持日数
log_level = INFO                  # ログレベル
```

### [Paths]

入出力ファイルパス (環境に合わせて変更)

```ini
input_path = C:\Shinseikai\OPHChecker\input
surgery_search_data = C:\Shinseikai\OPHChecker\input\眼科システム手術検索.csv
processed_surgery_search_data = C:\Shinseikai\OPHChecker\processed\processed_search.csv
surgery_schedule = C:\Shinseikai\OPHChecker\input\手術予定表.xls
processed_surgery_schedule = C:\Shinseikai\OPHChecker\processed\processed_schedule.csv
comparison_result = C:\Shinseikai\OPHChecker\processed\comparison.csv
template_path = C:\Shinseikai\OPHChecker\眼科手術指示確認.xlsx
output_path = C:\Shinseikai\OPHChecker\output
```

### [Replacements]

データ標準化用の置換辞書 (オリジナル値:統一値)

## 開発方法

### テスト実行

```bash
# すべてのテストを実行
python -m pytest tests/ -v

# カバレッジレポート付きで実行
python -m pytest tests/ -v --cov

# 特定のテストファイルを実行
python -m pytest tests/test_main.py -v
```

### 型チェック

```bash
# Pyright で型チェック (Python 3.12, standard mode)
pyright
```

### ビルド・バージョン管理

```bash
# 実行ファイルをビルド (バージョン自動更新)
python build.py

# 手動でバージョンを更新
python -c "from scripts.version_manager import update_version; update_version()"
```

**ビルド処理の流れ**:
1. `scripts/version_manager.py` が呼ばれてバージョンを自動インクリメント
2. `app/__init__.py` の `__version__` と `__date__` を更新
3. `docs/README.md` のバージョン・日付も同期更新
4. PyInstaller でスタンドアロン実行ファイルを生成 (`dist/眼科手術指示確認.exe`)

## コード規約

### 型ヒント

すべての関数パラメータと戻り値に型ヒント必須です。Pyright は `standard` モード、Python 3.12 で動作します。

```python
def process_data(input_file: str, output_file: str) -> None:
    df = pd.read_csv(input_file, encoding='cp932')
    # ...
    df.to_csv(output_file, encoding='cp932', index=False)
```

### インポート順序

標準ライブラリ → サードパーティ → カスタムモジュール (各グループで alphabetical)

```python
import sys
from configparser import ConfigParser
from pathlib import Path

import pandas as pd
from openpyxl import load_workbook

from utils.config_manager import load_config
```

### 日本語コメント

分かりにくいロジックのみ日本語でコメント。末尾のピリオド・句点は不要です。

```python
def _convert_surgery_date_format(row: pd.Series) -> str:
    # 手術日を標準形式に変換
    return row['date'].strftime('%Y年%m月%d日')
```

### ファイルエンコーディング

- Python ソースコード: UTF-8
- 日本語データファイル (CSV, Excel): cp932 (Windows Shift-JIS)

```python
# CSV 読み込み (日本語対応)
df = pd.read_csv('眼科システム手術検索.csv', encoding='cp932')

# CSV 出力 (日本語対応)
df.to_csv('output.csv', encoding='cp932', index=False)
```

## トラブルシューティング

### 日本語ファイルが文字化けする

**原因**: ファイルエンコーディングが UTF-8 ではなく cp932 を使用している

**解決策**: pandas の `encoding='cp932'` を指定

```python
df = pd.read_csv('ファイル名.csv', encoding='cp932')
df.to_csv('output.csv', encoding='cp932', index=False)
```

### PyInstaller ビルドで config.ini が見つからない

**原因**: PyInstaller で `--add-data` オプションを指定していない

**解決策**: `build.py` で config.ini を bundling するよう設定。`config_manager.py` は `sys.frozen` を検出して `sys._MEIPASS` からファイルを読み込みます。

### テスト実行時にモジュールが見つからない

**原因**: Python パスが正しく設定されていない

**解決策**: プロジェクトルートから pytest を実行

```bash
cd C:\Users\yokam\PycharmProjects\OPHChecker
python -m pytest tests/ -v
```

## 注意事項

### ファイルパス

- デフォルト設定では `C:\Shinseikai\OPHChecker\` を使用しています
- 環境に合わせて `config.ini` のパスを修正してください
- Windows パスはバックスラッシュ `\` で指定します

### 日本語対応

- すべての手術データファイルは cp932 (Windows Shift-JIS) エンコーディングで保存されています
- Python コード内で日本語ファイルを読み書きする際は、必ず `encoding='cp932'` を指定してください
- UTF-8 指定でファイルを読み込むと文字化けします

### PyInstaller ビルド

- `build.py` を実行すると、`dist/` ディレクトリに実行ファイルが生成されます
- ビルド時に自動でバージョンが更新されます
- 配布する際は `dist/` フォルダ全体をコピーしてください

## 変更履歴

詳細な変更履歴は [CHANGELOG.md](./CHANGELOG.md) を参照してください。

## ライセンス

[LICENSE](./LICENSE) を参照してください。

---

**開発者向け**: CLAUDE.md および CHANGELOG.md に詳細な開発ガイドラインがあります。
