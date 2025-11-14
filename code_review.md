## 🔴 重大な問題

### 1. ハードコードされたファイルパス

**ファイル**: `service/surgery_error_extractor.py:49`

```python
template_path = r'C:\Shinseikai\OPHChecker\眼科手術指示確認.xlsx'
```

**問題点**:
- 環境依存のパスがハードコードされている
- 他の環境での実行が不可能

**推奨対応**:
- `config.ini`の`Paths`セクションに`template_path`を追加し、設定から読み込む
- すでに`get_paths()`に`template_path`が存在するため、それを利用する

```python
# 修正例
from utils.config_manager import get_paths, load_config

config = load_config()
paths = get_paths(config)
template_path = paths['template_path']
wb = load_workbook(template_path)
```

---

### 2. 不適切な例外処理

**ファイル**: `service/surgery_comparator.py:36-41`

```python
try:
    df_search['手術日'] = pd.to_datetime(df_search['手術日'], format='%y/%m/%d').dt.strftime('%Y/%m/%d')
except:
    df_search['手術日'] = pd.to_datetime(df_search['手術日']).dt.strftime('%Y/%m/%d')
```

**問題点**:
- 空の`except`はすべての例外を無視する
- どの例外が発生したか追跡できない
- バグの原因特定が困難

**推奨対応**:
```python
try:
    df_search['手術日'] = pd.to_datetime(df_search['手術日'], format='%y/%m/%d').dt.strftime('%Y/%m/%d')
except (ValueError, TypeError) as e:
    logging.warning(f"手術日のフォーマット変換に失敗したため、自動判定を使用します: {e}")
    df_search['手術日'] = pd.to_datetime(df_search['手術日']).dt.strftime('%Y/%m/%d')
```

---

### 3. 関数の重複定義

**ファイル**:
- `utils/config_manager.py:52-69`
- `utils/log_rotation.py:8-12`

両方のファイルに`load_config()`関数が存在します。

**問題点**:
- DRY原則違反
- 将来的なメンテナンス時に混乱の原因

**推奨対応**:
- `utils/log_rotation.py`の`load_config()`を削除
- `utils/config_manager.py`の`load_config()`のみを使用

```python
# log_rotation.py を修正
import configparser
from utils.config_manager import load_config  # これを使う
```

---

## 🟠 改善推奨事項

### 5. 長い関数のリファクタリング

#### 5.1. `app/main_window.py::_run_analysis()`

**ファイル**: `app/main_window.py:178-264` (87行)

**問題点**:
- 単一の関数が複数の責任を持つ
- 4つの処理ステップが1つの関数に詰め込まれている
- テストが困難

**推奨対応**:
各処理ステップを独立した関数に分割：

```python
def _run_analysis(self) -> None:
    try:
        logging.info("分析処理を開始します")
        self._log_analysis_header()

        paths = get_paths(self.config)
        Path(paths["output_path"]).mkdir(parents=True, exist_ok=True)

        self._process_surgery_schedule(paths)
        self._process_surgery_search(paths)
        self._compare_surgery_data(paths)
        self._extract_surgery_errors(paths)

        self._log_completion_summary(paths['processed_surgery_search_data'])
        self._open_output_folder(paths["output_path"])

    except Exception as e:
        self._handle_analysis_error(e)
    finally:
        self.start_button.config(state=tk.NORMAL)

def _process_surgery_schedule(self, paths: dict) -> None:
    """手術予定表の処理"""
    self._log_message("\n[1/4] 手術予定表の処理を開始...")
    logging.info("[1/4] 手術予定表の処理を開始")

    try:
        process_surgery_schedule(
            paths['surgery_schedule'],
            paths['processed_surgery_schedule']
        )
        self._log_message("✓ 手術予定表の処理が完了しました")
        logging.info("手術予定表の処理が完了しました")
    except Exception as e:
        self._log_message(f"✗ エラー: {str(e)}")
        logging.error(f"手術予定表の処理中にエラーが発生: {str(e)}", exc_info=True)
        raise

# 同様に _process_surgery_search(), _compare_surgery_data(), _extract_surgery_errors() を分割
```

---

#### 5.2. `service/surgery_search_processor.py::process_eye_surgery_data()`

**ファイル**: `service/surgery_search_processor.py:15-112` (98行)

**問題点**:
- 複数のデータ変換ロジックが1つの関数に集中
- 各ステップが明確に分離されていない

**推奨対応**:
処理を意味のある単位で分割：

