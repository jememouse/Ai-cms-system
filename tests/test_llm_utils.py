"""
测试 LLM 工具类
"""
import sys
import os
import unittest
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared import llm_utils


class TestExtractJson(unittest.TestCase):
    """测试 JSON 提取功能"""

    def test_direct_parse(self):
        """测试直接解析"""
        content = '{"key": "value", "number": 123}'
        result = llm_utils.extract_json(content)
        self.assertEqual(result, {"key": "value", "number": 123})

    def test_with_markdown_wrapper(self):
        """测试带 Markdown 包装的 JSON"""
        content = '```json\n{"key": "value"}\n```'
        # 需要先清理
        cleaned = content.replace("```json", "").replace("```", "").strip()
        result = llm_utils.extract_json(cleaned)
        self.assertEqual(result, {"key": "value"})

    def test_with_extra_text(self):
        """测试带额外文本的 JSON"""
        content = 'Here is the JSON: {"key": "value"} and some more text'
        result = llm_utils.extract_json(content)
        self.assertEqual(result, {"key": "value"})

    def test_nested_json(self):
        """测试嵌套 JSON"""
        content = '{"outer": {"inner": {"deep": "value"}}}'
        result = llm_utils.extract_json(content)
        self.assertEqual(result["outer"]["inner"]["deep"], "value")

    def test_invalid_json(self):
        """测试无效 JSON"""
        content = "This is not JSON at all"
        result = llm_utils.extract_json(content)
        self.assertIsNone(result)

    def test_empty_input(self):
        """测试空输入"""
        result = llm_utils.extract_json("")
        self.assertIsNone(result)

        result = llm_utils.extract_json(None)
        self.assertIsNone(result)


class TestSanitizeJson(unittest.TestCase):
    """测试 JSON 清洗功能"""

    def test_fix_invalid_escape(self):
        """测试修复非法转义"""
        # 非法反斜杠
        text = r'{"path": "C:\Users\name"}'
        result = llm_utils.sanitize_json(text)
        # 应该变成合法的
        self.assertIn(r"\\", result)

    def test_preserve_valid_escape(self):
        """测试保留合法转义"""
        text = r'{"text": "Line1\nLine2"}'
        result = llm_utils.sanitize_json(text)
        # \n 应该保留
        self.assertIn(r"\n", result)

    def test_remove_control_chars(self):
        """测试移除控制字符"""
        text = '{"key": "value\x00with\x01control"}'
        result = llm_utils.sanitize_json(text)
        # 控制字符应该被移除
        self.assertNotIn("\x00", result)
        self.assertNotIn("\x01", result)


class TestExtractJsonArray(unittest.TestCase):
    """测试 JSON 数组提取"""

    def test_direct_array(self):
        """测试直接解析数组"""
        content = '[{"a": 1}, {"b": 2}]'
        result = llm_utils.extract_json_array(content)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["a"], 1)

    def test_array_with_text(self):
        """测试带文本的数组"""
        content = 'Here is the array: [1, 2, 3] end'
        result = llm_utils.extract_json_array(content)
        self.assertEqual(result, [1, 2, 3])

    def test_not_array(self):
        """测试返回的不是数组"""
        content = '{"key": "value"}'
        result = llm_utils.extract_json_array(content)
        self.assertIsNone(result)


class TestCallLlmWithRetry(unittest.TestCase):
    """测试带重试的 LLM 调用"""

    @patch("shared.llm_utils.requests.post")
    @patch("shared.llm_utils.config")
    def test_successful_call(self, mock_config, mock_post):
        """测试成功调用"""
        # Mock 配置
        mock_config.LLM_API_KEY = "test_key"
        mock_config.LLM_API_URL = "https://api.example.com"
        mock_config.LLM_MODEL = "test-model"

        # Mock 响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        mock_post.return_value = mock_response

        # 调用
        result = llm_utils.call_llm_with_retry("Test prompt")

        # 验证
        self.assertEqual(result, "Test response")
        mock_post.assert_called_once()

    @patch("shared.llm_utils.requests.post")
    @patch("shared.llm_utils.config")
    @patch("shared.llm_utils.time.sleep")  # Mock sleep 加速测试
    def test_retry_on_failure(self, mock_sleep, mock_config, mock_post):
        """测试失败重试"""
        # Mock 配置
        mock_config.LLM_API_KEY = "test_key"
        mock_config.LLM_API_URL = "https://api.example.com"
        mock_config.LLM_MODEL = "test-model"

        # 第一次失败，第二次成功
        mock_response_fail = MagicMock()
        mock_response_fail.status_code = 500

        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {
            "choices": [{"message": {"content": "Success after retry"}}]
        }

        mock_post.side_effect = [mock_response_fail, mock_response_success]

        # 调用
        result = llm_utils.call_llm_with_retry("Test prompt", max_retries=2)

        # 验证
        self.assertEqual(result, "Success after retry")
        self.assertEqual(mock_post.call_count, 2)
        mock_sleep.assert_called()


class TestCallLlmJson(unittest.TestCase):
    """测试自动解析 JSON 的 LLM 调用"""

    @patch("shared.llm_utils.call_llm_with_retry")
    def test_call_llm_json(self, mock_call_llm):
        """测试 JSON 自动解析"""
        # Mock LLM 返回
        mock_call_llm.return_value = '{"key": "value"}'

        # 调用
        result = llm_utils.call_llm_json("Test prompt")

        # 验证
        self.assertEqual(result, {"key": "value"})

    @patch("shared.llm_utils.call_llm_with_retry")
    def test_call_llm_json_array(self, mock_call_llm):
        """测试 JSON 数组自动解析"""
        # Mock LLM 返回
        mock_call_llm.return_value = '[{"a": 1}, {"b": 2}]'

        # 调用
        result = llm_utils.call_llm_json_array("Test prompt")

        # 验证
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["a"], 1)


if __name__ == "__main__":
    unittest.main()
