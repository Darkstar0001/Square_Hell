import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from time import sleep, perf_counter
import csv
from _thread import start_new_thread
from threading import Event


class Levels(tk.Frame):
    __slots__ = ('checkpoint', 'loaded_level', 'y_velocity', 'field', 'run', 'root', 'cycle', 'load_level_button', 'tk',
                 'WIDTH', 'deaths', 'coins_remaining', 'key_binds', 'running', 'player', 'customize_controls_button',
                 'HEIGHT', 'start_button', 'x_velocity', 'TILE_SIZE', '_name', '_w', 'widgetName', 'master', 'children')

    def __init__(self):
        self.root = tk.Tk()
        tk.Frame.__init__(self)
        self.grid()
        self.master.resizable(False, False)
        self.TILE_SIZE = 20
        self.WIDTH = 50 * self.TILE_SIZE  # default 1000
        self.HEIGHT = 35 * self.TILE_SIZE  # default 700
        self.running = False
        self.master.geometry(f"{self.WIDTH}x{self.HEIGHT + 57}")
        self.place(relx=0.5, relwidth=1, anchor='n')
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        ttk.Style().configure("TButton", font='arial 30')

        self.load_level_button = ttk.Button(self, text='Load Level', command=lambda: select_level(
            exit_func=self.load_level, field=self.field, tile_size=self.TILE_SIZE, height=self.HEIGHT, width=self.WIDTH))
        self.load_level_button.grid(row=0, sticky='w')
        self.start_button = ttk.Button(self, text='Start', state='disabled', command=self.start)
        self.start_button.grid(row=0)

        self.customize_controls_button = ttk.Button(self, text='Customize controls', command=lambda:
                                                    self.customize_controls_dialogue(tuple(self.key_binds.values())))
        self.customize_controls_button.grid(row=0, sticky='e')

        self.field = tk.Canvas(self, bg='azure', height=self.HEIGHT)
        self.field.grid(sticky='ews', row=1)

        self.x_velocity = self.y_velocity = 0
        self.key_binds = {'UP': 'w', 'DOWN': 's', 'LEFT': 'a', 'RIGHT': 'd', 'START/PAUSE': 'Return'}
        self.loaded_level = False
        start_new_thread(self.game_loop, ())
        print(self.__dict__)

    def load_level(self, filename: str, index: int, field: tk.Canvas, tile_size: int, height: int, width: int, window=None):
        if (name := load_level(filename=filename, index=index, field=field, tile_size=tile_size,
                               height=height, width=width, window=window, replace=self.loaded_level)[0]):
            self.player = self.field.find_withtag('Player')[0]
            self.field.tag_lower('Coin')
            self.field.tag_lower('Checkpoint')
            self.field.tag_lower('Goal')
            self.checkpoint = self.field.coords(self.player)
            self.coins_remaining = len(self.field.find_withtag('Coin'))
            self.master.title('Level - '+name)
            self.start_button.config(state='normal')
            self.root.bind(f"<{self.key_binds['START/PAUSE']}>", lambda _: self.start() if not self.running else self.stop())
            self.cycle = 0
            self.deaths = 0
            self.loaded_level = True

    def game_loop(self):
        while True:
            self.run = Event()
            self.run.wait()
            while self.running:
                frame_start_time = perf_counter()
                left, top, right, bottom = self.field.coords(self.player)
                x_offset, y_offset = self.wall_collision_check(left+self.x_velocity, top+self.y_velocity,
                                                               right+self.x_velocity, bottom+self.y_velocity)
                self.field.move(self.player, self.x_velocity+x_offset, self.y_velocity+y_offset)
                self.move_traps(self.cycle)
                left, top, right, bottom = self.field.coords(self.player)
                if collision := [self.field.gettags(item)[0] for item in self.field.find_overlapping(
                        left+1, top+1, right-1, bottom-1) if item != self.player]:
                    if 'Trap' in collision or 'V Trap' in collision or 'H Trap' in collision:
                        self.die()
                    elif (self.x_velocity or self.y_velocity) and (deep_collision := [
                        item for item in self.field.find_overlapping(
                            left+self.TILE_SIZE/3, top+self.TILE_SIZE/3, right-self.TILE_SIZE/3, bottom-self.TILE_SIZE/3)
                            if item != self.player]):
                        self.deep_collision(deep_collision)
                if self.cycle == 15:
                    self.cycle = 0
                self.cycle += 1
                if (rest := 0.033333333 - round(perf_counter() - frame_start_time, 7)) < 0:
                    rest = 0
                sleep(rest)

    def wall_collision_check(self, left: int, top: int, right: int, bottom: int) -> tuple:
        """Takes the anticipated position of the player after moving, and checks if it intercepts a wall. If it does,
        returns the x and y offsets required to line up with the wall's edge, which are then used to modify movement."""
        if wall_collision := [self.field.coords(item) for item in
                              self.field.find_overlapping(left + 1, top + 1, right - 1, bottom - 1)
                              if self.field.gettags(item)[0] == 'Wall']:
            return self.wall_collision(wall_collision, left, top, right, bottom)
        return 0, 0

    @staticmethod
    def wall_collision(collision: list, left: int, top: int, right: int, bottom: int) -> tuple:
        """Check collision with walls on all four sides, and determines the offset required to avoid clipping through
        them. Checks to ensure that offset is set in the correct direction by only counting clipping as coming from
        a particular direction if it isn't clipping very far in from that side, and it isn't the result of clipping
        from a horizontal direction for a vertical clip or the reverse."""
        if wall_left := [wall[0] for wall in collision if right - 5 <= wall[0] <= right and not (
                bottom - 5 <= wall[1] <= bottom) and not (top + 5 >= wall[3] >= top)]:
            wall_left = wall_left[0]
        else:
            wall_left = right
        if wall_top := [wall[1] for wall in collision if bottom - 5 <= wall[1] <= bottom and not (
                right - 5 <= wall[0] <= right) and not (left + 5 >= wall[2] >= left)]:
            wall_top = wall_top[0]
        else:
            wall_top = bottom
        if wall_right := [wall[2] for wall in collision if left + 5 >= wall[2] >= left and not (
                bottom - 5 <= wall[1] <= bottom) and not (top + 5 >= wall[3] >= top)]:
            wall_right = wall_right[0]
        else:
            wall_right = left
        if wall_bottom := [wall[3] for wall in collision if top + 5 >= wall[3] >= top and not (
                right - 5 <= wall[0] <= right) and not (left + 5 >= wall[2] >= left)]:
            wall_bottom = wall_bottom[0]
        else:
            wall_bottom = top
        return (wall_left - right) + (wall_right - left), (wall_top - bottom) + (wall_bottom - top)

    def move_traps(self, cycle: int):
        if cycle == 15:
            for vertical_trap in self.field.find_withtag('V Trap'):
                self.field.move(vertical_trap, 0, self.update_trap_direction(vertical_trap))
            for horizontal_trap in self.field.find_withtag('H Trap'):
                self.field.move(horizontal_trap, self.update_trap_direction(horizontal_trap), 0)
        else:
            for vertical_trap in self.field.find_withtag('V Trap'):
                self.field.move(vertical_trap, 0, self.field.gettags(vertical_trap)[2])
            for horizontal_trap in self.field.find_withtag('H Trap'):
                self.field.move(horizontal_trap, self.field.gettags(horizontal_trap)[2], 0)

    def update_trap_direction(self, trap) -> int:
        tags = list(self.field.gettags(trap))
        if int(tags[1]) == 3:
            tags[2] = -1
        elif int(tags[1]) == -3:
            tags[2] = 1
        tags[1] = int(tags[1]) + int(tags[2])
        self.field.itemconfig(trap, tags=tags)
        return int(tags[2])

    def deep_collision(self, collision: list):
        tags_list = [self.field.gettags(object)[0] for object in collision]
        if 'Checkpoint' in tags_list:
            self.set_checkpoint(*self.field.coords(collision[tags_list.index("Checkpoint")]))
        if 'Coin' in tags_list:
            for coin in collision:
                if self.field.gettags(coin)[0] == 'Coin':
                    self.field.itemconfig(coin, tags=['Coin', 'Collected'], state='hidden')
                    self.coins_remaining -= 1
        if 'Goal' in tags_list:
            if self.coins_remaining == 0:
                self.win()

    def set_checkpoint(self, left: int, top: int, right: int, bottom: int):
        self.checkpoint = (left+3, top+3, right-3, bottom-3)
        for coin in self.field.find_withtag('Coin'):
            if self.field.gettags(coin)[1] == 'Collected':
                self.field.delete(coin)

    def start(self):
        self.customize_controls_button.config(state='disabled')
        self.load_level_button.config(state='disabled')
        self.running = True
        self.run.set()
        self.bind_controls()
        self.start_button.config(text='Pause', command=self.stop)

    def stop(self):
        self.unbind_controls()
        self.running = False
        self.customize_controls_button.config(state='normal')
        self.load_level_button.config(state='normal')
        self.start_button.config(text='Start', command=self.start)

    def queue_move(self, x_move=0, y_move=0):
        if x_move:
            self.x_velocity = x_move
        else:  # y_move
            self.y_velocity = y_move

    def queue_stop(self, x_stop=-9, y_stop=-9):
        if x_stop == self.x_velocity:
            self.x_velocity = 0
        elif y_stop == self.y_velocity:
            self.y_velocity = 0

    def die(self):
        for coin in self.field.find_withtag('Coin'):
            if self.field.gettags(coin)[1] == 'Collected':
                self.field.itemconfig(coin, tags=['Coin', ' '], state='normal')
                self.coins_remaining += 1
        self.deaths += 1
        self.field.coords(self.player, *self.checkpoint)

    def win(self):
        self.stop()
        self.start_button.config(state='disabled')
        self.field.create_text(self.WIDTH/2, self.HEIGHT/2, text=f'Victory!\n{self.deaths} deaths', font='arial 40')

    def customize_controls_dialogue(self, bound_keys):
        key_bind_window = tk.Toplevel()
        key_bind_window.title('Customize Key Bindings')
        key_bind_window.resizable(False, False)
        key_bind_window.grab_set()
        ttk.Style().configure("TLabel", font='arial 30')

        ttk.Label(key_bind_window, text='_' * 20).grid(row=0, columnspan=2, pady=(50, 0))
        instructions = ttk.Label(key_bind_window, text='Click a button to bind\nthe key for that action')
        instructions.grid(row=0, columnspan=2, pady=(0, 10))

        button_list = [ttk.Button(key_bind_window, text=dir, command=lambda dir=dir: self.prepare_key_bind(
            dir, button_list, label_dict, instructions, key_bind_window)) for dir in ('UP', 'DOWN', 'LEFT', 'RIGHT', 'START/PAUSE')]
        for row in range(5):
            button_list[row].grid(row=row+1)

        label_dict = {dir: ttk.Label(key_bind_window, text=key)
                      for dir, key in zip(('UP', 'DOWN', 'LEFT', 'RIGHT', 'START/PAUSE'), bound_keys)}
        for row, label in enumerate(tuple(label_dict.values())):
            label.grid(row=row+1, column=1)

    def prepare_key_bind(self, direction: str, buttons: list, labels: dict, instructions: tk.Label, window: tk.Toplevel):
        for button in buttons:
            button.config(state='disabled')
        instructions.config(text=f'Press a key to use\nfor moving {direction}')
        window.bind('<Key>', lambda key: self.bind_custom_key(key.keysym, direction, buttons, labels, instructions, window))

    def bind_custom_key(self, key: str, direction: str, buttons: list, labels: dict, instructions: tk.Label, window: tk.Toplevel):
        window.unbind('<Key>')
        if key not in tuple(self.key_binds.values()):
            self.key_binds[direction] = key
            labels[direction].config(text=key)
        else:
            tk.messagebox.showwarning('Duplicate binding', 'A control is already bound to that key.')
        for button in buttons:
            button.config(state='normal')
        instructions.config(text='Click a button to bind\nthe key for that action')

    def bind_controls(self):
        self.root.bind(f"<{self.key_binds['UP']}>", lambda _: self.queue_move(y_move=-4))
        self.root.bind(f"<{self.key_binds['DOWN']}>", lambda _: self.queue_move(y_move=4))
        self.root.bind(f"<{self.key_binds['LEFT']}>", lambda _: self.queue_move(x_move=-4))
        self.root.bind(f"<{self.key_binds['RIGHT']}>", lambda _: self.queue_move(x_move=4))

        self.root.bind(f"<KeyRelease-{self.key_binds['UP']}>", lambda _: self.queue_stop(y_stop=-4))
        self.root.bind(f"<KeyRelease-{self.key_binds['DOWN']}>", lambda _: self.queue_stop(y_stop=4))
        self.root.bind(f"<KeyRelease-{self.key_binds['LEFT']}>", lambda _: self.queue_stop(x_stop=-4))
        self.root.bind(f"<KeyRelease-{self.key_binds['RIGHT']}>", lambda _: self.queue_stop(x_stop=4))

        self.root.bind(f"<{self.key_binds['START/PAUSE']}>", lambda _: self.start() if not self.running else self.stop())

    def unbind_controls(self):
        for control in tuple(self.key_binds.values()):
            self.root.unbind(control)
            self.root.unbind(f"KeyRelease-{control}")
            

