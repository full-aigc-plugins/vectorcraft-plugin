# VectorCraft 0.12.0 能力补充

官方发布：[v0.12.0](https://github.com/storytold/vectorcraft/releases/tag/v0.12.0)，提交 `8bc65329286dc1b84aa392997bb205613c3e96cb`。以下为独立原生CLI 0.12.0实测；内嵌引擎当前仍固定0.11.0，不能把原生升级当作内嵌引擎升级。官方源码保持只读。

## 大目录按需发现

原生CLI仍有770个编辑命令，新版MCP没有增加命令ID，扩展了目录查询参数。先读取实际工具schema，再调用：

```json
{"name":"command_list","arguments":{"query":"graph.","brief":true}}
```

按菜单查路径工具：`command_list {"menu":"Object > Path","brief":true}`。`brief`省略每条的params；选定目标后用 `command_list {"filter":"graph.setType"}`取得完整参数。`filter`与`query`同传时非空filter优先；保留返回的enabled/disabled_reason，不把目录命中当作授权或当前可执行证明。`list_commands`提供相同的query/menu/brief用法，enabledOnly与command_list的enabled_only按各自schema填写。

插件适配层也提供这三个参数，兼容当前内嵌引擎；只过滤目录结果，不模拟新编辑算法。已有宿主会话继续使用原会话，不能另起headless进程冒充同画面修改。

## 向旧版Illustrator流程交付AI 7

仅当接收方明确要求旧版AI，使用单独派生文件；默认现代PDF兼容AI与原生工程分别保留。先保存原生母版，再运行：

```text
vectorcraft-cli convert master.vectorcraft delivery.ai --ai-version 7 --hidden-objects layer --transparent-images flatten
```

以上每个token是独立argv参数；不要用shell拼接用户路径。对应MCP可用 `export {"path":"delivery.ai","format":"ai","options":{"aiVersion":"7","hiddenObjects":"layer","transparentImages":"flatten"}}`，先核实当前后端支持这些选项；当前0.11内嵌引擎尚未证明支持，不自动调用。`run_command document.export`的参数目录不一定列尽所有格式选项，先查询document.formats并检查返回warnings。

多画板旧AI按画板分别输出，使用返回的真实文件列表，不假定只有delivery.ai。隐藏对象默认形成隐藏图层；omit会删除派生文件中的隐藏对象，visible会显示它们，按交付要求选择。透明图片flatten会结合其下方内容，不能声称仍保留原透明图片编辑性。文字可选outline以摆脱字体依赖，但需另保留活文字母版。

保存后由新原生进程重开：检查组、图层和活文字，再渲染查看；输入母版摘要保持不变。0.12技术样例实际验证两种几何组成的组、一个活文字对象保存到PostScript AI后仍可编辑；不代表复杂透明、渐变、置入图、专色或跨Illustrator版本保真。

## 既有命令的行为修复

0.12发布还包含Transform Again/Transform Each、Reflect轴向、画板复制与导出隔离、SVG文字控制字符等修复。不能因命令ID与0.11相同就认为行为已对齐。涉及这些任务时先核对实际运行时版本和对象、另存测试副本，按相应业务检查几何、画板边界与输出warnings；本补充没有把这些全部标为验收通过。
