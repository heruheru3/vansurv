@echo off
chcp 65001 > nul
echo =======================================
echo   レザルト画面テストツール
echo =======================================
echo.
echo このツールは以下の機能をテストできます:
echo - 武器ダメージ統計表示
echo - エネミー撃破統計表示  
echo - ボス撃破統計表示
echo - ゲームクリア/オーバー画面
echo - レイアウト調整確認
echo.
echo 操作方法:
echo   SPACE: テストパターン切り替え
echo   C: クリア/オーバーモード切り替え
echo   D: ダメージ統計表示切り替え
echo   LEFT/RIGHT: ボタン選択
echo   ENTER: ボタン実行（テストモード）
echo   ESC: 終了
echo.
pause
python test_result_screen.py
pause