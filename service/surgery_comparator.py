import logging

from utils.csv_table import (
    DATE_OUTPUT_FORMAT,
    CsvRow,
    normalize_patient_id,
    parse_date,
    read_csv_rows,
    write_csv_rows,
)

COMPARE_COLUMNS = ['入外', '術眼', '手術', '医師', '麻酔']
NOT_ENTERED = '未入力'
OUTPUT_COLUMNS = [
    '手術日', '患者ID', '氏名', '入外', '術眼',
    '手術', '医師', '麻酔', '術前',
    '手術日_比較', '入外_比較', '術眼_比較',
    '手術_比較', '医師_比較', '麻酔_比較'
]


def _normalize_keys(rows: list[CsvRow]) -> None:
    """結合キー（手術日・患者ID）の表記を揃える"""
    for row in rows:
        row['手術日'] = parse_date(row['手術日']).strftime(DATE_OUTPUT_FORMAT)
        row['患者ID'] = normalize_patient_id(row['患者ID'])


def _compare_row(search_row: CsvRow, schedule_row: CsvRow | None) -> CsvRow:
    """検索データ1行と予定表1行（該当なしはNone）を比較"""
    output_row = dict(search_row)
    output_row['手術日_比較'] = str(True)

    for column in COMPARE_COLUMNS:
        schedule_value = schedule_row[column] if schedule_row else ''
        # 予定が未入力の場合は'未入力'、それ以外は一致判定（True/False）
        output_row[f'{column}_比較'] = (
            NOT_ENTERED if schedule_value == '' else str(search_row[column] == schedule_value)
        )

    return output_row


def compare_surgery_data(
        processed_surgery_search_data: str,
        processed_surgery_schedule: str,
        comparison_result: str
) -> None:
    """
    眼科手術検索データと手術予定表を比較してCSV形式で出力

    Args:
        processed_surgery_search_data: 眼科手術検索データのCSVファイルパス（基準）
        processed_surgery_schedule: 手術予定表のCSVファイルパス（比較対象）
        comparison_result: 比較結果を出力するCSVファイルパス
    """
    search_rows = read_csv_rows(processed_surgery_search_data)
    all_schedule_rows = read_csv_rows(processed_surgery_schedule)

    logging.info(f"検索データ件数: {len(search_rows)}件")
    logging.info(f"予定表データ件数（読み込み時）: {len(all_schedule_rows)}件")

    schedule_rows = [row for row in all_schedule_rows if row['手術日'] and row['患者ID']]
    removed_count = len(all_schedule_rows) - len(schedule_rows)
    if removed_count > 0:
        logging.warning(f"予定表から手術日または患者IDが空の行を {removed_count}件 除外しました")
        logging.info(f"予定表データ件数（除外後）: {len(schedule_rows)}件")

    _normalize_keys(search_rows)
    _normalize_keys(schedule_rows)

    if schedule_rows:
        schedule_dates = [row['手術日'] for row in schedule_rows]
        logging.info(f"予定表の手術日範囲: {min(schedule_dates)} ～ {max(schedule_dates)}")
    else:
        logging.warning("予定表にデータがありません")

    schedule_by_key: dict[tuple[str, str], list[CsvRow]] = {}
    for row in schedule_rows:
        schedule_by_key.setdefault((row['手術日'], row['患者ID']), []).append(row)

    # 検索データを基準に左結合（予定表に同一キーが複数あれば全件出力）
    output_rows: list[CsvRow] = []
    for search_row in search_rows:
        matched_rows = schedule_by_key.get((search_row['手術日'], search_row['患者ID']), [None])
        output_rows.extend(_compare_row(search_row, schedule_row) for schedule_row in matched_rows)

    write_csv_rows(comparison_result, OUTPUT_COLUMNS, output_rows)

    logging.info("=== 比較結果の詳細 ===")

    for column in COMPARE_COLUMNS:
        results = [row[f'{column}_比較'] for row in output_rows]
        true_count = results.count(str(True))
        false_count = results.count(str(False))
        not_entered_count = results.count(NOT_ENTERED)

        logging.info(f"{column}: 一致={true_count}件, 不一致={false_count}件, 未入力={not_entered_count}件")

    logging.info(f"処理が完了しました: 総件数={len(output_rows)}件")
    logging.info(f"出力ファイル: {comparison_result}")


if __name__ == '__main__':
    from utils.config_manager import load_config, get_paths

    config = load_config()
    paths = get_paths(config)

    compare_surgery_data(
        paths['processed_surgery_search_data'],
        paths['processed_surgery_schedule'],
        paths['comparison_result']
    )
