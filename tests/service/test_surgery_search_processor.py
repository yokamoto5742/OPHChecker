import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from service.surgery_search_processor import (
    _convert_surgery_date_format,
    _determine_eye_side,
    _filter_exclusion_keywords,
    _handle_duplicates,
    process_eye_surgery_data,
)
from utils.csv_table import CsvRow, read_csv_rows


@pytest.fixture
def mock_config():
    """モック設定オブジェクトを作成"""
    mock = MagicMock()
    return mock


@pytest.fixture
def temp_csv_file():
    """一時的なCSVファイルを作成"""
    temp_dir = tempfile.mkdtemp()

    # テスト用データ
    data = """手術日,患者ID,氏名,手術,医師,麻酔,病名,入外,右,左,術前
25/01/15,12345,患者A,白内障手術(トーリック),橋本義弘,球後麻酔,白内障,あやめ,○,,検査A
25/01/16,12346,患者B,緑内障手術,植田芳樹,点眼麻酔,緑内障,外来,,○,検査B
25/01/17,12347,患者C,白内障手術,増子杏,全身麻酔,白内障,さくら,○,○,検査C
25/01/18,12348,★除外患者,白内障手術,田中伸弥,局所麻酔,白内障,外来,○,,検査D
"""
    input_path = Path(temp_dir) / 'input.csv'
    input_path.write_text(data, encoding='cp932')

    output_path = Path(temp_dir) / 'output.csv'

    yield {
        'input': str(input_path),
        'output': str(output_path)
    }

    # クリーンアップ
    import shutil
    try:
        shutil.rmtree(temp_dir)
    except:
        pass


def test_process_eye_surgery_data_creates_output_file(temp_csv_file):
    """処理結果ファイルが作成される"""
    with patch('service.surgery_search_processor.load_config') as mock_load_config:
        mock_config = MagicMock()
        mock_load_config.return_value = mock_config

        # モック設定を返す
        with patch('service.surgery_search_processor.get_replacement_dict') as mock_get_replacement:
            mock_get_replacement.side_effect = [
                {'球後麻酔': '局所', '点眼麻酔': '局所', '全身麻酔': '全身', '局所麻酔': '局所'},  # anesthesia
                {'橋本義弘': '橋本', '植田芳樹': '植田', '増子杏': '増子', '田中伸弥': '田中'},  # surgeon
                {'あやめ': '入院', 'さくら': '入院', '外来': '外来'}  # inpatient
            ]

            with patch('service.surgery_search_processor.get_surgery_strings_to_remove') as mock_get_surgery:
                mock_get_surgery.return_value = ['(トーリック)', '(inject)']

                with patch('service.surgery_search_processor.get_exclusion_line_keywords') as mock_get_exclusion:
                    mock_get_exclusion.return_value = ['★', '霰粒腫']

                    process_eye_surgery_data(
                        temp_csv_file['input'],
                        temp_csv_file['output']
                    )

    assert Path(temp_csv_file['output']).exists()


def test_process_eye_surgery_data_correct_columns(temp_csv_file):
    """正しい列が出力される"""
    with patch('service.surgery_search_processor.load_config') as mock_load_config:
        mock_config = MagicMock()
        mock_load_config.return_value = mock_config

        with patch('service.surgery_search_processor.get_replacement_dict') as mock_get_replacement:
            mock_get_replacement.side_effect = [
                {'球後麻酔': '局所', '点眼麻酔': '局所', '全身麻酔': '全身', '局所麻酔': '局所'},
                {'橋本義弘': '橋本', '植田芳樹': '植田', '増子杏': '増子', '田中伸弥': '田中'},
                {'あやめ': '入院', 'さくら': '入院', '外来': '外来'}
            ]

            with patch('service.surgery_search_processor.get_surgery_strings_to_remove') as mock_get_surgery:
                mock_get_surgery.return_value = ['(トーリック)', '(inject)']

                with patch('service.surgery_search_processor.get_exclusion_line_keywords') as mock_get_exclusion:
                    mock_get_exclusion.return_value = ['★', '霰粒腫']

                    process_eye_surgery_data(
                        temp_csv_file['input'],
                        temp_csv_file['output']
                    )

    rows = read_csv_rows(temp_csv_file['output'])

    expected_columns = ['手術日', '患者ID', '氏名', '入外', '術眼', '手術', '医師', '麻酔', '術前']
    assert list(rows[0].keys()) == expected_columns


