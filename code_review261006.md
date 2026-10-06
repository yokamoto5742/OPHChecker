# コードレビュー 2026-10-06

対象: `main.py` / `app/` / `service/` / `utils/` / `widgets/`（本体 約1,900行）。`scripts/` と `build.py` は対象外。
観点: 可読性・メンテナンス性・KISS。

## 総評

`service/` の4処理は「パスを受け取りCSVを書く関数」に揃っており、`utils/csv_table.py` に入出力が集約されていて読みやすい。pandas依存を外した構成も妥当。

問題は3か所に集中している。

1. **結果が黙って誤る箇所が `surgery_search_processor.py` に2つある**（A-1, A-2）。確認漏れを見つけるためのツールなので最優先。
2. **`config_manager.py` は半分が重複と未使用コード**で、txt保存形式に入力値で壊れる穴がある（A-3, B-1, B-2）。
3. **`main_window.py` と `widgets/` はコピー&ペーストが多い**（B-3〜B-5）。動作に問題はないが、修正時に直し漏れが出る構造。

確認状況: A-1〜A-3 と A-6 は小さな入力で再現済み。A-4, A-5 はコードを読んだ判断で、実機での再現はしていない。

| 優先 | 項目 | 場所 |
|---|---|---|
| 高 | A-1 重複処理で患者が消える | `surgery_search_processor.py:110` |
| 高 | A-2 除外キーワードが正規表現として解釈される | `surgery_search_processor.py:89` |
| 高 | A-3 `,` `:` `%` を含む設定値が壊れる | `config_manager.py:249, 270` |
| 高 | A-4 ワーカースレッドからTkを直接操作 | `main_window.py:269` |
| 中 | A-5 初回実行時のパス検証が矛盾 | `main_window.py:156` |
| 中 | A-6 テスト3件が失敗中 | `tests/utils/test_config_manager.py` |
| 中 | B-1〜B-5 重複・未使用コードの整理 | `config_manager.py` ほか |
| 低 | C 細かい指摘 | 各所 |

---

## A. 不具合・リスク

### A-1. 同日・同一患者の重複処理で、患者が出力から消える

`service/surgery_search_processor.py:110` `_handle_duplicates`

「右1行＋左1行」の重複だけを想定しており、それ以外の組み合わせで結果が誤る。

| 入力（同日・同一患者） | 現在の出力 |
|---|---|
| 右 + 左 | 1行・術眼 `B`（想定どおり） |
| 左 + 左（左眼に2術式） | **0行。患者が比較対象から消える** |
| 右 + 右（右眼に2術式） | 2行とも術眼 `B`（実際は右のみ） |

消えた患者は比較CSVにも指示確認Excelにも出ないため、利用者は気づけない。

修正案: 重複グループ内の右・左の有無から術眼を決め、1行に集約する。

```python
def _handle_duplicates(rows: list[CsvRow]) -> list[CsvRow]:
    """同日・同一患者の行を1行にまとめ、術眼を右左の有無から決め直す"""
    merged_rows: dict[tuple[str, str], CsvRow] = {}
    for row in rows:
        first_row = merged_rows.setdefault((row['手術日'], row['患者ID']), row)
        if first_row is not row:
            first_row['右'] = first_row['右'] or row['右']
            first_row['左'] = first_row['左'] or row['左']
            first_row['術眼'] = _determine_eye_side(first_row)
    return list(merged_rows.values())
```

2行目以降の「手術」「医師」「麻酔」を捨ててよいかは業務判断が必要（現行も左眼の行を捨てている）。仕様を決めたうえでテストを追加すること。

### A-2. 除外キーワードが正規表現として解釈される

`service/surgery_search_processor.py:89`

```python
re.search(keyword, row[column])
```

キーワードは除外設定ダイアログから自由入力される文字列だが、正規表現として扱われる。

- `(仮` を登録 → `re.error` で分析全体が失敗する
- `術式未定(仮)` を登録 → 括弧がグループ扱いになり、`術式未定(仮)` という手術名に**一致しない**
- `.` `+` `*` `?` を含むキーワードは意図しない行まで除外する

手術名には括弧が頻出する（`(トーリック)` など）ので現実的に踏む。部分一致で十分なので `in` に変える。

```python
if not any(
    keyword in row[column]
    for column in ['氏名', '手術']
    for keyword in exclusion_line_keywords
)
```

これで `import re` の用途は日付判定の1か所だけになる。

### A-3. `,` `:` `%` を含む設定値が保存・読込で壊れる

`utils/config_manager.py:249-254, 270-271, 285, 299`

リストを `,` 区切り、置換を `:` 区切りの1行文字列にして保存しているが、ダイアログ側は入力値を検証していない。

