# 使用说明

这个 Skill 用来指导 Agent 制作学术 PPT。准备好论文或已有 PPTX 后，在 Agent 的聊天框中提出要求即可。

## 使用前准备

| 需要准备 | 用途 |
| --- | --- |
| Git | 从 GitHub 下载仓库 |
| Python 3.10+ | 运行 Skill 中的制作工具 |
| Codex、Claude Code 等支持 Skill 的 Agent | 读取材料、设计页面和执行制作 |
| 文件读写、命令执行和图片查看工具 | 读取论文、运行脚本、查看页面 |
| PowerPoint、WPS 或 LibreOffice | 打开 PPTX，并导出页面图片检查效果 |
| 绘图工具或参考图片 | 生成或提供页面设计图，见下方“生图方式” |

## 下载和调用

### 1. 下载仓库

打开终端，进入希望保存仓库的文件夹，然后运行：

```powershell
git clone https://github.com/MLNLP-World/Paper-Presentation-Tips.git
cd Paper-Presentation-Tips
python -m pip install -r skills/ppt-master/requirements.txt
```

最后一条命令会安装 Python 依赖。Agent、绘图服务和 PPT 软件需要另外准备。

### 2. 打开 Agent

将下载的 `Paper-Presentation-Tips` 文件夹设为项目目录，再启动 Codex 或 Claude Code。仓库已经提供了两个 Agent 的调用入口。

在 **Codex 聊天框**中输入：

```text
$ppt-master 请根据 D:/papers/paper.pdf 制作一份中文组会 PPT，汇报约 15 分钟。先确认大纲，再展示每页参考图。
```

在 **Claude Code 聊天框**中输入：

```text
/ppt-master 请润色 D:/slides/talk.pptx。先列出具体问题和改法，等确认后再设计参考图和制作 PPTX。
```

将示例中的路径换成自己的文件路径。上面两条是发给 Agent 的消息，下载和安装命令则在终端运行。

### 安装到其他项目

如果希望在另一个项目目录中调用，在仓库根目录运行下面对应的命令。将 `PROJECT` 换成目标项目的完整路径，例如 `D:/my-talk`。

```powershell
# 安装到 Codex 项目
python skills/ppt-master/scripts/install_skill.py --skill ppt-master --agent codex --project "PROJECT"

# 安装到 Claude Code 项目
python skills/ppt-master/scripts/install_skill.py --skill ppt-master --agent claude --project "PROJECT"
```

这会复制整份 Skill。安装后在目标项目中重新打开 Agent 对话。

其他支持 Agent Skills 的工具，可以复制完整的 `skills/ppt-master/` 文件夹，或指定安装目录：

```powershell
python skills/ppt-master/scripts/install_skill.py --skill ppt-master --destination "SKILLS_DIR/ppt-master"
```

将 `SKILLS_DIR` 换成该工具存放 Skill 的目录。目标已有同名安装时，加上 `--overwrite` 才会更新；旧目录会自动保留备份。

安装命令中请保留 `--skill ppt-master`，明确选择本页介绍的 Skill。

## 准备哪些材料

提供以下信息即可开始：

- 论文 PDF、研究材料或已有 PPTX 的准确路径。
- 汇报语言、听众和时长。
- 希望沿用的学校模板、背景或喜欢的样页；没有也可以说明。
- 如果接着上次修改，提供项目文件夹和要继续的版本。

例如：

> 根据 paper.pdf 制作中文组会 PPT，约 15 分钟，听众是本领域研究生。使用 GROW.pptx 的背景。重点讲清楚研究问题、方法和主要实验。

论文中的数值、公式、单位和结论应保留原意。缺少数据时，Agent 应指出需要补充什么。

## 制作时会确认什么

1. **问题和大纲**：已有 PPT 先列出问题所在、为什么影响理解、准备怎么改；新 PPT 先整理讲述顺序和每页内容。已经清楚的页面可以保留。
2. **页面参考图**：展示完整页面图片，供检查文字、主图、配色和布局。
3. **可编辑成品**：按确认的设计制作 PPTX，用 PPT 软件导出页面图片检查，再修正显示问题。

可以这样回复问题清单：

> D01、D03 按建议修改，D02 保留原页。

可以这样回复参考图：

> P01 和 P02 通过；P03 保留主图，放大右侧结论；P05 改成上下布局。

确认修改建议后，还会继续展示参考图。某页的内容或设计发生变化时，只需重新查看受影响的页面。

规划时会查看适合的模板、图表和图标，并说明准备借鉴什么。包内还带有 [11 页示例及组件索引](positive-examples.md)，可用于参考案例、公式讲解和实验展示。

## 生图方式

### Agent 自带绘图工具

有绘图工具时，默认用它生成完整页面参考图。提供背景或样页后，Agent 会将其作为图片参考。

