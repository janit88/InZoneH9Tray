import time
import threading
import traceback
from dataclasses import dataclass
from datetime import datetime

import serial
from serial.tools import list_ports

import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw, ImageFont


VID = "054C"
PID = "0E53"

POLL_INTERVAL_SECONDS = 60

INIT_1 = bytes.fromhex("01 00 FC 08 96 C3 21 01 01 01 00 7D")
INIT_2 = bytes.fromhex("01 00 FC 08 96 C3 41 02 01 01 00 9E")
BATTERY_QUERY = bytes.fromhex("01 00 FC 08 96 C3 41 04 01 01 00 A0")

BATTERY_SIGNATURE = bytes.fromhex("04 FF 0B 00 96 C3 14 04")


@dataclass
class BatteryState:
    battery: int | None = None
    charging: bool | None = None
    status: str = "init"
    port: str | None = None
    last_update: str | None = None
    error: str | None = None


state = BatteryState()
stop_event = threading.Event()
tray_icon: pystray.Icon | None = None


def find_inzone_port() -> str | None:
    """
    Ищем COM-порт INZONE H9/H7.

    На твоём ПК это было:
    USB\\VID_054C&PID_0E53&MI_06...
    COM3

    Но на другом ПК COM-порт может быть COM4, COM5, COM12 и т.д.
    Поэтому ищем по VID/PID, а не по номеру COM.
    """

    candidates = []

    for port in list_ports.comports():
        text = f"{port.device} {port.description} {port.hwid}".upper()

        # Вариант формата pyserial:
        # USB VID:PID=054C:0E53
        if f"VID:PID={VID}:{PID}" in text:
            candidates.append(port)
            continue

        # Вариант формата Windows PNPDeviceID:
        # USB\VID_054C&PID_0E53&MI_06...
        if f"VID_{VID}" in text and f"PID_{PID}" in text:
            candidates.append(port)
            continue

        # Запасной мягкий вариант
        if VID in text and PID in text:
            candidates.append(port)
            continue

    # Сначала предпочитаем именно интерфейс MI_06,
    # потому что у тебя COM-порт был на MI_06.
    for port in candidates:
        text = f"{port.device} {port.description} {port.hwid}".upper()

        if "MI_06" in text:
            return port.device

    # Если MI_06 не отображается, берём первый найденный порт с VID/PID.
    if candidates:
        return candidates[0].device

    return None


def read_for(ser: serial.Serial, seconds: float = 0.8) -> bytes:
    data = b""
    end = time.time() + seconds

    while time.time() < end:
        waiting = ser.in_waiting

        if waiting:
            data += ser.read(waiting)
        else:
            chunk = ser.read(1)

            if chunk:
                data += chunk
            else:
                time.sleep(0.02)

    return data


def send_and_read(ser: serial.Serial, cmd: bytes, pause: float = 0.25) -> bytes:
    ser.write(cmd)
    time.sleep(pause)
    return read_for(ser)


def find_battery_frame(data: bytes) -> bytes | None:
    for i in range(0, max(0, len(data) - 13)):
        frame = data[i:i + 14]

        if len(frame) == 14 and frame.startswith(BATTERY_SIGNATURE):
            return frame

    return None


def read_inzone_battery() -> BatteryState:
    port = find_inzone_port()

    if not port:
        return BatteryState(
            status="not_found",
            error="INZONE COM-порт не найден"
        )

    try:
        with serial.Serial(
            port=port,
            baudrate=115200,
            bytesize=8,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=0.2,
            write_timeout=10,
            xonxoff=False,
            rtscts=False,
            dsrdtr=False
        ) as ser:
            ser.dtr = True
            ser.rts = True

            time.sleep(0.5)

            ser.reset_input_buffer()
            ser.reset_output_buffer()

            send_and_read(ser, INIT_1)
            send_and_read(ser, INIT_2)

            rx = send_and_read(ser, BATTERY_QUERY)

            frame = find_battery_frame(rx)

            if not frame:
                return BatteryState(
                    status="bad_response",
                    port=port,
                    error="Кадр батареи не найден"
                )

            charging_byte = frame[11]
            battery_byte = frame[12]

            return BatteryState(
                battery=battery_byte,
                charging=(charging_byte == 1),
                status="ok",
                port=port,
                last_update=datetime.now().strftime("%H:%M:%S")
            )

    except PermissionError:
        return BatteryState(
            status="busy",
            port=port,
            error="COM-порт занят. Скорее всего открыт INZONE Hub"
        )

    except serial.SerialException as e:
        message = str(e)

        if (
            "PermissionError" in message
            or "Access is denied" in message
            or "Отказано в доступе" in message
        ):
            return BatteryState(
                status="busy",
                port=port,
                error="COM-порт занят. Скорее всего открыт INZONE Hub"
            )

        return BatteryState(
            status="serial_error",
            port=port,
            error=message
        )

    except Exception as e:
        return BatteryState(
            status="error",
            port=port,
            error=f"{type(e).__name__}: {e}"
        )


