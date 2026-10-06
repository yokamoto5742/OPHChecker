import configparser
import logging
import re
import unicodedata
from datetime import datetime

from utils.config_manager import (
    get_exclusion_line_keywords,
    get_paths,
    get_replacement_dict,
    get_surgery_strings_to_remove,
    load_config,
)
from utils.csv_table import (
    DATE_OUTPUT_FORMAT,
    CsvRow,
    normalize_patient_id,
    read_csv_rows,
    write_csv_rows,
)

OUTPUT_COLUMNS = ['手術日', '患者ID', '氏名', '入外', '術眼', '手術', '医師', '麻酔', '術前']


def _determine_eye_side(row: CsvRow) -> str:
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


def _select_required_columns(rows: list[CsvRow]) -> list[CsvRow]:
    """必要な列を選択"""
    required_columns = [
        '手術日', '患者ID', '氏名', '手術', '医師',
        '麻酔', '病名', '入外', '右', '左', '術前'
    ]
    return [{column: row[column] for column in required_columns} for row in rows]


def _convert_surgery_date_format(rows: list[CsvRow]) -> list[CsvRow]:
    """手術日をYYYY/MM/DD形式に変換"""
    # 眼科システムの出力形式により年が2桁(25/01/15)と4桁(2025/01/15)の両方がある
    has_four_digit_year = all(re.match(r'\d{4}/', row['手術日']) for row in rows)
    date_format = '%Y/%m/%d' if has_four_digit_year else '%y/%m/%d'
    for row in rows:
        row['手術日'] = datetime.strptime(row['手術日'], date_format).strftime(DATE_OUTPUT_FORMAT)
    return rows


def _apply_replacements(rows: list[CsvRow], config: configparser.ConfigParser) -> list[CsvRow]:
    """麻酔、術者、入外の値を置換"""
    anesthesia_replacements = get_replacement_dict(config, 'Replacements', 'anesthesia_replacements')
    surgeon_replacements = get_replacement_dict(config, 'Replacements', 'surgeon_replacements')
    inpatient_replacements = get_replacement_dict(config, 'Replacements', 'inpatient_replacements')

    for row in rows:
        row['麻酔'] = anesthesia_replacements.get(row['麻酔'], row['麻酔'])
        row['医師'] = surgeon_replacements.get(row['医師'], row['医師'])
        row['入外'] = inpatient_replacements.get(row['入外'], row['入外'])

    return rows


def _remove_surgery_strings(rows: list[CsvRow], config: configparser.ConfigParser) -> list[CsvRow]:
    """手術列から特定の文字列を削除"""
    surgery_strings_to_remove = get_surgery_strings_to_remove(config)
    for row in rows:
        for string in surgery_strings_to_remove:
            row['手術'] = row['手術'].replace(string, '')
    return rows


def _filter_exclusion_keywords(rows: list[CsvRow], config: configparser.ConfigParser) -> list[CsvRow]:
    """氏名列または手術列で特定の文字列が含まれている行を削除"""
    exclusion_line_keywords = get_exclusion_line_keywords(config)
    return [
        row for row in rows
        if not any(
            keyword in row[column]
            for column in ['氏名', '手術']
            for keyword in exclusion_line_keywords
        )
    ]


def _normalize_surgery_text(rows: list[CsvRow]) -> list[CsvRow]:
    """手術列の値を全角カナに変換"""
    for row in rows:
        row['手術'] = unicodedata.normalize('NFKC', row['手術'])
    return rows


def _create_eye_side_column(rows: list[CsvRow]) -> list[CsvRow]:
    """術眼列を作成"""
    for row in rows:
        row['術眼'] = _determine_eye_side(row)
    return rows


def _handle_duplicates(rows: list[CsvRow]) -> list[CsvRow]:
    """同日・同一患者の行を1行にまとめ、術眼を右左の有無から決め直す"""
    # 2行目以降の手術・医師・麻酔は捨て、1行目を残す
    merged_rows: dict[tuple[str, str], CsvRow] = {}
    for row in rows:
        first_row = merged_rows.setdefault((row['手術日'], row['患者ID']), row)
        if first_row is not row:
            first_row['右'] = first_row['右'] or row['右']
            first_row['左'] = first_row['左'] or row['左']
            first_row['術眼'] = _determine_eye_side(first_row)
    return list(merged_rows.values())


def _sort_rows(rows: list[CsvRow]) -> list[CsvRow]:
    """手術日・患者IDでソート"""
    return sorted(rows, key=lambda row: (row['手術日'], int(row['患者ID'])))


def process_eye_surgery_data(input_file_path: str, output_file_path: str) -> None:
    """
    手術検索データのCSVファイルを処理

    Args:
        input_file_path: 入力ファイルのパス
        output_file_path: 出力ファイルのパス
    """
    config = load_config()
    rows = _select_required_columns(read_csv_rows(input_file_path))
    for row in rows:
        row['患者ID'] = normalize_patient_id(row['患者ID'])

    rows = _convert_surgery_date_format(rows)
    rows = _apply_replacements(rows, config)
    rows = _remove_surgery_strings(rows, config)
    rows = _filter_exclusion_keywords(rows, config)
    rows = _normalize_surgery_text(rows)
    rows = _create_eye_side_column(rows)
    rows = _handle_duplicates(rows)
    rows = _sort_rows(rows)

    write_csv_rows(output_file_path, OUTPUT_COLUMNS, rows)
    logging.info(f"手術検索データの処理が完了しました: {output_file_path}")

if __name__ == '__main__':
    config = load_config()
    paths = get_paths(config)

    surgery_search_data = paths['surgery_search_data']
    processed_surgery_search_data = paths['processed_surgery_search_data']

    process_eye_surgery_data(surgery_search_data, processed_surgery_search_data)
