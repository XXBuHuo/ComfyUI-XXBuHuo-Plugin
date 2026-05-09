import os
import torch
import numpy as np
from PIL import Image, ImageOps
import folder_paths
import json
import base64
import urllib.request
from io import BytesIO
import logging
import traceback
import multiprocessing
import gc
import re
import glob
import requests
import random
import io
import string
import comfy.model_management as mm
import comfy.utils
from concurrent.futures import ThreadPoolExecutor
import torch.nn.functional as F
import shutil
import uuid
import cv2

HAS_DECORD = False
try:
    import decord

    decord.bridge.set_bridge('torch')
    HAS_DECORD = True
except ImportError:
    pass
logger = logging.getLogger(__name__)


class AnyType(str):
    def __ne__(self, __value: object) -> bool:
        return False


ANY = AnyType("*")
base_models_dir = folder_paths.models_dir
XXBUHUO_LLAMA_DIR = os.path.join(base_models_dir, "XXBuHuo", "llama")
XXBUHUO_MMPROJ_DIR = os.path.join(base_models_dir, "XXBuHuo", "mmproj")
XXBUHUO_INSIGHTFACE_DIR = os.path.join(base_models_dir, "XXBuHuo", "insightface")
XXBUHUO_PRESETS_DIR = os.path.join(base_models_dir, "XXBuHuo", "presets")
os.makedirs(XXBUHUO_PRESETS_DIR, exist_ok=True)
XXBUHUO_ENHANCERS_DIR = os.path.join(base_models_dir, "XXBuHuo", "enhancers")
os.makedirs(XXBUHUO_ENHANCERS_DIR, exist_ok=True)
XXBUHUO_ENDPOINTS_DIR = os.path.join(base_models_dir, "XXBuHuo", "endpoints")
os.makedirs(XXBUHUO_ENDPOINTS_DIR, exist_ok=True)
API_ENDPOINTS = []
if os.path.exists(XXBUHUO_ENDPOINTS_DIR):
    for f in os.listdir(XXBUHUO_ENDPOINTS_DIR):
        if f.endswith(".json"):
            try:
                with open(os.path.join(XXBUHUO_ENDPOINTS_DIR, f), "r", encoding="utf-8") as fp:
                    data = json.load(fp)
                    if isinstance(data, dict):
                        API_ENDPOINTS.extend([str(v) for v in data.values() if isinstance(v, str)])
                    elif isinstance(data, list):
                        API_ENDPOINTS.extend([str(v) for v in data if isinstance(v, str)])
            except Exception as e:
                logger.error(f"[XXBuHuo] API接口文件 {f} 加载失败: {e}")
FINAL_ENDPOINTS_STR = "|||".join(list(set(API_ENDPOINTS)))
PRESET_PROMPTS = {}
ENHANCER_PROMPTS = {}
if os.path.exists(XXBUHUO_ENHANCERS_DIR):
    for f in os.listdir(XXBUHUO_ENHANCERS_DIR):
        if f.endswith(".json"):
            try:
                with open(os.path.join(XXBUHUO_ENHANCERS_DIR, f), "r", encoding="utf-8") as fp:
                    data = json.load(fp)
                    if isinstance(data, dict):
                        ENHANCER_PROMPTS.update(data)
            except Exception as e:
                logger.error(f"[XXBuHuo] 增强器文件 {f} 加载失败: {e}")
if os.path.exists(XXBUHUO_PRESETS_DIR):
    for f in os.listdir(XXBUHUO_PRESETS_DIR):
        if f.endswith(".json"):
            try:
                with open(os.path.join(XXBUHUO_PRESETS_DIR, f), "r", encoding="utf-8") as fp:
                    data = json.load(fp)
                    if isinstance(data, dict):
                        PRESET_PROMPTS.update(data)
            except Exception as e:
                logger.error(f"[XXBuHuo] 预设文件 {f} 加载失败: {e}")
for d in [XXBUHUO_LLAMA_DIR, XXBUHUO_MMPROJ_DIR, XXBUHUO_INSIGHTFACE_DIR]:
    os.makedirs(d, exist_ok=True)
folder_paths.folder_names_and_paths["xxbuhuo_llama"] = ([XXBUHUO_LLAMA_DIR], set([".gguf"]))
folder_paths.folder_names_and_paths["xxbuhuo_mmproj"] = ([XXBUHUO_MMPROJ_DIR], set([".gguf"]))
HAS_LLAMA = False
GGML_Q4_0, GGML_Q4_1, GGML_Q5_0, GGML_Q5_1, GGML_Q8_0 = 2, 3, 4, 5, 8
try:
    from llama_cpp import Llama

    HAS_LLAMA = True
    try:
        from llama_cpp import GGML_TYPE_Q4_0, GGML_TYPE_Q4_1, GGML_TYPE_Q5_0, GGML_TYPE_Q5_1, GGML_TYPE_Q8_0

        GGML_Q4_0, GGML_Q4_1, GGML_Q5_0, GGML_Q5_1, GGML_Q8_0 = GGML_TYPE_Q4_0, GGML_TYPE_Q4_1, GGML_TYPE_Q5_0, GGML_TYPE_Q5_1, GGML_TYPE_Q8_0
    except:
        pass
except:
    pass


