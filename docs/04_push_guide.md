# Выгрузка в GitHub с вашего компьютера (от вашего имени)

Работа сделана в облачной сессии, у которой нет вашего терминала и ваших учётных данных. Поэтому файлы нужно перенести на свой компьютер и закоммитить там.

## Шаг 0. Один раз: личность и доступ

```bash
git config --global user.name "Ваше Имя"
git config --global user.email "ваш-email-с-GitHub"
```

Проверка доступа (любой один способ):

```bash
gh auth login
```

Либо вход по SSH-ключу или токеном при первом `git push`.

## Шаг 1. Клон репозитория

```bash
git clone https://github.com/SamPetux/Burst-Detection-of-Civic-Activity.git
cd Burst-Detection-of-Civic-Activity
git checkout -b paper-setup
```

## Шаг 2. Получить файлы из облачной сессии

Скачайте из панели файлов приложения и положите в клон с теми же путями:

- `README.md`, `.gitignore`, `.env.example`, `requirements.txt`
- папки `docs/`, `scripts/`, `data/series/`

Не копируйте: `.cursorrules`, `AGENTS.md`, `.cursor/`, `SETUP_DONE.md`, `.venv/`.
Для локальной работы в Cursor запустите стартпак отдельно, эти файлы в git не идут.

## Шаг 3. Проверка перед коммитом

```bash
git status
```

В списке должны быть только файлы из шага 2. Ни `.env`, ни `*.sql`, ни `*.db`, ни AI-файлов.

```bash
git diff --stat
```

## Шаг 4. Коммит и пуш

```bash
git add README.md .gitignore .env.example requirements.txt docs scripts data/series
git commit -m "Add analysis, work plan, source ledger and series builder"
git push -u origin paper-setup
```

Если нужно сразу в основную ветку, вместо `paper-setup` используйте `main` (проверьте имя ветки командой `git branch --show-current`).

## Шаг 5. Проверка на GitHub

Откройте репозиторий и убедитесь, что автор коммита вы, а в дереве нет секретов и AI-файлов.

## Если пуш отклонён

- Ошибка прав: войдите заново (`gh auth login`) или проверьте, что вы владелец репозитория.
- Ошибка «rejected, fetch first»: выполните `git pull --rebase origin <ветка>` и повторите пуш.
