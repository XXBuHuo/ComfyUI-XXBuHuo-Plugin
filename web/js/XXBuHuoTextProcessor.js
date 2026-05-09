import {app} from "../../../scripts/app.js";

app.registerExtension({
    name: "XXBuHuo.TXTParagraphSplitter",
    async beforeRegisterNodeDef(t, e) {
        if ("XXBuHuoTextProcessor" === e.name) {
            const onNodeCreated = t.prototype.onNodeCreated;
            const onConfigure = t.prototype.onConfigure;
            t.prototype.onConfigure = function (info) {
                this._isRestored = true;
                if (onConfigure) {
                    onConfigure.apply(this, arguments);
                }
                if (info && info.size) {
                    this._saved_size = [info.size[0], info.size[1]];
                }
            };
            t.prototype.onNodeCreated = function () {
                if (onNodeCreated) {
                    onNodeCreated.apply(this, arguments);
                }
                this.uO(false);
                this.uI(false);
                this.addWidget("button", "更新端口", null, () => {
                    this.uI(true);
                    this.uO(true);
                });
                const setupVisibility = () => {
                    const foldableSettings = [
                        "分段方式", "段落优化", "输出模式",
                        "输出段落", "输入端口", "选取段落",
                        "筛选段落", "更新端口"
                    ];
                    const updateWidgets = (isInitialization = false) => {
                        const expandWidget = this.widgets.find(w => w.name === "展开参数");
                        const isExpanded = expandWidget ? expandWidget.value : false;
                        const oldMinSize = this.computeSize();
                        foldableSettings.forEach(n => {
                            const w = this.widgets.find(i => i.name === n);
                            if (!w) return;
                            if (w.origType === undefined) {
                                w.origType = w.type;
                                w.origComputeSize = w.computeSize;
                                w.origDraw = w.draw || null;
                            }
                            if (isExpanded) {
                                if (w.type === "hidden") {
                                    w.type = w.origType;
                                    w.computeSize = w.origComputeSize;
                                    if (w.origDraw) w.draw = w.origDraw;
                                    else delete w.draw;
                                }
                            } else {
                                if (w.type !== "hidden") {
                                    w.type = "hidden";
                                    w.computeSize = () => [0, -4];
                                    w.draw = () => {
                                    };
                                }
                            }
                        });
                        const newMinSize = this.computeSize();
                        if (isInitialization) {
                            if (!this._isRestored) {
                                this.size = [400, newMinSize[1] + 200];
                            } else if (this._saved_size) {
                                this.size = [this._saved_size[0], this._saved_size[1]];
                            }
                        } else {
                            const deltaY = newMinSize[1] - oldMinSize[1];
                            this.size[1] = Math.max(100, this.size[1] + deltaY);
                        }
                        app.graph.setDirtyCanvas(true, true);
                    };
                    const expandW = this.widgets.find(i => i.name === "展开参数");
                    if (expandW) {
                        if (!this.properties || !this.properties.initialized) {
                            expandW.value = false;
                            if (!this.properties) this.properties = {};
                            this.properties.initialized = true;
                        }
                        const origCallback = expandW.callback;
                        expandW.callback = function (v) {
                            origCallback?.apply(expandW, arguments);
                            updateWidgets(false);
                        };
                    }
                    updateWidgets(true);
                };
                setTimeout(() => {
                    setupVisibility();
                }, 50);
            };
            t.prototype.onExecuted = function (t) {
                if (t?.text) {
                    const e = this.widgets.find((t => "text" === t.name));
                    if (e) {
                        e.value = t.text[0];
                        this.setDirtyCanvas?.(!0, !0);
                    }
                }
            };
            t.prototype.uI = function (userTriggered = false) {
                if (!this.widgets) return;
                const e = this.widgets.find((t => "输入端口" === t.name));
                if (!e) return;
                const oldMinSize = this.computeSize();
                const i = () => {
                    const target = Math.max(1, e.value);
                    this.inputs || (this.inputs = []);
                    const current = this.inputs.filter((t => t.name.startsWith("any_"))).length;
                    if (target > current) {
                        for (let n = current + 1; n <= target; n++) this.addInput("any_" + n, "*");
                    } else if (target < current) {
                        let removed = 0;
                        for (let n = this.inputs.length - 1; n >= 0 && removed < current - target; n--) {
                            if (this.inputs[n].name.startsWith("any_") && parseInt(this.inputs[n].name.split("_")[1]) > target) {
                                this.removeInput(n);
                                removed++;
                            }
                        }
                    }
                };
                i();
                if (userTriggered) {
                    const newMinSize = this.computeSize();
                    const deltaY = newMinSize[1] - oldMinSize[1];
                    if (deltaY !== 0 && this.size) {
                        this.size[1] = this.size[1] + deltaY;
                    }
                    this.setDirtyCanvas(true, true);
                }
            };
            t.prototype.uO = function (userTriggered = false) {
                if (!this.widgets) return;
                const e = this.widgets.find((t => "输出段落" === t.name));
                if (!e) return;
                const oldMinSize = this.computeSize();
                const i = () => {
                    const target = Math.max(0, e.value);
                    this.outputs || (this.outputs = []);
                    if (this.outputs.length < 1) this.addOutput("数:", "STRING");
                    if (this.outputs.length < 2) this.addOutput("总段:", "STRING");
                    const current = this.outputs.length - 2;
                    if (target > current) {
                        for (let n = current + 1; n <= target; n++) this.addOutput("段落" + n, "STRING");
                    } else if (target < current) {
                        for (let n = 0; n < current - target; n++) this.removeOutput(this.outputs.length - 1);
                    }
                };
                i();
                if (userTriggered) {
                    const newMinSize = this.computeSize();
                    const deltaY = newMinSize[1] - oldMinSize[1];
                    if (deltaY !== 0 && this.size) {
                        this.size[1] = this.size[1] + deltaY;
                    }
                    this.setDirtyCanvas(true, true);
                }
            };
        }
    }
});