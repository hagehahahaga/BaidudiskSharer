import itertools
import json
import time
import requests
import keyboard
import pyperclip
import win32api
import win32gui
import os

usable = ('netdisksharer', 'baidunetdisk', 'quarkclouddrive')
name_dict = {
    'baidunetdisk': '百度网盘',
    'quarkclouddrive': '夸克网盘'
}


class NetDiskAPIError(Exception):
    brand: str

    def __init__(self, message: str, method):
        super().__init__(message)
        self.method = method

    def error_show(self, brand: str):
        self.brand = brand
        print(f'Error on {self.brand}: {self.method.__name__}. ', end='')
        print(self)
        self.method(self)

    def invalid_user(self):
        config[self.brand] = input(f'Enter the cookie of the website {self.brand}:\n')

    def unknown(self):
        input('Press enter to retry.')


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


class NetDir:
    _list: list = None

    def __init__(self, brand: str, object: dict = None, is_parent: bool = False) -> None:
        """
        :param brand: 所属网盘品牌
        :param object: 字典对象
        :param is_parent: 是否为网盘根目录
        """
        self.is_parent = is_parent

        assert brand in usable, f'The brand {brand} is not supported'
        self.brand = brand

        if brand == 'netdisksharer':
            root_dict = {
                'baidunetdisk': {
                    'path': '/',
                    'server_filename': '百度网盘'
                },
                'quarkclouddrive': {
                    'fid': 0,
                    'file_name': '夸克网盘'
                }
            }
            self._list = list(
                map(
                    lambda a: NetDir(a, root_dict[a], is_parent=True),
                    root_dict
                )
            )
            return

        id_dict = {
            'baidunetdisk': 'fs_id',
            'quarkclouddrive': 'fid'
        }
        self.id = object.get(id_dict[self.brand])

        path_dict = {
            'baidunetdisk': 'path',
            'quarkclouddrive': None
        }
        self.path = object.get(path_dict[self.brand])

        file_name_dict = {
            'baidunetdisk': 'server_filename',
            'quarkclouddrive': 'file_name'
        }
        self.name = object.get(file_name_dict[self.brand])

    def get_list(self) -> list:
        if self._list:
            return self._list

        url_dict = {
            'baidunetdisk': 'https://pan.baidu.com/api/list',
            'quarkclouddrive': 'https://drive-pc.quark.cn/1/clouddrive/file/sort'
        }
        params_dict = {
            'baidunetdisk': {
                'dir': self.path
            },
            'quarkclouddrive': {
                'pr': 'ucpro',
                'fr': 'pc',
                'pdir_fid': self.id
            }
        }
        object_list = url_request(
            url_dict[self.brand],
            params_dict[self.brand],
            self.brand
        )

        path = {
            'baidunetdisk': ['list'],
            'quarkclouddrive': ['data', 'list']
        }[self.brand]
        for step in path:
            object_list = object_list[step]

        self._list = list(
            map(
                lambda a: (
                    NetDir
                    if a[
                        {
                            'baidunetdisk': 'isdir',
                            'quarkclouddrive': 'dir'
                        }[self.brand]
                    ]
                    else NetFile
                )(self.brand, a),
                object_list
            )
        )
        return self._list


class NetFile(NetDir):
    def get_list(self) -> None:
        print('It is not a dir!')
        time.sleep(ui_sleep_time)


def url_request(url: str, params: dict, brand: str, mode: str = 'get', json_data: dict = None) -> dict:
    assert mode in ('get', 'post'), f'{mode.capitalize()} is not supported'
    while True:
        response = eval(f'requests.{mode}')(
            url,
            params=params,
            headers={
                'Cookie': config.get(brand)
            },
            json=json_data
        )
        if response.status_code != 200:
            print(f'Error: {response.status_code}. Press enter to retry.')
            continue
        response = json.loads(response.text)

        error_handle_dict = {
            'baidunetdisk': {
                'status_code_path': ['errno'],
                0: 'pass',
                -6: NetDiskAPIError.invalid_user
            },
            'quarkclouddrive': {
                'status_code_path': ['code'],
                0: 'pass',
                31001: NetDiskAPIError.invalid_user
            }
        }

        error_code = response
        for steps in error_handle_dict[brand]['status_code_path']:
            error_code = error_code[steps]

        error_message_dict = {
            NetDiskAPIError.invalid_user: f'Try to get the cookie of {name_dict[brand]} by logging in again.',
            NetDiskAPIError.unknown: 'Maybe try again will work?'
        }

        try:
            if (error := error_handle_dict[brand][error_code]) != 'pass':
                raise NetDiskAPIError(error_message_dict[error], error)
        except KeyError:
            NetDiskAPIError(f'Maybe try again will work?', NetDiskAPIError.unknown).error_show(brand)
        except NetDiskAPIError as error:
            error.error_show(brand)
            continue
        else:
            time.sleep(ui_sleep_time)

        return response


