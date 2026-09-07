import json
import logging
from dataclasses import dataclass
from decimal import Decimal

from django.conf import settings
from google import genai
from google.genai import types

from common.retry import retry_on_network_error

logger = logging.getLogger(__name__)

class MealParsingError(Exception):
    """Вызывается, когда не удалось получить валидный JSON от модели после всех попыток."""
    pass

@dataclass
class ParsedMealItem:
    name: str
    is_liquid: bool
    amount: Decimal
    calories: Decimal
    protein: Decimal
    fat: Decimal
    carbs: Decimal

_client = genai.Client(api_key=settings.GEMINI_API_KEY)

MEAL_PARSER_PROMPT_TEMPLATE = """
Ты - помощник по подсчёту калорий. Пользователь описывает, что он съел.
Разбери описание на отдельные продукты. Для каждого продукта определи:
- name: короткое понятное название продукта (на русском)
- is_liquid: true, если это жидкость (напиток, суп, соус в жидком виде), иначе false
- amount: примерное количество продукта. Если продукт твёрдый - масса в граммах,
  если жидкий (is_liquid=true) - объём в миллилитрах. Указывай только число, без единиц измерения.
- calories, protein, fat, carbs: пищевая ценность (в граммах для белков/жиров/углеводов,
  в килокалориях для calories) именно на то количество продукта, которое указано в поле amount.
  Числа могут быть дробными (например, 12.5), не округляй специально до целых.

Если количество не указано явно - оцени разумную стандартную порцию для этого продукта.
Если описание не похоже на еду или содержит несъедобные/опасные предметы, верни пустой список items: {{"items": []}}

Ответь СТРОГО в формате JSON, без markdown-разметки, без пояснений до или после:
{{
  "items": [
    {{"name": "...", "is_liquid": true, "amount": число, "calories": число, "protein": число, "fat": число, "carbs": число}}
  ]
}}

Описание еды: {description}
"""

def _extract_json(text: str) -> dict:
    """
    Вырезает JSON-объект из текста ответа модели на случай,
    если она всё же обернула его в markdown или добавила лишний текст.
    """
    start = text.find('{')
    end = text.rfind('}')
    if start == -1 or end == -1 or start > end:
        raise ValueError("JSON не найден в ответе модели")

    return json.loads(text[start:end+1])

def _build_prompt(description: str, previous_error: str | None = None) -> str:
    """
    Формирует промпт для модели. Если previous_error передан (повторная попытка
    после невалидного JSON), добавляет к промпту явное указание об ошибке,
    чтобы повысить шанс корректного ответа со второй попытки.
    """
    prompt = MEAL_PARSER_PROMPT_TEMPLATE.format(description=description)

    if previous_error:
        prompt += (
            f"\n\nВнимание! Предыдущая попытка вернула невалидный JSON. Ошибка: {previous_error}. "
            f"Ответь строго в формате JSON."
        )

    return prompt

@retry_on_network_error(max_attempts=settings.RETRY_MAX_ATTEMPTS, delay_seconds=settings.RETRY_DELAY_SECONDS)
def _call_gemini(prompt: str) -> str:
    """
    Делает один запрос к Gemini API с заданным промптом и возвращает текст ответа.
    Обёрнута в retry_on_network_error, чтобы сетевые сбои обрабатывались отдельно
    от логики парсинга JSON.
    """

    response = _client.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(response_mime_type='application/json'),
    )

    return response.text

def _convert_to_meal_items(items: dict) -> list[ParsedMealItem]:
    result = []

    for item in items:
        result.append(
            ParsedMealItem(
                name=str(item['name']),
                is_liquid=bool(item['is_liquid']),
                amount=Decimal(str(item['amount'])),
                calories=Decimal(str(item['calories'])),
                protein=Decimal(str(item['protein'])),
                fat=Decimal(str(item['fat'])),
                carbs=Decimal(str(item['carbs'])),
            )
        )

    return result

def parse_meal_description(description: str, max_json_attempts: int = 2) -> list[ParsedMealItem]:
    """
    Отправляет текстовое описание еды в Gemini и возвращает список распознанных
    продуктов с оценкой КБЖУ, массы и признака жидкости.

    Если ответ модели не удаётся распарсить как JSON, повторяет попытку
    (до max_json_attempts раз), явно указывая модели на ошибку в промпте.
    Если все попытки провалились - выбрасывает MealParsingError.
    """
    attempt = 0
    last_exception = None
    previous_error = None

    while attempt < max_json_attempts:
        prompt = _build_prompt(description, previous_error)

        try:
            raw_response = _call_gemini(prompt)
            parsed_data = _extract_json(raw_response)
            items = _convert_to_meal_items(parsed_data['items'])

            return items

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            last_exception = e
            previous_error = str(e)
            attempt += 1
            logger.warning(f"Ошибка парсинга JSON от Gemini. Попытка {attempt}/{max_json_attempts}. Ошибка: {e}")

        except Exception as e:
            last_exception = e
            attempt += 1
            logger.error(f"Не удалось получить ответ от Gemini. Попытка {attempt}/{max_json_attempts}. Ошибка: {e}")

    raise MealParsingError(
        f"Не удалось распознать описание еды после {max_json_attempts} попыток. Ошибка: {last_exception}"
    )