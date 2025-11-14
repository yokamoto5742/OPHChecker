import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from service.surgery_search_processor import process_eye_surgery_data


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

    df = pd.read_csv(temp_csv_file['output'], encoding='cp932')

    expected_columns = ['手術日', '患者ID', '氏名', '入外', '術眼', '手術', '医師', '麻酔', '術前']
    assert list(df.columns) == expected_columns


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

    df = pd.read_csv(temp_csv_file['output'], encoding='cp932')

    # 日付フォーマットを確認
    assert df.iloc[0]['手術日'].startswith('2025/')


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

    df = pd.read_csv(temp_csv_file['output'], encoding='cp932')

    assert df.iloc[0]['麻酔'] == '局所'  # 球後麻酔 -> 局所


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

    df = pd.read_csv(temp_csv_file['output'], encoding='cp932')

    assert df.iloc[0]['医師'] == '橋本'  # 橋本義弘 -> 橋本


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

    df = pd.read_csv(temp_csv_file['output'], encoding='cp932')

    assert '(トーリック)' not in df.iloc[0]['手術']


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

    df = pd.read_csv(temp_csv_file['output'], encoding='cp932')

    assert df.iloc[0]['術眼'] == 'R'  # 右のみ
    assert df.iloc[1]['術眼'] == 'L'  # 左のみ
    assert df.iloc[2]['術眼'] == 'B'  # 両眼


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

    df = pd.read_csv(temp_csv_file['output'], encoding='cp932')

    # ★を含む患者は除外される
    assert '★除外患者' not in df['氏名'].values
