from typing import List, Optional
import telebot
import requests
import jsons



API_TOKEN = '7815930034:AAGsvqyPXfHunPG9AH180cg-YKEUJk9z1ms'
bot = telebot.TeleBot(API_TOKEN)

# Словарь для хранения контекста пользователей
user_contexts = {}

class UsageResponse:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

class MessageResponse:
    role: str
    content: str

class ChoiceResponse:
    index: int
    message: MessageResponse
    logprobs: Optional[str]
    finish_reason: str

class ModelResponse:
    id: str
    object: str
    created: int
    model: str
    choices: List[ChoiceResponse]
    usage: UsageResponse
    system_fingerprint: str

# Команда /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "Привет! Я ваш Telegram бот.\n"
        "Доступные команды:\n"
        "/start - вывод всех доступных команд\n"
        "/model - выводит название используемой языковой модели\n"
        "/clear - очищает контекст переписки\n"
        "Отправьте любое сообщение, и я отвечу с помощью LLM модели."
    )
    bot.reply_to(message, welcome_text)

# Команда /model
@bot.message_handler(commands=['model'])
def send_model_name(message):
    response = requests.get('http://localhost:1234/v1/models')
    if response.status_code == 200:
        model_info = response.json()
        model_name = model_info['data'][0]['id']
        bot.reply_to(message, f"Используемая модель: {model_name}")
    else:
        bot.reply_to(message, 'Не удалось получить информацию о модели.')

# Команда /clear
@bot.message_handler(commands=['clear'])
def clear_context(message):
    chat_id = message.chat.id
    if chat_id in user_contexts:
        user_contexts[chat_id] = []
        bot.reply_to(message, "Контекст очищен!")
    else:
        bot.reply_to(message, "Контекст уже пуст.")

# Обработка текстовых сообщений
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    chat_id = message.chat.id
    user_query = message.text

    # Инициализируем контекст для пользователя, если его нет
    if chat_id not in user_contexts:
        user_contexts[chat_id] = []

    # Добавляем сообщение пользователя в контекст
    user_contexts[chat_id].append({
        "role": "user",
        "content": user_query
    })

    # Формируем запрос с учётом всего контекста
    request = {
        "messages": user_contexts[chat_id]
    }

    # Отправляем запрос к LM Studio
    response = requests.post(
        'http://localhost:1234/v1/chat/completions',
        json=request
    )

    if response.status_code == 200:
        model_response: ModelResponse = jsons.loads(response.text, ModelResponse)
        bot_reply = model_response.choices[0].message.content
        # Добавляем ответ модели в контекст
        user_contexts[chat_id].append({
            "role": "assistant",
            "content": bot_reply
        })
        bot.reply_to(message, bot_reply)
    else:
        bot.reply_to(message, 'Произошла ошибка при обращении к модели.')

# Запуск бота
if __name__ == '__main__':
    bot.polling(none_stop=True)