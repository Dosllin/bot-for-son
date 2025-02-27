import os
import json
import logging
import pytz
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext, JobQueue
# Настройки
load_dotenv()
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)
tz = pytz.timezone('Europe/Moscow')

# --- КОНСТАНТЫ ---
QUESTIONS = [
    {
        "text": "🌷 Твой любимый цвет?",
        "options": [
            ("❤️ Красный", "color_red"),
            ("💙 Синий", "color_blue"),
            ("💛 Желтый", "color_yellow"),
            ("💜 Фиолетовый", "color_purple")
        ]
    },
    {
        "text": "📸 Самое яркое наше воспоминание?",
        "options": [
            ("🤘 Концерт", "memory_concert"),
            ("🍷 Первое знакомство", "memory_first_meet"),
            ("🎡 Прогулка по ТК", "memory_park"),
            ("💡 Диалог о Милане", "memory_milana")
        ]
    },
    {
        "text": "😊 Что тебя всегда радует?",
        "options": [
            ("🐶 Щенки", "joy_puppies"),
            ("🎨 Рисование", "joy_art"),
            ("☕ Кофе", "joy_coffee"),
            ("📚 Книги", "joy_books")
        ]
    },
    {
        "text": "🌞 Твое любимое время года?",
        "options": [
            ("🌸 Весна", "season_spring"),
            ("☀️ Лето", "season_summer"),
            ("🍂 Осень", "season_autumn"),
            ("❄️ Зима", "season_winter")
        ]
    },
    {
        "text": "🎵 Что тебя вдохновляет?",
        "options": [
            ("🎹 Музыка", "inspire_music"),
            ("🌌 Природа", "inspire_nature"),
            ("🎭 Искусство", "inspire_art"),
            ("🚀 Путешествия", "inspire_travel")
        ]
    }
]



# Хранение данных
def load_user_data(user_id: int) -> dict:
    try:
        with open(f'users/{user_id}.json', 'r') as f:
            return json.load(f)
    except:
        return {'progress': 0, 'answers': {}, 'garden': []}


def save_user_data(user_id: int, data: dict):
    os.makedirs('users', exist_ok=True)
    with open(f'users/{user_id}.json', 'w') as f:
        json.dump(data, f, indent=2)


# Генерация сада
def generate_garden(data: dict) -> str:
    elements = {
        'path': ['░░'] * 10,
        'flowers': [],
        'trees': [],
        'animals': [],
        'decor': []
    }

    # Цветы
    color_map = {
        'red': '🌹',
        'blue': '💠',
        'yellow': '🌼',
        'purple': '🪻'
    }
    if 'color' in data['answers']:
        elements['flowers'] = [color_map.get(data['answers']['color'], '🌸')]

    # Память
    memory_map = {
        'concert': '🎸',  # Гитарка для концерта
        'first_meet': '🍷',  # Бокал для первого знакомства
        'park': '🎡',  # Аттракцион
        'milana': '💡'  # Лампочка как символ интересного открытия
    }
    if 'memory' in data['answers']:
        elements['trees'] = [
            '🌳',
            memory_map.get(data['answers']['memory'], '🌲'),
            '🌴'
        ]

    # Радость
    if 'joy' in data['answers']:
        elements['animals'] = ['🦋', '🐇', '🐦']

    # Время года
    season_map = {
        'spring': '🌸',
        'summer': '🌞',
        'autumn': '🍁',
        'winter': '❄️'
    }
    if 'season' in data['answers']:
        elements['decor'].append(season_map.get(data['answers']['season'], '✨'))

    # Вдохновение
    if 'inspire' in data['answers']:
        elements['decor'].extend(['🎶', '🌟', '💫'])

    # Собираем сад
    garden = f"""
✨ *Сад {data.get('name', 'Мечты')}* ✨
{' '.join(elements['decor'])}
      {' '.join(elements['flowers'])}
     {' '.join(elements['trees'])}
    {' '.join(elements['animals'])}
┏{'━' * 18}┓
┃{'  '.join(elements['path'])}┃
┗{'━' * 18}┛
Прогресс: {data['progress']}/{len(QUESTIONS)}
""".strip()

    return garden

def can_answer(last_date: str) -> bool:
    if not last_date: return True
    last = datetime.fromisoformat(last_date).astimezone(tz)
    return datetime.now(tz) > last + timedelta(hours=24)
# Кнопки
def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 Ответить на вопрос", callback_data='question'),
         InlineKeyboardButton("🌿 Посмотреть сад", callback_data='garden')],
        [InlineKeyboardButton("🎁 Получить подарок", callback_data='gift')]
    ])


