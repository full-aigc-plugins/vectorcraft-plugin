# VectorCraft — release-compatibility

## Purpose

本能力定义 VectorCraft 在 release-compatibility 范围内对用户、宿主与下游系统承诺的可观察行为、失败语义和验收证据，确保规划、执行与实际交付之间保持可验证的边界。当前为目标规范；已有实现与限定范围证据不等于完整需求验收。

## ADDED Requirements

### Requirement: VC-RL-001 宿主与发布证据

发布 SHALL 分别验证插件结构、技能来源、运行时、宿主加载、真实任务和原生交付；文档阶段不得进入可安装市场或宣称功能完成。

#### Scenario: VC-RL-001-P 合同条件满足

- **WHEN** 请求满足本需求的来源、输入、状态和证据条件
- **THEN** 系统按本需求完成宿主与发布证据并返回可核对的结果
- **AND** 结果绑定当前版本与执行身份，不提升未验证能力状态

#### Scenario: VC-RL-001-N 边界条件

- **WHEN** 只有 OpenSpec 校验与文档检查通过
- **THEN** 仅新增文档对应能力不得提升为已实现，既有有界实现与验证记录保持原范围；未完成实现任务仍未完成

### Requirement: VC-RL-002 权限与秘密边界

运行 SHALL 限定素材读取与工程写入根目录；模型输出和素材元数据均为不可信输入；密钥通过宿主秘密引用传入，不进入日志、计划、包或技能。

#### Scenario: VC-RL-002-P 合同条件满足

- **WHEN** 请求满足本需求的来源、输入、状态和证据条件
- **THEN** 系统按本需求完成权限与秘密边界并返回可核对的结果
- **AND** 结果绑定当前版本与执行身份，不提升未验证能力状态

#### Scenario: VC-RL-002-N 边界条件

- **WHEN** 素材元数据包含额外命令或路径越界请求
- **THEN** 作为数据处理并拒绝越权执行，日志不泄露秘密

### Requirement: VC-RL-003 发布身份与运行时事实源一致

源码清单、插件锁、运行时说明和当前状态文档 SHALL 从可核对的版本事实源生成或校验。插件执行 SHALL 以固定技能源实际携带的运行时锁为依据；根目录研究基线必须明确标为历史／非执行用途，不能与执行锁竞争。固定目录描述能力基线，实时会话决定当前 enabled／选择状态；两者 SHALL 绑定实际二进制身份，不以最新上游版本替换已验证组合。

#### Scenario: VC-RL-003-P 当前身份可从锁追溯

- **WHEN** 维护者查询当前插件、13 项技能及原生 CLI／桌面的组合
- **THEN** 系统 SHALL 给出一致的插件版本、技能源标签及提交、技能摘要与各运行时身份，双语当前状态一致，历史基线单独标识
- **AND** 目录计数、实时能力和执行验收分别呈现；已有有界实现不再被笼统描述为“只有文档”，目标 Harness 仍保持未实现状态

#### Scenario: VC-RL-003-N 元数据漂移阻止错误发行

- **WHEN** 技能源套件版本与发布清单不同、插件快照不符合锁，或根目录历史运行时被展示为当前执行版本
- **THEN** 校验 SHALL 报告具体文件和差异并阻止对应发布门禁通过；不能删除历史证据、修改已发布标签或静默升级运行时来消除差异

### Requirement: VC-RL-004 源仓与插件持续验证及固定安装门禁

独立技能源和插件 SHALL 各自具备持续验证入口。源仓覆盖严格解析、字段保全、自包含同步和技能路径，插件覆盖规范追踪、固定来源、身份与证据索引。发行 SHALL 将候选测试、不可变标签／制品、实际安装副本、原生创作与宿主／平台矩阵分开验收；不得以跳过、不适用、模拟下载或离线静态检查计作真实安装通过。

#### Scenario: VC-RL-004-P 分层 CI 与固定副本验收

- **WHEN** 候选修复通过并在另行获得发布授权后形成固定技能源与插件制品
- **THEN** 流水线 SHALL 校验公开来源摘要及全部独立技能资源，并在声明支持的平台从实际安装副本验证空运行时首次使用、原生重开、局部返工与旧交付保全
- **AND** 记录宿主、平台、依赖版本、PASS／FAIL／SKIP／NOT_RUN 及原因；通用 Skills CLI 安装与模拟复制布局单列，Art 内置固定领域包升级另验

#### Scenario: VC-RL-004-N 未覆盖平台不扩张支持声明

- **WHEN** macOS arm64 用例通过而其他平台、模型派发、完整 GUI 或全量命令未执行，或任一必要故障用例失败
- **THEN** 对应门禁 SHALL 保持开放或失败，支持矩阵不扩张，完整 V1 不关闭
- **AND** 文档和 OpenSpec 校验通过不触发发布、不证明运行时修复已完成

## Implementation evidence (non-normative)

`docs/evidence/codex-current-release.json` binds current fixed releases to two actual Codex CLI/app-server versions, five enabled namespaced skills, installed public workflow outcomes and explicit exclusions. The corresponding bilingual Host-Verification-Architecture documents specify the repeatable check. RL-001 tasks remain unchecked until their full P0 prerequisites and scenarios pass.