def align_to_divisible(value: int, divisible_by: int) -> int:
    if divisible_by <= 0: return value
    return max(divisible_by, int(value) // divisible_by * divisible_by)


def get_available_cuda_devices() -> list:
    devices = []
    if torch.cuda.is_available():
        for i in range(torch.cuda.device_count()): devices.append(i)
    return devices


def load_image_with_orientation(path):
    try:
        img = Image.open(path)
        img = ImageOps.exif_transpose(img)
        return img.convert('RGB')
    except Exception as e:
        logger.warning(f"[XXBuHuo] 图片加载异常，回退默认加载: {e}")
        return Image.open(path).convert('RGB')


class OmniModelCache:
    def __init__(self):
        self.cache = {}
        self.current_key = None
        self.messages = {}
        self.sys_prompts = {}
        self.node_seed_states = {}

    def get(self, key):
        return self.cache.get(key, None)

    def get_messages(self, uid):
        return self.messages.get(uid, [])

    def set_messages(self, uid, messages):
        self.messages[uid] = messages

    def get_sys_prompt(self, uid):
        return self.sys_prompts.get(uid, None)

    def set_sys_prompt(self, uid, prompt):
        self.sys_prompts[uid] = prompt

    def get_node_seed(self, node_uid: int, input_seed: int) -> int:
        if node_uid not in self.node_seed_states:
            self.node_seed_states[node_uid] = input_seed if input_seed != -1 else 0
        else:
            self.node_seed_states[node_uid] += 1
        return self.node_seed_states[node_uid]

    def reset_node_seed(self, node_uid: int):
        if node_uid in self.node_seed_states: del self.node_seed_states[node_uid]

    def set(self, key, model):
        if self.current_key != key: self.clear()
        self.cache[key] = model
        self.current_key = key

    def clear(self):
        has_llm = bool(self.cache)
        has_face = "_FACE_DETECTOR_CACHE" in globals() and bool(globals()["_FACE_DETECTOR_CACHE"])
        if not has_llm and not has_face:
            return
        print("[XXBuHuo] 内存清理...")
        if self.cache:
            for k, v in list(self.cache.items()):
                if isinstance(v, dict) and "llm" in v and v["llm"] is not None:
                    llm_obj = v["llm"]
                    try:
                        if hasattr(llm_obj, "chat_handler") and llm_obj.chat_handler is not None:
                            handler = llm_obj.chat_handler
                            if hasattr(handler, "__del__"):
                                try:
                                    handler.__del__()
                                except:
                                    pass
                            llm_obj.chat_handler = None
                            del handler
                        if hasattr(llm_obj, "close"):
                            llm_obj.close()
                        if hasattr(llm_obj, "__del__"):
                            try:
                                llm_obj.__del__()
                            except:
                                pass
                    except Exception as e:
                        print(f"[XXBuHuo] 显存释放异常: {e}")
                    v["llm"] = None
                    del llm_obj
                if isinstance(v, dict): v.clear()
            self.cache.clear()
        if "_FACE_DETECTOR_CACHE" in globals() and globals()["_FACE_DETECTOR_CACHE"]:
            for k, v in list(globals()["_FACE_DETECTOR_CACHE"].items()):
                if isinstance(v, dict) and "app" in v and v["app"] is not None:
                    app_obj = v["app"]
                    try:
                        if hasattr(app_obj, "models"):
                            for model_name in list(app_obj.models.keys()):
                                sess = app_obj.models[model_name]
                                if hasattr(sess, "__del__"):
                                    try:
                                        sess.__del__()
                                    except:
                                        pass
                                app_obj.models[model_name] = None
                            app_obj.models.clear()
                    except:
                        pass
                    v["app"] = None
                    del app_obj
                if isinstance(v, dict): v.clear()
            globals()["_FACE_DETECTOR_CACHE"].clear()
        self.current_key = None
        self.messages.clear()
        self.sys_prompts.clear()
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
        mm.soft_empty_cache()
        print("[XXBuHuo] 显存释放已完成。")


_GLOBAL_OMNI_CACHE = OmniModelCache()
if not hasattr(mm, "_xxbuhuo_unload_hook_installed"):
    original_unload = getattr(mm, "unload_all_models", None)
    if original_unload is not None and callable(original_unload):
        def wrapped_unload_all_models(*args, **kwargs):
            try:
                _GLOBAL_OMNI_CACHE.clear()
            except:
                pass
            return original_unload(*args, **kwargs)


        mm.unload_all_models = wrapped_unload_all_models
        mm._xxbuhuo_unload_hook_installed = True


def extract_video_frames(video_path, max_frames):
    images = []
    try:
        if HAS_DECORD:
            vr = decord.VideoReader(video_path, ctx=decord.cpu(0))
            total_frames = len(vr)
            if total_frames > 0:
                if max_frames == -1 or max_frames >= total_frames:
                    indices = np.arange(total_frames)
                else:
                    indices = np.linspace(0, total_frames - 1, max_frames, dtype=int)
                raw_batch = vr.get_batch(indices).asnumpy()
                batch_tensors = torch.from_numpy(raw_batch).float() / 255.0
                images = [batch_tensors[i] for i in range(batch_tensors.shape[0])]
        else:
            cap = cv2.VideoCapture(video_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            if total_frames > 0:
                frames_np = []
                if max_frames == -1 or max_frames >= total_frames:
                    while True:
                        ret, frame = cap.read()
                        if not ret: break
                        frames_np.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                else:
                    indices = np.linspace(0, total_frames - 1, max_frames, dtype=int)
                    if max_frames > (total_frames / 4):
                        current_frame = 0
                        idx_set = set(indices)
                        while current_frame <= indices[-1]:
                            ret, frame = cap.read()
                            if not ret: break
                            if current_frame in idx_set:
                                frames_np.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                            current_frame += 1
                    else:
                        for idx in indices:
                            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
                            ret, frame = cap.read()
                            if ret: frames_np.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                if frames_np:
                    stacked_np = np.stack(frames_np)
                    batch_tensors = torch.from_numpy(stacked_np).float() / 255.0
                    images = [batch_tensors[i] for i in range(batch_tensors.shape[0])]
            cap.release()
    except Exception as e:
        logger.error(f"[XXBuHuo] 视频抽帧崩溃: {e}")
    return images


def parse_any_media_to_descriptors(obj, depth=0):
    if depth > 3: return []
    descriptors = []

    def check_and_add_path(p):
        if isinstance(p, str) and os.path.exists(p):
            if p.lower().endswith(('.mp4', '.mov', '.webm', '.avi', '.mkv', '.gif')):
                descriptors.append({"type": "video_path", "path": p})
            else:
                descriptors.append({"type": "image_path", "path": p})
            return True
        return False

    if isinstance(obj, torch.Tensor):
        descriptors.append({"type": "tensor", "data": obj})
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            descriptors.extend(parse_any_media_to_descriptors(item, depth + 1))
    elif isinstance(obj, str):
        if not check_and_add_path(obj):
            try:
                full_path = folder_paths.get_annotated_filepath(obj)
                check_and_add_path(full_path)
            except:
                pass
    else:
        path_found = False
        for attr in ["video_path", "path", "filepath", "file_path", "url"]:
            if hasattr(obj, attr):
                if check_and_add_path(getattr(obj, attr)):
                    path_found = True
                    break
        if not path_found:
            for method in ["get_path", "get_file", "get_video"]:
                if hasattr(obj, method) and callable(getattr(obj, method)):
                    try:
                        if check_and_add_path(getattr(obj, method)()):
                            path_found = True
                            break
                    except:
                        pass
        if not path_found and hasattr(obj, "__dict__"):
            for k, v in vars(obj).items():
                if check_and_add_path(v):
                    path_found = True
                    break
        if not path_found:
            tensor_found = False
            for attr in ["tensor", "frames", "image", "images", "video", "data"]:
                if hasattr(obj, attr):
                    val = getattr(obj, attr)
                    if isinstance(val, torch.Tensor):
                        descriptors.append({"type": "tensor", "data": val})
                        tensor_found = True
            if not tensor_found and hasattr(obj, "__dict__"):
                for k, v in vars(obj).items():
                    if isinstance(v, torch.Tensor):
                        descriptors.append({"type": "tensor", "data": v})
    return descriptors


def _重置llm推理状态(llm, vision_type) -> None:
    if vision_type not in ["Qwen3.5-VL", "Qwen3.6-VL"]: return
    try:
        llm.n_tokens = 0
    except:
        pass
    try:
        ctx = getattr(llm, "_ctx", None)
        if ctx is not None and hasattr(ctx, "memory_clear"): ctx.memory_clear(True)
        hybrid_cache_mgr = getattr(llm, "_hybrid_cache_mgr", None)
        if hybrid_cache_mgr is not None and hasattr(hybrid_cache_mgr, "clear"): hybrid_cache_mgr.clear()
        batch = getattr(llm, "_batch", None)
        if batch is not None and hasattr(batch, "reset"): batch.reset()
    except:
        pass


def tensor_to_base64_smart(tensor: torch.Tensor, max_size=1024, quality=95) -> str:
    try:
        max_size = int(max_size)
        if max_size < 256: max_size = 1024
        numpy_image = (tensor.cpu().numpy() * 255).astype("uint8")
        pil_image = Image.fromarray(numpy_image).convert('RGB')
        if max(pil_image.size) > max_size:
            ratio = max_size / max(pil_image.size)
            new_size = (int(pil_image.size[0] * ratio), int(pil_image.size[1] * ratio))
            pil_image = pil_image.resize(new_size, Image.Resampling.LANCZOS)
        buffered = BytesIO()
        pil_image.save(buffered, format="PNG")
        return f"data:image/png;base64,{base64.b64encode(buffered.getvalue()).decode('utf-8')}"
    except:
        return ""


def batch_tensors_to_base64(images_list, max_size):
    if not images_list: return []
    with ThreadPoolExecutor(max_workers=min(8, len(images_list))) as executor:
        return list(executor.map(lambda img: tensor_to_base64_smart(img, max_size), images_list))


def split_grid_image(image_tensor, rows=3, cols=3):
    try:
        h, w = image_tensor.shape[0], image_tensor.shape[1]
        cell_h, cell_w = h // rows, w // cols
        cells = []
        for i in range(rows):
            for j in range(cols):
                cells.append(image_tensor[i * cell_h:(i + 1) * cell_h, j * cell_w:(j + 1) * cell_w, :])
        return cells
    except:
        return [image_tensor]


def load_images_from_folder(folder_path):
    images = []
    if not os.path.exists(folder_path): return images
    for ext in ['*.jpg', '*.jpeg', '*.png', '*.webp']:
        for img_path in glob.glob(os.path.join(folder_path, ext)):
            try:
                img = load_image_with_orientation(img_path)
                images.append(torch.from_numpy(np.array(img)).float() / 255.0)
            except:
                pass
    return images


_FACE_DETECTOR_CACHE = {}
HAS_INSIGHTFACE = False
try:
    import insightface

    HAS_INSIGHTFACE = True
except ImportError:
    pass


def get_face_detector(device):
    device_str = str(device)
    if device_str not in _FACE_DETECTOR_CACHE:
        if HAS_INSIGHTFACE:
            import warnings
            warnings.filterwarnings("ignore", category=FutureWarning, module="insightface")
            from insightface.app import FaceAnalysis
            root_dir = XXBUHUO_INSIGHTFACE_DIR
            providers = ['CUDAExecutionProvider'] if 'cuda' in device_str else ['CPUExecutionProvider']
            app = FaceAnalysis(name='buffalo_l', root=root_dir, providers=providers, allowed_modules=['detection'])
            app.prepare(ctx_id=0 if 'cuda' in device_str else -1, det_size=(640, 640))
            _FACE_DETECTOR_CACHE[device_str] = {"type": "insightface", "app": app}
            print(f"[XXBuHuo] InsightFace 已加载 | 模型目录: {root_dir}")
        else:
            from facenet_pytorch import MTCNN
            _FACE_DETECTOR_CACHE[device_str] = {"type": "mtcnn", "app": MTCNN(keep_all=False, device=device)}
            print("[XXBuHuo] 未检测到 insightface 库。")
    return _FACE_DETECTOR_CACHE[device_str]


def unified_face_detect(detector_info, img_np):
    if detector_info["type"] == "insightface":
        app = detector_info["app"]
        img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
        faces = app.get(img_bgr)
        if not faces: return None, None, None
        face = faces[0]
        return np.array([face.bbox]), np.array([face.det_score]), np.array([face.kps])
    else:
        mtcnn = detector_info["app"]
        return mtcnn.detect(img_np, landmarks=True)


def process_resize_image_single(image_tensor, width, height, method, keep_proportion, crop_position, swap,
                                divisible_by=2, smooth_state=None, precomputed_face=None):
    try:
        if swap: width, height = height, width
        orig_input_w = int(width)
        orig_input_h = int(height)
        orig_h, orig_w = image_tensor.shape[0], image_tensor.shape[1]
        orig_ratio = orig_w / orig_h
        temp_target_w = orig_input_w if orig_input_w > 0 else orig_w
        temp_target_h = orig_input_h if orig_input_h > 0 else orig_h
        base_target_width = align_to_divisible(temp_target_w, divisible_by)
        base_target_height = align_to_divisible(temp_target_h, divisible_by)
        base_target_total_pixels = base_target_width * base_target_height
        if orig_w == base_target_width and orig_h == base_target_height and keep_proportion in ["stretch", "resize",
                                                                                                "filter", "pad"]:
            return image_tensor
        processed_tensor = image_tensor.unsqueeze(0)
        final_width, final_height = base_target_width, base_target_height
        need_final_resize = True
        if crop_position in ["face", "head"] and keep_proportion == "crop":
            is_dynamic_size = (orig_input_w == 0 or orig_input_h == 0)
            cx, cy = orig_w // 2, orig_h // 2
            face_found = False
            fx, fy, fw, fh = 0, 0, 0, 0
            angle = 0.0
            try:
                if precomputed_face is not None:
                    boxes, probs, landmarks = precomputed_face
                else:
                    detector_info = get_face_detector(image_tensor.device)
                    img_np = (image_tensor.cpu().numpy() * 255).astype(np.uint8)
                    boxes, probs, landmarks = unified_face_detect(detector_info, img_np)
                if boxes is not None and len(boxes) > 0 and boxes[0] is not None:
                    box = boxes[0]
                    fx, fy = int(box[0]), int(box[1])
                    fx2, fy2 = int(box[2]), int(box[3])
                    fw, fh = fx2 - fx, fy2 - fy
                    face_found = True
                    if landmarks is not None and len(landmarks) > 0 and landmarks[0] is not None:
                        lm = landmarks[0]
                        l_eye, r_eye, nose, l_mouth, r_mouth = lm[0], lm[1], lm[2], lm[3], lm[4]
                        eye_dx = r_eye[0] - l_eye[0]
                        eye_dy = r_eye[1] - l_eye[1]
                        eye_dist = np.hypot(eye_dx, eye_dy)
                        yaw_ratio = eye_dist / max(fh, 1e-6)
                        cy = fy + fh // 2
                        if yaw_ratio > 0.20:
                            cx = fx + fw // 2
                            angle = np.degrees(np.arctan2(eye_dy, eye_dx))
                            fw = max(fw, int(fh * 0.80))
                            fx = cx - fw // 2
                        else:
                            real_fw = max(fw, int(fh * 0.90))
                            eyes_mid_x = (l_eye[0] + r_eye[0]) / 2.0
                            nose_x = nose[0]
                            safety_margin = int(real_fw * 0.18)
                            if nose_x > eyes_mid_x:
                                ideal_right = nose_x + safety_margin
                                cx = int(ideal_right - real_fw / 2.0)
                            else:
                                ideal_left = nose_x - safety_margin
                                cx = int(ideal_left + real_fw / 2.0)
                            fw = real_fw
                            fx = cx - fw // 2
                            mid_eye_x = (l_eye[0] + r_eye[0]) / 2.0
                            mid_eye_y = (l_eye[1] + r_eye[1]) / 2.0
                            mid_mouth_x = (l_mouth[0] + r_mouth[0]) / 2.0
                            mid_mouth_y = (l_mouth[1] + r_mouth[1]) / 2.0
                            face_dx = mid_mouth_x - mid_eye_x
                            face_dy = mid_mouth_y - mid_eye_y
                            angle = np.degrees(np.arctan2(face_dy, face_dx)) - 90.0
                            angle = angle * 0.8
                    else:
                        cx, cy = fx + fw // 2, fy + fh // 2
                        angle = 0.0
            except Exception as e:
                pass
            if smooth_state is not None:
                if face_found:
                    target_center = np.array([cx, cy], dtype=np.float32)
                    target_angle = angle
                    shot_cut_threshold = 0.1
                    smoothing_factor = 0.15
                    is_shot_cut = False
                    if smooth_state["prev_center"] is not None:
                        dist = np.linalg.norm(target_center - smooth_state["prev_center"])
                        if dist > (orig_w * shot_cut_threshold): is_shot_cut = True
                    if smooth_state["prev_center"] is None or is_shot_cut:
                        smooth_state["prev_center"] = target_center
                        smooth_state["prev_angle"] = target_angle
                    else:
                        alpha = smoothing_factor
                        smooth_state["prev_center"] = (1 - alpha) * smooth_state["prev_center"] + alpha * target_center
                        smooth_state["prev_angle"] = (1 - alpha) * smooth_state["prev_angle"] + alpha * target_angle
                    smooth_state["prev_box"] = [fw, fh]
                    cx, cy = int(smooth_state["prev_center"][0]), int(smooth_state["prev_center"][1])
                    angle = smooth_state["prev_angle"]
                    fw, fh = smooth_state["prev_box"]
                    fx, fy = cx - fw // 2, cy - fh // 2
                else:
                    if smooth_state["prev_center"] is not None:
                        cx, cy = int(smooth_state["prev_center"][0]), int(smooth_state["prev_center"][1])
                        angle = smooth_state["prev_angle"]
                        fw, fh = smooth_state["prev_box"]
                        fx, fy = cx - fw // 2, cy - fh // 2
                        face_found = True
            if crop_position == "face" and face_found and abs(angle) > 0.0:
                M = cv2.getRotationMatrix2D((float(cx), float(cy)), float(angle), 1.0)
                img_np_full = (processed_tensor[0].cpu().numpy() * 255).astype(np.uint8)
                warped = cv2.warpAffine(img_np_full, M, (orig_w, orig_h), flags=cv2.INTER_LINEAR,
                                        borderMode=cv2.BORDER_REPLICATE)
                processed_tensor = torch.from_numpy(warped).float().unsqueeze(0) / 255.0
            if is_dynamic_size and face_found:
                expand_pixels = divisible_by if divisible_by > 0 else 0
                if crop_position == "head":
                    top_m = int(fh * 0.65)
                    bot_m = int(fh * 0.15)
                    hor_m = int(fw * 0.35)
                else:
                    top_m = int(fh * 0.20)
                    bot_m = int(fh * 0.10)
                    hor_m = int(fw * 0.10)
                left = fx - hor_m - expand_pixels
                right = fx + fw + hor_m + expand_pixels
                top = fy - top_m - expand_pixels
                bottom = fy + fh + bot_m + expand_pixels
                pad_left, pad_top = max(0, -left), max(0, -top)
                pad_right, pad_bottom = max(0, right - orig_w), max(0, bottom - orig_h)
                c_left, c_top = max(0, left), max(0, top)
                c_right, c_bottom = min(orig_w, right), min(orig_h, bottom)
                cropped = processed_tensor[:, c_top:c_bottom, c_left:c_right, :]
                if pad_left > 0 or pad_right > 0 or pad_top > 0 or pad_bottom > 0:
                    cropped = cropped.movedim(-1, 1)
                    cropped = F.pad(cropped, (pad_left, pad_right, pad_top, pad_bottom), mode='replicate')
                    cropped = cropped.movedim(1, -1)
                processed_tensor = cropped
                need_final_resize = False
                final_width = (c_right - c_left) + pad_left + pad_right
                final_height = (c_bottom - c_top) + pad_top + pad_bottom
            else:
                bw = base_target_width if base_target_width > 0 else (
                    base_target_height if base_target_height > 0 else 512)
                bh = base_target_height if base_target_height > 0 else bw
                left = cx - bw // 2
                right = left + bw
                top = cy - bh // 2
                bottom = top + bh
                pad_left, pad_top = max(0, -left), max(0, -top)
                pad_right, pad_bottom = max(0, right - orig_w), max(0, bottom - orig_h)
                c_left, c_top = max(0, left), max(0, top)
                c_right, c_bottom = min(orig_w, right), min(orig_h, bottom)
                cropped = processed_tensor[:, c_top:c_bottom, c_left:c_right, :]
                if pad_left > 0 or pad_right > 0 or pad_top > 0 or pad_bottom > 0:
                    cropped = cropped.movedim(-1, 1)
                    cropped = F.pad(cropped, (pad_left, pad_right, pad_top, pad_bottom), mode='replicate')
                    cropped = cropped.movedim(1, -1)
                processed_tensor = cropped
                need_final_resize = False
                final_width, final_height = bw, bh
        elif keep_proportion == "stretch":
            final_width = align_to_divisible(base_target_width, divisible_by)
            final_height = align_to_divisible(base_target_height, divisible_by)
        elif keep_proportion == "crop":
            target_ratio = base_target_width / base_target_height
            if orig_ratio > target_ratio:
                crop_height = orig_h
                crop_width = int(crop_height * target_ratio)
                offset = (orig_w - crop_width) // 2
                if crop_position == "left":
                    offset = 0
                elif crop_position == "right":
                    offset = orig_w - crop_width
                processed_tensor = processed_tensor[:, :, offset:offset + crop_width, :]
            else:
                crop_width = orig_w
                crop_height = int(crop_width / target_ratio)
                offset = (orig_h - crop_height) // 2
                if crop_position == "top":
                    offset = 0
                elif crop_position == "bottom":
                    offset = orig_h - crop_height
                processed_tensor = processed_tensor[:, offset:offset + crop_height, :, :]
            final_width = align_to_divisible(base_target_width, divisible_by)
            final_height = align_to_divisible(base_target_height, divisible_by)
        elif keep_proportion == "pad":
            scale = min(base_target_width / orig_w, base_target_height / orig_h)
            scaled_w = align_to_divisible(int(orig_w * scale), divisible_by)
            scaled_h = align_to_divisible(int(orig_h * scale), divisible_by)
            final_width, final_height = base_target_width, base_target_height
            processed_tensor = processed_tensor.movedim(-1, 1)
            processed_tensor = F.interpolate(processed_tensor, size=(scaled_h, scaled_w),
                                             mode=method if method != "lanczos" else "bilinear",
                                             align_corners=False if method in ['bilinear', 'bicubic'] else None)
            pad_left = (final_width - scaled_w) // 2
            pad_right = final_width - scaled_w - pad_left
            pad_top = (final_height - scaled_h) // 2
            pad_bottom = final_height - scaled_h - pad_top
            processed_tensor = F.pad(processed_tensor, (pad_left, pad_right, pad_top, pad_bottom), mode='constant',
                                     value=0)
            processed_tensor = processed_tensor.movedim(1, -1)
            need_final_resize = False
        elif keep_proportion == "pad_edge":
            scale = min(base_target_width / orig_w, base_target_height / orig_h)
            scaled_w = align_to_divisible(int(orig_w * scale), divisible_by)
            scaled_h = align_to_divisible(int(orig_h * scale), divisible_by)
            final_width, final_height = base_target_width, base_target_height
            processed_tensor = processed_tensor.movedim(-1, 1)
            processed_tensor = F.interpolate(processed_tensor, size=(scaled_h, scaled_w),
                                             mode=method if method != "lanczos" else "bilinear",
                                             align_corners=False if method in ['bilinear', 'bicubic'] else None)
            pad_left = (final_width - scaled_w) // 2
            pad_right = final_width - scaled_w - pad_left
            pad_top = (final_height - scaled_h) // 2
            pad_bottom = final_height - scaled_h - pad_top
            processed_tensor = F.pad(processed_tensor, (pad_left, pad_right, pad_top, pad_bottom), mode='replicate')
            processed_tensor = processed_tensor.movedim(1, -1)
            need_final_resize = False
        elif keep_proportion == "pad_lb_pixel":
            scale = min(base_target_width / orig_w, base_target_height / orig_h)
            scaled_w = align_to_divisible(int(orig_w * scale), divisible_by)
            scaled_h = align_to_divisible(int(orig_h * scale), divisible_by)
            final_width, final_height = base_target_width, base_target_height
            processed_tensor = processed_tensor.movedim(-1, 1)
            processed_tensor = F.interpolate(processed_tensor, size=(scaled_h, scaled_w),
                                             mode=method if method != "lanczos" else "bilinear",
                                             align_corners=False if method in ['bilinear', 'bicubic'] else None)
            fill_color = processed_tensor[:, :, -1, 0:1].mean(dim=[2, 3], keepdim=True)
            pad_left = (final_width - scaled_w) // 2
            pad_right = final_width - scaled_w - pad_left
            pad_top = (final_height - scaled_h) // 2
            pad_bottom = final_height - scaled_h - pad_top
            processed_tensor = F.pad(processed_tensor, (pad_left, pad_right, pad_top, pad_bottom), mode='constant',
                                     value=fill_color)
            processed_tensor = processed_tensor.movedim(1, -1)
            need_final_resize = False
        elif keep_proportion == "pillarbox_blur":
            final_width = align_to_divisible(base_target_width, divisible_by)
            final_height = align_to_divisible(base_target_height, divisible_by)
            bg_tensor = processed_tensor.movedim(-1, 1)
            bg_tensor = F.interpolate(bg_tensor, size=(final_height, final_width),
                                      mode=method if method != "lanczos" else "bilinear",
                                      align_corners=False if method in ['bilinear', 'bicubic'] else None)
            bg_tensor = F.gaussian_blur(bg_tensor, kernel_size=(31, 31), sigma=(15, 15))
            scale = min(final_width / orig_w, final_height / orig_h)
            fg_w = align_to_divisible(int(orig_w * scale), divisible_by)
            fg_h = align_to_divisible(int(orig_h * scale), divisible_by)
            fg_tensor = processed_tensor.movedim(-1, 1)
            fg_tensor = F.interpolate(fg_tensor, size=(fg_h, fg_w), mode=method if method != "lanczos" else "bilinear",
                                      align_corners=False if method in ['bilinear', 'bicubic'] else None)
            pad_left = (final_width - fg_w) // 2
            pad_top = (final_height - fg_h) // 2
            bg_tensor[:, :, pad_top:pad_top + fg_h, pad_left:pad_left + fg_w] = fg_tensor
            processed_tensor = bg_tensor.movedim(1, -1)
            need_final_resize = False
        elif keep_proportion == "resize" or keep_proportion == "filter":
            scale = min(base_target_width / orig_w, base_target_height / orig_h)
            final_width = align_to_divisible(int(orig_w * scale), divisible_by)
            final_height = align_to_divisible(int(orig_h * scale), divisible_by)
            processed_tensor = processed_tensor.movedim(-1, 1)
            processed_tensor = F.interpolate(processed_tensor, size=(final_height, final_width),
                                             mode=method if method != "lanczos" else "bilinear",
                                             align_corners=False if method in ['bilinear', 'bicubic'] else None)
            processed_tensor = processed_tensor.movedim(1, -1)
            need_final_resize = False
        elif keep_proportion == "total_pixels":
            orig_total_pixels = orig_w * orig_h
            if orig_total_pixels > base_target_total_pixels:
                scale = np.sqrt(base_target_total_pixels / orig_total_pixels)
                final_width = align_to_divisible(int(orig_w * scale), divisible_by)
                final_height = align_to_divisible(int(orig_h * scale), divisible_by)
                processed_tensor = processed_tensor.movedim(-1, 1)
                processed_tensor = F.interpolate(processed_tensor, size=(final_height, final_width),
                                                 mode=method if method != "lanczos" else "bilinear",
                                                 align_corners=False if method in ['bilinear', 'bicubic'] else None)
                processed_tensor = processed_tensor.movedim(1, -1)
            else:
                final_width = align_to_divisible(orig_w, divisible_by)
                final_height = align_to_divisible(orig_h, divisible_by)
            need_final_resize = False
        target_size = (final_width, final_height)
        if need_final_resize:
            if method == "lanczos":
                img_np = (processed_tensor[0].cpu().numpy() * 255).astype(np.uint8)
                pil_img = Image.fromarray(img_np)
                pil_img = pil_img.resize(target_size, Image.Resampling.LANCZOS)
                resized_np = np.array(pil_img).astype(np.float32) / 255.0
                final_tensor = torch.from_numpy(resized_np).unsqueeze(0).to(image_tensor.device)
            else:
                samples = processed_tensor.movedim(-1, 1)
                samples = F.interpolate(samples, size=(final_height, final_width), mode=method,
                                        align_corners=False if method in ['bilinear', 'bicubic'] else None)
                final_tensor = samples.movedim(1, -1)
        else:
            final_tensor = processed_tensor
        return final_tensor[0]
    except Exception as e:
        logger.error(f"[XXBuHuo] Resize 单图模式失败: {e}")
        return image_tensor


def _解析kv缓存类型(value: str):
    mapping = {"Q4_0(极致速度)": GGML_Q4_0, "Q4_1(极致速度+精度)": GGML_Q4_1, "Q5_0(高精度)": GGML_Q5_0,
               "Q5_1(高精度)": GGML_Q5_1, "Q8_0(提速30%)": GGML_Q8_0}
    return mapping.get(value, None)


class XXBuHuoOmniNode:
    @classmethod
    def INPUT_TYPES(s):
        input_dir = folder_paths.get_input_directory()
        files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))] if os.path.exists(
            input_dir) else []
        videos = ["None"] + [f for f in files if f.lower().endswith(('.mp4', '.mov', '.webm', '.avi', '.mkv'))]
        mmproj_list = ["None"] + folder_paths.get_filename_list("xxbuhuo_mmproj")
        llama_list = ["None"] + folder_paths.get_filename_list("xxbuhuo_llama")
        KV缓存选项 = ["默认(F16)", "Q5_K(平衡)", "Q8_0(提速30%)", "Q4_0(极致速度)", "Q4_1(极致速度+精度)",
                      "Q5_0(高精度)", "Q5_1(高精度)"]
        种子模式选项 = ["固定", "随机", "递增"]
        设备选项 = ["cpu", "cuda", "cuda:0", "cuda:1", "cuda:0+1", "auto(cpu+cuda混合)", "multi-gpu(自动均衡)"]
        模型架构选项 = ["Qwen3.5-VL", "Qwen3.6-VL", "Gemma4"]
        preset_list = ["None"] + list(PRESET_PROMPTS.keys())
        enhancer_list = ["None"] + list(ENHANCER_PROMPTS.keys())
        return {
            "required": {
                "ui_tab": (["参数", "模型", "模式"], {"default": "模型"}),
                "model_source": (["Local_GGUF", "Cloud_API"], {"default": "Local_GGUF"}),
                "gguf_model": (llama_list,),
                "mmproj_model": (mmproj_list,),
                "vision_type": (模型架构选项, {"default": "Gemma4"}),
                "draft_model": (llama_list, {"default": "None"}),
                "vram_limit": ("STRING", {"default": "Auto (-1)"}),
                "n_ctx": ("INT", {"default": 12800, "min": 2048, "max": 999999, "step": 1024}),
                "n_batch": ("INT", {"default": 2048, "min": 128, "max": 8192, "step": 128}),
                "n_gpu_layers": ("INT", {"default": -1, "min": -1, "max": 9999, "step": 1}),
                "cpu_threads": ("STRING", {"default": "Auto"}),
                "n_cpu_moe": ("STRING", {"default": "None"}),
                "kv_cache_type_k": (KV缓存选项, {"default": "默认(F16)"}),
                "kv_cache_type_v": (KV缓存选项, {"default": "默认(F16)"}),
                "api_url": ("STRING", {"default": ""}),
                "api_key": ("STRING", {"default": ""}),
                "api_model": ("STRING", {"default": ""}),
                "api_img_size": ("STRING", {"default": "2560x1440"}),
                "api_img_quality": (["standard", "hd", "low", "medium", "high", "auto"], {"default": "hd"}),
                "api_img_style": (["vivid", "natural"], {"default": "natural"}),
                "api_timeout": ("INT", {"default": 600, "min": 10, "max": 3000}),
                "api_url_presets": ("STRING", {"default": FINAL_ENDPOINTS_STR}),
                "multi_image_upload": ("STRING", {"multiline": True, "default": ""}),
                "video_upload": (videos,),
                "image_folder_path": ("STRING", {"default": ""}),
                "filter_store": ("STRING", {"default": ""}),
                "max_tokens": ("INT", {"default": 2048, "min": 16, "max": 8192}),
                "temperature": ("FLOAT", {"default": 0.8, "min": 0.0, "max": 2.0}),
                "top_p": ("FLOAT", {"default": 0.95, "min": 0.0, "max": 1.0, "step": 0.01}),
                "repeat_penalty": ("FLOAT", {"default": 1.1, "min": 1.0, "max": 2.0, "step": 0.01}),
                "video_max_frames": ("STRING", {"default": ""}),
                "image_max_size": ("INT", {"default": 1024, "min": 128, "max": 999999, "step": 64}),
                "enable_resize": ("BOOLEAN", {"default": False}),
                "resize_width": ("STRING", {"default": ""}),
                "resize_height": ("STRING", {"default": ""}),
                "swap_dimensions": ("BOOLEAN", {"default": False}),
                "upscale_method": (
                    ["nearest-exact", "bilinear", "area", "bicubic", "lanczos"], {"default": "nearest-exact"}),
                "keep_proportion": (
                    ["filter", "stretch", "resize", "pad", "pad_edge", "pad_lb_pixel", "crop", "pillarbox_blur",
                     "total_pixels"], {"default": "resize"}),
                "crop_position": (["center", "top", "bottom", "left", "right", "face", "head"], {"default": "center"}),
                "device": (设备选项, {"default": "cuda"}),
                "divisible_by": ("STRING", {"default": ""}),
                "preset_prompt": (preset_list, {"default": "None"}),
                "system_prompt": (
                    "STRING", {"multiline": True, "default": "你是一个AI助手，严格遵循用户要求，输出对应内容。"}),
                "prompt_enhancer": (enhancer_list, {"default": "None"}),
                "custom_prompt": ("STRING", {"multiline": True,
                                             "default": "简单的用描述一下图像，并输出200字中文提示词，不要包含任何注释！"}),
                "enable_preview": ("BOOLEAN", {"default": False}),
                "enable_smoothing": ("BOOLEAN", {"default": False}),
                "enable_llm_inference": ("BOOLEAN", {"default": False}),
                "force_unload": ("BOOLEAN", {"default": False}),
                "input_mode": (["逐帧推理", "视频推理", "宫格推理", "文本推理"],
                               {"default": "逐帧推理"}),
                "stream_to_console": ("BOOLEAN", {"default": True}),
                "enable_physical_block": ("BOOLEAN", {"default": True}),
                "save_chat_history": ("BOOLEAN", {"default": False}),
                "keep_model_in_vram": ("BOOLEAN", {"default": True}),
                "json_output": ("BOOLEAN", {"default": False}),
                "seed_mode": (种子模式选项, {"default": "固定"}),
                "llm_seed": ("INT", {"default": -1, "min": -1, "max": 0xffffffffffffffff}),
            },
            "optional": {
                "any_media": (ANY,),
                "sys_prompt": ("STRING", {"forceInput": True}),
                "user_prompt": ("STRING", {"forceInput": True}),
                "state_uid": ("INT", {"default": -1}),
            },
            "hidden": {"unique_id": "UNIQUE_ID"}
        }

    RETURN_TYPES = ("STRING", "IMAGE", "STRING", ANY)
    RETURN_NAMES = ("text", "image", "text_list", "Source_media")
    OUTPUT_IS_LIST = (False, False, True, False)
    OUTPUT_NODE = True
    FUNCTION = "execute"
    CATEGORY = "XXBuHuo"

    @classmethod
    def IS_CHANGED(s, **kwargs):
        enable_llm_inference = kwargs.get("enable_llm_inference", True)
        force_unload = kwargs.get("force_unload", False)
        keep_model_in_vram = kwargs.get("keep_model_in_vram", True)
        model_source = kwargs.get("model_source", "Local_GGUF")
        seed_mode = kwargs.get("seed_mode", "固定")
        if not enable_llm_inference:
            image_params = f"{kwargs.get('input_mode')}_{kwargs.get('multi_image_upload')}_{kwargs.get('video_upload')}_{kwargs.get('image_folder_path')}_{kwargs.get('enable_resize')}_{kwargs.get('resize_width')}_{kwargs.get('resize_height')}_{kwargs.get('swap_dimensions')}_{kwargs.get('upscale_method')}_{kwargs.get('keep_proportion')}_{kwargs.get('crop_position')}_{kwargs.get('divisible_by')}"
            return image_params
        if force_unload or not keep_model_in_vram or model_source == "Cloud_API":
            return float("NaN")
        if seed_mode == "随机":
            return float("NaN")
        gguf_model_name = kwargs.get("gguf_model", "").lower()
        vision_type = kwargs.get("vision_type", "Gemma4")
        if gguf_model_name != "none":
            if "qwen3.6" in gguf_model_name or "qwen-3.6" in gguf_model_name:
                vision_type = "Qwen3.6-VL"
            elif "qwen3.5" in gguf_model_name or "qwen-3.5" in gguf_model_name:
                vision_type = "Qwen3.5-VL"
            elif "gemma" in gguf_model_name:
                vision_type = "Gemma4"
            param_hash = f"{kwargs.get('gguf_model')}_{kwargs.get('mmproj_model')}_{kwargs.get('draft_model')}_{kwargs.get('n_ctx')}_{kwargs.get('n_batch')}_{kwargs.get('n_gpu_layers')}_{kwargs.get('cpu_threads')}_{kwargs.get('n_cpu_moe')}_{kwargs.get('vram_limit')}_{vision_type}_{kwargs.get('kv_cache_type_k')}_{kwargs.get('kv_cache_type_v')}_{kwargs.get('device')}_{kwargs.get('input_mode')}_{kwargs.get('preset_prompt')}_{kwargs.get('custom_prompt')}_{kwargs.get('system_prompt')}_{kwargs.get('sys_prompt')}_{kwargs.get('user_prompt')}_{kwargs.get('multi_image_upload')}_{kwargs.get('video_upload')}_{kwargs.get('image_folder_path')}_{kwargs.get('enable_physical_block')}_{kwargs.get('json_output')}_{kwargs.get('image_max_size')}_{kwargs.get('enable_resize')}_{kwargs.get('resize_width')}_{kwargs.get('resize_height')}_{kwargs.get('keep_proportion')}_{kwargs.get('crop_position')}"
            return f"{param_hash}_{kwargs.get('llm_seed')}"
        node_uid = int(kwargs.get("unique_id", "0").rpartition('.')[-1])
        if seed_mode == "递增":
            if hasattr(_GLOBAL_OMNI_CACHE, "last_param_hash") and _GLOBAL_OMNI_CACHE.last_param_hash.get(
                    node_uid) == param_hash:
                return float("NaN")
            else:
                _GLOBAL_OMNI_CACHE.reset_node_seed(node_uid)
                _GLOBAL_OMNI_CACHE.last_param_hash = getattr(_GLOBAL_OMNI_CACHE, "last_param_hash", {})
                _GLOBAL_OMNI_CACHE.last_param_hash[node_uid] = param_hash
                return float("NaN")
        return float("NaN")

    def execute(self, **kwargs):
        multi_image_upload = kwargs.get("multi_image_upload", "").strip()
        folder_path = kwargs.get("image_folder_path", "").strip().strip('"').strip("'")
        any_media = kwargs.get("any_media", None)
        active_sources = 0
        if any_media is not None: active_sources += 1
        if multi_image_upload: active_sources += 1
        if folder_path and os.path.exists(folder_path): active_sources += 1
        if active_sources > 1:
            err_msg = "连线模式、路径模式和上传模式只能选择其中一种！请断开连线、清空路径或清空上传列表。"
            print(f"\n[XXBuHuo] 错误：{err_msg}")
            raise ValueError(err_msg)
        media_passthrough = None
        if kwargs.get("any_media") is not None:
            media_passthrough = kwargs["any_media"]
        else:
            passthrough_list = []
            multi_img = kwargs.get("multi_image_upload", "").strip()
            if multi_img:
                for fname in multi_img.split("\n"):
                    if fname.strip():
                        p = folder_paths.get_annotated_filepath(fname.strip())
                        if os.path.exists(p): passthrough_list.append(p)
            folder_p = kwargs.get("image_folder_path", "").strip().strip('"').strip("'")
            if folder_p and os.path.exists(folder_p):
                for ext in ['*.jpg', '*.jpeg', '*.png', '*.webp', '*.mp4', '*.mov', '*.webm', '*.avi', '*.gif']:
                    passthrough_list.extend(glob.glob(os.path.join(folder_p, ext)))
            vid_up = kwargs.get("video_upload", "None")
            if vid_up != "None":
                vp = folder_paths.get_annotated_filepath(vid_up)
                if os.path.exists(vp): passthrough_list.append(vp)

            class MediaPassthroughProxy:
                def __init__(self, paths):
                    self.paths = paths
                    self._tensors = None

                def _load(self):
                    if self._tensors is None:
                        import torch
                        import numpy as np
                        from PIL import Image, ImageOps
                        tensors = []
                        for p in self.paths:
                            try:
                                if p.lower().endswith(('.mp4', '.mov', '.webm', '.avi', '.mkv', '.gif')):
                                    tensors.append(torch.zeros((512, 512, 3), dtype=torch.float32))
                                else:
                                    img = Image.open(p)
                                    img = ImageOps.exif_transpose(img).convert('RGB')
                                    tensors.append(torch.from_numpy(np.array(img)).float() / 255.0)
                            except:
                                tensors.append(torch.zeros((512, 512, 3), dtype=torch.float32))
                        self._tensors = tensors
                    return self._tensors

                def __getitem__(self, idx):
                    return self._load()[idx]

                def __len__(self):
                    return len(self.paths)

                def __iter__(self):
                    return iter(self._load())

                @property
                def shape(self):
                    import torch
                    return torch.stack(self._load()).shape

                def cpu(self):
                    import torch
                    return torch.stack(self._load()).cpu()

                def get_dimensions(self):
                    try:
                        p = self.paths[0]
                        if p.lower().endswith(('.mp4', '.mov', '.webm', '.avi', '.mkv', '.gif')):
                            import cv2
                            cap = cv2.VideoCapture(p)
                            w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                            cap.release()
                            return (w, h)
                        else:
                            from PIL import Image
                            with Image.open(p) as img:
                                return img.size
                    except:
                        return (512, 512)

                def save_to(self, dest_path, *args, **kwargs):
                    import shutil, os
                    try:
                        if os.path.exists(self.paths[0]): shutil.copy2(self.paths[0], dest_path)
                    except:
                        pass

                def __str__(self):
                    return self.paths[0]

            if passthrough_list:
                media_passthrough = MediaPassthroughProxy(passthrough_list)
        force_unload = kwargs.get("force_unload", False)
        enable_llm_inference = kwargs.get("enable_llm_inference", True)
        enable_physical_block = kwargs.get("enable_physical_block", True)
        enable_resize = kwargs.get("enable_resize", False)
        preview_enabled = kwargs.get("enable_preview", True)
        node_uid = int(kwargs.get("unique_id", "0").rpartition('.')[-1])
        uid = kwargs.get("state_uid", -1) if kwargs.get("state_uid", -1) != -1 else node_uid
        device = kwargs.get("device", "cuda")
        target_device = device if (device.startswith("cuda") or device == "cpu") else "cuda"
        raw_v_max_str = str(kwargs.get("video_max_frames", "8")).strip().lower()
        if raw_v_max_str in ["", "0"]:
            v_max = 0
        elif raw_v_max_str == "-1":
            v_max = -1
        else:
            try:
                v_max = int(raw_v_max_str.split('*')[0].split('x')[0])
            except:
                v_max = 8
        if not enable_llm_inference and not enable_resize and not preview_enabled:
            out_tensor_list = []
            any_media = kwargs.get("any_media")
            paths_to_read = []
            if any_media is not None:
                descriptors = parse_any_media_to_descriptors(any_media)
                for desc in descriptors:
                    if desc["type"] == "tensor":
                        t = desc["data"]
                        if t.dim() == 4:
                            out_tensor_list.extend([t[i] for i in range(t.shape[0])])
                        elif t.dim() == 3:
                            out_tensor_list.append(t)
                        elif t.dim() == 2:
                            out_tensor_list.append(t.unsqueeze(-1).repeat(1, 1, 3))
                    elif desc["type"] == "image_path":
                        paths_to_read.append({"type": "image", "path": desc["path"]})
                    elif desc["type"] == "video_path":
                        if v_max != 0:
                            paths_to_read.append({"type": "video", "path": desc["path"]})
            else:
                if media_passthrough is not None:
                    if hasattr(media_passthrough, 'paths'):
                        m_list = media_passthrough.paths
                    else:
                        m_list = media_passthrough if isinstance(media_passthrough, list) else [
                            media_passthrough]
                    for p in m_list:
                        p_str = str(p)
                        if os.path.exists(p_str):
                            if p_str.lower().endswith(('.mp4', '.mov', '.webm', '.avi', '.mkv', '.gif')):
                                if v_max != 0: paths_to_read.append({"type": "video", "path": p_str})
                            else:
                                paths_to_read.append({"type": "image", "path": p_str})
            if paths_to_read:
                def fast_read_task(info):
                    p = info["path"]
                    try:
                        if info["type"] == "video":
                            frames = extract_video_frames(p, v_max)
                            return [f if f.dim() == 3 else f.squeeze(0) for f in frames]
                        else:
                            img = load_image_with_orientation(p)
                            t = torch.from_numpy(np.array(img)).float() / 255.0
                            return [t]
                    except:
                        return []

                from concurrent.futures import ThreadPoolExecutor
                with ThreadPoolExecutor(max_workers=8) as executor:
                    for res_list in executor.map(fast_read_task, paths_to_read):
                        if res_list: out_tensor_list.extend(res_list)
            if not out_tensor_list:
                if v_max == 0: print("\n[XXBuHuo] 纯透传模式。")
                out_tensor_list = [torch.zeros((64, 64, 3), dtype=torch.float32, device=target_device)]
            return {"ui": {},
                    "result": ("纯透传模式", out_tensor_list, ["纯透传模式"], media_passthrough, uid)}
        gguf_model_name = kwargs.get("gguf_model", "").lower()
        if gguf_model_name != "none":
            if "qwen3.6" in gguf_model_name or "qwen-3.6" in gguf_model_name:
                kwargs["vision_type"] = "Qwen3.6-VL"
            elif "qwen3.5" in gguf_model_name:
                kwargs["vision_type"] = "Qwen3.5-VL"
            elif "gemma" in gguf_model_name:
                kwargs["vision_type"] = "Gemma4"
        if force_unload:
            print("[XXBuHuo] 强制卸载：清空显存...")
            _GLOBAL_OMNI_CACHE.clear()
        seed_mode = kwargs.get("seed_mode", "固定")
        input_seed = int(kwargs.get("llm_seed", -1))
        node_uid = int(kwargs.get("unique_id", "0").rpartition('.')[-1])
        uid = kwargs.get("state_uid", -1) if kwargs.get("state_uid", -1) != -1 else node_uid
        video_max_frames = v_max
        grid_param = str(kwargs.get("video_max_frames", "3*3")).lower()
        image_max_size_val = int(kwargs.get("image_max_size", 512))
        rw_str = str(kwargs.get("resize_width", "1024")).strip()
        resize_width = int(rw_str) if rw_str and rw_str.isdigit() else 0
        rh_str = str(kwargs.get("resize_height", "1024")).strip()
        resize_height = int(rh_str) if rh_str and rh_str.isdigit() else 0
        div_str = str(kwargs.get("divisible_by", "")).strip()
        divisible_by = int(div_str) if div_str and div_str.isdigit() else 0
        crop_position = kwargs.get("crop_position", "center")
        keep_proportion = kwargs.get("keep_proportion", "resize")
        if crop_position in ["head", "face"] and keep_proportion == "crop":
            if (resize_width > 0 or resize_height > 0) and divisible_by > 0:
                raise ValueError(
                    f"\n[XXBuHuo] 拦截：在【{crop_position}】模式下，[宽/高数值] 与 [对齐倍数] 逻辑互斥，不能同时填写！请清空对齐倍数，或将宽高设为0(留空)。")
        target_seed = input_seed
        if seed_mode == "随机":
            target_seed = random.randint(0, 0xffffffffffffffff)
        elif seed_mode == "递增":
            target_seed = _GLOBAL_OMNI_CACHE.get_node_seed(node_uid, input_seed)
        else:
            if target_seed == -1: target_seed = 0
        print(f"\n[XXBuHuo] 运行种子 (Seed): {target_seed} | 模式: {seed_mode}")
        model_source = kwargs.get("model_source", "Local_GGUF")
        device = kwargs.get("device", "cuda")
        cpu_core_count = multiprocessing.cpu_count()
        available_gpus = get_available_cuda_devices()
        target_device = device if (device.startswith("cuda") or device == "cpu") else "cuda"
        omni_engine = None
        if enable_llm_inference:
            if model_source == "Cloud_API":
                if not kwargs.get("save_chat_history", False) or force_unload:
                    _GLOBAL_OMNI_CACHE.clear()
                omni_engine = {"mode": "api", "api_url": kwargs["api_url"], "api_key": kwargs["api_key"],
                               "api_model": kwargs["api_model"], "has_vision": True}
            else:
                if not HAS_LLAMA: raise Exception("错误：未找到 llama-cpp-python 依赖，请先安装！")
                if kwargs["gguf_model"] == "None": raise Exception("请选择一个本地 GGUF 主模型！")
                n_ctx_val = int(kwargs.get("n_ctx", 12800))
                n_batch_val = int(kwargs.get("n_batch", 2048))
                n_gpu_layers = int(kwargs.get("n_gpu_layers", -1))
                enable_physical_block = kwargs.get("enable_physical_block", True)
                cpu_th_cache = str(kwargs.get('cpu_threads', '')).strip()
                moe_cache = str(kwargs.get('n_cpu_moe', '')).strip()
                cache_key = f"{kwargs['gguf_model']}_{kwargs.get('mmproj_model', 'None')}_{kwargs['draft_model']}_{n_ctx_val}_{n_batch_val}_{n_gpu_layers}_{kwargs['vram_limit']}_{kwargs['vision_type']}_{kwargs['kv_cache_type_k']}_{kwargs['kv_cache_type_v']}_{kwargs['device']}_block{enable_physical_block}_th{cpu_th_cache}_moe{moe_cache}"
                omni_engine = _GLOBAL_OMNI_CACHE.get(cache_key)
                if omni_engine is None:
                    _GLOBAL_OMNI_CACHE.clear()
                    print(f"\n[XXBuHuo] 初始化本地推理 | 运行设备: {device}")
                    model_path = folder_paths.get_full_path("xxbuhuo_llama", kwargs["gguf_model"])
                    draft_path = folder_paths.get_full_path("xxbuhuo_llama", kwargs["draft_model"]) if kwargs[
                                                                                                           "draft_model"] != "None" else None
                    chat_handler = None
                    has_vision = False
                    mmproj_model = kwargs.get("mmproj_model", "None")
                    vision_type = kwargs["vision_type"]
                    if mmproj_model != "None":
                        mmproj_path = folder_paths.get_full_path("xxbuhuo_mmproj", mmproj_model)
                        try:
                            if vision_type in ["Qwen3.5-VL", "Qwen3.6-VL"]:
                                from llama_cpp.llama_chat_format import Qwen35ChatHandler
                                chat_handler = Qwen35ChatHandler(clip_model_path=mmproj_path,
                                                                 enable_thinking=not enable_physical_block,
                                                                 add_vision_id=True, verbose=False)
                            elif vision_type == "Gemma4":
                                from llama_cpp.llama_chat_format import Gemma4ChatHandler
                                chat_handler = Gemma4ChatHandler(clip_model_path=mmproj_path, verbose=False)
                            has_vision = True
                        except ImportError as e:
                            logger.warning(f"高级 Handler 失败，回退 Llava: {e}")
                            from llama_cpp.llama_chat_format import Llava15ChatHandler
                            chat_handler = Llava15ChatHandler(clip_model_path=mmproj_path, verbose=False)
                            has_vision = True
                    vram_limit = kwargs.get("vram_limit", "Auto (-1)")
                    main_gpu = 0
                    tensor_split = None
                    cpu_core_count = multiprocessing.cpu_count()
                    cpu_threads_str = str(kwargs.get("cpu_threads", "")).strip().lower()
                    cpu_threads_input = 0 if ("auto" in cpu_threads_str or not cpu_threads_str) else (
                        int(cpu_threads_str) if cpu_threads_str.isdigit() else 0)
                    moe_str = str(kwargs.get("n_cpu_moe", "")).strip().lower()
                    if "none" in moe_str:
                        n_cpu_moe_input = -1
                    elif "auto" in moe_str or not moe_str:
                        n_cpu_moe_input = 0
                    else:
                        n_cpu_moe_input = int(moe_str) if moe_str.isdigit() else 0
                    n_gpu_layers = int(kwargs.get("n_gpu_layers", -1))
                    total_layers = 32
                    moe_total_layers = -1
                    model_size_gb = 0
                    try:
                        if os.path.exists(model_path):
                            model_size_gb = os.path.getsize(model_path) / (1024 ** 3)
                            with open(model_path, 'rb') as f:
                                header_data = f.read(2 * 1024 * 1024)
                                if b'llama.attention.layer_count' in header_data:
                                    idx = header_data.index(b'llama.attention.layer_count') + 30
                                    total_layers = int.from_bytes(header_data[idx:idx + 4], 'little')
                                if b'expert_count' in header_data or b'qwen2moe' in header_data or b'deepseek2' in header_data:
                                    matches = re.findall(rb'blk\.(\d+)\.(?:ffn|expert)', header_data)
                                    moe_total_layers = max([int(m) for m in matches]) + 1 if matches else total_layers
                                    print(f"\n[XXBuHuo] MoE 检测: {moe_total_layers} 层专家层。")
                    except Exception as e:
                        print(f"[XXBuHuo] 元数据扫描异常: {e}")
                    if device == "cpu":
                        n_gpu_layers = 0
                    elif device == "auto(cpu+cuda混合)":
                        if len(available_gpus) > 0 and model_size_gb > 0:
                            try:
                                gpu_free_mem = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3) - 1.0
                                layer_size_gb = (model_size_gb * 1.15) / total_layers
                                n_gpu_layers = max(1, int(gpu_free_mem / layer_size_gb))
                            except:
                                n_gpu_layers = 9999
                    if device != "cpu" and n_gpu_layers == -1:
                        n_gpu_layers = 9999
                    target_vram_gb = 999.0
                    if device.startswith("cuda") or device == "auto(cpu+cuda混合)":
                        if len(available_gpus) > 0:
                            target_vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3) - 1.0
                    vram_str = str(vram_limit).strip().lower()
                    is_explicit_limit = False
                    if vram_str and "auto" not in vram_str and "-1" not in vram_str:
                        try:
                            match = re.search(r'([0-9.]+)', vram_str)
                            if match:
                                target_vram_gb = float(match.group(1))
                                is_explicit_limit = True
                        except:
                            pass
                    safe_model_size = model_size_gb * 1.15
                    is_vram_tight = (model_size_gb > 0 and target_vram_gb < safe_model_size)
                    final_n_cpu_moe = 0
                    is_moe_enabled = (moe_total_layers > 0 and n_cpu_moe_input != -1)
                    if is_moe_enabled:
                        if is_vram_tight:
                            deficit_gb = safe_model_size - target_vram_gb
                            avg_layer_size = safe_model_size / max(1, total_layers)
                            expert_saved_per_layer = avg_layer_size * 0.75
                            needed_moe_layers = int(deficit_gb / expert_saved_per_layer) + 1
                            if n_cpu_moe_input == 0:
                                final_n_cpu_moe = max(0, min(moe_total_layers, needed_moe_layers))
                            else:
                                final_n_cpu_moe = max(n_cpu_moe_input, min(moe_total_layers, needed_moe_layers))
                            actual_saved = final_n_cpu_moe * expert_saved_per_layer
                            if deficit_gb > actual_saved:
                                n_gpu_layers = max(1, int(target_vram_gb / avg_layer_size))
                                print(f" ╰─ MoE 专家层全卸载，显存仍不足，已自动降低基础层 GPU 加载数。")
                            else:
                                if int(kwargs.get("n_gpu_layers", -1)) == -1: n_gpu_layers = 9999
                        else:
                            final_n_cpu_moe = n_cpu_moe_input if n_cpu_moe_input > 0 else 0
                    else:
                        if device == "auto(cpu+cuda混合)" or is_explicit_limit:
                            if is_vram_tight and device != "cpu":
                                layer_size_gb = safe_model_size / max(1, total_layers)
                                n_gpu_layers = max(1, int(target_vram_gb / layer_size_gb))
                                print(f" ╰─ 触发 {target_vram_gb}GB 限制，正在重新分配 GPU/CPU 层数。")
                    if cpu_threads_input > 0:
                        n_threads = n_threads_batch = cpu_threads_input
                    else:
                        n_threads = n_threads_batch = max(4, cpu_core_count)
                        if is_moe_enabled and final_n_cpu_moe > 0:
                            pass
                        elif n_gpu_layers < total_layers and n_gpu_layers != 9999:
                            restricted_val = min(8, max(4, cpu_core_count // 4))
                            n_threads = n_threads_batch = restricted_val
                            print(f" ╰─ 模型已部分卸载至系统内存，CPU 线程自动调整为 {restricted_val}。")
                        else:
                            pass
                    llama_kwargs = {
                        "model_path": model_path, "chat_handler": chat_handler, "n_ctx": n_ctx_val,
                        "n_gpu_layers": n_gpu_layers, "verbose": False, "n_batch": n_batch_val,
                        "n_threads": n_threads, "n_threads_batch": n_threads_batch, "main_gpu": main_gpu,
                        "flash_attn": True
                    }
                    if final_n_cpu_moe > 0: llama_kwargs["n_cpu_moe"] = final_n_cpu_moe
                    if draft_path: llama_kwargs["draft_model"] = draft_path
                    if tensor_split is not None: llama_kwargs["tensor_split"] = tensor_split
                    llama_kwargs["ctx_checkpoints"] = 0
                    if kwargs["kv_cache_type_k"] != "默认(F16)": llama_kwargs["type_k"] = _解析kv缓存类型(
                        kwargs["kv_cache_type_k"])
                    if kwargs["kv_cache_type_v"] != "默认(F16)": llama_kwargs["type_v"] = _解析kv缓存类型(
                        kwargs["kv_cache_type_v"])
                    llm = Llama(**llama_kwargs)
                    omni_engine = {"mode": "local", "llm": llm, "vision_type": vision_type, "has_vision": has_vision,
                                   "enable_thinking": False, "device": device}
                    _GLOBAL_OMNI_CACHE.set(cache_key, omni_engine)
                    print("[XXBuHuo] 部署完毕！")
        images_list = []
        input_mode = kwargs["input_mode"]
        any_media_ui_images = []
        images_list = []
        raw_sources = []
        temp_dir = folder_paths.get_temp_directory()
        multi_image_upload = kwargs.get("multi_image_upload", "").strip()
        folder_path = kwargs.get("image_folder_path", "").strip().strip('"').strip("'")
        any_media = kwargs.get("any_media", None)
        raw_sources = []
        temp_dir = folder_paths.get_temp_directory()
        preview_enabled = kwargs.get("enable_preview", True)
        if any_media is not None:
            descriptors = parse_any_media_to_descriptors(any_media)
            if not preview_enabled:
                for desc in descriptors:
                    if desc["type"] == "video_path":
                        raw_sources.append(
                            {"ui": None, "tensors": extract_video_frames(desc["path"], video_max_frames)})
                    elif desc["type"] == "image_path":
                        try:
                            img = load_image_with_orientation(desc["path"])
                            raw_sources.append(
                                {"ui": None, "tensors": [torch.from_numpy(np.array(img)).float() / 255.0]})
                        except:
                            pass
                    elif desc["type"] == "tensor":
                        t = desc["data"]
                        tensors = [t[i] if t.dim() == 4 else t for i in range(t.shape[0] if t.dim() == 4 else 1)]
                        raw_sources.append({"ui": None, "tensors": tensors})
            else:
                from concurrent.futures import ThreadPoolExecutor
                with ThreadPoolExecutor(max_workers=8) as executor:
                    futures = []
                    for desc in descriptors:
                        if desc["type"] == "video_path":
                            orig_path = desc["path"]
                            ext = os.path.splitext(orig_path)[1]
                            filename = f"xxbuhuo_temp_vid_{uuid.uuid4().hex[:8]}{ext}"
                            filepath = os.path.join(temp_dir, filename)
                            try:
                                os.symlink(orig_path, filepath)
                            except:
                                shutil.copy(orig_path, filepath)
                            raw_sources.append(
                                {"ui": {"filename": filename, "type": "temp", "subfolder": "", "media_type": "video"},
                                 "tensors": extract_video_frames(orig_path, video_max_frames)})
                        elif desc["type"] == "image_path":
                            orig_path = desc["path"]
                            ext = os.path.splitext(orig_path)[1]
                            filename = f"xxbuhuo_temp_img_{uuid.uuid4().hex[:8]}{ext}"
                            filepath = os.path.join(temp_dir, filename)
                            try:
                                os.symlink(orig_path, filepath)
                            except:
                                shutil.copy(orig_path, filepath)
                            try:
                                img = load_image_with_orientation(orig_path)
                                raw_sources.append(
                                    {"ui": {"filename": filename, "type": "temp", "subfolder": "",
                                            "media_type": "image"},
                                     "tensors": [torch.from_numpy(np.array(img)).float() / 255.0]})
                            except:
                                pass
                        elif desc["type"] == "tensor":
                            t = desc["data"]
                            if t.dim() == 4 and t.shape[0] > 1:
                                def process_video_tensor(t_vid):
                                    filename = f"xxbuhuo_temp_vid_{uuid.uuid4().hex[:8]}.mp4"
                                    filepath = os.path.join(temp_dir, filename)
                                    try:
                                        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                                        out = cv2.VideoWriter(filepath, fourcc, 8.0, (t_vid.shape[2], t_vid.shape[1]))
                                        frames_np = (t_vid.cpu().numpy() * 255).astype(np.uint8)
                                        for i in range(frames_np.shape[0]):
                                            out.write(cv2.cvtColor(frames_np[i], cv2.COLOR_RGB2BGR))
                                        out.release()
                                        tensors = [t_vid[i].squeeze(0) for i in range(t_vid.shape[0])]
                                        return {"ui": {"filename": filename, "type": "temp", "subfolder": "",
                                                       "media_type": "video"},
                                                "tensors": tensors}
                                    except:
                                        return None

                                futures.append(executor.submit(process_video_tensor, t))
                            else:
                                for i in range(t.shape[0] if t.dim() == 4 else 1):
                                    frame_t = t[i] if t.dim() == 4 else t

                                    def process_image_tensor(f_t):
                                        try:
                                            img_np = (f_t.cpu().numpy() * 255).astype(np.uint8)
                                            pil_img = Image.fromarray(img_np)
                                            filename = f"xxbuhuo_temp_img_{uuid.uuid4().hex[:8]}.png"
                                            filepath = os.path.join(temp_dir, filename)
                                            pil_img.save(filepath, format="PNG", compress_level=1)
                                            return {"ui": {"filename": filename, "type": "temp", "subfolder": "",
                                                           "media_type": "image"},
                                                    "tensors": [f_t.cpu().squeeze(0) if f_t.dim() == 4 else f_t.cpu()]}
                                        except:
                                            return None

                                    futures.append(executor.submit(process_image_tensor, frame_t))
                    for future in futures:
                        res = future.result()
                        if res:
                            raw_sources.append(res)
        multi_image_upload = kwargs.get("multi_image_upload", "").strip()
        if multi_image_upload:
            upload_filepaths = []
            for fname in multi_image_upload.split("\n"):
                fname = fname.strip()
                if not fname: continue
                img_path = folder_paths.get_annotated_filepath(fname)
                if os.path.exists(img_path):
                    upload_filepaths.append(img_path)

            def process_upload_file(img_path):
                try:
                    if img_path.lower().endswith(('.mp4', '.mov', '.webm', '.avi', '.mkv', '.gif')):
                        return {"ui": None, "tensors": extract_video_frames(img_path, video_max_frames)}
                    else:
                        img_tensor = torch.from_numpy(np.array(load_image_with_orientation(img_path))).float() / 255.0
                        return {"ui": None, "tensors": [img_tensor]}
                except Exception as e:
                    logger.error(f"[XXBuHuo] 上传文件读取失败 {img_path}: {e}")
                    return None

            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=8) as executor:
                for res in executor.map(process_upload_file, upload_filepaths):
                    if res: raw_sources.append(res)
        folder_path = kwargs.get("image_folder_path", "").strip().strip('"').strip("'")
        if folder_path and os.path.exists(folder_path):
            filepaths = []
            for ext in ['*.jpg', '*.jpeg', '*.png', '*.webp', '*.mp4', '*.mov', '*.webm', '*.avi', '*.gif']:
                filepaths.extend(glob.glob(os.path.join(folder_path, ext)))

            def process_folder_file(filepath):
                try:
                    is_video = filepath.lower().endswith(('.mp4', '.mov', '.webm', '.avi', '.gif'))
                    ui_meta = None
                    if preview_enabled:
                        filename = f"xxbuhuo_temp_{'vid' if is_video else 'img'}_{uuid.uuid4().hex[:8]}{os.path.splitext(filepath)[1]}"
                        temp_filepath = os.path.join(temp_dir, filename)
                        try:
                            os.symlink(filepath, temp_filepath)
                        except:
                            shutil.copy(filepath, temp_filepath)
                        ui_meta = {"filename": filename, "type": "temp", "subfolder": "",
                                   "media_type": "video" if is_video else "image"}
                    if is_video:
                        return {"ui": ui_meta, "tensors": extract_video_frames(filepath, video_max_frames)}
                    else:
                        img_tensor = torch.from_numpy(np.array(load_image_with_orientation(filepath))).float() / 255.0
                        return {"ui": ui_meta, "tensors": [img_tensor]}
                except Exception as e:
                    logger.error(f"[XXBuHuo] 文件夹读取失败 {filepath}: {e}")
                    return None

            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=8) as executor:
                for res in executor.map(process_folder_file, filepaths):
                    if res: raw_sources.append(res)
        video_upload = kwargs.get("video_upload", "None")
        if video_upload != "None":
            video_path = folder_paths.get_annotated_filepath(video_upload)
            if os.path.exists(video_path):
                raw_sources.append({"ui": None, "tensors": extract_video_frames(video_path, video_max_frames)})
        for src in raw_sources:
            if src["ui"]: any_media_ui_images.append(src["ui"])
        filter_str = kwargs.get("filter_store", "").strip()
        if filter_str:
            try:
                clean_str = re.sub(r'[^0-9,，/\\、\s]', ' ', filter_str)
                indices = [int(x.strip()) - 1 for x in re.split(r'[,，/\\、\s]+', clean_str) if
                           x.strip().isdigit()]
                valid_indices = [i for i in indices if 0 <= i < len(raw_sources)]
                if valid_indices:
                    raw_sources = [raw_sources[i] for i in valid_indices]
            except Exception as e:
                logger.error(f"[XXBuHuo] 筛选拦截逻辑出错: {e}")
        for src in raw_sources:
            images_list.extend(src["tensors"])
        processed_images = []
        if len(images_list) > 0:
            if kwargs["enable_resize"]:
                enable_smoothing = kwargs.get("enable_smoothing", False)
                smooth_state = {"prev_center": None, "prev_angle": 0.0, "prev_box": None} if enable_smoothing else None
                is_face_head = kwargs["crop_position"] in ["face", "head"] and kwargs["keep_proportion"] == "crop"
                precomputed_faces = [None] * len(images_list)
                if is_face_head and len(images_list) > 0:
                    try:
                        print(f"\n[XXBuHuo] 启动批量人脸侦测 (共 {len(images_list)} 帧)...")
                        detector_info = get_face_detector(target_device)
                        if detector_info["type"] == "insightface":
                            import torch.nn.functional as F
                            from concurrent.futures import ThreadPoolExecutor
                            try:
                                B = len(images_list)
                                bgr_numpy_list = [None] * B
                                H, W = images_list[0].shape[0], images_list[0].shape[1]
                                max_dim = max(H, W)
                                target_dim = 640
                                inv_scale = 1.0
                                if max_dim > target_dim:
                                    scale = target_dim / max_dim
                                    new_w, new_h = int(W * scale), int(H * scale)
                                    inv_scale = 1.0 / scale
                                else:
                                    new_w, new_h = W, H
                                chunk_size = 16
                                for i in range(0, B, chunk_size):
                                    chunk = images_list[i:i + chunk_size]
                                    chunk_tensor = torch.stack(chunk).to(target_device, non_blocking=True)
                                    if max_dim > target_dim:
                                        chunk_tensor = chunk_tensor.movedim(-1, 1)
                                        chunk_tensor = F.interpolate(chunk_tensor, size=(new_h, new_w), mode='bilinear',
                                                                     align_corners=False)
                                        chunk_tensor = chunk_tensor.movedim(1, -1)
                                    chunk_bgr = chunk_tensor[..., [2, 1, 0]]
                                    chunk_uint8 = (chunk_bgr * 255).byte().cpu().numpy()
                                    for j in range(len(chunk)):
                                        bgr_numpy_list[i + j] = chunk_uint8[j]
                                app = detector_info["app"]

                                def _infer_face(args):
                                    idx, img_bgr = args
                                    faces = app.get(img_bgr)
                                    if faces:
                                        face = faces[0]
                                        bbox = face.bbox * inv_scale if inv_scale != 1.0 else face.bbox
                                        kps = face.kps * inv_scale if inv_scale != 1.0 else face.kps
                                        return idx, np.array([bbox]), np.array([face.det_score]), np.array([kps])
                                    return idx, None, None, None

                                with ThreadPoolExecutor(max_workers=min(4, B)) as executor:
                                    results = executor.map(_infer_face, enumerate(bgr_numpy_list))
                                for idx, b, p, l in results:
                                    precomputed_faces[idx] = (b, p, l)
                            except Exception as e:
                                print(f"[XXBuHuo] 图像处理异常，回退基础模式: {e}")
                                import cv2
                                app = detector_info["app"]
                                for i, img in enumerate(images_list):
                                    img_np = (img.cpu().numpy() * 255).astype(np.uint8)
                                    img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
                                    faces = app.get(img_bgr)
                                    if faces:
                                        face = faces[0]
                                        precomputed_faces[i] = (
                                            np.array([face.bbox]), np.array([face.det_score]), np.array([face.kps]))
                            last_valid = None
                            for i in range(len(precomputed_faces)):
                                if precomputed_faces[i] is not None:
                                    last_valid = precomputed_faces[i]
                                elif last_valid is not None:
                                    precomputed_faces[i] = last_valid
                            last_valid = None
                            for i in range(len(precomputed_faces) - 1, -1, -1):
                                if precomputed_faces[i] is not None:
                                    last_valid = precomputed_faces[i]
                                elif last_valid is not None:
                                    precomputed_faces[i] = last_valid
                    except Exception as e:
                        print(f"[XXBuHuo] 批量面部检测失败: {e}")

                def _do_resize(args):
                    idx, img = args
                    state = smooth_state if enable_smoothing else None
                    face_data = precomputed_faces[idx]
                    out_img = process_resize_image_single(
                        img, resize_width, resize_height, kwargs["upscale_method"],
                        kwargs["keep_proportion"], kwargs["crop_position"], kwargs["swap_dimensions"],
                        divisible_by, smooth_state=state, precomputed_face=face_data
                    )
                    return out_img

                if len(images_list) == 1:
                    processed_images = [_do_resize((0, images_list[0]))]
                else:
                    if enable_smoothing and is_face_head:
                        processed_images = [_do_resize((idx, img)) for idx, img in enumerate(images_list)]
                    else:
                        from concurrent.futures import ThreadPoolExecutor
                        with ThreadPoolExecutor(max_workers=min(16, len(images_list))) as executor:
                            processed_images = list(executor.map(_do_resize, enumerate(images_list)))
            else:
                if enable_llm_inference:
                    processed_images = [img.to(target_device) for img in images_list]
                else:
                    processed_images = images_list
        else:
            processed_images = [torch.zeros((64, 64, 3), dtype=torch.float32, device=target_device)]
        out_image_list = []
        for img in processed_images:
            img_cpu = img.cpu()
            if img_cpu.dim() == 4:
                for b in range(img_cpu.shape[0]):
                    out_image_list.append(img_cpu[b])
            elif img_cpu.dim() == 3:
                out_image_list.append(img_cpu)
            elif img_cpu.dim() == 2:
                out_image_list.append(img_cpu.unsqueeze(-1).repeat(1, 1, 3))
        user_prompt_input = kwargs.get("user_prompt", "")
        if user_prompt_input and isinstance(user_prompt_input, str) and user_prompt_input.strip():
            custom_prompt = user_prompt_input.strip()
        else:
            custom_prompt = kwargs["custom_prompt"].strip()
        selected_preset = kwargs.get("preset_prompt", "None")
        prompt_enhancer = kwargs.get("prompt_enhancer", "None")
        sys_prompt_input = kwargs.get("sys_prompt", "")
        if sys_prompt_input and isinstance(sys_prompt_input, str) and sys_prompt_input.strip():
            system_prompt = sys_prompt_input.strip()
        elif selected_preset != "None":
            system_prompt = PRESET_PROMPTS.get(selected_preset, kwargs.get("system_prompt", ""))
        else:
            system_prompt = kwargs.get("system_prompt", "你是一个AI助手，请根据用户需求，输出对应内容。").strip()
        if prompt_enhancer != "None" and prompt_enhancer in ENHANCER_PROMPTS:
            enhancer_template = ENHANCER_PROMPTS[prompt_enhancer]
            user_input_text = custom_prompt if custom_prompt else "描述内容"
            if "{prompt}" in enhancer_template:
                user_prompt = enhancer_template.replace("{prompt}", user_input_text)
            else:
                user_prompt = enhancer_template + "\n" + user_input_text
        else:
            if selected_preset != "None" and not custom_prompt:
                user_prompt = "请严格按照你的系统角色设定和排版规则，处理当前提供的画面。"
            else:
                user_prompt = custom_prompt if custom_prompt else "请根据图片进行详细描述。"
        if not enable_llm_inference:
            images_list = []
            raw_sources = []
            processed_images = []
            any_media = None
            if force_unload or not kwargs.get("keep_model_in_vram", True):
                print("[XXBuHuo] 显存卸载...")
                gc.collect()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                    torch.cuda.ipc_collect()
                if 'omni_engine' in locals() and omni_engine is not None and isinstance(omni_engine, dict):
                    omni_engine.clear()
                omni_engine = None
                _GLOBAL_OMNI_CACHE.clear()
            return_payload = {"ui": {}}
            if len(any_media_ui_images) > 0:
                return_payload["ui"]["any_media_images"] = any_media_ui_images
            return {"ui": return_payload["ui"],
                    "result": (user_prompt, out_image_list, [user_prompt], media_passthrough, uid)}
        is_api = omni_engine.get("mode") == "api"
        has_vision = omni_engine.get("has_vision", False)
        vision_type = omni_engine.get("vision_type", "")
        batch_size = len(images_list)
        if batch_size > 0 and not has_vision: batch_size, images_list = 0, []
        base64_images = batch_tensors_to_base64(processed_images, image_max_size_val)
        is_qwen = vision_type in ["Qwen3.5-VL", "Qwen3.6-VL"]
        json_output = kwargs.get("json_output", False)
        enable_physical_block = kwargs.get("enable_physical_block", True)
        if json_output:
            json_instruction = (
                "\n\n==================================\n"
                "【强制 JSON 输出协议 (ComfyUI 标准版)】\n"
                "你当前处于机器接口模式，你的所有回复必须且只能是一个合法的 JSON 对象！\n"
                "绝不允许输出任何开场白、解释说明，绝不允许使用 ```json 这样的 Markdown 标记包裹！\n"
                "请严格结合用户指令与画面内容，按照以下标准结构进行输出。\n"
                "（注意：如果用户只问了简单的问答题，请将直接答案填入 summary，其余字段根据画面合理推测或留空即可）：\n"
                "{\n"
                '  "core_subject": "核心主体描述（例如：人物、动物的外貌、穿搭和特征）",\n'
                '  "scene": "场景与环境描述（例如：室内外背景、时间和天气）",\n'
                '  "action": "动作与姿态描述（例如：站立、奔跑、微表情、交互动作）",\n'
                '  "style": "艺术与视觉风格（例如：写实摄影、日系胶片风、3D渲染、8K高清）",\n'
                '  "lighting": "光影与色调（例如：侧逆光、柔和漫射光、丁达尔效应、暖金色调）",\n'
                '  "composition": "构图与镜头（例如：中景构图、主体居中、浅景深、焦外虚化）",\n'
                '  "color_palette": "画面主色调（例如：暖白色、橘色、低饱和度）",\n'
                '  "negative_prompt": "推测的负面提示词（例如：模糊, 低分辨率, 畸形, 噪点, 水印, 过曝），请输出为以逗号分隔的单行字符串",\n'
                '  "summary": "针对用户提问的直接回答，或是对整个画面的完整自然语言总结"\n'
                "}\n"
                "=================================="
            )
        else:
            json_instruction = ""
        anti_cot_instruction = ""
        if enable_physical_block:
            anti_cot_instruction = "\n[格式指令]: 请直接输出最终的描述结果。严禁添加任何开场白、结尾说明、以及诸如“Note:”、“注意：”之类的废话。"
        else:
            anti_cot_instruction = "\n[CRITICAL DIRECTIVE]: 即使你开启了内部深度思考，你的最终输出也必须极其详细、精准，绝不能偏离或遗漏我的核心指令！"
        system_prompt = system_prompt + anti_cot_instruction + json_instruction
        system_block = ""
        save_chat_history = kwargs["save_chat_history"]
        messages = _GLOBAL_OMNI_CACHE.get_messages(uid) if (
                save_chat_history and _GLOBAL_OMNI_CACHE.get_sys_prompt(uid) == system_prompt) else []
        _GLOBAL_OMNI_CACHE.set_sys_prompt(uid, system_prompt)
        if len(messages) == 0:
            if vision_type != "Gemma4": messages.append({"role": "system", "content": system_prompt})

        def build_content_payload(text_prompt, b64_list, is_video_flow=False):
            content = []
            if vision_type == "Gemma4":
                img_tags = ("<image>\n" * len(b64_list)) if b64_list else ""
                text_prompt = system_prompt + "\n\n【用户指令】:\n" + img_tags + text_prompt
                if enable_physical_block: text_prompt += "\n<|channel>output<channel|>"
            if is_qwen: text_prompt = "【用户指令】：\n" + text_prompt
            if b64_list:
                if is_video_flow and len(b64_list) > 1:
                    time_directive = "【动态视频上下文】：以下是一段视频的连续抽帧画面。请将它们视作一个完整的动态视频，直接输出连贯、流畅的动作与场景描述，无需逐帧分段说明，也不要提及“第一幅图”、“下一帧”。请严格遵循用户的具体指令。\n\n"
                    content.append({"type": "text", "text": time_directive})
                for b64 in b64_list:
                    content.append({"type": "image_url", "image_url": {"url": b64}})
                content.append({"type": "text", "text": text_prompt})
            else:
                content.append({"type": "text", "text": text_prompt})
            return content

        stream_to_console = kwargs["stream_to_console"]

        def process_inference(content_list, current_messages):
            current_messages.append({"role": "user", "content": content_list})
            max_tokens_val = int(kwargs.get("max_tokens", 1024))
            temperature_val = float(kwargs.get("temperature", 0.8))
            top_p_val = float(kwargs.get("top_p", 0.95))
            repeat_penalty_val = float(kwargs.get("repeat_penalty", 1.1))
            if is_api:
                import urllib.error
                api_url_input = omni_engine["api_url"].strip().rstrip("/")
                api_model_lower = omni_engine["api_model"].lower()
                is_image_task = "/images/" in api_url_input or \
                                any(kw in api_model_lower for kw in ["flux", "dalle", "sd", "image", "mj"])
                known_endpoints = ["/chat/completions", "/images/generations", "/images/edits", "/images/variations",
                                   "/responses",
                                   "/api/chat", "/completions"]
                if any(api_url_input.endswith(ep) for ep in known_endpoints):
                    api_url = api_url_input
                else:
                    if is_image_task:
                        api_url = api_url_input + "/images/generations"
                    else:
                        api_url = api_url_input + "/chat/completions"
                if is_image_task:
                    prompt_text = ""
                    base64_image_data = None
                    for item in content_list:
                        if isinstance(item, dict):
                            if item.get("type") == "text":
                                prompt_text += item.get("text", "")
                            elif item.get("type") == "image_url":
                                base64_image_data = item.get("image_url", {}).get("url", "")
                    prompt_text = prompt_text.replace("【用户指令】：\n", "").strip()[:1000]
                    prompts_to_run = [p.strip() for p in prompt_text.split("|||") if p.strip()]
                    if not prompts_to_run: prompts_to_run = ["A visually stunning image"]
                    multi_tensors = [None] * len(prompts_to_run)
                    multi_texts = [None] * len(prompts_to_run)
                    api_img_size = kwargs.get("api_img_size", "1024x1024").strip().replace("*", "x").lower()
                    api_img_quality = kwargs.get("api_img_quality", "standard")
                    api_img_style = kwargs.get("api_img_style", "vivid")
                    api_timeout = int(kwargs.get("api_timeout", 300))

                    def fetch_single_image(idx, single_prompt):
                        import time
                        import re
                        raw_size = str(kwargs.get("api_img_size", "1024x1024"))
                        clean_size = re.sub(r'\s+', '', raw_size)
                        clean_size = re.sub(r'[*X×]', 'x', clean_size, flags=re.IGNORECASE)
                        if clean_size != "auto" and not re.match(r'^\d+x\d+$', clean_size):
                            clean_size = "1024x1024"
                        local_img_size = clean_size
                        local_img_quality = kwargs.get("api_img_quality", "standard")
                        local_img_style = kwargs.get("api_img_style", "vivid")
                        local_timeout = int(kwargs.get("api_timeout", 300))
                        img_info_str = f"尺寸: {local_img_size} | 画质: {local_img_quality} | 风格: {local_img_style}"
                        if idx > 0:
                            delay = idx * 1.5 + random.uniform(0.1, 0.6)
                            time.sleep(delay)
                        data = {
                            "model": omni_engine["api_model"],
                            "prompt": single_prompt,
                            "n": 1,
                            "size": local_img_size,
                            "quality": local_img_quality,
                            "style": local_img_style
                        }
                        if base64_image_data:
                            data["image"] = base64_image_data
                            data["init_image"] = base64_image_data
                        req_headers = {
                            "Content-Type": "application/json",
                            "Authorization": f"Bearer {omni_engine['api_key']}",
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                        }
                        current_download_url = None
                        try:
                            print(f"\n[XXBuHuo] [并发线程 {idx + 1}] 发送指令...")
                            response = requests.post(api_url, json=data, headers=req_headers, timeout=local_timeout)
                            response.raise_for_status()
                            response_data = response.json()
                            img_data_obj = response_data.get("data", [{}])[0]
                            if "b64_json" in img_data_obj:
                                image_data = base64.b64decode(img_data_obj["b64_json"])
                                from io import BytesIO
                                pil_img = Image.open(BytesIO(image_data)).convert("RGB")
                                success_msg = f"图 {idx + 1} 生成成功\n{img_info_str}\n获取方式: Base64底层直传解析"
                                return idx, torch.from_numpy(np.array(pil_img)).float() / 255.0, success_msg
                            elif "url" in img_data_obj:
                                current_download_url = img_data_obj["url"]
                                print(f"[XXBuHuo] [并发线程 {idx + 1}] 开始下载: {current_download_url}")
                                img_res = requests.get(current_download_url, headers={'User-Agent': 'Mozilla/5.0'},
                                                       timeout=120)
                                img_res.raise_for_status()
                                from io import BytesIO
                                pil_img = Image.open(BytesIO(img_res.content)).convert("RGB")
                                success_msg = f"图 {idx + 1} 生成成功\n{img_info_str}\n下载地址: {current_download_url}"
                                return idx, torch.from_numpy(np.array(pil_img)).float() / 255.0, success_msg
                            else:
                                err_msg = f"图 {idx + 1} 生成失败\n原因: API 返回值格式异常，未找到图像链接。\n原始反馈: {str(img_data_obj)}"
                                print(f"\n[XXBuHuo] {err_msg}")
                                return idx, None, err_msg
                        except requests.exceptions.RequestException as e:
                            err_detail = str(e)
                            if hasattr(e, 'response') and e.response is not None:
                                try:
                                    err_text = e.response.text
                                    if "<html" in err_text.lower():
                                        import re
                                        title_match = re.search(r'<title>(.*?)</title>', err_text, re.IGNORECASE)
                                        if title_match:
                                            err_detail += f"\n服务器反馈: [网关/代理拦截] {title_match.group(1).strip()}"
                                        else:
                                            err_detail += f"\n服务器反馈: [网关/代理拦截] 接口返回了无效的 HTML 错误页面。"
                                    else:
                                        err_detail += f"\n服务器反馈: {err_text}"
                                except:
                                    pass
                            err_msg = f"图 {idx + 1} 生成失败\n网络或接口报错: {err_detail}"
                            if current_download_url:
                                err_msg += f"\n\n提示: 服务器已出图，但本地节点下载超时/崩溃。\n您可以尝试复制并在浏览器中手动下载:\n链接: {current_download_url}"
                            print(f"\n[XXBuHuo] {err_msg}")
                            return idx, None, err_msg
                        except Exception as e:
                            err_msg = f"图 {idx + 1} 生成失败\n系统解析崩溃: {str(e)}"
                            if current_download_url:
                                err_msg += f"\n\n提示: 图像已生成，但在转码期间崩溃。\n链接: {current_download_url}"
                            print(f"\n[XXBuHuo] {err_msg}")
                            return idx, None, err_msg

                    from concurrent.futures import ThreadPoolExecutor
                    with ThreadPoolExecutor(max_workers=min(8, len(prompts_to_run))) as executor:
                        futures = [executor.submit(fetch_single_image, i, p) for i, p in enumerate(prompts_to_run)]
                        for future in futures:
                            idx, tensor, text = future.result()
                            if tensor is not None:
                                multi_tensors[idx] = tensor
                            multi_texts[idx] = text
                    valid_tensors = [t for t in multi_tensors if t is not None]
                    if valid_tensors:
                        batch_tensors = [t.unsqueeze(0) if t.dim() == 3 else t for t in valid_tensors]
                        final_tensor = torch.cat(batch_tensors, dim=0)
                        return {"is_image_result": True, "tensor": final_tensor,
                                "text": "\n\n----------------------------\n\n".join(multi_texts)}
                    else:
                        fail_text = "\n\n----------------------------\n\n".join(multi_texts)
                        return {"is_image_result": True, "tensor": torch.zeros((1, 64, 64, 3)),
                                "text": f"【图像全部生成失败】\n\n{fail_text}"}
                else:
                    api_model_val = omni_engine.get("api_model", "").strip()
                    if not api_model_val:
                        return "[前端同步丢失]: '模型名称' 传到后端变成空了！请在节点面板里把模型名字剪切掉、再重新粘贴一次，并在面板外面点一下鼠标以确认保存。"
                    api_timeout = int(kwargs.get("api_timeout", 300))
                    data = {
                        "model": api_model_val,
                        "messages": current_messages,
                        "stream": stream_to_console
                    }
                    if json_output: data["response_format"] = {"type": "json_object"}
                    req_headers = {
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {omni_engine['api_key']}"
                    }
                    try:
                        print(f"\n[XXBuHuo] 正在向 {api_url} 发送请求 | 模型: [{api_model_val}]")
                        response = requests.post(api_url, json=data, headers=req_headers, timeout=api_timeout,
                                                 stream=stream_to_console)
                        response.raise_for_status()
                        response.encoding = "utf-8"
                        if stream_to_console:
                            print(f"\n[XXBuHuo] 云端API推理: ", end="", flush=True)
                            full_ans = ""
                            for line in response.iter_lines(decode_unicode=True):
                                if line and line.startswith("data: ") and line != "data: [DONE]":
                                    try:
                                        chunk = json.loads(line[6:])
                                        if "content" in chunk["choices"][0]["delta"] and chunk["choices"][0]["delta"][
                                            "content"] is not None:
                                            text = chunk["choices"][0]["delta"]["content"]
                                            if text:
                                                full_ans += text
                                                print(text, end="", flush=True)
                                    except:
                                        pass
                            print("\n")
                            ans = full_ans
                        else:
                            res_json = response.json()
                            ans = res_json["choices"][0]["message"]["content"]
                        ans = re.sub(r"<think>.*?</think>", "", ans, flags=re.DOTALL).strip()
                        return ans if ans else "[空]"
                    except requests.exceptions.HTTPError as e:
                        try:
                            err_msg = e.response.json()
                        except:
                            err_msg = e.response.text
                        return f"[对话API被拒绝]: HTTP {e.response.status_code} - {err_msg}"
                    except Exception as e:
                        return f"[对话API崩溃]: {str(e)}"
            else:
                llm = omni_engine["llm"]
                _重置llm推理状态(llm, vision_type)
                if vision_type in ["Qwen3.5-VL", "Qwen3.6-VL"]:
                    if hasattr(llm, "chat_handler") and llm.chat_handler is not None:
                        llm.chat_handler.enable_thinking = not enable_physical_block
                params = {"max_tokens": max_tokens_val, "temperature": temperature_val, "top_p": top_p_val,
                          "repeat_penalty": repeat_penalty_val, "seed": target_seed}
                if enable_physical_block:
                    try:
                        ban_tokens = []
                        if vision_type == "Gemma4":
                            t1 = llm.tokenize(b"<|channel>", add_bos=False, special=True)
                            t2 = llm.tokenize(b" <|channel>", add_bos=False, special=True)
                            ban_tokens.extend(t1 if t1 else (t2 if t2 else []))
                        elif vision_type in ["Qwen3.5-VL", "Qwen3.6-VL"]:
                            t1 = llm.tokenize(b"<think>", add_bos=False, special=True)
                            t2 = llm.tokenize(b" <think>", add_bos=False, special=True)
                            t3 = llm.tokenize(b"<|thought|>", add_bos=False, special=True)
                            t4 = llm.tokenize(b" <|thought|>", add_bos=False, special=True)
                            ban_tokens.extend(t1 + t2 + t3 + t4)
                        if ban_tokens:
                            params["logit_bias"] = {int(tok): -100.0 for tok in set(ban_tokens)}
                    except:
                        pass
                params["stream"] = stream_to_console
                import time
                prompt_start_time = time.time()
                first_token_time = None
                if stream_to_console:
                    import sys
                    print(f"\n[XXBuHuo] AI推理: ", end="", flush=True)
                    ans = ""
                    for chunk in llm.create_chat_completion(messages=current_messages, **params):
                        if first_token_time is None:
                            first_token_time = time.time()
                        delta = chunk["choices"][0].get("delta", {})
                        if "content" in delta and delta["content"] is not None:
                            piece = delta["content"]
                            print(piece, end="", flush=True)
                            ans += piece
                    print()
                    end_time = time.time()
                    token_count = len(llm.tokenize(ans.encode("utf-8"), add_bos=False, special=True))
                    ttft = first_token_time - prompt_start_time if first_token_time else 0
                    decode_time = end_time - first_token_time if first_token_time else 0
                    speed = token_count / decode_time if decode_time > 0 else 0
                    print(
                        f"[XXBuHuo] 性能剖析: 提示词读取 {ttft:.2f}秒 | 纯生成 {token_count} Tokens | 解码耗时 {decode_time:.2f}秒 | 真实速度 {speed:.2f} Tokens/s")
                else:
                    res_obj = llm.create_chat_completion(messages=current_messages, **params)
                    end_time = time.time()
                    ans = res_obj["choices"][0]["message"]["content"]
                    token_count = res_obj.get("usage", {}).get("completion_tokens", 0)
                    if token_count <= 0:
                        token_count = len(llm.tokenize(ans.encode("utf-8"), add_bos=False, special=True))
                    total_time = end_time - prompt_start_time
                    speed = token_count / total_time if total_time > 0 else 0
                    print(
                        f"[XXBuHuo] 性能剖析: 综合耗时 {total_time:.2f}秒 | 生成 {token_count} Tokens | 综合速度 {speed:.2f} Tokens/s (非流式无法测算首字延迟)")
                if vision_type == "Gemma4":
                    if "<|channel>thought" in ans: ans = re.sub(r"<\|channel>.*?<channel\|>", "", ans,
                                                                flags=re.DOTALL).strip()
                    ans = re.sub(r"<start_of_turn>.*?<end_of_turn>", "", ans, flags=re.DOTALL).strip()
                    ans = re.sub(r"<\|.*?\|>", "", ans).strip()
                    ans = re.sub(r"（自我检查.*?）", "", ans, flags=re.DOTALL).strip()
                    ans = re.sub(r"\(自我检查.*?\)", "", ans, flags=re.DOTALL).strip()
                    ans = re.sub(r"\n\s*\n", "\n", ans).strip()
                elif vision_type in ["Qwen3.5-VL", "Qwen3.6-VL"]:
                    if "</think>" in ans:
                        ans = re.sub(r"^.*?</think>", "", ans, flags=re.DOTALL).strip()
                    elif "</|thought|>" in ans:
                        ans = re.sub(r"^.*?</\|thought\|>", "", ans, flags=re.DOTALL).strip()
                    ans = re.sub(r"<think>.*", "", ans, flags=re.DOTALL).strip()
                    ans = re.sub(r"\n\s*\n", "\n", ans).strip()
                ans = re.sub(r"(?i)\n\s*\*\*Note\*\*.*", "", ans, flags=re.DOTALL).strip()
                ans = re.sub(r"(?i)\n\s*Note:.*", "", ans, flags=re.DOTALL).strip()
                ans = re.sub(r"\n\s*注意：.*", "", ans, flags=re.DOTALL).strip()
                return ans if ans else "[推理无结果，请检查模型和提示词]"

        final_responses = []
        full_text_prompt = user_prompt
        if input_mode == "文本推理" or batch_size == 0:
            res = process_inference(build_content_payload(full_text_prompt, [], is_video_flow=False), messages)
            final_responses.append(res)
        elif input_mode == "视频推理":
            print(f"[XXBuHuo] 视频推理：正在融合 {len(base64_images)} 帧动态画面...")
            res = process_inference(build_content_payload(full_text_prompt, base64_images, is_video_flow=True),
                                    messages)
            final_responses.append(res)
        elif input_mode == "宫格推理":
            try:
                if '*' in grid_param:
                    rows, cols = map(int, grid_param.split('*'))
                elif 'x' in grid_param:
                    rows, cols = map(int, grid_param.split('x'))
                else:
                    rows = cols = int(grid_param)
            except:
                rows = cols = 3
            print(f"[XXBuHuo] 宫格推理：正在执行 {rows}行 x {cols}列 图像切分...")
            final_base64_for_story = []
            for img_t in images_list:
                cells = split_grid_image(img_t, rows=rows, cols=cols)
                cell_b64s = batch_tensors_to_base64(cells, image_max_size_val)
                final_base64_for_story.extend(cell_b64s)
            story_protocol = (
                f"\n\n【宫格分镜叙事协议】：\n"
                f"你当前收到的是一组从 {rows}x{cols} 宫格图中提取的连续分镜画面。\n"
                "请你严格按照画面的物理排列顺序（从左到右，从上到下）观察每一格的细微变化。\n"
                "你的任务是将这些孤立的画面碎片，编织成一个逻辑完整、情节连贯的故事或动作过程描述。\n"
                "⛔ 绝对禁止使用'第一幅图'、'第二格'等逐图编号描述方式！请直接输出流畅的叙事文本。"
            )
            res = process_inference(
                build_content_payload(full_text_prompt + story_protocol, final_base64_for_story, is_video_flow=True),
                messages)
            final_responses.append(res)
        elif input_mode == "逐帧推理":
            for i, b64 in enumerate(base64_images):
                print(f"[XXBuHuo] 逐帧推理进度: {i + 1}/{len(base64_images)}...")
                res = process_inference(build_content_payload(full_text_prompt, [b64], is_video_flow=False),
                                        messages.copy())
                final_responses.append(res)
        images_list = [];
        base64_images = [];
        raw_sources = [];
        processed_images = [];
        any_media = None
        gc.collect()
        if torch.cuda.is_available(): torch.cuda.empty_cache(); torch.cuda.ipc_collect()
        if force_unload or not kwargs["keep_model_in_vram"]:
            if omni_engine is not None and isinstance(omni_engine, dict): omni_engine.clear()
            omni_engine = None;
            _GLOBAL_OMNI_CACHE.clear()
        actual_list_output = []
        extracted_api_images = []
        for r in final_responses:
            if isinstance(r, dict) and r.get("is_image_result"):
                t = r["tensor"]
                if t.dim() == 3: t = t.unsqueeze(0)
                extracted_api_images.append(t)
                actual_list_output.append(r["text"])
            elif isinstance(r, str):
                if "|||" in r:
                    parts = [p.strip() for p in r.split("|||") if p.strip()]
                    actual_list_output.extend(parts)
                else:
                    actual_list_output.append(r)
        if extracted_api_images:
            out_image_list = torch.cat(extracted_api_images, dim=0).cpu()
        else:
            is_empty = False
            if out_image_list is None:
                is_empty = True
            elif isinstance(out_image_list, list) and len(out_image_list) == 0:
                is_empty = True
            if is_empty:
                out_image_list = torch.zeros((1, 64, 64, 3), dtype=torch.float32)
        final_output = "\n\n".join(actual_list_output) if actual_list_output else user_prompt
        final_output_list = actual_list_output if actual_list_output else [user_prompt]
        return_payload = {"ui": {}}
        if len(any_media_ui_images) > 0:
            return_payload["ui"]["any_media_images"] = any_media_ui_images
        return {"ui": return_payload["ui"],
                "result": (final_output, out_image_list, final_output_list, media_passthrough, uid)}


