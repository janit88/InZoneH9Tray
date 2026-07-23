# InzoneH9Tray

# Sony INZONE H9 / H7 Battery Tray Indicator for Windows

InZoneH9Tray is a lightweight Windows system tray application that displays
the battery level and charging status of Sony INZONE H9 and INZONE H7 headsets.

InzoneH9Tray — небольшая программа для Windows, которая показывает уровень заряда наушников Sony INZONE H9 / INZONE H7 в системном трее.

Программа читает заряд напрямую через USB/COM-интерфейс донгла Sony и не требует открытого окна INZONE Hub.

## Возможности

- Показывает заряд наушников в системном трее Windows.
- Показывает состояние зарядки.
- Автоматически находит COM-порт по `VID_054C&PID_0E53`.
- Не привязана к конкретному номеру COM-порта.
- Пишет текущий статус в текстовые файлы рядом с программой.
- Показывает `BUSY`, если INZONE Hub запущен и занял COM-порт.

## Поддерживаемые устройства

Проверено на:

- Sony INZONE H9

Вероятно, также работает с:

- Sony INZONE H7

Оба устройства определяются как:

`VID_054C&PID_0E53`

## Ограничение

INZONE Hub и InzoneH9Tray используют один и тот же COM-интерфейс устройства.  
Если INZONE Hub запущен, он занимает COM-порт, и InzoneH9Tray не может прочитать заряд. В этом случае иконка показывает:

`BUSY`

Для постоянного отображения заряда INZONE Hub необходимо закрыть, включая значок в трее.

## Установка готовой версии

Скачайте InzoneH9Tray.exe из раздела Releases.  
Запустите файл.  
Значок появится в системном трее Windows.  
Если Windows скрыла значок, нажмите стрелку ^ в трее и перетащите его на видимую часть панели.  

## Автозапуск вместе с Windows  

Нажмите Win + R.  
Введите:
`shell:startup`  
Поместите в открывшуюся папку ярлык на InzoneH9Tray.exe.  

## Сборка из исходного кода

Установите зависимости:

`py -m pip install --upgrade pyserial pystray pillow pyinstaller`

Соберите exe:

`py -m PyInstaller --onefile --noconsole --clean --name InzoneH9Tray --hidden-import=pystray._win32 inzone_tray.py`

Готовый файл будет находиться в папке:

`dist\InzoneH9Tray.exe`

## Файлы статуса

Программа создаёт рядом с собой файлы:

`inzone_battery.txt`  
`inzone_battery_status.txt`  
`inzone_tray_error.log`

Они нужны для диагностики и возможной интеграции с другими виджетами.

### Статусы иконки

**70**    — текущий заряд  
**20**    — низкий заряд  
**BUSY**  — COM-порт занят INZONE Hub  
**NO**    — устройство не найдено  
**?**     — ошибка чтения

## Лицензия

Проект распространяется без гарантий. Используйте на свой риск.
