import pyperclip
import win32api

import Base
import NetDisks


class __Main(NetDisks.BaseNetDisk):
    def main(self):
        def input(print_str: str = '') -> str:
            print(print_str)
            return_str = ''
            while True:
                if len(keyboard_input := Base.get_keyboard()) == 1:
                    return_str += keyboard_input
                match keyboard_input:
                    case 'enter':
                        return return_str
                    case 'backspace':
                        return_str = return_str[:-1]
                print(return_str)

        disks: set[NetDisks.BaseNetDiskRoot] = self.show()
        for disk in disks:
            if disk.share_items:
                break
        else:
            exit()

        password = ''
        share_urls = []
        while True:
            try:
                password = input('Input the password(Length: 4. Only nums and alphabets).')
                share_urls = list(
                    map(
                        lambda a: a.share(password),
                        disks
                    )
                )
            except AssertionError as error:
                print(error)
                continue
            break

        output = '\n'.join(share_urls) + f'\nPassword: {password}'
        print(output)
        pyperclip.copy(output)
        print('Copied to the clipboard.')

        print('Press esc to exit.')
        while Base.get_keyboard() != 'esc':
            print('Press esc to exit.')

    def get_items(self) -> set:
        return {
            NetDisks.BaiduNetDiskRoot(),
            NetDisks.QuarkCloudDriveRoot()
        }


if __name__ == '__main__':
    win32api.SetConsoleTitle('NetDiskSharer')
    __Main(Base.Tree()).main()
