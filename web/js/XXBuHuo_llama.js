import {app} from "../../../scripts/app.js";
import {api} from "../../../scripts/api.js";

const style = document.createElement("style");
style.textContent = `
    .omni-node-root, .omni-node-root * {
        box-sizing: border-box;
        margin: 0;
        padding: 0;
    }
    .omni-node-root {
        width: 100%;
        height: calc(100% + 12px);
        display: flex;
        align-items: flex-start;
        justify-content: flex-start;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        color: var(--fg-color);
        background: transparent !important;
        pointer-events: auto;
        margin-top: -12px;
        overflow: visible;
    }
    .omni-inner-wrapper {
        width: 100%;
        height: 100%;
        display: flex;
        flex-direction: column;
        --node-width: 320px;
        --node-height: 480px;
        --cqmin: min(calc(var(--node-width) / 100), calc(var(--node-height) / 100));
    }
    .omni-node-root .omni-tab-bar {
        display: flex;
        width: 100%;
        background: transparent !important;
        border-bottom: 1px solid var(--border-color);
        flex-shrink: 0;
        user-select: none;
    }
    .omni-node-root .omni-tab-item {
        flex: 1;
        padding: clamp(3px, calc(1.5 * var(--cqmin)), 20px) 0;
        text-align: center;
        cursor: pointer;
        font-size: clamp(8px, calc(2.5 * var(--cqmin)), 30px);
        font-weight: 700;
        color: var(--fg-color);
        opacity: 0.6;
        border-bottom: 2px solid transparent;
        transition: all 0.2s;
        border-radius: 4px 4px 0 0;
    }
    .omni-node-root .omni-tab-item:hover { opacity: 0.9; }
    .omni-node-root .omni-tab-item.active {
        opacity: 1;
        border-bottom: 2px solid var(--accent-color);
        background: rgba(150, 150, 150, 0.2) !important;
    }
    .omni-node-root .omni-content-box {
        flex: 1 1 0%;
        width: 100%;
        height: 100%;
        display: none;
        flex-direction: column;
        padding: clamp(2px, calc(1 * var(--cqmin)), 8px);
        gap: clamp(2px, calc(1 * var(--cqmin)), 8px);
        min-width: 0;
        min-height: 0;
    }
    .omni-node-root .omni-content-box.active { display: flex; }
    .omni-node-root .omni-content-box > * {
        flex-shrink: 1;
        min-height: 0;
    }
    .omni-node-root .omni-group {
        width: 100%;
        border: 1px solid var(--border-color);
        border-radius: 4px;
        padding: clamp(2px, calc(1.5 * var(--cqmin)), 12px);
        display: flex;
        flex-direction: column;
        gap: clamp(2px, calc(1.2 * var(--cqmin)), 10px);
        min-width: 0;
        min-height: 0;
    }
    .omni-node-root .omni-group-title {
        font-size: clamp(7px, calc(2.5 * var(--cqmin)), 30px);
        font-weight: 800;
        color: var(--fg-color);
        line-height: 1;
    }
    .omni-node-root .omni-row-center {
        display: flex;
        width: 100%;
        gap: clamp(1px, calc(1 * var(--cqmin)), 15px);
        align-items: center;
        justify-content: space-between;
        flex-wrap: nowrap;
        overflow: hidden;
        min-width: 0;
    }
    .omni-node-root .omni-left-group {
        display: flex;
        align-items: center;
        gap: clamp(1px, calc(1 * var(--cqmin)), 15px);
        flex: 1;
        min-width: 0;
        overflow: hidden;
    }
    .omni-node-root .omni-right-group {
        display: flex;
        align-items: center;
        gap: clamp(1px, calc(1 * var(--cqmin)), 15px);
        flex-shrink: 0;
        justify-content: flex-end;
        min-width: 0;
    }
    .omni-node-root .sync-grid {
        display: grid;
        grid-template-columns: minmax(0, 1.3fr) minmax(0, 1.3fr) auto minmax(0, 1fr) minmax(0, 1fr);
        gap: clamp(2px, calc(1.5 * var(--cqmin)), 10px) clamp(1px, calc(1 * var(--cqmin)), 6px);
        width: 100%;
        align-items: center;
        min-width: 0;
        box-sizing: border-box;
    }
    .omni-node-root .sync-grid-item-flex {
        display: flex;
        align-items: center;
        gap: clamp(1px, calc(1 * var(--cqmin)), 8px);
        min-width: 0;
    }
    .ctrl-fixed {
        width: 100% !important;
        min-width: 0 !important;
        flex-shrink: 1;
    }
    .ctrl-wide {
        width: 100% !important;
        min-width: 0 !important;
    }
    .omni-node-root .ctrl-icon {
        width: clamp(14px, calc(5.5 * var(--cqmin)), 80px) !important;
        min-width: clamp(14px, calc(5.5 * var(--cqmin)), 80px) !important;
        padding: 0 !important;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: clamp(8px, calc(3 * var(--cqmin)), 40px) !important;
        border: none !important;
        transition: background-color 0.15s ease;
    }
    .omni-node-root .bg-blue { background-color: #4477aa !important; color: white !important; }
    .omni-node-root .bg-red { background-color: #aa4444 !important; color: white !important; }
    .omni-node-root .bg-darkred { background-color: #883333 !important; color: white !important; }
    .omni-node-root .bg-gray { background-color: #555555 !important; color: white !important; }
    .omni-node-root .omni-col { flex: 1; display: flex; flex-direction: column; gap: clamp(1px, calc(0.5 * var(--cqmin)), 8px); min-width: 0; }
    .omni-node-root .omni-row-2col { display: grid; grid-template-columns: repeat(2, 1fr); gap: clamp(1px, calc(1.5 * var(--cqmin)), 20px); width: 100%; flex-shrink: 0; }
    .omni-node-root .omni-row-3col { display: grid; grid-template-columns: repeat(3, 1fr); gap: clamp(1px, calc(1.5 * var(--cqmin)), 20px); width: 100%; flex-shrink: 0; align-items: center;}
    .omni-node-root .omni-row-4col { display: grid; grid-template-columns: repeat(4, 1fr); gap: clamp(1px, calc(1.2 * var(--cqmin)), 15px); width: 100%; flex-shrink: 0; align-items: center; }
    .omni-node-root .omni-row-5col { display: grid; grid-template-columns: repeat(5, 1fr); gap: clamp(1px, calc(1.2 * var(--cqmin)), 15px); width: 100%; flex-shrink: 0; }
    .omni-node-root .omni-row-6col { display: grid; grid-template-columns: repeat(6, 1fr); gap: clamp(1px, calc(1.0 * var(--cqmin)), 10px); width: 100%; flex-shrink: 0; }
    .omni-node-root .omni-label, .omni-node-root .omni-inline-label {
        font-size: clamp(7px, calc(2.2 * var(--cqmin)), 26px);
        font-weight: 600;
        color: var(--fg-color);
        line-height: 1.1;
        white-space: nowrap;
        flex-shrink: 0;
    }
    .omni-node-root input[type="number"]::-webkit-inner-spin-button,
    .omni-node-root input[type="number"]::-webkit-outer-spin-button { -webkit-appearance: none; margin: 0; }
    .omni-node-root input[type="number"] { -moz-appearance: textfield; }
    .omni-node-root .omni-input, .omni-node-root .omni-select, .omni-node-root .omni-textarea {
        width: 100%;
        min-width: 0;
        background: transparent !important;
        border: 1px solid var(--border-color);
        color: var(--fg-color);
        padding: 0 clamp(2px, calc(1 * var(--cqmin)), 15px);
        border-radius: 3px;
        font-size: clamp(5px, calc(2.2 * var(--cqmin)), 26px);
        outline: none;
        transition: border 0.2s;
        line-height: 1.5;
        height: clamp(14px, calc(4.5 * var(--cqmin)), 60px);
        flex-shrink: 1;
    }
    .omni-node-root .omni-select option {
        font-size: 15px;
        background: #e8e8e8;
        color: #111;
    }
    .omni-node-root select.hide-arrow {
        -webkit-appearance: none;
        -moz-appearance: none;
        appearance: none;
        background-image: none !important;
        padding-right: clamp(2px, calc(1 * var(--cqmin)), 15px);
    }
    .omni-node-root select.hide-arrow::-ms-expand { display: none; }
    .omni-node-root .omni-input-wrapper {
        display: flex;
        align-items: center;
        background: transparent !important;
        border: 1px solid var(--border-color);
        border-radius: 3px;
        padding: 0 clamp(2px, calc(1 * var(--cqmin)), 15px);
        height: clamp(14px, calc(4.5 * var(--cqmin)), 60px);
        transition: border 0.2s;
        width: 100%;
        box-sizing: border-box;
        min-width: 0;
        overflow: hidden;
    }
    .omni-node-root .omni-input-wrapper:focus-within {
        border-color: var(--accent-color);
    }
    .omni-node-root .wrapper-label {
        font-size: clamp(5px, calc(2.2 * var(--cqmin)), 26px);
        font-weight: 600;
        color: var(--fg-color);
        opacity: 0.7;
        margin-right: clamp(2px, calc(1 * var(--cqmin)), 10px);
        white-space: nowrap;
        flex-shrink: 0;
    }
    .omni-node-root .wrapper-input {
        flex: 1;
        width: 100%;
        min-width: 0;
        background: transparent;
        border: none;
        color: var(--fg-color);
        font-size: clamp(5px, calc(2.2 * var(--cqmin)), 26px);
        outline: none;
        text-align: left;
        font-family: inherit;
        font-weight: bold;
        -moz-appearance: textfield;
        padding: 0;
    }
    .omni-node-root .omni-input:focus, .omni-node-root .omni-select:focus, .omni-node-root .omni-textarea:focus { border-color: var(--accent-color); }
    .omni-node-root .omni-textarea {
        resize: none;
        padding: clamp(2px, calc(1 * var(--cqmin)), 8px);
        line-height: 1.3;
        flex: 1 1 0%;
        height: 100%;
        min-height: 20px;
    }
    .omni-node-root .omni-checkbox-label {
        display: flex; align-items: center; gap: clamp(1px, calc(0.8 * var(--cqmin)), 10px);
        font-size: clamp(5px, calc(2.2 * var(--cqmin)), 26px);
        font-weight: 600; color: var(--fg-color); cursor: pointer; user-select: none;
        white-space: nowrap; flex-shrink: 1; overflow: visible;
    }
    .omni-node-root .omni-checkbox {
        accent-color: var(--accent-color);
        width: clamp(9px, calc(3.5 * var(--cqmin)), 33px);
        height: clamp(9px, calc(3.5 * var(--cqmin)), 33px);
        cursor: pointer; flex-shrink: 0; flex-grow: 0;
    }
    .omni-node-root .omni-btn {
        padding: 0 clamp(2px, calc(1 * var(--cqmin)), 15px);
        background: transparent !important;
        border: 1px solid var(--border-color);
        border-radius: 3px;
        color: var(--fg-color);
        font-size: clamp(5px, calc(2.2 * var(--cqmin)), 26px);
        font-weight: 700; cursor: pointer; transition: all 0.2s; user-select: none;
        white-space: nowrap; flex-shrink: 0;
        height: clamp(14px, calc(4.5 * var(--cqmin)), 60px);
        line-height: 1.5;
        width: auto;
    }
    .omni-node-root .omni-btn:hover { filter: brightness(1.2); }
    .omni-node-root .omni-upload-btn {
        position: relative;
        padding: clamp(0.5px, calc(0.5 * var(--cqmin)), 6px) 0;
        background: transparent !important;
        border: 1px solid var(--border-color); border-radius: 3px;
        color: var(--fg-color);
        font-size: clamp(6px, calc(2.5 * var(--cqmin)), 30px);
        font-weight: 700; text-align: center; cursor: pointer; transition: all 0.2s;
        user-select: none; width: 100%; flex-shrink: 0;
    }
    .omni-node-root .omni-upload-btn:hover { border-color: var(--accent-color); color: var(--accent-color); }
    .omni-node-root .omni-upload-btn input[type="file"] { position: absolute; inset: 0; opacity: 0; cursor: pointer; }
    .omni-node-root .omni-preview-area {
        flex: 1 1 0;
        min-height: 0;
        width: 100%;
        border: 1px solid var(--border-color);
        border-radius: 4px;
        background: transparent !important;
        overflow: hidden;
        position: relative;
        padding: clamp(2px, calc(1 * var(--cqmin)), 15px);
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .omni-node-root .preview-content {
        display: flex;
        flex-wrap: wrap;
        align-content: center;
        justify-content: center;
        background: transparent;
        box-sizing: border-box;
        margin: 0 auto;
    }
    .omni-node-root .preview-thumb-wrap { box-sizing: border-box; padding: clamp(1px, calc(0.8 * var(--cqmin)), 8px); }
    .omni-node-root .preview-thumb-inner {
        position: relative; width: 100%; height: 100%;
        background: transparent !important;
        border-radius: 3px; overflow: hidden; cursor: pointer; border: 1px solid var(--border-color);
        display: flex; align-items: center; justify-content: center;
    }
    .omni-node-root .preview-thumb-inner img, .omni-node-root .preview-thumb-inner video {
        width: 100%; height: 100%;
        object-fit: contain !important;
    }
    .omni-node-root .preview-thumb-inner .preview-delete-btn {
        position: absolute;
        top: 2px !important;
        right: 2px !important;
        width: 20% !important;
        height: 20% !important;
        max-width: 14px !important;
        max-height: 14px !important;
        aspect-ratio: 1 / 1 !important;
        background-color: transparent !important;
        background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='4' stroke-linecap='round' stroke-linejoin='round'%3e%3cline x1='18' y1='6' x2='6' y2='18'%3e%3c/line%3e%3cline x1='6' y1='6' x2='18' y2='18'%3e%3c/line%3e%3c/svg%3e") !important;
        background-size: 100% 100% !important;
        background-position: center !important;
        background-repeat: no-repeat !important;
        filter: drop-shadow(0px 1px 2px rgba(0,0,0,0.85));
        border: none !important;
        color: transparent !important;
        font-size: 0 !important;
        padding: 0 !important;
        margin: 0 !important;
        cursor: pointer;
        opacity: 0;
        pointer-events: none;
        z-index: 10;
        transform-origin: center center !important;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    .omni-node-root .preview-thumb-inner:hover .preview-delete-btn {
        opacity: 0.9;
        pointer-events: auto;
    }
    .omni-node-root .preview-delete-btn:hover {
        background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23ff4444' stroke-width='4' stroke-linecap='round' stroke-linejoin='round'%3e%3cline x1='18' y1='6' x2='6' y2='18'%3e%3c/line%3e%3cline x1='6' y1='6' x2='18' y2='18'%3e%3c/line%3e%3c/svg%3e") !important;
        background-color: transparent !important;
        filter: drop-shadow(0px 0px 3px rgba(255,68,68,0.7));
        transform: scale(1.3) rotate(90deg) !important;
        opacity: 1 !important;
    }
    .omni-node-root .preview-thumb-inner.highlight-glow {
        box-shadow: 0 0 5px 1px #00bcd4;
        border: 2.1px solid #00bcd4 !important;
        transform: scale(1.02);
        transition: all 0.2s ease-in-out;
    }
    .omni-node-root .omni-zoom-layer {
        position: absolute; top: 0; left: 0; width: 100%; height: 100%;
        background: var(--comfy-menu-bg, rgba(30, 30, 30, 0.95)); display: none;
        flex-direction: column; z-index: 100; backdrop-filter: blur(4px);
    }
    .omni-node-root .omni-zoom-wrapper {
        flex: 1; width: 100%; height: 100%; display: flex; align-items: center; justify-content: center;
        overflow: hidden; position: relative; cursor: zoom-out;
    }
    .omni-node-root .omni-zoom-wrapper img, .omni-node-root .omni-zoom-wrapper video {
        max-width: 95%; max-height: 95%; object-fit: contain; border-radius: 4px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
    }
    .omni-node-root .omni-zoom-info {
        text-align: center; padding: clamp(2px, calc(1 * var(--cqmin)), 12px); font-size: clamp(6px, calc(2.5 * var(--cqmin)), 24px);
        color: var(--fg-color); background: transparent;
    }
    .omni-node-root .omni-zoom-close {
        display: none !important;
    }
    .omni-node-root .preview-speed-mask {
        position: absolute; inset: 0; background: var(--comfy-menu-bg, rgba(25, 25, 25, 0.95));
        display: none; flex-direction: column; align-items: center; justify-content: center;
        z-index: 50; text-align: center; border-radius: 4px; backdrop-filter: blur(5px);
    }
    .omni-node-root .preview-speed-mask.show { display: flex; }
    .omni-node-root .speed-icon { font-size: clamp(30px, calc(10 * var(--cqmin)), 60px); margin-bottom: 8px; filter: drop-shadow(0 2px 5px rgba(0,0,0,0.5)); }
    .omni-node-root .speed-title { font-size: clamp(12px, calc(4 * var(--cqmin)), 24px); font-weight: bold; color: var(--fg-color); margin-bottom: 4px; }
    .omni-node-root .speed-desc { font-size: clamp(9px, calc(3 * var(--cqmin)), 18px); color: #aaa; }
    .omni-node-root .omni-custom-dropdown {
        display: none; position: absolute; top: calc(100% + 2px); left: 0; width: 100%;
        max-height: clamp(100px, calc(30 * var(--cqmin)), 250px); overflow-y: auto;
        background: var(--comfy-menu-bg, #222); border: 1px solid var(--border-color, #444);
        border-radius: 4px; z-index: 9999; box-shadow: 0 4px 10px rgba(0,0,0,0.5);
    }
    .omni-node-root .omni-custom-dropdown::-webkit-scrollbar { width: 3px; }
    .omni-node-root .omni-custom-dropdown::-webkit-scrollbar-thumb { background: #888; border-radius: 3px; }
    .omni-node-root .omni-custom-dropdown::-webkit-scrollbar-track { background: transparent; }
    .omni-node-root .omni-dropdown-item {
        padding: clamp(4px, calc(1.5 * var(--cqmin)), 12px) clamp(6px, calc(2 * var(--cqmin)), 15px);
        cursor: pointer; font-size: clamp(6px, calc(2.2 * var(--cqmin)), 22px);
        border-bottom: 1px solid rgba(255,255,255,0.05); color: var(--fg-color, #fff);
        transition: background 0.1s; word-break: break-all; line-height: 1.2;
    }
    .omni-node-root .omni-dropdown-item:hover { background: var(--comfy-input-bg, #444); color: var(--fg-color, #fff); }
`;
document.head.appendChild(style);