class XXBuHuoImageCombiner:
    INPUT_IS_LIST = True

    @classmethod
    def INPUT_TYPES(s):
        optional_inputs = {f"image_{i}": ("IMAGE",) for i in range(1, 100)}
        return {
            "required": {
                "input_count": ("INT", {"default": 1, "min": 1, "max": 99, "step": 1}),
                "update_inputs": ("BOOLEAN", {"default": False}),
            },
            "optional": optional_inputs,
            "hidden": {"unique_id": "UNIQUE_ID"}
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    OUTPUT_IS_LIST = (False,)
    OUTPUT_NODE = False
    FUNCTION = "combine_images"
    CATEGORY = "XXBuHuo"

    def combine_images(self, input_count, update_inputs, unique_id=None, **kwargs):
        import torch
        images = []
        for i in range(1, 100):
            key = f"image_{i}"
            if key in kwargs:
                items = kwargs[key]
                if items is None:
                    continue

                def flatten_extract(data):
                    if isinstance(data, list):
                        for item in data:
                            flatten_extract(item)
                    elif isinstance(data, torch.Tensor):
                        images.append(data)

                flatten_extract(items)
        if not images:
            return ([torch.zeros((64, 64, 3))],)
        final_list = []
        for img in images:
            if img.dim() == 4:
                for b in range(img.shape[0]):
                    final_list.append(img[b])
            elif img.dim() == 3:
                final_list.append(img)
            elif img.dim() == 2:
                final_list.append(img.unsqueeze(-1).repeat(1, 1, 3))
        return (final_list,)


class XXBuHuoImageSplitter:
    INPUT_IS_LIST = True

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "output_count": ("INT", {"default": 1, "min": 1, "max": 99, "step": 1}),
                "update_outputs": ("BOOLEAN", {"default": False}),
            },
            "optional": {"image": ("IMAGE",), },
            "hidden": {"unique_id": "UNIQUE_ID"}
        }

    RETURN_TYPES = tuple(["IMAGE"] * 99)
    OUTPUT_IS_LIST = tuple([False] * 99)
    OUTPUT_NODE = False
    FUNCTION = "split_images"
    CATEGORY = "XXBuHuo"

    def split_images(self, output_count, update_outputs, image=None, unique_id=None):
        count = output_count[0] if isinstance(output_count, list) else output_count
        images = []
        if image is not None:
            for item in image:
                if isinstance(item, list):
                    for sub in item:
                        if isinstance(sub, torch.Tensor):
                            for i in range(sub.shape[0]): images.append(sub[i:i + 1])
                elif isinstance(item, torch.Tensor):
                    for i in range(item.shape[0]): images.append(item[i:i + 1])
        results = []
        for i in range(99):
            if i < len(images):
                results.append(images[i])
            else:
                results.append(torch.zeros((1, 16, 16, 3)))
        return tuple(results)