def send_reminder(context: CallbackContext):
    user_id = context.job.context
    data = load_user_data(user_id)


    if data['progress'] < len(QUESTIONS):
        context.bot.send_message(
            chat_id=user_id,
            text="🌅 Доброе утро, Солнышко! Сегодня ты можешь:\n"
                 f"- Ответить на вопрос дня {data['progress'] + 1}\n"
                 "- Посмотреть свой сад\n"
                 "Выбирай в меню! 🌸",
            reply_markup=main_menu()
        )
    if data['progress'] >= len(QUESTIONS):
        return  # Не отправляем напоминания если квест завершен

def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    chat_id = user.id
    data = load_user_data(chat_id)
    save_user_data(chat_id, data)

    # Добавляем задание на напоминание
    target_date = datetime(2024, 3, 5, 12, 0, tzinfo=tz)
    context.job_queue.run_once(
        callback=send_reminder,
        when=target_date,
        context=chat_id,
        name=f"reminder_{chat_id}"
    )



    context.bot.send_voice(
        chat_id=chat_id,
        voice=open('media/voice_message.ogg', 'rb'),
        caption=f"Привет, {user.first_name}! 👋\nНажми кнопку ниже чтобы начать!",
        reply_markup=main_menu()
    )


def button_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user = update.effective_user
    data = load_user_data(user.id)

    try:
        query.answer()

        if query.data == 'garden':
            context.bot.send_message(
                chat_id=user.id,
                text=generate_garden(data),
                parse_mode='Markdown',
                reply_markup=main_menu()
            )

        elif query.data == 'question':
            if not can_answer(data.get('last_answer')):
                context.bot.send_message(
                    chat_id=user.id,
                    text="⏳ Следующий вопрос будет доступен завтра!\nЯ пришлю напоминание утром 🌄"
                )
                return

            if data['progress'] >= len(QUESTIONS):
                context.bot.send_message(
                    chat_id=user.id,
                    text="🎉 Ты прошла все вопросы! Сад полностью расцвел!",
                    reply_markup=main_menu()
                )
                return

            current_q = QUESTIONS[data['progress']]
            keyboard = [[InlineKeyboardButton(t, callback_data=c)] for t, c in current_q['options']]

            context.bot.send_message(
                chat_id=user.id,
                text=f"📅 День {data['progress'] + 1}\n{current_q['text']}",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )



            # Напоминалка на завтра
            context.job_queue.run_once(
                callback=send_reminder,
                when=86400,  # 24 часа
                context=user.id,
                name=f"reminder_{user.id}"
            )

        elif query.data.startswith(('color_', 'memory_', 'joy_', 'season_', 'inspire_')):
            category, value = query.data.split('_', 1)
            data['answers'][category] = value

            # Увеличиваем прогресс ТОЛЬКО ПОСЛЕ ОТВЕТА
            data['progress'] += 1
            data['last_answer'] = datetime.now(tz).isoformat()
            save_user_data(user.id, data)

            context.bot.send_message(
                chat_id=user.id,
                text=f"🌿 Ответ добавлен в сад: {value.capitalize()}",
                reply_markup=main_menu()
            )



        elif query.data == 'gift':

            if data['progress'] < len(QUESTIONS):

                context.bot.send_message(

                    chat_id=user.id,

                    text=f"🌱 Твой сад ещё не расцвел! Осталось ответить на {len(QUESTIONS) - data['progress']} вопросов",

                    reply_markup=main_menu()
                )
                return  # Важно: прерываем выполнение




            # Отправка финального сообщения

            context.bot.send_photo(

                chat_id=user.id,

                photo=open('media/your_photo.jpg', 'rb'),

                caption="🎉 *Твой сад полностью расцвел!*\n"

                        "Спасибо, тебе за всё!)\n"
                        "👇 **Твой подарок ждет здесь** 👇\n"
                        "https://dosllin.github.io/8marta-sonya/",

                parse_mode='Markdown'

            )


    except Exception as e:

        logger.error(f"Ошибка в обработчике: {str(e)}")

        context.bot.send_message(

            chat_id=user.id,

            text="😢 Что-то пошло не так, попробуй позже!"

        )

# Планировщик напоминаний


def main() -> None:
  application = Application.builder().token(os.getenv('BOT_TOKEN')).build()
    
    # Регистрируем обработчики
  application.add_handler(CommandHandler("start", start))
    
    # Запускаем бота
  application.run_polling()


if __name__ == '__main__':
    main()
