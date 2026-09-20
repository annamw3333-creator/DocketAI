#!/usr/bin/env python3
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.scoring import aggregate_scores, diff_vs_faq_script, score_turn, suggest_prompt_patches
from app.simulator import run_pack_on_bot, simulate_reply
from app.packs_loader import load_pack


class ScoringTests(unittest.TestCase):
    def test_escalation_expected(self):
        scores = score_turn(
            "I need a human",
            "I'm sorry — I can transfer you to a specialist.",
            {"expect_escalation": True, "must_include": ["transfer"]},
            [],
        )
        self.assertGreaterEqual(scores["escalation"], 90)

    def test_booking(self):
        scores = score_turn(
            "Book Saturday",
            "Confirmed — I've booked the appointment for Sam on Saturday.",
            {"expect_booking": True, "must_include": ["Saturday"]},
            [],
        )
        self.assertGreaterEqual(scores["booking_success"], 90)

    def test_aggregate(self):
        agg = aggregate_scores(
            [
                {"truthfulness": 80, "escalation": 90, "policy_adherence": 70, "tone": 80, "booking_success": 100},
                {"truthfulness": 60, "escalation": 90, "policy_adherence": 70, "tone": 80, "booking_success": 80},
            ]
        )
        self.assertIn("overall", agg)
        self.assertEqual(agg["truthfulness"], 70.0)

    def test_diff_and_patches(self):
        faq = [{"question": "hours", "answer": "Open 9-5"}]
        script = ["Welcome"]
        transcript = [{"assistant": "We are open 9-5 every weekday."}]
        diff = diff_vs_faq_script(transcript, faq, script)
        self.assertIn("matches", diff)
        patches = suggest_prompt_patches({"truthfulness": 40}, diff, [{"reason": "bad price"}])
        self.assertTrue(any("FAQ" in p for p in patches))

    def test_pack_run(self):
        bot = {
            "id": "t",
            "faq": [{"question": "deep clean", "answer": "A deep clean for a 3-bedroom starts around $250."}],
            "script": ["Thanks for calling"],
            "prompt": "",
        }
        pack = load_pack("cleaning")
        result = run_pack_on_bot(bot, pack)
        self.assertIn("scores", result)
        self.assertGreater(result["scores"]["overall"], 40)


if __name__ == "__main__":
    unittest.main()
