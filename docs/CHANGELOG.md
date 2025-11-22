# 変更履歴

このファイルは、OPHCheckerプロジェクトにおけるすべての重要な変更を記録します。
フォーマットは [Keep a Changelog](https://keepachangelog.com/ja/1.1.0/) に基づいています。

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
