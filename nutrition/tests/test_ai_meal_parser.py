import pytest
import json
from unittest.mock import patch
from decimal import Decimal

from nutrition.services.ai_meal_parser import (
    parse_meal_description,
    MealParsingError,
    ParsedMealItem,
)

pytestmark = pytest.mark.django_db
target_patch = 'nutrition.services.ai_meal_parser._call_gemini'

# parse_meal_description
def test_parse_meal_description_returns_items_on_valid_response():
    """
    Проверяем happy path: _call_gemini возвращает валидный JSON с одним продуктом,
    parse_meal_description должен вернуть список из одного ParsedMealItem
    с корректно сконвертированными полями (включая Decimal).
    """
    fake_response = json.dumps({
        "items": [
            {
                "name": "Банан", "is_liquid": False, "amount": 118,
                "calories": 105, "protein": 1.3, "fat": 0.3, "carbs": 27.0
            }
        ]
    })

    with patch(target_patch, return_value=fake_response) as mocked_call:
        result = parse_meal_description("банан")

    assert mocked_call.call_count == 1
    assert len(result) == 1
    assert result[0] == ParsedMealItem(
        name="Банан", is_liquid=False, amount=Decimal('118'),
        calories=Decimal('105'), protein=Decimal('1.3'), fat=Decimal('0.3'), carbs=Decimal('27.0')
    )

def test_parse_meal_description_retries_once_on_invalid_json_then_succeeds():
    """
    Проверяем retry-логику: первый вызов _call_gemini возвращает невалидный JSON
    (например, обрывок текста без закрывающей скобки), второй - валидный.
    parse_meal_description должен использовать side_effect для имитации разных
    ответов на разные вызовы, сделать ровно 2 вызова _call_gemini и в итоге
    вернуть корректный результат со второй попытки.
    """
    fake_valid_response = json.dumps({
        "items": [
            {
                "name": "Банан", "is_liquid": False, "amount": 118,
                "calories": 105, "protein": 1.3, "fat": 0.3, "carbs": 27.0
            }
        ]
    })
    fake_invalid_response = fake_valid_response.rstrip('}')

    with patch(target_patch, side_effect=[
        fake_invalid_response,
        fake_valid_response
    ]) as mocked_call:
        result = parse_meal_description("банан")

    assert mocked_call.call_count == 2
    assert len(result) == 1
    assert result[0] == ParsedMealItem(
        name="Банан", is_liquid=False, amount=Decimal('118'),
        calories=Decimal('105'), protein=Decimal('1.3'), fat=Decimal('0.3'), carbs=Decimal('27.0')
    )

def test_parse_meal_description_raises_error_after_all_attempts_fail():
    """
    Проверяем, что если _call_gemini постоянно возвращает невалидный JSON
    (все max_json_attempts попыток), parse_meal_description выбрасывает
    MealParsingError, а не зацикливается и не падает с другим исключением.
    """
    fake_valid_response = json.dumps({
        "items": [
            {
                "name": "Банан", "is_liquid": False, "amount": 118,
                "calories": 105, "protein": 1.3, "fat": 0.3, "carbs": 27.0
            }
        ]
    })
    fake_invalid_response = fake_valid_response.rstrip('}')

    with patch(target_patch, side_effect=[
        fake_invalid_response,
        fake_invalid_response
    ]) as mocked_call:
        with pytest.raises(MealParsingError):
            parse_meal_description("банан")

    assert mocked_call.call_count == 2

def test_parse_meal_description_extracts_json_wrapped_in_markdown():
    """
    Проверяем, что если _call_gemini возвращает JSON, обёрнутый в markdown-разметку
    (например, "```json\\n{...}\\n```" с текстом до и после), parse_meal_description
    всё равно успешно извлекает и парсит данные благодаря _extract_json.
    """
    fake_response = json.dumps({
        "items": [
            {
                "name": "Банан", "is_liquid": False, "amount": 118,
                "calories": 105, "protein": 1.3, "fat": 0.3, "carbs": 27.0
            }
        ]
    })
    fake_response = 'Собрал такой json: ```' + fake_response + '``` Про какой продукт мне ещё дать информацию?'

    with patch(target_patch, return_value=fake_response) as mocked_call:
        result = parse_meal_description('банан')

    assert mocked_call.call_count == 1
    assert len(result) == 1
    assert result[0] == ParsedMealItem(
        name="Банан", is_liquid=False, amount=Decimal('118'),
        calories=Decimal('105'), protein=Decimal('1.3'), fat=Decimal('0.3'), carbs=Decimal('27.0')
    )

def test_parse_meal_description_handles_multiple_items():
    """
    Проверяем случай, когда _call_gemini возвращает JSON с несколькими продуктами
    (например, 3 items). Ожидаем список из 3 ParsedMealItem в правильном порядке.
    """
    fake_response = json.dumps({
        "items": [
            {
                "name": "Банан", "is_liquid": False, "amount": 118,
                "calories": 105, "protein": 1.3, "fat": 0.3, "carbs": 27.0
            },
            {
                "name": "Куриная грудка отварная", "is_liquid": False, "amount": 150,
                "calories": 165, "protein": 31.0, "fat": 3.6, "carbs": 0.0
            },
            {
                "name": "Апельсиновый сок", "is_liquid": True, "amount": 200,
                "calories": 90, "protein": 1.4, "fat": 0.2, "carbs": 20.8
            }
        ]
    })

    with patch(target_patch, return_value=fake_response) as mocked_call:
        result = parse_meal_description('банан, куриная грудка, апельсиновый сок')

    assert mocked_call.call_count == 1
    assert len(result) == 3
    assert result[0] == ParsedMealItem(
        name="Банан", is_liquid=False, amount=Decimal('118'),
        calories=Decimal('105'), protein=Decimal('1.3'), fat=Decimal('0.3'), carbs=Decimal('27.0')
    )
    assert result[1] == ParsedMealItem(
        name="Куриная грудка отварная", is_liquid=False, amount=Decimal('150'),
        calories=Decimal('165'), protein=Decimal('31.0'), fat=Decimal('3.6'), carbs=Decimal('0.0')
    )
    assert result[2] == ParsedMealItem(
        name="Апельсиновый сок", is_liquid=True, amount=Decimal('200'),
        calories=Decimal('90'), protein=Decimal('1.4'), fat=Decimal('0.2'), carbs=Decimal('20.8')
    )

def test_parse_meal_description_second_prompt_includes_previous_error():
    """
    Проверяем, что при повторной попытке (после невалидного JSON на первой)
    промпт для второго вызова _call_gemini действительно содержит информацию
    об ошибке. Для этого нужно замокать _call_gemini с side_effect и после
    вызова проверить mocked_call.call_args_list - аргументы, с которыми
    функция была вызвана во второй раз, должны содержать текст об ошибке.
    """
    fake_valid_response = json.dumps({
        "items": [
            {
                "name": "Банан", "is_liquid": False, "amount": 118,
                "calories": 105, "protein": 1.3, "fat": 0.3, "carbs": 27.0
            }
        ]
    })
    fake_invalid_response = fake_valid_response.rstrip('}')

    with patch(target_patch, side_effect=[
        fake_invalid_response,
        fake_valid_response,
    ]) as mocked_call:
        parse_meal_description('банан')

    assert mocked_call.call_count == 2

    first_prompt = mocked_call.call_args_list[0].args[0]
    second_prompt = mocked_call.call_args_list[1].args[0]

    assert 'банан' in first_prompt
    assert 'банан' in second_prompt
    assert 'ошибка' in second_prompt.lower() or 'невалиден' in second_prompt.lower()