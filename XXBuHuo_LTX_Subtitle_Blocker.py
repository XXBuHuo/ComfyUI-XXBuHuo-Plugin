import torch
import re
import math
import nodes


class XXBuHuo_LTX_Subtitle_Blocker:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": ("MODEL",),
                "clip": ("CLIP",),
                "text": ("STRING", {"multiline": True, "forceInput": True}),
                "video_latent": ("LATENT",),
                "safe_zone_ratio": ("FLOAT", {"default": 0.70, "min": 0.4, "max": 0.95, "step": 0.05}),
                "debug_log": (["On", "Off"],),
            }
        }

    RETURN_TYPES = ("MODEL", "CONDITIONING")
    RETURN_NAMES = ("SPLIT_MODEL", "POSITIVE")
    FUNCTION = "apply_blocker"
    CATEGORY = "XXBuHuo/LTX_Video"

    def apply_blocker(self, model, clip, text, video_latent, safe_zone_ratio, debug_log):
        samples = video_latent.get("samples", None)
        if samples is None: raise ValueError("[XXBuHuo] Error: video_latent is empty!")
        vid_shape = samples.shape
        if len(vid_shape) == 5:
            lat_f, lat_h, lat_w = vid_shape[2], vid_shape[3], vid_shape[4]
        else:
            lat_f, lat_h, lat_w = 1, vid_shape[2], vid_shape[3]
        S_vid_base = lat_f * lat_h * lat_w
        real_text = text
        pattern1 = r'[^.,，。！？]*?(?:说|道|喊|问|讲|语|言|开口|声|呼|:|：)\s*["“”「」『』\'].*?(?:["“”「」『』\']|$)'
        fake_text = re.sub(pattern1, ' (is presenting naturally) ', text, flags=re.DOTALL)
        pattern2 = r'["“”「」『』\'].*?[\u4e00-\u9fa5].*?(?:["“”「」『』\']|$)'
        fake_text = re.sub(pattern2, ' (is presenting naturally) ', fake_text, flags=re.DOTALL)
        fake_text = re.sub(r'\s+', ' ', fake_text).strip()
        clip_encoder = nodes.CLIPTextEncode()
        cond_real = clip_encoder.encode(clip, real_text)[0]
        cond_fake = clip_encoder.encode(clip, fake_text)[0]
        cr_tensor, cr_dict = cond_real[0]
        cf_tensor, cf_dict = cond_fake[0]
        L_real = cr_tensor.shape[1]
        L_fake = cf_tensor.shape[1]
        L_total = L_real + L_fake
        split_cond_tensor = torch.cat([cr_tensor, cf_tensor], dim=1)
        split_cond_dict = cr_dict.copy()
        if "attention_mask" in cr_dict and "attention_mask" in cf_dict:
            split_cond_dict["attention_mask"] = torch.cat([cr_dict["attention_mask"], cf_dict["attention_mask"]],
                                                          dim=-1)
        m = model.clone()
        if debug_log == "On":
            print(f" -> Real Text (Upper/Audio): {real_text}")
            print(f" -> Fake Text (Bottom 30%): {fake_text}")
        hook_state = [-1, -1, lat_h, lat_w]

        def spatial_deception_attn2(q, k, v, extra_options):
            Seq_Q = q.shape[-2]
            Seq_K = k.shape[-2]
            if Seq_K != L_total or Seq_Q < S_vid_base:
                return q, k, v
            if hook_state[0] == -1: hook_state[0] = max(0, Seq_Q - S_vid_base)
            current_S_vid = Seq_Q - hook_state[0]
            if Seq_Q != hook_state[1]:
                hook_state[1] = Seq_Q
                if current_S_vid != S_vid_base:
                    A = current_S_vid // lat_f
                    R = lat_w / lat_h
                    new_h = max(1, int(round(math.sqrt(A / R))))
                    new_w = max(1, A // new_h)
                    hook_state[2], hook_state[3] = new_h, new_w
            curr_h, curr_w = hook_state[2], hook_state[3]
            mask = torch.zeros((1, 1, Seq_Q, Seq_K), dtype=q.dtype, device=q.device)
            cutoff_h = int(curr_h * safe_zone_ratio)
            applied = False
            for f in range(lat_f):
                frame_start = f * curr_h * curr_w
                bottom_start = frame_start + cutoff_h * curr_w
                frame_end = (f + 1) * curr_h * curr_w
                mask[:, :, frame_start:bottom_start, L_real:L_total] = -10000.0
                mask[:, :, bottom_start:frame_end, 0:L_real] = -10000.0
                applied = True
            if Seq_Q > current_S_vid:
                mask[:, :, current_S_vid:, L_real:L_total] = -10000.0
            if applied:
                if "attn_mask" in extra_options and extra_options["attn_mask"] is not None:
                    try:
                        extra_options["attn_mask"] = extra_options["attn_mask"] + mask
                    except:
                        extra_options["attn_mask"] = mask
                else:
                    extra_options["attn_mask"] = mask
            return q, k, v

        def modal_firewall_attn1(q, k, v, extra_options):
            Seq_Q = q.shape[-2]
            Seq_K = k.shape[-2]
            if Seq_Q != Seq_K or Seq_Q < S_vid_base: return q, k, v
            current_S_vid = Seq_Q - hook_state[0]
            if current_S_vid <= 0 or Seq_Q <= current_S_vid: return q, k, v
            curr_h, curr_w = hook_state[2], hook_state[3]
            mask = torch.zeros((1, 1, Seq_Q, Seq_K), dtype=q.dtype, device=q.device)
            cutoff_h = int(curr_h * safe_zone_ratio)
            applied = False
            for f in range(lat_f):
                frame_start = f * curr_h * curr_w
                bottom_start = frame_start + cutoff_h * curr_w
                frame_end = (f + 1) * curr_h * curr_w
                mask[:, :, bottom_start:frame_end, current_S_vid:] = -10000.0
                mask[:, :, current_S_vid:, bottom_start:frame_end] = -10000.0
                applied = True
            if applied:
                if "attn_mask" in extra_options and extra_options["attn_mask"] is not None:
                    try:
                        extra_options["attn_mask"] = extra_options["attn_mask"] + mask
                    except:
                        extra_options["attn_mask"] = mask
                else:
                    extra_options["attn_mask"] = mask
            return q, k, v

        m.set_model_attn2_patch(spatial_deception_attn2)
        m.set_model_attn1_patch(modal_firewall_attn1)
        return (m, [[split_cond_tensor, split_cond_dict]])


NODE_CLASS_MAPPINGS = {
    "XXBuHuo_LTX_Subtitle_Blocker": XXBuHuo_LTX_Subtitle_Blocker
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "XXBuHuo_LTX_Subtitle_Blocker": "XXBuHuoLTX字幕屏蔽"
}
