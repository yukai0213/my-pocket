# -*- coding: utf-8 -*-
from plugin_manager import BasePlugin

class ExampleCustomPlugin(BasePlugin):
    """
    範例：針對特定網站 (例如 example.com) 的外掛
    """
    priority = 10  # 優先級較高

    def match(self, url):
        # 只要網址含有 "example.com" 就觸發
        return "example.com" in url

    def get_js_script(self):
        # 這裡可以回傳針對 example.com 的特別 JS 檔案路徑
        # 或者直接回傳 None (如果不需 JS)
        return None

    def get_filename_prefix(self, url, title):
        # 強制在檔名加上前綴
        return "[Example]-"

    def get_custom_args(self):
        # 例如：遇到這個網站時，延遲載入時間設長一點
        return ["--load-deferred-images-max-idle-time=5000"]