async function uploadFile(file) {
    const body = new FormData();
    body.append("image", file);
    body.append("type", "input");
    body.append("subfolder", "");
    try {
        const resp = await api.fetchApi("/upload/image", {method: "POST", body});
        if (resp.ok) {
            const data = await resp.json();
            return data.name;
        }
    } catch (err) {
        console.error("[XXBuHuo] 文件上传失败:", err);
    }
    return null;
}

function setupFeedbackBtn(btnEl, originalText, onClickAction) {
    btnEl.onclick = async () => {
        await onClickAction();
        btnEl.textContent = "OK";
        btnEl.style.backgroundColor = "#28a745";
        btnEl.style.setProperty("background-color", "#28a745", "important");
        setTimeout(() => {
            btnEl.textContent = originalText;
            btnEl.style.backgroundColor = "";
        }, 800);
    };
}

app.registerExtension({
    name: "XXBuHuo.LlamaCPP.V47", async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "XXBuHuoOmniNode") {
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            const onConfigure = nodeType.prototype.onConfigure;
            const onExecuted = nodeType.prototype.onExecuted;
            const originalSetSize = nodeType.prototype.setSize;
            const MIN_WIDTH = 320;
            const MIN_HEIGHT = 360;
            nodeType.prototype.setSize = function (size) {
                const clampedSize = [Math.max(size[0], MIN_WIDTH), Math.max(size[1], MIN_HEIGHT)];
                return originalSetSize.call(this, clampedSize);
            };
            nodeType.prototype.onConfigure = function (info) {
                if (onConfigure) onConfigure.apply(this, arguments);
                if (this.syncWidgetToUI) {
                    setTimeout(() => this.syncWidgetToUI(), 100);
                }
                setTimeout(() => {
                    if (this.widgets && this.uploadedFiles) {
                        const imgW = this.widgets.find(w => w.name === "multi_image_upload");
                        if (imgW && imgW.value) {
                            const fnames = imgW.value.split('\n').map(s => s.trim()).filter(Boolean);
                            this.uploadedFiles.image = [];
                            this.uploadedFiles.video = [];
                            fnames.forEach(name => {
                                const isVideo = name.match(/\.(mp4|webm|mov|avi|mkv|gif)$/i);
                                const fileObj = {
                                    name: name,
                                    url: api.apiURL(`/view?filename=${encodeURIComponent(name)}&type=input&subfolder=`),
                                    file: {type: isVideo ? 'video/mp4' : 'image/png'},
                                    is_received: false
                                };
                                if (isVideo) this.uploadedFiles.video.push(fileObj); else this.uploadedFiles.image.push(fileObj);
                            });
                        }
                        const vidW = this.widgets.find(w => w.name === "video_upload");
                        if (vidW && vidW.value && vidW.value !== "None") {
                            const name = vidW.value;
                            this.uploadedFiles.video = [{
                                name: name,
                                url: api.apiURL(`/view?filename=${encodeURIComponent(name)}&type=input&subfolder=`),
                                file: {type: 'video/mp4'},
                                is_received: false
                            }];
                        }
                        if (this.renderPreview) this.renderPreview();
                    }
                }, 150);
            };
            nodeType.prototype.onExecuted = function (message) {
                if (onExecuted) onExecuted.apply(this, arguments);
                if (message && message.any_media_images !== undefined) {
                    this.receivedFiles = [];
                    message.any_media_images.forEach(img => {
                        const url = api.apiURL(`/view?filename=${encodeURIComponent(img.filename)}&type=${img.type}&subfolder=${img.subfolder || ''}`);
                        const isVideo = img.media_type === 'video' || img.filename.match(/\.(mp4|webm|mov|avi)$/i);
                        this.receivedFiles.push({
                            name: img.filename,
                            url: url,
                            file: {type: isVideo ? 'video/mp4' : 'image/png'},
                            is_received: true,
                            media_type: isVideo ? 'video' : 'image'
                        });
                    });
                    this.renderPreview();
                }
            };
            nodeType.prototype.onNodeCreated = function () {
                if (onNodeCreated) onNodeCreated.apply(this, arguments);
                const node = this;
                const uid = node.id;
                node.ui = {};
                node.uploadedFiles = {image: [], video: []};
                node.receivedFiles = [];
                node.storedFilterFiles = [];
                node.widgets.forEach(w => {
                    w.type = "hidden";
                    w.hidden = true;
                    w.computeSize = () => [0, -4];
                });
                node.setSize([MIN_WIDTH, MIN_HEIGHT]);
                const root = document.createElement("div");
                root.className = "omni-node-root";
                node.ui.root = root;
                let urlOptionsHtml = "";
                const urlPresetsW = node.widgets.find(wd => wd.name === "api_url_presets");
                if (urlPresetsW && urlPresetsW.value) {
                    const urls = urlPresetsW.value.split("|||");
                    urls.forEach(u => {
                        if (u.trim()) {
                            urlOptionsHtml += `<div class="omni-dropdown-item">${u.trim()}</div>`;
                        }
                    });
                }
                root.innerHTML = `
                    <div class="omni-inner-wrapper">
                        <div class="omni-tab-bar">
                            <div class="omni-tab-item active" data-tab="cmd-${uid}">📁 指令</div>
                            <div class="omni-tab-item" data-tab="engine-${uid}">🧠 大脑</div>
                        </div>
                        <div id="cmd-${uid}" class="omni-content-box active">
                            <div class="omni-group" style="flex: 0.8 1 0%; display: flex; flex-direction: column;">
                                <div style="display: flex; gap: clamp(2px, calc(1 * var(--cqmin)), 8px); width: 100%; flex-shrink: 0;">
                                    <select id="ui-${uid}-preset_prompt" class="omni-select" style="flex: 1; min-width: 0;"></select>
                                    <select id="ui-${uid}-prompt_enhancer" class="omni-select" style="flex: 1; min-width: 0;"></select>
                                </div>
                                <textarea id="ui-${uid}-system_prompt" class="omni-textarea" placeholder="系统提示词 (例如：你是一个AI助手，请根据用户需求，输出对应内容。)">你是一个AI助手，请根据用户需求，输出对应内容。</textarea>
                                <textarea id="ui-${uid}-custom_prompt" class="omni-textarea" placeholder="用户提示词 (例如：请详细描述画面内容)"></textarea>
                            </div>
                            <div class="sync-grid" style="flex-shrink: 0;">
                                <div style="grid-column: 1; display: flex; align-items: center;">
                                    <label class="omni-checkbox-label" style="color: #ff9800; font-weight: 900; font-size: clamp(9px, calc(3 * var(--cqmin)), 32px);"><input type="checkbox" id="ui-${uid}-enable_llm_inference" class="omni-checkbox" checked> llama推理</label>
                                </div>
                                <div style="grid-column: 2; display: flex; align-items: center;">
                                    <label class="omni-checkbox-label" style="color: #00bcd4; font-weight: 900; font-size: clamp(9px, calc(3 * var(--cqmin)), 32px);"><input type="checkbox" id="ui-${uid}-enable_resize" class="omni-checkbox"> 激活Resize</label>
                                </div>
                                <div class="sync-grid-item-flex" style="grid-column: 3;">
                                    <button id="btn-${uid}-toggle_preview" class="omni-btn ctrl-icon bg-blue" title="关闭预览 (进入极速透传模式)">👀</button>
                                    <button id="btn-${uid}-toggle_smooth" class="omni-btn ctrl-icon bg-gray" title="开启防抖 (视频人脸处理适用)">🎬</button>
                                </div>
                                <select id="ui-${uid}-input_mode" class="omni-select ctrl-fixed" style="grid-column: 4;"></select>
                                <div class="omni-input-wrapper ctrl-fixed" style="grid-column: 5;">
                                    <span class="wrapper-label">帧数</span>
                                    <input type="text" id="ui-${uid}-video_max_frames" class="wrapper-input" value="空" placeholder="空">
                                </div>
                                <input type="text" id="ui-${uid}-image_folder_path" class="omni-input ctrl-wide" placeholder="批量图路径" style="grid-column: 1;">
                                <input type="text" id="ui-${uid}-filter_input" class="omni-input ctrl-wide" placeholder="筛选 1,2,3" style="grid-column: 2;">
                                <div class="sync-grid-item-flex" style="grid-column: 3;">
                                    <button id="btn-${uid}-store" class="omni-btn ctrl-icon bg-blue" title="储存筛选">💾</button>
                                    <button id="btn-${uid}-clear_filter" class="omni-btn ctrl-icon bg-red" title="清除筛选">✖️</button>
                                </div>
                                <select id="ui-${uid}-upscale_method" class="omni-select ctrl-fixed" style="grid-column: 4;"></select>
                                <select id="ui-${uid}-keep_proportion" class="omni-select ctrl-fixed" style="grid-column: 5;"></select>
                                <div class="omni-input-wrapper ctrl-wide" style="grid-column: 1;">
                                    <span class="wrapper-label">宽</span>
                                    <input type="text" id="ui-${uid}-resize_width" class="wrapper-input" value="" placeholder="自适应">
                                </div>
                                <div class="omni-input-wrapper ctrl-wide" style="grid-column: 2;">
                                    <span class="wrapper-label">高</span>
                                    <input type="text" id="ui-${uid}-resize_height" class="wrapper-input" value="" placeholder="自适应">
                                </div>
                                <div class="sync-grid-item-flex" style="grid-column: 3;">
                                    <button id="btn-${uid}-swap_dimensions" class="omni-btn ctrl-icon bg-gray" title="反转宽高">🔄</button>
                                    <button id="btn-${uid}-clear_all" class="omni-btn ctrl-icon bg-gray" title="清空全部">🧹</button>
                                </div>
                                <select id="ui-${uid}-crop_position" class="omni-select ctrl-fixed" style="grid-column: 4;"></select>
                                <div class="omni-input-wrapper ctrl-fixed" style="grid-column: 5;">
                                    <span class="wrapper-label">对齐倍数</span>
                                    <input type="text" id="ui-${uid}-divisible_by" class="wrapper-input" value="" placeholder="无">
                                </div>
                            </div>
                            <div class="omni-upload-btn">
                                📂 上传文件（图片/视频）
                                <input type="file" id="upload-${uid}-all" multiple accept="image/*,video/*">
                            </div>
                            <div class="omni-preview-area" id="preview-viewport-${uid}" style="flex: 1.2 1 0%;">
                                <div id="mask-${uid}-speed" class="preview-speed-mask">
                                    <div class="speed-icon">🚀</div>
                                    <div class="speed-title">Speed Mode Active</div>
                                    <div class="speed-desc">Visuals hidden for max performance</div>
                                </div>
                                <div class="preview-content" id="preview-${uid}-content"></div>
                                <div class="omni-zoom-layer" id="zoom-layer-${uid}">
                                    <div class="omni-zoom-close" id="zoom-close-${uid}">×</div>
                                    <div class="omni-zoom-wrapper" id="zoom-wrapper-${uid}"></div>
                                    <div class="omni-zoom-info" id="zoom-info-${uid}"></div>
                                </div>
                            </div>
                        </div>
                        <div id="engine-${uid}" class="omni-content-box">
                            <div class="omni-group">
                                <label class="omni-group-title">模式选择</label>
                                <select id="ui-${uid}-model_source" class="omni-select"></select>
                            </div>
                            <div id="engine-local-${uid}" class="omni-group">
                                <div class="omni-col">
                                    <label class="omni-label">本地模型GGUF</label>
                                    <select id="ui-${uid}-gguf_model" class="omni-select"></select>
                                </div>
                                <div class="omni-col">
                                    <label class="omni-label">视觉投影MMproj</label>
                                    <select id="ui-${uid}-mmproj_model" class="omni-select"></select>
                                </div>
                                <div class="omni-row-4col">
                                    <div class="omni-col">
                                        <label class="omni-label">模型架构</label>
                                        <select id="ui-${uid}-vision_type" class="omni-select"></select>
                                    </div>
                                    <div class="omni-col">
                                        <label class="omni-label">投机草稿</label>
                                        <select id="ui-${uid}-draft_model" class="omni-select"></select>
                                    </div>
                                    <div class="omni-col">
                                        <label class="omni-label">KV量化 (K)</label>
                                        <select id="ui-${uid}-kv_cache_type_k" class="omni-select"></select>
                                    </div>
                                    <div class="omni-col">
                                        <label class="omni-label">KV量化 (V)</label>
                                        <select id="ui-${uid}-kv_cache_type_v" class="omni-select"></select>
                                    </div>
                                </div>
                                <div class="omni-row-4col">
                                    <label class="omni-checkbox-label">
                                        <input type="checkbox" id="ui-${uid}-stream_to_console" class="omni-checkbox" checked> 打印信息
                                    </label>
                                    <label class="omni-checkbox-label" title="关闭后允许Gemma4输出思考过程，提高复杂推理准确率">
                                        <input type="checkbox" id="ui-${uid}-enable_physical_block" class="omni-checkbox" checked> 关闭思考
                                    </label>
                                    <label class="omni-checkbox-label" title="运行结束后保持模型在显存中，下次秒开">
                                        <input type="checkbox" id="ui-${uid}-keep_model_in_vram" class="omni-checkbox" checked> 显存缓存
                                    </label>
                                    <div class="omni-input-wrapper">
                                        <span class="wrapper-label">图片限幅</span>
                                        <input type="number" id="ui-${uid}-image_max_size" class="wrapper-input" value="512" title="受限于固定Patch，缩小此值仅为防显存溢出">
                                    </div>
                                </div>
                                <div class="omni-row-4col">
                                    <label class="omni-checkbox-label" title="执行前后彻底清空显存(作除错兜底用)">
                                        <input type="checkbox" id="ui-${uid}-force_unload" class="omni-checkbox"> 强制卸载
                                    </label>
                                    <label class="omni-checkbox-label">
                                        <input type="checkbox" id="ui-${uid}-save_chat_history" class="omni-checkbox"> 多轮对话
                                    </label>
                                    <label class="omni-checkbox-label" title="输出JSON结构提示词。注意推理速度会变慢，可以通过编写系统提示词来实现类似的json结构提示词，速度快。">
                                        <input type="checkbox" id="ui-${uid}-json_output" class="omni-checkbox"> JSON输出
                                    </label>
                                    <select id="ui-${uid}-device" class="omni-select hide-arrow"></select>
                                </div>
                            </div>
                            <div id="engine-api-${uid}" class="omni-group">
                                <div class="omni-col" style="position: relative; z-index: 101;">
                                    <label class="omni-label">API接口地址</label>
                                    <div style="position: relative; width: 100%; height: clamp(14px, calc(4.5 * var(--cqmin)), 60px); display: flex;">
                                        <input type="text" id="ui-${uid}-api_url" class="omni-input" style="height: 100%; padding-right: 30px; flex: 1;" placeholder="https://api.openai.com/v1">
                                        <div id="btn-${uid}-api_url" style="position: absolute; right: 10px; top: 0; width: 14px; height: 100%; display: flex; align-items: center; justify-content: center; cursor: pointer; color: var(--fg-color);">
                                        </div>
                                    </div>
                                    <div id="list-${uid}-api_url" class="omni-custom-dropdown">${urlOptionsHtml}</div>
                                </div>
                                <div class="omni-col">
                                    <label class="omni-label">API密钥 (Key)</label>
                                    <input type="password" id="ui-${uid}-api_key" class="omni-input" value="" placeholder="sk-...">
                                </div>
                                <div class="omni-col">
                                    <label class="omni-label">模型名称</label>
                                    <input type="text" id="ui-${uid}-api_model" class="omni-input" value="" placeholder="gpt-image-2">
                                </div>
                                <div class="omni-row-4col" style="margin-top: 4px;">
                                    <div class="omni-col" style="position: relative; z-index: 100;">
                                        <label class="omni-label">尺寸</label>
                                        <div style="position: relative; width: 100%; height: clamp(14px, calc(4.5 * var(--cqmin)), 60px); display: flex;">
                                            <input type="text" id="ui-${uid}-api_img_size" class="omni-input" style="height: 100%; padding-right: 26px; flex: 1;" placeholder="2560x1440">
                                            <div id="btn-${uid}-api_img_size" style="position: absolute; right: 8px; top: 0; width: 16px; height: 100%; display: flex; align-items: center; justify-content: center; cursor: pointer; color: var(--fg-color);">
                                            </div>
                                        </div>
                                        <div id="list-${uid}-api_img_size" class="omni-custom-dropdown">
                                            <div class="omni-dropdown-item">1024x1024 (1:1)</div>
                                            <div class="omni-dropdown-item">2048x2048 (1:1)</div>
                                            <div class="omni-dropdown-item">4096x4096 (1:1)</div>
                                            <div class="omni-dropdown-item">1024x1536 (2:3)</div>
                                            <div class="omni-dropdown-item">1536x1024 (3:2)</div>
                                            <div class="omni-dropdown-item">1024x1792 (9:16)</div>
                                            <div class="omni-dropdown-item">1440x2560 (9:16)</div>
                                            <div class="omni-dropdown-item">2160x3840 (9:16)</div>
                                            <div class="omni-dropdown-item">1792x1024 (16:9)</div>
                                            <div class="omni-dropdown-item">2560x1440 (16:9)</div>
                                            <div class="omni-dropdown-item">3840x2160 (16:9)</div>
                                            <div class="omni-dropdown-item">auto (自动适配)</div>
                                        </div>
                                    </div>
                                    <div class="omni-col">
                                        <label class="omni-label">画质</label>
                                        <select id="ui-${uid}-api_img_quality" class="omni-select">
                                            <option value="standard">standard</option>
                                            <option value="hd">hd</option>
                                            <option value="low">low</option>
                                            <option value="medium">medium</option>
                                            <option value="high">high</option>
                                            <option value="auto">auto</option>
                                        </select>
                                    </div>
                                    <div class="omni-col">
                                        <label class="omni-label">风格</label>
                                        <select id="ui-${uid}-api_img_style" class="omni-select">
                                            <option value="vivid">vivid (生动)</option>
                                            <option value="natural">natural (写实)</option>
                                        </select>
                                    </div>
                                    <div class="omni-col">
                                        <label class="omni-label">超时时间(秒)</label>
                                        <input type="number" id="ui-${uid}-api_timeout" class="omni-input" placeholder="600">
                                    </div>
                                </div>
                            </div>
                            <div id="engine-params-${uid}" class="omni-group">
                                <div class="omni-row-6col">
                                    <div class="omni-col">
                                        <label class="omni-label">最大生成长度</label>
                                        <input type="number" id="ui-${uid}-max_tokens" class="omni-input" value="2048">
                                    </div>
                                    <div class="omni-col">
                                        <label class="omni-label">温度系数</label>
                                        <input type="number" step="0.1" id="ui-${uid}-temperature" class="omni-input" value="0.8">
                                    </div>
                                    <div class="omni-col">
                                        <label class="omni-label">随机种子</label>
                                        <input type="number" id="ui-${uid}-llm_seed" class="omni-input" value="-1">
                                    </div>
                                    <div class="omni-col">
                                        <label class="omni-label">上下文窗口</label>
                                        <input type="number" id="ui-${uid}-n_ctx" class="omni-input" value="16384">
                                    </div>
                                    <div class="omni-col">
                                        <label class="omni-label">GPU层数</label>
                                        <input type="number" id="ui-${uid}-n_gpu_layers" class="omni-input" value="-1">
                                    </div>
                                    <div class="omni-col" style="position: relative; z-index: 92;">
                                        <label class="omni-label">CPU线程</label>
                                        <div style="position: relative; width: 100%; height: clamp(14px, calc(4.5 * var(--cqmin)), 60px); display: flex;">
                                            <input type="text" id="ui-${uid}-cpu_threads" class="omni-input" style="height: 100%; flex: 1;" value="Auto" placeholder="Auto">
                                            <div id="btn-${uid}-cpu_threads" style="position: absolute; right: 0; top: 0; width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; cursor: pointer; background: transparent;">
                                            </div>
                                        </div>
                                        <div id="list-${uid}-cpu_threads" class="omni-custom-dropdown">
                                            <div class="omni-dropdown-item">Auto</div>
                                        </div>
                                    </div>
                                </div>
                                <div class="omni-row-6col">
                                    <div class="omni-col">
                                        <label class="omni-label">Top P</label>
                                        <input type="number" step="0.05" id="ui-${uid}-top_p" class="omni-input" value="0.95">
                                    </div>
                                    <div class="omni-col">
                                        <label class="omni-label">重复惩罚</label>
                                        <input type="number" step="0.05" id="ui-${uid}-repeat_penalty" class="omni-input" value="1.1">
                                    </div>
                                    <div class="omni-col">
                                        <label class="omni-label">种子模式</label>
                                        <select id="ui-${uid}-seed_mode" class="omni-select hide-arrow"></select>
                                    </div>
                                    <div class="omni-col">
                                        <label class="omni-label">批处理大小</label>
                                        <input type="number" id="ui-${uid}-n_batch" class="omni-input" value="2048">
                                    </div>
                                    <div class="omni-col" style="position: relative; z-index: 90;">
                                        <label class="omni-label">显存上限</label>
                                        <div style="position: relative; width: 100%; height: clamp(14px, calc(4.5 * var(--cqmin)), 60px); display: flex;">
                                            <input type="text" id="ui-${uid}-vram_limit" class="omni-input" style="height: 100%; flex: 1;" value="Auto (-1)" placeholder="">
                                            <div id="btn-${uid}-vram_limit" style="position: absolute; right: 0; top: 0; width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; cursor: pointer; background: transparent;">
                                            </div>
                                        </div>
                                        <div id="list-${uid}-vram_limit" class="omni-custom-dropdown">
                                            <div class="omni-dropdown-item">Auto (-1)</div>
                                            <div class="omni-dropdown-item">8GB</div>
                                            <div class="omni-dropdown-item">12GB</div>
                                            <div class="omni-dropdown-item">16GB</div>
                                            <div class="omni-dropdown-item">24GB</div>
                                            <div class="omni-dropdown-item">48GB</div>
                                            <div class="omni-dropdown-item">96GB</div>
                                        </div>
                                    </div>
                                    <div class="omni-col" style="position: relative; z-index: 91;">
                                        <label class="omni-label">MoE</label>
                                        <div style="position: relative; width: 100%; height: clamp(14px, calc(4.5 * var(--cqmin)), 60px); display: flex;">
                                            <input type="text" id="ui-${uid}-n_cpu_moe" class="omni-input" style="height: 100%; flex: 1;" value="" placeholder="">
                                            <div id="btn-${uid}-n_cpu_moe" style="position: absolute; right: 0; top: 0; width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; cursor: pointer; background: transparent;">
                                            </div>
                                        </div>
                                        <div id="list-${uid}-n_cpu_moe" class="omni-custom-dropdown">
                                            <div class="omni-dropdown-item">Auto</div>
                                            <div class="omni-dropdown-item">None</div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
                node.ui.wrapper = root.querySelector('.omni-inner-wrapper');

                function updateSizeVars() {
                    if (!node.ui.wrapper) return;
                    const w = root.clientWidth;
                    const h = root.clientHeight;
                    node.ui.wrapper.style.setProperty('--node-width', `${w}px`);
                    node.ui.wrapper.style.setProperty('--node-height', `${h}px`);
                    if (node.updateLayout) node.updateLayout();
                }

                setTimeout(updateSizeVars, 10);
                const widgetMap = [["enable_preview", true], ["preset_prompt", false], ["prompt_enhancer", false], ["system_prompt", false], ["custom_prompt", false], ["enable_llm_inference", true], ["stream_to_console", true], ["keep_model_in_vram", true], ["save_chat_history", true], ["json_output", true], ["force_unload", true], ["enable_physical_block", true], ["image_max_size", false], ["input_mode", false], ["video_max_frames", false], ["image_folder_path", false], ["enable_resize", true], ["resize_width", false], ["resize_height", false], ["swap_dimensions", true], ["upscale_method", false], ["keep_proportion", false], ["crop_position", false], ["device", false], ["divisible_by", false], ["model_source", false], ["gguf_model", false], ["mmproj_model", false], ["vision_type", false], ["draft_model", false], ["kv_cache_type_k", false], ["kv_cache_type_v", false], ["api_url", false], ["api_key", false], ["api_model", false], ["max_tokens", false], ["temperature", false], ["llm_seed", false], ["seed_mode", false], ["n_ctx", false], ["n_batch", false], ["top_p", false], ["repeat_penalty", false], ["n_gpu_layers", false], ["vram_limit", false], ["enable_smoothing", true], ["api_img_size", false], ["api_img_quality", false], ["api_img_style", false], ["api_timeout", false], ["api_url_presets", false], ["cpu_threads", false], ["n_cpu_moe", false]];
                widgetMap.forEach(([name]) => {
                    node.ui[name] = root.querySelector(`#ui-${uid}-${name}`);
                });
                node.ui.tabs = root.querySelectorAll(".omni-tab-item");
                node.ui.tabContents = root.querySelectorAll(".omni-content-box");
                node.ui.engineLocal = root.querySelector(`#engine-local-${uid}`);
                node.ui.engineApi = root.querySelector(`#engine-api-${uid}`);
                node.ui.engineParams = root.querySelector(`#engine-params-${uid}`);
                node.ui.filterInput = root.querySelector(`#ui-${uid}-filter_input`);
                node.ui.btnStore = root.querySelector(`#btn-${uid}-store`);
                node.ui.btnClearFilter = root.querySelector(`#btn-${uid}-clear_filter`);
                node.ui.btnClearAll = root.querySelector(`#btn-${uid}-clear_all`);
                node.ui.previewArea = root.querySelector(`#preview-viewport-${uid}`);
                node.ui.previewContent = root.querySelector(`#preview-${uid}-content`);
                node.ui.zoomLayer = root.querySelector(`#zoom-layer-${uid}`);
                node.ui.zoomWrapper = root.querySelector(`#zoom-wrapper-${uid}`);
                node.ui.zoomInfo = root.querySelector(`#zoom-info-${uid}`);
                node.ui.zoomClose = root.querySelector(`#zoom-close-${uid}`);
                node.ui.upload_all = root.querySelector(`#upload-${uid}-all`);
                node.ui.filterInput.addEventListener("input", (e) => {
                    const val = e.target.value;
                    const thumbs = node.ui.previewContent.querySelectorAll('.preview-thumb-inner');
                    thumbs.forEach(t => t.classList.remove('highlight-glow'));
                    if (val.trim()) {
                        const cleanStr = val.replace(/^筛选\s*/, '').replace(/[^0-9,，/\\、\s]/g, ' ');
                        const indexes = cleanStr.split(/[,，/\\、\s]+/).map(s => parseInt(s.trim()) - 1).filter(n => !isNaN(n) && n >= 0);
                        indexes.forEach(idx => {
                            if (thumbs[idx]) thumbs[idx].classList.add('highlight-glow');
                        });
                    }
                });
                const tooltips = {
                    preset_prompt: "【系统指令预设模板】快速切换内置场景模板。\n1. 选中后将优先执行并覆盖下方的系统指令。\n2. 存放位置：models/XXBuHuo/presets 目录，格式为 .json。",
                    prompt_enhancer: "【提示词增强模板】规范模型输出格式。\n1. 强制 AI 按特定逻辑输出，防止复读或长篇大论。\n2. 存放位置：models/XXBuHuo/enhancers 目录，格式为 .json。",
                    system_prompt: "【系统提示词】定义 AI 行为准则。\n1. 设定 AI 的角色定位与基础回复偏好。",
                    custom_prompt: "【用户提示词】针对当前任务的要求或描述。",
                    enable_llm_inference: "【启用推理】AI 推理总开关。\n1. 不勾选时节点仅做媒体预处理，实现 0 显存极速透传。",
                    enable_resize: "【激活 Resize】视觉预处理开关。\n1. 不勾选时，所有的宽高、裁剪及对齐设置均不生效。",
                    input_mode: "【输入模式】AI 解析画面的逻辑。\n1. 可选逐帧、视频全局融合、宫格切分或纯文本对话。",
                    video_max_frames: "【帧数 / 宫格】多功能核心参数：\n1. 视频抽帧：限制提取帧数(推荐8)，填-1全抽。\n2. 填0不抽帧，输入视频image输出为空，Source_media输出极速透传。\n3. 宫格切分：输入如3*3，系统会将单图切片后分块解析。\n4. 此模式针对视频/宫格起作用，图像模式不受影响。",
                    image_folder_path: "【本地路径】批量加载本地媒体。\n1. 自动读取目录下所有文件。\n2. 填入文件夹地址示例：D:/XXBuHuo或\"D:/csimage\" 。",
                    filterInput: "【画面筛选】精准过滤多余画面。\n1. 提取特定帧：输入要保留的序号(如 1,3,5)并点击右侧 💾 按钮保存。",
                    resize_width: "【目标宽度】输出画面的绝对宽度。\n1. 留空：开启自适应，保持原图比例。",
                    resize_height: "【目标高度】输出画面的绝对高度。\n1. 留空：开启自适应，保持原图比例。",
                    upscale_method: "【缩放算法】图像重采样方式。\n1. 推荐 nearest-exact：计算极快；追求极致清晰度可选 lanczos。",
                    keep_proportion: "【缩放策略】画面的尺寸调整方式。\n1. 包含，拉伸、智能裁剪、边缘填充、背景模糊填充等模式。",
                    crop_position: "【裁剪锚点】缩放裁剪时保留的中心区域。\n1. 选 face 或 head 时，将调用视觉模型自动锁定并对齐人脸。\n2. 使用InsightFace 模型进行精准识别，第一次加载会自动下载，也可自行下载onnx格式模型。\n3. InsightFace 模型存放位置 /models/XXBuHuo/insightface/models/buffalo_l文件夹下。",
                    divisible_by: "【对齐倍数】多模式动态参数：\n1. 基础对齐：强制输出宽高为此数值的整数倍。\n2. 视觉缓冲：配合 face/head 且宽高为空时，代表向外扩充的像素距离。\n3. ⚠️ 注意：face/head模式，若宽高有值，此处必须留空或删除宽高值。",
                    image_max_size: "【图像限幅】送入 AI 前的长边最高限制。\n1. 推荐 1024：既保证视觉特征识别精度，又能有效防止显存溢出。",
                    model_source: "【算力来源】本地与API切换。\n1. 选择使用本地 GGUF 模型文件，或云端 Cloud API 接口。",
                    gguf_model: "【本地模型】本地主模型文件。\n1. 请确保存放在 models/XXBuHuo/llama 目录下。",
                    mmproj_model: "【视觉投影】赋予 AI 看图能力的文件。\n1. 须与主模型架构匹配，存放在 models/XXBuHuo/mmproj 目录下。",
                    vision_type: "【模型架构】指定模型架构。\n1. 必须与模型真实的架构一致，选错会乱码，名称不错会自动切换。",
                    draft_model: "【投机模型】小参数辅助提速模型。\n1. 日常使用通常设为 None 即可。",
                    api_url: "【API 接口】云端推理的地址前缀。\n1. 需兼容标准的 OpenAI 接口规范。\n2.如： https://api.openai.com/v1。\n3.如： http://localhost:11434/v1。\n4.如： http://localhost:8080/v1",
                    api_key: "【API 密钥】云端模型的认证凭证。\n1. 访问大模型 API 必须的验证字符串。\n2.如： sk-...。\n3.如： 本地ollama没有则留空。",
                    api_model: "【模型名称】云端接口的模型标识。\n1. 请求云端接口时调用的具体模型名称。\n2.如： gpt-image-2。\n3.如： 本地模型全名称（XX/模型名称）。",
                    api_img_size: "【API出图尺寸】云端AI绘图的目标分辨率。\n1. 强烈推荐使用下拉框中的标准长宽比例，自定义异常尺寸极易被服务器拒绝。",
                    api_img_quality: "【API画质】生成图像的质量级别。\n1. standard：标准画质；hd：高清画质（仅限部分如 DALL-E 3 等高级模型支持）。",
                    api_img_style: "【API风格】生成图像的艺术倾向。\n1. vivid：生动鲜艳，富有表现力；natural：自然写实，偏向真实摄影物理光影。",
                    api_timeout: "【超时时间】API请求的断开死线(秒)。\n1. 建议设为 600 (10分钟)，防止中转站生成慢导致图被强行丢弃。",
                    kv_cache_type_k: "【K缓存量化】降低显存占用。\n1. 默认 F16 为无损状态。",
                    kv_cache_type_v: "【V缓存量化】降低显存占用。\n1. 默认 F16 为无损状态。",
                    device: "【运算设备】硬件调度分配。\n1. cuda：显卡全速运算；auto：显存不足时自动分流防崩，默认cuda。",
                    n_gpu_layers: "【GPU层数】模型在显卡运行的层数。\n1. 推荐 -1 (全量加载)；若报错 OOM 请逐步调低此数值。",
                    vram_limit: "【物理限存】强制锁定显存使用上限。\n1. 推荐 Auto：由系统自动核算层数，有效预防爆显存崩溃。",
                    stream_to_console: "【流式输出】后台打印进程。\n1. 开启后在控制台中以打字机模式实时显示 AI 的生成过程。",
                    enable_physical_block: "【封锁思考】关闭思考。\n1. 拦截 <think> 标签的内部思考过程，直接输出结果，极大提速。",
                    keep_model_in_vram: "【显存驻留】常驻显存开关。\n1. 勾选后模型不释放，免去下一次生成的加载等待时间。",
                    force_unload: "【强制卸载】显存清理开关。\n1. 执行前强制彻底清空显存并重新加载模型，无法卸载模型时使用。",
                    save_chat_history: "【对话记忆】多轮对话上下文。\n1. 注意：途中切换不同图像或更改指令时建议关闭，防逻辑混淆。",
                    json_output: "【JSON强制】指定数据结构。\n1. 要求大模型以标准 JSON 格式返回结果。",
                    n_ctx: "【上下文容量】单次处理的图文最大记忆视野。\n1. 单图推荐 4096，视频推荐 8192 或以上(每张图约占上千 Token)。",
                    n_batch: "【批处理块】文本与图像的解码吞吐量。\n1. 推荐 1024 或 2048。设置过大可能导致瞬间显存峰值溢出。",
                    max_tokens: "【生成长度】AI 单次输出的最大字符数。\n1. 推荐 1024，足以覆盖绝大多数复杂视觉场景的细致描述。",
                    temperature: "【温度系数】控制输出词汇的随机发散性。\n1. 推荐 0.8：平衡指令执行的严谨性与语言的丰富程度。",
                    top_p: "【核采样】控制候选词的范围。\n1. 推荐 0.95：在保证句子语法连贯的同时，提供合理的词汇变化。",
                    repeat_penalty: "【重复惩罚】防止 AI 输出复读机式内容。\n1. 推荐 1.1 到 1.2 之间。数值过高会导致行文逻辑破碎。",
                    llm_seed: "【推理种子】控制初始的随机状态。\n1. 设为 -1 表示每次完全不可复现的盲盒生成。",
                    seed_mode: "【种子模式】种子演变逻辑。\n1. 固定(测试参数)、随机(盲盒变化)、递增(对比细微变异)。",
                    cpu_threads: "【CPU 线程数】控制参与内存计算的核心数，推荐保持默认。\n1. 自动模式 (Auto/空)：根据具体运行状况智能分配。\n2. 手动输入：根据自身 CPU 逻辑线程数填写，建议不超过总数的 70%。\n3. MoE 满载说明：开启 MoE 卸载时默认会占用 100% 算力。为防系统卡顿，可手动适当调低。\n4. 显存压制联动：若手动限制了【显存上限】，自动模式(Auto)会默认为你压制线程（约 4~8 线程）。",
                    n_cpu_moe: "【MoE 专家卸载】加载模型时，底层会自动识别是否为 MoE 模型。\n1. 关闭状态 (None)：默认关闭，不进行专家剥离。\n2. 自动模式 (Auto/空)：将根据探测到的模型层数和显存差额，进行效率最大化的智能卸载。\n3. 手动填写：可根据控制台打印的专家层数信息手动填写。若不会设置，强烈推荐 Auto。\n4. 显存上限配合：在 MoE 模式下，需要限制显存上限，建议将输入数值与想要压制的最终值，降低 2G~3G 作为冗余，不需要显存上限默认Auto就行。"
                };
                Object.keys(tooltips).forEach(key => {
                    if (node.ui[key]) {
                        node.ui[key].title = tooltips[key];
                        if (node.ui[key].type === "checkbox" && node.ui[key].parentElement) {
                            node.ui[key].parentElement.title = tooltips[key];
                        }
                        if (node.ui[key].parentElement && node.ui[key].parentElement.classList.contains("omni-input-wrapper")) {
                            node.ui[key].parentElement.title = tooltips[key];
                        }
                        const overlayBtn = root.querySelector(`#btn-${uid}-${key}`);
                        if (overlayBtn) {
                            overlayBtn.title = tooltips[key];
                        }
                    }
                });
                const extraElements = [{
                    id: `btn-${uid}-store`, text: "【💾 储存筛选】应用左侧文本框中的数字规则，高亮并仅保留指定的预览画面参与大模型推理。"
                }, {
                    id: `btn-${uid}-clear_filter`, text: "【✖️ 清除筛选】一键撤销所有筛选状态。"
                }, {
                    id: `btn-${uid}-swap_dimensions`, text: "【🔄 宽高互换】一键交换当前输入的目标宽度与高度数值。"
                }, {
                    id: `btn-${uid}-clear_all`, text: "【🧹 终极清空】彻底清除所有已上传的本地文件、节点缓存以及各项筛选规则。"
                }, {
                    id: `btn-${uid}-toggle_preview`, text: "【👀 预览/透传切换】开启可查看缩略图；关闭后将进入极速透传模式，跳过多线程解码直接将底层张量交接给大模型。"
                }, {
                    id: `btn-${uid}-toggle_smooth`, text: "【🎬 时序防抖】开启后处理视频人脸时将引入卡尔曼滤波，彻底消除前后的画面闪烁；单图处理建议关闭恢复多线程极速并发。"
                }, {
                    class: "omni-upload-btn", text: "【📂 本地上传】点击此处，从电脑硬盘直接选择图片、拼接长图或视频片段注入节点内存池。"
                }, {
                    id: `preview-viewport-${uid}`,
                    text: "【预览区】显示媒体文件预览。\n1. 点击缩略图可无损放大，再次点击还原。\n2. 点击右上角微型红叉可从内存中剔除该媒体（只有上传模式下生效）。"
                }];
                extraElements.forEach(item => {
                    let el = item.id ? root.querySelector(`#${item.id}`) : root.querySelector(`.${item.class}`);
                    if (el) el.title = item.text;
                });
                node.ui.tabs.forEach(tab => {
                    tab.onclick = () => {
                        const targetId = tab.getAttribute("data-tab");
                        node.ui.tabs.forEach(t => t.classList.remove("active"));
                        node.ui.tabContents.forEach(c => c.classList.remove("active"));
                        tab.classList.add("active");
                        root.querySelector(`#${targetId}`).classList.add("active");
                    };
                });
                const updateEngineDisplay = () => {
                    const val = node.ui.model_source?.value;
                    if (!val) return;
                    const isLocal = val === "Local_GGUF";
                    node.ui.engineLocal.style.display = isLocal ? "flex" : "none";
                    node.ui.engineApi.style.display = val === "Cloud_API" ? "flex" : "none";
                    node.ui.engineParams.style.display = isLocal ? "flex" : "none";
                };
                node.ui.model_source.addEventListener("change", updateEngineDisplay);
                const updatePromptStatus = () => {
                    const presetVal = node.ui.preset_prompt?.value;
                    const sysPromptEl = node.ui.system_prompt;
                    if (!sysPromptEl) return;
                    const isSysConnected = !!node.inputs[1]?.link;
                    if (isSysConnected || (presetVal && presetVal !== "None")) {
                        sysPromptEl.style.opacity = "0.5";
                        sysPromptEl.style.backgroundColor = "rgba(0,0,0,0.1)";
                        sysPromptEl.readOnly = true;
                        sysPromptEl.title = isSysConnected ? "已连接外部[系统提示词]，此文本框被接管禁用。" : "当前正在使用预设提示词，此文本框被接管禁用。";
                    } else {
                        sysPromptEl.style.opacity = "1";
                        sysPromptEl.style.backgroundColor = "transparent";
                        sysPromptEl.readOnly = false;
                        sysPromptEl.title = "系统级指令，定义AI的角色。当前预设为None且无外部连线，此框生效。";
                    }
                };
                node.ui.preset_prompt.addEventListener("change", updatePromptStatus);
                setTimeout(updatePromptStatus, 200);
                const optionTooltips = {
                    "逐帧推理": "对输入的每一帧画面进行独立前向计算，输出对应的描述列表。",
                    "视频推理": "采用全局视角，将多帧画面作为连续的时间线输入给模型，输出连贯的动态描述。",
                    "宫格推理": "将画面按照指定的行列数物理切分，依次读取并编织分镜故事。",
                    "文本推理": "忽略任何图像或视频的输入，仅执行纯文本对话任务。",
                    "lanczos": "高阶图像插值算法。边缘锐利且清晰度最高，但计算耗时较长。",
                    "nearest-exact": "最近邻插值算法。运算速度极快，但容易产生像素锯齿。",
                    "bilinear": "双线性插值算法。在处理速度与画面平滑度之间取得良好平衡。",
                    "bicubic": "双三次插值算法。平滑度优于双线性，适合图像的放大操作。",
                    "area": "区域重采样算法。适合大幅度缩小图像，能有效防止摩尔纹的产生。",
                    "stretch": "比例策略：无视原始画面的长宽比，强制拉伸画面以铺满目标尺寸。",
                    "crop": "比例策略：智能裁剪。按原始比例缩放后，切割并丢弃超出目标范围的像素。",
                    "pad": "比例策略：边缘填充。保持完整画面不被裁切，在不足的部分填充纯黑边框。",
                    "pad_edge": "比例策略：边缘延展。复制并拉伸画面最外侧边缘的像素来填补空白区域。",
                    "pad_lb_pixel": "比例策略：均值填充。提取画面底边的色彩均值作为背景底色进行填充。",
                    "pillarbox_blur": "比例策略：高斯垫底。使用原图的高斯模糊版作为背景，再将原图叠加于其上（适合竖屏转横屏处理）。",
                    "resize": "比例策略：基础对齐。严格保持原始长宽比进行安全的尺寸调整。",
                    "filter": "比例策略：滤镜模式。用于特殊的图像降噪与预处理。",
                    "total_pixels": "比例策略：总像素锁定。按照设定的总像素阈值进行等比例缩放，严控显存占用。",
                    "center": "裁剪锚点：以画面几何中心为基准进行保留。",
                    "top": "裁剪锚点：重点保留画面顶部区域（适合横屏裁剪为竖屏时保留人物头部）。",
                    "bottom": "裁剪锚点：重点保留画面底部区域。",
                    "left": "裁剪锚点：重点保留画面左侧区域（适合全景长图的截取）。",
                    "right": "裁剪锚点：重点保留画面右侧区域。",
                    "face": "裁剪锚点：人脸对齐。调用底层视觉引擎锁定五官位置，强制进行水平端正与居中操作。",
                    "head": "裁剪锚点：头部追踪。锁定完整头部轮廓，带有一定的边缘缓冲区域，适合视频防抖及居中追踪。",
                    "默认(F16)": "缓存精度：保持原生的半精度浮点运算，上下文质量最高，但显存消耗最大。",
                    "Q5_K(平衡)": "缓存精度：显存消耗降低近半，且几乎无损画质与文本逻辑，强烈推荐作为常规首选。",
                    "Q8_0(提速30%)": "缓存精度：节省少量显存，同时能带来较为明显的推理速度提升。",
                    "Q4_0(极致速度)": "缓存精度：极大降低显存占用，但处理长文本或复杂逻辑分析时可能会出现理解偏差。",
                    "Q4_1(极致速度+精度)": "缓存精度：在 Q4 的基础上对运算精度进行了适当改良。",
                    "Q5_0(高精度)": "缓存精度：Q5 的基础量化版本，逻辑控制与语义理解能力优秀。",
                    "Q5_1(高精度)": "缓存精度：Q5 系列中表现最佳的非线性精度版本。",
                    "固定": "种子模式：锁定随机数种子，多次执行相同配置将得到可复现的一致结果。",
                    "随机": "种子模式：每次执行生成不同的随机数种子，产生具有多样性的输出内容。",
                    "递增": "种子模式：种子数值每次执行后递增，适用于工作流微调阶段对比细微变化。",
                    "Auto (-1)": "显存限制：系统自动根据当前设备的可用显存状况，动态分配计算资源。",
                    "cpu": "硬件设备：完全依赖系统内存和 CPU 进行张量计算，处理速度极为缓慢。",
                    "cuda": "硬件设备：将运算任务全量移交至系统主显卡，获取最佳的推理吞吐速度。",
                    "cuda:0+1": "硬件设备：将计算图物理分割至两张显卡，共同分摊显存与算力压力。",
                    "cuda:0": "硬件设备：强制指定使用第 1 张独立显卡进行推理，适用于多卡指定调度。",
                    "cuda:1": "硬件设备：强制指定使用第 2 张独立显卡进行推理。",
                    "multi-gpu(自动均衡)": "硬件设备：全自动将模型切割并分布到所有可用的显卡上，实现显存与算力负载均衡。",
                    "8GB": "显存限制：将模型载入层数严格限制在 8GB 显存红线以内，其余移交内存。",
                    "12GB": "显存限制：将模型载入层数严格限制在 12GB 显存红线以内。",
                    "16GB": "显存限制：将模型载入层数严格限制在 16GB 显存红线以内。",
                    "24GB": "显存限制：将模型载入层数严格限制在 24GB 显存红线以内。",
                    "48GB": "显存限制：将模型载入层数严格限制在 48GB 显存红线以内。",
                    "96GB": "显存限制：针对顶级算力平台，解锁 96GB 的物理显存限制。",
                    "standard": "画质参数：标准画质 (出图快，绝大多数第三方模型兼容)。",
                    "hd": "画质参数：极致高清画质 (需官方底层明确支持此参数)。",
                    "vivid": "画质风格：色彩生动、富有表现力与视觉张力。",
                    "natural": "画质风格：偏向真实摄影、自然光影与物理写实。",
                    "auto(cpu+cuda混合)": "硬件设备：当模型大小超出单张显卡容量时，自动将部分层卸载至系统内存以防止程序崩溃。"
                };
                setTimeout(() => {
                    widgetMap.forEach(([name, isCheck]) => {
                        const el = node.ui[name];
                        const w = node.widgets.find(wd => wd.name === name);
                        if (el && w && el.tagName === "SELECT" && w.options?.values) {
                            el.innerHTML = "";
                            w.options.values.forEach(v => {
                                const opt = document.createElement("option");
                                opt.value = v;
                                opt.textContent = v;
                                if (optionTooltips[v]) {
                                    opt.title = optionTooltips[v];
                                }
                                el.appendChild(opt);
                            });
                        }
                    });
                    node.syncWidgetToUI();
                    updateEngineDisplay();
                }, 100);
                node.syncWidgetToUI = () => {
                    widgetMap.forEach(([name, isCheck]) => {
                        const el = node.ui[name];
                        const w = node.widgets.find(wd => wd.name === name);
                        if (el && w) {
                            if (name === "n_cpu_moe" && (w.value === "" || w.value === "0" || w.value === 0)) {
                                w.value = "None";
                            }
                            if (name === "cpu_threads" && (w.value === "" || w.value === "0" || w.value === 0)) {
                                w.value = "Auto";
                            }
                            if (isCheck) el.checked = w.value; else el.value = w.value;
                        }
                    });
                    updateEngineDisplay();
                };
                widgetMap.forEach(([name, isCheck]) => {
                    const el = node.ui[name];
                    const w = node.widgets.find(wd => wd.name === name);
                    if (el && w) {
                        el.addEventListener("change", () => {
                            w.value = isCheck ? el.checked : el.value;
                            app.graph.setDirtyCanvas(true, true);
                        });
                        if (!isCheck && el.tagName !== "SELECT") {
                            el.addEventListener("input", () => {
                                w.value = el.type === "number" ? Number(el.value) : el.value;
                                app.graph.setDirtyCanvas(true, true);
                            });
                        }
                    }
                });

                function bindCustomDropdown(inputId, btnId, listId, widgetName) {
                    const input = root.querySelector(inputId);
                    const btn = root.querySelector(btnId);
                    const list = root.querySelector(listId);
                    if (!input || !btn || !list) return;
                    btn.addEventListener("click", (e) => {
                        e.stopPropagation();
                        input.focus();
                        const isShowing = list.style.display === "block";
                        root.querySelectorAll('.omni-custom-dropdown').forEach(d => d.style.display = "none");
                        list.style.display = isShowing ? "none" : "block";
                        Array.from(list.children).forEach(c => c.style.display = "block");
                    });
                    input.addEventListener("click", (e) => {
                        e.stopPropagation();
                        root.querySelectorAll('.omni-custom-dropdown').forEach(d => {
                            if (d !== list) d.style.display = "none";
                        });
                        Array.from(list.children).forEach(c => c.style.display = "block");
                        if (list.children.length > 0) list.style.display = "block";
                    });
                    input.addEventListener("input", (e) => {
                        const val = e.target.value.toLowerCase();
                        let hasVisible = false;
                        Array.from(list.children).forEach(child => {
                            if (child.textContent.toLowerCase().includes(val)) {
                                child.style.display = "block";
                                hasVisible = true;
                            } else {
                                child.style.display = "none";
                            }
                        });
                        list.style.display = hasVisible ? "block" : "none";
                        const w = node.widgets.find(wd => wd.name === widgetName);
                        if (w) w.value = input.value;
                        app.graph.setDirtyCanvas(true, true);
                    });
                    list.addEventListener("click", (e) => {
                        e.stopPropagation();
                        if (e.target.classList.contains("omni-dropdown-item")) {
                            let val = e.target.textContent.trim();
                            if (widgetName === "api_img_size" && val.includes(" ")) {
                                val = val.split(" ")[0];
                            }
                            input.value = val;
                            const w = node.widgets.find(wd => wd.name === widgetName);
                            if (w) w.value = val;
                            app.graph.setDirtyCanvas(true, true);
                            list.style.display = "none";
                        }
                    });
                }

                bindCustomDropdown(`#ui-${uid}-api_url`, `#btn-${uid}-api_url`, `#list-${uid}-api_url`, "api_url");
                bindCustomDropdown(`#ui-${uid}-api_img_size`, `#btn-${uid}-api_img_size`, `#list-${uid}-api_img_size`, "api_img_size");
                bindCustomDropdown(`#ui-${uid}-vram_limit`, `#btn-${uid}-vram_limit`, `#list-${uid}-vram_limit`, "vram_limit");
                bindCustomDropdown(`#ui-${uid}-cpu_threads`, `#btn-${uid}-cpu_threads`, `#list-${uid}-cpu_threads`, "cpu_threads");
                bindCustomDropdown(`#ui-${uid}-n_cpu_moe`, `#btn-${uid}-n_cpu_moe`, `#list-${uid}-n_cpu_moe`, "n_cpu_moe");
                document.addEventListener("click", () => {
                    root.querySelectorAll('.omni-custom-dropdown').forEach(d => d.style.display = "none");
                });
                if (node.ui.gguf_model && node.ui.vision_type) {
                    node.ui.gguf_model.addEventListener("change", (e) => {
                        const modelName = e.target.value.toLowerCase();
                        let targetVision = "";
                        if (modelName.includes("qwen3.6") || modelName.includes("qwen-3.6")) {
                            targetVision = "Qwen3.6-VL";
                        } else if (modelName.includes("qwen")) {
                            targetVision = "Qwen3.5-VL";
                        } else if (modelName.includes("gemma")) {
                            targetVision = "Gemma4";
                        }
                        if (targetVision && node.ui.vision_type.value !== targetVision) {
                            node.ui.vision_type.value = targetVision;
                            const visionW = node.widgets.find(wd => wd.name === "vision_type");
                            if (visionW) visionW.value = targetVision;
                            const originalBorder = node.ui.vision_type.style.borderColor;
                            const originalColor = node.ui.vision_type.style.color;
                            node.ui.vision_type.style.borderColor = "#4caf50";
                            node.ui.vision_type.style.color = "#4caf50";
                            setTimeout(() => {
                                node.ui.vision_type.style.borderColor = originalBorder;
                                node.ui.vision_type.style.color = originalColor;
                            }, 800);
                            app.graph.setDirtyCanvas(true, true);
                        }
                    });
                }
                const swapBtn = root.querySelector(`#btn-${uid}-swap_dimensions`);
                setupFeedbackBtn(swapBtn, "🔄", async () => {
                    const wInput = node.ui.resize_width;
                    const hInput = node.ui.resize_height;
                    const wWidget = node.widgets.find(wd => wd.name === "resize_width");
                    const hWidget = node.widgets.find(wd => wd.name === "resize_height");
                    const temp = wInput.value;
                    wInput.value = hInput.value;
                    hInput.value = temp;
                    const tempW = wWidget.value;
                    wWidget.value = hWidget.value;
                    hWidget.value = tempW;
                    app.graph.setDirtyCanvas(true, true);
                });
                setupFeedbackBtn(node.ui.btnClearAll, "🧹", async () => {
                    node.uploadedFiles.image = [];
                    node.uploadedFiles.video = [];
                    node.receivedFiles = [];
                    node.storedFilterFiles = [];
                    node.ui.filterInput.value = "";
                    node.ui.image_folder_path.value = "";
                    const imgW = node.widgets.find(wd => wd.name === "multi_image_upload");
                    const vidW = node.widgets.find(wd => wd.name === "video_upload");
                    const folderW = node.widgets.find(wd => wd.name === "image_folder_path");
                    const filterW = node.widgets.find(wd => wd.name === "filter_store");
                    if (imgW) {
                        imgW.value = "";
                        if (imgW.callback) imgW.callback(imgW.value);
                    }
                    if (vidW) {
                        vidW.value = "None";
                        if (vidW.callback) vidW.callback(vidW.value);
                    }
                    if (folderW) folderW.value = "";
                    if (filterW) filterW.value = "";
                    node.renderPreview();
                    app.graph.setDirtyCanvas(true, true);
                });
                node.updateLayout = () => {
                    if (!node.ui.previewArea || !node.ui.previewContent) return;
                    const gridWrapper = node.ui.previewContent;
                    const count = gridWrapper.children.length;
                    if (count === 0) return;
                    gridWrapper.style.width = "100%";
                    gridWrapper.style.height = "100%";
                    const area = node.ui.previewArea;
                    const computed = window.getComputedStyle(area);
                    const padX = (parseFloat(computed.paddingLeft) || 0) + (parseFloat(computed.paddingRight) || 0);
                    const padY = (parseFloat(computed.paddingTop) || 0) + (parseFloat(computed.paddingBottom) || 0);
                    const contW = area.clientWidth - padX;
                    const contH = area.clientHeight - padY;
                    if (contW <= 0 || contH <= 0) return;
                    let imgW = 4;
                    let imgH = 3;
                    const firstMedia = gridWrapper.querySelector('img, video');
                    if (firstMedia) {
                        imgW = firstMedia.naturalWidth || firstMedia.videoWidth || 4;
                        imgH = firstMedia.naturalHeight || firstMedia.videoHeight || 3;
                    }
                    let bestCols = 1;
                    let maxScale = 0;
                    for (let cols = 1; cols <= count; cols++) {
                        const rows = Math.ceil(count / cols);
                        const scaleW = contW / (cols * imgW);
                        const scaleH = contH / (rows * imgH);
                        const scale = Math.min(scaleW, scaleH);
                        if (scale > maxScale) {
                            maxScale = scale;
                            bestCols = cols;
                        }
                    }
                    const finalRows = Math.ceil(count / bestCols);
                    gridWrapper.style.width = `${Math.floor(bestCols * imgW * maxScale)}px`;
                    gridWrapper.style.height = `${Math.floor(finalRows * imgH * maxScale)}px`;
                    const itemPercent = 100 / bestCols;
                    for (let wrap of gridWrapper.children) {
                        wrap.style.width = `${itemPercent}%`;
                        wrap.style.height = "auto";
                        const inner = wrap.querySelector('.preview-thumb-inner');
                        if (inner) {
                            inner.style.aspectRatio = `${imgW}/${imgH}`;
                        }
                    }
                };
                node.renderPreview = () => {
                    node.ui.previewContent.innerHTML = "";
                    const allFiles = [...node.uploadedFiles.image.map(f => ({
                        ...f, type: 'image'
                    })), ...node.uploadedFiles.video.map(f => ({
                        ...f, type: 'video'
                    })), ...node.receivedFiles.map(f => ({...f, type: f.media_type || 'image'}))];
                    if (allFiles.length === 0) return;
                    allFiles.forEach((file, idx) => {
                        const thumbWrap = document.createElement("div");
                        thumbWrap.className = "preview-thumb-wrap";
                        const thumb = document.createElement("div");
                        thumb.className = "preview-thumb-inner";
                        thumb.dataset.type = file.type;
                        thumb.dataset.index = idx;
                        if (file.type === 'image') {
                            const imgEl = document.createElement("img");
                            imgEl.src = file.url;
                            imgEl.alt = `Img${idx + 1}`;
                            imgEl.onload = () => {
                                if (node.updateLayout) node.updateLayout();
                            };
                            thumb.appendChild(imgEl);
                        } else if (file.type === 'video') {
                            const vidEl = document.createElement("video");
                            vidEl.src = file.url;
                            vidEl.controls = true;
                            vidEl.muted = true;
                            vidEl.preload = "metadata";
                            vidEl.onloadedmetadata = () => {
                                if (node.updateLayout) node.updateLayout();
                            };
                            thumb.appendChild(vidEl);
                        }
                        if (!file.is_received) {
                            const deleteBtn = document.createElement("button");
                            deleteBtn.className = "preview-delete-btn";
                            deleteBtn.innerHTML = "×";
                            deleteBtn.onclick = (e) => {
                                e.stopPropagation();
                                const uIdx = node.uploadedFiles[file.type].findIndex(f => f.name === file.name);
                                if (uIdx > -1) node.uploadedFiles[file.type].splice(uIdx, 1);
                                const imgW = node.widgets.find(wd => wd.name === "multi_image_upload");
                                const vidW = node.widgets.find(wd => wd.name === "video_upload");
                                const allNames = [...node.uploadedFiles.image.map(f => f.name), ...node.uploadedFiles.video.map(f => f.name)];
                                if (imgW) {
                                    imgW.value = allNames.join('\n');
                                    if (imgW.callback) imgW.callback(imgW.value);
                                }
                                if (vidW) vidW.value = "None";
                                node.renderPreview();
                                app.graph.setDirtyCanvas(true, true);
                            };
                            thumb.appendChild(deleteBtn);
                        }
                        thumb.onclick = () => {
                            node.ui.zoomWrapper.innerHTML = "";
                            if (file.type === 'image') {
                                const img = document.createElement("img");
                                img.src = file.url;
                                node.ui.zoomWrapper.appendChild(img);
                                node.ui.zoomInfo.textContent = `${idx + 1}/${allFiles.length} : 获取尺寸中...`;
                                img.onload = () => {
                                    node.ui.zoomInfo.textContent = `${idx + 1}/${allFiles.length} : ${img.naturalWidth} × ${img.naturalHeight}`;
                                };
                            } else if (file.type === 'video') {
                                const vid = document.createElement("video");
                                vid.src = file.url;
                                vid.controls = true;
                                vid.autoplay = true;
                                vid.loop = true;
                                node.ui.zoomWrapper.appendChild(vid);
                                node.ui.zoomInfo.textContent = `${idx + 1}/${allFiles.length} : 获取尺寸中...`;
                                vid.onloadedmetadata = () => {
                                    node.ui.zoomInfo.textContent = `${idx + 1}/${allFiles.length} : ${vid.videoWidth} × ${vid.videoHeight}`;
                                };
                            }
                            node.ui.zoomLayer.style.display = "flex";
                        };
                        thumbWrap.appendChild(thumb);
                        node.ui.previewContent.appendChild(thumbWrap);
                    });
                    setTimeout(() => {
                        if (node.updateLayout) node.updateLayout();
                    }, 10);
                };
                node.ui.zoomClose.onclick = () => {
                    node.ui.zoomLayer.style.display = "none";
                    node.ui.zoomWrapper.innerHTML = "";
                };
                node.ui.zoomWrapper.onclick = () => {
                    node.ui.zoomLayer.style.display = "none";
                    node.ui.zoomWrapper.innerHTML = "";
                };
                const input = node.ui.upload_all;
                input.onchange = async (e) => {
                    const files = e.target.files;
                    if (!files.length) return;
                    for (let file of files) {
                        const name = await uploadFile(file);
                        if (name) {
                            const url = URL.createObjectURL(file);
                            if (file.type.startsWith("image/")) {
                                node.uploadedFiles.image.push({name, url, file});
                            } else if (file.type.startsWith("video/")) {
                                node.uploadedFiles.video.push({name, url, file});
                            }
                        }
                    }
                    node.renderPreview();
                    const imgW = node.widgets.find(wd => wd.name === "multi_image_upload");
                    const vidW = node.widgets.find(wd => wd.name === "video_upload");
                    const allNames = [...node.uploadedFiles.image.map(f => f.name), ...node.uploadedFiles.video.map(f => f.name)];
                    if (imgW) {
                        imgW.value = allNames.join('\n');
                        if (imgW.callback) imgW.callback(imgW.value);
                    }
                    if (vidW) vidW.value = "None";
                    app.graph.setDirtyCanvas(true, true);
                    input.value = "";
                };
                setupFeedbackBtn(node.ui.btnStore, "💾", async () => {
                    const inputVal = node.ui.filterInput.value.trim();
                    const filterW = node.widgets.find(wd => wd.name === "filter_store");
                    if (filterW) filterW.value = inputVal;
                    app.graph.setDirtyCanvas(true, true);
                });
                setupFeedbackBtn(node.ui.btnClearFilter, "✖️", async () => {
                    node.ui.filterInput.value = "";
                    const filterW = node.widgets.find(wd => wd.name === "filter_store");
                    if (filterW) filterW.value = "";
                    const thumbs = node.ui.previewContent.querySelectorAll('.preview-thumb-inner');
                    thumbs.forEach(t => t.classList.remove('highlight-glow'));
                    app.graph.setDirtyCanvas(true, true);
                });
                let lastWidth = 0, lastHeight = 0;
                const resizeObserver = new ResizeObserver((entries) => {
                    const entry = entries[0];
                    if (entry) {
                        const w = entry.contentRect.width;
                        const h = entry.contentRect.height;
                        if (Math.abs(w - lastWidth) > 1 || Math.abs(h - lastHeight) > 1) {
                            lastWidth = w;
                            lastHeight = h;
                            window.requestAnimationFrame(() => updateSizeVars());
                        }
                    }
                });
                node.onConnectionsChange = function (type, index, connected, link_info) {
                    if (type === 1 && index === 0 && !connected) {
                        this.receivedFiles = [];
                        this.renderPreview();
                        app.graph.setDirtyCanvas(true, true);
                    }
                    if (type === 1 && (index === 1 || index === 2)) {
                        const customPromptEl = node.ui.custom_prompt;
                        setTimeout(() => {
                            updatePromptStatus();
                            const isCustomConnected = !!node.inputs[2]?.link;
                            if (customPromptEl) {
                                if (isCustomConnected) {
                                    customPromptEl.style.opacity = "0.5";
                                    customPromptEl.style.backgroundColor = "rgba(0,0,0,0.1)";
                                    customPromptEl.readOnly = true;
                                    customPromptEl.title = "已连接外部[用户提示词]，此文本框被接管禁用。";
                                } else {
                                    customPromptEl.style.opacity = "1";
                                    customPromptEl.style.backgroundColor = "transparent";
                                    customPromptEl.readOnly = false;
                                    customPromptEl.title = "用户提示词 (例如：请详细描述画面内容)";
                                }
                            }
                        }, 10);
                    }
                };
                if (node.ui.image_folder_path) {
                    node.ui.image_folder_path.addEventListener("input", (e) => {
                        if (e.target.value.trim() === "") {
                            console.log("[XXBuHuo] 路径清空，清除相关缓存");
                            node.receivedFiles = [];
                            node.renderPreview();
                            app.graph.setDirtyCanvas(true, true);
                        }
                    });
                }
                if (node.ui.vram_limit) {
                    node.ui.vram_limit.addEventListener("blur", (e) => {
                        let val = e.target.value.trim();
                        if (val === "") val = "Auto (-1)";
                        e.target.value = val;
                        const w = node.widgets.find(wd => wd.name === "vram_limit");
                        if (w) w.value = val;
                        app.graph.setDirtyCanvas(true, true);
                    });
                }
                ["cpu_threads", "n_cpu_moe"].forEach(name => {
                    if (node.ui[name]) {
                        node.ui[name].addEventListener("blur", (e) => {
                            let val = e.target.value.trim();
                            if (name === "n_cpu_moe" && (val === "" || val === "0" || val.toLowerCase() === "none")) {
                                val = "None";
                            }
                            if (name === "cpu_threads" && (val === "0" || val === "" || val.toLowerCase() === "auto")) {
                                val = "Auto";
                            }
                            e.target.value = val;
                            const w = node.widgets.find(wd => wd.name === name);
                            if (w) w.value = val;
                            app.graph.setDirtyCanvas(true, true);
                        });
                    }
                });
                const btnTogglePreview = root.querySelector(`#btn-${uid}-toggle_preview`);
                const speedMask = root.querySelector(`#mask-${uid}-speed`);
                const previewWidget = node.widgets.find(w => w.name === "enable_preview");
                if (btnTogglePreview) {
                    btnTogglePreview.onclick = () => {
                        const isEnabled = previewWidget ? previewWidget.value : true;
                        const newState = !isEnabled;
                        if (previewWidget) previewWidget.value = newState;
                        if (newState) {
                            btnTogglePreview.innerText = "👀";
                            btnTogglePreview.className = "omni-btn ctrl-icon bg-blue";
                            btnTogglePreview.title = "关闭预览 (进入极速透传模式)";
                            if (speedMask) speedMask.classList.remove("show");
                        } else {
                            btnTogglePreview.innerText = "🚀";
                            btnTogglePreview.className = "omni-btn ctrl-icon bg-gray";
                            btnTogglePreview.title = "开启预览 (生成缩略图)";
                            if (speedMask) speedMask.classList.add("show");
                            node.receivedFiles = [];
                            node.uploadedFiles.image = node.uploadedFiles.image.filter(f => !f.name.startsWith('xxbuhuo_temp_'));
                            node.uploadedFiles.video = node.uploadedFiles.video.filter(f => !f.name.startsWith('xxbuhuo_temp_'));
                            node.renderPreview();
                        }
                        app.graph.setDirtyCanvas(true, true);
                    };
                    setTimeout(() => {
                        if (previewWidget && !previewWidget.value) {
                            btnTogglePreview.innerText = "🚀";
                            btnTogglePreview.className = "omni-btn ctrl-icon bg-gray";
                            if (speedMask) speedMask.classList.add("show");
                        }
                    }, 200);
                }
                const btnToggleSmooth = root.querySelector(`#btn-${uid}-toggle_smooth`);
                const smoothWidget = node.widgets.find(w => w.name === "enable_smoothing");
                if (btnToggleSmooth) {
                    btnToggleSmooth.onclick = () => {
                        const isEnabled = smoothWidget ? smoothWidget.value : false;
                        const newState = !isEnabled;
                        if (smoothWidget) smoothWidget.value = newState;
                        if (newState) {
                            btnToggleSmooth.innerText = "🎬";
                            btnToggleSmooth.className = "omni-btn ctrl-icon bg-blue";
                            btnToggleSmooth.title = "关闭防抖 (恢复多线程极速处理)";
                        } else {
                            btnToggleSmooth.innerText = "📳";
                            btnToggleSmooth.className = "omni-btn ctrl-icon bg-gray";
                            btnToggleSmooth.title = "开启防抖 (处理视频人脸时消除闪烁)";
                        }
                        app.graph.setDirtyCanvas(true, true);
                    };
                    setTimeout(() => {
                        if (smoothWidget && smoothWidget.value) {
                            btnToggleSmooth.innerText = "🎬";
                            btnToggleSmooth.className = "omni-btn ctrl-icon bg-blue";
                            btnToggleSmooth.title = "关闭防抖 (恢复多线程极速处理)";
                        } else {
                            btnToggleSmooth.innerText = "📳";
                            btnToggleSmooth.className = "omni-btn ctrl-icon bg-gray";
                            btnToggleSmooth.title = "开启防抖 (处理视频人脸时消除闪烁)";
                        }
                    }, 200);
                }
                resizeObserver.observe(root);
                node.addDOMWidget("omni_ui", "custom", root, {
                    getMinHeight: () => 0, getMinWidth: () => 0,
                });
            };
        }
        if (nodeData.name === "XXBuHuoImageSplitter") {
            const onConfigure = nodeType.prototype.onConfigure;
            nodeType.prototype.onConfigure = function (info) {
                if (info && info.widgets_values) {
                    const countWidgetIdx = this.widgets.findIndex(w => w.name === "output_count");
                    if (countWidgetIdx > -1) {
                        const savedCount = info.widgets_values[countWidgetIdx];
                        if (this.updateOutputs) this.updateOutputs(savedCount);
                    }
                }
                if (onConfigure) onConfigure.apply(this, arguments);
            };
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                if (onNodeCreated) onNodeCreated.apply(this, arguments);
                const node = this;
                node.updateOutputs = function (count) {
                    count = parseInt(count, 10) || 1;
                    if (!this.outputs) this.outputs = [];
                    const current = this.outputs.length;
                    if (current < count) {
                        for (let i = current; i < count; i++) {
                            this.addOutput(`image_${i + 1}`, "IMAGE");
                        }
                    } else if (current > count) {
                        for (let i = current - 1; i >= count; i--) {
                            this.removeOutput(i);
                        }
                    }
                    for (let i = 0; i < this.outputs.length; i++) {
                        this.outputs[i].name = `image_${i + 1}`;
                    }
                    const newSize = this.computeSize();
                    this.setSize([Math.max(200, newSize[0]), Math.max(80, newSize[1])]);
                    if (app.graph) app.graph.setDirtyCanvas(true, true);
                };
                const countWidget = node.widgets.find(w => w.name === "output_count");
                const updateWidget = node.widgets.find(w => w.name === "update_outputs");
                if (updateWidget) {
                    updateWidget.type = "hidden";
                    updateWidget.hidden = true;
                    updateWidget.computeSize = () => [0, -4];
                }
                node.addWidget("button", "Update outputs", "Update outputs", function () {
                    if (countWidget) node.updateOutputs(countWidget.value);
                });
                if (!app.configuringGraph && countWidget) {
                    setTimeout(() => {
                        node.updateOutputs(countWidget.value);
                    }, 10);
                }
            };
        }
        if (nodeData.name === "XXBuHuoImageCombiner") {
            const onConfigure = nodeType.prototype.onConfigure;
            nodeType.prototype.onConfigure = function (info) {
                if (info && info.widgets_values) {
                    const countWidgetIdx = this.widgets.findIndex(w => w.name === "input_count");
                    if (countWidgetIdx > -1) {
                        const savedCount = info.widgets_values[countWidgetIdx];
                        if (this.updateInputs) this.updateInputs(savedCount);
                    }
                }
                if (onConfigure) onConfigure.apply(this, arguments);
            };
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                if (onNodeCreated) onNodeCreated.apply(this, arguments);
                const node = this;
                node.updateInputs = function (count) {
                    count = parseInt(count, 10) || 1;
                    if (!this.inputs) this.inputs = [];
                    const current = this.inputs.length;
                    if (current < count) {
                        for (let i = current; i < count; i++) {
                            this.addInput(`image_${i + 1}`, "IMAGE");
                        }
                    } else if (current > count) {
                        for (let i = current - 1; i >= count; i--) {
                            this.removeInput(i);
                        }
                    }
                    for (let i = 0; i < this.inputs.length; i++) {
                        this.inputs[i].name = `image_${i + 1}`;
                        this.inputs[i].type = "IMAGE";
                    }
                    const newSize = this.computeSize();
                    this.setSize([Math.max(200, newSize[0]), Math.max(80, newSize[1])]);
                    if (app.graph) app.graph.setDirtyCanvas(true, true);
                };
                const countWidget = node.widgets.find(w => w.name === "input_count");
                const updateWidget = node.widgets.find(w => w.name === "update_inputs");
                if (updateWidget) {
                    updateWidget.type = "hidden";
                    updateWidget.hidden = true;
                    updateWidget.computeSize = () => [0, -4];
                }
                node.addWidget("button", "Update inputs", "Update inputs", function () {
                    if (countWidget) node.updateInputs(countWidget.value);
                });
                if (!app.configuringGraph && countWidget) {
                    setTimeout(() => {
                        node.updateInputs(countWidget.value);
                    }, 10);
                }
            };
        }
        if (nodeData.name === "XXBuHuoTextSplitter") {
            const onConfigure = nodeType.prototype.onConfigure;
            nodeType.prototype.onConfigure = function (info) {
                if (info && info.widgets_values) {
                    const countWidgetIdx = this.widgets.findIndex(w => w.name === "output_count");
                    if (countWidgetIdx > -1) {
                        const savedCount = info.widgets_values[countWidgetIdx];
                        if (this.updateOutputs) this.updateOutputs(savedCount);
                    }
                }
                if (onConfigure) onConfigure.apply(this, arguments);
            };
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                if (onNodeCreated) onNodeCreated.apply(this, arguments);
                const node = this;
                node.updateOutputs = function (count) {
                    count = parseInt(count, 10) || 1;
                    if (!this.outputs) this.outputs = [];
                    const current = this.outputs.length;
                    if (current < count) {
                        for (let i = current; i < count; i++) {
                            this.addOutput(`text_${i + 1}`, "STRING");
                        }
                    } else if (current > count) {
                        for (let i = current - 1; i >= count; i--) {
                            this.removeOutput(i);
                        }
                    }
                    for (let i = 0; i < this.outputs.length; i++) {
                        this.outputs[i].name = `text_${i + 1}`;
                        this.outputs[i].type = "STRING";
                    }
                    const newSize = this.computeSize();
                    this.setSize([Math.max(200, newSize[0]), Math.max(80, newSize[1])]);
                    if (app.graph) app.graph.setDirtyCanvas(true, true);
                };
                const countWidget = node.widgets.find(w => w.name === "output_count");
                const updateWidget = node.widgets.find(w => w.name === "update_outputs");
                if (updateWidget) {
                    updateWidget.type = "hidden";
                    updateWidget.hidden = true;
                    updateWidget.computeSize = () => [0, -4];
                }
                node.addWidget("button", "Update outputs", "Update outputs", function () {
                    if (countWidget) node.updateOutputs(countWidget.value);
                });
                if (!app.configuringGraph && countWidget) {
                    setTimeout(() => {
                        node.updateOutputs(countWidget.value);
                    }, 10);
                }
            };
        }
    }
});