def place_object(event, field: tk.Canvas, active_object: str, tile_size: int, height: int, width: int, properties: str,
                 draw_commands=(
        ('dodger blue', 'Player'), ('deep sky blue', 'Wall'), ('yellow2', 'Trap'), ('orange', 'V Trap'),
        ('DarkOrange1', 'H Trap'), ('gold', 'Coin'), ('SpringGreen', 'Checkpoint'), ('green', 'Goal'))):
    if type(event) is not tuple:  # Manual drawing in level creator
        if str(event)[1] == 'M':
            sleep(0.015)
        left, top, right, bottom = get_grid_location(event.x, event.y, tile_size)
        if field.find_overlapping(left+2, top+2, right-2, bottom-2) or not active_object or\
                event.y >= height or event.y < 0 or event.x < 0 or event.x > width:
            return
    else:  # Automatic drawing when loading a level
        left, top, right, bottom = event[0], event[1], event[0]+tile_size, event[1]+tile_size
    item = int(active_object[0]) - 1
    color, tag = draw_commands[item]
    shape_name = 'rectangle' if item in (0, 1, 6, 7) else 'oval'
    dash = '' if item not in (2, 3, 4) else '1,'
    outline = 'black' if item not in (6, 7) else ''
    if tag == 'Player':
        left += 3
        top += 3
        right -= 3
        bottom -= 3
        if old_spawn := field.find_withtag('Player'):
            return field.coords(old_spawn[0], left, top, right, bottom)
    direction = 1
    if tag not in ('V Trap', 'H Trap'):
        properties = ' '
    elif properties == 6:
        direction = -1
    eval(f"field.create_{shape_name}(left, top, right, bottom, fill='{color}', dash=({dash}), outline='{outline}', "
         f"tags=['{tag}', '{properties}', '{direction}'])")