def show(dir_to_show: NetDir) -> set[NetDir, NetFile]:
    def flush() -> None:
        print(
            '\n\n---------------------------------\n\n' +
            '\n'.join(
                map(
                    lambda a: (
                            (
                                (
                                    '8' if pointer == object_list.index(a) else '√'
                                )
                                if a in return_objects else
                                (
                                    'o' if pointer == object_list.index(a) else ' '
                                )
                            ) +
                            ' ' +
                            a.name +
                            ' - ' +
                            ('DIR' if type(a) == NetDir else 'FIL')
                    ),
                    object_list
                )
            ),
            '\nPress up/down to choose\n'
            '      s          select\n'
            '      a          select all\n'
            '      enter      go into\n'
            f'      esc        {"share" if dir_to_show.brand == "netdisksharer" else "go back"}'
        )

    object_list: [NetDir, NetFile] = dir_to_show.get_list()
    pointer = 0
    return_objects = set()
    list_len = len(object_list)
    fls = True
    while True:
        if fls:
            flush()
        fls = True
        match get_keyboard():
            case 'up':
                if pointer > 0:
                    pointer -= 1
            case 'down':
                if pointer < list_len - 1:
                    pointer += 1
            case 's':
                got_object = object_list[pointer]
                if got_object.is_parent:
                    print('Root is not selectable.')
                    time.sleep(ui_sleep_time)
                    continue

                if got_object in return_objects:
                    return_objects.remove(got_object)
                    continue
                return_objects.add(got_object)
            case 'a':
                if not (object_set := set(object_list)) - return_objects:
                    return_objects -= object_set
                    continue
                return_objects.update(object_set)
            case 'enter':
                pointed_object = object_list[pointer]
                if not pointed_object.get_list():
                    print('It is empty.')
                    time.sleep(ui_sleep_time)
                    continue
                return_objects.update(show(pointed_object))
            case 'esc':
                return return_objects
            case _:
                fls = False


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


def share(objects_grouped: dict[str: set[NetDir | NetFile]], password: str) -> set[str]:
    assert len(password) == 4, 'Error: the length of the password must be 4'
    assert password.isalnum(), 'Error: the allowed are alphabets and numbers'
    return_set: set[str] = set()

    for key in objects_grouped:
        match key:
            case 'quarkclouddrive':
                task_id = url_request(
                    'https://drive-pc.quark.cn/1/clouddrive/share',
                    {'pr': 'ucpro', 'fr': 'pc'},
                    'quarkclouddrive',
                    mode='post',
                    json_data={
                        'expired_type': 1,
                        'fid_list': list(
                            map(
                                lambda a: a.id,
                                objects_grouped[key]
                            )
                        ),
                        'passcode': password,
                        'url_type': 2
                    }
                )['data']['task_id']

                retry_index = 0
                while True:
                    share_id = url_request(
                        'https://drive-pc.quark.cn/1/clouddrive/task',
                        {
                            'pr': 'ucpro',
                            'fr': 'pc',
                            'task_id': task_id,
                            'retry_index': retry_index
                        },
                        'quarkclouddrive'
                    )
                    retry_index += 1
                    if share_id := share_id['data'].get('share_id', share_id):
                        break

                return_set.add(
                    url_request(
                        'https://drive-pc.quark.cn/1/clouddrive/share/password',
                        {
                            'pr': 'ucpro',
                            'fr': 'pc'
                        },
                        'quarkclouddrive',
                        mode='post',
                        json_data={
                            'share_id': share_id
                        }
                    )['data']['share_url']
                )
            case _:
                dict = {
                    'baidunetdisk': {
                        'url': 'https://pan.baidu.com/share/set',
                        'params': {
                            'schannel': 4,
                            'fid_list': str(
                                list(
                                    map(
                                        lambda a: a.id,
                                        objects_grouped[key]
                                    )
                                )
                            ),
                            'pwd': password
                        }
                    }
                }

                return_set.add(
                    url_request(
                        dict[key]['url'],
                        dict[key]['params'],
                        key
                    )['link']
                )

    return return_set


def __main() -> None:
    def input(print_str: str = '') -> str:
        print(print_str)
        return_str = ''
        while True:
            if len(keyboard_input := get_keyboard()) == 1:
                return_str += keyboard_input
            match keyboard_input:
                case 'enter':
                    return return_str
                case 'backspace':
                    return_str = return_str[:-1]
            print(return_str)

    share_dict = dict(
        map(
            lambda a: (a[0], list(a[1])),
            itertools.groupby(
                sorted(
                    show(
                        NetDir(
                            'netdisksharer',
                        )
                    ),
                    key=lambda a: a.brand
                ),
                key=lambda a: a.brand
            )
        )
    )

    if not share_dict:
        exit()

    share_file_ids = set()
    password = ''
    while True:
        try:
            password = input('Input the password(Length: 4. Only nums and alphabets).')
            share_file_ids = share(
                share_dict,
                password
            )
        except AssertionError as error:
            print(error)
            continue
        break

    output = '\n'.join(share_file_ids) + f'\nPassword: {password}'
    print(output)
    pyperclip.copy(output)
    print('Copied to the clipboard.')

    print('Press esc to exit.')
    while get_keyboard() != 'esc':
        print('Press esc to exit.')


if __name__ == '__main__':
    win32api.SetConsoleTitle('BaidudiskSharer')
    ui_sleep_time = 0.5
    with Config('config.json') as config:
        __main()
