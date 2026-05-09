import {app} from "../../../scripts/app.js";

function getGlobalNodes(typeName) {
    let result = [];
    let visited = new Set();

    function search(graph) {
        if (!graph || visited.has(graph)) return;
        visited.add(graph);
        let nodes = graph._nodes || graph.nodes;
        if (!nodes) return;
        for (let n of nodes) {
            if (n.type === typeName) result.push(n);
            if (n.getInnerGraph) search(n.getInnerGraph());
            if (n.subgraph) search(n.subgraph);
        }
    }

    search(app.graph);
    return result;
}

function getGlobalGroups() {
    let result = [];
    let visited = new Set();

    function search(graph) {
        if (!graph || visited.has(graph)) return;
        visited.add(graph);
        if (graph._groups) result.push(...graph._groups);
        let nodes = graph._nodes || graph.nodes;
        if (nodes) {
            for (let n of nodes) {
                if (n.getInnerGraph) search(n.getInnerGraph());
                if (n.subgraph) search(n.subgraph);
            }
        }
    }

    search(app.graph);
    return result;
}

function getTrueUpstreamNode(graph, parentNode, inp) {
    if (!inp.link) return null;
    let innerLink = graph.links[inp.link];
    if (!innerLink) return null;
    let originNode = graph.getNodeById(innerLink.origin_id);
    if (!originNode) return null;
    if (originNode.type !== "GraphInput" && originNode.type !== "PrimitiveNode") {
        return originNode;
    }
    if (parentNode && parentNode.inputs) {
        let mappedPInp = null;
        let gName = originNode.title || originNode.properties?.name || originNode.name;
        if (gName) {
            mappedPInp = parentNode.inputs.find(pi => pi.name === gName);
        }
        if (!mappedPInp) {
            mappedPInp = parentNode.inputs.find(pi => pi.name === inp.name || (inp._custom_label && pi.name === inp._custom_label));
        }
        if (!mappedPInp && inp._custom_label) {
            mappedPInp = parentNode.inputs.find(pi => pi.name && pi.name.includes(inp._custom_label));
        }
        if (mappedPInp && mappedPInp.link) {
            let extLink = app.graph.links[mappedPInp.link];
            if (extLink) {
                return app.graph.getNodeById(extLink.origin_id);
            }
        }
    }
    return originNode;
}

function getTrueOriginInfo(graph, node, slotIndex) {
    let inp = node.inputs[slotIndex];
    if (!inp || !inp.link) return null;
    let link = graph.links[inp.link];
    if (!link) return null;
    let originNode = graph.getNodeById(link.origin_id);
    if (!originNode) return null;
    if (originNode.type !== "GraphInput" && originNode.type !== "PrimitiveNode") {
        let originOut = null;
        if (originNode.outputs) originOut = originNode.outputs[link.origin_slot] || originNode.outputs[0];
        return {node: originNode, output: originOut};
    }
    let parentNode = findParentNodeOfGraph(graph);
    if (parentNode) {
        let parentGraph = parentNode.graph || app.graph;
        let proxyName = originNode.properties?.name || originNode.title || originNode.name;
        let pIdx = parentNode.inputs?.findIndex(pi => pi.name === proxyName);
        if (pIdx === -1 || pIdx === undefined) pIdx = parentNode.inputs?.findIndex(pi => pi.name === inp.name);
        if ((pIdx === -1 || pIdx === undefined) && inp._custom_label) pIdx = parentNode.inputs?.findIndex(pi => pi.name && pi.name.includes(inp._custom_label));
        if (pIdx !== -1 && pIdx !== undefined) {
            return getTrueOriginInfo(parentGraph, parentNode, pIdx);
        }
    }
    return {node: originNode, output: null};
}

function traceUpstream(graph, node, slotIndex, linksToColor, nodesToMute, visitedLinks = new Set()) {
    let inp = node.inputs[slotIndex];
    if (!inp || !inp.link) return;
    let link = graph.links[inp.link];
    if (!link || visitedLinks.has(link.id)) return;
    visitedLinks.add(link.id);
    linksToColor.push(link);
    let originNode = graph.getNodeById(link.origin_id);
    if (!originNode) return;
    if (originNode.type !== "GraphInput" && originNode.type !== "PrimitiveNode") {
        nodesToMute.add(originNode);
        return;
    }
    let parentNode = findParentNodeOfGraph(graph);
    if (parentNode) {
        let parentGraph = parentNode.graph || app.graph;
        let proxyName = originNode.properties?.name || originNode.title || originNode.name;
        let pIdx = parentNode.inputs?.findIndex(pi => pi.name === proxyName);
        if (pIdx === -1 || pIdx === undefined) pIdx = parentNode.inputs?.findIndex(pi => pi.name === inp.name);
        if ((pIdx === -1 || pIdx === undefined) && inp._custom_label) pIdx = parentNode.inputs?.findIndex(pi => pi.name && pi.name.includes(inp._custom_label));
        if (pIdx !== -1 && pIdx !== undefined) {
            traceUpstream(parentGraph, parentNode, pIdx, linksToColor, nodesToMute, visitedLinks);
        }
    }
}

