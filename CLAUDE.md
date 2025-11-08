# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## House Rules:
- 文章ではなくパッチの差分を返す。
- コードの変更範囲は最小限に抑える。
- コードの修正は直接適用する。
- Pythonのコーディング規約はPEP8に従います。
- KISSの原則に従い、できるだけシンプルなコードにします。
- 可読性を優先します。一度読んだだけで理解できるコードが最高のコードです。
- Pythonのコードのimport文は以下の適切な順序に並べ替えてください。
標準ライブラリ
サードパーティライブラリ
カスタムモジュール 
それぞれアルファベット順に並べます。importが先でfromは後です。

## CHANGELOG
このプロジェクトにおけるすべての重要な変更は日本語でdcos/CHANGELOG.mdに記録します。
フォーマットは[Keep a Changelog](https://keepachangelog.com/ja/1.1.0/)に基づきます。

## Automatic Notifications (Hooks)
自動通知は`.claude/settings.local.json` で設定済：
- **Stop Hook**: ユーザーがClaude Codeを停止した時に「作業が完了しました」と通知
- **SessionEnd Hook**: セッション終了時に「Claude Code セッションが終了しました」と通知

## クリーンコードガイドライン
- 関数のサイズ：関数は50行以下に抑えることを目標にしてください。関数の処理が多すぎる場合は、より小さなヘルパー関数に分割してください。
- 単一責任：各関数とモジュールには明確な目的が1つあるようにします。無関係なロジックをまとめないでください。
- 命名：説明的な名前を使用してください。`tmp` 、`data`、`handleStuff`のような一般的な名前は避けてください。例えば、`doCalc`よりも`calculateInvoiceTotal` の方が適しています。
- DRY原則：コードを重複させないでください。類似のロジックが2箇所に存在する場合は、共有関数にリファクタリングしてください。それぞれに独自の実装が必要な場合はその理由を明確にしてください。
- コメント:分かりにくいロジックについては説明を加えます。説明不要のコードには過剰なコメントはつけないでください。
- コメントとdocstringは必要最小限に日本語で記述し、文末に"。"や"."をつけないでください。

## Project Overview

OPHChecker is a Python application for processing ophthalmology surgical data. It handles two main data processing workflows:
1. **Surgery Schedule Processing** (`service/surgery_schedule_processor.py`): Converts Excel surgery schedule files to CSV format with standardized columns
2. **Eye Surgery Data Processing** (`service/surgery_search_processor.py`): Processes CSV files from the ophthalmology system, cleaning and standardizing anesthesia/inpatient data, removing specific entries

The project is built as a standalone executable using PyInstaller, with version management automated through scripts.

## Architecture

### Directory Structure
```
OPHChecker/
├── app/              # Application metadata (__version__, __date__)
├── service/          # Core data processors
│   ├── surgery_schedule_processor.py
│   └── surgery_search_processor.py
├── utils/            # Configuration management
│   ├── config_manager.py (handles config.ini for both script and PyInstaller builds)
│   └── config.ini
├── scripts/          # Build and version automation
│   └── version_manager.py (updates app/__init__.py and docs/README.md)
├── tests/            # Test files (currently minimal)
├── docs/             # Documentation (README.md)
└── build.py          # PyInstaller build script
```

### Key Components

**Service Layer**: Data processors use pandas for Excel/CSV manipulation. Both processors:
- Accept input/output file paths as parameters
- Handle Japanese encoding (cp932/Shift-JIS) for file I/O
- Print status messages to console

**Configuration**: `utils/config_manager.py` provides:
- `load_config()`: Reads config.ini (handles both normal Python and PyInstaller frozen executables)
- `save_config()`: Writes configuration changes
- Path resolution: Uses `sys._MEIPASS` for PyInstaller builds, `__file__` for normal execution

**Version Management**: `scripts/version_manager.py` automates:
- Version bumping (patch-level increment from semantic versioning)
- Synchronizing version in `app/__init__.py` with regex-based updates
- README.md version/date updates
- Date formatting (Japanese calendar notation: "YYYY年MM月DD日")

## Development Commands

### Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Activate virtual environment (if using .venv)
.venv\Scripts\activate
```

### Testing
```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ -v --cov

# Run specific test file
python -m pytest tests/test_main.py -v
```

### Type Checking
```bash
# Run pyright (configured in pyrightconfig.json)
pyright
```

### Build & Version Management
```bash
# Build executable (updates version automatically)
python build.py

# Manually update version (from project root)
python -c "from scripts.version_manager import update_version; update_version()"
```

## Code Standards

### Type Hints
- Use type hints for all function parameters and return types
- Pyright is configured with `standard` mode, Python 3.13
- Excluded from type checking: tests, scripts

### Configuration
- Hard-coded paths in service processors are examples; use `config_manager.py` to handle file paths properly
- File encoding: Use `encoding='utf-8'` for text files, `encoding='cp932'` for Japanese data files

### Japanese Comments
- Use Japanese comments sparingly, only for unclear logic
- No periods at end of comments
- Follow existing style from `surgery_search_processor.py` and `version_manager.py`

### Dependencies
Key packages:
- `pandas`: Data processing (Excel, CSV operations)
- `pyinstaller`: Executable building
- `pyright`: Type checking
- `pytest`: Testing framework
- `coverage`: Test coverage reporting

## Common Development Tasks

### Processing Surgery Data
Both processors follow the same pattern:
```python
from service.surgery_schedule_processor import process_surgery_schedule
# or
from service.surgery_search_processor import process_eye_surgery_data

process_surgery_schedule(input_path, output_path)  # Excel → CSV
process_eye_surgery_data(input_path, output_path)   # CSV → Cleaned CSV
```

### Adding New Data Processors
1. Create function in `service/` directory
2. Accept `input_path` and `output_path` parameters
3. Use pandas for data manipulation
4. Handle `cp932` encoding for Japanese data
5. Add type hints for all parameters
6. Include docstring with Japanese description

### Modifying Configuration
Use `utils/config_manager.py`:
```python
from utils.config_manager import load_config, save_config
config = load_config()
config.set('section', 'key', 'value')
save_config(config)
```

## Important Notes

- **PyInstaller Builds**: The application supports both normal Python execution and PyInstaller frozen executables. Config loading checks `sys.frozen` to determine paths.
- **Japanese File Encoding**: All user-facing data files use `cp932` (Windows Shift-JIS). Use this encoding when reading/writing CSV and Excel files.
- **Version Management**: Version is stored in `app/__init__.py` and synchronized with `docs/README.md` via version_manager.py during builds.
- **Input/Output Paths**: Service processors use hard-coded paths in their `__main__` sections as examples. In production, use `config_manager.py` or pass paths dynamically.
