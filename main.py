"""
Flow:
1. Show a welcome screen.
2. Let the teacher select one curriculum document.
3. Convert the document to Markdown with Docling.
4. Send the extracted Markdown to a local Gemma model through Ollama.
5. Display the generated activities.
6. Save the generated activities as a Markdown file.
"""

# ---------------------------------------------------------------------------
# IMPORTS
# ---------------------------------------------------------------------------


from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import flet as ft
from docling.document_converter import DocumentConverter
from ollama import ResponseError, chat


# ---------------------------------------------------------------------------
# APPLICATION CONFIGURATION
# ---------------------------------------------------------------------------

APP_TITLE = "Curriculum Activity Generator"
TEACHER_NAME = "Mrs. Smith"

OLLAMA_MODEL = "gemma4:12b" # this is where we define the exact model

OUTPUT_DIRECTORY = Path.home() / "TeacherCurriculumActivities"
SUPPORTED_EXTENSIONS = {"pdf", "docx"}


DOCUMENT_CONVERTER = DocumentConverter() # single converter, not one per upload


# ---------------------------------------------------------------------------
# RETURNED DATA
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class GenerationResult:
    title: str
    markdown_content: str
    output_path: Path


# ---------------------------------------------------------------------------
# GEMMA PROMPT
# ---------------------------------------------------------------------------

def build_activity_prompt(curriculum_markdown: str) -> str:
    """Build the prompt sent to the local Gemma model."""

    return f"""
Below is Markdown extracted from a curriculum document.

--- CURRICULUM START ---
{curriculum_markdown}
--- CURRICULUM END ---

You are an expert curriculum-planning assistant for teachers.

Read only the supplied curriculum. Do not invent curriculum expectations that
are not supported by the document.

Identify:
1. The grade.
2. The subject.
3. Every distinct strand represented in the supplied document.

Ignore assessment policies, achievement charts, grading levels,
administrative guidance, and other non-instructional material.

Generate five engaging activities for EACH strand:

1. A local field trip or community excursion.
2. An interactive group activity.
3. A second interactive group activity.
4. A hands-on or experiential activity.
5. An applied STEM or design challenge.

For every activity include:
- Activity type
- Target curriculum expectation
- Recommended group size
- Materials or equipment
- Teacher instructions
- Student instructions
- A short explanation of why the activity strengthens understanding

Use the following Markdown structure exactly:

# [Grade] — [Subject] — [Strand name]

## Activity 1: [Name]
- **Activity Type:** Field Trip / Excursion
- **Target Curriculum Expectation:** [Expectation from the document]
- **Recommended Group Size:** [Number of students, or whole class]
- **Materials / Equipment:** [List]
- **Teacher Instructions:** [Clear instructions]
- **Student Instructions:** [Clear instructions]
- **Why This Strengthens Understanding:** [Explanation]

## Activity 2: [Name]
- **Activity Type:** Group Activity
- **Target Curriculum Expectation:** [Expectation from the document]
- **Recommended Group Size:** [Number]
- **Materials / Equipment:** [List]
- **Teacher Instructions:** [Clear instructions]
- **Student Instructions:** [Clear instructions]
- **Why This Strengthens Understanding:** [Explanation]

## Activity 3: [Name]
- **Activity Type:** Group Activity
- **Target Curriculum Expectation:** [Expectation from the document]
- **Recommended Group Size:** [Number]
- **Materials / Equipment:** [List]
- **Teacher Instructions:** [Clear instructions]
- **Student Instructions:** [Clear instructions]
- **Why This Strengthens Understanding:** [Explanation]

## Activity 4: [Name]
- **Activity Type:** Hands-On / Experiential
- **Target Curriculum Expectation:** [Expectation from the document]
- **Recommended Group Size:** [Number]
- **Materials / Equipment:** [List]
- **Teacher Instructions:** [Clear instructions]
- **Student Instructions:** [Clear instructions]
- **Why This Strengthens Understanding:** [Explanation]

## Activity 5: [Name]
- **Activity Type:** STEM / Design Challenge
- **Target Curriculum Expectation:** [Expectation from the document]
- **Recommended Group Size:** [Number]
- **Materials / Equipment:** [List]
- **Teacher Instructions:** [Clear instructions]
- **Student Instructions:** [Clear instructions]
- **Why This Strengthens Understanding:** [Explanation]

Repeat the complete block for every strand.

Begin immediately with the first "# Grade — Subject — Strand" heading.
Do not include an introduction or conclusion.
""".strip()


