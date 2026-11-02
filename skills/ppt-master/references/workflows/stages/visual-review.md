---
description: Inspect page previews and the final PowerPoint render.
---

# 页面视觉检查

页面制作后，先检查 SVG，再查看实际 PPTX 的渲染效果。按内容组织、整体构图、阅读顺序和可读性判断，参数用于定位修改。

## 查看 SVG

```bash
python "${SKILL_DIR}/scripts/visual_review.py" PROJECT
```

脚本在本地启动无界面的 Chromium，将项目图片和图标嵌入页面，输出到 `.preview/`。不需要网页确认服务。所需环境为 Playwright 和 Chromium。

逐页检查：核心信息是否清楚，主要图形与文字是否协调，正文/图注能否读清，图片是否完整，是否有遮挡、错误换行、空旷失衡或多个任务堆放。对照已确认参考页；不要把构图改成更容易编码的通用模板。

## 查看实际 PPTX

导出后用实际 PowerPoint 或其他可用渲染器生成页面图。核对文字、数据、单位、公式、图层、裁剪、来源和对象类型，修复后重新渲染受影响页。SVG 预览不能代替最终文件显示效果。

已足够好的页面保留。缺少源材料、无法确认的数据或不支持的对象要说明具体范围，不凭图补造。

视觉判断参考 [visual-review.md](../../visual-review.md)，完整学术要求见 [academic-chat-design.md](../../academic-chat-design.md)。
