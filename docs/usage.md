# 使用说明

## 安装

完整 Skill 在 `skills/ppt-master/`，仓库内的 Codex 和 Claude 入口都读取这一份内容。安装到其他项目时，复制的是整个运行包。

需要 Git 和 Python 3.10+。从 GitHub 克隆仓库后安装依赖：

```powershell
git clone https://github.com/MLNLP-World/Paper-Presentation-Tips.git
cd Paper-Presentation-Tips
python -m pip install -r skills/ppt-master/requirements.txt
```

在克隆目录中启动 Codex 或 Claude Code，可以使用仓库已有入口。安装到其他项目时，在仓库根目录运行，将 PROJECT 换成目标项目绝对路径：

```powershell
python tools/install_skill.py --skill ppt-master --agent codex --project "PROJECT"
# Claude Code 使用 --agent claude；其他宿主可指定 --destination "SKILLS_DIR/ppt-master"
```

目标已有安装时，明确更新加 `--overwrite`，旧目录会保留备份。重开对话后核对实际加载的 SKILL.md 路径，避免仍使用旧的个人副本。

## 准备材料

提供论文或 PPTX 的准确路径、听众、时长，以及希望沿用的模板、背景或样页。已有项目还应提供项目目录和确认过的版本。

不确定的科学结论、图表数据和公式不能由生图模型补造。论文原图、数值、单位、条件和来源需要保留。

## 从规划到成品

1. 读取正文、图表、公式和已有 PPTX 对象，核对实际页面。
2. 按 12 条汇报建议检查整套与逐页表达，在聊天中说明有证据的缺陷、理解影响和调整方向，供确认。足够好的页面明确保留，疑点与可选建议单列。
3. 根据确认范围确定论述顺序和每页核心任务，实际查看合适的模板、样页与资源，说明配色及其语义用途。
4. 将内容规划写成逐页视觉简报和完整提示词，生成整页参考图。
5. 在聊天中展示实际图片，记录页号、版本和你的反馈。
6. 按确认页复用或制作原生对象，输出可编辑 PPTX。
7. 渲染实际 PPTX，检查内容、字体、构图与遮挡，调整后再看。

主要文件包括 `design_spec.md`、`reference_review/` 中的简报、提示词、参考图和确认记录，以及最终 PPTX、实际页面预览和来源记录。Quick 会压缩规划说明，仍保留参考图确认。

### 缺陷确认与参考图确认

已有 PPTX 的缺陷判断结合实际渲染和对象读取；从论文新建汇报时，检查的是材料与大纲的表达风险，不能虚构原页面的排版缺陷。Tip 6、7、11 分别检查相关页段的案例→问题、例子→公式和整套收束；Tip 10 按数据重点选图，保留适合查值或比较的清楚表格。

可回复“D01、D03 同意，D02 保留原页”，仅落实已确认的调整。缺陷与确认记录保存在 `reference_review/diagnosis.md`；缺陷确认不等于之后的参考图批准。完整判断规则见 [参考图前缺陷识别](../skills/ppt-master/references/pre-reference-diagnosis.md)。

### 参考资源与配色

包内 [正面教材用途索引](../skills/ppt-master/references/positive-examples.md) 提供 11 页完整 PPTX、实际页面预览与原生组件定位。按本次表达问题选看相关页，学习图文关系或组件实现；无需沿用它的颜色、布局，也可以不采用。

配色随大纲说明“语义或组件 → 颜色用途”：同类结构保持一致，表格按整体层级配色，独立类别允许分色，图例与论文原图的语义色保留。模板和教材的采用方式写进规划及受影响页的简报。详见 [学术规则 §1A–§1C](../skills/ppt-master/references/academic-chat-design.md)。

## 生图方式

### 使用 Agent 内置工具

默认走这一条。将真实背景和样页传给工具，用完整页面提示词生成参考图。能识图、写 SVG 或导出 PNG，不代表宿主具备 AI 生图能力。

### 使用自己配置的外部 API

没有内置绘图工具时，可以选择外部服务。`skills/ppt-master/.env.example` 提供配置字段；真实配置放在自己的本地 `.env` 或环境变量中。不要将真实凭据提交到仓库。

选定 provider 和图像模型后，先确认它是否支持参考图片、图片编辑与所需比例。可以查看现有适配器：

```powershell
python skills/ppt-master/scripts/image_gen.py --list-backends
```

只有明确选择 API 路径时才加 `--allow-api`。下面以现有 OpenAI-compatible 适配器为例，SERVICE、MODEL 和 PROJECT 应使用自己的配置：

```powershell
$env:IMAGE_BACKEND = 'openai'
$env:OPENAI_BASE_URL = 'SERVICE'
$env:OPENAI_MODEL = 'MODEL'
# OPENAI_API_KEY 在本地配置，不写入提示词和页面记录。
python skills/ppt-master/scripts/image_gen.py "完整页面提示词" --allow-api --backend openai --reference-image "PROJECT/background.png" --aspect_ratio 16:9 --output "PROJECT/reference_review" --filename P01
```

带参考图的页面逐页调用。批量 `--manifest` 不接受单图 `--reference-image`；不要丢掉背景后直接切换批量模式。项目已有 `AI Image Acquisition Path` 时，应与选用路径一致，不能覆盖已确认的内置生图选择。

API 参考页用 `reference_generation: external_image_api`，逐页 `generation` 记录真实 `tool`、`invocation_ref`、`prompt`、`provider`、`model`、参考图片，以及用户选择 API 的 `authorization.message/message_id`。内置生图使用 `host_native_image`。两种路径使用相同的参考页确认流程。

如果两条路径都不可用，可以提供参考图、跨工具生成，或明确选用原生设计预览。实际采用的方法要说清楚。

## 反馈和继续修改

可以按页直接反馈，例如“P03 保留主图，放大右侧结论；P05 改成上下布局”。仅更新受影响页，保留其他页面和确认状态。内容、来源或参考图片改变后，重新确认对应版本。

继续已有项目时，一起提供来源、简报、提示词、参考图和确认记录。没有回复不算通过；不要把自己的推测写成用户批准。

## 可编辑范围

- 标题、正文、图注：原生文本框、段落和 run。
- 图表和表格：数据可靠时使用相应原生对象。
- 流程和机制图：独立形状、连接线及必要分组。
- 公式：优先保留或生成 Office Math。
- 照片、复杂论文原图：独立图片，可移动、缩放和裁剪。

最终整页参考图不直接铺成放映页。制作完成后要查看真实 PPTX 的渲染结果。

## 页面预览

已生成 SVG 可在本地直接转成 PNG，不需要打开网页或启动确认服务：

```powershell
python -m pip install playwright
python -m playwright install chromium
python skills/ppt-master/scripts/visual_review.py "PROJECT"
```

输出在项目 `.preview/`。这用于检查 SVG；最终交付仍要渲染实际 PPTX。

## 常见情况

| 情况 | 处理方式 |
| --- | --- |
| 找不到 Skill 或加载旧规则 | 核对安装目录和实际 SKILL.md 路径 |
| 没有内置绘图工具 | 选择已配置的 API、提供参考图或明确选择原生预览 |
| API 不支持参考图片 | 换用支持此能力的后端，或先准备可直接使用的参考图 |
| 导出成功但显示不理想 | 查看实际 PPTX 页面，在源对象层调整并重新渲染 |
| 图片中文字或数值不清楚 | 放大查看，区分精确值、近似读图值和无法辨认项 |
| 命令执行不可用 | 保留具体错误，继续可独立完成的内容工作 |

成品展示、来源与许可证见 [学术 PPT 生成与润色](../README.md#academic-ppt-skill)。