def test_process_eye_surgery_data_date_conversion(temp_csv_file):
    """日付がYYYY/MM/DD形式に変換される"""
    with patch('service.surgery_search_processor.load_config') as mock_load_config:
        mock_config = MagicMock()
        mock_load_config.return_value = mock_config

        with patch('service.surgery_search_processor.get_replacement_dict') as mock_get_replacement:
            mock_get_replacement.side_effect = [
                {'球後麻酔': '局所', '点眼麻酔': '局所', '全身麻酔': '全身', '局所麻酔': '局所'},
                {'橋本義弘': '橋本', '植田芳樹': '植田', '増子杏': '増子', '田中伸弥': '田中'},
                {'あやめ': '入院', 'さくら': '入院', '外来': '外来'}
            ]

            with patch('service.surgery_search_processor.get_surgery_strings_to_remove') as mock_get_surgery:
                mock_get_surgery.return_value = ['(トーリック)', '(inject)']

                with patch('service.surgery_search_processor.get_exclusion_line_keywords') as mock_get_exclusion:
                    mock_get_exclusion.return_value = ['★', '霰粒腫']

                    process_eye_surgery_data(
                        temp_csv_file['input'],
                        temp_csv_file['output']
                    )

    rows = read_csv_rows(temp_csv_file['output'])

    # 日付フォーマットを確認
    assert rows[0]['手術日'].startswith('2025/')


@pytest.mark.parametrize('surgery_date', ['26/09/15', '2026/09/15'])
def test_convert_surgery_date_format_accepts_two_and_four_digit_year(surgery_date):
    """年が2桁・4桁どちらでもYYYY/MM/DD形式に変換される"""
    rows = _convert_surgery_date_format([{'手術日': surgery_date}])

    assert rows[0]['手術日'] == '2026/09/15'


def _same_day_row(right: str, left: str, surgery: str) -> CsvRow:
    """同日・同一患者の行を作成"""
    row = {'手術日': '2025/01/15', '患者ID': '12345', '右': right, '左': left, '手術': surgery}
    row['術眼'] = _determine_eye_side(row)
    return row


@pytest.mark.parametrize(('eye_marks', 'expected_eye_side'), [
    ([('○', ''), ('', '○')], 'B'),
    ([('', '○'), ('○', '')], 'B'),
    ([('', '○'), ('', '○')], 'L'),
    ([('○', ''), ('○', '')], 'R'),
])
def test_handle_duplicates_merges_same_day_patient(eye_marks, expected_eye_side):
    """同日・同一患者は1行にまとまり、術眼は右左の有無で決まる"""
    rows = _handle_duplicates([
        _same_day_row(right, left, f'手術{index}')
        for index, (right, left) in enumerate(eye_marks, start=1)
    ])

    assert len(rows) == 1
    assert rows[0]['術眼'] == expected_eye_side
    # 手術・医師・麻酔は1行目を残す
    assert rows[0]['手術'] == '手術1'


def test_handle_duplicates_keeps_other_patients():
    """同日でも患者が異なれば別の行として残る"""
    other_patient_row = _same_day_row('', '○', '手術2')
    other_patient_row['患者ID'] = '99999'

    rows = _handle_duplicates([_same_day_row('○', '', '手術1'), other_patient_row])

    assert [row['術眼'] for row in rows] == ['R', 'L']


