
import os
import sys
from select import select
if os.name == 'nt':
    import msvcrt

class ScreenManager:
    def __init__(self):
        self.last_line_count = 0

    def clear_screen(self):
        if os.name == 'nt':
            os.system('cls')
        else:
            os.system('clear')

    def clear_last_output(self):
        if os.name == 'nt':
            self.clear_screen()
        else:
            for _ in range(self.last_line_count):
                sys.stdout.write('\033[F')
                sys.stdout.write('\033[K')

    def check_for_quit(self):
        if os.name == 'nt':
            if msvcrt.kbhit():
                return msvcrt.getch().decode('utf-8').lower() == 'q'
        else:
            rlist, _, _ = select([sys.stdin], [], [], 0)
            if rlist:
                return sys.stdin.read(1).lower() == 'q'
        return False
