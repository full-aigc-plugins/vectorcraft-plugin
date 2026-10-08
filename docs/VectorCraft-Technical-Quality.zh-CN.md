# VectorCraft 技术质量候选检查

只读候选检查器核对当前运行时／工程／全部文件摘要，使用Pillow解码PNG，使用PyMuPDF解码PDF／SVG。解码器缺失保持NOT_RUN；导出损坏或身份漂移时，即使创作判断为PASS也阻止接受。文件完整性不代替原生重开：工程状态保持NOT_RUN，接受状态为pending。

已验证5项单元用例及固定38／源35生成的18份真实导出，包含两项“清单摘要已更新但PNG损坏”案例。6.1完成，ReviewStore／CLI集成6.2及完整工程／创作验收6.3仍开放。[绑定证据](evidence/vectorcraft-technical-quality-candidate-20261008.json)。
