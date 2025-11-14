import tempfile
from io import StringIO
from pathlib import Path

import pandas as pd
import pytest

from service.surgery_comparator import compare_surgery_data


@pytest.fixture
def temp_csv_files():
    """一時的なCSVファイルを作成"""
    temp_dir = tempfile.mkdtemp()

    # 手術検索データ
    search_data = """手術日,患者ID,氏名,入外,術眼,手術,医師,麻酔,術前
2025/01/15,12345,患者A,外来,R,白内障手術,橋本,局所,検査A
2025/01/16,12346,患者B,入院,L,緑内障手術,植田,全身,検査B
2025/01/17,12347,患者C,外来,B,白内障手術,増子,局所,検査C
"""
    search_path = Path(temp_dir) / 'search.csv'
    search_path.write_text(search_data, encoding='cp932')

    # 手術予定表（一致するデータ）
    schedule_data = """手術日,患者ID,氏名,入外,術眼,手術,医師,麻酔
2025/01/15,12345,患者A,外来,R,白内障手術,橋本,局所
2025/01/16,12346,患者B,入院,L,緑内障手術,植田,全身
2025/01/17,12347,患者C,外来,L,白内障手術,増子,局所
"""
    schedule_path = Path(temp_dir) / 'schedule.csv'
    schedule_path.write_text(schedule_data, encoding='cp932')

    comparison_path = Path(temp_dir) / 'comparison.csv'

    yield {
        'search': str(search_path),
        'schedule': str(schedule_path),
        'comparison': str(comparison_path)
    }

    # クリーンアップ
    import shutil
    try:
        shutil.rmtree(temp_dir)
    except:
        pass


def test_compare_surgery_data_creates_output_file(temp_csv_files):
    """比較結果ファイルが作成される"""
    compare_surgery_data(
        temp_csv_files['search'],
        temp_csv_files['schedule'],
        temp_csv_files['comparison']
    )

    assert Path(temp_csv_files['comparison']).exists()


def test_compare_surgery_data_correct_columns(temp_csv_files):
    """比較結果ファイルに正しい列が含まれる"""
    compare_surgery_data(
        temp_csv_files['search'],
        temp_csv_files['schedule'],
        temp_csv_files['comparison']
    )

    df = pd.read_csv(temp_csv_files['comparison'], encoding='cp932')

    expected_columns = [
        '手術日', '患者ID', '氏名', '入外', '術眼',
        '手術', '医師', '麻酔', '術前',
        '手術日_比較', '入外_比較', '術眼_比較',
        '手術_比較', '医師_比較', '麻酔_比較'
    ]

    assert list(df.columns) == expected_columns


def test_compare_surgery_data_matching_records(temp_csv_files):
    """一致するレコードが正しく比較される"""
    compare_surgery_data(
        temp_csv_files['search'],
        temp_csv_files['schedule'],
        temp_csv_files['comparison']
    )

    df = pd.read_csv(temp_csv_files['comparison'], encoding='cp932')

    # 1件目は完全一致
    assert df.iloc[0]['入外_比較'] == True
    assert df.iloc[0]['術眼_比較'] == True
    assert df.iloc[0]['手術_比較'] == True
    assert df.iloc[0]['医師_比較'] == True
    assert df.iloc[0]['麻酔_比較'] == True


def test_compare_surgery_data_mismatching_records(temp_csv_files):
    """不一致レコードが正しく検出される"""
    compare_surgery_data(
        temp_csv_files['search'],
        temp_csv_files['schedule'],
        temp_csv_files['comparison']
    )

    df = pd.read_csv(temp_csv_files['comparison'], encoding='cp932')

    # 3件目は術眼が不一致（B vs L）
    assert df.iloc[2]['術眼_比較'] == False


def test_compare_surgery_data_missing_records():
    """予定表にないレコードは未入力として扱われる"""
    temp_dir = tempfile.mkdtemp()

    # 検索データ
    search_data = """手術日,患者ID,氏名,入外,術眼,手術,医師,麻酔,術前
2025/01/15,12345,患者A,外来,R,白内障手術,橋本,局所,検査A
"""
    search_path = Path(temp_dir) / 'search.csv'
    search_path.write_text(search_data, encoding='cp932')

    # 予定表（空）
    schedule_data = """手術日,患者ID,氏名,入外,術眼,手術,医師,麻酔
"""
    schedule_path = Path(temp_dir) / 'schedule.csv'
    schedule_path.write_text(schedule_data, encoding='cp932')

    comparison_path = Path(temp_dir) / 'comparison.csv'

    try:
        compare_surgery_data(
            str(search_path),
            str(schedule_path),
            str(comparison_path)
        )

        df = pd.read_csv(str(comparison_path), encoding='cp932')

        # すべて未入力
        assert df.iloc[0]['入外_比較'] == '未入力'
        assert df.iloc[0]['術眼_比較'] == '未入力'
        assert df.iloc[0]['手術_比較'] == '未入力'

    finally:
        import shutil
        try:
            shutil.rmtree(temp_dir)
        except:
            pass


def test_compare_surgery_data_handles_empty_schedule():
    """空の予定表を処理できる"""
    temp_dir = tempfile.mkdtemp()

    search_data = """手術日,患者ID,氏名,入外,術眼,手術,医師,麻酔,術前
2025/01/15,12345,患者A,外来,R,白内障手術,橋本,局所,検査A
"""
    search_path = Path(temp_dir) / 'search.csv'
    search_path.write_text(search_data, encoding='cp932')

    schedule_data = """手術日,患者ID,氏名,入外,術眼,手術,医師,麻酔
"""
    schedule_path = Path(temp_dir) / 'schedule.csv'
    schedule_path.write_text(schedule_data, encoding='cp932')

    comparison_path = Path(temp_dir) / 'comparison.csv'

    try:
        compare_surgery_data(
            str(search_path),
            str(schedule_path),
            str(comparison_path)
        )

        assert Path(comparison_path).exists()

    finally:
        import shutil
        try:
            shutil.rmtree(temp_dir)
        except:
            pass
