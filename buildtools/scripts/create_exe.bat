@echo off
REM VanSurv Windows版ビルドスクリプト
REM PyInstallerを使用してone-fileの実行ファイル(.exe)を作成

echo Building VanSurv for Windows...
echo.

REM 現在のディレクトリを取得（プロジェクトルートに移動）
set SCRIPT_DIR=%~dp0..\..\

REM プロジェクトルートに移動
cd /d "%SCRIPT_DIR%"

REM PyInstallerでアプリケーションをビルド
pyinstaller --noconfirm --onefile --windowed --clean --name heruheru3_vansurv ^
--hidden-import=colorsys ^
--hidden-import=math ^
--hidden-import=random ^
--hidden-import=json ^
--hidden-import=os ^
--hidden-import=sys ^
--hidden-import=datetime ^
--icon "assets\favicon.ico" ^
--add-data "constants.py;." ^
--add-data "core;core/" ^
--add-data "systems;systems/" ^
--add-data "ui;ui/" ^
--add-data "tools;tools/" ^
--add-data "weapons;weapons/" ^
--add-data "effects;effects/" ^
--add-data "assets;assets/" ^
--add-data "data;data/" ^
--add-data "map;map/" ^
--add-data "save;save/" ^
--add-data "utils;utils/" ^
"main.py"


REM ビルド結果の確認
if exist "dist\heruheru3_vansurv.exe" (
    echo.
    echo ✅ Build successful!
    echo Executable created at: dist\heruheru3_vansurv.exe
    echo.
    echo To run the game:
    echo   dist\heruheru3_vansurv.exe
    echo.
    echo Or double-click the executable file in the dist folder.
) else (
    echo.
    echo ❌ Build failed!
    echo Please check the output above for errors.
)

pause