def extract_document_markdown(selected_file: Path) -> str:
    """Convert a supported curriculum document into Markdown."""

    if not selected_file.exists():
        raise FileNotFoundError(f"The selected file does not exist: {selected_file}")

    extension = selected_file.suffix.lower().lstrip(".")
    if extension not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise ValueError(
            f"Unsupported file type '.{extension}'. Supported types: {supported}."
        )

    conversion_result = DOCUMENT_CONVERTER.convert(str(selected_file))
    markdown_content = conversion_result.document.export_to_markdown().strip()

    if not markdown_content:
        raise ValueError("Docling did not extract any readable text from the document.")

    return markdown_content


def generate_activities(curriculum_markdown: str) -> str:
    """Send curriculum Markdown to the locally running Gemma model."""

    prompt = build_activity_prompt(curriculum_markdown)

    response = chat(
        model=OLLAMA_MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )

    generated_content = response.message.content.strip()

    if not generated_content:
        raise ValueError("Gemma returned an empty response.")

    return generated_content


def extract_first_heading(markdown_content: str, fallback: str) -> str:
    """Use the first level-one Markdown heading as the display title."""

    for line in markdown_content.splitlines():
        stripped_line = line.strip()
        if stripped_line.startswith("# "):
            title = stripped_line[2:].strip()
            if title:
                return title

    return fallback


def safe_filename(value: str) -> str:
    """Convert a title into a safe cross-platform filename."""

    cleaned = re.sub(r'[<>:"/\\|?*\n\r\t]+', "-", value)
    cleaned = re.sub(r"\s+", "_", cleaned.strip())
    cleaned = re.sub(r"_+", "_", cleaned)
    cleaned = cleaned.strip("._-")

    return cleaned[:100] or "curriculum_activities"


def save_markdown(
    markdown_content: str,
    document_title: str,
    source_file: Path,
) -> Path:
    """Save generated activities to the teacher's home directory."""

    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    title_part = safe_filename(document_title)
    source_part = safe_filename(source_file.stem)

    output_path = OUTPUT_DIRECTORY / (
        f"{source_part}_{title_part}_{timestamp}.md"
    )
    output_path.write_text(markdown_content, encoding="utf-8")

    return output_path


def process_curriculum(selected_file_path: str) -> GenerationResult:
    """
    Run all blocking document and model operations.

    This function is called through asyncio.to_thread(), preventing the
    Flet interface from freezing while Docling and Gemma are working.
    """

    selected_file = Path(selected_file_path)

    curriculum_markdown = extract_document_markdown(selected_file)
    generated_content = generate_activities(curriculum_markdown)

    fallback_title = f"Activities for {selected_file.stem}"
    document_title = extract_first_heading(generated_content, fallback_title)

    output_path = save_markdown(
        markdown_content=generated_content,
        document_title=document_title,
        source_file=selected_file,
    )

    return GenerationResult(
        title=document_title,
        markdown_content=generated_content,
        output_path=output_path,
    )


# ---------------------------------------------------------------------------
# Flet interface
# ---------------------------------------------------------------------------

