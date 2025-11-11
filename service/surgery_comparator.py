import pandas as pd


def compare_surgery_data(
        search_csv_path: str,
        schedule_csv_path: str,
        output_csv_path: str
) -> None:
    """
    手術検索データと手術予定表を比較してCSV形式で出力する

    Args:
        search_csv_path: 手術検索データのCSVファイルパス（基準データ）
        schedule_csv_path: 手術予定表のCSVファイルパス（比較対象データ）
        output_csv_path: 比較結果を出力するCSVファイルパス
    """
    # CSVファイルを読み込み
    df_search = pd.read_csv(search_csv_path, encoding='cp932')
    df_schedule = pd.read_csv(schedule_csv_path, encoding='cp932')

    print(f"検索データ件数: {len(df_search)}件")
    print(f"予定表データ件数（読み込み時）: {len(df_schedule)}件")

    # 手術日または患者IDが欠損している行を除外
    df_schedule_original_count = len(df_schedule)
    df_schedule = df_schedule.dropna(subset=['手術日', '患者ID'])
    if len(df_schedule) < df_schedule_original_count:
        removed_count = df_schedule_original_count - len(df_schedule)
        print(f"警告: 予定表から手術日または患者IDが空の行を {removed_count}件 除外しました。")
        print(f"予定表データ件数（除外後）: {len(df_schedule)}件")

    if len(df_schedule) > 0:
        # NaN（欠損値）を除外してmin/maxを取得
        valid_dates = df_schedule['手術日'].dropna()
        if len(valid_dates) > 0:
            print(f"予定表の手術日範囲: {valid_dates.min()} ～ {valid_dates.max()}")
        else:
            print("予定表に有効な手術日がありません。")

        # NaNが含まれている場合は警告を表示
        nan_count = df_schedule['手術日'].isna().sum()
        if nan_count > 0:
            print(f"\n警告: 予定表に手術日が空の行が {nan_count}件 あります。")
    else:
        print("予定表にデータがありません。")
        print(f"\n検索データのサンプル（最初の3件）:")
        print(df_search[['手術日', '患者ID', '氏名']].head(3))

    # 手術日と患者IDをキーとして左結合（left join）
    df_merged = df_search.merge(
        df_schedule,
        on=['手術日', '患者ID'],
        how='left',
        suffixes=('_検索', '_予定')
    )

    # 比較対象の列名
    compare_columns = ['入外', '術眼', '手術', '医師', '麻酔']

    # 手術日の比較列を追加（常にTrueになるはずだが、念のため）
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
    # 最初の9列：検索データの元データ
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
    df_output.to_csv(output_csv_path, index=False, encoding='cp932')

    # 統計情報を表示
    total_rows = len(df_output)
    print(f"\n=== 比較結果の詳細 ===")

    for col in ['入外_比較', '術眼_比較', '手術_比較', '医師_比較', '麻酔_比較']:
        true_count = (df_output[col] == True).sum()
        false_count = (df_output[col] == False).sum()
        not_entered_count = (df_output[col] == '未入力').sum()

        print(f"{col.replace('_比較', '')}: 一致={true_count}件, 不一致={false_count}件, 未入力={not_entered_count}件")

    print(f"\n処理が完了しました。")
    print(f"総件数: {total_rows}件")
    print(f"出力ファイル: {output_csv_path}")


if __name__ == '__main__':
    # ファイルパスを指定
    search_csv_path = r'C:\Shinseikai\OPHChecker\processed_surgery_search.csv'
    schedule_csv_path = r'C:\Shinseikai\OPHChecker\processed_surgery_schedule.csv'
    output_csv_path = r'C:\Shinseikai\OPHChecker\comparison_result.csv'

    # 比較処理を実行
    compare_surgery_data(search_csv_path, schedule_csv_path, output_csv_path)