class XXBuHuoImageListToBatch:
    INPUT_IS_LIST = True

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "any_input": (ANY,),
                "start_frame": ("INT", {"default": 1, "min": 1, "max": 999999}),
                "end_frame": ("INT", {"default": -1, "min": -1, "max": 999999}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image_batch",)
    OUTPUT_IS_LIST = (False,)
    FUNCTION = "convert"
    CATEGORY = "XXBuHuo"

    def convert(self, any_input, start_frame, end_frame):
        import torch
        import numpy as np
        s_idx = (start_frame[0] if isinstance(start_frame, list) else start_frame) - 1
        e_idx = end_frame[0] if isinstance(end_frame, list) else end_frame
        all_frames = []
        for item in any_input:
            try:
                descriptors = parse_any_media_to_descriptors(item)
                for desc in descriptors:
                    if desc["type"] == "video_path":
                        video_frames = extract_video_frames(desc["path"], -1)
                        all_frames.extend(video_frames)
                    elif desc["type"] == "image_path":
                        try:
                            img = load_image_with_orientation(desc["path"])
                            all_frames.append(torch.from_numpy(np.array(img)).float() / 255.0)
                        except:
                            pass
                    elif desc["type"] == "tensor":
                        t = desc["data"]
                        for i in range(t.shape[0] if t.dim() == 4 else 1):
                            all_frames.append(t[i] if t.dim() == 4 else t)
            except Exception:
                if isinstance(item, torch.Tensor):
                    for i in range(item.shape[0] if item.dim() == 4 else 1):
                        all_frames.append(item[i] if item.dim() == 4 else item)
        if not all_frames:
            return ([torch.zeros((64, 64, 3))],)
        if e_idx == -1 or e_idx >= len(all_frames):
            sliced = all_frames[s_idx:]
        else:
            sliced = all_frames[s_idx: e_idx]
        if not sliced:
            sliced = [all_frames[0]]
        final_list = []
        for img in sliced:
            if img.dim() == 4:
                for b in range(img.shape[0]):
                    final_list.append(img[b])
            elif img.dim() == 3:
                final_list.append(img)
            elif img.dim() == 2:
                final_list.append(img.unsqueeze(-1).repeat(1, 1, 3))
        return (final_list,)


class XXBuHuoImageBatchToList:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "any_input": (ANY,),
                "start_frame": ("INT", {"default": 1, "min": 1, "max": 999999}),
                "end_frame": ("INT", {"default": -1, "min": -1, "max": 999999}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image_list",)
    OUTPUT_IS_LIST = (True,)
    FUNCTION = "convert"
    CATEGORY = "XXBuHuo"

    def convert(self, any_input, start_frame, end_frame):
        all_frames = []
        descriptors = parse_any_media_to_descriptors(any_input)
        for desc in descriptors:
            if desc["type"] == "video_path":
                video_frames = extract_video_frames(desc["path"], -1)
                all_frames.extend(video_frames)
            elif desc["type"] == "tensor":
                t = desc["data"]
                for i in range(t.shape[0] if t.dim() == 4 else 1):
                    all_frames.append(t[i] if t.dim() == 4 else t)
        if not all_frames:
            return ([torch.zeros((1, 64, 64, 3))],)
        s_idx = start_frame - 1
        if end_frame == -1 or end_frame >= len(all_frames):
            sliced = all_frames[s_idx:]
        else:
            sliced = all_frames[s_idx: end_frame]
        if not sliced: sliced = [all_frames[0]]
        return ([t.unsqueeze(0) if t.dim() == 3 else t for t in sliced],)


class XXBuHuoTextSplitter:
    INPUT_IS_LIST = True

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "output_count": ("INT", {"default": 1, "min": 1, "max": 99, "step": 1}),
                "update_outputs": ("BOOLEAN", {"default": False}),
            },
            "optional": {"text_list": ("STRING", {"forceInput": True}), },
            "hidden": {"unique_id": "UNIQUE_ID"}
        }

    RETURN_TYPES = tuple(["STRING"] * 99)
    OUTPUT_IS_LIST = tuple([False] * 99)
    OUTPUT_NODE = False
    FUNCTION = "split_texts"
    CATEGORY = "XXBuHuo"

    def split_texts(self, output_count, update_outputs, text_list=None, unique_id=None):
        count = output_count[0] if isinstance(output_count, list) else output_count
        texts = []
        if text_list is not None:
            for item in text_list:
                if isinstance(item, list):
                    for sub in item:
                        if sub is not None: texts.append(str(sub))
                elif item is not None:
                    texts.append(str(item))
        results = []
        for i in range(99):
            if i < len(texts):
                results.append(texts[i])
            else:
                results.append("")
        return tuple(results)


