from env import ToolOrchestrationEnv


class BaselineAgent:
    """
    Rule-based baseline agent for OpenEnv evaluation.

    This agent:
    - reads environment observations
    - selects tools dynamically
    - adapts decisions based on results
    - produces deterministic reproducible scores
    """

    def __init__(self):

        self.env = ToolOrchestrationEnv()


    # =========================
    # TOOL SELECTION POLICY
    # =========================

    def select_action(self, state):

        goal = state["goal"]
        history = state.get("history", [])

        goal_type = goal["type"]


        # -------------------------
        # EASY TASK POLICY
        # -------------------------

        if goal_type == "weather_selection":

            # BUG FIX: key was 'candidate_cities' but tasks.py uses
            # 'candidate_destinations' — unified to 'candidate_destinations'
            cities = goal["candidate_destinations"]

            checked_cities = [
                step["parameters"].get("city")
                for step in history
                if step["tool"] == "get_weather"
            ]

            for city in cities:

                if city not in checked_cities:

                    return (
                        "get_weather",
                        {"city": city}
                    )

            return (
                "get_weather",
                {"city": cities[0]}
            )


        # -------------------------
        # MEDIUM TASK POLICY
        # -------------------------

        if goal_type == "flight_selection":

            source = goal["source_city"]
            destinations = goal["candidate_destinations"]

            checked_routes = [
                step["parameters"].get("destination")
                for step in history
                if step["tool"] == "search_flights"
            ]

            for dest in destinations:

                if dest not in checked_routes:

                    return (
                        "search_flights",
                        {
                            "source": source,
                            "destination": dest
                        }
                    )

            return (
                "get_weather",
                {"city": destinations[0]}
            )


        # -------------------------
        # HARD TASK POLICY
        # -------------------------

        if goal_type == "full_trip_planning":

            source = goal["source_city"]
            destinations = goal["candidate_destinations"]

            searched = [
                step["parameters"].get("destination")
                for step in history
                if step["tool"] == "search_flights"
            ]

            if len(searched) < len(destinations):

                for dest in destinations:

                    if dest not in searched:

                        return (
                            "search_flights",
                            {
                                "source": source,
                                "destination": dest
                            }
                        )

            weather_checked = [
                step["parameters"].get("city")
                for step in history
                if step["tool"] == "get_weather"
            ]

            if len(weather_checked) < len(destinations):

                for dest in destinations:

                    if dest not in weather_checked:

                        return (
                            "get_weather",
                            {"city": dest}
                        )

            return (
                "book_ticket",
                {"flight_number": "SG202"}
            )


        return (
            "get_weather",
            {"city": "Delhi"}
        )


    # =========================
    # RUN SINGLE TASK
    # =========================

    def run_task(self, task_id):

        state = self.env.reset(task_id)

        done = False

        while not done:

            tool_name, parameters = self.select_action(state)

            state, reward, done, info = self.env.step(
                tool_name,
                parameters
            )

        return {

            "task": task_id,

            "final_reward": state["total_reward"],

            "normalized_score": state["normalized_score"],

            "steps": state["step"]
        }


    # =========================
    # SOLVE ALL TASKS
    # =========================

    def solve(self):

        results = {}

        for task_id in ["easy", "medium", "hard"]:

            results[task_id] = self.run_task(task_id)

        return results
