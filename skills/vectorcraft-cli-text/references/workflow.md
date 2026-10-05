# 可执行原生计划

`scripts/workflow.py` 是技能自带的原生矢量操作助手，运行在单个 headless MCP 会话中；插件级任务账本与跨插件调度仍在实现。需要 Python 3.11+。首次调用自动复用或安装锁定 CLI，安装范围见技能入口。

```bash
python3 /mnt/skills/user/vectorcraft-cli-text/scripts/workflow.py \
  /mnt/skills/user/vectorcraft-cli-text/examples/brand-assets.json \
  --output /absolute/project/brand-v1
```

按实际挂载位置替换技能根。输出目录必须是新的修订目录，已有目录不会被覆盖。

计划字段：

| 字段 | 用法 |
| --- | --- |
| document | 首次创建设置 name、width、height、units（Pixels/Points）；尺寸大于 0 且不超过 16384 |
| operations | 按顺序执行 `{command, params, as?}`；只允许脚本 ALLOWED 集中的原生编辑命令 |
| as | 把实际命令结果绑定为稳定业务名称，例如 logo；不猜上游对象 ID |
| `$ref` | `{"$ref":"logo.ids.0"}` 解析布尔结果的第一个 ID；普通文字不做替换 |
| exports | `{format: "svg"/"png"/"pdf", artboard: 0}`；画板索引从 0 开始 |
| expectedProjectSha256 | 修改既有交付时必须匹配源工程和 manifest 中的摘要 |

支持的命令范围见脚本 `ALLOWED`：基础形状、路径、文字创建、填充与描边、选择、组合、变换、四种布尔操作、添加与调整画板。其他命令通过原生 CLI/MCP 单独执行并验证，不能假定此助手已支持。

## 局部改色

读取 `brand-v1/manifest.json` 的 `files.project.vectorcraft` 和 `bindings`，创建以下修订计划，将示意摘要替换为实际值：

```json
{
  "expectedProjectSha256": "源工程的实际 SHA-256",
  "operations": [{
    "command": "paint.setFill",
    "params": {
      "ids": [{"$ref": "logo.ids.0"}, {"$ref": "wordmark.id"}],
      "color": "#175cce"
    }
  }],
  "exports": [{"format": "png", "artboard": 0}]
}
```

执行时加 `--source /absolute/project/brand-v1 --output /absolute/project/brand-v2`。源目录保留不动；先核对摘要，再进入暂存工程编辑。命令失败不会发布目标目录。副作用超时不自动重试。

交付包含原生工程、各画板导出、重开后的对象模型、操作结果、计划和内容摘要。导出警告保留在 manifest；单画板 PDF 的 preserve-editing 警告不能忽略。`acceptance` 默认为需要领域与视觉复核，文件存在不是完整验收。

示例的两画板为 Logo/文字和未绑定的独立图标。修改 Logo 颜色时，第二画板应保持相同像素与文件摘要；原生对象的其他属性也应保持。此示例用于功能回归，不代表通用品牌设计质量验收。
