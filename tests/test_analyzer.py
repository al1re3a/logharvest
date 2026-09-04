import unittest

from logharvest.analyzer import analyze_lines, normalize_message


class AnalyzerTests(unittest.TestCase):
    def test_dynamic_values_share_fingerprint(self):
        lines = [
            "2026-09-04 ERROR request 123 failed from 10.0.0.1",
            "2026-09-04 ERROR request 987 failed from 10.0.0.2",
        ]
        report = analyze_lines(lines)
        self.assertEqual(len(report.groups), 1)
        self.assertEqual(report.groups[0].count, 2)

    def test_stack_trace_is_kept_with_event(self):
        lines = ["ERROR boom", "  at app.main(app.py:42)", "INFO recovered"]
        report = analyze_lines(lines)
        self.assertEqual(report.matched_events, 1)
        self.assertIn("at app.main", report.groups[0].sample)

    def test_warning_filter(self):
        report = analyze_lines(["WARN disk almost full", "ERROR write failed"], include_warnings=False)
        self.assertEqual(report.matched_events, 1)
        self.assertEqual(report.groups[0].level, "ERROR")

    def test_normalizer_removes_volatile_values(self):
        value = normalize_message("ERROR user 123 at 192.168.1.9 after 41ms")
        self.assertEqual(value, "user <n> at <ip> after <n>")


if __name__ == "__main__":
    unittest.main()
