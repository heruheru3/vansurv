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
    
    print('=== FPS 60 維持可能なエネミー数 ===')
    fps60_data = df[df['fps'] >= 60]
    if not fps60_data.empty:
        max_enemies_fps60 = fps60_data['enemies_count'].max()
        print(f'FPS60維持: 最大 {max_enemies_fps60} 体')
    else:
        print('FPS60を維持できるデータなし')
    
    print('\n=== FPS 50 維持可能なエネミー数 ===')
    fps50_data = df[df['fps'] >= 50]
    if not fps50_data.empty:
        max_enemies_fps50 = fps50_data['enemies_count'].max()
        print(f'FPS50維持: 最大 {max_enemies_fps50} 体')
    else:
        print('FPS50を維持できるデータなし')
    
    print('\n=== CPU使用効率分析 ===')
    print(f'平均CPU効率: {df["cpu_efficiency"].mean():.1f}%')
    print(f'平均使用コア数: {df["cpu_cores_used"].mean():.1f}/8')
    print(f'最大使用コア数: {df["cpu_cores_used"].max()}/8')
    
    print('\n=== エネミー数別FPS分析 ===')
    enemy_ranges = [(0, 50), (51, 100), (101, 150), (151, 200), (201, 250)]
    for low, high in enemy_ranges:
        range_data = df[(df['enemies_count'] >= low) & (df['enemies_count'] <= high)]
        if not range_data.empty:
            avg_fps = range_data['fps'].mean()
            print(f'エネミー {low}-{high}体: 平均FPS {avg_fps:.1f}')
    
    print('\n=== 詳細分析 ===')
    print(f'総データ数: {len(df)}')
    print(f'エネミー数範囲: {df["enemies_count"].min():.0f}-{df["enemies_count"].max():.0f}体')
    print(f'FPS範囲: {df["fps"].min():.1f}-{df["fps"].max():.1f}')
    
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()