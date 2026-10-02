import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List

from playwright.async_api import async_playwright


# ============================================================
# CONFIG
# ============================================================

HEADLESS = True

# Normal Google Chrome installation path on Windows
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

# If Chrome is installed in Program Files (x86), use this instead:
# CHROME_PATH = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"


VIEWPORTS = {
    "desktop": {
        "width": 1440,
        "height": 900
    },
    "tablet": {
        "width": 768,
        "height": 1024
    },
    "mobile": {
        "width": 390,
        "height": 844
    }
}


# ============================================================
# HELPER
# ============================================================

def save_json(data: Any, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ============================================================
# BROWSER AUDIT
# ============================================================

async def audit_viewport(
    browser,
    url: str,
    viewport_name: str,
    viewport: Dict[str, int],
    output_dir: Path
):

    context = await browser.new_context(
        viewport=viewport,
        device_scale_factor=1
    )

    page = await context.new_page()

    console_errors: List[str] = []
    page_errors: List[str] = []
    failed_requests: List[Dict[str, Any]] = []
    bad_responses: List[Dict[str, Any]] = []

    # --------------------------------------------------------
    # Browser events
    # --------------------------------------------------------

    def on_console(message):
        if message.type == "error":
            console_errors.append(message.text)

    def on_page_error(error):
        page_errors.append(str(error))

    def on_request_failed(request):
        failed_requests.append({
            "url": request.url,
            "method": request.method,
            "resource_type": request.resource_type,
            "failure": request.failure
        })

    async def on_response(response):
        if response.status >= 400:
            bad_responses.append({
                "url": response.url,
                "status": response.status,
                "resource_type": response.request.resource_type
            })

    page.on("console", on_console)
    page.on("pageerror", on_page_error)
    page.on("requestfailed", on_request_failed)
    page.on("response", on_response)

    # --------------------------------------------------------
    # Open website
    # --------------------------------------------------------

    navigation_error = None

    try:
        await page.goto(
            url,
            wait_until="networkidle",
            timeout=60000
        )
    except Exception as e:
        navigation_error = str(e)

        # Try to continue even if networkidle fails
        try:
            await page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=60000
            )
        except Exception as e2:
            navigation_error = str(e2)

    # Give frontend JS a little time
    await page.wait_for_timeout(2000)

    # --------------------------------------------------------
    # Screenshot
    # --------------------------------------------------------

    screenshot_path = (
        output_dir /
        f"{viewport_name}.png"
    )

    await page.screenshot(
        path=str(screenshot_path),
        full_page=False
    )

    # --------------------------------------------------------
    # DOM / frontend analysis
    # --------------------------------------------------------

    browser_facts = await page.evaluate(
        """
        () => {

            const viewportWidth = window.innerWidth;
            const viewportHeight = window.innerHeight;

            const documentWidth =
                document.documentElement.scrollWidth;

            const documentHeight =
                document.documentElement.scrollHeight;

            // ------------------------------------------------
            // Horizontal overflow
            // ------------------------------------------------

            const horizontalOverflow =
                documentWidth > viewportWidth + 2;


            // ------------------------------------------------
            // Broken images
            // ------------------------------------------------

            const brokenImages = [];

            document.querySelectorAll("img").forEach((img) => {

                if (
                    img.src &&
                    img.complete &&
                    img.naturalWidth === 0
                ) {

                    brokenImages.push({
                        src: img.src,
                        alt: img.alt || "",
                        width: img.width,
                        height: img.height
                    });

                }

            });


            // ------------------------------------------------
            // Missing alt attributes
            // ------------------------------------------------

            const imagesWithoutAlt = [];

            document.querySelectorAll("img").forEach((img) => {

                if (!img.hasAttribute("alt")) {

                    imagesWithoutAlt.push({
                        src: img.src
                    });

                }

            });


            // ------------------------------------------------
            // Empty buttons
            // ------------------------------------------------

            const emptyButtons = [];

            document.querySelectorAll("button").forEach((button) => {

                const text =
                    button.innerText.trim();

                const ariaLabel =
                    button.getAttribute("aria-label");

                const title =
                    button.getAttribute("title");

                if (
                    !text &&
                    !ariaLabel &&
                    !title
                ) {

                    emptyButtons.push({
                        html: button.outerHTML.substring(0, 300)
                    });

                }

            });


            // ------------------------------------------------
            // Empty links
            // ------------------------------------------------

            const emptyLinks = [];

            document.querySelectorAll("a").forEach((link) => {

                const text =
                    link.innerText.trim();

                const ariaLabel =
                    link.getAttribute("aria-label");

                if (
                    !text &&
                    !ariaLabel
                ) {

                    emptyLinks.push({
                        href: link.href,
                        html: link.outerHTML.substring(0, 300)
                    });

                }

            });


            // ------------------------------------------------
            // Very small clickable elements
            // ------------------------------------------------

            const smallControls = [];

            document.querySelectorAll(
                "button, a, input, select, textarea"
            ).forEach((element) => {

                const rect =
                    element.getBoundingClientRect();

                if (
                    rect.width > 0 &&
                    rect.height > 0 &&
                    (
                        rect.width < 20 ||
                        rect.height < 20
                    )
                ) {

                    smallControls.push({
                        tag: element.tagName,
                        text: element.innerText
                            ?.trim()
                            .substring(0, 100) || "",
                        width: rect.width,
                        height: rect.height
                    });

                }

            });


            // ------------------------------------------------
            // Elements outside viewport
            // ------------------------------------------------

            const overflowingElements = [];

            document.querySelectorAll("*").forEach((element) => {

                const rect =
                    element.getBoundingClientRect();

                if (
                    rect.width > 0 &&
                    (
                        rect.right > viewportWidth + 5 ||
                        rect.left < -5
                    )
                ) {

                    overflowingElements.push({
                        tag: element.tagName,
                        id: element.id,
                        className:
                            typeof element.className === "string"
                                ? element.className.substring(0, 150)
                                : "",
                        left: rect.left,
                        right: rect.right,
                        width: rect.width
                    });

                }

            });


            // Limit huge results
            overflowingElements.splice(50);

            // ------------------------------------------------
            // Forms
            // ------------------------------------------------

            const formInputs = [];

            document.querySelectorAll(
                "input, textarea, select"
            ).forEach((input) => {

                formInputs.push({
                    tag: input.tagName,
                    type: input.type || "",
                    name: input.name || "",
                    placeholder:
                        input.getAttribute("placeholder") || "",
                    ariaLabel:
                        input.getAttribute("aria-label") || ""
                });

            });


            // ------------------------------------------------
            // Buttons
            // ------------------------------------------------

            const buttons = [];

            document.querySelectorAll("button").forEach((button) => {

                buttons.push({
                    text: button.innerText
                        .trim()
                        .substring(0, 100),

                    disabled: button.disabled,

                    ariaLabel:
                        button.getAttribute("aria-label") || ""
                });

            });


            // ------------------------------------------------
            // Basic page information
            // ------------------------------------------------

            return {

                viewportWidth,
                viewportHeight,

                documentWidth,
                documentHeight,

                horizontalOverflow,

                brokenImages,

                imagesWithoutAlt,

                emptyButtons,

                emptyLinks,

                smallControls,

                overflowingElements,

                formInputs,

                buttons,

                title: document.title,

                url: window.location.href

            };

        }
        """
    )

    # --------------------------------------------------------
    # Result
    # --------------------------------------------------------

    result = {

        "viewport": viewport_name,

        "viewport_size": viewport,

        "screenshot": str(
            screenshot_path
        ),

        "navigation_error": navigation_error,

        "console_errors": console_errors,

        "page_errors": page_errors,

        "failed_requests": failed_requests,

        "bad_responses": bad_responses,

        "browser_facts": browser_facts

    }

    await context.close()

    return result


# ============================================================
# MAIN AUDIT
# ============================================================

async def audit_url(
    url: str,
    project_dir: str = "."
):

    output_dir = (
        Path(project_dir) /
        "screenshots"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    async with async_playwright() as playwright:

        print("Launching Google Chrome...")

        browser = await playwright.chromium.launch(
            headless=HEADLESS,
            executable_path=CHROME_PATH
        )

        results = []

        for viewport_name, viewport in VIEWPORTS.items():

            print(
                f"  -> Testing {viewport_name} "
                f"({viewport['width']}x{viewport['height']})"
            )

            try:

                result = await audit_viewport(
                    browser,
                    url,
                    viewport_name,
                    viewport,
                    output_dir
                )

                results.append(result)

            except Exception as e:

                print(
                    f"  !! Error in {viewport_name}: {e}"
                )

                results.append({
                    "viewport": viewport_name,
                    "error": str(e)
                })

        await browser.close()

    # --------------------------------------------------------
    # Save raw audit
    # --------------------------------------------------------

    report_path = (
        Path(project_dir) /
        "reports" /
        "browser_audit.json"
    )

    save_json(
        results,
        report_path
    )

    print(
        f"\nBrowser audit saved to: "
        f"{report_path}"
    )

    return results