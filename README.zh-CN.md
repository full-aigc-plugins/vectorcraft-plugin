# VectorCraft Agent Plugin

独立技能驱动的可编辑矢量品牌资产与多画板设计.

[English](README.md) | [简体中文](README.zh-CN.md)

## 当前版本与可复现宿主验证

此前完成宿主验证的插件/技能源版本：`0.1.0-dev.3`。Codex 0.147.0 与 0.153.4 均安装五个固定公开发布，发现全部 58 项启用的命名空间技能，加载错误为零，来源摘要一致。五项代表流程已通过 0.147.0 安装后的场景技能入口验证，包括原生工程、局部修订和 ArtCraft 在线混合流程。模型自动派发、桌面 GUI、创作最终评审和完整交换保真尚未验证。

[宿主验证设计](docs/VectorCraft-Host-Verification-Architecture.zh_CN.md) · [绑定版本的证据](docs/evidence/codex-skill-suite.json)。历史里程碑保留原证据范围；当前版本身份以 manifest 和锁文件为准。

> 开发版已通过固定标签的 Codex 安装、技能发现和原生代表工作流；完整产品与创作验收仍未完成。

独立技能包已进入实施，单技能隔离安装已在 macOS arm64 实测；完整创作流程与插件宿主验收仍未完成。[证据](docs/evidence/bootstrap-tests.json)

独立技能现已包含原生工作流助手：已实测形状与路径、布尔合并、可编辑文字、双画板、SVG/PNG/PDF 导出和定向改色。验收样例中未绑定对象及其导出保持不变，完整插件验收仍待完成。[工作流证据](docs/evidence/vector-workflow-tests.json)

## 定位

制作 Logo 与图标资产，交付 .vectorcraft、SVG 和 PNG；修改品牌色后更新所有绑定的变体，并保留无关颜色。

面向需要原生可编辑工程、反复修改和可靠自动化的创作者。

## 一眼了解

```text
Intent + assets
  -> independent Skills (pinned development release)
  -> public skill workflow / ArtCraft adapter
  -> verified runtime / child adapter
  -> native project + preview + export + evidence
```
| Property | Value |
| :--- | :--- |
| Plugin ID | vectorcraft |
| Metadata version | 0.1.0-dev.6 |
| Stage | implementation-in-progress |
| Skills source | vectorcraft-skills / v0.1.0-dev.5 |
| Execution | 上游 CLI；ArtCraft 使用子适配器 |
| Host compatibility | Codex development install/discovery pass; GUI and other hosts pending |
| License | Apache-2.0 (original repository content) |


## 能力与边界

| 能力 | 行为边界 | 状态 |
| :--- | :--- | :--- |
| 路径形状与坐标 | 定义画板坐标、单位、路径控制点、闭合性与描边；不可把预览像素当成路径事实。 | 待完整验收 |
| 组合与布尔操作 | 记录参与对象 ID、布尔运算与结果对象身份，保留修改前检查点；操作失败不丢失原对象。 | 待完整验收 |
| 品牌色与文字 | 以显式 token 绑定品牌色而非全文件颜色替换；保留文本内容与字体依赖，轮廓化输出记录可编辑性损失。 | 待完整验收 |
| 画板与变体 | 每个画板有稳定 ID、名称、尺寸和输出映射；预览顺序与导出范围明确，避免索引基准混淆。 | 待完整验收 |
| 交换格式能力范围 | 原生 .vectorcraft 与 SVG、PDF、PNG 分别验证；遇到不可交换效果时报告栅格化范围并保留原工程。 | 待完整验收 |
| 品牌变体更新 | 根据 token 与素材依赖更新相关变体，核对无关对象属性与输出没有变化。 | 待完整验收 |

不重写上游编辑引擎，不暗中改变原生交付格式，不宣称 GUI 或跨平台验收完成。

## 架构与文档

- [完整运行时架构](docs/VectorCraft-Runtime-Architecture.zh_CN.md)
- [技术方案与路线](product-docs/VectorCraft/5%E3%80%81VectorCraft-%E6%8A%80%E6%9C%AF%E6%96%B9%E6%A1%88%E4%B8%8E%E8%B7%AF%E7%BA%BF.md)
- [V1 PRD 与需求映射](product-docs/VectorCraft/V1/5%E3%80%81VectorCraft-PRD%E6%96%87%E6%A1%A3-V1.md)
- [完整文档导航](docs/README.zh-CN.md)
- [OpenSpec proposal](openspec/changes/establish-v1-plugin/proposal.md)
- [OpenSpec tasks](openspec/changes/establish-v1-plugin/tasks.md)