Claude 等 Agent 的不同版本、不同会话，可用工具可能不同。可以先问：“本次对话能否生成图片？准备使用什么工具？”

### 已配置的在线绘图服务

没有内置绘图工具时，可以选择自己能使用的在线服务。服务商会提供服务地址、模型名和 API Key（访问密钥）。

`skills/ppt-master/.env.example` 包含配置示例。将自己的配置放在本地 `.env` 或环境变量中，真实密钥不要写进聊天内容或提交到仓库。

可以先让 Agent 检查支持哪些服务，或在终端运行：

```powershell
python skills/ppt-master/scripts/image_gen.py --list-backends
```

以兼容 OpenAI 接口的服务为例，下面的 `SERVICE`、`MODEL`、`PROJECT` 都需要替换。API Key 在本地配置好后再执行：

```powershell
$env:IMAGE_BACKEND = 'openai'
$env:OPENAI_BASE_URL = 'SERVICE'
$env:OPENAI_MODEL = 'MODEL'
python skills/ppt-master/scripts/image_gen.py "完整页面提示词" --allow-api --backend openai --reference-image "PROJECT/background.png" --aspect_ratio 16:9 --output "PROJECT/reference_review" --filename P01
```

`--allow-api` 表示本次明确选择在线服务。使用背景图时，服务需要支持参考图片；带参考图的页面应逐页生成。

### 自己提供图片或查看可编辑草稿

也可以在其他绘图工具中生成参考图，再把图片交给 Agent。暂时没有绘图工具时，可明确选择“先制作可编辑草稿，再查看它的实际预览”。Agent 应说明本次采用哪种方式。

无论采用哪种方式，后续都需要查看真实 PPTX 的显示效果。

## 会得到哪些文件

Agent 会说明项目目录和成品位置。通常包括：

| 文件 | 用途 |
| --- | --- |
| `design_spec.md` | 汇报大纲、每页内容和设计安排；快速模式会简化这部分 |
| `reference_review/` | 页面参考图、生成提示词和按页反馈 |
| 最终 `.pptx` 文件 | 可以在 PPT 软件中继续编辑的成品 |
| 实际页面预览和前后对照 | 查看 PPTX 打开后的真实效果 |
| 来源与修改说明 | 说明用过的材料、改过的页面和保留为图片的部分 |

打开 Markdown 对照文档时，应保留旁边的图片文件夹，并使用支持 Markdown 图片预览的编辑器，例如 VS Code。只复制 Markdown 文件会导致图片缺失。

## 哪些部分可以编辑

| 组件 | 在 PPT 中能做什么 |
| --- | --- |
| 标题、正文和图注 | 直接改字、调整字体和段落 |
| 表格 | 编辑单元格内容和样式 |
| 数据图表 | 数据来源完整、工具支持时，编辑图表及其数据 |
| 流程图、机制图 | 分别移动和修改形状、连接线及组合 |
| 公式 | 优先使用 Office 原生公式，按实际软件支持情况编辑 |
| 照片、复杂论文原图 | 移动、缩放和裁剪；图片内部的文字和图形通常不能分别编辑 |

交付时应说明哪些组件仍是图片，以及哪些对象受软件支持限制。

## 继续修改

提供项目文件夹，并说明要改的页和保留的部分，例如：

> 继续这个项目。第 3 页结论再大一点，第 5 页换成上下布局，其余页保留。

保留原材料、页面参考图和反馈记录，Agent 才能接着已确认的版本制作。

## 常见问题

| 遇到的情况 | 可以怎么做 |
| --- | --- |
| 找不到 Skill | 确认打开的是安装所在项目，再重新打开对话 |
| 同时出现 Local 和 Project 两个版本 | 在仓库内测试时选 Project，并让 Agent 显示实际读取的 SKILL.md 路径 |
| 仍然读到旧规则 | 更新实际安装的目录；更新仓库不会自动替换其他项目的副本 |
| 没有绘图工具 | 配置在线绘图服务、提供参考图，或选择可编辑草稿预览 |
| 服务不接受背景图 | 换用支持参考图片的服务，或自行准备完整参考图 |
| PPT 打开后字体或布局不对 | 提供实际页面截图或渲染结果，让 Agent 在 PPT 对象上修改后重新检查 |
| 图片中的数字看不清 | 提供高清原图或原始数据，无法确认的数值应标为未知 |
| Agent 无法执行命令 | 提供原始报错，先解决执行问题，再继续制作和导出 |

## 更新

进入最初克隆的仓库目录，运行：

```powershell
git pull --ff-only
python -m pip install -r skills/ppt-master/requirements.txt
```

安装到其他项目的副本需要再次运行安装命令，并加 `--overwrite`。仓库内的入口会直接读取 `skills/ppt-master/`。

成品对照和来源说明见 [仓库首页](../../../README.md#academic-ppt-skill)。
