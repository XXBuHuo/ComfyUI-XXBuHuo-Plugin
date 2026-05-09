import {app} from "../../../scripts/app.js";

function isGetSetNode(node) {
    if (!node) return false;
    const type = node.type || "";
    if (type === "GetNode" || type === "SetNode") return true;
    const checkStr = (s) => {
        if (!s) return false;
        const upper = s.toUpperCase();
        return upper.startsWith("GET_") || upper.startsWith("SET_") || upper === "GET" || upper === "SET";
    };
    return checkStr(node.title) || checkStr(node._orig_title);
}

function updateFollowerPosition(followerNode) {
    if (!app.graph) return;
    if (app.configuring) return;
    let targetNode = null;
    if (followerNode.outputs && followerNode.outputs.length > 0) {
        for (let out of followerNode.outputs) {
            if (out.links && out.links.length > 0) {
                const link = app.graph.links[out.links[0]];
                if (link) {
                    targetNode = app.graph.getNodeById(link.target_id);
                    break;
                }
            }
        }
    }
    if (!targetNode && followerNode.inputs && followerNode.inputs.length > 0) {
        for (let inp of followerNode.inputs) {
            if (inp.link) {
                const link = app.graph.links[inp.link];
                if (link) {
                    targetNode = app.graph.getNodeById(link.origin_id);
                    break;
                }
            }
        }
    }
    if (targetNode && !isGetSetNode(targetNode)) {
        if (!followerNode._target_tracker || followerNode._target_tracker.id !== targetNode.id) {
            followerNode._target_tracker = {id: targetNode.id};
            followerNode._relative_x = followerNode.pos[0] - targetNode.pos[0];
            followerNode._relative_y = followerNode.pos[1] - targetNode.pos[1];
        }
        const isSelected = app.canvas && app.canvas.selected_nodes && app.canvas.selected_nodes[followerNode.id];
        if (isSelected) {
            const new_rel_x = followerNode.pos[0] - targetNode.pos[0];
            const new_rel_y = followerNode.pos[1] - targetNode.pos[1];
            if (followerNode._relative_x !== undefined) {
                if (Math.abs(followerNode._relative_x - new_rel_x) > 2 || Math.abs(followerNode._relative_y - new_rel_y) > 2) {
                    followerNode.properties = followerNode.properties || {};
                    followerNode.properties.manual_arranged = true;
                }
            }
            followerNode._relative_x = new_rel_x;
            followerNode._relative_y = new_rel_y;
        } else {
            if (Number.isFinite(followerNode._relative_x) && Number.isFinite(followerNode._relative_y)) {
                followerNode.pos[0] = targetNode.pos[0] + followerNode._relative_x;
                followerNode.pos[1] = targetNode.pos[1] + followerNode._relative_y;
            }
        }
    } else {
        followerNode._target_tracker = null;
    }
}

function snapToTarget(followerNode) {
    if (!app.graph) return;
    if (app.configuring) return;
    let targetNode = null;
    let isGet = false;
    let slotIndex = -1;
    if (followerNode.outputs && followerNode.outputs.length > 0) {
        for (let out of followerNode.outputs) {
            if (out.links && out.links.length > 0) {
                const link = app.graph.links[out.links[0]];
                if (link) {
                    targetNode = app.graph.getNodeById(link.target_id);
                    slotIndex = link.target_slot;
                    isGet = true;
                    break;
                }
            }
        }
    }
    if (!targetNode && followerNode.inputs && followerNode.inputs.length > 0) {
        for (let inSlot = 0; inSlot < followerNode.inputs.length; inSlot++) {
            let inp = followerNode.inputs[inSlot];
            if (inp.link) {
                const link = app.graph.links[inp.link];
                if (link) {
                    targetNode = app.graph.getNodeById(link.origin_id);
                    slotIndex = link.origin_slot;
                    isGet = false;
                    break;
                }
            }
        }
    }
    if (targetNode && slotIndex !== -1 && !isGetSetNode(targetNode)) {
        const slotPos = targetNode.getConnectionPos(isGet ? true : false, slotIndex);
        if (slotPos) {
            let targetX = isGet ? (targetNode.pos[0] - followerNode.size[0] - 10) : (targetNode.pos[0] + targetNode.size[0] + 10);
            let targetY = slotPos[1] - followerNode.size[1] * 0.5;
            let overlap = true;
            let safetyCounter = 30;
            while (overlap && safetyCounter > 0) {
                overlap = false;
                safetyCounter--;
                for (let n of app.graph._nodes) {
                    if (n.id !== followerNode.id && isGetSetNode(n)) {
                        if (n._target_tracker && n._target_tracker.id === targetNode.id) {
                            if (Math.abs(n.pos[0] - targetX) < 20 && Math.abs(n.pos[1] - targetY) < followerNode.size[1] * 0.9) {
                                targetY += followerNode.size[1] + 5;
                                overlap = true;
                                break;
                            }
                        }
                    }
                }
            }
            followerNode.pos[0] = targetX;
            followerNode.pos[1] = targetY;
            followerNode._target_tracker = {id: targetNode.id};
            followerNode._relative_x = targetX - targetNode.pos[0];
            followerNode._relative_y = targetY - targetNode.pos[1];
            if (app.graph) app.graph.setDirtyCanvas(true, true);
        }
    }
}