class XXBuHuoGridSplitter:
    INPUT_IS_LIST = True

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "grid_pattern": ("STRING", {"default": "2*2"}),
            },
            "optional": {"image": ("IMAGE",), },
            "hidden": {"unique_id": "UNIQUE_ID"}
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    OUTPUT_IS_LIST = (False,)
    OUTPUT_NODE = False
    FUNCTION = "split_grid"
    CATEGORY = "XXBuHuo"

    def split_grid(self, grid_pattern, image=None, unique_id=None):
        import torch
        import re
        pattern = grid_pattern[0] if isinstance(grid_pattern, list) else grid_pattern
        try:
            parts = re.split(r'[*xX×,，]', str(pattern))
            rows = int(parts[0].strip())
            cols = int(parts[1].strip()) if len(parts) > 1 else rows
        except:
            rows = cols = 2
        all_splits = []
        if image is not None:
            input_images = []

            def flatten_image(obj):
                if isinstance(obj, (list, tuple)):
                    for item in obj:
                        flatten_image(item)
                elif isinstance(obj, torch.Tensor):
                    if obj.dim() == 4:
                        for i in range(obj.shape[0]): input_images.append(obj[i])
                    elif obj.dim() == 3:
                        input_images.append(obj)
                    elif obj.dim() == 2:
                        input_images.append(obj.unsqueeze(-1).repeat(1, 1, 3))

            flatten_image(image)
            for img in input_images:
                h, w, c = img.shape
                cell_h = h // rows
                cell_w = w // cols
                for r in range(rows):
                    for c_idx in range(cols):
                        y_start = r * cell_h
                        y_end = y_start + cell_h
                        x_start = c_idx * cell_w
                        x_end = x_start + cell_w
                        crop = img[y_start:y_end, x_start:x_end, :]
                        all_splits.append(crop.unsqueeze(0))
        if len(all_splits) == 0:
            return (torch.zeros((1, 16, 16, 3)),)
        batch_tensor = torch.cat(all_splits, dim=0)
        return (batch_tensor,)


