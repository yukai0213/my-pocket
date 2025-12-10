# -*- coding: utf-8 -*-
from plugin_manager import BasePlugin
import os

class DefaultPlugin(BasePlugin):
    """
    預設外掛：處理所有未被其他外掛攔截的 URL。
    繼承了原本 ArchiverApp 的邏輯 (local_fix.js)。
    """
    priority = 999  # 最低優先級，最後才被選中

    def match(self, url):
        # 永遠回傳 True，作為 Fallback
        return True

    def get_js_script(self):
        # 回傳專案根目錄下的 local_fix.js
        # 注意：我們假設這個檔案在 CWD
        if os.path.exists("local_fix.js"):
            return "local_fix.js"
        return None

    def get_filename_prefix(self, url, title):
        return ""