def load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        r"C:\Windows\Fonts\arialbd.ttf",
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\segoeuib.ttf",
        r"C:\Windows\Fonts\segoeui.ttf",
    ]

    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass

    return ImageFont.load_default()


def make_icon_image(current_state: BatteryState) -> Image.Image:
    size = 64
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    if current_state.status == "ok":
        if current_state.battery is not None and current_state.battery <= 20:
            bg = (150, 40, 40, 255)
        elif current_state.charging:
            bg = (60, 110, 60, 255)
        else:
            bg = (90, 35, 150, 255)
    elif current_state.status == "busy":
        bg = (120, 90, 30, 255)
    else:
        bg = (80, 80, 80, 255)

    draw.rounded_rectangle((2, 2, 62, 62), radius=12, fill=bg)

    if current_state.status == "ok" and current_state.battery is not None:
        text = str(current_state.battery)

        font_size = 25 if current_state.battery >= 100 else 31
        font = load_font(font_size)

        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        x = (size - text_w) // 2
        y = (size - text_h) // 2 - 3

        draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))

        if current_state.charging:
            small_font = load_font(16)
            draw.text((47, 43), "⚡", font=small_font, fill=(255, 255, 255, 255))

    elif current_state.status == "busy":
        font = load_font(16)
        text = "BUSY"
        bbox = draw.textbbox((0, 0), text, font=font)

        draw.text(
            ((size - (bbox[2] - bbox[0])) // 2, (size - (bbox[3] - bbox[1])) // 2),
            text,
            font=font,
            fill=(255, 255, 255, 255)
        )

    elif current_state.status == "not_found":
        font = load_font(18)
        text = "NO"
        bbox = draw.textbbox((0, 0), text, font=font)

        draw.text(
            ((size - (bbox[2] - bbox[0])) // 2, (size - (bbox[3] - bbox[1])) // 2),
            text,
            font=font,
            fill=(255, 255, 255, 255)
        )

    else:
        font = load_font(22)
        text = "?"
        bbox = draw.textbbox((0, 0), text, font=font)

        draw.text(
            ((size - (bbox[2] - bbox[0])) // 2, (size - (bbox[3] - bbox[1])) // 2 - 2),
            text,
            font=font,
            fill=(255, 255, 255, 255)
        )

    return image


def make_title(current_state: BatteryState) -> str:
    if current_state.status == "ok":
        charging_text = " / charging" if current_state.charging else ""
        port_text = f" / {current_state.port}" if current_state.port else ""

        return f"INZONE H9: {current_state.battery}%{charging_text}{port_text} | {current_state.last_update}"

    if current_state.status == "busy":
        return f"INZONE H9: COM-порт занят INZONE Hub ({current_state.port})"

    if current_state.status == "not_found":
        return "INZONE H9: устройство не найдено"

    return f"INZONE H9: ошибка — {current_state.error}"


def save_status_file(current_state: BatteryState) -> None:
    try:
        with open("inzone_battery_status.txt", "w", encoding="utf-8") as f:
            f.write(make_title(current_state))

        if current_state.battery is not None:
            with open("inzone_battery.txt", "w", encoding="utf-8") as f:
                f.write(str(current_state.battery))

    except Exception:
        pass


def update_tray_icon(current_state: BatteryState) -> None:
    global tray_icon

    if tray_icon is None:
        return

    tray_icon.icon = make_icon_image(current_state)
    tray_icon.title = make_title(current_state)


def refresh_once() -> None:
    global state

    new_state = read_inzone_battery()
    state = new_state

    save_status_file(new_state)
    update_tray_icon(new_state)


def worker_loop() -> None:
    while not stop_event.is_set():
        try:
            refresh_once()
        except Exception:
            with open("inzone_tray_error.log", "a", encoding="utf-8") as f:
                f.write(traceback.format_exc())
                f.write("\n")

        stop_event.wait(POLL_INTERVAL_SECONDS)


def on_refresh(icon, menu_item):
    threading.Thread(target=refresh_once, daemon=True).start()


def on_exit(icon, menu_item):
    stop_event.set()
    icon.stop()


def get_menu_text():
    return make_title(state)


def main():
    global tray_icon

    initial_state = BatteryState(status="init", error="Инициализация")

    tray_icon = pystray.Icon(
        "INZONE H9 Battery",
        make_icon_image(initial_state),
        "INZONE H9: запуск...",
        menu=pystray.Menu(
            item(lambda text: get_menu_text(), None, enabled=False),
            item("Обновить сейчас", on_refresh),
            item("Выход", on_exit)
        )
    )

    thread = threading.Thread(target=worker_loop, daemon=True)
    thread.start()

    tray_icon.run()


if __name__ == "__main__":
    main()