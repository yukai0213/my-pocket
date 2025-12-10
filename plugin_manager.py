# -*- coding: utf-8 -*-
import os
import importlib.util
import inspect

class BasePlugin:
    """
    所有外掛的基礎類別。
    自訂外掛必須繼承此類別並實作相關方法。
    """
    priority = 100  # 優先級，越小越優先檢查 match

    def match(self, url):
        """
        判斷此外掛是否應該處理該 URL。
        :param url: 目標網址
        :return: True/False
        """
        return False

    def get_js_script(self):
        """
        回傳要注入的 JS 腳本路徑或是 JS 字串。
        預設回傳 None (不注入)。
        """
        return None

    def get_filename_prefix(self, url, title):
        """
        (選用) 回傳檔名修飾，例如 "[Youtube]-..."
        """
        return ""
    
    def get_custom_args(self):
        """
        (選用) 回傳額外的 single-file CLI 參數列表。
        """
        return []

class PluginManager:
    def __init__(self, plugin_dir="plugins"):
        self.plugin_dir = os.path.join(os.getcwd(), plugin_dir)
        self.plugins = []
        self._load_plugins()

    def _load_plugins(self):
        """
        載入 plugin_dir 下所有的 .py 檔，並尋找繼承 BasePlugin 的類別。
        """
        self.plugins = []
        
        # 確保 plugin 資料夾存在
        if not os.path.exists(self.plugin_dir):
            try:
                os.makedirs(self.plugin_dir)
                # 建立 __init__.py 讓其成為 package
                with open(os.path.join(self.plugin_dir, "__init__.py"), "w") as f:
                    pass
            except Exception as e:
                print(f"Error creating plugin dir: {e}")
                return

        # 遍歷資料夾
        for filename in os.listdir(self.plugin_dir):
            if filename.endswith(".py") and not filename.startswith("__"):
                self._load_plugin_file(filename)

        # 根據優先級排序 (數字小優先)
        self.plugins.sort(key=lambda x: x.priority)
        print(f"Loaded {len(self.plugins)} plugins.")

    def _load_plugin_file(self, filename):
        module_name = filename[:-3]
        file_path = os.path.join(self.plugin_dir, filename)
        
        try:
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # 尋找模組中的 Plugin 類別
                for name, obj in inspect.getmembers(module):
                    if inspect.isclass(obj) and issubclass(obj, BasePlugin) and obj is not BasePlugin:
                        print(f"Discover plugin: {name} from {filename}")
                        self.plugins.append(obj())
        except Exception as e:
            print(f"Failed to load plugin {filename}: {e}")

    def get_handler(self, url):
        """
        根據 URL 找到第一個 match 的 plugin。
        若無，則回傳 None (外部應使用預設邏輯)。
        """
        for plugin in self.plugins:
            if plugin.match(url):
                print(f"URL matched with plugin: {plugin.__class__.__name__}")
                return plugin
        return None
