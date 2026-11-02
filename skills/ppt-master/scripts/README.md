# PPT 制作工具

所有命令相对本目录所在的 Skill 路径解析。Windows 可将示例中的 `python3` 换成 `python`。

## 常用入口

| 用途 | 脚本 | 说明 |
| --- | --- | --- |
| 创建项目与导入材料 | project_manager.py | 项目结构、来源和模板资源 |
| 读取论文、PPTX、网页等 | source_to_md.py | 统一入口，按输入选择读取后端 |
| 导入原生 PPTX | pptx_to_svg.py | 支持保留来源对象的往返编辑 |
| 应用模板资源 | apply_template.py、icon_sync.py | 安装选定模板和项目图标 |
| 参考页确认 | reference_review.py | 绑定来源、页号、图片和真实聊天反馈 |
| 外部 API 生图 | image_gen.py | 显式 `--allow-api`；也可离线 `--render-md` |
| 图片处理 | image_treat.py、analyze_images.py、slice_images.py | 缩放、裁剪、分析及切片 |
| 本地预览 | visual_review.py | 直接用 Chromium 渲染 SVG，不启动网页服务 |
| SVG 质量与整理 | svg_quality_checker.py、finalize_svg.py | 内容、资源、文本与布局检查 |
| 正式导出 | reviewed_export.py | 确认参考页后调用原生 PPTX 后端 |
| 交付检查 | pptx_delivery_check.py | 包、来源和对象检查 |
| 可选旁白和视频 | notes_to_audio.py、narration_sync.py、powerpoint_video.py | 按任务需要使用 |

## 常用命令

```bash
python project_manager.py init my-presentation
python source_to_md.py paper.pdf
python pptx_to_svg.py input.pptx -o PROJECT --inheritance-mode both --roundtrip
python apply_template.py PROJECT --root TEMPLATE_WORKSPACE
python visual_review.py PROJECT
python reference_review.py prepare PROJECT --pages PROJECT/reference_review/pages.json
# 用户在聊天确认后，按真实消息记录对应页和版本。
python reference_review.py check PROJECT --before-authoring
python svg_quality_checker.py PROJECT
python finalize_svg.py PROJECT
python reviewed_export.py PROJECT --native-charts-and-tables
```

`svg_to_pptx.py` 是底层转换器，普通生成和重设计使用带参考页确认检查的 `reviewed_export.py`。

## 说明

- [材料读取](../references/commands/conversion.md)
- [SVG 与原生 PPTX](../references/commands/svg-pipeline.md)
- [图片与生图](../references/commands/image.md)
- [模板工具](../references/commands/template-tools.md)
- [原生数据](../references/commands/native-data.md)
- [常见问题](../references/commands/troubleshooting.md)

项目工具会保留必要的来源、确认与执行记录，便于继续修改。上游版权和许可保留在包内 LICENSE。
