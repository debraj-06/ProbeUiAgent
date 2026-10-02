# UI/UX + Frontend Bug Detection Agent

This is the first agent in a multi-agent website review system.

Input: a public website URL.
Output: a structured JSON bug report for the final review agent.

## Architecture

URL -> Playwright browser audit -> screenshots + DOM/browser diagnostics -> local Qwen3-VL model -> structured JSON -> final reviewer agent

The model runs locally through Ollama. No OpenAI/Gemini/Claude API key is required.

## 1. Install Ollama

Install Ollama for your operating system from the official Ollama website.

Then download the vision model:

```powershell
ollama pull qwen3-vl:4b
```

For a lower-memory machine, use `qwen3-vl:2b` and change `FROM` and `UI_BUG_MODEL` accordingly.

## 2. Create the specialized local model

From this project folder:

```powershell
ollama create ui-bug-detector -f Modelfile
```

This creates a local specialized model configuration based on the open model. It is not foundation-model training yet.

## 3. Python setup (Windows PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
playwright install chromium
```

If PowerShell blocks activation, run Python directly with `.venv\Scripts\python.exe`.

## 4. Run

```powershell
python main.py https://example.com
```

Or:

```powershell
python main.py https://your-site.com --output reports/my_site.json
```

Screenshots are stored in `screenshots/` and the full report in `reports/`.

## What this first version checks

- desktop/tablet/mobile rendering
- horizontal overflow
- broken images
- missing image alt attributes
- unlabeled form controls/buttons
- empty links/buttons
- suspiciously tiny controls
- elements rendered outside the viewport
- browser console errors
- page errors
- failed requests
- HTTP responses >= 400
- screenshot-based visual issues
- screenshot-based responsive UI issues
- basic UX problems visible in the page

## Important limitation

Do not claim that this is a fully trained LLM. This first version uses an open-weight local vision-language model and specializes it with prompts + browser evidence.

## Training phase

Collect real examples in `dataset/`. Each example should contain:

- screenshot
- browser diagnostics
- correct bug JSON labels

Once you have enough labeled examples, fine-tune a small vision-language base model with LoRA/QLoRA. That is the stage where you can honestly say the model was trained on your own bug dataset.
