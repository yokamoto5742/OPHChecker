# 変更履歴

このファイルは、OPHCheckerプロジェクトにおけるすべての重要な変更を記録します。
フォーマットは [Keep a Changelog](https://keepachangelog.com/ja/1.1.0/) に基づいています。

## [Unreleased]

`code_review261006.md` の指摘（A-1〜A-7, B-1〜B-5）への対応。

### 修正
- 同日・同一患者の重複処理で、左眼に2術式ある患者が出力から消える／右眼に2術式ある患者の術眼が `B` になる不具合を修正。1行にまとめ、術眼を右左の有無から決める（2行目以降の手術・医師・麻酔は捨てる）
- 除外キーワードが正規表現として解釈され、括弧を含むキーワードでエラーになる・一致しない不具合を修正（部分一致で判定）
- 除外設定・置換設定で `,` `:` `%` を含む値を保存すると設定が壊れるため、入力時に拒否するように変更
- 分析処理をワーカースレッドではなくメインスレッドで同期実行するように変更（スレッドからのTk操作によるフリーズ・エラーの防止）。右上の×でも実行中は閉じないようにした
- 初回実行時、出力フォルダが無いと検証エラーで止まる不具合を修正。出力先フォルダ（output / processed）は自動作成し、テンプレートの有無を実行前に検証する
- 対象データが0件のとき、4処理の成功後に完了サマリーでエラーになる不具合を修正
- 除外設定・置換設定のtxtが壊れていると既定値で上書きされる不具合を修正（読めない場合はエラーにする）
- 置換設定で、値に ` → ` を含む項目を編集・削除できない不具合と、置換前を変更すると保存後の並び順が変わる不具合を修正
- 失敗していた `test_config_manager.py` のテスト3件を修正

### 変更
- `config_manager.py` の除外設定用・置換設定用の重複コードを統合。公開関数を `get_exclude_items` / `save_exclude_items` / `get_replacements` / `save_replacements` に変更
- `config_manager.py` のエラー通知を `print` から例外の送出に変更
- `main_window.py` のボタン生成・ステップ実行・設定ダイアログ呼び出しの重複を整理。例外のログ出力を1回にした
- 追加・編集の入力ダイアログを `BaseDialog._ask_values` に共通化
- 列名と判定値（一致・不一致・未入力）の定義を `utils/csv_table.py` に集約

### 削除
- 未使用の `get_exclude_items`（旧）・`get_dialog_settings`、`config.ini` の `[DialogSize]` `[ExcludeItems]` `[Replacements]` `log_level`
- 読まれていなかった `utils/excludeitems.txt` `utils/replacements.txt`（既定値は `DEFAULT_CONFIG` のみ）
- 比較CSVの `手術日_比較` 列（常に `True` で未使用）

## [1.1.0] - 2026-10-05

### 変更
- pandasへの依存を削除し、標準ライブラリのcsvとxlrd・openpyxlのみで処理するように変更
  - 実行ファイルのサイズを約83MBから約30MBに削減
  - CSVの読み書きと日付・患者IDの正規化を `utils/csv_table.py` に集約
- `build.py` でnumpy・pandasを同梱対象から除外
- テストコードからpandasを削除

### 修正
- 予定表に該当のない患者（未入力）が含まれると、不一致のみの行が眼科手術指示確認ファイルに出力されない不具合を修正

## [1.0.5] - 2025-12-26

### 変更
- surgery_error_extractorの不要なコメントを削除し、コードを簡潔化
- serviceモジュール内の不要なcast呼び出しを削除し、コード品質を向上

## [1.0.4] - 2025-11-22

### 追加
- excludeitems.txt、replacements.txtの外部設定ファイルをサポート
  - 除外項目・置換項目の設定を独立したファイルで管理可能に
  - config.iniから外部ファイルのパスを参照可能

### 変更
- config_manager.pyの機能拡張
  - `_load_exclude_items_config()`でexcludeitems.txtから除外項目設定を読み込み
  - `_load_replacements_config()`でreplacements.txtから置換項目設定を読み込み
  - `_save_exclude_items_config()`で除外項目設定をファイルに保存
  - `_save_replacements_config()`で置換項目設定をファイルに保存
  - 設定ファイルの構造を改善し、複数ファイルからの設定読み込みに対応
- config.iniの設定項目
  - ExcludeItemsセクションに詳細な除外キーワードと除外文字列を追加
  - Pathsセクションにexcludeitems_file、replacements_fileパスを追加
  - 
### 技術的な改善
- プロジェクト構造を整理
  - scripts/project_structure.txtを更新し、プロジェクトの構造をドキュメント化

## [1.0.3] - 2025-11-22

### 変更
- docs/README.mdを大幅に改善し、コードベースとの整合性を確保
  - 利用可能なプロセッサ機能（4つのプロセッサ）の説明を明確化
  - config_managerの関数仕様（16個の関数）をドキュメント化
  - 516行から453行に簡潔化しながら、より充実した内容に改善
  - 使用方法、主要モジュール、開発方法、コード規約のセクションを整理
  - トラブルシューティング、セットアップ手順、具体的な使用例を明確化

## [1.0.2] - 2025-11-18

### 追加
- surgery_error_extractorで真偽値データを「一致」「不一致」に変換する機能を追加

### 変更
- surgery_error_extractorの手術日付変換処理をテンプレート形式に対応するようリファクタリング
- 手術日付文字列をdatetimeオブジェクトに変換する処理を改善
- main_windowのウィンドウタイトルを日本語に変更

## [1.0.1] - 2025-11-16

### 追加
- pandas-stubsを依存関係に追加し、型チェックの精度を向上

### 変更
- プロダクト名を「眼科手術指示確認」に更新（build.py、app/__init__.py、app/main_window.py）
- ウィンドウタイトルとログメッセージを新しいプロダクト名に更新

### 修正
- 設定ファイルのパスを修正し、環境依存性を解消
- surgery_schedule_processor.pyに型ヒントを追加し、コードの型安全性を向上

### 改善
- パース処理ロジックを改善し、データ処理の精度を向上させる新しいパースロジックを追加