- [专业领域技术设计](docs/VectorCraft-Domain-Design.zh_CN.md)

## 当前可执行的快速开始

```bash
python3 scripts/validate_docs.py
openspec validate establish-v1-plugin --strict --no-interactive
```
以上校验文档和规范，不运行产品工作流。OpenSpec 校验使用 1.13.1；本仓不自动安装工具。

已安装官方 CLI 后可执行基础检查：

```bash
vectorcraft-cli --version
```

本次记录结果为 0.2.0。独立技能的 bootstrap 与 workflow 是当前开发版入口；插件安装与技能发现已有证据；完整宿主验收仍待完成。

## 配置与运行时

目标配置包含 CLI 路径、允许读写根目录、运行模式、预算、超时与输出目录；配置 schema 尚待实现。技能锁文件固定已发布的独立技能源提交与内容摘要。运行时锁文件中的摘要来自真实官方制品，只证明已记录平台的基础运行。

## 可靠性与安全

规划要求：单工程写入锁、版本前置条件、持久化意图、幂等键、不明确结果核对、原生工程检查点、产物摘要及受限修订。密钥只通过宿主秘密引用传递；素材元数据不作为执行指令。

## 验证与成熟度

[脱敏 CLI 证据](docs/evidence/runtime-baseline.json)

| 层面 | 状态 |
| :--- | :--- |
| 上游 CLI 与只读 MCP | 已观察，仅 macOS arm64 |
| 独立技能与适配器 | 技术工作流已验证；完整 Harness 待完成 |
| 原生工程与创作验收 | 原生技术用例通过；创作质量待验收 |
| 目标宿主安装 | Codex 受控安装与发现通过；完整宿主验收待完成 |


## 路线与贡献

| 阶段 | 交付 | 进入下一阶段条件 |
| :--- | :--- | :--- |
| D0 | 双语文档与 OpenSpec 基线 | 文档、链接、规范校验通过；实现任务仍未完成 |
| M1 | 独立技能与运行时适配 | 清洁环境安装、摘要检查、真实 MCP 调用 |
| M2 | 专业领域完整闭环 | 代表任务、工程重开、输出解码、局部修改 |
| M3 | ArtCraft 跨插件协作 | 版本传播、局部失效、断线恢复与幂等 |
| M4 | 宿主与发布验收 | 宿主实装与多平台证据；市场清单一致 |

先更新 OpenSpec 再实现行为；每项任务通过实际验收后才能勾选。中英文文档同时维护。参考 CONTRIBUTING.md 与 AGENTS.md。

## 许可与上游

原创内容遵循 [Apache-2.0](LICENSE)。这是第三方集成规划，不代表上游背书。四款应用的代码许可与 ArtCraft/Services 的受限许可分别处理；不复制上游 ArtCraft/Services 代码或品牌资产。

