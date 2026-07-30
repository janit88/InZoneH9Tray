# InzoneH9Tray

**English** | [Русский](README.ru.md)

## Sony INZONE H9 / H7 Battery Tray Indicator for Windows

InzoneH9Tray is a lightweight Windows system tray application that displays the battery level and charging status of Sony INZONE H9 and INZONE H7 headsets.

The application reads the battery status directly through the USB/COM interface of the Sony wireless dongle and does not require the INZONE Hub window to remain open.

## Features

* Displays the headset battery level in the Windows system tray.
* Displays the charging status.
* Automatically detects the COM port using `VID_054C&PID_0E53`.
* Does not depend on a fixed COM port number.
* Writes the current status to text files next to the application.
* Displays `BUSY` when INZONE Hub is running and has occupied the COM port.

## Supported Devices

Tested with:

* Sony INZONE H9

Expected to also work with:

* Sony INZONE H7

Both devices use the following hardware identifier:

```text
VID_054C&PID_0E53
```

Support for the Sony INZONE H7 has not yet been confirmed by direct testing.

## Limitation

INZONE Hub and InzoneH9Tray use the same COM interface of the wireless dongle.

When INZONE Hub is running, it occupies the COM port and InzoneH9Tray cannot read the battery level. In this case, the tray icon displays:

```text
BUSY
```

For continuous battery monitoring, close INZONE Hub completely, including its system tray icon.

## Installing the Prebuilt Version

1. Download `InzoneH9Tray.exe` from the repository's **Releases** page.
2. Run the downloaded file.
3. The application icon will appear in the Windows system tray.
4. If Windows hides the icon, click the `^` arrow and drag the icon to the visible part of the tray.

## Starting with Windows

1. Press `Win + R`.
2. Enter:

```text
shell:startup
```

3. Place a shortcut to `InzoneH9Tray.exe` in the opened folder.

## Building from Source

Install the required dependencies:

```powershell
py -m pip install --upgrade pyserial pystray pillow pyinstaller
```

Build the executable:

```powershell
py -m PyInstaller --onefile --noconsole --clean --name InzoneH9Tray --hidden-import=pystray._win32 inzone_tray.py
```

The resulting executable will be located at:

```text
dist\InzoneH9Tray.exe
```

## Status Files

The application creates the following files next to the executable:

```text
inzone_battery.txt
inzone_battery_status.txt
inzone_tray_error.log
```

These files can be used for diagnostics and integration with other applications or desktop widgets.

## Tray Icon Statuses

| Icon   | Meaning                            |
| ------ | ---------------------------------- |
| `70`   | Current battery level              |
| `20`   | Low battery level                  |
| `BUSY` | COM port is occupied by INZONE Hub |
| `NO`   | Headset or dongle was not found    |
| `?`    | Battery reading error              |

## License

This project is licensed under the [MIT License](LICENSE).