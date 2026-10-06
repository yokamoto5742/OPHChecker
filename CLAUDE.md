# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

すべての回答は必ず日本語で回答してください。
コーディング規約・コミット規約・応答スタイルは `.claude/rules/` を参照する。

## コマンド

パッケージ管理は uv（`uv.lock`）。Python 3.13以上。

```bash
uv sync                          # 依存関係のインストール
uv run python main.py            # アプリ起動
pyright                          # 型チェック（対象: app, service, utils, tests）
python build.py                  # PyInstallerでexe作成 → dist/眼科手術指示確認.exe
```

テスト実行コマンドは `.claude/rules/testing.md` を参照（記載のファイル例は古いので、実在するテストファイルを指定すること）。

## アーキテクチャ

Tkinter GUI（`app/main_window.py`）が `service/` の4処理をメインスレッドで順に同期実行する（Tkはメインスレッド以外から操作できないため、スレッドは使わない）。

1. `process_surgery_schedule`: 手術予定表Excel(.xls)をCSVに変換
2. `process_eye_surgery_data`: 眼科システムのCSVを整形
3. `compare_surgery_data`: 上記2つを比較して比較CSVを出力
4. `surgery_error_extractor`: FALSE・未入力の行を抽出し、Excelテンプレートにタイムスタンプ付きで出力

各processorはGUIに依存せず、入出力ファイルパスを引数で受け取る。除外項目・置換リストは `widgets/` のダイアログで編集する。

## 注意点

- 文字コード: データCSV・Excelはcp932、ソースおよびtxt/iniはUTF-8
- 設定は `utils/config.ini` に集約（環境変数は使わない）。パスは `C:\Shinseikai\OPHChecker\...` にハードコードされており、除外項目・置換のtxtも `utils/` ではなくそちらを読む
- txtが存在しない場合は `config_manager.DEFAULT_CONFIG` の値に黙ってフォールバックする
- PyInstaller実行時は `config.ini` が `sys._MEIPASS`（一時展開先）から読まれるため、`save_config` の内容は終了時に失われる。永続化されるのはtxtのみ
- `pyright` は `widgets/` と `main.py` を対象にしていない
- 変更履歴は `docs/CHANGELOG.md` に日本語・Keep a Changelog形式で記載する
- 古い参照が残っている: README と `scripts/version_manager.py` は存在しない `requirements.txt` / `docs/README.md` を前提にしている（`version_manager` は警告のみで成功扱いになる）
