# LiveJournal Backup Tool

A Python script to create a full local backup of a LiveJournal blog. The script asks for the target username, validates if the journal exists, and downloads all posts, images, and comments into a local folder.

## Features

*   **Interactive Input:** Upon launch, it requests the LiveJournal username.
*   **Validation:** Checks if the journal exists before starting. If the journal is not found (404), the script terminates with the message "нет такого журнал" (no such journal).
*   **Offline Content:** Downloads posts as `.html` files for offline reading.
*   **Image Archiving:** Finds images within posts, downloads them locally, and updates the links in the HTML to point to the local files.
*   **Comments Backup:** Fetches comments (using the mobile version of the site) and appends them to the bottom of the post file.
*   **Organized Structure:** Creates a main folder named after the journal, with subfolders for images and raw comment data.

## Requirements

*   Python 3.x
*   `requests`
*   `beautifulsoup4`

## Installation

1.  Clone the repository or download the script.
2.  Install the required dependencies:
    ```bash
    pip install requests beautifulsoup4
    ```

## Usage

1.  Run the script:
    ```bash
    python SaveLj.py
    ```
2.  Enter the LiveJournal username when prompted (e.g., `mi3ch`).
3.  The script will verify the URL. If valid, it will create a folder named `{username}` and start downloading.

## Output Structure

```text
username/
├── images/               # All downloaded images from posts
├── comments_raw/         # Raw HTML files of comments (for debugging/backup)
├── YYYY_MM_DD_ID_Title.html  # The post with embedded content
└── ...
```

------------------------------------

# Скрипт для бекапа LiveJournal (ЖЖ)

Python-скрипт для создания полной локальной копии блога LiveJournal. Скрипт запрашивает имя пользователя, проверяет существование журнала и скачивает все посты, изображения и комментарии в локальную папку.

## Возможности

*   **Интерактивный ввод:** При запуске скрипт спрашивает название журнала (username).
*   **Проверка существования:** Перед началом работы проверяет доступность журнала. Если журнал не найден (ошибка 404), скрипт завершает работу с сообщением «нет такого журнал».
*   **Офлайн чтение:** Сохраняет посты в виде `.html` файлов.
*   **Сохранение изображений:** Находит изображения в постах, скачивает их в локальную папку и обновляет ссылки в HTML, чтобы они работали без интернета.
*   **Скачивание комментариев:** Загружает ветки комментариев (используя мобильную версию сайта) и добавляет их в конец файла с постом.
*   **Структура папок:** Создает папку с именем журнала, внутри которой располагаются файлы и подпапки.

## Требования

*   Python 3.x
*   `requests`
*   `beautifulsoup4`

## Установка

1.  Скачайте скрипт.
2.  Установите необходимые библиотеки:
    ```bash
    pip install requests beautifulsoup4
    ```

## Использование

1.  Запустите скрипт:
    ```bash
    python SaveLj.py
    ```
3.  Введите имя пользователя ЖЖ, когда появится запрос (например: `tema` или `varlamov`).
4.  Скрипт проверит URL. Если журнал существует, он создаст папку с именем этого журнала и начнет скачивание.

## Структура выходных данных

```text
имя_журнала/
├── images/               # Все скачанные картинки из постов
├── comments_raw/         # "Сырые" HTML файлы комментариев (техническая папка)
├── YYYY_MM_DD_ID_Название.html  # Файл поста с текстом и комментариями
└── ...
```
