---
name: ppt-master
description: >
  AI-driven presentation workflow for generating editable PPTX decks and slides,
  reconstructing page visuals, creating reusable Brand/Style/Layout/Deck
  workspaces, filling native PPTX templates, and enhancing finished PPTX files.
  Use when the user asks to create, generate, reconstruct, regenerate, beautify,
  redesign, template, fill, or enhance a presentation, PPT, PPTX, slide deck, or
  courseware — including adding narration or animation to one — requests a
  presentation-authored narrated/self-running video, or mentions ppt-master.
metadata:
  version: "6.7.0"
  local_profile: "academic-chat-reference-v2"
  copyright: "Copyright (c) 2025-2026 Hugo He"
  license: "MIT"
  official_repository: "https://github.com/hugohe3/ppt-master"
---

# Academic PPT Master

基于 Hugo He 的 PPT Master 6.7.0 的学术定制版，保留上游许可证、资源库与原生转换后端。用于从论文/材料生成学术汇报，重设计已有 PPTX，以及按确认页面制作可编辑 PPTX。已有 PPTX 的证据审阅与稀疏修改也可使用独立的 academic-pptx-review。

## 输入与执行条件

- 先核对输入的实际路径、版本和已有项目；明确论文/PPTX、模板/背景、听众与时长。复用已确认的信息与页级反馈。
- 需要文件读写、命令执行和图片查看能力。AI 生图是独立能力：能识图或写 SVG 不代表有生图工具。先确认实际工具，按真实能力执行。
- 原文件保持完整，工作文件、草稿和交付物另存。未知数值、公式、引用或结论保持未知；论文证据图保留来源。

## 加载顺序与工作流选择

1. 将本文件所在绝对目录保留为 `SKILL_DIR`，所有包内路径相对它解析；仓库发现入口应先解析到本文件。
2. 运行 `python3 "${SKILL_DIR}/scripts/attribution_guard.py"`；Windows 使用实际可用的 `python` 执行同一命令。返回 0 才继续。执行工具不可用与校验失败分别报告，不反复盲试或跳过检查。
3. 阅读 [学术设计与交付规则](references/academic-chat-design.md) 和 [共享术语与执行约定](references/entry-contract.md)。
4. 阅读 [路由规则](references/workflows/routing.md)，只加载选中路线及按条件需要的支持文件：

| 任务 | 执行文件 |
| --- | --- |
| 从论文/材料生成；普通 Default | [generate-pptx.md](references/workflows/generate-pptx.md) |
| 明确要求 Quick | [quick-generate.md](references/workflows/profiles/quick-generate.md) |
| 美化与重设计已有 PPTX | [beautify-pptx.md](references/workflows/profiles/beautify-pptx.md) |
| 复刻用户给定的页面图片 | [image-to-pptx.md](references/workflows/profiles/image-to-pptx.md)，按其宿主支持边界执行 |
| 原生编辑、套用已有 PPTX | [edit-native-pptx.md](references/workflows/edit-native-pptx.md) |
| 创建可复用模板 | [create-template.md](references/workflows/create-template.md) |

按学术设计规则执行，确认与反馈在聊天内完成。默认使用宿主内置生图；外部 API 由用户选择并配置后显式调用。

需要表达案例或原生组件实现时，按 [正面教材用途索引](references/positive-examples.md) 定向查看相关页；教材按需加载，可不采用，不设置默认配色或版式。

## 六阶段主线

以下用于生成与美化；原生稀疏修改只设计和确认修改页，模板提取等专门任务按选中路线执行。

| 阶段 | 必须得到的结果 |
| --- | --- |
| 1. 理解材料 | 读取正文、实际图像、数据、公式与来源；核对 PPTX 对象和渲染，记录可读内容及盲区。 |
| 2. 规划汇报 | 先按 [参考图前缺陷识别](references/pre-reference-diagnosis.md) 展示整套与逐页发现并取得用户确认，再据此完善内容与结构。随逐页内容与排版大纲汇总 [通用视觉约定与配色用途](references/academic-chat-design.md#1c-通用视觉约定与配色用途)，复用已有确认。明确论述链与每页核心任务；实际查看适合的模板/样页/图表/图标，将文件、拟用页、借鉴点与理由写进方案和逐页简报。详见学术规则 §1A。 |
| 3. 设计参考页 | 缺陷确认完成后，按 [完整参考图流程](references/page-reference-generation.md) 写视觉简报与完整提示词，默认用宿主内置绘图工具生成完整页面并传入实际参考图片。最终全原生或 image_usage:none 均不跳过此阶段。 |
| 4. 聊天确认 | 查看并核对参考图，展示实际图片，记录真实的按页批准/修改/委托与版本。没有回复或工具成功不算批准。 |
| 5. 可编辑制作 | 按 [参考图精准复刻规范](references/reference-reconstruction.md) 还原视觉、复用源 PPT 与内置组件、使背景之外主要组件可原生编辑并分别验收；页面不协调时仅作有记录的最小调整。复用现有 SVG→DrawingML/round-trip 后端；Default/Quick 使用 scripts/reviewed_export.py，稀疏原生修改保留未改页身份。 |
| 6. 实际渲染与修正 | 重新读取并渲染真正生成的 PPTX，逐页比较内容、整体观感、字体、遮挡和对象类型；修复后复查，再交付。 |

Default 在 `design_spec.md` 记录规划；Quick 在聊天与页级简报保留紧凑规划，不额外创建根级 Design Spec/lock。来源、参考图、提示词和批准使用 `reference_review/` 的版本记录。

## 判断与交付边界

- 12 条学术设计原则完整保留在学术规则 §4：先看内容组织、整体观感和理解效果；参数用于定位修复。足够好的页面可以保留并说明“无需修改”。
- 没有内置绘图工具时，可使用用户选定并配置的外部 API，或由用户提供参考图、跨工具生图、明确选择原生设计预览。记录实际工具和来源，API 路径使用 `external_image_api`，不标成宿主内置生图。
- 制作环节沿用现有路线和导出后端；辅助脚本服务于已确认设计，不能交付一个另写的文字型“一键生成脚本”代替最终 PPTX、预览和验收。
- 标题/正文为原生文本；可靠数据图表与表格使用相应原生对象；公式优先 Office Math。照片和复杂论文原图是独立图片，不宣称内部语义组件可编辑。详细边界见学术规则 §5。
- 交付可编辑 PPTX、实际逐页渲染/对照、来源与修改记录、验证结果和剩余限制。文件存在、退出码为零、SVG 预览或结构检查不能单独证明视觉与内容验收通过。
- 全部执行规则、12 条原则及批准命令以学术规则为准；共享原生能力、术语和条件功能见 entry-contract，避免在本入口重复展开。