@pytest.mark.parametrize(('keyword', 'expected_names'), [
    ('(仮', ['患者B']),
    ('術式未定(仮)', ['患者B']),
    ('.', ['患者A', '患者B']),
])
def test_filter_exclusion_keywords_matches_as_plain_text(keyword, expected_names):
    """除外キーワードは正規表現ではなく部分一致で判定する"""
    rows = [
        {'氏名': '患者A', '手術': '術式未定(仮)'},
        {'氏名': '患者B', '手術': '白内障手術'},
    ]

    with patch('service.surgery_search_processor.get_exclusion_line_keywords', return_value=[keyword]):
        filtered_rows = _filter_exclusion_keywords(rows, MagicMock())

    assert [row['氏名'] for row in filtered_rows] == expected_names


def test_process_eye_surgery_data_anesthesia_replacement(temp_csv_file):
    """麻酔の値が置換される"""
    with patch('service.surgery_search_processor.load_config') as mock_load_config:
        mock_config = MagicMock()
        mock_load_config.return_value = mock_config

        with patch('service.surgery_search_processor.get_replacement_dict') as mock_get_replacement:
            mock_get_replacement.side_effect = [
                {'球後麻酔': '局所', '点眼麻酔': '局所', '全身麻酔': '全身', '局所麻酔': '局所'},
                {'橋本義弘': '橋本', '植田芳樹': '植田', '増子杏': '増子', '田中伸弥': '田中'},
                {'あやめ': '入院', 'さくら': '入院', '外来': '外来'}
            ]

            with patch('service.surgery_search_processor.get_surgery_strings_to_remove') as mock_get_surgery:
                mock_get_surgery.return_value = ['(トーリック)', '(inject)']

                with patch('service.surgery_search_processor.get_exclusion_line_keywords') as mock_get_exclusion:
                    mock_get_exclusion.return_value = ['★', '霰粒腫']

                    process_eye_surgery_data(
                        temp_csv_file['input'],
                        temp_csv_file['output']
                    )

    rows = read_csv_rows(temp_csv_file['output'])

    assert rows[0]['麻酔'] == '局所'  # 球後麻酔 -> 局所


def test_process_eye_surgery_data_surgeon_replacement(temp_csv_file):
    """医師名が置換される"""
    with patch('service.surgery_search_processor.load_config') as mock_load_config:
        mock_config = MagicMock()
        mock_load_config.return_value = mock_config

        with patch('service.surgery_search_processor.get_replacement_dict') as mock_get_replacement:
            mock_get_replacement.side_effect = [
                {'球後麻酔': '局所', '点眼麻酔': '局所', '全身麻酔': '全身', '局所麻酔': '局所'},
                {'橋本義弘': '橋本', '植田芳樹': '植田', '増子杏': '増子', '田中伸弥': '田中'},
                {'あやめ': '入院', 'さくら': '入院', '外来': '外来'}
            ]

            with patch('service.surgery_search_processor.get_surgery_strings_to_remove') as mock_get_surgery:
                mock_get_surgery.return_value = ['(トーリック)', '(inject)']

                with patch('service.surgery_search_processor.get_exclusion_line_keywords') as mock_get_exclusion:
                    mock_get_exclusion.return_value = ['★', '霰粒腫']

                    process_eye_surgery_data(
                        temp_csv_file['input'],
                        temp_csv_file['output']
                    )

    rows = read_csv_rows(temp_csv_file['output'])

    assert rows[0]['医師'] == '橋本'  # 橋本義弘 -> 橋本