async def main(page: ft.Page) -> None:
    page.title = APP_TITLE
    page.padding = 0
    page.window.width = 1050
    page.window.height = 750
    page.window.min_width = 700
    page.window.min_height = 550

    file_picker = ft.FilePicker()
    page.services.append(file_picker)

    async def choose_curriculum(_: ft.ControlEvent) -> None:
        files = await file_picker.pick_files(
            dialog_title="Select a curriculum document",
            allow_multiple=False,
            allowed_extensions=sorted(SUPPORTED_EXTENSIONS),
        )

        if not files:
            return

        selected_file_path = files[0].path

        if not selected_file_path:
            show_error(
                "Flet could not access the selected file path. "
                "Run the project as a desktop application."
            )
            return

        show_processing(files[0].name)

        try:
            result = await asyncio.to_thread(
                process_curriculum,
                selected_file_path,
            )
        except FileNotFoundError as error:
            show_error(str(error))
        except ResponseError as error:
            show_error(
                "Ollama could not generate the activities.\n\n"
                f"{error}\n\n"
                f"Confirm that Ollama is running and that '{OLLAMA_MODEL}' "
                "appears when you run 'ollama list'."
            )
        except ConnectionError:
            show_error(
                "The application could not connect to Ollama. "
                "Start Ollama and try again."
            )
        except Exception as error:
            show_error(
                "The curriculum could not be processed.\n\n"
                f"Details: {error}"
            )
        else:
            show_results(result)

    def replace_screen(content: ft.Control) -> None:
        page.clean()
        page.add(content)
        page.update()

    def show_welcome() -> None:
        welcome_screen = ft.Container(
            expand=True,
            alignment=ft.Alignment.CENTER,
            content=ft.Column(
                controls=[
                    ft.Text(
                        f"Hello, {TEACHER_NAME}!",
                        size=34,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        "Turn a curriculum document into classroom activities.",
                        size=16,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(height=12),
                    ft.Button(
                        content="Upload new curriculum",
                        icon=ft.Icons.UPLOAD_FILE,
                        bgcolor=ft.Colors.BLUE_600,
                        color=ft.Colors.WHITE,
                        height=52,
                        on_click=choose_curriculum,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=12,
            ),
        )

        replace_screen(welcome_screen)

    def show_processing(filename: str) -> None:
        processing_screen = ft.Container(
            expand=True,
            alignment=ft.Alignment.CENTER,
            padding=40,
            content=ft.Column(
                controls=[
                    ft.Text(
                        "Generating curriculum activities",
                        size=30,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        f"Processing: {filename}",
                        size=16,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(height=12),
                    ft.ProgressBar(width=500),
                    ft.Text(
                        "Docling is reading the curriculum and Gemma is "
                        "generating activities. Large documents may take longer.",
                        size=14,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=16,
            ),
        )

        replace_screen(processing_screen)

    def show_results(result: GenerationResult) -> None:
        saved_path = str(result.output_path)

        result_screen = ft.Column(
            expand=True,
            spacing=0,
            controls=[
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=28, vertical=20),
                    content=ft.Row(
                        controls=[
                            ft.Column(
                                expand=True,
                                spacing=4,
                                controls=[
                                    ft.Text(
                                        result.title,
                                        size=26,
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                    ft.Text(
                                        f"Saved to: {saved_path}",
                                        size=13,
                                        selectable=True,
                                    ),
                                ],
                            ),
                            ft.Button(
                                content="Upload another",
                                icon=ft.Icons.UPLOAD_FILE,
                                on_click=choose_curriculum,
                            ),
                        ],
                    ),
                ),
                ft.Divider(height=1),
                ft.Container(
                    expand=True,
                    padding=28,
                    content=ft.ListView(
                        expand=True,
                        controls=[
                            ft.Markdown(
                                result.markdown_content,
                                selectable=True,
                                extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                            )
                        ],
                    ),
                ),
            ],
        )

        replace_screen(result_screen)

    def show_error(message: str) -> None:
        error_screen = ft.Container(
            expand=True,
            alignment=ft.Alignment.CENTER,
            padding=40,
            content=ft.Column(
                controls=[
                    ft.Icon(
                        ft.Icons.ERROR_OUTLINE,
                        size=56,
                        color=ft.Colors.RED_600,
                    ),
                    ft.Text(
                        "Something went wrong",
                        size=28,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        message,
                        size=15,
                        text_align=ft.TextAlign.CENTER,
                        selectable=True,
                    ),
                    ft.Container(height=8),
                    ft.Row(
                        controls=[
                            ft.Button(
                                content="Try another document",
                                icon=ft.Icons.UPLOAD_FILE,
                                on_click=choose_curriculum,
                            ),
                            ft.TextButton(
                                content="Return home",
                                on_click=lambda _: show_welcome(),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=14,
            ),
        )

        replace_screen(error_screen)

    show_welcome()


if __name__ == "__main__":
    ft.run(main)
