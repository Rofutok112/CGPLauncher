#!/usr/bin/env python3
"""
選択の持続性をテストするスクリプト
"""

import tkinter as tk
from tkinter import ttk

class SelectionTest:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Selection Persistence Test")
        self.root.geometry("400x300")
        
        # 選択情報を保存する変数
        self.selected_item = None
        self.selected_index = None
        
        self.create_widgets()
        
    def create_widgets(self):
        # リストボックス
        self.listbox = tk.Listbox(self.root, height=10)
        self.listbox.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # テストデータ
        items = ["Game 1", "Game 2", "Game 3", "Game 4"]
        for item in items:
            self.listbox.insert(tk.END, item)
            
        # 選択イベントバインド
        self.listbox.bind('<<ListboxSelect>>', self.on_select)
        
        # Entry フィールド
        self.entry_var = tk.StringVar()
        self.entry = ttk.Entry(self.root, textvariable=self.entry_var, width=30)
        self.entry.pack(padx=10, pady=5)
        
        # ボタン
        button_frame = ttk.Frame(self.root)
        button_frame.pack(padx=10, pady=5)
        
        self.update_button = ttk.Button(button_frame, text="Update Selected", command=self.update_selected)
        self.update_button.pack(side=tk.LEFT, padx=5)
        
        self.status_button = ttk.Button(button_frame, text="Show Status", command=self.show_status)
        self.status_button.pack(side=tk.LEFT, padx=5)
        
    def on_select(self, event):
        """アイテム選択時の処理"""
        selection = self.listbox.curselection()
        if selection:
            index = selection[0]
            item = self.listbox.get(index)
            
            # 選択情報を保存
            self.selected_item = item
            self.selected_index = index
            
            # Entryフィールドに現在の値を設定
            self.entry_var.set(item)
            
            print(f"Selected: {item} (index: {index})")
        
    def update_selected(self):
        """選択されたアイテムを更新"""
        if self.selected_item is None or self.selected_index is None:
            print("No item selected")
            return
            
        new_value = self.entry_var.get()
        if new_value:
            # リストボックスを更新
            self.listbox.delete(self.selected_index)
            self.listbox.insert(self.selected_index, new_value)
            
            # 選択情報も更新
            self.selected_item = new_value
            
            # 選択を復元
            self.listbox.selection_set(self.selected_index)
            
            print(f"Updated to: {new_value}")
        
    def show_status(self):
        """現在の選択状態を表示"""
        listbox_selection = self.listbox.curselection()
        print(f"Listbox selection: {listbox_selection}")
        print(f"Stored selection: item='{self.selected_item}', index={self.selected_index}")
        
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = SelectionTest()
    app.run()