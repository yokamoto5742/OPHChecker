from datetime import datetime
from pathlib import Path

import pandas as pd


def generate_surgery_instruction(comparison_result: str, output_path: str) -> str:
    """
    comparison_resultからFALSEまたは未入力が含まれる行を抽出してxlsxファイルとして出力

    Args:
        comparison_result: 比較結果CSVファイルのパス
        output_path: 出力先ディレクトリのパス

    Returns:
        生成されたファイルのパス
    """
    # CSVファイルを読み込み
    df = pd.read_csv(comparison_result, encoding='cp932')
    comparison_cols = ['入外_比較', '術眼_比較', '手術_比較', '医師_比較', '麻酔_比較']

    # FALSEまたは「未入力」が含まれる行を抽出
    mask = pd.Series([False] * len(df))
    for col in comparison_cols:
        mask |= (df[col] == False) | (df[col] == '未入力')

    df_errors = df[mask]

    # 出力する列を選択
    output_columns = ['手術日', '患者ID', '氏名', '入外', '術眼', '手術', '医師', '麻酔', '術前','入外_比較', '術眼_比較', '手術_比較', '医師_比較', '麻酔_比較']
    df_output = df_errors[output_columns]

    # 出力ディレクトリを作成
    Path(output_path).mkdir(parents=True, exist_ok=True)

    # 現在時刻を含むファイル名を生成
    timestamp = datetime.now().strftime('%y%m%d_%H%M')
    output_filename = f'眼科手術指示確認{timestamp}.xlsx'
    output_filepath = Path(output_path) / output_filename

    # xlsxファイルとして保存
    df_output.to_excel(output_filepath, index=False, engine='openpyxl')

    print(f"処理が完了しました")
    print(f"エラー件数: {len(df_errors)}件")
    print(f"出力ファイル: {output_filepath}")

    return str(output_filepath)


if __name__ == '__main__':
    from utils.config_manager import get_paths, load_config

    config = load_config()
    paths = get_paths(config)

    generate_surgery_instruction(
        paths['comparison_result'],
        paths['output_path']
    )
