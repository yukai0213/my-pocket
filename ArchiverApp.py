import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import os
import threading
import shutil
import platform
import sys
from datetime import datetime

# --- 設定區 ---
REPO_PATH = os.getcwd() 

class ArchiverApp:
    def __init__(self, root):
        self.root = root
        self.system = platform.system() # 偵測作業系統 (Windows/Darwin/Linux)
        self.root.title(f"網頁存檔控制中心 (Local Archiver) - V49 {self.system} 版")
        self.root.geometry("950x650")

        # 字型設定 (Mac 和 Windows 字型不同)
        font_name = '微軟正黑體' if self.system == 'Windows' else 'PingFang TC'
        
        style = ttk.Style()
        style.configure("Treeview", font=(font_name, 10), rowheight=25)
        style.configure("TButton", font=(font_name, 10))
        style.configure("TLabel", font=(font_name, 10))
        
        # --- 1. 上方操作區 ---
        frame_top = ttk.Frame(root, padding=10)
        frame_top.pack(fill=tk.X)

        self.url_var = tk.StringVar()
        ttk.Label(frame_top, text="網址:").pack(side=tk.LEFT, padx=5)
        self.entry_url = ttk.Entry(frame_top, textvariable=self.url_var, width=60)
        self.entry_url.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.entry_url.bind("<Return>", lambda event: self.start_download_thread())

        self.btn_download = ttk.Button(frame_top, text="🚀 立即抓取", command=self.start_download_thread)
        self.btn_download.pack(side=tk.LEFT, padx=5)

        # --- 2. 中間列表區 ---
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
        self.tree.bind("<Button-3>", self.show_context_menu)

        # --- 3. 下方功能區 ---
        frame_bot = ttk.Frame(root, padding=10)
        frame_bot.pack(fill=tk.X)

        self.btn_refresh = ttk.Button(frame_bot, text="🔄 重新整理", command=self.load_files)
        self.btn_refresh.pack(side=tk.LEFT, padx=5)
        
        self.btn_check = ttk.Button(frame_bot, text="🏥 系統健檢", command=self.check_environment)
        self.btn_check.pack(side=tk.LEFT, padx=5)

        self.btn_sync = ttk.Button(frame_bot, text="☁️ 同步到 GitHub", command=self.sync_to_github)
        self.btn_sync.pack(side=tk.RIGHT, padx=5)

        # --- 4. 狀態列 ---
        self.status_var = tk.StringVar()
        self.status_var.set("系統就緒")
        self.status_entry = tk.Entry(root, textvariable=self.status_var, relief=tk.SUNKEN, state='readonly')
        self.status_entry.pack(side=tk.BOTTOM, fill=tk.X)

        self.load_files()
        
        self.context_menu = tk.Menu(root, tearoff=0)
        self.context_menu.add_command(label="開啟檔案", command=self.open_file)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="❌ 刪除檔案", command=self.delete_file)

    def log(self, message):
        self.status_var.set(message)

    def get_singlefile_cmd(self):
        """根據作業系統決定指令名稱"""
        if self.system == "Windows":
            return "single-file.cmd"
        else:
            return "single-file" # Mac/Linux

    def check_environment(self):
        self.log("正在檢查環境...")
        cmd_name = self.get_singlefile_cmd()
        sf_path = shutil.which(cmd_name)
        
        if sf_path:
            self.log(f"✅ 環境正常: {sf_path}")
            return True
        else:
            # 再次嘗試找沒有副檔名的
            if shutil.which("single-file"):
                self.log(f"✅ 環境正常: single-file")
                return True
                
            self.log(f"❌ 環境錯誤: 找不到 {cmd_name} 指令！")
            msg = "找不到 single-file！\n\nMac 請執行: sudo npm install -g single-file-cli\nWindows 請執行: npm install -g single-file-cli"
            messagebox.showerror("錯誤", msg)
            return False

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
        
        # 跨平台開啟檔案
        try:
            if self.system == "Windows":
                os.startfile(filepath)
            elif self.system == "Darwin": # macOS
                subprocess.run(["open", filepath], check=True)
            else: # Linux
                subprocess.run(["xdg-open", filepath], check=True)
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
        if not self.check_environment(): return

        self.btn_download.config(state=tk.DISABLED)
        threading.Thread(target=self.run_singlefile, args=(url,)).start()

    def run_singlefile(self, url):
        self.log(f"正在抓取: {url} ...")
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        filename = f"saved-{timestamp}.html"
        
        # --- V48 連結復活版 JS 腳本 (跨平台通用) ---
        js_script = r"""
        (function() {
            console.log("Local Archiver V48 Running (Native Anchor Mode)...");
            window.scrollBy(0, 100); setTimeout(() => window.scrollBy(0, -100), 500);
            
            function queryAllDeep(selector, root = document) {
                let elements = Array.from(root.querySelectorAll(selector));
                const hosts = Array.from(root.querySelectorAll('*')).filter(e => e.shadowRoot);
                for (const host of hosts) {
                    elements = elements.concat(queryAllDeep(selector, host.shadowRoot));
                }
                return elements;
            }

            function fixAll() {
                const targets = [...queryAllDeep('iframe'), ...queryAllDeep('video')];
                targets.forEach(el => {
                    if(el.dataset.patched === "true") return;
                    
                    let tagName = el.tagName.toLowerCase();
                    let src = "";
                    if (tagName === 'iframe') src = el.src || el.dataset.src || "";
                    else if (tagName === 'video') src = el.currentSrc || el.src || "";

                    if(!src || src === "about:blank") return;
                    if(el.offsetWidth < 30) return;

                    let bg='rgba(0,0,0,0.8)', icon='🔗', txt='開啟內容', col='#007bff', url=src;
                    
                    if(src.includes('youtube') || src.includes('youtu.be')) {
                        let m = src.match(/([a-zA-Z0-9_-]{11})/);
                        if(m) { bg='url(https://img.youtube.com/vi/'+m[1]+'/hqdefault.jpg)'; col='#c00'; icon='▶'; txt='YouTube'; url='https://www.youtube.com/watch?v='+m[1]; }
                    } else if(src.includes('vimeo')) {
                        let m = src.match(/video\/(\d+)/);
                        if(m) { bg='url(https://vumbnail.com/'+m[1]+'.jpg)'; col='#1ab7ea'; icon='▶'; txt='Vimeo'; url='https://vimeo.com/'+m[1]; }
                    } else if(tagName === 'video') {
                        icon='🎬'; txt='原始檔'; col='#28a745';
                        bg = 'rgba(0,0,0,0.5)';
                    }

                    // 處理父層連結衝突
                    let parentLink = el.closest('a');
                    if (parentLink) {
                        parentLink.removeAttribute('href'); 
                        parentLink.style.cursor = 'default';
                        parentLink.onclick = (e) => e.preventDefault();
                    }

                    let card = document.createElement('a');
                    card.className = 'my-fix-card';
                    card.href = url;
                    card.target = "_blank";
                    card.rel = "noopener noreferrer";
                    
                    card.style.cssText = `position:absolute;top:0;left:0;width:100%;height:100%;background:${bg} center/cover no-repeat;display:flex;flex-direction:column;align-items:center;justify-content:center;z-index:2147483647 !important;cursor:pointer;border:2px solid ${col};box-sizing:border-box;border-radius:inherit;text-decoration:none;`;
                    card.innerHTML = `<div style="background:rgba(0,0,0,0.7);padding:5px 15px;border-radius:20px;text-align:center;color:white;font-weight:bold;font-size:14px;box-shadow:0 2px 5px rgba(0,0,0,0.5);">${icon} ${txt}</div>`;
                    
                    if(el.parentNode) {
                        let p = el.parentNode;
                        if(getComputedStyle(p).position==='static') p.style.position='relative';
                        p.insertBefore(card, el);
                        el.style.opacity = '0';
                        el.style.pointerEvents = 'none';
                        el.dataset.patched = "true";
                    }
                });
            }
            setInterval(fixAll, 1000);
        })();
        """
        
        with open("local_fix.js", "w", encoding="utf-8") as f:
            f.write(js_script)

        # 組合指令 (跨平台)
        cmd_name = self.get_singlefile_cmd()
        cmd = [
            cmd_name, 
            url, 
            filename,
            "--browser-script=local_fix.js",
            "--block-scripts=false", 
            "--load-deferred-images-max-idle-time=2000",
            "--browser-width=1920",
            "--browser-height=1080",
            "--browser-args=[\"--no-sandbox\"]"
        ]

        try:
            # Mac 不需要 startupinfo
            if self.system == "Windows":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', startupinfo=startupinfo)
            else:
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')

            stdout, stderr = process.communicate()

            if process.returncode == 0:
                self.root.after(0, lambda: [self.load_files(), self.log(f"✅ 抓取成功: {filename}"), self.entry_url.delete(0, tk.END)])
            else:
                err_msg = stderr
                self.root.after(0, lambda: messagebox.showerror("抓取失敗", f"錯誤訊息：\n{err_msg}"))
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
            # Mac 不需要 creationflags
            kwargs = {}
            if self.system == "Windows":
                kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW

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