import re

from app.ai.llm import SynoraLLM
from app.tools.document_tools import create_word_document_with_title
from app.tools.code_tools import create_code_file


class SynoraExecutor:
    """
    Executes higher-level user tasks.

    Supported:
    - Word document creation
    - AI-generated document content
    - Code/source file creation
    """

    def __init__(self):
        self.ai = SynoraLLM()

    # ==========================================================
    # MAIN EXECUTOR
    # ==========================================================

    def execute(self, user_request: str):

        request = user_request.strip()

        if not request:
            return None

        if self._is_word_document_request(request):
            return self._create_word_document(request)

        if self._is_code_file_request(request):
            return self._create_code_file(request)

        return None

    # ==========================================================
    # WORD DOCUMENT DETECTION
    # ==========================================================

    @staticmethod
    def _is_word_document_request(request: str) -> bool:

        text = request.lower()

        document_keywords = [
            "word file",
            "word document",
            ".docx",
            "docx file",
            "ms word",
            "microsoft word",
            "word format",
        ]

        creation_keywords = [
            "create",
            "make",
            "write",
            "generate",
            "prepare",
        ]

        return (
            any(keyword in text for keyword in document_keywords)
            and any(keyword in text for keyword in creation_keywords)
        )

    # ==========================================================
    # CODE FILE DETECTION
    # ==========================================================

    @staticmethod
    def _is_code_file_request(request: str) -> bool:

        text = request.lower()

        code_file_keywords = [
            "python file",
            "java file",
            "javascript file",
            "typescript file",
            "c++ file",
            "c file",
            "c# file",
            "source file",
            "code file",
            ".py",
            ".java",
            ".js",
            ".ts",
            ".tsx",
            ".jsx",
            ".cpp",
            ".c",
            ".cs",
            ".go",
            ".rs",
            ".php",
        ]

        creation_keywords = [
            "create",
            "make",
            "write",
            "generate",
            "prepare",
        ]

        return (
            any(keyword in text for keyword in code_file_keywords)
            and any(keyword in text for keyword in creation_keywords)
        )

    # ==========================================================
    # CREATE CODE FILE
    # ==========================================================

    def _create_code_file(self, request: str):

        information = self._extract_code_information(request)

        filename = information["filename"]
        language = information["language"]
        location = information["location"]

        prompt = f"""
Write a complete, working {language} program.

IMPORTANT OUTPUT RULES:

1. Return ONLY source code.
2. Do NOT use Markdown.
3. Do NOT use ``` code fences.
4. Do NOT explain the code.
5. Do NOT include commentary before the code.
6. Do NOT include commentary after the code.
7. Make the program complete and runnable.
8. Include all required imports.
9. Include a proper entry point when appropriate.
10. Do not leave TODO placeholders.
11. Do not truncate the program.
12. Make sure the program satisfies the user's actual request.

USER REQUEST:

{request}
"""

        try:

            content = self.ai.generate(prompt)

        except Exception as error:

            return f"I couldn't generate the code: {error}"

        if not content or not content.strip():

            return "I couldn't generate any code."

        content = self._clean_generated_code(content)

        if not content.strip():

            return "I couldn't generate usable code."

        return create_code_file(
            filename=filename,
            content=content,
            location=location,
        )

    # ==========================================================
    # CREATE WORD DOCUMENT
    # ==========================================================

    def _create_word_document(self, request: str):

        information = self._extract_document_information(request)

        title = information["title"]
        filename = information["filename"]
        word_count = information["word_count"]
        location = information["location"]

        prompt = f"""
Create the complete content for a professional Word document.

Document title:

{title}

Target length:

Approximately {word_count} words.

IMPORTANT OUTPUT RULES:

1. Write the COMPLETE document.
2. Do not stop before the conclusion.
3. Do not produce an incomplete sentence.
4. Do not produce an incomplete paragraph.
5. Do not use Markdown.
6. Do not use Markdown headings.
7. Do not write "Title:" before the title.
8. Do not repeat the document title.
9. The document title will be added separately.
10. Do not include commentary about the generation process.
11. Do not say that you are an AI.
12. Return ONLY the document body.
13. Make the content coherent and natural.
14. Make sure the ending is complete.
15. If the user requests a story, include a proper ending and a final lesson/conclusion when appropriate.

ORIGINAL USER REQUEST:

{request}
"""

        try:

            content = self.ai.generate(prompt)

        except Exception as error:

            return f"I couldn't generate the document content: {error}"

        if not content or not content.strip():

            return "I couldn't generate any document content."

        content = self._clean_generated_document(
            content,
            title,
        )

        if not content.strip():

            return "I couldn't generate usable document content."

        return create_word_document_with_title(
            filename=filename,
            title=title,
            content=content,
            location=location,
        )

    # ==========================================================
    # DOCUMENT INFORMATION
    # ==========================================================

    @staticmethod
    def _extract_document_information(request: str):

        text = request.strip()

        location = SynoraExecutor._extract_location(text)

        word_count = 100

        word_count_match = re.search(
            r"\b(\d+)\s*[-–]?\s*word(?:s)?\b",
            text,
            flags=re.IGNORECASE,
        )

        if word_count_match:

            try:
                word_count = int(word_count_match.group(1))
            except ValueError:
                word_count = 100

        title = None

        # ------------------------------------------------------
        # QUOTED TOPIC
        # ------------------------------------------------------

        quoted_patterns = [
            r'\btopic\s+(?:is\s+)?["\']([^"\']+)["\']',
            r'\babout\s+["\']([^"\']+)["\']',
            r'\bon\s+["\']([^"\']+)["\']',
            r'\bcalled\s+["\']([^"\']+)["\']',
            r'\bnamed\s+["\']([^"\']+)["\']',
        ]

        for pattern in quoted_patterns:

            match = re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            )

            if match:

                candidate = match.group(1).strip()

                if candidate:

                    title = candidate
                    break

        # ------------------------------------------------------
        # TEACHING STORY
        # ------------------------------------------------------

        if title is None:

            lower = text.lower()

            if (
                "teaching story" in lower
                or "educational story" in lower
            ):

                title = "Teaching Story"

        # ------------------------------------------------------
        # TOPIC OF
        # ------------------------------------------------------

        if title is None:

            match = re.search(
                r"\btopic\s+of\s+(.+?)"
                r"(?:\s+and\s+save"
                r"|\s+save"
                r"|\s+to\s+(?:my\s+)?desktop"
                r"|\s+on\s+(?:my\s+)?desktop"
                r"|\s+in\s+(?:my\s+)?desktop"
                r"|$)",
                text,
                flags=re.IGNORECASE,
            )

            if match:

                candidate = match.group(1).strip()

                candidate = SynoraExecutor._clean_title_candidate(
                    candidate
                )

                if candidate:
                    title = candidate

        # ------------------------------------------------------
        # ON TOPIC
        # ------------------------------------------------------

        if title is None:

            match = re.search(
                r"\bon\s+"
                r"(?:the\s+topic\s+of\s+)?"
                r"(.+?)"
                r"(?:\s+and\s+save"
                r"|\s+save"
                r"|\s+to\s+(?:my\s+)?desktop"
                r"|\s+on\s+(?:my\s+)?desktop"
                r"|\s+in\s+(?:my\s+)?desktop"
                r"|$)",
                text,
                flags=re.IGNORECASE,
            )

            if match:

                candidate = match.group(1).strip()

                candidate = SynoraExecutor._clean_title_candidate(
                    candidate
                )

                if (
                    candidate
                    and not SynoraExecutor._looks_like_instruction(
                        candidate
                    )
                ):

                    title = candidate

        # ------------------------------------------------------
        # EXPLICIT DOCUMENT FILENAME
        # ------------------------------------------------------

        filename = None

        filename_patterns = [
            r'\bfile\s+name\s+(?:is\s+)?["\']([^"\']+)["\']',
            r'\bfilename\s+(?:is\s+)?["\']([^"\']+)["\']',
            r'\bfile\s+called\s+["\']([^"\']+)["\']',
            r'\bfile\s+named\s+["\']([^"\']+)["\']',
            r'\bcalled\s+["\']([^"\']+)["\']',
            r'\bnamed\s+["\']([^"\']+)["\']',
        ]

        for pattern in filename_patterns:

            match = re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            )

            if match:

                candidate = match.group(1).strip()

                if candidate:

                    filename = SynoraExecutor._safe_filename(
                        candidate
                    )

                    break

        # ------------------------------------------------------
        # FALLBACK TITLE
        # ------------------------------------------------------

        if not title:

            title = SynoraExecutor._infer_title_from_request(
                text
            )

        if not title:

            title = "Synora Document"

        # ------------------------------------------------------
        # DEFAULT FILENAME
        # ------------------------------------------------------

        if not filename:

            filename = SynoraExecutor._safe_filename(
                title
            )

        if not filename.lower().endswith(".docx"):

            filename += ".docx"

        return {
            "title": title,
            "filename": filename,
            "word_count": word_count,
            "location": location,
        }

    # ==========================================================
    # CODE INFORMATION
    # ==========================================================

    @staticmethod
    def _extract_code_information(request: str):

        text = request.strip()

        location = SynoraExecutor._extract_location(text)

        language = SynoraExecutor._detect_language(text)

        filename = None

        # ======================================================
        # EXPLICIT FILENAME
        #
        # IMPORTANT:
        # These patterns deliberately capture ONLY the filename.
        #
        # Example:
        #
        # Create a Python file named test_synora.py on my Desktop
        #
        # Result:
        #
        # test_synora.py
        #
        # NOT:
        #
        # Create a Python file named test_synora.py
        # ======================================================

        filename_patterns = [

            # file named test_synora.py
            r'\bfile\s+named\s+["\']?'
            r'([A-Za-z0-9_.-]+\.[A-Za-z0-9]+)'
            r'["\']?(?=\s+(?:on|in|to)\b)',

            # file called test_synora.py
            r'\bfile\s+called\s+["\']?'
            r'([A-Za-z0-9_.-]+\.[A-Za-z0-9]+)'
            r'["\']?(?=\s+(?:on|in|to)\b)',

            # named test_synora.py
            r'\bnamed\s+["\']?'
            r'([A-Za-z0-9_.-]+\.[A-Za-z0-9]+)'
            r'["\']?(?=\s|$)',

            # called test_synora.py
            r'\bcalled\s+["\']?'
            r'([A-Za-z0-9_.-]+\.[A-Za-z0-9]+)'
            r'["\']?(?=\s|$)',

            # filename test_synora.py
            r'\bfilename\s+(?:is\s+)?["\']?'
            r'([A-Za-z0-9_.-]+\.[A-Za-z0-9]+)'
            r'["\']?(?=\s|$)',

            # file name test_synora.py
            r'\bfile\s+name\s+(?:is\s+)?["\']?'
            r'([A-Za-z0-9_.-]+\.[A-Za-z0-9]+)'
            r'["\']?(?=\s|$)',
        ]

        for pattern in filename_patterns:

            match = re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            )

            if match:

                candidate = match.group(1).strip()

                if candidate:

                    filename = SynoraExecutor._safe_filename(
                        candidate
                    )

                    break

        # ======================================================
        # QUOTED FILENAME FALLBACK
        # ======================================================

        if not filename:

            quoted_patterns = [

                r'\bnamed\s+["\']([^"\']+)["\']',
                r'\bcalled\s+["\']([^"\']+)["\']',
                r'\bfilename\s+(?:is\s+)?["\']([^"\']+)["\']',
                r'\bfile\s+name\s+(?:is\s+)?["\']([^"\']+)["\']',

            ]

            for pattern in quoted_patterns:

                match = re.search(
                    pattern,
                    text,
                    flags=re.IGNORECASE,
                )

                if match:

                    candidate = match.group(1).strip()

                    if candidate:

                        filename = SynoraExecutor._safe_filename(
                            candidate
                        )

                        break

        # ======================================================
        # FALLBACK FILENAME
        # ======================================================

        if not filename:

            if language == "Python":

                filename = "Synora_Program.py"

            elif language == "Java":

                filename = "Synora_Program.java"

            elif language == "JavaScript":

                filename = "Synora_Program.js"

            elif language == "TypeScript":

                filename = "Synora_Program.ts"

            elif language == "C++":

                filename = "Synora_Program.cpp"

            elif language == "C":

                filename = "Synora_Program.c"

            elif language == "C#":

                filename = "Synora_Program.cs"

            else:

                filename = "Synora_Code.txt"

        # ======================================================
        # EXTENSION
        # ======================================================

        extension_map = {
            "Python": ".py",
            "Java": ".java",
            "JavaScript": ".js",
            "TypeScript": ".ts",
            "C++": ".cpp",
            "C": ".c",
            "C#": ".cs",
            "Go": ".go",
            "Rust": ".rs",
            "PHP": ".php",
        }

        expected_extension = extension_map.get(language)

        if (
            expected_extension
            and not filename.lower().endswith(
                expected_extension
            )
        ):

            filename += expected_extension

        return {
            "filename": filename,
            "language": language,
            "location": location,
        }

    # ==========================================================
    # LOCATION
    # ==========================================================

    @staticmethod
    def _extract_location(text: str):

        location = "desktop"

        patterns = [
            r"\bsave\s+(?:it\s+)?(?:on|in|to)\s+(?:my\s+)?"
            r"(desktop|documents?|downloads?)\b",

            r"\b(?:on|in|to)\s+(?:my\s+)?"
            r"(desktop|documents?|downloads?)\b",
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            )

            if match:

                location_name = match.group(1).lower()

                if location_name.startswith("document"):

                    location = "documents"

                elif location_name.startswith("download"):

                    location = "downloads"

                else:

                    location = "desktop"

                break

        return location

    # ==========================================================
    # LANGUAGE DETECTION
    # ==========================================================

    @staticmethod
    def _detect_language(text: str):

        lower = text.lower()

        if (
            "python" in lower
            or ".py" in lower
        ):
            return "Python"

        if (
            "java" in lower
            or ".java" in lower
        ):
            return "Java"

        if (
            "javascript" in lower
            or "node.js" in lower
            or ".js" in lower
        ):
            return "JavaScript"

        if (
            "typescript" in lower
            or ".ts" in lower
            or ".tsx" in lower
        ):
            return "TypeScript"

        if (
            "c++" in lower
            or ".cpp" in lower
        ):
            return "C++"

        if (
            "c#" in lower
            or "c sharp" in lower
            or ".cs" in lower
        ):
            return "C#"

        if re.search(r"\bgo\b", lower):

            return "Go"

        if "rust" in lower or ".rs" in lower:

            return "Rust"

        if "php" in lower or ".php" in lower:

            return "PHP"

        if re.search(r"\bc\b", lower):

            return "C"

        return "Python"

    # ==========================================================
    # TITLE CLEANING
    # ==========================================================

    @staticmethod
    def _clean_title_candidate(candidate: str):

        candidate = candidate.strip()

        candidate = candidate.rstrip(
            ".,:;"
        )

        stop_patterns = [
            r"\s+and\s+save\b.*$",
            r"\s+save\s+(?:it\s+)?(?:on|in|to)\b.*$",
            r"\s+on\s+(?:my\s+)?desktop\b.*$",
            r"\s+in\s+(?:my\s+)?desktop\b.*$",
            r"\s+to\s+(?:my\s+)?desktop\b.*$",
            r"\s+on\s+(?:my\s+)?documents?\b.*$",
            r"\s+in\s+(?:my\s+)?documents?\b.*$",
            r"\s+to\s+(?:my\s+)?documents?\b.*$",
            r"\s+on\s+(?:my\s+)?downloads?\b.*$",
            r"\s+in\s+(?:my\s+)?downloads?\b.*$",
            r"\s+to\s+(?:my\s+)?downloads?\b.*$",
        ]

        for pattern in stop_patterns:

            candidate = re.sub(
                pattern,
                "",
                candidate,
                flags=re.IGNORECASE,
            )

        return candidate.strip().strip("\"'")

    # ==========================================================
    # INSTRUCTION DETECTION
    # ==========================================================

    @staticmethod
    def _looks_like_instruction(text: str):

        lower = text.lower()

        instruction_words = [
            "create",
            "make",
            "write",
            "generate",
            "prepare",
            "save",
            "file",
            "document",
            "paragraph",
            "story",
            "word",
            "words",
            "desktop",
            "lesson",
            "format",
            "professionally",
            "engaging",
        ]

        matches = sum(
            1
            for word in instruction_words
            if re.search(
                rf"\b{re.escape(word)}\b",
                lower,
            )
        )

        return matches >= 3

    # ==========================================================
    # TITLE FALLBACK
    # ==========================================================

    @staticmethod
    def _infer_title_from_request(request: str):

        text = request.lower()

        if (
            "teaching story" in text
            or "educational story" in text
        ):

            return "Teaching Story"

        if "essay" in text:

            topic_match = re.search(
                r"(?:essay|write an essay)"
                r".*?"
                r"(?:about|on|regarding)\s+"
                r"(.+?)"
                r"(?:\s+and\s+|\s+save\s+|\s+to\s+|\s+on\s+my\s+desktop|$)",
                request,
                flags=re.IGNORECASE,
            )

            if topic_match:

                candidate = (
                    topic_match.group(1)
                    .strip()
                    .strip("\"'")
                )

                if candidate:

                    return candidate

            return "Essay"

        return "Synora Document"

    # ==========================================================
    # CLEAN GENERATED CODE
    # ==========================================================

    @staticmethod
    def _clean_generated_code(content: str):

        content = content.strip()

        # Remove code fences.

        content = re.sub(
            r"^\s*```(?:python|java|javascript|typescript|"
            r"cpp|c\+\+|c|csharp|cs|go|rust|php)?\s*",
            "",
            content,
            flags=re.IGNORECASE,
        )

        content = re.sub(
            r"\s*```\s*$",
            "",
            content,
        )

        return content.strip()

    # ==========================================================
    # CLEAN GENERATED DOCUMENT
    # ==========================================================

    @staticmethod
    def _clean_generated_document(
        content: str,
        title: str,
    ):

        content = content.strip()

        content = re.sub(
            r"^\s*```(?:text|markdown)?\s*",
            "",
            content,
            flags=re.IGNORECASE,
        )

        content = re.sub(
            r"\s*```\s*$",
            "",
            content,
            flags=re.IGNORECASE,
        )

        lines = content.splitlines()

        cleaned_lines = []

        normalized_title = re.sub(
            r"[^a-z0-9]+",
            " ",
            title.lower(),
        ).strip()

        for line in lines:

            stripped = line.strip()

            if not stripped:

                cleaned_lines.append("")
                continue

            stripped = re.sub(
                r"^#{1,6}\s*",
                "",
                stripped,
            ).strip()

            if re.match(
                r"^title\s*:",
                stripped,
                flags=re.IGNORECASE,
            ):

                stripped = re.sub(
                    r"^title\s*:\s*",
                    "",
                    stripped,
                    flags=re.IGNORECASE,
                ).strip()

            normalized_line = re.sub(
                r"[^a-z0-9]+",
                " ",
                stripped.lower(),
            ).strip()

            if normalized_line == normalized_title:

                continue

            cleaned_lines.append(stripped)

        return "\n".join(
            cleaned_lines
        ).strip()

    # ==========================================================
    # SAFE WINDOWS FILENAME
    # ==========================================================

    @staticmethod
    def _safe_filename(value: str):

        value = value.strip().strip("\"'")

        # Remove Windows-invalid characters.
        #
        # IMPORTANT:
        # Underscore is intentionally NOT removed.
        #
        # test_synora.py
        # Synora_Program.java
        #
        # remain unchanged.

        value = re.sub(
            r'[<>:"/\\|?*]',
            "",
            value,
        )

        # Remove Markdown formatting characters.
        #
        # IMPORTANT:
        # "_" is NOT included here.
        #
        # This preserves valid filenames containing underscores.

        value = re.sub(
            r"[#*`]",
            "",
            value,
        )

        # Convert whitespace to underscores.

        value = re.sub(
            r"\s+",
            "_",
            value,
        )

        # Remove trailing periods/spaces.

        value = value.rstrip(". ")

        if not value:

            value = "Synora_Document"

        return value


