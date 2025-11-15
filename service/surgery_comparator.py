import logging

import pandas as pd


def compare_surgery_data(
        processed_surgery_search_data: str,
        processed_surgery_schedule: str,
        comparison_result: str
) -> None:
    """
    手術検索データと手術予定表を比較してCSV形式で出力

    Args:
        processed_surgery_search_data: 手術検索データのCSVファイルパス（基準）
        processed_surgery_schedule: 手術予定表のCSVファイルパス（比較対象）
        comparison_result: 比較結果を出力するCSVファイルパス
    """
    # CSVファイルを読み込み
    df_search = pd.read_csv(processed_surgery_search_data, encoding='cp932')
    df_schedule = pd.read_csv(processed_surgery_schedule, encoding='cp932')

    logging.info(f"検索データ件数: {len(df_search)}件")
    logging.info(f"予定表データ件数（読み込み時）: {len(df_schedule)}件")

    # 手術日または患者IDが欠損している行を除外
    df_schedule_original_count = len(df_schedule)
    df_schedule = df_schedule.dropna(subset=['手術日', '患者ID'])
    if len(df_schedule) < df_schedule_original_count:
        removed_count = df_schedule_original_count - len(df_schedule)
        logging.warning(f"予定表から手術日または患者IDが空の行を {removed_count}件 除外しました")
        logging.info(f"予定表データ件数（除外後）: {len(df_schedule)}件")

    # 手術日を統一フォーマット（YYYY/MM/DD）に変換
    # 検索データの手術日フォーマットを自動判定
    try:
        # まずYY/MM/DD形式で試行
        df_search['手術日'] = pd.to_datetime(df_search['手術日'], format='%y/%m/%d').dt.strftime('%Y/%m/%d')
    except (ValueError, TypeError) as e:
        # 失敗したら自動判定
        logging.warning(f"手術日のフォーマット変換に失敗したため、自動判定を使用します: {e}")
        df_search['手術日'] = pd.to_datetime(df_search['手術日']).dt.strftime('%Y/%m/%d')

    # 予定表の手術日フォーマットを自動判定して統一
    if len(df_schedule) > 0:
        df_schedule['手術日'] = pd.to_datetime(df_schedule['手術日']).dt.strftime('%Y/%m/%d')

    # 患者IDを文字列型に統一し前後の空白を削除、浮動小数点型の場合は整数に変換してから文字列
    df_search['患者ID'] = df_search['患者ID'].astype(float).astype(int).astype(str).str.strip()
    if len(df_schedule) > 0:
        df_schedule['患者ID'] = df_schedule['患者ID'].astype(float).astype(int).astype(str).str.strip()

    if len(df_schedule) > 0:
        # NaN（欠損値）を除外してmin/maxを取得
        valid_dates = df_schedule['手術日'].dropna()
        if len(valid_dates) > 0:
            logging.info(f"予定表の手術日範囲: {valid_dates.min()} ～ {valid_dates.max()}")
        else:
            logging.warning("予定表に有効な手術日がありません")

        # NaNが含まれている場合は警告を表示
        nan_count = df_schedule['手術日'].isna().sum()
        if nan_count > 0:
            logging.warning(f"予定表に手術日が空の行が {nan_count}件 あります")
    else:
        logging.warning("予定表にデータがありません")

    # 手術日と患者IDをキーとして左結合（left join）
    df_merged = df_search.merge(
        df_schedule,
        on=['手術日', '患者ID'],
        how='left',
        suffixes=('_検索', '_予定')
    )

    # 比較対象の列名
    compare_columns = ['入外', '術眼', '手術', '医師', '麻酔']

    # 手術日の比較列を追加（常にTrue）
    df_merged['手術日_比較'] = True

    # 各列の比較結果を格納
    for column in compare_columns:
        search_col = f'{column}_検索'
        schedule_col = f'{column}_予定'
        result_col = f'{column}_比較'

        # 比較結果を計算
        df_merged[result_col] = df_merged.apply(
            lambda row: '未入力' if pd.isna(row[schedule_col])
            else (row[search_col] == row[schedule_col]),
            axis=1
        )

    # 出力用のデータフレームを作成
    # 手術検索データ
    output_columns = [
        '手術日', '患者ID', '氏名_検索', '入外_検索', '術眼_検索',
        '手術_検索', '医師_検索', '麻酔_検索', '術前'
    ]

    # 次の6列：比較結果
    comparison_columns = [
        '手術日_比較', '入外_比較', '術眼_比較',
        '手術_比較', '医師_比較', '麻酔_比較'
    ]

    # 列名を元の名前に戻す（_検索を削除）
    df_output = df_merged[output_columns + comparison_columns].copy()
    df_output.columns = [
        '手術日', '患者ID', '氏名', '入外', '術眼',
        '手術', '医師', '麻酔', '術前',
        '手術日_比較', '入外_比較', '術眼_比較',
        '手術_比較', '医師_比較', '麻酔_比較'
    ]

    # CSVファイルとして保存
    df_output.to_csv(comparison_result, index=False, encoding='cp932')

    # 統計情報を表示
    total_rows = len(df_output)
    logging.info("=== 比較結果の詳細 ===")

    for col in ['入外_比較', '術眼_比較', '手術_比較', '医師_比較', '麻酔_比較']:
        true_count = (df_output[col] == True).sum()
        false_count = (df_output[col] == False).sum()
        not_entered_count = (df_output[col] == '未入力').sum()

        logging.info(f"{col.replace('_比較', '')}: 一致={true_count}件, 不一致={false_count}件, 未入力={not_entered_count}件")

    logging.info(f"処理が完了しました: 総件数={total_rows}件")
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
