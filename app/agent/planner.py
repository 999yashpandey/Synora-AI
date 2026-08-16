import json
import re

from app.ai.llm import SynoraLLM


class SynoraPlanner:
    """
    Converts a user's goal into a structured sequence of tasks.

    This version only creates plans.
    It does NOT execute computer actions.
    """

    def __init__(self):
        self.llm = SynoraLLM()

    def create_plan(self, user_goal: str) -> dict:
        prompt = f"""
You are Synora AI's task planning module.

Your job is to break the user's goal into a small number
of clear, executable steps.

IMPORTANT RULES:

1. Return ONLY valid JSON.
2. Do not use Markdown.
3. Do not explain your reasoning.
4. Do not perform the task.
5. Each step must contain:
   - step_number
   - action
   - description
6. Keep the number of steps between 1 and 7.

Return this exact JSON structure:

{{
    "goal": "user goal",
    "steps": [
        {{
            "step_number": 1,
            "action": "ACTION_NAME",
            "description": "What needs to be done"
        }}
    ]
}}

Possible action names include:

SEARCH_FILES
OPEN_APPLICATION
OPEN_FILE
READ_FILE
SEARCH_WEB
EXTRACT_INFORMATION
ANALYZE_INFORMATION
WRITE_TEXT
ASK_USER
FINISH

User goal:

{user_goal}
"""

        raw_response = self.llm.generate(prompt)

        return self._parse_response(raw_response)

    @staticmethod
    def _parse_response(response: str) -> dict:
        """
        Extract JSON from the model response.
        """

        response = response.strip()

        # Remove Markdown code fences if the model adds them.
        response = re.sub(
            r"```json\s*",
            "",
            response,
            flags=re.IGNORECASE
        )

        response = re.sub(
            r"```\s*$",
            "",
            response
        )

        response = response.strip()

        try:
            plan = json.loads(response)

        except json.JSONDecodeError as error:
            raise ValueError(
                f"Synora Planner returned invalid JSON.\n\n"
                f"Model response:\n{response}"
            ) from error

        if "goal" not in plan or "steps" not in plan:
            raise ValueError(
                "Planner response is missing 'goal' or 'steps'."
            )

        return plan


if __name__ == "__main__":

    planner = SynoraPlanner()

    print("=" * 60)
    print("              SYNORA AI PLANNER")
    print("=" * 60)
    print("Planning mode — no computer actions will be executed.\n")

    while True:

        user_goal = input("Goal: ")

        if user_goal.lower() in ["exit", "quit"]:
            print("Planner stopped.")
            break

        try:

            plan = planner.create_plan(user_goal)

            print("\nGenerated Plan:")
            print(json.dumps(
                plan,
                indent=4,
                ensure_ascii=False
            ))

            print()

        except Exception as error:

            print(f"\nPlanner Error: {error}\n")