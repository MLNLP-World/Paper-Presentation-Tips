# 图片与生图

默认使用宿主内置图像生成/编辑工具。没有该工具时，可使用用户选定并配置的外部 API；选用方式、实际提示词、参考图片和生成来源都应记录。

- `image_gen.py --list-backends`：列出包内适配器。
- `image_gen.py --render-md MANIFEST`：离线导出提示词 Markdown。
- `image_gen.py "完整提示词" --allow-api --backend PROVIDER --reference-image BACKGROUND --output OUTPUT`：显式使用选定 API，实际支持范围取决于后端和模型。
- `image_treat.py`、`analyze_images.py`、`slice_images.py`：图片处理、检查与切片。

完整参考页的标题、正文、图表和图注均可以出现在 AI 参考图中。原生可编辑制作在聊天确认后完成。论文原图、真实数据和公式含义需要核对，不能由生图模型补造。

细节见 [学术设计规则](../academic-chat-design.md)、[参考图流程](../page-reference-generation.md) 和仓库使用说明。
