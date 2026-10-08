# SVG 文字交付与显式定位

开发插件52锁定独立技能源39。普通工作流、native.command 与完整命令入口共用文字修改校验，要求显式 id 或 ids 以及字符串 text；拒绝隐式选区、空目标、布尔ID和附带字体替换。

```mermaid
flowchart LR
    A[三个公开文字入口] --> B[共享定位合同]
    B -->|有效目标| C[原生文字修改与保存]
    B -->|无效参数| D[安装和输出前拒绝]
    C --> E[读取实际导出会话模式]
    E --> F[SVG与交换损失报告]
    F --> G[轮廓模式记录编辑性损失]
    C --> H[保留原生文字与字体依赖]
```

SVG 的 appearance 模式记录 live-text-editability=lost；editable 模式存在文字节点时记录 observed。未知模式或只有路径不足以证明轮廓化。字体可移植性继续为 unknown，文档文字ID不能证明对象在画板内可见，也不构成逐轮廓映射。

源39候选验证包括151项通过／30项跳过、真实中文修订、品牌消费者隔离、同色非消费者保留，以及两种原生SVG模式与18项入口拒绝。候选报告见[独立技能源证据](https://github.com/full-aigc-skills/vectorcraft-skills/blob/v0.1.0-dev.39/docs/evidence/text-outline-candidate39-20261009.json)。固定52安装及原生验收另行登记；4.7–4.9和完整V1仍开放。历史51证据保留原始执行字节，不重绑定到52。
