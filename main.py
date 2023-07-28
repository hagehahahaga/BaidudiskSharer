import json
import time

import configobj
import keyboard
import pyperclip
import requests
import win32api
import win32gui


def _main() -> None:
    global input
    if not config.get('cookie'):
        config['cookie'] = input("Enter your Cookie of the API.")
        config.write()

    def input(print_str: str = '') -> str:
        print(print_str)
        return_str = ''
        while True:
            match get_keyboard():
                case 'enter':
                    return return_str
                case 'backspace':
                    return_str = return_str[:-1]
                case _ as entered_str:
                    return_str += entered_str
            print(return_str)

    share_list = print_list(get_list(), root=True)
    while True:
        try:
            password = input('Input the password(Length: 4. Only nums and alphabets).')
            share_file_ids = share(
                share_list,
                password,
                bool(input('Encrypt?(Enter for false, else for true.)'))
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


def get_list(path: str = '/') -> list[dict]:
    sep = '%2F'
    url = f'https://pan.baidu.com/api/list?dir={sep.join(path.split("/"))}'

    response = url_get(url)

    file_list_dict: dict = json.loads(
        response.text
    )

    errno_handle(file_list_dict['errno'])
    print('Got the list...')

    return file_list_dict['list']


def errno_handle(errno_code: int) -> None:
    match errno_code:
        case 0:
            time.sleep(ui_sleep_time)
        case -6:
            del config['cookie']
            config.write()
            raise Exception('Error: Invalid user. Try to get cookie of the API by logging in again')
        case _ as error_code:
            raise Exception(f'Error: Unknown: {error_code}')


def url_get(url: str) -> requests.Response:
    headers = {
        'Cookie': config['cookie']
    }
    while True:
        response = requests.get(url, headers=headers)
        match response.status_code:
            case 200:
                break
            case _ as error_code:
                with open('error.txt', mode='a') as file:
                    file.write(f'\nError: {error_code}')
                print(f'Error: {error_code}. Press enter to retry.')
    return response


def print_list(list: list[dict], root: bool = False) -> set[int]:
    def flush() -> None:
        print(
            '\n\n---------------------------------\n\n',
            '\n'.join(
                map(
                    lambda a: (
                            (
                                (
                                    '8' if pointer == list.index(a) else '√'
                                )
                                if a['fs_id'] in return_ids else
                                (
                                    'o' if pointer == list.index(a) else ' '
                                )
                            ) +
                            ' ' +
                            a['server_filename'] +
                            ' - ' +
                            ('DIR' if a['isdir'] else 'FIL')
                    ),
                    list
                )
            ),
            f'\n---------------------------------\nPress  up/down  to choose\n       s           select\n       a     '
            f'      select all\n       enter       go into the dir\n       backspace   {"share" if root else "go back"}'
        )

    pointer = 0
    return_ids = set()
    list_len = len(list)
    # 文件(夹)名: sever_filename
    # 分享时用到的id: fs_id
    # 是否是目录: isdir
    # 文件(夹)绝对路径: path
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
                pointer_file_fs_id = list[pointer]['fs_id']
                if pointer_file_fs_id in return_ids:
                    return_ids.remove(pointer_file_fs_id)
                    continue
                return_ids.add(pointer_file_fs_id)
            case 'a':
                list_fs_ids = set(map(lambda a: a['fs_id'], list))
                if len(list) <= len(return_ids) and not list_fs_ids - return_ids:
                    return_ids -= list_fs_ids
                    continue
                return_ids = return_ids | list_fs_ids
            case 'enter':
                pointer_file = list[pointer]
                if not pointer_file['isdir']:
                    print('Its not a dir!')
                    time.sleep(ui_sleep_time)
                    continue
                list_got_entered = get_list(pointer_file['path'].replace('\\', ''))
                if not list_got_entered:
                    print('Its empty!')
                    time.sleep(ui_sleep_time)
                    continue
                return_ids = return_ids | \
                             print_list(
                                 list_got_entered
                             )
            case 'backspace':
                return return_ids
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

        if console_window_handle == focus_window_handle:
            break

    return key


def share(fid_list: set, password: str, encrypt: bool = False) -> set[str]:
    # the length of the password must be 4
    # the allowed are alphabets and numbers
    assert len(password) == 4, 'Error: the length of the password must be 4'
    assert password.isalnum(), 'Error: the allowed are alphabets and numbers'

    return_list = set()

    for fid in fid_list:
        url = f'https://pan.baidu.com/share/set?schannel=4&fid_list=%5B{fid}%5D&pwd={password}'
        response = json.loads(
            url_get(url).text
        )

        errno_handle(response['errno'])

        if encrypt:
            response['link'] = response['link'].split('/')[-1]

        return_list.add(response['link'])

    return return_list


if __name__ == '__main__':
    win32api.SetConsoleTitle('BaidudiskSharer')
    ui_sleep_time = 0.5
    config = configobj.ConfigObj('config.ini', encoding='utf-8')
    _main()
