import unittest
import sys
from pathlib import Path
from datetime import date

# Add the AI engine directory to Python's import path.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from planner import generate_daily_plan, reschedule_tasks
from goal_decomposer import decompose_goal
from assistant import process_chat_message


class PlannerTests(unittest.TestCase):
    def setUp(self):
        self.tasks = [
            {"id": "a", "title": "DSA practice", "estimated_minutes": 60, "priority": "high", "importance": "high"},
            {"id": "b", "title": "Read notes", "estimated_minutes": 45, "priority": "low", "importance": "medium"},
            {"id": "c", "title": "Submit report", "estimated_minutes": 30, "priority": "critical", "importance": "high", "deadline": "2026-10-11"},
        ]

    def test_never_exceeds_budget(self):
        plan = generate_daily_plan(self.tasks, 75, plan_date="2026-10-11")
        self.assertLessEqual(plan["total_planned_minutes"], 75)
        self.assertEqual(plan["total_planned_minutes"], sum(x["duration_minutes"] for x in plan["schedule"]))

    def test_marks_tasks_that_do_not_fit(self):
        plan = generate_daily_plan(self.tasks, 60, plan_date="2026-10-11")
        self.assertTrue(plan["unscheduled_tasks"])

    def test_sequential_no_overlap(self):
        plan = generate_daily_plan(self.tasks, 180, plan_date="2026-10-11", start_time="10:00")
        for first, second in zip(plan["schedule"], plan["schedule"][1:]):
            self.assertEqual(first["end_time"], second["start_time"])

    def test_completed_tasks_excluded(self):
        tasks = [{"id": "x", "title": "Done", "estimated_minutes": 20, "status": "completed"}]
        self.assertEqual(generate_daily_plan(tasks, 60)["schedule"], [])

    def test_unmet_dependency_blocked(self):
        tasks = [{"id": "b", "title": "Build", "estimated_minutes": 20, "dependencies": ["a"]}]
        plan = generate_daily_plan(tasks, 60)
        self.assertEqual(plan["unscheduled_tasks"][0]["reason"], "Blocked by incomplete dependencies")

    def test_zero_minutes(self):
        plan = generate_daily_plan(self.tasks, 0)
        self.assertEqual(plan["total_planned_minutes"], 0)
        self.assertEqual(len(plan["unscheduled_tasks"]), 3)

    def test_invalid_duration_rejected(self):
        with self.assertRaises(ValueError):
            generate_daily_plan([{"id": "x", "title": "Bad", "estimated_minutes": 0}], 30)

    def test_goal_decomposition_marks_estimates(self):
        result = decompose_goal("Prepare for DBMS exam", 5)
        self.assertTrue(result["tasks"])
        self.assertEqual(result["tasks"][0]["estimate_type"], "heuristic_estimate")
        self.assertFalse(result["llm_used"])

    def test_chat_routes_plan(self):
        result = process_chat_message("Plan my day", {"tasks": self.tasks, "available_minutes": 120})
        self.assertEqual(result["intent"], "generate_daily_plan")


if __name__ == "__main__":
    unittest.main()
