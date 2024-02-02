import keyboard
import win32api
import win32gui
import time
import os
import json
from typing import Any


class Tree(dict):
    def get_by_path(self, path: list, els='dict') -> Any:
        if els == 'dict':
            els = {}

        def recursion(path):
            nonlocal item_to_return
            if not path:
                return item_to_return
            try:
                item_to_return = item_to_return[path.pop(0)]
            except (KeyError, IndexError, TypeError):
                item_to_return = els
            return recursion(path)

        item_to_return = self
        path = path.copy()
        return recursion(path)

    def set_by_path(self, path: list, value):
        if not path:
            return value
        step = path.pop(0)
        self[step] = self.set_by_path(path, value)
        return self


class NetDiskAPIError(Exception):
    object = None

    def __init__(self, message: str, method):
        super().__init__(message)
        self.method = method

    def error_show(self, object):
        self.object = object
        print(f'Error on {self.object.BRAND}: {self.method.__name__}.', self)
        self.method(self)

    def invalid_user(self):
        with Config('config.json') as config:
            key = list(config[self.object.BRAND]["headers"].keys())[0]
            config[self.object.BRAND]["headers"][key] = input(f'Enter the cookie of the website {self.object.BRAND}:\n')
            match self.object.BRAND:
                case 'ALiYunDrive':
                    if not config[self.object.BRAND].get("drive_id"):
                        config[self.object.BRAND]["drive_id"] = input(
                            f'Enter the drive id of the website {self.object}:\n')

    def shared_too_much(self):
        self.object.retry_times = -1

    def unknown(self):
        if input('Press enter to retry, else to exit.'):
            exit()


class Config(dict):
    """
    You can use it like a dict naturally by with it as an object
    """

    def __init__(self, file: str) -> None:
        self.file = file

        if not os.path.exists(self.file):
            super().__init__()
            return

        with open(self.file, mode='r') as file:
            super().__init__(json.load(file))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        with open(self.file, mode='w') as file:
            json.dump(self, file, indent=2)


def get_keyboard() -> str:
    while True:
        key = keyboard.read_key()

        focus_window_handle = win32gui.GetForegroundWindow()
        original_window_title = win32api.GetConsoleTitle()
        win32api.SetConsoleTitle(original_window_title + '*')
        time.sleep(0.1)
        console_window_handle = win32gui.FindWindow(None, original_window_title + '*')
        win32api.SetConsoleTitle(original_window_title)

        # break  # TODO: for debugging, #this before posting
        if console_window_handle == focus_window_handle:
            break

    return key


def show_message(message):
    print(message)
    time.sleep(ui_sleep_time)


ui_sleep_time = 1
