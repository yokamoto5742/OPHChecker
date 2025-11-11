# 変更履歴

このファイルは、OPHCheckerプロジェクトにおけるすべての重要な変更を記録します。
フォーマットは [Keep a Changelog](https://keepachangelog.com/ja/1.1.0/) に基づいています。

## [Unreleased]

### 追加
- TKinterによるGUIアプリケーション(gui.py)を追加
- 分析開始ボタン: 手術予定表処理、眼科システムデータ処理、データ比較を順序実行
- 設定ボタン: config.iniファイルをエディタで開く
- 実行ログ表示とステータスバーを追加
- 手術予定表処理で術式列を全角カナに変換する機能を追加

### 変更
- surgery_schedule_processor.py: ハードコードされたファイルパスをconfig.iniから読み込むように変更
- config_manager.py: processed_surgery_scheduleパスキーを追加

### 修正

### 削除
