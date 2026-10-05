# 原生品牌 token 与变体更新

VectorCraft 的全局色板是原生品牌色 token。创建 `swatch.new` 时设 `global: true`，通过 `paint.setFill` 的 `swatch` 和明确的 `ids` 将 Logo、字标、画板变体绑定到该色板。`swatch.edit` 修改全局颜色后，原生引擎更新所有关联填充／文字；无关联图标不参与更新。

所有命令属于现有原生 CLI。技能的 `workflow.py` 支持 `swatch.new/edit/list`，不创建同名的新 CLI。以实际加载 SKILL.md 目录定位脚本，单独安装本技能即可首次安装与使用。

```bash
python3 -I -B "$SKILL_DIR/scripts/workflow.py" \
  "$SKILL_DIR/examples/brand-token-assets.json" --output "$FIRST_DELIVERY"
```

示例保留三个画板：Logo／字标、独立橙色图标、与品牌色关联的另一变体。交付包含 `.vectorcraft`、原生模型、操作回执、素材与导出摘要和交换报告。

修改色板时使用新输出目录及此前保存的原工程摘要；`primary.name` 来自原生创建回执，避免猜测发生重名后的真实色板名称。示例修订计划如下，替换摘要后保存为 JSON，可以显式指定导出配置；省略 exports 时，swatch.edit 修订会核对原 plan.json 摘要并沿用其变体导出清单，不能信任被修改的清单。示例如下：

```json
{
  "expectedProjectSha256": "此前保存的原 project.vectorcraft 摘要",
  "operations": [{
    "command": "swatch.edit",
    "params": {"name": {"$ref": "primary.name"}, "color": "#175cce"}
  }],
  "exports": [
    {"format": "svg", "artboard": 0}, {"format": "png", "artboard": 0},
    {"format": "png", "artboard": 1},
    {"format": "svg", "artboard": 2}, {"format": "png", "artboard": 2}
  ]
}
```

```bash
python3 -I -B "$SKILL_DIR/scripts/workflow.py" "$REVISION_PLAN" \
  --source "$FIRST_DELIVERY" --output "$NEXT_DELIVERY"
```

原生项目重新打开后仍保留关联关系；默认填充、非全局色板、直接写入 RGB 的对象不应被当作关联对象。缺少色板、错误摘要或既有输出目录应停止，不自动重放未知结果。当前验证覆盖 RGB 全局色板、路径及文字关联、两关联画板的 SVG／PNG 更新、独立图标和旧工程不变。其他颜色模型、tint／gradient／spot、跨编辑器色板保真、跨文件消费者与完整创作接受仍须单独验证。