function formatGetSetNode(node) {
    if (node._is_formatted_getset) return;
    node._is_formatted_getset = true;
    node.properties = node.properties || {};
    if (!node._orig_title) node._orig_title = node.title || node.type;
    if (node.widgets) {
        for (let w of node.widgets) {
            w.name = "";
        }
    }
    if (node.inputs) node.inputs.forEach(i => i.label = " ");
    if (node.outputs) node.outputs.forEach(o => o.label = " ");
    const origComputeSize = node.computeSize;
    node.computeSize = function (out) {
        let s = origComputeSize ? origComputeSize.call(this, out) : LGraphNode.prototype.computeSize.call(this, out);
        s[0] = Math.max(120, Math.min(s[0], 200));
        return s;
    };
    const origOnConnectionsChange = node.onConnectionsChange;
    node.onConnectionsChange = function (type, slotIndex, isConnected, link_info) {
        if (origOnConnectionsChange) origOnConnectionsChange.apply(this, arguments);
        if (app.configuring) return;
        this.properties = this.properties || {};
        if (!isConnected) {
            this.properties.manual_arranged = false;
        } else if (link_info) {
            if (!this.properties.manual_arranged) {
                snapToTarget(this);
                this.properties.manual_arranged = true;
            }
        }
    };
    setTimeout(() => {
        if (!node.flags.collapsed) {
            node.setSize(node.computeSize());
        }
    }, 10);
}

app.registerExtension({
    name: "XXBuHuo.GetSetFollower",
    setup() {
        const origOnNodeAdded = LGraph.prototype.onNodeAdded;
        LGraph.prototype.onNodeAdded = function (node) {
            if (origOnNodeAdded) origOnNodeAdded.apply(this, arguments);
            if (isGetSetNode(node)) {
                formatGetSetNode(node);
            }
        };
        const origDraw = LGraphCanvas.prototype.draw;
        LGraphCanvas.prototype.draw = function (keep_canvas, calculate_visible_area) {
            if (app.graph && app.graph._nodes) {
                for (let n of app.graph._nodes) {
                    if (isGetSetNode(n)) {
                        updateFollowerPosition(n);
                    }
                }
            }
            if (origDraw) origDraw.apply(this, arguments);
        };
        const origDrawForeground = LGraphCanvas.prototype.drawForeground;
        LGraphCanvas.prototype.drawForeground = function (ctx, visible_area) {
            if (origDrawForeground) origDrawForeground.apply(this, arguments);
            const selected_nodes = this.selected_nodes ? Object.values(this.selected_nodes) : [];
            let hasSelectedTarget = false;
            ctx.save();
            for (let node of selected_nodes) {
                if (isGetSetNode(node)) {
                    hasSelectedTarget = true;
                    if (node.outputs) {
                        for (let outSlot = 0; outSlot < node.outputs.length; outSlot++) {
                            const out = node.outputs[outSlot];
                            if (out.links) {
                                for (let linkId of out.links) {
                                    const link = app.graph.links[linkId];
                                    if (!link) continue;
                                    const targetNode = app.graph.getNodeById(link.target_id);
                                    if (!targetNode) continue;
                                    try {
                                        const p1 = node.getConnectionPos(false, outSlot);
                                        const p2 = targetNode.getConnectionPos(true, link.target_slot);
                                        if (!p1 || !p2) continue;
                                        ctx.beginPath();
                                        ctx.moveTo(p1[0], p1[1]);
                                        const dist = Math.max(Math.abs(p1[0] - p2[0]) * 0.5, 30);
                                        ctx.bezierCurveTo(p1[0] + dist, p1[1], p2[0] - dist, p2[1], p2[0], p2[1]);
                                        ctx.strokeStyle = "#4DB8FF";
                                        ctx.lineWidth = 3;
                                        ctx.setLineDash([8, 8]);
                                        ctx.lineDashOffset = -(performance.now() / 15);
                                        ctx.stroke();
                                        ctx.shadowColor = "#4DB8FF";
                                        ctx.shadowBlur = 8;
                                        ctx.stroke();
                                        ctx.shadowBlur = 0;
                                    } catch (e) {
                                    }
                                }
                            }
                        }
                    }
                    if (node.inputs) {
                        for (let inSlot = 0; inSlot < node.inputs.length; inSlot++) {
                            const inp = node.inputs[inSlot];
                            if (inp.link) {
                                const link = app.graph.links[inp.link];
                                if (!link) continue;
                                const originNode = app.graph.getNodeById(link.origin_id);
                                if (!originNode) continue;
                                try {
                                    const p1 = originNode.getConnectionPos(false, link.origin_slot);
                                    const p2 = node.getConnectionPos(true, inSlot);
                                    if (!p1 || !p2) continue;
                                    ctx.beginPath();
                                    ctx.moveTo(p1[0], p1[1]);
                                    const dist = Math.max(Math.abs(p1[0] - p2[0]) * 0.5, 30);
                                    ctx.bezierCurveTo(p1[0] + dist, p1[1], p2[0] - dist, p2[1], p2[0], p2[1]);
                                    ctx.strokeStyle = "#FF8C00";
                                    ctx.lineWidth = 3;
                                    ctx.setLineDash([8, 8]);
                                    ctx.lineDashOffset = -(performance.now() / 15);
                                    ctx.stroke();
                                    ctx.shadowColor = "#FF8C00";
                                    ctx.shadowBlur = 8;
                                    ctx.stroke();
                                    ctx.shadowBlur = 0;
                                } catch (e) {
                                }
                            }
                        }
                    }
                }
            }
            ctx.restore();
            if (hasSelectedTarget) {
                this.setDirty(true, true);
            }
        };
    },
    loadedGraphNode(node) {
        if (isGetSetNode(node)) {
            formatGetSetNode(node);
        }
    }
});