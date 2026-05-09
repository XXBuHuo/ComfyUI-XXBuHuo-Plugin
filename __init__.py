import os
import importlib

print("\n" + "=" * 40)
print("👏 欢迎使用 XXBuHuo 插件包")
NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}
WEB_DIRECTORY = "./web"
current_dir = os.path.dirname(os.path.abspath(__file__))
for filename in os.listdir(current_dir):
    if filename.endswith(".py") and filename != "__init__.py":
        module_name = filename[:-3]
        try:
            module = importlib.import_module(f".{module_name}", package=__name__)
            if hasattr(module, "NODE_CLASS_MAPPINGS"):
                NODE_CLASS_MAPPINGS.update(module.NODE_CLASS_MAPPINGS)
            if hasattr(module, "NODE_DISPLAY_NAME_MAPPINGS"):
                NODE_DISPLAY_NAME_MAPPINGS.update(module.NODE_DISPLAY_NAME_MAPPINGS)
            print(f"  [+] 成功加载: {module_name}")
        except Exception as e:
            print(f"  [!] 加载 {module_name} 失败, 错误: {e}")
print("✅ XXBuHuo 插件包加载完毕！")
print("=" * 40 + "\n")
__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', 'WEB_DIRECTORY']