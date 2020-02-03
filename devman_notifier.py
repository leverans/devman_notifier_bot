import datetime
import os
import requests
import telegram


DEVMAN_API_URL = "https://dvmn.org/api/long_polling/"


def request_reviews(since_timestamp=""):
    try:
        response = requests.get(
            DEVMAN_API_URL, params={'timestamp': since_timestamp, },
            headers={'Authorization': f"Token {os.getenv('DEVMAN_API_AUTH_TOKEN')}"}
        )
        res = response.json()
        if res['status'] == "timeout":
            return res['timestamp_to_request'], None
        elif res['status'] == "found":
            return res['last_attempt_timestamp'], res['new_attempts']

    except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
        pass
    # если возникло перехваченное выше исключение или статус вернулся какой-то неизвестный, то просто ждем дальше
    return since_timestamp, None


if __name__ == "__main__":
    proxy_url = os.getenv('PROXY_URL', "")
    pp = telegram.utils.request.Request(proxy_url=proxy_url) if proxy_url else None
    bot = telegram.Bot(token=os.getenv('BOT_TOKEN'), request=pp)

    current_timestamp = ""
    while True:
        current_timestamp, reviews = request_reviews(since_timestamp=current_timestamp)
        reviews = reviews or list()
        for review in reviews:
            result = "Задача возвращена на доработку" if review['is_negative'] else "Задача принята преподавателем"
            submitted_at = datetime.datetime.fromisoformat(review['submitted_at'])
            review_date_string = submitted_at.strftime("%d.%m в %H:%M %Z")
            bot.send_message(
                chat_id=os.getenv('CHAT_ID'),
                text=f"{result}\n"
                     f"Урок: {review['lesson_title']}\n"
                     f"Дата проверки: {review_date_string}\n"
                     f"https://dvmn.org{review['lesson_url']}"
            )
