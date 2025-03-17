#!/usr/bin/env python3
import curses

class SimpleNeovimClone:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.text = [""]
        self.cursor_x = 0
        self.cursor_y = 0
        self.mode = 'NORMAL'  # Start in NORMAL mode
        self.filename = 'newfile.txt'
        self.running = True
        self.command = ""
        self.scroll_x = 0
        self.scroll_y = 0
        self.search_query = ""
        self.search_results = []
        self.init_curses()
        self.run()

    def init_curses(self):
        curses.curs_set(1)
        self.stdscr.keypad(True)
        self.stdscr.clear()
        self.stdscr.refresh()

    def draw(self):
        self.stdscr.clear()
        height, width = self.stdscr.getmaxyx()
        line_number_width = len(str(len(self.text))) + 2
        
        for idx, line in enumerate(self.text[self.scroll_y:self.scroll_y + height - 2]):
            line_number = f"{self.scroll_y + idx + 1:>{line_number_width}} "
            self.stdscr.addstr(idx, 0, line_number, curses.A_DIM)
            self.stdscr.addstr(idx, line_number_width + 1, line[self.scroll_x:self.scroll_x + width - line_number_width - 1])
        
        cursor_y = min(self.cursor_y - self.scroll_y, height - 2)
        cursor_x = min(self.cursor_x - self.scroll_x + line_number_width, width - 2) + 1
        
        if self.mode == 'COMMAND':
            status_bar = f":{self.command[1:]}"
        elif self.mode == 'SEARCH':
            status_bar = f"/{self.search_query}"
        else:
            status_bar = f"-- {self.mode} -- | {self.filename} | {self.cursor_y + 1}:{self.cursor_x + 1}"
        
        self.stdscr.addstr(height - 1, 0, status_bar[:width - 1], curses.A_REVERSE)
        self.stdscr.move(cursor_y, cursor_x)
        self.stdscr.refresh()

    def process_input(self, key):
        height, width = self.stdscr.getmaxyx()
        max_y = len(self.text) - 1
        max_x = len(self.text[self.cursor_y]) if self.cursor_y < len(self.text) else 0
        
        if self.mode == 'NORMAL':
            if key == ord('i'):
                self.mode = 'INSERT'
            elif key == ord(':'):
                self.mode = 'COMMAND'
                self.command = ":"
            elif key == ord('/'):
                self.mode = 'SEARCH'
                self.search_query = ""
                self.search_results = []
            elif key == ord('h'):
                self.cursor_x = max(0, self.cursor_x - 1)
            elif key == ord('l'):
                self.cursor_x = min(max_x, self.cursor_x + 1)
            elif key == ord('j'):
                self.cursor_y = min(max_y, self.cursor_y + 1)
            elif key == ord('k'):
                self.cursor_y = max(0, self.cursor_y - 1)
        elif self.mode == 'INSERT':
            if key == 27:  # ESC key
                self.mode = 'NORMAL'
            elif key == curses.KEY_BACKSPACE or key == 127:
                if self.cursor_x > 0:
                    self.text[self.cursor_y] = self.text[self.cursor_y][:self.cursor_x-1] + self.text[self.cursor_y][self.cursor_x:]
                    self.cursor_x -= 1
                elif self.cursor_y > 0:
                    prev_line_length = len(self.text[self.cursor_y - 1])
                    self.text[self.cursor_y - 1] += self.text[self.cursor_y]
                    del self.text[self.cursor_y]
                    self.cursor_y -= 1
                    self.cursor_x = prev_line_length
            elif key == ord('\n'):
                self.text.insert(self.cursor_y + 1, self.text[self.cursor_y][self.cursor_x:])
                self.text[self.cursor_y] = self.text[self.cursor_y][:self.cursor_x]
                self.cursor_y += 1
                self.cursor_x = 0
            else:
                if self.cursor_y >= len(self.text):
                    self.text.append("")
                self.text[self.cursor_y] = self.text[self.cursor_y][:self.cursor_x] + chr(key) + self.text[self.cursor_y][self.cursor_x:]
                self.cursor_x += 1
        elif self.mode == 'COMMAND':
            if key == 27:  # ESC key
                self.mode = 'NORMAL'
                self.command = ""
            elif key == 10:  # Enter key
                if self.command == ':w':
                    self.save_file()
                elif self.command == ':q':
                    self.running = False
                self.mode = 'NORMAL'
                self.command = ""
            elif key == 127 or key == curses.KEY_BACKSPACE:
                if len(self.command) > 1:
                    self.command = self.command[:-1]
                else:
                    pass
            else:
                self.command += chr(key)
        elif self.mode == 'SEARCH':
            if key == 27:  # ESC key
                self.mode = 'NORMAL'
            elif key == 10:  # Enter key
                self.perform_search()
                self.mode = 'NORMAL'
            elif key == 127 or key == curses.KEY_BACKSPACE:
                if len(self.search_query) > 0:
                    self.search_query = self.search_query[:-1]
            else:
                self.search_query += chr(key)
        
        self.cursor_x = min(len(self.text[self.cursor_y]), self.cursor_x)
        self.scroll_adjust(height, width)

    def perform_search(self):
        self.search_results = []
        for i, line in enumerate(self.text):
            if self.search_query in line:
                self.search_results.append(i)
        if self.search_results:
            self.cursor_y = self.search_results[0]
            self.cursor_x = self.text[self.cursor_y].find(self.search_query)

    def scroll_adjust(self, height, width):
        if self.cursor_y < self.scroll_y:
            self.scroll_y = self.cursor_y
        elif self.cursor_y >= self.scroll_y + height - 2:
            self.scroll_y = self.cursor_y - height + 3
        
        if self.cursor_x < self.scroll_x:
            self.scroll_x = self.cursor_x
        elif self.cursor_x >= self.scroll_x + width - 5:
            self.scroll_x = self.cursor_x - width + 6

    def save_file(self):
        with open(self.filename, 'w') as f:
            f.write("\n".join(self.text))

    def run(self):
        while self.running:
            self.draw()
            key = self.stdscr.getch()
            self.process_input(key)

if __name__ == "__main__":
    curses.wrapper(SimpleNeovimClone)