class XXBuHuoGridCombiner:
    INPUT_IS_LIST = True

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "grid_pattern": ("STRING", {"default": "2*2"}),
            },
            "optional": {"image": ("IMAGE",), },
            "hidden": {"unique_id": "UNIQUE_ID"}
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    OUTPUT_IS_LIST = (False,)
    FUNCTION = "combine_grid"
    CATEGORY = "XXBuHuo"

    def combine_grid(self, grid_pattern, image=None, unique_id=None):
        import torch
        import re
        pattern = grid_pattern[0] if isinstance(grid_pattern, list) else grid_pattern
        try:
            parts = re.split(r'[*xX×,，]', str(pattern))
            rows = int(parts[0].strip())
            cols = int(parts[1].strip()) if len(parts) > 1 else rows
        except:
            rows = cols = 2
        if image is None:
            return (torch.zeros((1, 64, 64, 4)),)
        all_imgs = []

        def flatten_image(obj):
            if isinstance(obj, (list, tuple)):
                for item in obj:
                    flatten_image(item)
            elif isinstance(obj, torch.Tensor):
                if obj.dim() == 4:
                    for i in range(obj.shape[0]):
                        all_imgs.append(obj[i])
                elif obj.dim() == 3:
                    all_imgs.append(obj)
                elif obj.dim() == 2:
                    all_imgs.append(obj.unsqueeze(-1))

        flatten_image(image)
        if not all_imgs:
            return (torch.zeros((1, 64, 64, 4)),)
        max_h = max(img.shape[0] for img in all_imgs)
        max_w = max(img.shape[1] for img in all_imgs)
        uniform_imgs = []
        for img in all_imgs:
            h, w, c = img.shape
            if c == 1:
                img_rgb = img.repeat(1, 1, 3)
                alpha = torch.ones((h, w, 1), dtype=img.dtype, device=img.device)
                img = torch.cat([img_rgb, alpha], dim=-1)
            elif c == 3:
                alpha = torch.ones((h, w, 1), dtype=img.dtype, device=img.device)
                img = torch.cat([img, alpha], dim=-1)
            elif c > 4:
                img = img[..., :4]
            if h == max_h and w == max_w:
                uniform_imgs.append(img)
            else:
                canvas = torch.zeros((max_h, max_w, 4), dtype=img.dtype, device=img.device)
                y_offset = (max_h - h) // 2
                x_offset = (max_w - w) // 2
                canvas[y_offset:y_offset + h, x_offset:x_offset + w, :] = img
                uniform_imgs.append(canvas)
        num_needed = rows * cols
        imgs_to_use = uniform_imgs[:num_needed]
        while len(imgs_to_use) < num_needed:
            imgs_to_use.append(
                torch.zeros((max_h, max_w, 4), dtype=uniform_imgs[0].dtype, device=uniform_imgs[0].device))
        batch_tensor = torch.stack(imgs_to_use, dim=0)
        combined = batch_tensor.view(rows, cols, max_h, max_w, 4).permute(0, 2, 1, 3, 4).contiguous().view(1,
                                                                                                           rows * max_h,
                                                                                                           cols * max_w,
                                                                                                           4)
        return (combined,)


