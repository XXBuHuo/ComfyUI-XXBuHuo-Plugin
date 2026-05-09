import os
import shutil
import folder_paths


class XXBuHuo_Downloader:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "repo_id": ("STRING", {
                    "default": "Qwen/Qwen2.5-1.5B-Instruct",
                    "multiline": False,
                    "tooltip": "模型仓库ID。例如: 'Qwen/Qwen2.5-7B'。请确保 ID 与所选下载源匹配。"
                }),
                "source": (["HuggingFace_Official", "HuggingFace_Mirror", "ModelScope"], {
                    "default": "HuggingFace_Mirror",
                    "tooltip": "【下载源】\n1. Official: 官网直连。\n2. Mirror: 国内镜像(hf-mirror)。\n3. ModelScope: 阿里魔搭(推荐)。"
                }),
                "target_folder_name": ("STRING", {
                    "default": "LLM/Qwen2.5-1.5B",
                    "multiline": False,
                    "tooltip": "存储路径。模型将保存在 ComfyUI/models/ 目录下指定的文件夹内。"
                }),
                "max_workers": ("INT", {
                    "default": 8,
                    "min": 1,
                    "max": 64,
                    "step": 1,
                    "tooltip": "并发线程数。建议 4-16，数值过高容易被服务器限制IP速度。"
                }),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("local_model_path",)
    FUNCTION = "download_model"
    CATEGORY = "XXBuHuo/Downloads"

    def download_model(self, repo_id, source, target_folder_name, max_workers=8):
        repo_id = repo_id.strip()
        target_folder_name = target_folder_name.strip()
        base_models_dir = folder_paths.models_dir
        target_path = os.path.join(base_models_dir, target_folder_name)
        os.makedirs(target_path, exist_ok=True)
        if self.migrate_cached_model(repo_id, target_path):
            print(f"[XXBuHuo-Downloads] 本地缓存完成迁移。")
            return (target_path,)
        if source == "ModelScope":
            try:
                from modelscope import snapshot_download
                print(f"[XXBuHuo-Downloads] ModelScope 下载...")
                snapshot_download(repo_id, local_dir=target_path)
            except ImportError:
                raise ImportError("缺失组件: 请运行 pip install modelscope")
        else:
            if source == "HuggingFace_Mirror":
                os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
                print(f"[XXBuHuo-Downloads] 国内镜像站(hf-mirror)下载...")
            else:
                os.environ.pop("HF_ENDPOINT", None)
                print(f"[XXBuHuo-Downloads] HuggingFace 官方源下载...")
            os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"
            try:
                from huggingface_hub import snapshot_download
                print(f"[XXBuHuo-Downloads] 断点续传...")
                snapshot_download(
                    repo_id=repo_id,
                    local_dir=target_path,
                    max_workers=max_workers,
                    resume_download=True,
                    local_dir_use_symlinks=False,
                    endpoint="https://hf-mirror.com" if source == "HuggingFace_Mirror" else None,
                    etag_timeout=30
                )
            except Exception as e:
                print(f"[XXBuHuo-Downloads] 下载或校验过程出错: {e}")
                raise e
        self.cleanup_residual_files(target_path)
        print(f"\n[XXBuHuo-Downloads] 任务完成: {target_path}")
        return (target_path,)

    def cleanup_residual_files(self, target_path: str):
        residuals = [".msc", "._____temp", "__pycache__"]
        if os.path.exists(target_path):
            for item in os.listdir(target_path):
                path = os.path.join(target_path, item)
                if item in residuals or item.endswith(".downloading"):
                    try:
                        if os.path.isdir(path):
                            shutil.rmtree(path)
                        else:
                            os.remove(path)
                    except:
                        pass
                if item.endswith(".parts"):
                    try:
                        shutil.rmtree(path)
                    except:
                        pass

    def migrate_cached_model(self, repo_id: str, target_path: str) -> bool:
        hf_cache = os.path.join(os.path.expanduser("~"), ".cache", "huggingface", "hub")
        hf_model_dir = os.path.join(hf_cache, f"models--{repo_id.replace('/', '--')}")
        if os.path.exists(hf_model_dir):
            snapshots_dir = os.path.join(hf_model_dir, "snapshots")
            if os.path.exists(snapshots_dir):
                snapshots = os.listdir(snapshots_dir)
                if snapshots:
                    source = os.path.join(snapshots_dir, snapshots[0])
                    print(f"[XXBuHuo-Downloads] 缓存迁移...")
                    shutil.copytree(source, target_path, dirs_exist_ok=True)
                    return True
        ms_cache = os.path.join(os.path.expanduser("~"), ".cache", "modelscope", "hub")
        ms_model_dir = os.path.join(ms_cache, repo_id)
        if os.path.exists(ms_model_dir):
            print(f"[XXBuHuo-Downloads] 缓存迁移...")
            shutil.copytree(ms_model_dir, target_path, dirs_exist_ok=True)
            return True
        return False


NODE_CLASS_MAPPINGS = {
    "XXBuHuo_Downloader": XXBuHuo_Downloader
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "XXBuHuo_Downloader": "XXBuHuo Downloader"
}
