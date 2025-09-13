#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enemy Image Management Tool
敵画像の管理とリネーム用ツール
"""

import os
import shutil
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import glob
import json

class EnemyImageTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Enemy Image Management Tool")
        self.root.geometry("800x1200")
        
        # 画像情報を格納するリスト
        self.image_data = []
        
        # フレーム作成
        self.create_widgets()
        
        # 画像を読み込み
        self.load_images()
        
        # 状態を自動読み込み
        self.auto_load_state()
        
        # 初期表示時にソート
        self.resort_display()
    
    def create_widgets(self):
        # メインフレーム
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # タイトル
        title_label = ttk.Label(main_frame, text="Enemy Image Management Tool", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 10))
        
        # 説明ラベル
        info_label = ttk.Label(main_frame, 
                              text="画像を選択して敵タイプと強さレベルを設定し、保存ボタンを押してください")
        info_label.pack(pady=(0, 10))
        
        # スクロール可能なフレーム用のコンテナ
        scroll_container = ttk.Frame(main_frame)
        scroll_container.pack(fill=tk.BOTH, expand=True)
        
        # スクロール可能なフレーム
        canvas = tk.Canvas(scroll_container)
        scrollbar = ttk.Scrollbar(scroll_container, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # パッキング
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # ボタンフレーム（一番下に配置）
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # リフレッシュボタン（横並び）
        refresh_button = ttk.Button(button_frame, text="リフレッシュ/並び替え", command=self.refresh_images)
        refresh_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 保存ボタン（横並び）
        save_button = ttk.Button(button_frame, text="保存", command=self.save_images)
        save_button.pack(side=tk.LEFT)
    
    def load_images(self):
        """_temp/enemyフォルダから画像を読み込み"""
        temp_path = "_temp/enemy"
        
        if not os.path.exists(temp_path):
            messagebox.showwarning("警告", f"フォルダが見つかりません: {temp_path}")
            return
        
        # 画像ファイルを取得（重複を完全に排除）
        image_extensions = [".png", ".jpg", ".jpeg", ".bmp", ".gif"]
        image_files = set()
        
        # os.listdirを使用してより確実にファイルを取得
        try:
            for filename in os.listdir(temp_path):
                file_path = os.path.join(temp_path, filename)
                if os.path.isfile(file_path):
                    _, ext = os.path.splitext(filename.lower())
                    if ext in image_extensions:
                        image_files.add(file_path)
        except Exception as e:
            messagebox.showerror("エラー", f"フォルダの読み取りエラー: {str(e)}")
            return
        
        # setをリストに変換してソート
        image_files = sorted(list(image_files))
        
        if not image_files:
            messagebox.showinfo("情報", f"画像ファイルが見つかりません: {temp_path}")
            return
        
        print(f"読み込んだ画像ファイル数: {len(image_files)}")  # デバッグ用
        
        # 画像データをクリア
        self.image_data = []
        
        # 既存のウィジェットを削除
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        # 画像を表示（まず全て作成してからソート）
        temp_image_data = []
        for i, image_path in enumerate(image_files):
            temp_image_data.append(self.create_image_row_data(i, image_path))
        
        # 画像データをクリア
        self.image_data = []
        
        # ソートして表示
        self.sort_and_display_images(temp_image_data)
    
    def create_image_row_data(self, index, image_path):
        """画像データを作成（まだ表示しない）"""
        filename = os.path.basename(image_path)
        return {
            'index': index,
            'path': image_path,
            'filename': filename
        }
    
    def sort_and_display_images(self, temp_data):
        """画像データをソートして表示"""
        # 状態を読み込んでソートキーを作成
        state_data = {}
        try:
            if os.path.exists('data/enemy_image_state.json'):
                with open('data/enemy_image_state.json', 'r', encoding='utf-8') as f:
                    state_data = json.load(f)
        except Exception:
            pass
        
        def get_sort_key(data):
            filename = data['filename']
            if filename in state_data:
                saved_data = state_data[filename]
                type_val = saved_data.get('type', 'none')
                level_val = saved_data.get('level', 'none')
                
                # noneの場合は大きな値を設定（後ろに回す）
                type_num = 999 if type_val == 'none' else int(type_val)
                level_num = 999 if level_val == 'none' else int(level_val)
                
                return (type_num, level_num, filename)
            else:
                # 状態がない場合は最後に回す
                return (999, 999, filename)
        
        # ソート実行
        temp_data.sort(key=get_sort_key)
        
        # ソート順で表示
        self.create_header_row()  # ヘッダーを最初に追加
        for data in temp_data:
            self.create_image_row(data['index'], data['path'])
    
    def create_header_row(self):
        """ヘッダー行を作成"""
        header_frame = ttk.Frame(self.scrollable_frame)
        header_frame.pack(fill=tk.X, pady=(5, 10), padx=5)
        
        # 画像エリアのスペーサー（32px + padding）
        image_spacer = ttk.Label(header_frame, text="", width=5)
        image_spacer.pack(side=tk.LEFT, padx=(0, 10))
        
        # ファイル名ヘッダー
        filename_header = ttk.Label(header_frame, text="ファイル名", width=20, font=("Arial", 9, "bold"))
        filename_header.pack(side=tk.LEFT, padx=(0, 10))
        
        # タイプヘッダー（列幅を合わせる）
        type_header_frame = ttk.Frame(header_frame)
        type_header_frame.pack(side=tk.LEFT, padx=(0, 10))
        
        type_main_label = ttk.Label(type_header_frame, text="タイプ", font=("Arial", 9, "bold"))
        type_main_label.pack()
        
        type_numbers_frame = ttk.Frame(type_header_frame)
        type_numbers_frame.pack()
        
        # タイプ番号ヘッダー（ラジオボタンと同じ幅で配置）
        for i in range(1, 5):
            type_num_label = ttk.Label(type_numbers_frame, text=f"{i:02d}", 
                                     font=("Arial", 8), width=3)
            type_num_label.pack(side=tk.LEFT, padx=2)
        
        # レベルヘッダー（列幅を合わせる）
        level_header_frame = ttk.Frame(header_frame)
        level_header_frame.pack(side=tk.LEFT, padx=(0, 10))
        
        level_main_label = ttk.Label(level_header_frame, text="レベル", font=("Arial", 9, "bold"))
        level_main_label.pack()
        
        level_numbers_frame = ttk.Frame(level_header_frame)
        level_numbers_frame.pack()
        
        # レベル番号ヘッダー（ラジオボタンと同じ幅で配置）
        for i in range(1, 6):
            level_num_label = ttk.Label(level_numbers_frame, text=f"{i:02d}", 
                                      font=("Arial", 8), width=3)
            level_num_label.pack(side=tk.LEFT, padx=2)
        
        # 有効ヘッダー
        enabled_header = ttk.Label(header_frame, text="有効", font=("Arial", 9, "bold"))
        enabled_header.pack(side=tk.LEFT, padx=(0, 10))

    def create_image_row(self, index, image_path):
        """画像行を作成"""
        row_frame = ttk.Frame(self.scrollable_frame)
        row_frame.pack(fill=tk.X, pady=5, padx=5)
        
        # 画像を読み込み、表示用にリサイズ
        try:
            pil_image = Image.open(image_path)
            # 16x16から32x32へニアレストネイバーで拡大
            pil_image = pil_image.resize((32, 32), Image.Resampling.NEAREST)
            photo = ImageTk.PhotoImage(pil_image)
            
            # 画像ラベル
            image_label = ttk.Label(row_frame, image=photo)
            image_label.image = photo  # 参照を保持
            image_label.pack(side=tk.LEFT, padx=(0, 10))
            
        except Exception as e:
            # 画像読み込みエラーの場合
            error_label = ttk.Label(row_frame, text="[画像エラー]", 
                                   foreground="red", width=10)
            error_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # ファイル名ラベル
        filename = os.path.basename(image_path)
        filename_label = ttk.Label(row_frame, text=filename, width=20)
        filename_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # 敵タイプ選択（ラジオボタン）
        type_var = tk.StringVar(value="none")
        type_frame = ttk.Frame(row_frame)
        type_frame.pack(side=tk.LEFT, padx=(0, 10))
        
        # タイプ1-4のラジオボタンを横並びで配置
        for i in range(1, 5):
            type_radio = ttk.Radiobutton(type_frame, text="", 
                                       variable=type_var, value=f"{i:02d}",
                                       command=self.auto_save_state)
            type_radio.pack(side=tk.LEFT, padx=2)
        
        # 強さレベル選択（ラジオボタン）
        level_var = tk.StringVar(value="none")
        level_frame = ttk.Frame(row_frame)
        level_frame.pack(side=tk.LEFT, padx=(0, 10))
        
        # レベル1-5のラジオボタンを横並びで配置
        for i in range(1, 6):
            level_radio = ttk.Radiobutton(level_frame, text="", 
                                        variable=level_var, value=f"{i:02d}",
                                        command=self.auto_save_state)
            level_radio.pack(side=tk.LEFT, padx=2)
        
        # 有効/無効チェックボックス（初期状態は無効）
        enabled_var = tk.BooleanVar(value=False)
        enabled_check = ttk.Checkbutton(row_frame, text="", variable=enabled_var,
                                       command=self.auto_save_state)
        enabled_check.pack(side=tk.LEFT, padx=(0, 10))
        
        # データを保存
        image_info = {
            'path': image_path,
            'filename': filename,
            'type_var': type_var,
            'level_var': level_var,
            'enabled_var': enabled_var
        }
        self.image_data.append(image_info)
    
    def save_images(self):
        """選択された画像をリネームしてコピー"""
        output_dir = "assets/character/enemy"
        
        # 出力ディレクトリを作成
        os.makedirs(output_dir, exist_ok=True)
        
        copied_files = []
        skipped_files = []
        error_files = []
        
        # 有効な画像データをソート用に抽出
        valid_images = []
        for image_info in self.image_data:
            if not image_info['enabled_var'].get():
                continue  # 無効な画像はスキップ
            
            enemy_type = image_info['type_var'].get()
            enemy_level = image_info['level_var'].get()
            
            # タイプまたはレベルが未選択の場合はスキップ
            if enemy_type == "none" or enemy_level == "none":
                skipped_files.append(f"{image_info['filename']}: タイプまたはレベルが未選択")
                continue
            
            valid_images.append(image_info)
        
        # ソート: 1.タイプ順 2.強さ順 3.ファイル名順
        valid_images.sort(key=lambda x: (
            int(x['type_var'].get()),  # タイプ順
            int(x['level_var'].get()), # 強さ順
            x['filename']              # ファイル名順
        ))
        
        for image_info in valid_images:
            source_path = image_info['path']
            enemy_type = image_info['type_var'].get()
            enemy_level = image_info['level_var'].get()
            
            # 新しいファイル名を生成
            new_filename = f"{enemy_type}-{enemy_level}.png"
            dest_path = os.path.join(output_dir, new_filename)
            
            try:
                # 画像をPNGとして保存（元のサイズを保持）
                with Image.open(source_path) as img:
                    # RGBA形式で保存（リサイズはしない）
                    if img.mode != 'RGBA':
                        img = img.convert('RGBA')
                    img.save(dest_path, 'PNG')
                
                copied_files.append(f"{image_info['filename']} → {new_filename}")
                
            except Exception as e:
                error_files.append(f"{image_info['filename']}: {str(e)}")
        
        # 結果を表示
        result_message = f"コピー完了:\n{len(copied_files)} 個のファイルをコピーしました。"
        
        if copied_files:
            result_message += "\n\n[コピーされたファイル]\n" + "\n".join(copied_files[:10])
            if len(copied_files) > 10:
                result_message += f"\n... 他 {len(copied_files) - 10} 個"
        
        if skipped_files:
            result_message += f"\n\n[スキップされたファイル]\n" + "\n".join(skipped_files[:5])
            if len(skipped_files) > 5:
                result_message += f"\n... 他 {len(skipped_files) - 5} 個"
        
        if error_files:
            result_message += f"\n\n[エラーファイル]\n" + "\n".join(error_files[:5])
            if len(error_files) > 5:
                result_message += f"\n... 他 {len(error_files) - 5} 個"
        
        messagebox.showinfo("結果", result_message)
    
    def auto_save_state(self):
        """変更時に自動で状態を保存"""
        try:
            state_data = {}
            for image_info in self.image_data:
                filename = image_info['filename']
                state_data[filename] = {
                    'type': image_info['type_var'].get(),
                    'level': image_info['level_var'].get(),
                    'enabled': image_info['enabled_var'].get()
                }
            
            with open('data/enemy_image_state.json', 'w', encoding='utf-8') as f:
                json.dump(state_data, f, ensure_ascii=False, indent=2)
                
        except Exception:
            pass  # エラーは無視（自動保存なのでユーザーに通知しない）
    
    def resort_display(self):
        """現在の表示をソート順に並び替え"""
        # 現在のウィジェットを削除
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        # image_dataをソートキーでソート
        def get_sort_key(image_info):
            type_val = image_info['type_var'].get()
            level_val = image_info['level_var'].get()
            
            type_num = 999 if type_val == 'none' else int(type_val)
            level_num = 999 if level_val == 'none' else int(level_val)
            
            return (type_num, level_num, image_info['filename'])
        
        self.image_data.sort(key=get_sort_key)
        
        # ソート順で再描画
        temp_image_data = []
        for image_info in self.image_data:
            temp_image_data.append({
                'index': 0,  # インデックスは再利用
                'path': image_info['path'],
                'filename': image_info['filename']
            })
        
        # image_dataをクリアして再構築
        old_data = self.image_data.copy()
        self.image_data = []
        
        # ヘッダーを追加
        self.create_header_row()
        
        for i, data in enumerate(temp_image_data):
            # 対応する古いデータを見つける
            old_info = None
            for old in old_data:
                if old['filename'] == data['filename']:
                    old_info = old
                    break
            
            if old_info:
                # 古い状態を保持して行を再作成
                self.create_image_row_with_state(i, data['path'], old_info)
            else:
                self.create_image_row(i, data['path'])
    
    def create_image_row_with_state(self, index, image_path, old_info):
        """既存の状態を保持して画像行を再作成"""
        row_frame = ttk.Frame(self.scrollable_frame)
        row_frame.pack(fill=tk.X, pady=5, padx=5)
        
        # 画像を読み込み、表示用にリサイズ
        try:
            pil_image = Image.open(image_path)
            # 16x16から32x32へニアレストネイバーで拡大
            pil_image = pil_image.resize((32, 32), Image.Resampling.NEAREST)
            photo = ImageTk.PhotoImage(pil_image)
            
            # 画像ラベル
            image_label = ttk.Label(row_frame, image=photo)
            image_label.image = photo  # 参照を保持
            image_label.pack(side=tk.LEFT, padx=(0, 10))
            
        except Exception as e:
            # 画像読み込みエラーの場合
            error_label = ttk.Label(row_frame, text="[画像エラー]", 
                                   foreground="red", width=10)
            error_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # ファイル名ラベル
        filename = os.path.basename(image_path)
        filename_label = ttk.Label(row_frame, text=filename, width=20)
        filename_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # 敵タイプ選択（ラジオボタン）
        type_var = tk.StringVar(value=old_info['type_var'].get())
        type_frame = ttk.Frame(row_frame)
        type_frame.pack(side=tk.LEFT, padx=(0, 10))
        
        # タイプ1-4のラジオボタンを横並びで配置
        for i in range(1, 5):
            type_radio = ttk.Radiobutton(type_frame, text="", 
                                       variable=type_var, value=f"{i:02d}",
                                       command=self.auto_save_state)
            type_radio.pack(side=tk.LEFT, padx=2)
        
        # 強さレベル選択（ラジオボタン）
        level_var = tk.StringVar(value=old_info['level_var'].get())
        level_frame = ttk.Frame(row_frame)
        level_frame.pack(side=tk.LEFT, padx=(0, 10))
        
        # レベル1-5のラジオボタンを横並びで配置
        for i in range(1, 6):
            level_radio = ttk.Radiobutton(level_frame, text="", 
                                        variable=level_var, value=f"{i:02d}",
                                        command=self.auto_save_state)
            level_radio.pack(side=tk.LEFT, padx=2)
        
        # 有効/無効チェックボックス（初期状態は無効）
        enabled_var = tk.BooleanVar(value=old_info['enabled_var'].get())
        enabled_check = ttk.Checkbutton(row_frame, text="", variable=enabled_var,
                                       command=self.auto_save_state)
        enabled_check.pack(side=tk.LEFT, padx=(0, 10))
        
        # データを保存
        image_info = {
            'path': image_path,
            'filename': filename,
            'type_var': type_var,
            'level_var': level_var,
            'enabled_var': enabled_var
        }
        self.image_data.append(image_info)
    
    def auto_load_state(self):
        """起動時に自動で状態を読み込み"""
        try:
            if not os.path.exists('data/enemy_image_state.json'):
                return
            
            with open('data/enemy_image_state.json', 'r', encoding='utf-8') as f:
                state_data = json.load(f)
            
            for image_info in self.image_data:
                filename = image_info['filename']
                if filename in state_data:
                    data = state_data[filename]
                    image_info['type_var'].set(data.get('type', 'none'))
                    image_info['level_var'].set(data.get('level', 'none'))
                    image_info['enabled_var'].set(data.get('enabled', False))
        
        except Exception:
            pass  # エラーは無視（自動読み込みなのでユーザーに通知しない）
    
    def save_state(self):
        """現在の状態をJSONファイルに保存"""
        state_data = {}
        for image_info in self.image_data:
            filename = image_info['filename']
            state_data[filename] = {
                'type': image_info['type_var'].get(),
                'level': image_info['level_var'].get(),
                'enabled': image_info['enabled_var'].get()
            }
        
        try:
            with open('data/enemy_image_state.json', 'w', encoding='utf-8') as f:
                json.dump(state_data, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("保存完了", "状態を data/enemy_image_state.json に保存しました")
        except Exception as e:
            messagebox.showerror("保存エラー", f"状態の保存に失敗しました: {str(e)}")
    
    def load_state(self):
        """JSONファイルから状態を読み込み"""
        try:
            if not os.path.exists('data/enemy_image_state.json'):
                messagebox.showwarning("ファイルなし", "data/enemy_image_state.json が見つかりません")
                return
            
            with open('data/enemy_image_state.json', 'r', encoding='utf-8') as f:
                state_data = json.load(f)
            
            loaded_count = 0
            for image_info in self.image_data:
                filename = image_info['filename']
                if filename in state_data:
                    data = state_data[filename]
                    image_info['type_var'].set(data.get('type', 'none'))
                    image_info['level_var'].set(data.get('level', 'none'))
                    image_info['enabled_var'].set(data.get('enabled', False))
                    loaded_count += 1
            
            messagebox.showinfo("読み込み完了", f"{loaded_count} 個の画像の状態を復元しました")
        
        except Exception as e:
            messagebox.showerror("読み込みエラー", f"状態の読み込みに失敗しました: {str(e)}")
    
    def refresh_images(self):
        """画像リストをリフレッシュして並び替え"""
        self.load_images()
        # リフレッシュ後も状態を復元
        self.auto_load_state()
        # 並び替えを実行
        self.resort_display()

def main():
    root = tk.Tk()
    app = EnemyImageTool(root)
    root.mainloop()

if __name__ == "__main__":
    main()
