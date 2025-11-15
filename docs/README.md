# OPHChecker

眼科手術データ処理用の Python アプリケーション。手術スケジュール、検索データ、エラーデータを一元的に処理し、データ品質を確保します。

## 主な機能

- **手術スケジュール変換**: Excel ファイルを CSV 形式に変換し、統一されたカラム構造に整形
- **眼科データクリーニング**: CSVファイルを清掃・標準化し、麻酔・入院情報を統一
- **手術データ比較**: スケジュール データと検索データの突合、差分確認
- **エラー抽出・レポート**: 不正なレコードを自動検出し、Excel レポート生成
- **自動化ビルド**: PyInstaller でスタンドアロン実行ファイルを生成、バージョン自動管理
- **日本語対応**: Windows Shift-JIS (cp932) エンコーディングで日本語ファイル対応

**バージョン**: 1.0.0
**更新日**: 2025年11月11日

## システム要件

- **Python**: 3.13 以上
- **OS**: Windows (ファイルパスが Windows パスになっています)
- **メモリ**: 最小 2GB (大規模 CSV 処理時は 4GB 推奨)

### 必須ライブラリ

- pandas (1.5.3) - データ処理
- openpyxl (3.1.5) - Excel ファイル操作
- pyinstaller (6.16.0) - 実行ファイル生成

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

### 4. 設定ファイルを準備

`utils/config.ini` に手術データファイルのパスを設定します。デフォルト値は以下の通りです:

```ini
[Paths]
input_path = C:\Shinseikai\OPHChecker\input
surgery_search_data = C:\Shinseikai\OPHChecker\input\眼科システム手術検索.csv
processed_surgery_search_data = C:\Shinseikai\OPHChecker\processed\processed_surgery_search.csv
surgery_schedule = C:\Shinseikai\OPHChecker\input\手術予定表.xls
processed_surgery_schedule = C:\Shinseikai\OPHChecker\processed\processed_surgery_schedule.csv
comparison_result = C:\Shinseikai\OPHChecker\processed\comparison_result.csv
template_path = C:\Shinseikai\OPHChecker\眼科手術指示確認.xlsx
output_path = C:\Shinseikai\OPHChecker\output
```

実際の環境に合わせて、パスを修正してください。

### 5. インストール確認

```bash
# 型チェック実行
pyright

# テスト実行
python -m pytest tests/ -v
```

## 使用方法

### 基本的な処理フロー

#### 1. 手術スケジュール処理 (Excel → CSV)

```python
from service.surgery_schedule_processor import process_surgery_schedule
from utils.config_manager import load_config

config = load_config()
input_file = config['Paths']['surgery_schedule']
output_file = config['Paths']['processed_surgery_schedule']

process_surgery_schedule(input_file, output_file)
```

#### 2. 眼科システムデータクリーニング

```python
from service.surgery_search_processor import process_eye_surgery_data
from utils.config_manager import load_config

config = load_config()
input_file = config['Paths']['surgery_search_data']
output_file = config['Paths']['processed_surgery_search_data']

process_eye_surgery_data(input_file, output_file)
```

#### 3. 手術データ比較

```python
from service.surgery_comparator import compare_surgery_data
from utils.config_manager import load_config

config = load_config()
schedule_file = config['Paths']['processed_surgery_schedule']
search_file = config['Paths']['processed_surgery_search_data']
output_file = config['Paths']['comparison_result']

compare_surgery_data(schedule_file, search_file, output_file)
```

#### 4. エラーデータ抽出

