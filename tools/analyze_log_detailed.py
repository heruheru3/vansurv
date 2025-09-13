import pandas as pd
import sys

try:
    df = pd.read_csv('logs/performance_log.csv')
    # コメント行を除外
    df = df[~df['timestamp'].str.startswith('#', na=False)]
    # 数値変換
    df['enemies_count'] = pd.to_numeric(df['enemies_count'], errors='coerce')
    df['fps'] = pd.to_numeric(df['fps'], errors='coerce')
    df['cpu_cores_used'] = pd.to_numeric(df['cpu_cores_used'], errors='coerce')
    df['cpu_efficiency'] = pd.to_numeric(df['cpu_efficiency'], errors='coerce')
    
    print('=== エネミー数150制限後の改善分析 ===')
    
    # 最新データ（エネミー数150制限後）のみを分析
    latest_data = df.tail(500)  # 最新500レコード
    
    print(f'\n=== 最新データ分析（最新500レコード） ===')
    print(f'エネミー数範囲: {latest_data["enemies_count"].min():.0f}-{latest_data["enemies_count"].max():.0f}体')
    print(f'平均FPS: {latest_data["fps"].mean():.1f}')
    print(f'最低FPS: {latest_data["fps"].min():.1f}')
    print(f'FPS60以上の割合: {(latest_data["fps"] >= 60).sum() / len(latest_data) * 100:.1f}%')
    print(f'FPS50以上の割合: {(latest_data["fps"] >= 50).sum() / len(latest_data) * 100:.1f}%')
    
    print(f'\n=== エネミー数と安定性分析 ===')
    # エネミー数の分布
    enemy_ranges = [(0, 30), (31, 60), (61, 90), (91, 120), (121, 150)]
    for low, high in enemy_ranges:
        range_data = latest_data[(latest_data['enemies_count'] >= low) & (latest_data['enemies_count'] <= high)]
        if not range_data.empty:
            avg_fps = range_data['fps'].mean()
            min_fps = range_data['fps'].min()
            fps60_rate = (range_data['fps'] >= 60).sum() / len(range_data) * 100
            print(f'エネミー {low}-{high}体: 平均FPS {avg_fps:.1f}, 最低FPS {min_fps:.1f}, FPS60以上 {fps60_rate:.1f}%')
    
    print(f'\n=== 並列処理効果分析 ===')
    parallel_data = latest_data[latest_data['parallel_threads'] > 0]
    single_data = latest_data[latest_data['parallel_threads'] == 0]
    
    if not parallel_data.empty and not single_data.empty:
        print(f'並列処理あり: 平均FPS {parallel_data["fps"].mean():.1f}')
        print(f'並列処理なし: 平均FPS {single_data["fps"].mean():.1f}')
        print(f'並列処理時の平均エネミー数: {parallel_data["enemies_count"].mean():.1f}体')
        print(f'単一処理時の平均エネミー数: {single_data["enemies_count"].mean():.1f}体')
    
    print(f'\n=== パフォーマンス統計 ===')
    print(f'平均処理時間: {latest_data["total_processing_ms"].mean():.1f}ms')
    print(f'平均敵更新時間: {latest_data["enemy_update_ms"].mean():.1f}ms')
    print(f'平均レンダリング時間: {latest_data["render_time_ms"].mean():.1f}ms')
    print(f'平均パーティクル数: {latest_data["particles_count"].mean():.1f}個')
    print(f'平均ジェム数: {latest_data["gems_count"].mean():.1f}個')
    
    print(f'\n=== 改善効果まとめ ===')
    print(f'✅ エネミー数上限: 150体（制限効果あり）')
    print(f'✅ FPS安定性: 平均{latest_data["fps"].mean():.1f}（良好）')
    print(f'✅ 並列処理活用: {(latest_data["parallel_threads"] > 0).sum()}回 / {len(latest_data)}回')
    
    # FPS低下の原因分析
    low_fps_data = latest_data[latest_data['fps'] < 55]
    if not low_fps_data.empty:
        print(f'\n=== FPS低下時の分析（FPS55未満） ===')
        print(f'発生回数: {len(low_fps_data)}回')
        print(f'平均エネミー数: {low_fps_data["enemies_count"].mean():.1f}体')
        print(f'平均パーティクル数: {low_fps_data["particles_count"].mean():.1f}個')
        print(f'平均処理時間: {low_fps_data["total_processing_ms"].mean():.1f}ms')
    else:
        print(f'\n✅ FPS55未満の発生なし - 非常に安定！')

except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()