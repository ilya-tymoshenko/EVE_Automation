import os
import base64
import email
from email.header import decode_header
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from bs4 import BeautifulSoup
import requests 
import time
import random # Добавил для небольшой паузы

from eve_config import resource_path

# --- Конфигурация ---
DEFAULT_GOOGLE_AUTH_URI = "https://accounts.google.com/o/oauth2/auth"
DEFAULT_GOOGLE_TOKEN_URI = "https://oauth2.googleapis.com/token"
DEFAULT_GOOGLE_CERT_URL = "https://www.googleapis.com/oauth2/v1/certs"
DEFAULT_GOOGLE_REDIRECT_URI = "http://localhost"
GMAIL_TOKEN_PATH = os.environ.get("GMAIL_TOKEN_PATH", "").strip()

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify'
]

TARGET_SENDER = "eveonline@news.ccpgames.com" 
TARGET_SUBJECT = "Осталось пройти процедуру проверки" 


def env_value(name, default=""):
    return os.environ.get(name, default).strip()


def gmail_credentials_from_env():
    client_id = env_value("GOOGLE_CLIENT_ID")
    client_secret = env_value("GOOGLE_CLIENT_SECRET")
    refresh_token = env_value("GMAIL_REFRESH_TOKEN")
    if not (client_id and client_secret and refresh_token):
        return None

    return Credentials(
        token=env_value("GMAIL_ACCESS_TOKEN") or None,
        refresh_token=refresh_token,
        token_uri=env_value("GOOGLE_TOKEN_URI", DEFAULT_GOOGLE_TOKEN_URI),
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES,
    )


def google_client_config_from_env():
    client_id = env_value("GOOGLE_CLIENT_ID")
    client_secret = env_value("GOOGLE_CLIENT_SECRET")
    if not (client_id and client_secret):
        return None

    redirect_uris = [
        item.strip()
        for item in env_value("GOOGLE_REDIRECT_URIS", DEFAULT_GOOGLE_REDIRECT_URI).split(",")
        if item.strip()
    ]

    return {
        "installed": {
            "client_id": client_id,
            "project_id": env_value("GOOGLE_PROJECT_ID"),
            "auth_uri": env_value("GOOGLE_AUTH_URI", DEFAULT_GOOGLE_AUTH_URI),
            "token_uri": env_value("GOOGLE_TOKEN_URI", DEFAULT_GOOGLE_TOKEN_URI),
            "auth_provider_x509_cert_url": env_value("GOOGLE_AUTH_PROVIDER_CERT_URL", DEFAULT_GOOGLE_CERT_URL),
            "client_secret": client_secret,
            "redirect_uris": redirect_uris or [DEFAULT_GOOGLE_REDIRECT_URI],
        }
    }


def configured_token_path():
    if not GMAIL_TOKEN_PATH:
        return None
    return resource_path(GMAIL_TOKEN_PATH)


def save_credentials_if_requested(creds):
    token_path = configured_token_path()
    if not token_path:
        return
    with open(token_path, "w", encoding="utf-8") as token_file:
        token_file.write(creds.to_json())
    print(f"Токен сохранен в: {token_path}")


def remove_configured_token_file():
    token_path = configured_token_path()
    if not token_path or not token_path.exists():
        return
    try:
        token_path.unlink()
    except OSError as error:
        print(f"Не удалось удалить {token_path}: {error}")


def get_gmail_service():
    creds = gmail_credentials_from_env()
    if creds:
        print("Gmail OAuth credentials loaded from environment.")
    
    if not creds or not creds.valid:
        if creds and creds.refresh_token:
            print("Обновление токена доступа...")
            try:
                creds.refresh(Request())
            except Exception as e_refresh:
                print(f"Ошибка обновления токена: {e_refresh}. Требуется повторная авторизация.")
                remove_configured_token_file()
                creds = None
                
        if not creds:
            print("Авторизация пользователя...")
            client_config = google_client_config_from_env()
            if not client_config:
                print("!!! Не заданы GOOGLE_CLIENT_ID/GOOGLE_CLIENT_SECRET и GMAIL_REFRESH_TOKEN. Заполните .env. !!!")
                return None
            try:
                flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
                # Используем run_console для приложений без графического интерфейса или если run_local_server вызывает проблемы
                # creds = flow.run_console() 
                creds = flow.run_local_server(port=0) # Запускает локальный сервер для OAuth потока
            except Exception as e_flow:
                print(f"Ошибка во время потока авторизации: {e_flow}")
                return None
        
        if creds: # Проверяем, что creds были получены
            save_credentials_if_requested(creds)
        else: # Если creds не были получены по какой-то причине
            print("Не удалось получить учетные данные после авторизации.")
            return None


    try:
        service = build('gmail', 'v1', credentials=creds)
        print("Сервис Gmail API успешно создан.")
        return service
    except HttpError as error:
        print(f"Произошла ошибка HttpError при создании сервиса Gmail API: {error}")
        return None
    except Exception as e_build:
        print(f"Непредвиденная ошибка при создании сервиса Gmail API: {e_build}")
        return None

