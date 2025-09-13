@echo off
REM VanSurv Windows版 - 開発環境セットアップスクリプト
echo Setting up VanSurv development environment for Windows...
echo.

REM 必要なパッケージのインストール
echo Installing required packages...
pip install --upgrade pygame
pip install --upgrade pyinstaller

REM インストール結果の確認
echo.
echo ✅ Setup complete!
echo.
echo Required packages installed:
echo   - pygame (game engine)
echo   - pyinstaller (executable builder)
echo.
echo You can now run:
echo   python main.py                       (to run the game)
echo   buildtools\scripts\create_exe.bat    (to build executable)
echo.

pause
