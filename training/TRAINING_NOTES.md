# Training plan

## Do this only after the MVP works

Training a foundation LLM from random initialization is unnecessary for this project and would require a very large dataset and compute budget.

Use supervised fine-tuning (LoRA/QLoRA) on a vision-language base model instead.

### Dataset target

Start with 200-500 carefully labeled website screenshots and diagnostics.
Aim for 1,000+ examples for a stronger project demo.

Include both:
- buggy pages
- clean pages with an empty bug list

Balance the dataset across:
- UI
- UX
- Frontend
- desktop/tablet/mobile
- different frameworks and design styles

### Label quality

Every bug should have:
- exact viewport
- evidence
- severity
- selector when possible
- recommended fix

Never label a design preference as a bug unless your project has a stated rule for it.
