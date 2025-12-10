# -*- coding: utf-8 -*-
import tkinter as tk
import urllib.request
import re
from tkinter import ttk, messagebox
import subprocess
import os
import threading
import shutil
import platform
from datetime import datetime


# --- 設定區 ---
try:
    from plugin_manager import PluginManager
except ImportError:
    # 若同層找不到，嘗試加入 path (雖通常不需要，為防萬一)
    import sys
    sys.path.append(os.getcwd())
    from plugin_manager import PluginManager

REPO_PATH = os.path.abspath(os.getcwd())

    def __init__(self, root):
        self.root = root
        self.system = platform.system()
        self.root.title(f"網頁存檔控制中心 (Local Archiver) - V56 模組化版")
        
        # 初始化 Plugin Manager
        self.plugin_manager = PluginManager()


        self.root.geometry("1000x700")

        font_name = '微軟正黑體' if self.system == 'Windows' else 'PingFang TC'
        style = ttk.Style()
        style.configure("Treeview", font=(font_name, 10), rowheight=25)
        style.configure("TButton", font=(font_name, 10))
        
        # --- 上方 ---
        frame_top = ttk.Frame(root, padding=10)
        frame_top.pack(fill=tk.X)

        self.url_var = tk.StringVar()
        ttk.Label(frame_top, text="網址:").pack(side=tk.LEFT, padx=5)
        self.entry_url = ttk.Entry(frame_top, textvariable=self.url_var, width=60)
        self.entry_url.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.entry_url.bind("<Return>", lambda event: self.start_download_thread())

        self.btn_download = ttk.Button(frame_top, text="🚀 立即抓取", command=self.start_download_thread)
        self.btn_download.pack(side=tk.LEFT, padx=5)

        # --- 中間 ---
        frame_mid = ttk.Frame(root, padding=10)
        frame_mid.pack(fill=tk.BOTH, expand=True)

        columns = ("filename", "size", "date")
        self.tree = ttk.Treeview(frame_mid, columns=columns, show="headings")
        self.tree.heading("filename", text="檔案名稱")
        self.tree.heading("size", text="大小")
        self.tree.heading("date", text="修改日期")
        self.tree.column("filename", width=500)
        self.tree.column("size", width=100)
        self.tree.column("date", width=150)

        scrollbar = ttk.Scrollbar(frame_mid, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<Double-1>", self.open_file)
        if self.system == "Darwin":
            self.tree.bind("<Button-2>", self.show_context_menu)
            self.tree.bind("<Button-3>", self.show_context_menu)
        else:
            self.tree.bind("<Button-3>", self.show_context_menu)

        # --- 下方 ---
        frame_bot = ttk.Frame(root, padding=10)
        frame_bot.pack(fill=tk.X)

        self.btn_refresh = ttk.Button(frame_bot, text="🔄 重新整理", command=self.load_files)
        self.btn_refresh.pack(side=tk.LEFT, padx=5)
        
        self.btn_check = ttk.Button(frame_bot, text="🏥 系統健檢", command=self.check_environment)
        self.btn_check.pack(side=tk.LEFT, padx=5)

        self.btn_sync = ttk.Button(frame_bot, text="☁️ 同步到 GitHub", command=self.sync_to_github)
        self.btn_sync.pack(side=tk.RIGHT, padx=5)

        # --- 狀態列 ---
        self.status_var = tk.StringVar()
        self.status_var.set(f"儲存位置: {REPO_PATH}")
        self.status_entry = tk.Entry(root, textvariable=self.status_var, relief=tk.SUNKEN, state='readonly')
        self.status_entry.pack(side=tk.BOTTOM, fill=tk.X)

        self.load_files()
        
        self.context_menu = tk.Menu(root, tearoff=0)
        self.context_menu.add_command(label="開啟檔案", command=self.open_file)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="❌ 刪除檔案", command=self.delete_file)
        
        self.btn_del = ttk.Button(frame_bot, text="🗑️ 刪除檔案", command=self.delete_file)
        self.btn_del.pack(side=tk.LEFT, padx=5)

    def log(self, message):
        self.status_var.set(message)

    def get_singlefile_cmd(self):
        return "single-file.cmd" if self.system == "Windows" else "single-file"

    def check_environment(self):
        self.log("正在檢查環境...")
        cmd_name = self.get_singlefile_cmd()
        sf_path = shutil.which(cmd_name) or shutil.which("single-file")
        if sf_path:
            self.log(f"✅ 環境正常: {sf_path}")
            return True, sf_path
        else:
            self.log("❌ 環境錯誤: 找不到 single-file")
            messagebox.showerror("錯誤", "找不到 single-file！\nMac 請輸入: sudo npm install -g single-file-cli")
            return False, None

    def load_files(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        try:
            files = [f for f in os.listdir(REPO_PATH) if f.endswith('.html')]
            files.sort(key=lambda x: os.path.getmtime(os.path.join(REPO_PATH, x)), reverse=True)
            for f in files:
                path = os.path.join(REPO_PATH, f)
                size = f"{os.path.getsize(path) / 1024:.1f} KB"
                mtime = datetime.fromtimestamp(os.path.getmtime(path)).strftime('%Y-%m-%d %H:%M')
                self.tree.insert("", "end", values=(f, size, mtime))
            self.log(f"已載入 {len(files)} 個檔案")
        except Exception as e:
            self.log(f"讀取列表錯誤: {str(e)}")

    def show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def open_file(self, event=None):
        selected = self.tree.selection()
        if not selected: return
        filename = self.tree.item(selected[0])['values'][0]
        filepath = os.path.join(REPO_PATH, filename)
        try:
            if self.system == "Windows": os.startfile(filepath)
            elif self.system == "Darwin": subprocess.run(["open", filepath], check=True)
            else: subprocess.run(["xdg-open", filepath], check=True)
        except Exception as e:
            messagebox.showerror("錯誤", str(e))

    def delete_file(self):
        selected = self.tree.selection()
        if not selected: return
        filename = self.tree.item(selected[0])['values'][0]
        filepath = os.path.join(REPO_PATH, filename)
        if messagebox.askyesno("確認刪除", f"確定要刪除 {filename} 嗎？"):
            try:
                os.remove(filepath)
                self.load_files()
                self.log(f"已刪除: {filename}")
            except Exception as e:
                messagebox.showerror("錯誤", str(e))

    def start_download_thread(self):
        url = self.url_var.get().strip()
        if not url: return
        ok, sf_path = self.check_environment()
        if not ok: return

        self.btn_download.config(state=tk.DISABLED)
        threading.Thread(target=self.run_singlefile, args=(url, sf_path)).start()

    def sanitize_filename(self, name):
        # 移除非法字元
        name = re.sub(r'[\\/*?:"<>|]', "", name)
        # 移除前後空白
        return name.strip()

    def get_webpage_title(self, url):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'})
            with urllib.request.urlopen(req, timeout=10) as response:
                content = response.read()
                # 嘗試偵測編碼
                charset = response.headers.get_content_charset()
                if not charset:
                    # 簡單猜測：看 meta tag
                    content_start = content[:1024].decode('ascii', errors='ignore')
                    match = re.search(r'charset=["\']?([\w-]+)', content_start, re.IGNORECASE)
                    if match:
                        charset = match.group(1)
                    else:
                        charset = 'utf-8' # 預設
                
                html = content.decode(charset, errors='ignore')
                title_match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
                if title_match:
                    return title_match.group(1).strip()
        except Exception as e:
            self.log(f"標題抓取失敗 (將使用預設名稱): {str(e)}")
        return None

    def run_singlefile(self, url, sf_path):
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        
        # 1. 嘗試抓取標題當作檔名
        self.log(f"正在分析網頁標題: {url} ...")
        page_title = self.get_webpage_title(url)
        
        if page_title:
            safe_title = self.sanitize_filename(page_title)
            filename = f"{safe_title}.html"
            # 檢查檔案是否已存在，若存在則加上時間戳記
            if os.path.exists(os.path.join(REPO_PATH, filename)):
                 filename = f"{safe_title}_{timestamp}.html"
        else:
            filename = f"saved-{timestamp}.html"
            
        full_filepath = os.path.join(REPO_PATH, filename)
        
        self.log(f"正在抓取並儲存為: {filename} ...")
        
        # --- V56 改用 Plugin System ---
        handler = self.plugin_manager.get_handler(url)
        js_arg = ""
        extra_args = []
        
        if handler:
            # 1. 取得 JS
            js_path_or_script = handler.get_js_script()
            if js_path_or_script:
                # 簡單判斷是檔案路徑還是腳本字串
                if os.path.exists(js_path_or_script):
                    js_arg = f"--browser-script={js_path_or_script}"
                else:
                    # 如果回傳的是 script 內容 (尚未支援，目前假設都是檔案路徑)
                    pass
            
            # 2. 取得額外參數
            extra_args = handler.get_custom_args()

            # 3. 處理檔名前綴 (Optional)
            prefix = handler.get_filename_prefix(url, page_title)
            if prefix:
                full_filepath = os.path.join(REPO_PATH, f"{prefix}{filename}")
        
        cmd = [
            sf_path, 
            url, 
            full_filepath,
            "--block-scripts=false", 
            "--load-deferred-images-max-idle-time=2000",
            "--browser-width=1920",
            "--browser-height=1080",
            "--browser-args=[\"--no-sandbox\"]"
        ]
        
        if js_arg:
            cmd.insert(3, js_arg)
            
        if extra_args:
            cmd.extend(extra_args)



        try:
            startupinfo = None
            if self.system == "Windows":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', startupinfo=startupinfo)
            stdout, stderr = process.communicate()

            if process.returncode == 0:
                if os.path.exists(full_filepath):
                    self.root.after(0, lambda: [self.load_files(), self.log(f"✅ 抓取成功: {filename}"), self.entry_url.delete(0, tk.END)])
                else:
                    self.root.after(0, lambda: self.log("❌ 假性成功：檔案未生成"))
            else:
                err_msg = stderr + "\n" + stdout
                self.root.after(0, lambda: messagebox.showerror("抓取失敗", f"SingleFile 報錯：\n\n{err_msg}"))
        except Exception as e:
            err_msg = str(e)
            self.root.after(0, lambda: messagebox.showerror("執行錯誤", f"Python 錯誤：\n{err_msg}"))
        finally:
            self.root.after(0, lambda: self.btn_download.config(state=tk.NORMAL))

    def sync_to_github(self):
        self.log("正在同步到 GitHub...")
        threading.Thread(target=self.run_git_sync).start()

    def run_git_sync(self):
        try:
            kwargs = {'creationflags': subprocess.CREATE_NO_WINDOW} if self.system == "Windows" else {}
            subprocess.run(["git", "add", "."], check=True, **kwargs)
            subprocess.run(["git", "commit", "-m", f"Local Update {datetime.now()}"], check=False, **kwargs)
            subprocess.run(["git", "pull", "--rebase"], check=True, **kwargs)
            subprocess.run(["git", "push"], check=True, **kwargs)
            self.root.after(0, lambda: [self.load_files(), self.log("✅ 同步完成")])
        except Exception as e:
            err_msg = str(e)
            self.root.after(0, lambda: messagebox.showerror("同步失敗", f"Git 錯誤：\n{err_msg}"))

if __name__ == "__main__":
    root = tk.Tk()
    app = ArchiverApp(root)
    root.mainloop()