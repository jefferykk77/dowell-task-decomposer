import unittest
from datetime import datetime, timedelta
from app.services.decomposer import DecomposerService

class TestDecomposer(unittest.TestCase):
    def setUp(self):
        self.service = DecomposerService()

    def test_rule_decompose_short_term(self):
        # 3 days: 2025-12-29 to 2025-12-31
        start = datetime(2025, 12, 29)
        end = datetime(2025, 12, 31, 23, 59, 59)
        
        result = self.service._rule_decompose("Test Short", start, end, 10, [0,1,2,3,4])
        
        self.assertEqual(len(result["months"]), 0, "Should have 0 months for 3 days")
        self.assertEqual(len(result["weeks"]), 0, "Should have 0 weeks for 3 days")
        self.assertGreater(len(result["days"]), 0, "Should have days")
        print("Short term (3 days) check passed: 0 months, 0 weeks, >0 days")

    def test_rule_decompose_medium_term(self):
        # 20 days: 2025-12-29 to 2026-01-17
        start = datetime(2025, 12, 29)
        end = datetime(2026, 1, 17, 23, 59, 59)
        
        result = self.service._rule_decompose("Test Medium", start, end, 10, [0,1,2,3,4])
        
        self.assertEqual(len(result["months"]), 0, "Should have 0 months for 20 days")
        self.assertGreater(len(result["weeks"]), 0, "Should have weeks for 20 days")
        self.assertGreater(len(result["days"]), 0, "Should have days")
        print(f"Medium term (20 days) check passed: 0 months, {len(result['weeks'])} weeks, {len(result['days'])} days")

    def test_rule_decompose_long_term(self):
        # 40 days: 2025-12-29 to 2026-02-06
        start = datetime(2025, 12, 29)
        end = datetime(2026, 2, 6, 23, 59, 59)
        
        result = self.service._rule_decompose("Test Long", start, end, 10, [0,1,2,3,4])
        
        self.assertGreater(len(result["months"]), 0, "Should have months for 40 days")
        self.assertGreater(len(result["weeks"]), 0, "Should have weeks for 40 days")
        self.assertGreater(len(result["days"]), 0, "Should have days")
        print(f"Long term (40 days) check passed: {len(result['months'])} months, {len(result['weeks'])} weeks, {len(result['days'])} days")

    def test_build_prompt_short_term(self):
        start = datetime(2025, 12, 29)
        end = datetime(2025, 12, 31)
        prompt = self.service._build_prompt("Test Prompt", start, end, None)
        
        self.assertIn("不需要生成 `months` 和 `weeks`", prompt)
        self.assertIn("`year` (作为根节点), `days`", prompt)
        print("Prompt check passed for short term")

    def test_build_prompt_medium_term(self):
        start = datetime(2025, 12, 29)
        end = datetime(2026, 1, 17)
        prompt = self.service._build_prompt("Test Prompt", start, end, None)
        
        self.assertIn("不需要生成 `months`", prompt)
        self.assertNotIn("和 `weeks`", prompt) # Should allow weeks
        self.assertIn("`year` (作为根节点), `weeks`, `days`", prompt)
        print("Prompt check passed for medium term")

if __name__ == '__main__':
    unittest.main()