def get_grid_location(x: int, y: int, tile_size: int) -> tuple[int, int, int, int]:
    left = int(x/tile_size)*tile_size
    top = int(y/tile_size)*tile_size
    return left, top, left+tile_size, top+tile_size


def select_level(exit_func, field: tk.Canvas, tile_size: int, height: int, width: int):
    if not (filename := filedialog.askopenfilename()):
        return
    try:
        with open(filename, newline='') as csvfile:
            level_list = [level['Name'] + ' - ' + level['Description'].replace('\n', ' ') for level in csv.DictReader(csvfile)]
    except KeyError:
        return tk.messagebox.showerror('Invalid file', 'Level data could not be found')
    loaded_levels = tk.Toplevel()
    loaded_levels.title("Select Level")
    loaded_levels.resizable(False, False)
    loaded_levels.grab_set()
    scroll_y = tk.Scrollbar(loaded_levels)
    scroll_x = tk.Scrollbar(loaded_levels)
    levels_listbox = tk.Listbox(loaded_levels, width=40, font='courier 12', height=20, yscrollcommand=scroll_y.set,
                                xscrollcommand=scroll_x.set)
    levels_listbox.grid(row=1)
    tk.Button(loaded_levels, text='Load Level', command=lambda: exit_func(filename=filename,
              index=levels_listbox.curselection()[0]+1, field=field, tile_size=tile_size,
              height=height, width=width, window=loaded_levels)).grid()
    scroll_x.grid(row=0, sticky='ew', columnspan=2)
    scroll_x.config(command=levels_listbox.xview)
    scroll_y.grid(row=1, column=1, sticky='ns')
    scroll_y.config(command=levels_listbox.yview)
    for level in level_list:
        levels_listbox.insert('end', level)


def load_level(filename: str, index: int, field: tk.Canvas, tile_size: int, height: int, width: int, window=None, replace=False):
    with open(filename, newline='') as csvfile:
        data = tuple(csv.reader(csvfile))[index]
    if replace:
        field.delete("all")
    create_border(field, width, height)
    for item_index, item_type in enumerate(data[4:]):
        if not item_type:
            continue
        for coordinate in item_type.split('|'):
            if len(coordinate.split()) >= 3:
                properties = ' '.join((coordinate.split())[2:])
            else:
                properties = ' '
            place_object(event=(int((coordinate.split())[0])*tile_size, int((coordinate.split())[1])*tile_size),
                         field=field, active_object=str(item_index+1), tile_size=tile_size, height=height,
                         width=width, properties=properties)
    if window:
        window.destroy()
    return data[0], data[1]


def create_border(field, width, height):
    field.create_rectangle(0, 0, width, 0, tags='Wall', outline='')
    field.create_rectangle(0, 0, 0, height, tags='Wall', outline='')
    field.create_rectangle(width, 0, width, height, tags='Wall', outline='')
    field.create_rectangle(0, height, width, height, tags='Wall', outline='')


def main():
    Levels().mainloop()


if __name__ == "__main__":
    main()