def test_process_eye_surgery_data_removes_surgery_strings(temp_csv_file):
    """手術名から特定文字列が削除される"""
    with patch('service.surgery_search_processor.load_config') as mock_load_config:
        mock_config = MagicMock()
        mock_load_config.return_value = mock_config

        with patch('service.surgery_search_processor.get_replacement_dict') as mock_get_replacement:
            mock_get_replacement.side_effect = [
                {'球後麻酔': '局所', '点眼麻酔': '局所', '全身麻酔': '全身', '局所麻酔': '局所'},
                {'橋本義弘': '橋本', '植田芳樹': '植田', '増子杏': '増子', '田中伸弥': '田中'},
                {'あやめ': '入院', 'さくら': '入院', '外来': '外来'}
            ]

            with patch('service.surgery_search_processor.get_surgery_strings_to_remove') as mock_get_surgery:
                mock_get_surgery.return_value = ['(トーリック)', '(inject)']

                with patch('service.surgery_search_processor.get_exclusion_line_keywords') as mock_get_exclusion:
                    mock_get_exclusion.return_value = ['★', '霰粒腫']

                    process_eye_surgery_data(
                        temp_csv_file['input'],
                        temp_csv_file['output']
                    )

    rows = read_csv_rows(temp_csv_file['output'])

    assert '(トーリック)' not in rows[0]['手術']


def test_process_eye_surgery_data_creates_eye_field(temp_csv_file):
    """術眼列が正しく作成される"""
    with patch('service.surgery_search_processor.load_config') as mock_load_config:
        mock_config = MagicMock()
        mock_load_config.return_value = mock_config

        with patch('service.surgery_search_processor.get_replacement_dict') as mock_get_replacement:
            mock_get_replacement.side_effect = [
                {'球後麻酔': '局所', '点眼麻酔': '局所', '全身麻酔': '全身', '局所麻酔': '局所'},
                {'橋本義弘': '橋本', '植田芳樹': '植田', '増子杏': '増子', '田中伸弥': '田中'},
                {'あやめ': '入院', 'さくら': '入院', '外来': '外来'}
            ]

            with patch('service.surgery_search_processor.get_surgery_strings_to_remove') as mock_get_surgery:
                mock_get_surgery.return_value = ['(トーリック)', '(inject)']

                with patch('service.surgery_search_processor.get_exclusion_line_keywords') as mock_get_exclusion:
                    mock_get_exclusion.return_value = ['★', '霰粒腫']

                    process_eye_surgery_data(
                        temp_csv_file['input'],
                        temp_csv_file['output']
                    )

    rows = read_csv_rows(temp_csv_file['output'])

    assert rows[0]['術眼'] == 'R'  # 右のみ
    assert rows[1]['術眼'] == 'L'  # 左のみ
    assert rows[2]['術眼'] == 'B'  # 両眼


def test_process_eye_surgery_data_excludes_keywords(temp_csv_file):
    """除外キーワードを含む行が削除される"""
    with patch('service.surgery_search_processor.load_config') as mock_load_config:
        mock_config = MagicMock()
        mock_load_config.return_value = mock_config

        with patch('service.surgery_search_processor.get_replacement_dict') as mock_get_replacement:
            mock_get_replacement.side_effect = [
                {'球後麻酔': '局所', '点眼麻酔': '局所', '全身麻酔': '全身', '局所麻酔': '局所'},
                {'橋本義弘': '橋本', '植田芳樹': '植田', '増子杏': '増子', '田中伸弥': '田中'},
                {'あやめ': '入院', 'さくら': '入院', '外来': '外来'}
            ]

            with patch('service.surgery_search_processor.get_surgery_strings_to_remove') as mock_get_surgery:
                mock_get_surgery.return_value = ['(トーリック)', '(inject)']

                with patch('service.surgery_search_processor.get_exclusion_line_keywords') as mock_get_exclusion:
                    mock_get_exclusion.return_value = ['★', '霰粒腫']

                    process_eye_surgery_data(
                        temp_csv_file['input'],
                        temp_csv_file['output']
                    )

    rows = read_csv_rows(temp_csv_file['output'])

    # ★を含む患者は除外される
    assert '★除外患者' not in [row['氏名'] for row in rows]
