import re


class AnyType(str):
    def __ne__(self, __value: object) -> bool:
        return False


ANY = AnyType("*")


class XXBuHuo_NexusRouter:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "组数 (Groups)": ("INT", {"default": 1, "min": 1, "step": 1}),
                "端口 (Ports)": ("INT", {"default": 4, "min": 1, "step": 1}),
                "对齐 (Align)": (["Off", "On"], {"default": "Off"}),
                "激活 (Active)": ([f"Group {i}" for i in range(1, 100)],),
            },
            "hidden": {
                "prompt": "PROMPT",
                "unique_id": "UNIQUE_ID",
                "组名 (Name)": ("STRING", {"default": "Group 1", "multiline": True}),
            }
        }

    @classmethod
    def VALIDATE_INPUTS(cls, **kwargs):
        return True

    RETURN_TYPES = tuple(["XX_CTRL"] + ["*"] * 64)
    RETURN_NAMES = tuple(["CTRL"] + [f"Port {i}" for i in range(1, 65)])
    FUNCTION = "route_models"
    CATEGORY = "XXBuHuo/Routing"

    @classmethod
    def check_lazy_status(cls, **kwargs):
        needed_inputs = []
        raw_inputs = {}
        if "prompt" in kwargs and "unique_id" in kwargs:
            try:
                raw_inputs = kwargs["prompt"][kwargs["unique_id"]]["inputs"]
            except Exception:
                pass
        control_ports = ["组数 (Groups)", "激活 (Active)", "组名 (Name)", "端口 (Ports)", "对齐 (Align)"]
        for port in control_ports:
            if port in raw_inputs and isinstance(raw_inputs[port], list):
                if port not in kwargs:
                    needed_inputs.append(port)
        if needed_inputs:
            return needed_inputs
        exposed_groups = kwargs.get("组数 (Groups)", 1)
        active_group = str(kwargs.get("激活 (Active)", "Group 1")).strip()
        group_names_str = str(kwargs.get("组名 (Name)", ""))
        if not group_names_str and "prompt" in kwargs and "unique_id" in kwargs:
            try:
                if "组名 (Name)" in raw_inputs and isinstance(raw_inputs["组名 (Name)"], str):
                    group_names_str = str(raw_inputs["组名 (Name)"])
            except Exception:
                pass
        names_list = [s.strip() for s in re.split(r'[,，;；|\n]+', group_names_str) if s.strip()]
        selected_group_num = 1
        if active_group in names_list:
            selected_group_num = names_list.index(active_group) + 1
        else:
            match = re.search(r'(?i)group\s*(\d+)', active_group)
            if match:
                selected_group_num = int(match.group(1))
            else:
                match = re.search(r'\d+', active_group)
                if match:
                    selected_group_num = int(match.group())
        port_count = kwargs.get("端口 (Ports)", 4)
        target_ports = [f"G{selected_group_num}_Port{p}" for p in range(1, port_count + 1)]
        for port in target_ports:
            if port in raw_inputs and isinstance(raw_inputs[port], list):
                if port not in kwargs:
                    needed_inputs.append(port)
        return needed_inputs

    def route_models(self, **kwargs):
        exposed_groups = kwargs.get("组数 (Groups)", 1)
        active_group = str(kwargs.get("激活 (Active)", "Group 1")).strip()
        group_names_str = str(kwargs.get("组名 (Name)", ""))
        if not group_names_str and "prompt" in kwargs and "unique_id" in kwargs:
            try:
                raw_inputs = kwargs["prompt"][kwargs["unique_id"]]["inputs"]
                if isinstance(raw_inputs.get("组名 (Name)"), str):
                    group_names_str = str(raw_inputs["组名 (Name)"])
            except Exception:
                pass
        names_list = [s.strip() for s in re.split(r'[,，;；|\n]+', group_names_str) if s.strip()]
        selected_group_num = 1
        if active_group in names_list:
            selected_group_num = names_list.index(active_group) + 1
        else:
            match = re.search(r'(?i)group\s*(\d+)', active_group)
            if match:
                selected_group_num = int(match.group(1))
            else:
                match = re.search(r'\d+', active_group)
                if match:
                    selected_group_num = int(match.group())
        prefix = f"G{selected_group_num}_"
        port_count = kwargs.get("端口 (Ports)", 4)
        result_ports = []
        for p in range(1, 65):
            if p <= port_count:
                result_ports.append(kwargs.get(f"{prefix}Port{p}"))
            else:
                result_ports.append(None)
        return tuple([active_group] + result_ports)


class XXBuHuo_JointController:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "控制模式 (Mode)": (["静音 (Mute - 关闭)", "绕过 (Bypass - 略过)"], {"default": "静音 (Mute - 关闭)"})
            },
            "optional": {"CTRL": ("XX_CTRL",), }
        }

    RETURN_TYPES = ()
    FUNCTION = "do_nothing"
    CATEGORY = "XXBuHuo/Routing"
    OUTPUT_NODE = True

    def do_nothing(self, **kwargs):
        return ()


class XXBuHuo_CategorySelector:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {"选择 (Select)": (["Group 1"],), }
        }

    @classmethod
    def VALIDATE_INPUTS(cls, **kwargs):
        return True

    RETURN_TYPES = (ANY,)
    RETURN_NAMES = ("激活 (Active)",)
    FUNCTION = "get_selection"
    CATEGORY = "XXBuHuo/Routing"

    def get_selection(self, **kwargs):
        return (kwargs.get("选择 (Select)", "Group 1"),)


NODE_CLASS_MAPPINGS = {
    "XXBuHuo_NexusRouter": XXBuHuo_NexusRouter,
    "XXBuHuo_JointController": XXBuHuo_JointController,
    "XXBuHuo_CategorySelector": XXBuHuo_CategorySelector
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "XXBuHuo_NexusRouter": "XXBuHuo 核心路由中枢",
    "XXBuHuo_JointController": "XXBuHuo 联合控制",
    "XXBuHuo_CategorySelector": "XXBuHuo 分类选择器"
}