NODE_CLASS_MAPPINGS = {
    "XXBuHuoOmniNode": XXBuHuoOmniNode,
    "XXBuHuoImageSplitter": XXBuHuoImageSplitter,
    "XXBuHuoImageCombiner": XXBuHuoImageCombiner,
    "XXBuHuoImageListToBatch": XXBuHuoImageListToBatch,
    "XXBuHuoImageBatchToList": XXBuHuoImageBatchToList,
    "XXBuHuoTextSplitter": XXBuHuoTextSplitter,
    "XXBuHuoGridCombiner": XXBuHuoGridCombiner,
    "XXBuHuoGridSplitter": XXBuHuoGridSplitter
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "XXBuHuoOmniNode": "XXBuHuo llama AI",
    "XXBuHuoImageSplitter": "XXBuHuo 图像拆分",
    "XXBuHuoImageCombiner": "XXBuHuo 图像组合",
    "XXBuHuoImageListToBatch": "XXBuHuo 图像 List 转 Batch",
    "XXBuHuoImageBatchToList": "XXBuHuo 图像 Batch 转 List",
    "XXBuHuoTextSplitter": "XXBuHuo 文本分割器",
    "XXBuHuoGridCombiner": "XXBuHuo 宫格合成",
    "XXBuHuoGridSplitter": "XXBuHuo 宫格拆分"
}