# ==========================================================
# TEST
# ==========================================================

if __name__ == "__main__":

    executor = SynoraExecutor()

    test_requests = [

        (
            "Create a Python file named "
            "test_synora.py on my Desktop "
            "that prints Hello Synora."
        ),

        (
            "Create a Java program in a file "
            "named Calculator on my Desktop."
        ),

        (
            'Create a Word file on my Desktop '
            'about "History of India" with 100 words.'
        ),

        (
            "Create a Word document on my Desktop "
            "containing an engaging teaching story "
            "of 800–1000 words."
        ),

        (
            'Write a 500 word essay on '
            '"Artificial Intelligence" '
            "and save it on desktop."
        ),
    ]

    print("\nSynora Executor Parser Test")
    print("=" * 70)

    for request in test_requests:

        print("\nREQUEST:")
        print(request)

        if executor._is_code_file_request(request):

            info = executor._extract_code_information(
                request
            )

            print("\nTYPE: Code File")
            print("LANGUAGE:", info["language"])
            print("FILENAME:", info["filename"])
            print("LOCATION:", info["location"])

        elif executor._is_word_document_request(request):

            info = executor._extract_document_information(
                request
            )

            print("\nTYPE: Word Document")
            print("TITLE:", info["title"])
            print("FILENAME:", info["filename"])
            print("WORDS:", info["word_count"])
            print("LOCATION:", info["location"])

        else:

            print("\nTYPE: Not handled")