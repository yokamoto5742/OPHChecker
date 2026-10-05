import logging
from datetime import datetime
from pathlib import Path

from openpyxl import load_workbook

from utils.csv_table import DATE_OUTPUT_FORMAT, read_csv_rows

COMPARISON_COLUMNS = ['入外_比較', '術眼_比較', '手術_比較', '医師_比較', '麻酔_比較']
OUTPUT_COLUMNS = ['手術日', '患者ID', '氏名', '入外', '術眼', '手術', '医師', '麻酔', '術前'] + COMPARISON_COLUMNS
RESULT_LABELS = {'True': '一致', 'False': '不一致'}


def _to_cell_value(column: str, text: str) -> datetime | int | str | None:
    """CSVの文字列をExcelセルに書き込む値に変換"""
    if text == '':
        return None
    if column == '手術日':
        # datetimeオブジェクトに変換してテンプレートの書式を反映
        try:
            return datetime.strptime(text, DATE_OUTPUT_FORMAT)
        except ValueError:
            return text
    if column == '患者ID':
        return int(text)
    return RESULT_LABELS.get(text, text)


def surgery_error_extractor(comparison_result: str, output_path: str, template_path: str) -> str:
    """
    comparison_resultからFALSEまたは未入力が含まれる行を抽出し眼科手術指示確認.xlsxとして出力

    Args:
        comparison_result: 比較結果CSVファイルのパス
        output_path: 出力先ディレクトリのパス
        template_path: テンプレートExcelファイルのパス

    Returns:
        生成されたファイルのパス
    """
    error_rows = [
        row for row in read_csv_rows(comparison_result)
        if any(row[column] in ('False', '未入力') for column in COMPARISON_COLUMNS)
    ]

    if len(error_rows) == 0:
        logging.info("不一致および未入力はありませんでした")
        return ""

    Path(output_path).mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    output_filename = f'眼科手術指示確認{timestamp}.xlsx'
    output_filepath = Path(output_path) / output_filename

    wb = load_workbook(template_path)
    ws = wb.active

    if ws is not None:
        for row_idx, row in enumerate(error_rows, start=2):
            for col_idx, column in enumerate(OUTPUT_COLUMNS, start=1):
                ws.cell(row=row_idx, column=col_idx, value=_to_cell_value(column, row[column]))

    wb.save(output_filepath)

    logging.info(f"眼科手術指示確認ファイルの作成が完了しました")
    logging.info(f"エラー件数: {len(error_rows)}件")
    logging.info(f"出力ファイル: {output_filepath}")

    return str(output_filepath)


if __name__ == '__main__':
    from utils.config_manager import get_paths, load_config

    config = load_config()
    paths = get_paths(config)

    surgery_error_extractor(
        paths['comparison_result'],
        paths['output_path'],
        paths['template_path']
    )