```python
from service.surgery_error_extractor import surgery_error_extractor
from utils.config_manager import load_config

config = load_config()
input_file = config['Paths']['comparison_result']
output_file = config['Paths']['output_path'] + '\errors.xlsx'
template_file = config['Paths']['template_path']

surgery_error_extractor(input_file, output_file, template_file)
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
│   └── __version__ = "1.0.0"
│
├── service/                      # データ処理サービス層
│   ├── surgery_schedule_processor.py    # Excel手術スケジュール処理
│   ├── surgery_search_processor.py      # CSV眼科データクリーニング (10+ ヘルパー関数)
│   ├── surgery_comparator.py            # データ突合比較
│   ├── surgery_error_extractor.py       # エラーレコード抽出・レポート
│   └── __init__.py
│
├── utils/                        # ユーティリティ・設定管理
│   ├── config_manager.py        # 設定読込・保存 (16関数)
│   ├── config.ini               # 設定ファイル
│   └── __init__.py
│
├── widgets/                      # UI コンポーネント
│   └── __init__.py
│
├── tests/                        # テストスイート
│   ├── test_main.py
│   ├── app/, service/, utils/, widgets/
│   └── __init__.py
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

Excel 形式の手術スケジュール(`手術予定表.xls`)を CSV 形式に変換します。

**機能**:
- 手術日時の解析・変換
- 患者情報の正規化
- 術式・医師名の統一

**使用例**:
```python
from service.surgery_schedule_processor import process_surgery_schedule

process_surgery_schedule('input.xls', 'output.csv')
```

### surgery_search_processor.py

眼科システムから出力された CSV(`眼科システム手術検索.csv`)を清掃・標準化します。

**主要処理**:
- `_select_required_columns()`: 必須カラムのみ抽出
- `_create_eye_side_column()`: 左右眼別カラム生成
- `_apply_replacements()`: 麻酔・入院・医師名の標準化
- `_remove_surgery_strings()`: 不要な術式情報削除
- `_filter_exclusion_keywords()`: 除外キーワード行を削除
- `_normalize_surgery_text()`: 術式テキスト正規化
- `_convert_surgery_date_format()`: 日付形式統一
- `_handle_duplicates()`: 重複レコード処理
- `_reorder_and_sort()`: カラム並び替え・ソート

**使用例**:
```python
from service.surgery_search_processor import process_eye_surgery_data

process_eye_surgery_data('input.csv', 'output.csv')
```

### surgery_comparator.py

スケジュールデータと検索データを突き合わせて差分を確認し、レポートを生成します。

**機能**:
- 2つのデータセット間の差分抽出
- 一致・不一致レコードの分類
- 比較結果を CSV で出力

**使用例**:
```python
from service.surgery_comparator import compare_surgery_data

compare_surgery_data('schedule.csv', 'search.csv', 'result.csv')
```

### surgery_error_extractor.py

エラー・不正なレコードを検出し、Excel レポート(`眼科手術指示確認.xlsx`)を生成します。

**機能**:
- 比較結果から不正レコード抽出
- Template Excel ファイルにデータを書き込み
- エラー情報の可視化

**使用例**:
```python
from service.surgery_error_extractor import surgery_error_extractor

surgery_error_extractor('input.csv', 'output.xlsx', 'template.xlsx')
```

### config_manager.py

設定ファイル(`config.ini`)の読込・保存・管理を行います。

**主要関数**:
- `load_config()`: config.ini から設定を読み込む
- `save_config()`: 設定を保存
- `get_paths()`: ファイルパスを取得
- `get_exclusion_line_keywords()`: 除外キーワード一覧を取得
- `get_surgery_strings_to_remove()`: 削除対象術式文字列を取得
- `get_replacement_dict()`: 置換辞書を取得

PyInstaller でビルドした実行ファイル(`sys.frozen`)でも、通常の Python 実行でも、正しく config.ini を読み込めます。

**使用例**:
```python
from utils.config_manager import load_config, save_config

config = load_config()
paths = config['Paths']
input_path = paths['surgery_search_data']

# 設定を修正して保存
config.set('Logging', 'log_level', 'DEBUG')
save_config(config)
```

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
exclusion_line_keywords = ★,霰粒腫,術式未定,先天性鼻涙管閉塞開放術,新患,ブジー
surgery_strings_to_remove = (クラレオントーリック),(クラレオンパンオプティクス),(クラレオンパンオプティクストーリック)
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
processed_surgery_search_data = C:\Shinseikai\OPHChecker\processed\processed_surgery_search.csv
surgery_schedule = C:\Shinseikai\OPHChecker\input\手術予定表.xls
processed_surgery_schedule = C:\Shinseikai\OPHChecker\processed\processed_surgery_schedule.csv
comparison_result = C:\Shinseikai\OPHChecker\processed\comparison_result.csv
template_path = C:\Shinseikai\OPHChecker\眼科手術指示確認.xlsx
output_path = C:\Shinseikai\OPHChecker\output
```

