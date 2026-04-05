from typing import Dict, Any, List


class Task:
    def __init__(
        self,
        task_id: str,
        name: str,
        description: str,
        goal: Dict[str, Any],
        max_steps: int,
    ):
        self.task_id = task_id
        self.name = name
        self.description = description
        self.goal = goal
        self.max_steps = max_steps

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "name": self.name,
            "description": self.description,
            "goal": self.goal,
            "max_steps": self.max_steps,
        }


TASKS = {

    # EASY TASK
    "easy": Task(
        task_id="easy",
        name="Find Comfortable Weather City",
        description=(
            "Check weather across multiple cities and select a city "
            "with temperature between 20°C and 30°C."
        ),
        goal={
            "type": "weather_selection",
            "temperature_range": (20, 30),
            "candidate_destinations": [
                "Delhi",
                "Mumbai",
                "Bangalore",
                "Hyderabad",
                "Chennai"
            ]
        },
        max_steps=4,
    ),


    # MEDIUM TASK
    "medium": Task(
        task_id="medium",
        name="Find Cheapest Comfortable Flight",
        description=(
            "Search flights from Pune to cities with comfortable weather "
            "(20°C–30°C) and choose the cheapest route."
        ),
        goal={
            "type": "flight_selection",
            "source_city": "Pune",
            "temperature_range": (20, 30),
            "budget_limit": 5000,
            "candidate_destinations": ["Delhi", "Mumbai", "Bangalore"],
        },
        max_steps=6,
    ),


    # HARD TASK
    "hard": Task(
        task_id="hard",
        name="Plan Complete Travel Successfully",
        description=(
            "Find a destination with good weather, cheapest flight under budget, "
            "and successfully book the ticket despite possible tool failures."
        ),
        goal={
            "type": "full_trip_planning",
            "source_city": "Pune",
            "temperature_range": (20, 30),
            "budget_limit": 5000,
            "booking_required": True,
            "candidate_destinations": ["Delhi", "Mumbai", "Bangalore"],
        },
        max_steps=8,
    ),
}


def get_task(task_id: str) -> Task:
    return TASKS.get(task_id)


def get_all_tasks() -> List[Dict[str, Any]]:
    return [task.to_dict() for task in TASKS.values()]