[Upstream VectorCraft](https://github.com/storytold/vectorcraft) · [Issues](https://github.com/full-aigc-plugins/vectorcraft-plugin/issues)

独立技能现已绑定当前已发布开发标签 `v0.1.0-dev.4`，`skills.lock.json` 固定来源提交与整个技能摘要。使用 `python3 scripts/vendor/skill_vendor.py check` 核对。技能源快照发布不代表宿主验收或生产完成。

## 开发版独立技能安装与使用

安装独立技能：`npx skills add full-aigc-skills/vectorcraft-skills --skill vectorcraft-use`。安装技能后，从其真实目录运行公开入口；插件快照也包含相同技能。

```bash
python3 -I -B skills/vectorcraft-use/scripts/bootstrap.py
python3 -I -B skills/vectorcraft-use/scripts/workflow.py --help
```

首次入口会安装锁定官方 CLI 到用户数据目录；要求 macOS arm64 与 Python 3.11+。使用技能内示例计划并提供真实素材；交付与修订合同见技能的 SKILL.md。[来源与校验证据](docs/evidence/skill-publication.json)。

## Codex 开发版宿主验证

五个插件已在隔离 Codex 配置中从公开标签安装，app-server 发现带命名空间的技能且无加载错误；安装缓存中的 ArtCraft 入口已交付四种原生工程。[宿主证据](docs/evidence/codex-installation.json)。此为受控开发验收，不代表桌面 GUI、其他宿主、完整创作或正式市场发布通过。

开发版本 `0.1.0-dev.1` 同步独立技能的安装锁等待修复；并行安装和复用按有界互斥协调，原生任务不自动重放。

当前开发里程碑为原生交付增加摘要绑定的交换损失报告，区分 lost、observed、unknown；派生导出不替代原生工程。跨编辑器字体、效果和蒙版保真尚未验证，完整交换验收任务保持未完成。

## CLI 与场景技能体系

技能源包含 12 项可独立安装的技能，分为安装、CLI 公共操作与场景任务。[架构与清单](docs/VectorCraft-Skill-Suite-Architecture.zh_CN.md)。运行时与插件版本分别维护；旧宿主证据保持原版本范围。

当前插件版本：`0.1.0-dev.5`；技能源版本：`0.1.0-dev.4`。命令示例以宿主实际加载的 `SKILL.md` 所在目录调用脚本。全部技能在用户、项目与插件三种含空格布局中通过隔离入口检查。[路径证据](docs/evidence/installed-skill-paths.json)。此前宿主验证仍对应其记录版本，既有安装需更新。

插件 `0.1.0-dev.5` 从固定公开标签重新取快照并修正整个技能摘要，未带入本地 Python 缓存。插件标签 `v0.1.0-dev.4` 的摘要误包含被忽略的开发缓存，已被替代，不可安装该标签。

当前插件 `0.1.0-dev.6` 固定技能源 `0.1.0-dev.5`。九类场景技能各自冷安装并完成真实原生操作，验证显式选择、图像嵌入、符号复用与无关画板保护；完整回归 38 项、零跳过。[证据](docs/evidence/task-skill-first-use.json)。完整创作、GUI 与模型派发验收仍未完成。

当前固定发布的宿主核验（2026-10-06）：Codex 0.153.4 安装五个当前固定插件，加载全部 58 技能并逐项核对内容身份。本插件代表性原生工作流从实际安装路径调用，在新的原生运行时中完成创建、重开和修订检查；五工作流调用后，全部 58 个技能摘要保持不变。[证据](docs/evidence/codex-current-release-20261006.json)。显式标签生成器由 ArtCraft 统一持有。模型派发等待授权，GUI、创作与完整宿主验收仍未完成；本次 QA 维护不改变已发布技能/运行时内容或标签。

当前固定发布矩阵（FilmCraft dev.6、EffectCraft dev.7、PhotoCraft dev.6、VectorCraft dev.6、ArtCraft dev.17）在隔离 Codex 安装后通过 58 技能发现及原生代表工作流；执行后所有技能摘要保持不变。[宿主安装内容的原生验证](docs/evidence/codex-release17-native-20261006.json)。此证据不代表模型调度、GUI 或完整创作验收。

补充安装后品牌导出验证通过：选定 Logo／字标改色后，SVG 色值与 PNG 解码像素同时更新；无关图标属性及第二画板 PNG 保持不变。本次使用已核验运行时缓存，不是新的冷安装，也不证明自动推导 token 依赖。[证据](docs/evidence/brand-export-color.json)。插件及技能源发布标签保持不变。

原生 RGB 全局品牌色板工作流已通过单独复制 appearance 技能的首次在线冷启动验证，脚本与示例均来自同一技能；关联 SVG／PNG 更新、独立图标与旧工程保留有真实原生证据。独立技能源 v0.1.0-dev.6 已发布，插件 v0.1.0-dev.7 已发布；实际宿主安装后的单技能在线冷启动原生验证通过（6.487 秒），全部 58 个安装技能摘要保持一致。实际 npx 独立安装和模型派发仍待验证。详见 [品牌色架构](docs/VectorCraft-Brand-Tokens-Architecture.zh_CN.md) 与 [验证记录](docs/evidence/native-brand-token-first-use.json)。

原生中文文字修订通过单技能冷启动：明确对象修改保留首样式、独立页脚与旧工程；缺失字体停止交付，可用字体依赖写入清单。技能源 dev.7 与插件 dev.8 已发布；实际安装后的单技能在线冷启动原生验证通过（8.275 秒），全部 58 个安装摘要不变。[架构](docs/VectorCraft-Chinese-Text-Architecture.zh_CN.md)、[证据](docs/evidence/native-chinese-text.json)。