### [Replacements]

データ標準化用の置換辞書 (オリジナル値:統一値)

```ini
anesthesia_replacements = 球後麻酔:局所,局所麻酔:局所,点眼麻酔:局所,全身麻酔:全身
surgeon_replacements = 橋本義弘:橋本,植田芳樹:植田,増子杏:増子,田中伸弥:田中
inpatient_replacements = あやめ:入院,わかば:入院,さくら:入院,外来:外来
```

## 開発コマンド

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
# Pyright で型チェック (Python 3.13, standard mode)
pyright
```

### ビルド・バージョン管理

```bash
# 実行ファイルをビルド (バージョン自動更新)
python build.py

# 手動でバージョンを更新
python -c "from scripts.version_manager import update_version; update_version()"
```

#### ビルド処理について

`build.py` を実行すると:
1. `scripts/version_manager.py` の `update_version()` が呼ばれます
2. バージョン番号を自動インクリメント (セマンティックバージョニング準拠)
3. `app/__init__.py` の `__version__` と `__date__` を更新
4. `docs/README.md` のバージョン・日付も同期更新
5. PyInstaller でスタンドアロン実行ファイルを生成

生成ファイル: `dist/OPHChecker.exe`

### 依存パッケージ

主要パッケージ一覧は `requirements.txt` を参照してください。

```
pandas==1.5.3
openpyxl==3.1.5
pyinstaller==6.16.0
pyright==1.1.407
pytest==8.4.2
pytest-cov==7.0.0
coverage==7.11.0
```

## コード規約

### 型ヒント

- すべての関数パラメータに型ヒント必須
- すべての関数の戻り値に型ヒント必須
- Pyright 設定: `standard` モード, Python 3.13

```python
from typing import Optional
import pandas as pd

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
from service.surgery_search_processor import process_eye_surgery_data
```

### 日本語コメント

分かりにくいロジックのみ日本語でコメント。末尾のピリオド・句点は不要。

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

**解決策**: `build.py` で config.ini を bundling するよう設定

```python
"--add-data", "utils/config.ini:.",
```

`config_manager.py` は `sys.frozen` を検出して `sys._MEIPASS` からファイルを読み込みます。

### テスト実行時にモジュールが見つからない

**原因**: Python パスが正しく設定されていない

**解決策**: プロジェクトルートから pytest を実行

```bash
cd C:\Users\yokam\PycharmProjects\OPHChecker
python -m pytest tests/ -v
```

### メモリ不足でクラッシュ

**原因**: 大規模 CSV ファイル処理時にメモリ溢れ

**解決策**: pandas のチャンク読み込みを使用

```python
for chunk in pd.read_csv('large_file.csv', encoding='cp932', chunksize=10000):
    # chunk ごとに処理
    process_chunk(chunk)
```

## 注意事項

### ファイルパスについて

- デフォルト設定では `C:\Shinseikai\OPHChecker\` を使用しています
- 環境に合わせて `config.ini` のパスを修正してください
- Windows パスはバックスラッシュ `\` で指定します

### 日本語対応

- すべての手術データファイルは cp932 (Windows Shift-JIS) エンコーディングで保存されています
- Python コード内で日本語ファイルを読み書きする際は、必ず `encoding='cp932'` を指定してください
- UTF-8 指定でファイルを読み込むと文字化けします

### PyInstaller ビルド

- `build.py` を実行すると、`dist/` ディレクトリに `OPHChecker.exe` が生成されます
- ビルド時に自動でバージョンが更新されます
- 配布する際は `dist/` フォルダ全体をコピーしてください

### パフォーマンス

- 大規模ファイル処理時は、Python メモリ制限を確認してください
- 比較・抽出処理は複数のパスでデータを読み込むため、SSD 推奨です

## 変更履歴

詳細な変更履歴は [CHANGELOG.md](./CHANGELOG.md) を参照してください。

## ライセンス

[LICENSE](./LICENSE) を参照してください。

---

**開発者向け**: CLAUDE.md および CHANGELOG.md に詳細な開発ガイドラインがあります。
