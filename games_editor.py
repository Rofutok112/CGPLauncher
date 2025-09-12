import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
import shutil
from datetime import datetime
import urllib.request
import urllib.error
import threading

class GamesEditor:
    def __init__(self, root):
        self.is_saved = True  # 変更保存フラグ
        self.root = root
        self.root.title("Games.json エディター")
        self.root.geometry("600x780")
        self.root.resizable(False, False)  # 画面サイズ固定
        
        # JSONファイルのパス
        self.json_file = "games.json"
        self.games_data = []
        self.filtered_games = []  # 検索結果用
        self.is_new_game_mode = False  # 新規追加モードフラグ
        
        # GUI要素の初期化
        self.setup_ui()
        self.load_games()
        # 起動時に新規追加モードにする
        self.add_new_game()
        # 閉じるボタンのプロトコル設定
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        if not self.is_saved:
            if not messagebox.askyesno("警告", "保存されていない変更があります。終了してもよろしいですか？"):
                return
        self.root.destroy()

    def mark_unsaved(self, *args):
        self.is_saved = False

    def show_status(self, message, status_type="info", auto_clear=True, duration=3000):
        """ステータスバーにメッセージを表示
        
        Args:
            message (str): 表示するメッセージ
            status_type (str): メッセージの種類 ("info", "success", "warning", "error")
            auto_clear (bool): 自動でクリアするかどうか
            duration (int): 自動クリアまでの時間（ミリ秒）
        """
        color_map = {
            "info": "blue",
            "success": "green", 
            "warning": "orange",
            "error": "red"
        }
        
        self.status_label.configure(text=message, foreground=color_map.get(status_type, "black"))
        
        if auto_clear:
            self.root.after(duration, lambda: self.status_label.configure(text="準備完了", foreground="green"))
        
    def clear_status(self):
        """ステータスバーをクリア"""
        self.status_label.configure(text="準備完了", foreground="green")
        
    def setup_ui(self):
        # メインフレーム
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 検索フレーム
        search_frame = ttk.Frame(main_frame)
        search_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(search_frame, text="検索:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.on_search_change)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(search_frame, text="クリア", command=self.clear_search).pack(side=tk.LEFT)
        
        # ゲームリスト
        list_frame = ttk.LabelFrame(main_frame, text="ゲーム一覧", padding="5")
        list_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # リストボックスとスクロールバー
        self.game_listbox = tk.Listbox(list_frame, height=8)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.game_listbox.yview)
        self.game_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.game_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # リストボックスの選択イベント
        self.game_listbox.bind('<<ListboxSelect>>', self.on_game_select)
        
        # ボタンフレーム
        button_frame = ttk.Frame(list_frame)
        button_frame.grid(row=1, column=0, columnspan=2, pady=(5, 0))
        
        ttk.Button(button_frame, text="新規ゲーム追加", command=self.add_new_game).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="選択したゲームを更新", command=self.update_current_game).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="選択したゲームを削除", command=self.delete_game).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="保存", command=self.save_games).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="再読み込み", command=self.load_games).pack(side=tk.LEFT)
        
        # 編集フレーム
        edit_frame = ttk.LabelFrame(main_frame, text="ゲーム編集", padding="5")
        edit_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 編集フィールド
        self.create_edit_fields(edit_frame)
        
        # ステータスバーフレーム
        status_frame = ttk.Frame(self.root)
        status_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=10, pady=(0, 5))
        
        # ステータスラベル
        self.status_label = ttk.Label(status_frame, text="準備完了", foreground="green")
        self.status_label.pack(side=tk.LEFT)
        
        # グリッド設定
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        edit_frame.columnconfigure(1, weight=1)
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        status_frame.columnconfigure(0, weight=1)
        
    def create_edit_fields(self, parent):
        """編集フィールドを作成"""
        # 基本情報フィールド
        basic_fields = [
            ("name", "ゲーム名"),
            ("version", "バージョン"),
            ("authors", "作者（カンマ区切り）"),
            ("tags", "タグ（カンマ区切り）"),
        ]
        
        # ダウンロード関連フィールド（セット）
        download_fields = [
            ("url", "ダウンロードURL"),
            ("buildFile", "実行ファイル名"),
        ]
        
        # その他のURL
        url_fields = [
            ("unityroomurl", "unityroomURL"),
            ("githuburl", "GitHubURL"),
        ]
        
        # その他の情報
        other_fields = [
            ("description", "説明"),
            ("image", "画像URL"),
            ("markdown", "MarkdownファイルURL")
        ]
        
        self.entry_vars = {}
        row = 0
        
        # 基本情報セクション
        ttk.Label(parent, text="基本情報", font=('', 10, 'bold')).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        row += 1
        
        for field, label in basic_fields:
            ttk.Label(parent, text=label + ":").grid(row=row, column=0, sticky=tk.W, padx=(0, 5), pady=2)
            var = tk.StringVar()
            var.trace('w', self.mark_unsaved)  # 変更検知を追加
            entry = ttk.Entry(parent, textvariable=var, width=50)
            entry.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=2)
            self.entry_vars[field] = var
            row += 1
            
        # ダウンロード情報セクション（セット）
        ttk.Separator(parent, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        row += 1
        ttk.Label(parent, text="ダウンロード情報", font=('', 10, 'bold')).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        row += 1
        
        for field, label in download_fields:
            ttk.Label(parent, text=label + ":").grid(row=row, column=0, sticky=tk.W, padx=(0, 5), pady=2)
            var = tk.StringVar()
            var.trace('w', self.mark_unsaved)  # 変更検知を追加
            entry = ttk.Entry(parent, textvariable=var, width=50)
            entry.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=2)
            self.entry_vars[field] = var
            row += 1
            
        # URL情報セクション
        ttk.Separator(parent, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        row += 1
        ttk.Label(parent, text="URL情報", font=('', 10, 'bold')).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        row += 1
        
        for field, label in url_fields:
            ttk.Label(parent, text=label + ":").grid(row=row, column=0, sticky=tk.W, padx=(0, 5), pady=2)
            var = tk.StringVar()
            var.trace('w', self.mark_unsaved)  # 変更検知を追加
            entry = ttk.Entry(parent, textvariable=var, width=50)
            entry.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=2)
            self.entry_vars[field] = var
            row += 1
            
        # その他の情報セクション
        ttk.Separator(parent, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        row += 1
        ttk.Label(parent, text="その他の情報", font=('', 10, 'bold')).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        row += 1
        
        for field, label in other_fields:
            ttk.Label(parent, text=label + ":").grid(row=row, column=0, sticky=tk.W, padx=(0, 5), pady=2)
            
            if field in ["description"]:
                # 複数行テキスト
                text_widget = tk.Text(parent, height=3, width=50)
                text_widget.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=2)
                # Text ウィジェットの変更検知を追加
                text_widget.bind('<KeyRelease>', self.mark_unsaved)
                text_widget.bind('<Button-1>', self.mark_unsaved)  # マウスでの変更も検知
                self.entry_vars[field] = text_widget
            else:
                # 単一行テキスト
                var = tk.StringVar()
                var.trace('w', self.mark_unsaved)  # 変更検知を追加
                entry = ttk.Entry(parent, textvariable=var, width=50)
                entry.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=2)
                self.entry_vars[field] = var
            
            row += 1
            
        # 新規追加モード用のボタンフレーム
        self.new_game_button_frame = ttk.Frame(parent)
        self.new_game_button_frame.grid(row=row, column=0, columnspan=2, pady=(10, 0))
        
        self.save_new_button = ttk.Button(self.new_game_button_frame, text="新しいゲームを保存", command=self.save_new_game, state="disabled")
        self.save_new_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.cancel_new_button = ttk.Button(self.new_game_button_frame, text="キャンセル", command=self.cancel_new_game, state="disabled")
        self.cancel_new_button.pack(side=tk.LEFT)
        

            
    def load_games(self):
        """games.jsonファイルを読み込む"""
        try:
            if os.path.exists(self.json_file):
                with open(self.json_file, 'r', encoding='utf-8') as f:
                    self.games_data = json.load(f)
            else:
                self.games_data = []
                
            self.filtered_games = self.games_data.copy()  # 初期状態では全ゲームを表示
            self.refresh_game_list()
            self.clear_edit_fields()
            self.is_saved = True  # データ読み込み後にフラグをリセット
            self.show_status("ゲームデータを読み込みました", "success")
            
        except Exception as e:
            self.show_status(f"ファイルの読み込みに失敗しました: {str(e)}", "error", auto_clear=False)
            
    def refresh_game_list(self):
        """ゲームリストを更新"""
        self.game_listbox.delete(0, tk.END)
        for game in self.filtered_games:
            self.game_listbox.insert(tk.END, game.get("name", "名前なし"))
            
    def on_game_select(self, event):
        """ゲーム選択時の処理"""
        selection = self.game_listbox.curselection()
        if selection:
            # 新規追加モードを終了
            if self.is_new_game_mode:
                self.exit_new_game_mode()
                
            index = selection[0]
            if index < len(self.filtered_games):
                game = self.filtered_games[index]
                self.load_game_to_fields(game)
            
    def load_game_to_fields(self, game):
        """選択したゲームの情報を編集フィールドに読み込む"""
        for field, widget in self.entry_vars.items():
            value = game.get(field, "")
            
            if field == "authors" and isinstance(value, list):
                value = ", ".join(value)
            elif field == "tags" and isinstance(value, list):
                value = ", ".join(value)
                
            if isinstance(widget, tk.Text):
                widget.delete(1.0, tk.END)
                widget.insert(1.0, str(value))
            else:
                widget.set(str(value))
                
    def clear_edit_fields(self):
        """編集フィールドをクリア"""
        for field, widget in self.entry_vars.items():
            if isinstance(widget, tk.Text):
                widget.delete(1.0, tk.END)
            else:
                widget.set("")
                
    def get_current_game_data(self):
        """現在の編集フィールドからゲームデータを取得"""
        game_data = {}
        
        for field, widget in self.entry_vars.items():
            if isinstance(widget, tk.Text):
                value = widget.get(1.0, tk.END).strip()
            else:
                value = widget.get().strip()
                
            if field == "authors":
                game_data[field] = [author.strip() for author in value.split(",") if author.strip()]
            elif field == "tags":
                game_data[field] = [tag.strip() for tag in value.split(",") if tag.strip()]
            else:
                game_data[field] = value
                
        return game_data
        
    def validate_game_data(self, game_data):
        """ゲームデータのバリデーション"""
        # ゲーム名必須チェック
        if not game_data.get("name"):
            self.show_status("ゲーム名を入力してください", "warning", auto_clear=False)
            return False
            
        # URL必須チェック（GitHubURL、UnityRoomURL、ダウンロードURLのいずれか1つ以上）
        url_fields = ["url", "unityroomurl", "githuburl"]
        has_url = any(game_data.get(field, "").strip() for field in url_fields)
        
        if not has_url:
            self.show_status("GitHubURL、UnityRoomURL、ダウンロードURLのいずれか1つ以上を入力してください", "warning", auto_clear=False)
            return False
            
        # ダウンロードURLと実行ファイル名のセットチェック
        download_url = game_data.get("url", "").strip()
        build_file = game_data.get("buildFile", "").strip()
        
        if download_url and not build_file:
            self.show_status("ダウンロードURLを入力した場合は、実行ファイル名も入力してください", "warning", auto_clear=False)
            return False
            
        if build_file and not download_url:
            self.show_status("実行ファイル名を入力した場合は、ダウンロードURLも入力してください", "warning", auto_clear=False)
            return False
            
        return True
        
    def add_new_game(self):
        """新規ゲーム追加モードを開始"""
        # フィールドをクリア
        self.clear_edit_fields()
        
        # 選択をクリア
        self.game_listbox.selection_clear(0, tk.END)
        
        # 新規追加モードに設定
        self.is_new_game_mode = True
        
        # 編集フレームのタイトルを変更
        for child in self.root.winfo_children():
            if isinstance(child, ttk.Frame):
                for grandchild in child.winfo_children():
                    if isinstance(grandchild, ttk.LabelFrame) and "ゲーム編集" in str(grandchild.cget("text")):
                        grandchild.configure(text="新規ゲーム追加")
        
        # 新規追加用ボタンを有効化
        self.save_new_button.configure(state="normal")
        self.cancel_new_button.configure(state="normal")
        
        # 通常の更新ボタンを無効化
        for child in self.root.winfo_children():
            if isinstance(child, ttk.Frame):
                for grandchild in child.winfo_children():
                    if isinstance(grandchild, ttk.LabelFrame):
                        for button_frame in grandchild.winfo_children():
                            if isinstance(button_frame, ttk.Frame):
                                for button in button_frame.winfo_children():
                                    if isinstance(button, ttk.Button) and "更新" in str(button.cget("text")):
                                        button.configure(state="disabled")
        
        self.show_status("新しいゲームの情報を入力してください", "info")
        
    def save_new_game(self):
        """新しいゲームを保存"""
        game_data = self.get_current_game_data()
        
        # バリデーションチェック
        if not self.validate_game_data(game_data):
            return
        
        # URL検証を実行
        url_check_result = self._check_urls_sync(game_data)
        
        # URL検証結果を表示
        if url_check_result['has_urls']:
            # 検証結果のダイアログを表示
            if url_check_result['results']:
                result_message = "URL検証結果:\n\n" + "\n".join(url_check_result['results'])
                
                # 無効なURLがある場合は確認
                if not url_check_result['all_valid']:
                    result_message += "\n\n無効なURLがありますが、このまま保存しますか？"
                    if not messagebox.askyesno("URL検証結果", result_message):
                        return
                else:
                    # URL検証結果の成功部分のみステータスバーに表示
                    success_count = url_check_result['valid_count']
                    total_count = url_check_result['total_count']
                    self.show_status(f"URL検証完了: {success_count}/{total_count} 個のURLが有効", "success")
            
        self.games_data.append(game_data)
        
        # 検索をクリアして全ゲームを表示
        self.search_var.set("")
        self.filtered_games = self.games_data.copy()
        self.refresh_game_list()
        
        # 新しく追加したゲームを選択
        try:
            new_index = next(i for i, game in enumerate(self.filtered_games) if game == game_data)
            self.game_listbox.selection_set(new_index)
            self.load_game_to_fields(game_data)
        except StopIteration:
            pass
        
        # 新規追加モードを終了
        self.exit_new_game_mode()
        
        self.is_saved = True  # 新しいゲーム追加後にフラグをリセット
        self.show_status("新しいゲームを追加しました", "success")
        
    def cancel_new_game(self):
        """新規ゲーム追加をキャンセル"""
        self.clear_edit_fields()
        self.exit_new_game_mode()
        self.is_saved = True  # キャンセル時にフラグをリセット
        
    def exit_new_game_mode(self):
        """新規追加モードを終了"""
        self.is_new_game_mode = False
        
        # 編集フレームのタイトルを元に戻す
        for child in self.root.winfo_children():
            if isinstance(child, ttk.Frame):
                for grandchild in child.winfo_children():
                    if isinstance(grandchild, ttk.LabelFrame) and "新規ゲーム追加" in str(grandchild.cget("text")):
                        grandchild.configure(text="ゲーム編集")
        
        # 新規追加用ボタンを無効化
        self.save_new_button.configure(state="disabled")
        self.cancel_new_button.configure(state="disabled")
        
        # 通常の更新ボタンを有効化
        for child in self.root.winfo_children():
            if isinstance(child, ttk.Frame):
                for grandchild in child.winfo_children():
                    if isinstance(grandchild, ttk.LabelFrame):
                        for button_frame in grandchild.winfo_children():
                            if isinstance(button_frame, ttk.Frame):
                                for button in button_frame.winfo_children():
                                    if isinstance(button, ttk.Button) and "更新" in str(button.cget("text")):
                                        button.configure(state="normal")
        
    def delete_game(self):
        """選択したゲームを削除"""
        selection = self.game_listbox.curselection()
        if not selection:
            self.show_status("削除するゲームを選択してください", "warning")
            return
            
        index = selection[0]
        if index >= len(self.filtered_games):
            return
            
        game = self.filtered_games[index]
        game_name = game.get("name", "名前なし")
        
        if messagebox.askyesno("確認", f"ゲーム '{game_name}' を削除しますか？"):
            # 元のリストからも削除
            actual_index = self.games_data.index(game)
            del self.games_data[actual_index]
            
            # フィルターリストも更新
            self.on_search_change()
            self.clear_edit_fields()
            self.is_saved = True  # ゲーム削除後にフラグをリセット
            self.show_status("ゲームを削除しました", "success")
            
    def update_current_game(self):
        """現在選択中のゲームを更新"""
        # 新規追加モードの場合は何もしない
        if self.is_new_game_mode:
            self.show_status("新規追加モードです。「新しいゲームを保存」ボタンを使用してください", "warning")
            return
            
        selection = self.game_listbox.curselection()
        if not selection:
            self.show_status("更新するゲームを選択してください", "warning")
            return
            
        index = selection[0]
        if index >= len(self.filtered_games):
            return
            
        game_data = self.get_current_game_data()
        
        # バリデーションチェック
        if not self.validate_game_data(game_data):
            return
            
        # 元のリストでの実際のインデックスを取得
        actual_index = self.get_actual_index(index)
        self.games_data[actual_index] = game_data
        
        # フィルターリストも更新
        self.on_search_change()
        
        # 更新したゲームを再選択（可能であれば）
        try:
            new_index = self.filtered_games.index(game_data)
            self.game_listbox.selection_set(new_index)
        except ValueError:
            pass
            
        self.is_saved = True  # ゲーム更新後にフラグをリセット
        self.show_status("ゲーム情報を更新しました", "success")
        
    def save_games(self):
        """現在の編集内容を反映してからJSONファイルに保存"""
        selection = self.game_listbox.curselection()
        if selection:
            # 現在選択中のゲームがあれば更新
            index = selection[0]
            game_data = self.get_current_game_data()
            if self.validate_game_data(game_data):
                # 検索フィルターがある場合は元のインデックスを取得
                actual_index = self.get_actual_index(index)
                self.games_data[actual_index] = game_data
            else:
                return  # バリデーションエラーの場合は保存を中止
                
        try:
            # バックアップを作成
            self.create_backup()
            
            with open(self.json_file, 'w', encoding='utf-8') as f:
                json.dump(self.games_data, f, ensure_ascii=False, indent=2)
            self.is_saved = True  # 保存完了後にフラグをリセット
            self.show_status("games.jsonを保存しました", "success")
        except Exception as e:
            self.show_status(f"保存に失敗しました: {str(e)}", "error", auto_clear=False)
            
    def create_backup(self):
        """バックアップファイルを作成"""
        if os.path.exists(self.json_file):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = "backup"
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            backup_name = os.path.join(backup_dir, f"games_backup_{timestamp}.json")
            shutil.copy2(self.json_file, backup_name)
            
    def on_search_change(self, *args):
        """検索テキストが変更された時の処理"""
        search_text = self.search_var.get().lower()
        
        if not search_text:
            self.filtered_games = self.games_data.copy()
        else:
            self.filtered_games = []
            for game in self.games_data:
                # ゲーム名、作者、タグ、説明で検索
                if (search_text in game.get("name", "").lower() or
                    any(search_text in author.lower() for author in game.get("authors", [])) or
                    any(search_text in tag.lower() for tag in game.get("tags", [])) or
                    search_text in game.get("description", "").lower()):
                    self.filtered_games.append(game)
                    
        self.refresh_game_list()
        
    def clear_search(self):
        """検索をクリア"""
        self.search_var.set("")
        
    def get_actual_index(self, filtered_index):
        """フィルター後のインデックスから元のインデックスを取得"""
        if filtered_index < len(self.filtered_games):
            filtered_game = self.filtered_games[filtered_index]
            return self.games_data.index(filtered_game)
        return filtered_index
        
    def _check_urls_sync(self, game_data):
        """URL検証の同期版（保存時用）"""
        url_fields = {
            "url": "ダウンロードURL",
            "unityroomurl": "unityroomURL", 
            "githuburl": "GitHubURL",
            "image": "画像URL",
            "markdown": "MarkdownURL"
        }
        
        results = []
        valid_count = 0
        total_count = 0
        
        for field, label in url_fields.items():
            url = game_data.get(field, "").strip()
            if url:
                total_count += 1
                status = self._check_single_url(url)
                if status == "有効":
                    valid_count += 1
                    results.append(f"✅ {label}: {status}")
                else:
                    results.append(f"❌ {label}: {status}")
        
        return {
            'has_urls': total_count > 0,
            'total_count': total_count,
            'valid_count': valid_count,
            'all_valid': valid_count == total_count and total_count > 0,
            'results': results
        }
        
    def _check_single_url(self, url):
        """単一URLの有効性をチェック"""
        try:
            # User-Agentを設定してリクエスト
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            
            # タイムアウト5秒でリクエスト実行
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.getcode() == 200:
                    return "有効"
                else:
                    return f"エラー (HTTP {response.getcode()})"
        except urllib.error.HTTPError as e:
            return f"HTTPエラー ({e.code})"
        except urllib.error.URLError as e:
            return f"URLエラー ({str(e)})"
        except Exception as e:
            return f"エラー ({str(e)})"

def main():
    root = tk.Tk()
    app = GamesEditor(root)
    root.mainloop()

if __name__ == "__main__":
    main()
