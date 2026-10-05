import logging
import unicodedata
from datetime import date
from pathlib import Path
from typing import Any

import xlrd
from openpyxl import load_workbook

from utils.csv_table import DATE_OUTPUT_FORMAT, CsvRow, parse_date, write_csv_rows

HEADER_ROW_INDEX = 1
OUTPUT_COLUMNS = ['手術日', '患者ID', '氏名', '入外', '術眼', '手術', '医師', '麻酔']


def _convert_xls_cell(cell: xlrd.sheet.Cell, book: xlrd.Book) -> Any:
    """xlrdのセルをPythonの値に変換（空セルはNone）"""
    if cell.ctype == xlrd.XL_CELL_DATE:
        return xlrd.xldate_as_datetime(float(cell.value), book.datemode)
    if cell.ctype == xlrd.XL_CELL_NUMBER:
        return int(cell.value) if cell.value == int(cell.value) else cell.value
    if cell.ctype == xlrd.XL_CELL_TEXT and cell.value != '':
        return cell.value
    return None


def _read_sheet_rows(surgery_schedule: str, sheet_name: str) -> list[list[Any]]:
    """Excelシートを行のリストとして読み込む"""
    if Path(surgery_schedule).suffix.lower() == '.xls':
        book = xlrd.open_workbook(surgery_schedule)
        sheet = book.sheet_by_name(sheet_name)
        return [
            [_convert_xls_cell(cell, book) for cell in sheet.row(row_index)]
            for row_index in range(sheet.nrows)
        ]

    workbook = load_workbook(surgery_schedule, read_only=True, data_only=True)
    try:
        return [list(row) for row in workbook[sheet_name].iter_rows(values_only=True)]
    finally:
        workbook.close()


def _format_date(value: Any) -> str:
    if value is None:
        return ''
    if isinstance(value, date):
        return value.strftime(DATE_OUTPUT_FORMAT)
    return parse_date(str(value)).strftime(DATE_OUTPUT_FORMAT)


def _to_text(value: Any) -> str:
    return '' if value is None else str(value)


def _split_surgery_field(value: Any) -> tuple[str, str]:
    """術式を全角カナに変換し、')'で術眼と手術に分割"""
    if value is None:
        return '', ''
    eye_side, _, surgery = unicodedata.normalize('NFKC', str(value)).partition(')')
    return eye_side, surgery.strip()


def _sort_key(row: CsvRow) -> tuple[bool, str, bool, float]:
    """手術日・患者IDの昇順（空欄は末尾）"""
    patient_id = row['患者ID']
    return (
        row['手術日'] == '', row['手術日'],
        patient_id == '', float(patient_id) if patient_id else 0.0
    )


def process_surgery_schedule(surgery_schedule: str, processed_surgery_schedule: str, sheet_name: str = '南館2') -> None:
    """
    手術予定表を処理してCSV形式で出力

    Args:
        surgery_schedule: 入力Excelファイルのパス
        processed_surgery_schedule: 出力CSVファイルのパス
        sheet_name: 処理対象のシート名（デフォルト: '南館2'）
    """
    sheet_rows = _read_sheet_rows(surgery_schedule, sheet_name)
    header = sheet_rows[HEADER_ROW_INDEX]
    column_index = {
        name: header.index(name)
        for name in ['日付', 'ID', '氏名', '入外', '術式', '麻酔', '術者']
    }

    processed_rows: list[CsvRow] = []
    for sheet_row in sheet_rows[HEADER_ROW_INDEX + 1:]:
        eye_side, surgery = _split_surgery_field(sheet_row[column_index['術式']])
        processed_rows.append({
            '手術日': _format_date(sheet_row[column_index['日付']]),
            '患者ID': _to_text(sheet_row[column_index['ID']]),
            '氏名': _to_text(sheet_row[column_index['氏名']]),
            '入外': _to_text(sheet_row[column_index['入外']]),
            '術眼': eye_side,
            '手術': surgery,
            '医師': _to_text(sheet_row[column_index['術者']]),
            '麻酔': _to_text(sheet_row[column_index['麻酔']]),
        })

    processed_rows.sort(key=_sort_key)

    write_csv_rows(processed_surgery_schedule, OUTPUT_COLUMNS, processed_rows)

    logging.info(f"手術予定表の処理が完了しました: {processed_surgery_schedule}")


if __name__ == '__main__':
    from utils.config_manager import load_config, get_paths

    config = load_config()
    paths = get_paths(config)

    process_surgery_schedule(
        paths['surgery_schedule'],
        paths['processed_surgery_schedule']
    )
