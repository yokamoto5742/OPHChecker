import tempfile
from pathlib import Path

import pandas as pd
import pytest

from service.surgery_schedule_processor import process_surgery_schedule


@pytest.fixture
def temp_excel_file():
    """一時的なExcelファイルを作成"""
    temp_dir = tempfile.mkdtemp()

    from openpyxl import Workbook

    excel_path = Path(temp_dir) / 'schedule.xlsx'

    # openpyxlを使って直接Excelファイルを作成
    wb = Workbook()
    ws = wb.active
    ws.title = '南館2'

    # 0行目（削除される行）
    ws.append(['削除される行1', '削除される行2', '削除される行3', '削除される行4', '削除される行5', '削除される行6', '削除される行7'])

    # 1行目（ヘッダー）
    ws.append(['日付', 'ID', '氏名', '入外', '術式', '麻酔', '術者', '不要列'])

    # データ行
    ws.append(['2025/01/15', 12345, '患者A', '外来', 'R)白内障手術', '局所', '橋本', 'データ1'])
    ws.append(['2025/01/16', 12346, '患者B', '入院', 'L)緑内障手術', '全身', '植田', 'データ2'])

    wb.save(excel_path)

    output_path = Path(temp_dir) / 'output.csv'

    yield {
        'input': str(excel_path),
        'output': str(output_path)
    }

    # クリーンアップ
    import shutil
    try:
        shutil.rmtree(temp_dir)
    except:
        pass


def test_process_surgery_schedule_creates_output_file(temp_excel_file):
    """処理結果ファイルが作成される"""
    process_surgery_schedule(
        temp_excel_file['input'],
        temp_excel_file['output']
    )

    assert Path(temp_excel_file['output']).exists()


def test_process_surgery_schedule_correct_columns(temp_excel_file):
    """正しい列が出力される"""
    process_surgery_schedule(
        temp_excel_file['input'],
        temp_excel_file['output']
    )

    df = pd.read_csv(temp_excel_file['output'], encoding='cp932')

    expected_columns = ['手術日', '患者ID', '氏名', '入外', '術眼', '手術', '医師', '麻酔']
    assert list(df.columns) == expected_columns


def test_process_surgery_schedule_splits_surgery_field(temp_excel_file):
    """術式が術眼と手術に分割される"""
    process_surgery_schedule(
        temp_excel_file['input'],
        temp_excel_file['output']
    )

    df = pd.read_csv(temp_excel_file['output'], encoding='cp932')

    assert df.iloc[0]['術眼'] == 'R'
    assert df.iloc[0]['手術'] == '白内障手術'


def test_process_surgery_schedule_date_format(temp_excel_file):
    """日付がYYYY/MM/DD形式に変換される"""
    process_surgery_schedule(
        temp_excel_file['input'],
        temp_excel_file['output']
    )

    df = pd.read_csv(temp_excel_file['output'], encoding='cp932')

    # 日付フォーマットを確認
    assert '/' in df.iloc[0]['手術日']
    assert len(df.iloc[0]['手術日']) == 10  # YYYY/MM/DD


def test_process_surgery_schedule_sorted_by_date_and_id(temp_excel_file):
    """手術日と患者IDでソートされる"""
    process_surgery_schedule(
        temp_excel_file['input'],
        temp_excel_file['output']
    )

    df = pd.read_csv(temp_excel_file['output'], encoding='cp932')

    # 日付でソートされていることを確認
    assert df.iloc[0]['手術日'] <= df.iloc[1]['手術日']


def test_process_surgery_schedule_with_different_sheet_name():
    """異なるシート名を指定できる"""
    temp_dir = tempfile.mkdtemp()

    from openpyxl import Workbook

    excel_path = Path(temp_dir) / 'schedule.xlsx'
    output_path = Path(temp_dir) / 'output.csv'

    # openpyxlを使って直接Excelファイルを作成
    wb = Workbook()
    ws = wb.active
    ws.title = 'カスタムシート'

    # 0行目（削除される行）
    ws.append(['削除される行1', '削除される行2', '削除される行3', '削除される行4', '削除される行5', '削除される行6', '削除される行7'])

    # 1行目（ヘッダー）
    ws.append(['日付', 'ID', '氏名', '入外', '術式', '麻酔', '術者'])

    # データ行
    ws.append(['2025/01/15', 12345, '患者A', '外来', 'R)白内障手術', '局所', '橋本'])

    wb.save(excel_path)

    try:
        process_surgery_schedule(
            str(excel_path),
            str(output_path),
            sheet_name='カスタムシート'
        )

        assert Path(output_path).exists()

    finally:
        import shutil
        try:
            shutil.rmtree(temp_dir)
        except:
            pass
