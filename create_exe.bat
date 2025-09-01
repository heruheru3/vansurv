pyinstaller --noconfirm --onefile --windowed ^
--icon "E:\jupy_work\vansurv\assets\favicon.ico" ^
--add-data "E:\jupy_work\vansurv\__init__.py;." ^
--add-data "E:\jupy_work\vansurv\constants.py;." ^
--add-data "E:\jupy_work\vansurv\enemy.py;." ^
--add-data "E:\jupy_work\vansurv\generate_icons.py;." ^
--add-data "E:\jupy_work\vansurv\player.py;." ^
--add-data "E:\jupy_work\vansurv\resources.py;." ^
--add-data "E:\jupy_work\vansurv\subitems.py;." ^
--add-data "E:\jupy_work\vansurv\ui.py;." ^
--add-data "E:\jupy_work\vansurv\collision.py;." ^
--add-data "E:\jupy_work\vansurv\game_logic.py;." ^
--add-data "E:\jupy_work\vansurv\game_utils.py;." ^
--add-data "E:\jupy_work\vansurv\weapons;weapons/" ^
--add-data "E:\jupy_work\vansurv\effects;effects/" ^
--add-data "E:\jupy_work\vansurv\assets;assets/" ^
--add-data "E:\jupy_work\vansurv\data;data/" ^
"E:\jupy_work\vansurv\main.py"