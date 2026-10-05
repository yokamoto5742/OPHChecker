import csv
from datetime import datetime

CSV_ENCODING = 'cp932'
DATE_OUTPUT_FORMAT = '%Y/%m/%d'
DATE_INPUT_FORMATS = ['%Y/%m/%d', '%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%y/%m/%d']

type CsvRow = dict[str, str]


def read_csv_rows(file_path: str) -> list[CsvRow]:
    """CSVを列名→文字列の辞書のリストとして読み込む（空欄は空文字）"""
    with open(file_path, encoding=CSV_ENCODING, newline='') as csv_file:
        return [dict(row) for row in csv.DictReader(csv_file)]


def write_csv_rows(file_path: str, columns: list[str], rows: list[CsvRow]) -> None:
    """指定した列順でCSVを書き出す"""
    with open(file_path, 'w', encoding=CSV_ENCODING, newline='') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=columns, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)


def parse_date(text: str) -> datetime:
    """日付文字列をdatetimeに変換"""
    for date_format in DATE_INPUT_FORMATS:
        try:
            return datetime.strptime(text.strip(), date_format)
        except ValueError:
            continue
    raise ValueError(f"日付として解釈できません: {text}")


def normalize_patient_id(text: str) -> str:
    """患者IDを整数表記の文字列に揃える（'12345.0' → '12345'）"""
    return str(int(float(text)))
