import pytest
from unittest.mock import patch
import json
from text_moderator import get_moderation_result

# 测试不当内容
@patch('langchain_core.runnables.RunnableSequence.invoke')
def test_text_moderation_inappropriate(mock_invoke):
    mock_invoke.return_value = {"content": "inappropriate"}
    text = "I hate everyone!"
    result = get_moderation_result(text)
    assert result == True

# 测试正常内容
@patch('langchain_core.runnables.RunnableSequence.invoke')
def test_text_moderation_appropriate(mock_invoke):
    mock_invoke.return_value = {"content": "appropriate"}
    text = "Have a great day!"
    result = get_moderation_result(text)
    assert result == False

# 测试缓存命中
def test_text_moderation_cache():
    with open('cache.json', 'w') as f:
        json.dump({"Have a great day!": False}, f)
    result = get_moderation_result("Have a great day!")
    assert result == False

if __name__ == "__main__":
    pytest.main(["-v"])