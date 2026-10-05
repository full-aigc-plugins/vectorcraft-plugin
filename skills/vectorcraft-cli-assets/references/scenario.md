# 链接与可复用资产操作指南

## 目标与前置

放置素材、管理链接、符号与已有图像描摹。图像描摹后检查实际路径结构；链接收集并核对摘要，明确嵌入与引用差异。

先检查需求中的工程格式、目标对象、素材摘要、字体与输出约束。输入不完整时继续只读调查，但不猜测依赖它的参数。

## 当前版本命令入口

`commands` 返回 JSON 参数目录；`run --in <工程> --cmd <id> --params <JSON> ... --export <新工程.vectorcraft>`，同批次解析对象 ID；convert 按扩展名输出。

| 命令 ID | 目录标签 |
| :--- | :--- |
| `imageTrace.make` | Make |
| `imageTrace.makeAndExpand` | Make and Expand |
| `imageTrace.release` | Release |
| `imageTrace.expand` | Expand |
| `imageTrace.presets` | Image Trace Presets |
| `symbol.list` | Symbols |
| `symbol.new` | New Symbol… |
| `symbol.place` | Place Symbol Instance |

完整候选参数见本技能 commands.json；enabled 是空会话观察，打开目标工程后必须重查。命令参数 schema 存在不证明它在全部素材与平台有效。

## 执行与验收

1. 保存原生检查点、读取对象 ID 和参数值；已有素材先核验引用。
2. 构造当前版本命令参数；一次只改变请求的属性或对象。连续创建 ID 使用实际回执或同一会话。
3. 保存新原生工程、重新打开，比较目标参数和未修改对象。需要输出时检查帧、像素、音频或矢量结构。
4. 原生工程、素材清单、预览/导出及交换报告交付；技术核验和视觉审核分开记录。

首次组合实例采用本技能 examples 与 references/workflow.md。此实例验证组合能力，不替代所有候选命令的逐项验收。失败保留检查点，不将无损原生交付替换成扁平结果。

## 已验证的导入、嵌入与符号前置（CLI 0.2.0）

用 `file.place` 的真实路径与 `link:true` 导入已有图像；返回 `ids`、`linked` 和尺寸。把这些 IDs 传给 `links.embed`，要求 `embedded` 包含全部目标且 `missing` 为空，再保存。重开工程并在原图不再可访问时渲染，才能证明像素已嵌入；链接工程在素材变更或丢失时应重新关联，不能冒充独立资产。

重新打开工程后，`symbol.new` 即使传入 `ids`，也可能因没有活动选择被拒绝。先执行 `select.set`，再在同一批次建立符号并放置实例：

```bash
: "${SKILL_DIR:?本技能实际加载目录}" "${SOURCE_PROJECT:?原生工程绝对路径}" "${OUTPUT_PROJECT:?新工程绝对路径}" "${OBJECT_IDS_JSON:?从真实回执取得的整数 ID 数组}"
python3 -I -B "$SKILL_DIR/scripts/cli.py" -- run --in "$SOURCE_PROJECT" \
  --cmd select.set --params "{\"ids\":$OBJECT_IDS_JSON}" \
  --cmd symbol.new --params '{"name":"Brand mark"}' \
  --cmd symbol.place --params '{"name":"Brand mark","x":64,"y":32}' \
  --export "$OUTPUT_PROJECT"
```

示例坐标应按真实画板替换。`symbol.new` 返回名称和实例 ID，`symbol.place` 返回新实例 ID；重开后应保留符号定义与两个实例，并确认其他图标和对象未修改。