| 入力 | 結果 |
|---|---|
| キーワード `a,b` | 読込時に `a` と `b` の2件になる |
| 置換 `A,B → x` | `{'B': 'x'}` になり `A` が消える |
| 置換 `10:30 → y` | `{'10': '30:y'}` になる |
| `%` を含む値 | `configparser` の補間エラーで保存に失敗する |

最小の対処はダイアログの `on_ok` で `,` `:` `%` を含む入力を拒否すること（追加・編集は B-4 で1か所にまとまる）。`%` だけは `ConfigParser(interpolation=None)` でも解消できる。
保存形式をJSONに変えれば根本解決するが、既存txtの移行が必要なので今は勧めない。

### A-4. ワーカースレッドからTkウィジェットを直接操作している

`app/main_window.py:138-141, 269-291`

`_run_analysis` は別スレッドで動くが、その中で `log_text.insert`、`root.update()`、`status_var.set`、`start_button.config`、`messagebox.showerror` を呼んでいる。Tkinterはメインスレッド以外からの操作を保証しておらず、特にワーカー側の `root.update()` は再入の原因になる。現状動いていても、フリーズや `RuntimeError: main thread is not in main loop` が不定期に出る類の問題。

処理は数秒で終わる想定なので、KISSの観点では **スレッドをやめて同期実行する**のが最も単純（`_log_message` の `root.update()` で画面は更新される）。スレッドを残すなら、UI操作をすべて `self.root.after(0, ...)` 経由にする。

関連: `_close_application`（`:405`）は「実行中か」をボタンの `state` で判定している。ウィンドウ右上の×には `WM_DELETE_WINDOW` が設定されていないため、このガードは×で閉じると効かない。同期実行にすればガード自体が不要になる。

### A-5. 初回実行時のパス検証が矛盾している

`app/main_window.py:156, 277`

- `_validate_config` は `output_path` の存在を必須にしているが、直後の `_run_analysis` が `mkdir(parents=True, exist_ok=True)` で作成する。出力フォルダが無い初回は「ファイルが見つかりません」で止まり、`mkdir` に到達しない。
- 逆に `processed_*` の出力先フォルダと `template_path` は検証も作成もされず、無い場合は処理途中で例外になる（テンプレートは3ステップ完了後の4ステップ目で初めて分かる）。

`required_paths` を入力である `surgery_search_data` / `surgery_schedule` / `template_path` にし、出力先フォルダは `mkdir` で作る形に揃える。

### A-6. テストが3件失敗している

`pytest tests/` の結果は 86 passed / **3 failed**。

- `test_save_replacement_dict`
- `test_save_exclusion_line_keywords`
- `test_save_surgery_strings_to_remove`

いずれも `ValueError: excludeitems_file のパスが設定されていません`。保存先がtxtに変わった後、テスト用iniに `excludeitems_file` / `replacements_file` が追加されていない。fixtureで `tmp_path` 配下のtxtを指定すれば直る。
`pyright` は19件のエラーがあるが、すべて `tests/` 配下（未使用変数と `ws` の `None` 可能性）で、本体は0件。

### A-7. その他の小さなリスク

- **空データで完了サマリーが落ちる** — `main_window.py:254-255`。除外の結果0件になると `min([])` で `ValueError`。4処理が成功した後に「エラーが発生しました」と表示される。
- **設定ファイルのエラーが見えない** — `config_manager.py` は `print` で通知しているが、`--windowed` ビルドではコンソールが無く表示されない。`logging` に統一する（ただし `load_config` は `setup_logging` より前に呼ばれるので、そこは例外をそのまま上げるだけでよい）。
- **txtが壊れていると既定値で上書きされる** — `_load_exclude_items_config`（`:76`）は読込失敗を握りつぶして `DEFAULT_CONFIG` を返す。その状態でダイアログから保存すると、利用者が積み上げた設定が既定値に置き換わる。ファイルが**存在するのに読めない**場合は例外を上げるべき。

---

## B. 簡素化（KISS）

### B-1. `config_manager.py` の重複を1組にまとめる

除外項目用と置換用で、パス取得・読込・保存がほぼ同一コードで2組ある（`:54-142`、約90行）。違うのはパスのキー名、セクション名、メッセージだけ。

```python
def _load_settings_file(config: configparser.ConfigParser, path_key: str, section: str) -> configparser.ConfigParser:
    """txtを読み込み、不足キーをDEFAULT_CONFIGで補う"""
    settings = configparser.ConfigParser()
    file_path = config.get('Paths', path_key, fallback='')
    if file_path and os.path.exists(file_path):
        with open(file_path, encoding='utf-8') as settings_file:
            settings.read_file(settings_file)
    if not settings.has_section(section):
        settings.add_section(section)
    for key, default_value in DEFAULT_CONFIG[section].items():
        if not settings.has_option(section, key):
            settings.set(section, key, default_value)
    return settings
```

