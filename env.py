import random
from typing import Dict, Any, Tuple

from tasks import get_task
from tools import get_tool
from grader import Grader


class ToolOrchestrationEnv:
    """
    OpenEnv-compatible environment for tool orchestration.
    Supports goal-based evaluation instead of fixed workflows.
    """

    def get_grading_results(self):
        return self.grader.get_results()

    def __init__(self):

        self.current_task = None
        self.goal = None
        self.max_steps = 0

        self.step_count = 0
        self.total_reward = 0.0

        self.history = []
        self.last_tool_output = None

        self.grader = Grader()


    # =========================
    # RESET ENVIRONMENT
    # =========================

    def reset(self, task_id: str):
        from tools import generate_dynamic_weather, WEATHER_DB
        WEATHER_DB.update(generate_dynamic_weather())

        task = get_task(task_id)

        if task is None:
            raise ValueError(f"Invalid task_id: {task_id}")

        self.current_task = task_id
        self.goal = task.goal
        self.max_steps = task.max_steps

        self.step_count = 0
        self.total_reward = 0.0
        self.history = []
        self.last_tool_output = None

        # BUG FIX: include 'history' in reset state so baseline.select_action
        # doesn't KeyError on state['history'] before the first step
        return {
            "task_id": task_id,
            "step": 0,
            "goal": self.goal,
            "remaining_steps": self.max_steps,
            "last_tool_output": None,
            "total_reward": 0.0,
            "normalized_score": 0.0,
            "history": []
        }


    # =========================
    # STEP FUNCTION
    # =========================

    def step(
        self,
        tool_name: str,
        parameters: Dict[str, Any]
    ) -> Tuple[Dict, float, bool, Dict]:

        self.step_count += 1

        tool = get_tool(tool_name)

        if tool is None:

            reward = -3
            tool_output = {"error": "invalid tool"}

        else:

            tool_output = tool.execute(**parameters)

            reward = self._compute_reward(
                tool_name,
                parameters,
                tool_output
            )

        self.last_tool_output = tool_output

        self.history.append({
            "tool": tool_name,
            "parameters": parameters,
            "output": tool_output
        })

        self.total_reward += reward

        done = self.step_count >= self.max_steps
        if done:
            self.grader.grade(
                self.current_task,
                self.total_reward
            )

        state = self.state()

        info = {
            "tool": tool_name,
            "parameters": parameters,
            "output": tool_output
        }

        return state, reward, done, info


    # =========================
    # REWARD FUNCTION
    # =========================

    def _compute_reward(
        self,
        tool_name,
        parameters,
        tool_output
    ):

        reward = 0

        # penalty if tool failed
        if "error" in tool_output:
            return -2

        goal_type = self.goal["type"]

        # -------------------------
        # EASY TASK
        # Weather selection
        # -------------------------

        if goal_type == "weather_selection":

            temperature = tool_output.get("temperature")

            # BUG FIX: guard against non-numeric temperature (e.g. "unknown"
            # returned by chaos wrong_data failure mode)
            if temperature is None or not isinstance(temperature, (int, float)):
                return -2

            min_temp, max_temp = self.goal["temperature_range"]

            if min_temp <= temperature <= max_temp:
                reward += 3
            else:
                reward -= 1


        # -------------------------
        # MEDIUM TASK
        # Flight + weather decision
        # -------------------------

        elif goal_type == "flight_selection":

            if tool_name == "search_flights":

                flights = tool_output.get("flights", [])

                if not flights:
                    return -2

                cheapest_price = min(
                    flight["price"] for flight in flights
                )

                if cheapest_price <= self.goal["budget_limit"]:
                    reward += 3
                else:
                    reward -= 2


            elif tool_name == "get_weather":

                temperature = tool_output.get("temperature")

                # BUG FIX: guard against non-numeric temperature
                if temperature is None or not isinstance(temperature, (int, float)):
                    return -2

                min_temp, max_temp = self.goal["temperature_range"]

                if min_temp <= temperature <= max_temp:
                    reward += 2
                else:
                    reward -= 1


        # -------------------------
        # HARD TASK
        # Full trip planning
        # -------------------------

        elif goal_type == "full_trip_planning":

            if tool_name == "search_flights":

                flights = tool_output.get("flights", [])

                if not flights:
                    return -2

                cheapest_price = min(
                    flight["price"] for flight in flights
                )

                if cheapest_price <= self.goal["budget_limit"]:
                    reward += 2
                else:
                    reward -= 2


            elif tool_name == "get_weather":

                temperature = tool_output.get("temperature")

                # BUG FIX: guard against non-numeric temperature
                if temperature is None or not isinstance(temperature, (int, float)):
                    return -2

                min_temp, max_temp = self.goal["temperature_range"]

                if min_temp <= temperature <= max_temp:
                    reward += 2
                else:
                    reward -= 1


            elif tool_name == "book_ticket":

                if tool_output.get("status") == "booked":
                    reward += 4
                else:
                    reward -= 2


        # discourage unnecessary tool calls
        reward -= 0.5

        return reward


    # =========================
    # CURRENT STATE OBSERVATION
    # =========================

    def state(self):

        return {

            "task_id": self.current_task,

            "step": self.step_count,

            "goal": self.goal,

            "remaining_steps":
                self.max_steps - self.step_count,

            "last_tool_output":
                self.last_tool_output,

            "total_reward":
                self.total_reward,

            "normalized_score":
                min(self.total_reward / 10.0, 1.0),

            "history":
                self.history
        }