def decode_mime_words(s):
    if not s: return ""
    decoded_parts = []
    try:
        for part, charset in decode_header(s):
            if isinstance(part, bytes):
                decoded_parts.append(part.decode(charset or 'utf-8', 'ignore'))
            else:
                decoded_parts.append(part)
    except Exception:
        return s 
    return "".join(decoded_parts)

def find_confirmation_link_in_html(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    link_tag = None
    strong_tags = soup.find_all("strong")
    for strong in strong_tags:
        if "ПОДТВЕРДИТЬ" in strong.get_text(strip=True).upper():
            parent = strong.parent
            while parent:
                if parent.name == 'a' and parent.has_attr('href'):
                    link_tag = parent
                    break
                parent = parent.parent
            if link_tag: break
    
    if link_tag:
        print(f"  Найдена ссылка с текстом 'ПОДТВЕРДИТЬ': {link_tag['href']}")
        return link_tag['href']

    print("  Точная ссылка с 'ПОДТВЕРДИТЬ' не найдена, пробую более общий поиск...")
    all_links = soup.find_all("a", href=True)
    for link_candidate in all_links:
        link_text = link_candidate.get_text(strip=True).upper()
        href_value = link_candidate['href']
        if ("ПОДТВЕРДИТЬ" in link_text or "VERIFY" in link_text or "CONFIRM" in link_text) and \
           ("ccpgames.com/" in href_value or "eveonline.com/" in href_value):
            if "unsubscribe" not in href_value.lower() and "отписаться" not in link_text.lower():
                print(f"  Найдена вероятная ссылка подтверждения (общий поиск): {href_value}")
                return href_value
    
    print("  Ссылка подтверждения не найдена в HTML.")
    return None

def get_email_body(service, user_id, msg_id):
    try:
        message = service.users().messages().get(userId=user_id, id=msg_id, format='full').execute()
        payload = message.get('payload', {})
        parts = payload.get('parts', [])
        html_body = None

        if parts: 
            for part in parts:
                mime_type = part.get('mimeType')
                body_data = part.get('body', {}).get('data')
                if body_data and mime_type == 'text/html':
                    html_body = base64.urlsafe_b64decode(body_data.encode('ASCII')).decode('utf-8', 'ignore')
                    break 
        elif payload.get('body', {}).get('data'): 
            if payload.get('mimeType') == 'text/html':
                body_data = payload['body']['data']
                html_body = base64.urlsafe_b64decode(body_data.encode('ASCII')).decode('utf-8', 'ignore')
        
        return html_body
    except HttpError as error:
        print(f"Ошибка при получении тела письма (ID: {msg_id}): {error}")
        return None
    except Exception as e_get_body:
        print(f"Непредвиденная ошибка при получении тела письма (ID: {msg_id}): {e_get_body}")
        return None


def process_and_confirm_emails(service):
    user_id = 'me' 
    processed_successfully_ids = []
    failed_to_process_ids = []
    messages = [] 
    response = None 
    email_uids_found_count = 0

    try:
        query = f'from:"{TARGET_SENDER}" subject:"{TARGET_SUBJECT}" is:unread'
        print(f"Поиск писем по запросу: {query}")
        response = service.users().messages().list(userId=user_id, q=query).execute()
        messages = response.get('messages', [])
        
        if not messages:
            print("Не найдено новых писем, соответствующих критериям.")
            return

        email_uids_found_count = len(messages)
        print(f"Найдено писем для обработки: {email_uids_found_count}")

        for message_summary in messages:
            msg_id = message_summary['id']
            print(f"\n--- Обработка письма ID: {msg_id} ---")
            
            html_content = get_email_body(service, user_id, msg_id)

            if html_content:
                confirmation_link = find_confirmation_link_in_html(html_content)
                if confirmation_link:
                    print(f"  Переход по ссылке: {confirmation_link}")
                    confirmation_ok = False
                    try:
                        http_response = requests.get(confirmation_link, timeout=20, allow_redirects=True)
                        http_response.raise_for_status() 
                        
                        print(f"  Статус ответа от сервера: {http_response.status_code}")
                        print(f"  Финальный URL после редиректов: {http_response.url}")

                        if 200 <= http_response.status_code < 300:
                            # ВАЖНО: Уточните эту проверку на основе реальной страницы успеха!
                            # if "подтвержден" in http_response.text.lower() or "verified" in http_response.text.lower():
                            #     print("  Подтверждение на странице выглядит успешным.")
                            #     confirmation_ok = True
                            # else:
                            #     print("  Не найден явный признак успеха на странице подтверждения. Считаем успехом по статусу 2xx.")
                            #     confirmation_ok = True # Или False, если нужна строгая проверка текста
                            confirmation_ok = True # Пока считаем успехом, если статус 2xx
                            print("  Предполагаем, что переход по ссылке был успешным (статус 2xx).")
                        else:
                            print(f"  Переход по ссылке вернул статус: {http_response.status_code}")

                    except requests.exceptions.RequestException as e_req:
                        print(f"  Ошибка при переходе по ссылке (requests): {e_req}")
                    except Exception as e_link_click:
                        print(f"  Непредвиденная ошибка при обработке ссылки: {e_link_click}")

                    if confirmation_ok:
                        print(f"  Успешное подтверждение для письма ID: {msg_id}.")
                        print(f"  Перемещение письма ID: {msg_id} в корзину...")
                        try:
                            service.users().messages().modify(
                                userId=user_id, 
                                id=msg_id, 
                                body={'removeLabelIds': ['INBOX', 'UNREAD'], 'addLabelIds': ['TRASH']}
                            ).execute()
                            print("  Письмо успешно перемещено в корзину.")
                            processed_successfully_ids.append(msg_id)
                        except HttpError as error_trash:
                            print(f"  Ошибка при перемещении письма ID: {msg_id} в корзину: {error_trash}")
                            failed_to_process_ids.append(msg_id)
                    else:
                        print(f"  Не удалось подтвердить успех на странице для письма ID: {msg_id}.")
                        failed_to_process_ids.append(msg_id)
                else: 
                    print(f"  Ссылка подтверждения не найдена в теле письма ID: {msg_id}.")
                    failed_to_process_ids.append(msg_id)
            else: 
                print(f"  Не удалось извлечь HTML-тело для письма ID: {msg_id}.")
                failed_to_process_ids.append(msg_id)
            
            time.sleep(random.uniform(1.0, 2.0)) # Небольшая пауза между письмами

    except HttpError as error:
        print(f"Произошла ошибка Gmail API: {error}")
        # Сообщение об ошибке 403 было в предыдущем логе, его обработка здесь важна
        if error.resp.status in [401, 403]: # 401 - Unauthorized, 403 - Forbidden
            error_content = error.content.decode('utf-8') if error.content else "Нет деталей"
            print(f"Ошибка авторизации/доступа ({error.resp.status}). Детали: {error_content}")
            if "Gmail API has not been used" in error_content or "accessNotConfigured" in error_content:
                print("!!! API Gmail не включен для вашего проекта или изменения еще не вступили в силу. !!!")
                print(f"!!! Пожалуйста, перейдите по ссылке https://console.developers.google.com/apis/api/gmail.googleapis.com/overview?project={error.uri.split('project=')[-1].split('&')[0] if 'project=' in error.uri else 'ВАШ_PROJECT_ID'} и включите API. !!!")
                print("!!! Затем подождите несколько минут и попробуйте снова. !!!")

            remove_configured_token_file()
    except Exception as e:
        print(f"Произошла непредвиденная ошибка: {type(e).__name__} - {e}")

    print("\n" + "="*30 + " ОТЧЕТ ОБРАБОТКИ ПИСЕМ (GMAIL API) " + "="*30)
    print(f"Всего найдено писем по критериям: {email_uids_found_count}")
    if processed_successfully_ids:
        print(f"УСПЕШНО обработаны и перемещены в корзину письма с ID ({len(processed_successfully_ids)} шт.): {processed_successfully_ids}")
    if failed_to_process_ids:
        print(f"НЕ УДАЛОСЬ обработать (или были ошибки) для писем с ID ({len(failed_to_process_ids)} шт.): {failed_to_process_ids}")
    
    if email_uids_found_count > 0 and not processed_successfully_ids and not failed_to_process_ids:
        print("Ни одно из найденных писем не было обработано (возможно, из-за отсутствия ссылок или ошибок до этапа обработки UID).")
    elif email_uids_found_count == 0 and ('response' in locals() and response is not None and response.get('resultSizeEstimate', -1) == 0): # Проверка, что поиск был, но ничего не нашел
         print("Писем, соответствующих критериям, для обработки не найдено.")
    elif 'response' not in locals() or response is None: # Если ошибка произошла до выполнения запроса list
         print("Не удалось выполнить поиск писем из-за предыдущей ошибки (возможно, с API или аутентификацией).")

if __name__ == '__main__':
    gmail_service = get_gmail_service()
    if gmail_service:
        process_and_confirm_emails(gmail_service)
    else:
        print("Не удалось получить доступ к сервису Gmail. Завершение работы.")