function findParentNodeOfGraph(targetGraph) {
    let result = null;

    function search(g) {
        if (!g || !g._nodes || result) return;
        for (let n of g._nodes) {
            let inner = n.getInnerGraph ? n.getInnerGraph() : n.subgraph;
            if (inner === targetGraph) {
                result = n;
                return;
            }
            if (inner) search(inner);
        }
    }

    search(app.graph);
    return result;
}

function getPrettyLabel(name) {
    if (!name) return "";
    let n = name.toUpperCase();
    if (n.includes("MODEL")) return "模型";
    if (n.includes("CLIP")) return "CLIP";
    if (n.includes("VAE")) return "VAE";
    if (n.includes("LATENT")) return "Latent";
    if (n.includes("CONDITIONING")) return "条件";
    if (n.includes("IMAGE")) return "图像";
    if (n.includes("MASK")) return "遮罩";
    if (n.includes("CONTROL_NET")) return "ControlNet";
    return name;
}

function parseGroupNames(inputStr) {
    if (!inputStr) return [];
    return inputStr.split(/[,，;；]+/).map(s => s.trim()).filter(s => s);
}

function joinGroupNames(names) {
    return names.join(", ");
}

app.registerExtension({
    name: "XXBuHuo.NexusRouter",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name === "XXBuHuo_NexusRouter") {
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                if (onNodeCreated) onNodeCreated.apply(this, arguments);
                if (!this.customGroupNames) this.customGroupNames = ["Group 1"];
                if (!this.groupNamesInput) this.groupNamesInput = joinGroupNames(this.customGroupNames);
                this._last_active_group = "Group 1";
                const wireWidgetIndex = this.widgets.findIndex(w => w.name === "连线 (Wires)");
                if (wireWidgetIndex !== -1) {
                    if (this.widgets[wireWidgetIndex].onRemove) this.widgets[wireWidgetIndex].onRemove();
                    this.widgets.splice(wireWidgetIndex, 1);
                }
                this.addWidget("button", "🔄 更新", null, () => this.updatePorts(true));
                this.updatePorts(true);
            };
            nodeType.prototype.forceSyncAllPorts = function () {
                const portsWidget = this.widgets.find(w => w.name === "端口 (Ports)");
                const maxPorts = portsWidget ? Math.max(1, portsWidget.value) : 4;
                for (let p = 1; p <= maxPorts; p++) {
                    let refType = null;
                    for (let i = 0; i < this.inputs.length; i++) {
                        if (this.inputs[i].name.endsWith(`_Port${p}`) && this.inputs[i].link) {
                            refType = this.inputs[i]._actual_type || this.inputs[i].type;
                            break;
                        }
                    }
                    if (refType && refType !== "*") {
                        for (let i = 0; i < this.inputs.length; i++) {
                            if (this.inputs[i].name.endsWith(`_Port${p}`)) {
                                this.inputs[i].type = refType;
                                this.inputs[i]._actual_type = refType;
                                if (!this.inputs[i].link) {
                                    this.inputs[i]._custom_label = "";
                                    this.inputs[i].label = " ";
                                }
                            }
                        }
                    } else {
                        for (let i = 0; i < this.inputs.length; i++) {
                            if (this.inputs[i].name.endsWith(`_Port${p}`)) {
                                this.inputs[i].type = "*";
                                this.inputs[i]._actual_type = "*";
                                if (!this.inputs[i].link) {
                                    this.inputs[i]._custom_label = "";
                                    this.inputs[i].label = " ";
                                }
                            }
                        }
                    }
                }
                if (this.graph) this.graph.setDirtyCanvas(true, true);
            };
            const onSerialize = nodeType.prototype.onSerialize;
            nodeType.prototype.onSerialize = function (obj) {
                if (onSerialize) onSerialize.apply(this, arguments);
                obj.customGroupNames = this.customGroupNames;
                obj.groupNamesInput = this.groupNamesInput;
            };
            const onConfigure = nodeType.prototype.onConfigure;
            nodeType.prototype.onConfigure = function (info) {
                if (onConfigure) onConfigure.apply(this, arguments);
                if (info.customGroupNames) this.customGroupNames = info.customGroupNames;
                if (info.groupNamesInput) this.groupNamesInput = info.groupNamesInput;
                if (this.customGroupNames && !this.groupNamesInput) {
                    this.groupNamesInput = joinGroupNames(this.customGroupNames);
                }
                const activeWidget = this.widgets?.find(w => w.name === "激活 (Active)");
                if (activeWidget) this._last_active_group = activeWidget.value;
                this.updatePorts(true);
            };
            const onConnectionsChange = nodeType.prototype.onConnectionsChange;
            nodeType.prototype.onConnectionsChange = function (type, index, connected, link_info) {
                const activeW = this.widgets?.find(w => w.name === "激活 (Active)");
                if (activeW && activeW.value) {
                    this._last_active_group = activeW.value;
                }
                if (onConnectionsChange) onConnectionsChange.apply(this, arguments);
                if (type === LiteGraph.INPUT && this.inputs[index]) {
                    const inp = this.inputs[index];
                    if (inp.name === "激活 (Active)" && inp.type !== "*") {
                        inp.type = "*";
                    }
                    if (inp.name.match(/^G\d+_Port\d+/)) {
                        const portMatch = inp.name.match(/^G\d+_(Port\d+)/);
                        if (portMatch) {
                            const portIdx = parseInt(portMatch[1].replace("Port", ""));
                            const alignWidget = this.widgets.find(w => w.name === "对齐 (Align)");
                            const isAligned = alignWidget && alignWidget.value === "On";
                            if (connected && link_info) {
                                let originInfo = getTrueOriginInfo(this.graph || app.graph, this, index);
                                if (originInfo && originInfo.node && originInfo.output) {
                                    let trueOrigin = originInfo.node;
                                    let originOut = originInfo.output;
                                    const actualType = originOut.type || "*";
                                    let nodeTitle = trueOrigin.title || trueOrigin.type || "";
                                    let outPretty = getPrettyLabel(originOut.name || originOut.type || "");
                                    let newLabel = nodeTitle;
                                    if (trueOrigin.outputs && trueOrigin.outputs.length > 1) {
                                        newLabel = `${nodeTitle} - ${outPretty}`;
                                    }
                                    inp._custom_label = newLabel;
                                    inp._actual_type = actualType;
                                    inp.label = " ";
                                    if (isAligned) {
                                        inp.type = actualType;
                                        for (let i = 0; i < this.inputs.length; i++) {
                                            if (this.inputs[i].name.endsWith(`_Port${portIdx}`)) {
                                                this.inputs[i].type = actualType;
                                                this.inputs[i]._actual_type = actualType;
                                                if (!this.inputs[i].link) {
                                                    this.inputs[i]._custom_label = "";
                                                    this.inputs[i].label = " ";
                                                }
                                            }
                                        }
                                    } else {
                                        inp.type = "*";
                                    }
                                }
                            } else if (!connected) {
                                inp._custom_label = "";
                                inp._actual_type = "*";
                                inp.label = " ";
                                let anyConnected = false;
                                let refType = "*";
                                for (let i = 0; i < this.inputs.length; i++) {
                                    if (this.inputs[i].name.endsWith(`_Port${portIdx}`) && this.inputs[i].link) {
                                        anyConnected = true;
                                        refType = this.inputs[i]._actual_type || "*";
                                        break;
                                    }
                                }
                                if (!anyConnected) {
                                    for (let i = 0; i < this.inputs.length; i++) {
                                        if (this.inputs[i].name.endsWith(`_Port${portIdx}`)) {
                                            this.inputs[i].type = "*";
                                            this.inputs[i]._actual_type = "*";
                                            this.inputs[i]._custom_label = "";
                                            this.inputs[i].label = " ";
                                        }
                                    }
                                } else {
                                    if (isAligned) {
                                        inp.type = refType;
                                        inp._actual_type = refType;
                                    } else {
                                        inp.type = "*";
                                        inp._actual_type = "*";
                                    }
                                }
                            }
                        }
                    }
                }
                setTimeout(() => {
                    const postActiveW = this.widgets?.find(w => w.name === "激活 (Active)");
                    if (postActiveW && this._last_active_group && postActiveW.value !== this._last_active_group) {
                        postActiveW.value = this._last_active_group;
                    }
                    this.updateVisualStates();
                }, 10);
            };
            nodeType.prototype.updateVisualStates = function (forcedActiveValue = null) {
                let graph = this.graph || app.graph;
                const activeGroupWidget = this.widgets?.find(w => w.name === "激活 (Active)");
                let actualActiveValue = forcedActiveValue !== null ? forcedActiveValue : (activeGroupWidget ? activeGroupWidget.value : null);
                const activeInput = this.inputs?.find(inp => inp.name === "激活 (Active)");
                if (activeInput) {
                    let originInfo = getTrueOriginInfo(graph, this, this.inputs.indexOf(activeInput));
                    if (originInfo && originInfo.node && originInfo.node.type === "XXBuHuo_CategorySelector") {
                        const selWidget = originInfo.node.widgets?.find(w => w.name === "选择 (Select)");
                        if (selWidget && selWidget.value) actualActiveValue = selWidget.value;
                    }
                }
                let activeGroupNum = 1;
                for (let i = 0; i < this.customGroupNames.length; i++) {
                    if (this.customGroupNames[i] === actualActiveValue) {
                        activeGroupNum = i + 1;
                        break;
                    }
                }
                if (activeGroupNum === 1) {
                    const match = actualActiveValue.match(/Group (\d+)/);
                    if (match) activeGroupNum = parseInt(match[1]);
                }
                let activeLinks = [];
                let activeNodes = new Set();
                let inactiveLinks = [];
                let inactiveNodes = new Set();
                for (let i = 0; i < this.inputs.length; i++) {
                    const inp = this.inputs[i];
                    if (!inp.name) continue;
                    const match = inp.name.match(/^G(\d+)_/);
                    if (!match) continue;
                    const groupNum = parseInt(match[1]);
                    const isActive = (groupNum === activeGroupNum);
                    if (inp.name.endsWith("_header")) {
                    } else {
                        if (isActive) {
                            delete inp.color_on;
                            delete inp.color_off;
                        } else {
                            inp.color_on = "rgba(150, 150, 150, 0.5)";
                            inp.color_off = "rgba(150, 150, 150, 0.5)";
                        }
                        if (isActive) traceUpstream(graph, this, i, activeLinks, activeNodes);
                        else traceUpstream(graph, this, i, inactiveLinks, inactiveNodes);
                    }
                }
                activeLinks.forEach(link => {
                    delete link.color;
                });
                inactiveLinks.forEach(link => {
                    link.color = "rgba(150, 150, 150, 0.4)";
                });
                activeNodes.forEach(node => {
                    if (node.mode !== 0) node.mode = 0;
                });
                inactiveNodes.forEach(node => {
                    if (!activeNodes.has(node) && node.mode !== 4) node.mode = 4;
                });
                if (this.outputs && this.outputs.length > 1) {
                    for (let p = 1; p < this.outputs.length; p++) {
                        const activeInputName = `G${activeGroupNum}_Port${p}`;
                        const activeInp = this.inputs.find(inp => inp.name === activeInputName);
                        if (activeInp) {
                            const expectedType = activeInp._actual_type && activeInp._actual_type !== "*" ? activeInp._actual_type : (activeInp.type !== "*" ? activeInp.type : "*");
                            this.outputs[p].type = expectedType;
                            if (activeInp.link && activeInp._custom_label) {
                                this.outputs[p].name = activeInp._custom_label;
                                this.outputs[p].label = activeInp._custom_label;
                            } else {
                                this.outputs[p].name = " ";
                                this.outputs[p].label = " ";
                            }
                        }
                    }
                }
                const activeName = this.customGroupNames[activeGroupNum - 1] || `Group ${activeGroupNum}`;
                const allNames = this.customGroupNames;
                const controllers = getGlobalNodes("XXBuHuo_JointController");
                controllers.forEach(ctrl => {
                    if (ctrl.inputs && ctrl.inputs[0] && ctrl.inputs[0].link) {
                        if (ctrl.applyControl) ctrl.applyControl(activeName, allNames);
                    }
                });
                if (app.canvas && app.canvas.ctx && this.inputs) {
                    const ctx = app.canvas.ctx;
                    ctx.save();
                    let maxLabelWidth = 0;
                    for (let i = 0; i < this.inputs.length; i++) {
                        const inp = this.inputs[i];
                        let text = "";
                        if (inp.name.endsWith("_header")) {
                            const match = inp.name.match(/^G(\d+)_/);
                            if (match) {
                                const groupNum = parseInt(match[1]);
                                text = this.customGroupNames?.[groupNum - 1] || `Group ${groupNum}`;
                                ctx.font = "bold 12px Arial";
                            }
                        } else {
                            text = inp._custom_label || "";
                            ctx.font = "12px Arial";
                        }
                        if (text) {
                            const w = ctx.measureText(text).width;
                            if (w > maxLabelWidth) maxLabelWidth = w;
                        }
                    }
                    ctx.restore();
                    const minWidth = Math.max(300, maxLabelWidth * 2 + 100);
                    if (this.size[0] < minWidth || this.size[0] > minWidth + 50) {
                        this.size[0] = minWidth;
                    }
                }
                if (graph) graph.setDirtyCanvas(true, true);
                if (app.graph) app.graph.setDirtyCanvas(true, true);
            };
            nodeType.prototype.updatePorts = function (forceUpdate = false) {
                for (let i = this.widgets.length - 1; i >= 0; i--) {
                    if (this.widgets[i].name === "组名 (Name)") {
                        if (this.widgets[i].onRemove) {
                            this.widgets[i].onRemove();
                        }
                        this.widgets.splice(i, 1);
                    }
                }
                const countWidget = this.widgets.find(w => w.name === "组数 (Groups)");
                if (!countWidget) return;
                const targetCount = Math.max(1, countWidget.value);
                if (!this.inputs) this.inputs = [];
                if (!this.customGroupNames) this.customGroupNames = [];
                while (this.customGroupNames.length < targetCount) {
                    this.customGroupNames.push(`Group ${this.customGroupNames.length + 1}`);
                }
                this.groupNamesInput = joinGroupNames(this.customGroupNames);
                const universalPerfectDraw = function (ctx, node, widget_width, y, H) {
                    const margin = 15;
                    const bg_color = LiteGraph.WIDGET_BGCOLOR || "#222";
                    const text_color = LiteGraph.WIDGET_TEXT_COLOR || "#ddd";
                    const secondary_text_color = LiteGraph.WIDGET_SECONDARY_TEXT_COLOR || "#999";
                    ctx.fillStyle = bg_color;
                    ctx.beginPath();
                    if (ctx.roundRect) ctx.roundRect(margin, y, widget_width - margin * 2, H, H * 0.5);
                    else ctx.rect(margin, y, widget_width - margin * 2, H);
                    ctx.fill();
                    ctx.fillStyle = secondary_text_color;
                    ctx.beginPath();
                    ctx.moveTo(margin + 16, y + 5);
                    ctx.lineTo(margin + 6, y + H * 0.5);
                    ctx.lineTo(margin + 16, y + H - 5);
                    ctx.fill();
                    ctx.beginPath();
                    ctx.moveTo(widget_width - margin - 16, y + 5);
                    ctx.lineTo(widget_width - margin - 6, y + H * 0.5);
                    ctx.lineTo(widget_width - margin - 16, y + H - 5);
                    ctx.fill();
                    ctx.fillStyle = secondary_text_color;
                    ctx.textAlign = "left";
                    ctx.textBaseline = "middle";
                    const labelX = margin + 20;
                    ctx.fillText(this.name, labelX, y + H * 0.5 + 1);
                    const labelWidth = ctx.measureText(this.name).width;
                    const safeStartX = labelX + labelWidth + 10;
                    const safeEndX = widget_width - margin - 24;
                    const safeWidth = Math.max(0, safeEndX - safeStartX);
                    ctx.save();
                    ctx.beginPath();
                    ctx.rect(safeStartX, y, safeWidth, H);
                    ctx.clip();
                    ctx.fillStyle = text_color;
                    let val = this.value;
                    if (val === undefined || val === null) val = "";
                    let display_val = String(val);
                    const textWidth = ctx.measureText(display_val).width;
                    if (textWidth <= safeWidth) {
                        ctx.textAlign = "right";
                        ctx.fillText(display_val, safeEndX, y + H * 0.5 + 1);
                    } else {
                        ctx.textAlign = "left";
                        ctx.fillText(display_val, safeStartX, y + H * 0.5 + 1);
                    }
                    ctx.restore();
                };
                const updateBtnIndex = this.widgets.findIndex(w => w.name === "🔄 更新");
                const newWidgets = [];
                for (let i = 0; i < updateBtnIndex; i++) {
                    const w = this.widgets[i];
                    if (w.name !== "组名 (Name)") {
                        if (w.name === "组数 (Groups)" || w.name === "激活 (Active)" || w.name === "端口 (Ports)" || w.name === "对齐 (Align)") {
                            w.draw = universalPerfectDraw;
                        }
                        if (w.name === "对齐 (Align)") {
                            w.callback = function (value) {
                                if (value === "On") {
                                    this.forceSyncAllPorts();
                                } else {
                                    for (let idx = 0; idx < this.inputs.length; idx++) {
                                        const inp = this.inputs[idx];
                                        if (inp.name.match(/^G\d+_Port\d+/)) {
                                            inp.type = "*";
                                        }
                                    }
                                }
                                this.updateVisualStates();
                                if (this.graph) this.graph.setDirtyCanvas(true, true);
                            }.bind(this);
                        }
                        newWidgets.push(w);
                    }
                }
                const namesWidget = this.addWidget("text", "组名 (Name)", this.groupNamesInput || "", (value) => {
                    this.groupNamesInput = value;
                    this.customGroupNames = parseGroupNames(value);
                    while (this.customGroupNames.length < targetCount) {
                        this.customGroupNames.push(`Group ${this.customGroupNames.length + 1}`);
                    }
                    const activeGroupWidget = this.widgets.find(w => w.name === "激活 (Active)");
                    if (activeGroupWidget) {
                        let newOptions = [];
                        for (let i = 1; i <= targetCount; i++) newOptions.push(this.customGroupNames[i - 1] || `Group ${i}`);
                        activeGroupWidget.options.values = newOptions;
                    }
                    this.updateVisualStates();
                });
                namesWidget.name = "组名 (Name)";
                namesWidget.draw = universalPerfectDraw;
                newWidgets.push(namesWidget);
                if (updateBtnIndex !== -1) {
                    const btn = this.widgets[updateBtnIndex];
                    if (!btn._hooked) {
                        const origCb = btn.callback;
                        btn.callback = function () {
                            btn._is_pressed = true;
                            if (this.graph) this.graph.setDirtyCanvas(true, true);
                            setTimeout(() => {
                                btn._is_pressed = false;
                                if (this.graph) this.graph.setDirtyCanvas(true, true);
                            }, 100);
                            if (origCb) origCb.apply(this, arguments);
                        }.bind(this);
                        btn._hooked = true;
                    }
                    btn.draw = function (ctx, node, widget_width, y, H) {
                        const margin = 15;
                        const is_pressed = this._is_pressed;
                        ctx.fillStyle = LiteGraph.WIDGET_BGCOLOR || "#222";
                        ctx.beginPath();
                        if (ctx.roundRect) ctx.roundRect(margin, y, widget_width - margin * 2, H, 4);
                        else ctx.rect(margin, y, widget_width - margin * 2, H);
                        ctx.fill();
                        if (is_pressed) {
                            ctx.fillStyle = "rgba(0, 0, 0, 0.4)";
                            ctx.fill();
                        }
                        ctx.strokeStyle = LiteGraph.WIDGET_OUTLINE_COLOR || "#000";
                        ctx.lineWidth = 1;
                        ctx.stroke();
                        ctx.fillStyle = LiteGraph.WIDGET_TEXT_COLOR || "#ddd";
                        ctx.font = "12px Arial";
                        ctx.textAlign = "center";
                        ctx.textBaseline = "middle";
                        const textY = y + H * 0.5 + (is_pressed ? 1.5 : 0) + 1.2;
                        ctx.fillText(this.name, widget_width * 0.5, textY);
                    };
                    newWidgets.push(btn);
                }
                this.widgets = newWidgets;
                const portsWidget = this.widgets.find(w => w.name === "端口 (Ports)");
                const targetPortsCount = portsWidget ? Math.max(1, portsWidget.value) : 4;
                for (let i = this.inputs.length - 1; i >= 0; i--) {
                    const inp = this.inputs[i];
                    if (!inp.name) continue;
                    const matchG = inp.name.match(/^G(\d+)_/);
                    const matchP = inp.name.match(/_Port(\d+)$/);
                    if (matchG) {
                        const gNum = parseInt(matchG[1]);
                        if (gNum > targetCount) {
                            this.removeInput(i);
                            continue;
                        }
                        if (matchP) {
                            const pNum = parseInt(matchP[1]);
                            if (pNum > targetPortsCount) this.removeInput(i);
                        }
                    }
                }
                for (let g = 1; g <= targetCount; g++) {
                    const prefix = `G${g}_`;
                    const portNames = [`${prefix}header`];
                    for (let p = 1; p <= targetPortsCount; p++) {
                        portNames.push(`${prefix}Port${p}`);
                    }
                    portNames.forEach(pName => {
                        const existingInp = this.inputs.find(inp => inp.name === pName);
                        if (!existingInp) {
                            let type = "*";
                            this.addInput(pName, type, {
                                label: " ",
                                color_off: pName.endsWith("_header") ? "rgba(0,0,0,0)" : undefined
                            });
                            const newInp = this.inputs[this.inputs.length - 1];
                            newInp._custom_label = "";
                            newInp._actual_type = "*";
                        }
                    });
                }
                this.inputs.sort((a, b) => {
                    const matchA = a.name.match(/^G(\d+)_/);
                    const matchB = b.name.match(/^G(\d+)_/);
                    if (!matchA || !matchB) return 0;
                    const gA = parseInt(matchA[1]);
                    const gB = parseInt(matchB[1]);
                    if (gA !== gB) return gA - gB;
                    const isHeaderA = a.name.endsWith("_header");
                    const isHeaderB = b.name.endsWith("_header");
                    if (isHeaderA && !isHeaderB) return -1;
                    if (!isHeaderA && isHeaderB) return 1;
                    const pA = a.name.match(/_Port(\d+)$/);
                    const pB = b.name.match(/_Port(\d+)$/);
                    if (pA && pB) {
                        return parseInt(pA[1]) - parseInt(pB[1]);
                    }
                    return 0;
                });
                if (this.graph) {
                    for (let i = 0; i < this.inputs.length; i++) {
                        const inp = this.inputs[i];
                        if (inp.link) {
                            const linkObj = this.graph.links[inp.link];
                            if (linkObj) {
                                linkObj.target_slot = i;
                            }
                        }
                    }
                }
                if (!this.outputs) this.outputs = [];
                if (this.outputs.length === 0) {
                    this.addOutput("CTRL", "XX_CTRL");
                } else {
                    this.outputs[0].name = "CTRL";
                    this.outputs[0].type = "XX_CTRL";
                    this.outputs[0].label = "CTRL";
                }
                for (let p = 1; p <= targetPortsCount; p++) {
                    if (this.outputs.length <= p) {
                        let out = this.addOutput(" ", "*");
                        out.label = " ";
                    }
                }
                while (this.outputs.length > targetPortsCount + 1) {
                    this.removeOutput(this.outputs.length - 1);
                }
                const activeGroupWidget = this.widgets.find(w => w.name === "激活 (Active)");
                if (activeGroupWidget) {
                    let newOptions = [];
                    for (let i = 1; i <= targetCount; i++) newOptions.push(this.customGroupNames[i - 1] || `Group ${i}`);
                    activeGroupWidget.options.values = newOptions;
                    let targetValue = this._last_active_group || activeGroupWidget.value;
                    if (!newOptions.includes(targetValue)) targetValue = newOptions[0];
                    activeGroupWidget.value = targetValue;
                    this._last_active_group = targetValue;
                    const origCallback = activeGroupWidget.callback;
                    activeGroupWidget.callback = function (value) {
                        this._last_active_group = value;
                        if (origCallback) origCallback.apply(this, arguments);
                        this.updateVisualStates();
                    }.bind(this);
                }
                const alignWidget = this.widgets.find(w => w.name === "对齐 (Align)");
                if (alignWidget && alignWidget.value === "On") {
                    this.forceSyncAllPorts();
                }
                const selectors = getGlobalNodes("XXBuHuo_CategorySelector");
                selectors.forEach(sel => {
                    if (sel.syncOptions) sel.syncOptions();
                });
                this.updateVisualStates();
                if (forceUpdate) {
                    this.setSize([this.size[0], this.computeSize()[1]]);
                    if (this.graph) this.graph.setDirtyCanvas(true, true);
                    if (app.graph) app.graph.setDirtyCanvas(true, true);
                }
            };
            const onDrawForeground = nodeType.prototype.onDrawForeground;
            nodeType.prototype.onDrawForeground = function (ctx) {
                if (onDrawForeground) onDrawForeground.apply(this, arguments);
                const activeGroupWidget = this.widgets.find(w => w.name === "激活 (Active)");
                let activeGroupNum = 1;
                let actualActiveValue = activeGroupWidget ? activeGroupWidget.value : null;
                let graph = this.graph || app.graph;
                const activeInput = this.inputs?.find(inp => inp.name === "激活 (Active)");
                if (activeInput) {
                    let originInfo = getTrueOriginInfo(graph, this, this.inputs.indexOf(activeInput));
                    if (originInfo && originInfo.node && originInfo.node.type === "XXBuHuo_CategorySelector") {
                        const selWidget = originInfo.node.widgets?.find(w => w.name === "选择 (Select)");
                        if (selWidget && selWidget.value) actualActiveValue = selWidget.value;
                    }
                }
                if (actualActiveValue) {
                    for (let i = 0; i < this.customGroupNames.length; i++) {
                        if (this.customGroupNames[i] === actualActiveValue) {
                            activeGroupNum = i + 1;
                            break;
                        }
                    }
                    if (activeGroupNum === 1) {
                        const match = actualActiveValue.match(/Group (\d+)/);
                        if (match) activeGroupNum = parseInt(match[1]);
                    }
                }
                ctx.save();
                if (this.inputs) {
                    for (let i = 0; i < this.inputs.length; i++) {
                        const inp = this.inputs[i];
                        if (!inp.name) continue;
                        const match = inp.name.match(/^G(\d+)_/);
                        if (!match) continue;
                        const groupNum = parseInt(match[1]);
                        const isActive = (groupNum === activeGroupNum);
                        const pos = this.getConnectionPos(true, i);
                        if (!pos) continue;
                        const TEXT_X = 16;
                        const local_y = pos[1] - this.pos[1];
                        if (inp.name.endsWith("_header")) {
                            const TEXT_Y = local_y + 1;
                            const displayName = this.customGroupNames?.[groupNum - 1] || `Group ${groupNum}`;
                            ctx.fillStyle = "#3B82F6";
                            ctx.globalAlpha = isActive ? 1.0 : 0.5;
                            ctx.font = `bold 12px Arial`;
                            ctx.textAlign = "left";
                            ctx.textBaseline = "middle";
                            ctx.fillText(displayName, TEXT_X, TEXT_Y);
                            ctx.globalAlpha = 1.0;
                        } else {
                            let labelText = inp._custom_label || "";
                            const TEXT_Y = local_y + 1.23;
                            ctx.fillStyle = LiteGraph.NODE_TEXT_COLOR || "#dddddd";
                            if (isActive) {
                                ctx.globalAlpha = inp.link ? 1.0 : 0.6;
                            } else {
                                ctx.globalAlpha = 0.35;
                            }
                            ctx.font = `12px Arial`;
                            ctx.textAlign = "left";
                            ctx.textBaseline = "middle";
                            if (labelText) {
                                ctx.fillText(labelText, TEXT_X, TEXT_Y);
                            }
                            ctx.globalAlpha = 1.0;
                        }
                    }
                }
                ctx.restore();
            };
        }
    }
});
app.registerExtension({
    name: "XXBuHuo.JointController",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name === "XXBuHuo_JointController") {
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                if (onNodeCreated) onNodeCreated.apply(this, arguments);
                setTimeout(() => {
                    const modeWidget = this.widgets?.find(w => w.name === "控制模式 (Mode)");
                    if (modeWidget) {
                        const origCallback = modeWidget.callback;
                        modeWidget.callback = function (value) {
                            if (origCallback) origCallback.apply(this, arguments);
                            const routers = getGlobalNodes("XXBuHuo_NexusRouter");
                            routers.forEach(r => {
                                if (r.updateVisualStates) r.updateVisualStates();
                            });
                        }.bind(this);
                    }
                }, 50);
            };
            nodeType.prototype.applyControl = function (activeGroupName, allGroupNames) {
                const modeWidget = this.widgets?.find(w => w.name === "控制模式 (Mode)");
                const targetMode = (modeWidget && modeWidget.value.includes("Bypass")) ? 4 : 2;
                const groups = getGlobalGroups();
                let changed = false;
                for (let i = 0; i < groups.length; i++) {
                    const group = groups[i];
                    const groupTitle = group.title.trim();
                    if (allGroupNames.includes(groupTitle)) {
                        group.recomputeInsideNodes();
                        const nodesInGroup = group._nodes || [];
                        const isGroupActive = (groupTitle === activeGroupName.trim());
                        nodesInGroup.forEach(node => {
                            if (isGroupActive) {
                                if (node.mode !== 0) {
                                    node.mode = 0;
                                    changed = true;
                                }
                            } else {
                                if (node.mode !== targetMode) {
                                    node.mode = targetMode;
                                    changed = true;
                                }
                            }
                        });
                    }
                }
                if (changed && app.graph) app.graph.setDirtyCanvas(true, true);
            };
        }
    }
});
app.registerExtension({
    name: "XXBuHuo.CategorySelector",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name === "XXBuHuo_CategorySelector") {
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                if (onNodeCreated) onNodeCreated.apply(this, arguments);
                setTimeout(() => {
                    const selectWidget = this.widgets?.find(w => w.name === "选择 (Select)");
                    if (selectWidget) {
                        const origCallback = selectWidget.callback;
                        selectWidget.callback = function (value) {
                            if (origCallback) origCallback.apply(this, arguments);
                            const routers = getGlobalNodes("XXBuHuo_NexusRouter");
                            routers.forEach(r => {
                                const actW = r.widgets?.find(w => w.name === "激活 (Active)");
                                if (actW) actW.value = value;
                                r._last_active_group = value;
                                if (r.updateVisualStates) r.updateVisualStates(value);
                            });
                            if (this.graph) this.graph.setDirtyCanvas(true, true);
                            if (app.graph) app.graph.setDirtyCanvas(true, true);
                        }.bind(this);
                    }
                    this.syncOptions();
                }, 50);
            };
            const onConnectionsChange = nodeType.prototype.onConnectionsChange;
            nodeType.prototype.onConnectionsChange = function (type, index, connected, link_info) {
                if (onConnectionsChange) onConnectionsChange.apply(this, arguments);
                if (type === LiteGraph.OUTPUT && connected) {
                    this.syncOptions();
                }
            };
            nodeType.prototype.syncOptions = function () {
                const selectWidget = this.widgets?.find(w => w.name === "选择 (Select)");
                const routers = getGlobalNodes("XXBuHuo_NexusRouter");
                if (routers.length > 0 && selectWidget) {
                    const routerNode = routers[0];
                    if (routerNode.customGroupNames) {
                        selectWidget.options.values = [...routerNode.customGroupNames];
                        if (!selectWidget.options.values.includes(selectWidget.value)) {
                            selectWidget.value = selectWidget.options.values[0];
                        }
                        if (this.graph) this.graph.setDirtyCanvas(true, true);
                        if (app.graph) app.graph.setDirtyCanvas(true, true);
                    }
                }
            };
        }
    }
});