---
description: Recovery and resume rules for the local chat/reference workflow.
---

# Failure Recovery Governance

## 1. Recovery Matrix

| Failure | Handling | Resume |
|---|---|---|
| Missing chat decision | Retain existing decisions, show unresolved items in chat, wait; never start a web server or fabricate a receipt | Current Stage 1/2 or reference gate |
| Image tool unavailable | Retry a transient host-tool error once; ask for user material or a concrete native alternative; no image API fallback or silent replacement | Resource preparation |
| Reference or blueprint changed | Prepare new revision; preserve unaffected approvals, show changed images and wait for scoped confirmation | Reference-image gate |
| Source snapshot changed | Reconcile affected facts/blueprints and invalidate their decisions; do not reuse stale approval | Source intake/reference gate |
| Missing resource or slice | Repair its actual preparation and file; placeholders cannot be final output | Resource readiness |
| Changed design/lock anchors | Repair from the retained real chat decisions and synchronize affected references | Plan/reference gate |
| Unsupported template structure | Keep source intact; use Create Template only when appropriate and authorized; do not graft native structure | Owning template stage |
| Formula or chart validation failure | Correct from reliable source data/LaTeX; never invent a number or flatten silently | Owning native object |
| SVG quality/export failure | Read the blocking findings, repair their source and rerun the gate; preserve original PPTX | Current author/export stage |
| Actual PPTX differs from reference | Repair its source/native implementation, render again; after two targeted unsuccessful repairs report the exact remaining mismatch in chat | Actual PPTX validation |
| Target renderer unavailable | Deliver no claim of visual verification; state missing renderer and keep preview distinct from actual PPTX rendering | Render validation |

All user-facing decisions and images stay in chat. Deprecated browser waits,
automatic live preview, API A/B fallback and silent Quick replanning do not run.

## 2. Artifact Repair

Repair the shallowest owning artifact. Preserve source files and source object
identity; a required missing artifact blocks downstream work. An existing
confirmed value cannot be weakened by a recovery suggestion. Spec/lock changes
affecting approved page designs require new reference evidence and scoped
approval. File existence or successful commands alone are not acceptance.

## 3. Resume

For Default, read the current Design Spec and lock once; for Quick use its
source-bound page blueprints. Read reference_review/manifest.json, source/image
hashes and the real decisions, then only the active page and required resources.
Resume at the earliest incomplete gate: intake → plan → resource/reference images
→ actual chat approval → native reconstruction → quality/export → actual PPTX
render/readback/comparison. Never jump from resource completion directly to final
authoring when page-reference approval is missing. Unchanged pages and approvals
remain intact. Edit Native keeps its round-trip passthrough identity and only
reopens the approved change scope.
