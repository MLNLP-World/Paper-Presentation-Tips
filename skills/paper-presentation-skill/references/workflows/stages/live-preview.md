---
description: Chat-only per-page image presentation and feedback stage.
---

# Chat Preview and Feedback

The stage name is retained for existing links. No web editor, localhost URL,
daemon, browser annotation or wait-only command is used by this local profile.

1. Read the current page IDs and revision under reference_review/. Show actual
   images in chat, labelled by page and revision. Use absolute local paths on
   hosts that support them; otherwise attach images using the host capability.
2. Receive natural-language page/object feedback. Record the actual user words,
   identify the target and update only the affected blueprint/reference image.
3. Prepare the new revision and show the changed image in chat. Record approval
   only after the user's explicit scoped reply. No response means wait.
4. After the approved-reference gate, modify the corresponding native/SVG
   objects, run normal quality/export gates, and render the actual PPTX again.
5. Show the approved reference beside the actual PPTX render. A request to change
   unrelated pages preserves other page objects and approvals.

Full contract: [academic-chat-design.md](../../academic-chat-design.md)
§5. Web/source research remains available; it is not a confirmation surface.
