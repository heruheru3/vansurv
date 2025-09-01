@echo off
REM VanSurv Windows版ビルドスクリプト
REM PyInstallerを使用してone-fileの実行ファイル(.exe)を作成

echo Building VanSurv for Windows...
echo.

REM 現在のディレクトリを取得
set SCRIPT_DIR=%~dp0

REM PyInstallerでアプリケーションをビルド
pyinstaller --noconfirm --onefile --windowed ^
--icon "%SCRIPT_DIR%assets\favicon.ico" ^
--add-data "%SCRIPT_DIR%__init__.py;." ^
--add-data "%SCRIPT_DIR%constants.py;." ^
--add-data "%SCRIPT_DIR%enemy.py;." ^
--add-data "%SCRIPT_DIR%player.py;." ^
--add-data "%SCRIPT_DIR%resources.py;." ^
--add-data "%SCRIPT_DIR%subitems.py;." ^
--add-data "%SCRIPT_DIR%ui.py;." ^
--add-data "%SCRIPT_DIR%collision.py;." ^
--add-data "%SCRIPT_DIR%game_logic.py;." ^
--add-data "%SCRIPT_DIR%game_utils.py;." ^
--add-data "%SCRIPT_DIR%weapons;weapons/" ^
--add-data "%SCRIPT_DIR%effects;effects/" ^
--add-data "%SCRIPT_DIR%assets;assets/" ^
--add-data "%SCRIPT_DIR%data;data/" ^
"%SCRIPT_DIR%main.py"

REM ビルド結果の確認
if exist "%SCRIPT_DIR%dist\main.exe" (
    echo.
    echo ✅ Build successful!
    echo Executable created at: %SCRIPT_DIR%dist\main.exe
    echo.
    echo To run the game:
    echo   dist\main.exe
    echo.
    echo Or double-click the executable file in the dist folder.
) else (
    echo.
    echo ❌ Build failed!
    echo Please check the output above for errors.
)

pause