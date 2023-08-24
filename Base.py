import Config
import keyboard
import win32api
import win32gui
import time


class Tree(dict):
    def get_by_path(self, path: list, els=None):
        if els is None:
            els = {}

        def recursion(path):
            nonlocal item_to_return
            if not path:
                return item_to_return
            try:
                item_to_return = item_to_return[path.pop(0)]
            except (KeyError, IndexError):
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
    brand: str

    def __init__(self, message: str, method):
        super().__init__(message)
        self.method = method

    def error_show(self, brand: str):
        self.brand = brand
        print(f'Error on {self.brand}: {self.method.__name__}.', self)
        self.method(self)

    def invalid_user(self):
        with Config.Config('config.json') as config:
            config[self.brand] = input(f'Enter the cookie of the website {self.brand}:\n')

    def unknown(self):
        input('Press enter to retry.')


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