```python
def process_eye_surgery_data(input_file_path: str, output_file_path: str) -> None:
    """手術検索データのCSVファイルを処理"""
    config = load_config()
    df = pd.read_csv(input_file_path, encoding='cp932')

    df_processed = _select_required_columns(df)
    df_processed = _convert_surgery_date_format(df_processed)
    df_processed = _apply_replacements(df_processed, config)
    df_processed = _remove_surgery_strings(df_processed, config)
    df_processed = _filter_exclusion_keywords(df_processed, config)
    df_processed = _normalize_surgery_text(df_processed)
    df_processed = _create_eye_side_column(df_processed)
    df_processed = _handle_duplicates(df_processed)
    df_processed = _reorder_and_sort(df_processed)

    df_processed.to_csv(output_file_path, index=False, encoding='cp932')
    logging.info(f"手術検索データの処理が完了しました: {output_file_path}")

def _select_required_columns(df: pd.DataFrame) -> pd.DataFrame:
    """必要な列を選択"""
    required_columns = [
        '手術日', '患者ID', '氏名', '手術', '医師',
        '麻酔', '病名', '入外', '右', '左', '術前'
    ]
    return df[required_columns].copy()

def _convert_surgery_date_format(df: pd.DataFrame) -> pd.DataFrame:
    """手術日をYYYY/MM/DD形式に変換"""
    df['手術日'] = pd.to_datetime(df['手術日'], format='%y/%m/%d').dt.strftime('%Y/%m/%d')
    return df

def _apply_replacements(df: pd.DataFrame, config: configparser.ConfigParser) -> pd.DataFrame:
    """麻酔、術者、入外の値を置換"""
    anesthesia_replacements = get_replacement_dict(config, 'Replacements', 'anesthesia_replacements')
    df['麻酔'] = df['麻酔'].map(
        lambda x: anesthesia_replacements.get(x, x) if pd.notna(x) else x
    )

    surgeon_replacements = get_replacement_dict(config, 'Replacements', 'surgeon_replacements')
    df['医師'] = df['医師'].replace(surgeon_replacements)

    inpatient_replacements = get_replacement_dict(config, 'Replacements', 'inpatient_replacements')
    df['入外'] = df['入外'].map(
        lambda x: inpatient_replacements.get(x, x) if pd.notna(x) else x
    )

    return df

# 残りのヘルパー関数も同様に作成
```

**メリット**:
- 各関数の目的が明確
- 単体テストが容易
- 処理フローが理解しやすい
- 将来的な変更が局所化される

---

### 12. 条件式の可読性

**ファイル**: `service/surgery_search_processor.py:83-88`

```python
# 現在
df_processed['術眼'] = df_processed.apply(
    lambda row: 'B' if row['右'] == '○' and row['左'] == '○'
                else 'R' if row['右'] == '○'
                else 'L' if row['左'] == '○'
                else '', axis=1
)
```

**推奨**:
```python
def _determine_eye_side(row: pd.Series) -> str:
    """右眼・左眼の記号から術眼を判定"""
    has_right = row['右'] == '○'
    has_left = row['左'] == '○'

    if has_right and has_left:
        return 'B'
    elif has_right:
        return 'R'
    elif has_left:
        return 'L'
    else:
        return ''

df_processed['術眼'] = df_processed.apply(_determine_eye_side, axis=1)
```

---

### 13. 重複コードの削減

**ファイル**: `app/main_window.py:199-206, 210-217, 222-229, 234-245`

4つの処理ステップで同じtry-exceptパターンが繰り返されています。

**推奨対応**:
```python
def _execute_step(
    self,
    step_num: int,
    total_steps: int,
    step_name: str,
    func: Callable,
    *args,
    **kwargs
) -> None:
    """処理ステップを実行"""
    self._log_message(f"\n[{step_num}/{total_steps}] {step_name}を開始...")
    logging.info(f"[{step_num}/{total_steps}] {step_name}を開始")

    try:
        result = func(*args, **kwargs)
        self._log_message(f"✓ {step_name}が完了しました")
        logging.info(f"{step_name}が完了しました")
        return result
    except Exception as e:
        self._log_message(f"✗ エラー: {str(e)}")
        logging.error(f"{step_name}中にエラーが発生: {str(e)}", exc_info=True)
        raise

# 使用例
self._execute_step(
    1, 4, "手術予定表の処理",
    process_surgery_schedule,
    surgery_schedule_path,
    processed_surgery_schedule
)
```

---

### 14. Pandasの警告回避

**ファイル**: `service/surgery_schedule_processor.py:24, 27`

```python
# 現在
df_processed.loc[:, '日付'] = ...
df_processed.loc[:, '術式'] = ...
```

**問題点**:
- `.loc[:, column]`は不要に冗長
- `SettingWithCopyWarning`を避けるための過剰な対策

**推奨**:
```python
# すでに.copy()しているため、直接代入で問題なし
df_processed['日付'] = pd.to_datetime(df_processed['日付']).dt.strftime('%Y/%m/%d')
df_processed['術式'] = df_processed['術式'].apply(
    lambda x: unicodedata.normalize('NFKC', str(x)) if pd.notna(x) else x
)