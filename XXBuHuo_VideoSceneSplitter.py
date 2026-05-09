import torch
import cv2
import numpy as np
import os
import folder_paths
import datetime
from PIL import Image
import subprocess
import concurrent.futures

try:
    from scenedetect import detect, ContentDetector

    SCENEDETECT_AVAILABLE = True
except ImportError:
    SCENEDETECT_AVAILABLE = False


class AnyType(str):
    def __ne__(self, __value: object) -> bool:
        return False


ANY = AnyType("*")


class XXBuHuo_VideoSceneSplitter:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "video_data": (ANY, {
                    "tooltip": "【视频输入源】\n支持连接视频路径对象，或直接连接图像批次。"
                }),
                "threshold": ("FLOAT", {
                    "default": 0.27, "min": 0.01, "max": 1.0, "step": 0.01,
                    "tooltip": "【切镜敏感度】\n推荐：0.27 (影视级标准)。数值越小，越容易切分微小的镜头变化。"
                }),
                "min_scene_frames": ("INT", {
                    "default": 3, "min": 1, "max": 120, "step": 1,
                    "tooltip": "【分镜防抖】\n推荐：3。防闪光灯误切。"
                }),
                "search_window": ("INT", {
                    "default": 10, "min": 1, "max": 30, "step": 1,
                    "tooltip": "【绝对清晰度寻优】\n推荐：10。系统会扫描每个分镜开头的这几帧，并强制选出物理锐度最高的一张，彻底告别模糊！"
                }),
                "save_video_dir": ("STRING", {
                    "default": "开启",
                    "tooltip": "【视频切片保存路径 (带声音)】\n填 '开启' 保存在 output/Scene/video 下。\n填 '关闭' 则不保存。\n也可直接填入你的绝对路径。"
                }),
                "save_image_dir": ("STRING", {
                    "default": "开启",
                    "tooltip": "【清晰首帧保存路径】\n填 '开启' 保存在 output/Scene/image 下。\n填 '关闭' 则不保存。\n也可直接填入你的绝对路径。"
                }),
            },
        }

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("first_frames", "scene_info")
    FUNCTION = "detect_and_split"
    CATEGORY = "XXBuHuo/Video"

    def _get_sharpness_tensor(self, tensor_img):
        gray = (0.299 * tensor_img[..., 0] + 0.587 * tensor_img[..., 1] + 0.114 * tensor_img[..., 2])
        gray_np = (gray.cpu().numpy() * 255).astype(np.uint8)
        return cv2.Laplacian(gray_np, cv2.CV_64F).var()

    def detect_and_split(self, video_data, threshold, min_scene_frames, search_window, save_video_dir, save_image_dir):
        if not SCENEDETECT_AVAILABLE:
            raise ImportError("【致命错误】未安装 scenedetect 库！请打开终端运行: pip install scenedetect")
        save_video_flag = save_video_dir.strip() != "关闭"
        save_image_flag = save_image_dir.strip() != "关闭"
        output_dir = folder_paths.get_output_directory()
        actual_vid_dir = ""
        actual_img_dir = ""
        if save_video_flag:
            val = save_video_dir.strip().strip('"').strip("'")
            if val == "开启" or val.lower() == "default":
                actual_vid_dir = os.path.join(output_dir, "Scene", "video")
            else:
                actual_vid_dir = val
            os.makedirs(actual_vid_dir, exist_ok=True)
        if save_image_flag:
            val = save_image_dir.strip().strip('"').strip("'")
            if val == "开启" or val.lower() == "default":
                actual_img_dir = os.path.join(output_dir, "Scene", "image")
            else:
                actual_img_dir = val
            os.makedirs(actual_img_dir, exist_ok=True)
        time_prefix = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        vid_name = "VideoClip"
        sub_kwargs = {}
        if os.name == 'nt':
            sub_kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW

        def convert_to_tensor(frame_bgr):
            frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            return torch.from_numpy(frame_rgb.astype(np.float32) / 255.0)

        video_path = None
        first_frames = []
        final_indices = []
        scene_list = []
        if not isinstance(video_data, torch.Tensor):
            if isinstance(video_data, str):
                video_path = video_data
            elif isinstance(video_data, (list, tuple)) and len(video_data) > 0 and isinstance(video_data[0], str):
                video_path = video_data[0]
            elif isinstance(video_data, dict):
                for val in video_data.values():
                    if isinstance(val, str) and val.lower().endswith(
                        ('.mp4', '.mov', '.webm', '.avi', '.mkv')): video_path = val; break
            else:
                for attr in ['path', 'video_path', 'file_path', 'filepath', 'url']:
                    if hasattr(video_data, attr):
                        val = getattr(video_data, attr)
                        if isinstance(val, str): video_path = val; break
                if video_path is None:
                    try:
                        for attr in dir(video_data):
                            if not attr.startswith('__'):
                                val = getattr(video_data, attr)
                                if isinstance(val, str) and val.lower().endswith(
                                    ('.mp4', '.mov', '.webm', '.avi', '.mkv')): video_path = val; break
                    except:
                        pass
            if video_path:
                video_path = str(video_path).strip('"').strip("'")
                if not os.path.exists(video_path):
                    input_dir = folder_paths.get_input_directory()
                    test_path = os.path.join(input_dir, video_path)
                    if os.path.exists(test_path):
                        video_path = test_path
                    else:
                        video_path = os.path.join(input_dir, os.path.basename(video_path))
                vid_name = os.path.splitext(os.path.basename(video_path))[0]
                sd_threshold = threshold * 100.0
                scene_list = detect(video_path, ContentDetector(threshold=sd_threshold, min_scene_len=min_scene_frames))
                if not scene_list:
                    raise ValueError("XXBuHuo: 未检测到任何切镜，请降低 threshold 参数。")
                cap = cv2.VideoCapture(video_path)
                for i, scene in enumerate(scene_list):
                    start_f = scene[0].get_frames()
                    end_f = scene[1].get_frames()
                    limit = min(start_f + search_window, end_f)
                    cap.set(cv2.CAP_PROP_POS_FRAMES, start_f)
                    best_score = -1
                    best_frame = None
                    best_idx = start_f
                    for j in range(start_f, limit):
                        ret, frame = cap.read()
                        if not ret: break
                        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                        score = cv2.Laplacian(gray, cv2.CV_64F).var()
                        if score > best_score:
                            best_score = score
                            best_frame = frame.copy()
                            best_idx = j
                    if best_frame is not None:
                        first_frames.append(convert_to_tensor(best_frame))
                        final_indices.append(best_idx)
                cap.release()
        if not video_path and isinstance(video_data, torch.Tensor):
            B = len(video_data)
            if B <= 1: return (video_data, "输入仅1帧")
            diffs = torch.mean(torch.abs(video_data[1:] - video_data[:-1]), dim=(1, 2, 3))
            raw_cuts = [0]
            last_cut = 0
            for i in range(len(diffs)):
                if diffs[i].item() > threshold:
                    cut_idx = i + 1
                    if (cut_idx - last_cut) >= min_scene_frames:
                        raw_cuts.append(cut_idx)
                        last_cut = cut_idx
            bounds = raw_cuts + [B]
            for i in range(len(raw_cuts)):
                start_f = raw_cuts[i]
                limit = min(start_f + search_window, bounds[i + 1])
                best_score = -1
                best_idx = start_f
                for j in range(start_f, limit):
                    score = self._get_sharpness_tensor(video_data[j])
                    if score > best_score:
                        best_score = score
                        best_idx = j
                first_frames.append(video_data[best_idx])
                final_indices.append(best_idx)
        if not first_frames:
            raise ValueError("XXBuHuo: 提取失败，有效帧数为 0。")
        if save_image_flag:
            for i, (idx, tensor_img) in enumerate(zip(final_indices, first_frames)):
                img_np = (tensor_img.cpu().numpy() * 255).astype(np.uint8)
                Image.fromarray(img_np).save(
                    os.path.join(actual_img_dir, f"{vid_name}_{time_prefix}_scene_{i:04d}_frame_{idx:05d}.png"))
        if save_video_flag:
            if video_path and scene_list:
                def _cut_video_task(args):
                    start_sec, duration, out_vid, v_path = args
                    cmd = [
                        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                        "-ss", str(start_sec),
                        "-i", v_path,
                        "-t", str(duration),
                        "-c:v", "libx264", "-preset", "superfast", "-crf", "18",
                        "-c:a", "aac",
                        out_vid
                    ]
                    subprocess.run(cmd, check=True, **sub_kwargs)

                cut_args = []
                for i, scene in enumerate(scene_list):
                    start_sec = scene[0].get_seconds()
                    end_sec = scene[1].get_seconds()
                    duration = end_sec - start_sec
                    out_vid = os.path.join(actual_vid_dir, f"{vid_name}_{time_prefix}_scene_{i:04d}.mp4")
                    cut_args.append((start_sec, duration, out_vid, video_path))
                if cut_args:
                    max_workers = min(8, (os.cpu_count() or 4))
                    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                        list(executor.map(_cut_video_task, cut_args))
            elif isinstance(video_data, torch.Tensor):
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                height, width = video_data.shape[1:3]
                for i in range(len(raw_cuts)):
                    start_f = raw_cuts[i]
                    end_f = bounds[i + 1]
                    out_path = os.path.join(actual_vid_dir, f"Tensor_{time_prefix}_scene_{i:04d}.mp4")
                    out = cv2.VideoWriter(out_path, fourcc, 24.0, (int(width), int(height)))
                    for j in range(start_f, end_f):
                        frame_np = (video_data[j].cpu().numpy() * 255).astype(np.uint8)
                        out.write(cv2.cvtColor(frame_np, cv2.COLOR_RGB2BGR))
                    out.release()
        out_tensor = torch.stack(first_frames)
        info = (
            f"提取独立分镜: {len(final_indices)} 段\n"
            f"首帧确切索引: {final_indices}"
        )
        return (out_tensor, info)


NODE_CLASS_MAPPINGS = {
    "XXBuHuo_VideoSceneSplitter": XXBuHuo_VideoSceneSplitter
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "XXBuHuo_VideoSceneSplitter": "🎞️ XXBuHuo 视频分割首帧提取"
}
