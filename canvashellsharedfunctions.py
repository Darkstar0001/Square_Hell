import tkinter as tk
from tkinter import messagebox, filedialog
from time import sleep
import csv


def place_object(event, field: tk.Canvas, active_object: str, tile_size: int, height: int, width: int, properties: str,
                 editor_preload=None, draw_commands=(
        ('dodger blue', 'Player'), ('deep sky blue', 'Wall'), ('yellow2', 'Trap'), ('orange', 'V Trap'),
        ('DarkOrange1', 'H Trap'), ('gold', 'Coin'), ('SpringGreen', 'Checkpoint'), ('green', 'Goal'))):
    direction = ''
    if editor_preload is None:  # Manual drawing in level creator
        if str(event)[1] == 'M':
            sleep(0.015)
        left, top, right, bottom = get_grid_location(event.x, event.y, tile_size)
        if field.find_overlapping(left+2, top+2, right-2, bottom-2) or not active_object or\
                event.y >= height or event.y < 0 or event.x < 0 or event.x > width:
            return
    else:  # Automatic drawing when loading a level
        left, top, right, bottom = event[0], event[1], event[0]+tile_size, event[1]+tile_size
        if not editor_preload:
            direction = 1
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
    if tag not in ('V Trap', 'H Trap'):
        properties = ' '
    elif properties == 6 and direction:
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
            level_list = [level['Name'] + ' - ' + level['Description'].replace('\n', ' ') if level['Description'] else
                          level['Name'] for level in csv.DictReader(csvfile)]
    except KeyError:
        return tk.messagebox.showerror('Invalid file', 'Level data could not be found')
    loaded_levels = tk.Toplevel()
    loaded_levels.title("Select Level")
    loaded_levels.resizable(False, False)
    loaded_levels.grab_set()
    scroll_y = tk.Scrollbar(loaded_levels)
    scroll_x = tk.Scrollbar(loaded_levels, orient='horizontal')
    levels_listbox = tk.Listbox(loaded_levels, width=60, font='courier 12', height=20, yscrollcommand=scroll_y.set,
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


def load_level(filename: str, index: int, field: tk.Canvas, tile_size: int, height: int, width: int, window=None,
               replace=False, editor_preload=False):
    with open(filename, newline='') as csvfile:
        data = tuple(csv.reader(csvfile))[index]
    if replace:
        field.delete("all")
    if not editor_preload:
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
                         width=width, properties=properties, editor_preload=editor_preload)
    if window:
        window.destroy()
    return data[0], data[1]


def create_border(field, width, height):
    field.create_rectangle(0, 0, width, 0, tags='Wall', outline='')
    field.create_rectangle(0, 0, 0, height, tags='Wall', outline='')
    field.create_rectangle(width, 0, width, height, tags='Wall', outline='')
    field.create_rectangle(0, height, width, height, tags='Wall', outline='')