保存側も同様に1関数にできる。あわせて以下も整理できる。

- `get_exclusion_line_keywords` と `get_surgery_strings_to_remove`、`save_*` の2つはキー名以外同一（`:220-229, 276-301`）。
- `get_replacement_dict` / `save_replacement_dict` の `section` 引数は常に `'Replacements'`。引数から外せる。
- 1回の操作でtxtを何度も読み書きしている。置換ダイアログは開くときに3回読み、保存時に3回読んで3回書く。3種類まとめて読む・書く関数にすれば呼び出し側（`main_window.py:336-338, 350-352` と `surgery_search_processor.py:62-64`）も1行になる。

### B-2. 未使用コード・未使用設定を削除する

| 対象 | 状況 |
|---|---|
| `get_exclude_items`（`config_manager.py:215`） | どこからも呼ばれていない |
| `get_dialog_settings`（`:195`）と `[DialogSize]` | テストからしか呼ばれていない |
| `config.ini` の `[ExcludeItems]` `[Replacements]` | 読まれていない。実際に使われるのはtxtと `DEFAULT_CONFIG` |
| `utils/excludeitems.txt` `utils/replacements.txt` | 読まれていない（実際は `C:\Shinseikai\OPHChecker\` 側） |
| `[LOGGING] log_level` | 読まれていない（`log_rotation.py:23` で `INFO` 固定） |
| `main_window.py:322, 353` の `save_config(self.config)` | `self.config` は変更されていないので、同じ内容を書き戻すだけ |
| 比較CSVの `手術日_比較` 列（`surgery_comparator.py:32`） | 常に `True`。抽出側でも使っていない |

特に既定値が **`DEFAULT_CONFIG`・`config.ini`・`utils/*.txt` の3か所**にあり、しかも内容が食い違っている（`utils/excludeitems.txt` にだけ `新患` `ブジー`、`utils/replacements.txt` にだけ `あや:入院`）。どれが正か分からない状態なので、`DEFAULT_CONFIG` だけを残すのがよい。`utils/*.txt` を配布用の雛形として残すなら、その旨をREADMEに書く。

### B-3. `main_window.py` の繰り返しをまとめる

- **ボタン生成（`:58-117`）** — 5個のボタンが `text` / `command` / `bg` 以外同一で60行。`_create_button(parent, text, command, bg=None)` にすれば各1行。`grid_rowconfigure(4, weight=1)` も2回呼んでいる（`:49, 126`）。
- **ステップ実行（`:201-250`）** — `_process_surgery_schedule` など3つは `_execute_step` を呼ぶだけの薄いラッパー。`_extract_surgery_errors` は `_execute_step` と同じ try/except を再実装している。`_run_analysis` 内に並べれば4メソッドと `step_num` / `total_steps` の手書き番号が消える。

  ```python
  steps = [
      ("手術予定表の処理", lambda: process_surgery_schedule(paths['surgery_schedule'], paths['processed_surgery_schedule'])),
      ("手術検索データの処理", lambda: process_eye_surgery_data(paths['surgery_search_data'], paths['processed_surgery_search_data'])),
      ...
  ]
  for step_num, (step_name, run_step) in enumerate(steps, start=1):
      self._execute_step(step_num, len(steps), step_name, run_step)
  ```

- **エラーの二重記録** — `_execute_step` がログ出力して再送出し、`_handle_analysis_error` が同じ例外をもう一度ログ出力する。トレースバックが2回ログに残る。記録は外側の1か所でよい。
- **設定ダイアログ（`:305-361`）** — `_open_exclude_items` と `_open_replacements` は同じ構造。B-1 でまとめて読み書きする関数を作れば、差分は「ダイアログのクラス・読込関数・保存関数・名称」だけになる。
- `str(e)` をf文字列内で多用しているが `{e}` で同じ。

### B-4. `widgets/` の追加・編集ダイアログを共通化する

- `ExcludeItemsDialog._add_item` と `_edit_item`（`:69-159`）は約40行ずつで、違いは初期値と確定時の処理だけ。
- `ReplacementsDialog._add_replacement` と `_edit_replacement`（`:62-186`）も同様。
- さらに2つのダイアログ間でも、Toplevel生成・OK/キャンセルボタン・Enter/Escapeバインド・中央配置が同一。

`BaseDialog` に「ラベルと初期値のリストを受け取り、入力値を返す」小さな入力ダイアログを1つ用意すれば、4メソッド（約170行）が呼び出し側の数行ずつになる。A-3 の入力チェックもそこに1回書けば済む。

その他:

- `replacements_dialog.py:48-53` — `tab_type` で分岐して `self.anesthesia_listbox` などに代入しているが、本体では使っておらずテストが参照するだけ。
- `replacements_dialog.py:122, 198` — 表示文字列 `"キー → 値"` を `split(" → ")` して元のキーを復元している。値に ` → ` が含まれると壊れる。`list(replacements_dict)[index]` で取れる。
- `replacements_dialog.py:160-161` — キーを変更すると辞書上は末尾に移動するが、リストボックス上は元の位置のまま。保存後に開き直すと並び順が変わる。

### B-5. 列名・判定値の定義を1か所にする

同じ列リストが4ファイルに別々に書かれている。

- `OUTPUT_COLUMNS` が `surgery_search_processor.py:23`、`surgery_schedule_processor.py:13`、`surgery_comparator.py:14`、`surgery_error_extractor.py:10` にある
- `surgery_error_extractor.py:9` の `COMPARISON_COLUMNS` は `surgery_comparator.py:12` の `COMPARE_COLUMNS` に `_比較` を付けたもの
- `'未入力'` は比較側が定数 `NOT_ENTERED`、抽出側（`:43`）は文字列リテラル。`'True'` / `'False'` も同様

比較項目を1つ増やすと4ファイルの修正が必要になる。`utils/csv_table.py` に基本列・比較列・判定値を定義し、各ファイルは参照するだけにする。

---

## C. 細かい指摘

- **`process_eye_surgery_data` だけ内部で `load_config()` を呼ぶ**（`surgery_search_processor.py:140`）。他の3処理はパスだけを受け取るのに対し、これだけ設定ファイルに暗黙依存している。置換辞書と除外リストを引数で受け取れば4処理の形が揃い、テストでパッチを当てる必要もなくなる。
- **行リストを書き換えつつ返している**（`surgery_search_processor.py:50-107`）。`_apply_replacements` などは引数を破壊的に変更したうえで同じリストを返すため、`rows = f(rows)` という呼び出しが「新しいリストを返す」ように見える。変更するなら `None` を返す、のどちらかに揃える。
- **処理順への依存がコメントされていない**（`:147-149`）。文字列削除はNFKC正規化の前に行う必要がある（`(アイハンストーリックⅡ)` の `Ⅱ` が正規化で `II` に変わるため）。順序を入れ替えると黙って一致しなくなるので、1行コメントが欲しい。
- **`_convert_surgery_date_format` が `parse_date` を使っていない**（`:50-57`）。`csv_table.parse_date` は2桁年・4桁年の両方を扱えるので、独自の判定と `re` が不要になる。
- **`surgery_error_extractor.py:59`** — `if ws is not None` で黙ってスキップすると、データの無いExcelが正常終了として出力される。`None` なら例外にする。`:20-23` の `try/except` も、比較側で日付を正規化済みなので到達しない。`:66` は変数の無いf文字列。
- **`log_rotation.py`** — `suffix` を独自形式にしたため標準の `backupCount` による削除が効かず、それを補うために `cleanup_old_logs` を自作している。`suffix` の上書きをやめれば `cleanup_old_logs` ごと不要になる。ほか、`import configparser` の位置がimport順の規約と異なる、戻り値の型ヒントが無い（`save_config` も同様）、`get_paths` などの戻り値が `dict` で型引数が無い。
- **UIメッセージの規約と実装が合っていない** — `.claude/rules/python-coding.md` は「`constants.py` で一元管理」としているが、`constants.py` は存在せず、全メッセージが文字列リテラル。この規模なら直書きのままでも読みやすいので、規約のほうを現状に合わせる選択肢もある。どちらにするか決めること。
- **ドキュメントの食い違い** — `CLAUDE.md` は Python 3.13以上、`pyproject.toml` は `>=3.12`。`build.py` は `--onefile` を指定していないため、出力は `dist/眼科手術指示確認/眼科手術指示確認.exe`（フォルダ形式）になるはずで、`CLAUDE.md` の「`dist/眼科手術指示確認.exe`」「一時展開先」という記述と合わない（ビルドしての確認はしていない）。`.claude/rules/testing.md` のテストファイル例も実在しない。

---

## 推奨する進め方

1. **A-6** テスト3件を直す（以降の変更の安全網）
2. **A-1, A-2** を再現テスト付きで修正する。A-1 は先に業務仕様を確認する
3. **A-3, A-5, A-7** を修正する
4. **B-2** 未使用コードを削除し、続けて **B-1** で `config_manager.py` をまとめる
5. **A-4** 同期実行に切り替え、あわせて **B-3** で `main_window.py` を整理する
6. **B-4, B-5, C** は該当箇所に手を入れるときに対応する

1〜3 は挙動の修正、4〜6 は挙動を変えないリファクタリングなので、コミットを分けること。
