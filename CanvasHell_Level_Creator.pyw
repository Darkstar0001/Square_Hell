import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from time import sleep
from sys import setrecursionlimit
import csv
from os.path import exists
from CanvasHell import place_object, get_grid_location, select_level, load_level


class Setup(tk.Frame):
    def __init__(self):
        tk.Tk()
        tk.Frame.__init__(self)
        self.master.resizable(False, False)
        self.grid()
        ttk.Style(self).configure('TLabel', font='arial 25')
        ttk.Style(self).configure('TButton', font='arial 25')
       
        ttk.Button(self, text='Create New', command= self.finish).grid(columnspan=3)
        ttk.Button(self, text='Preload level from file', command=lambda: select_level(self.load_level, None, None, None, None)).grid(columnspan=2)

    def load_level(self, **kwargs):
        if kwargs['index']:
            kwargs['window'].destroy()
            self.finish(kwargs)

    def finish(self, level=None):
        self.settings_list = (35, 50, level)
        self.master.destroy()


class LevelCreator(tk.Frame):
    def __init__(self, height: int, width: int, preload=()):
        self.VERSION = 0.1
        tk.Tk()
        tk.Frame.__init__(self)
        self.master.title("Level Creator")
        self.master.resizable(False, False)
        self.TILE_SIZE = 20
        self.WIDTH = width*self.TILE_SIZE  # default 1000
        self.HEIGHT = height*self.TILE_SIZE  # default 700
        self.master.geometry(f"{self.WIDTH}x{self.HEIGHT+57}")
        self.place(relx=0.5, relwidth=1, anchor='n')
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        ttk.Style().configure("TButton", font='arial 30')

        self.active_object = tk.StringVar()
        self.options = tk.OptionMenu(self, self.active_object, "1 - Starting point", "2 - Wall",
                                     "3 - Trap (stationary)", "4 - Trap (vertical movement)",
                                     "5 - Trap (horizontal movement)", "6 - Coin", '7 - Checkpoint', '8 - Goal')
        self.options.grid(sticky='nw', row=0)
        self.options.config(font='arial 26', width=25)

        tk.Label(self, text="Trap movement\noffset (tiles):", font='arial 14').grid(row=0, padx=(180, 0))
        self.offset = tk.StringVar(value='0')
        self.offset_box = tk.Spinbox(self, from_=-3, to=3, state='readonly',
                                     font='arial 25', width=2, textvariable=self.offset)
        self.offset_box.grid(row=0, padx=(400, 0))

        self.field = tk.Canvas(self, bg='azure', height=self.HEIGHT)
        self.field.grid(sticky='ews')
        ttk.Button(self, text="Save Level", command=self.save_level_dialogue).grid(row=0, sticky='e')
        self.field.bind('<Button-1>', lambda event: place_object(event, self.field, self.active_object.get(),
                                                                 self.TILE_SIZE, self.HEIGHT, self.WIDTH, self.offset.get()))
        self.field.bind('<B1-Motion>', lambda event: place_object(event, self.field, self.active_object.get(),
                                                                  self.TILE_SIZE, self.HEIGHT, self.WIDTH, self.offset.get()))
        self.field.bind('<Button-3>', self.remove_object)
        self.field.bind('<B3-Motion>', self.remove_object)

        self.level_name = ''
        self.level_desc = ''

        if preload:
            self.level_name, self.level_desc = load_level(
                filename=preload['filename'], index=preload['index'], field=self.field,
                tile_size=self.TILE_SIZE, height=self.HEIGHT, width=self.WIDTH)
            self.master.title("Level Creator - " + self.level_name)

    def remove_object(self, event):
        if obj := self.field.find_overlapping(event.x, event.y, event.x, event.y):
            self.field.delete(obj)
        if str(event)[1] == 'M':
            sleep(0.005)

    def save_level_dialogue(self):
        if self.level_validate() is not True:
            return
        save_window = tk.Toplevel(self)
        save_window.resizable(False, False)
        save_window.grab_set()
        tk.Label(save_window, text="Level Name:", font='arial 25').grid()
        name_field = tk.Entry(save_window, font='arial 25')
        name_field.grid(padx=10, pady=(0, 10))
        tk.Label(save_window, text='Level Description (optional):', font='arial 20').grid()
        description_field = tk.Text(save_window, width=44, height=10, wrap='word')
        description_field.grid(pady=(0, 15))
        ttk.Button(save_window, text='Save Level', command=lambda: self.level_info_validate(
            name=name_field.get(), description=description_field.get(1.0, 'end').strip(), window=save_window)).grid()

        name_field.insert(0, self.level_name)
        description_field.insert(1.0, self.level_desc)

    def level_validate(self):
        if not self.field.find_withtag('Player'):
            return tk.messagebox.showwarning('No spawn point', 'You must specify a starting point for the player.')
        if not self.field.find_withtag('Goal'):
            return tk.messagebox.showwarning('No end point', 'You must include at least one goal tile.')
        x1, y1, x2, y2 = self.field.coords(self.field.find_withtag('Player'))
        if not self.plot_path_to_goal(x1=x1+2, y1=y1+2, x2=x2-2, y2=y2-2, walked={'Goal': 0, 'Coin': 0, 'Tiles': []}):
            return tk.messagebox.showwarning('Goal or coin(s) unreachable', 'The goal or some coins are currently '
                                                                            'blocked, rendering the level unwinnable.')
        return True

    def plot_path_to_goal(self, x1: int, y1: int, x2: int, y2: int, walked: dict) -> bool | None: # Pathing dict still breaks sometimes
        if walked['Goal'] and walked['Coin'] == len(self.field.find_withtag('Coin')):
            return True
        if (x1, y1) in walked['Tiles'] or x1 < 0 or x1 > self.WIDTH or y1 < 0 or y2 > self.HEIGHT:
            return
        walked['Tiles'].append((x1, y1))
        if current := self.field.find_overlapping(x1, y1, x2, y2):
            current = self.field.gettags(current[0])[0]
            if current == 'Coin':
                walked['Coin'] += 1
            elif current == 'Goal':
                walked['Goal'] = 1
            elif current in 'Wall, Trap':
                return
        #self.field.create_rectangle(x1, y1, x2, y2, fill='blue', tags='Test')  # for testing purposes only
        if any((self.plot_path_to_goal(x1 + self.TILE_SIZE, y1, x2 + self.TILE_SIZE, y2, walked),
               self.plot_path_to_goal(x1 - self.TILE_SIZE, y1, x2 - self.TILE_SIZE, y2, walked),
               self.plot_path_to_goal(x1, y1 + self.TILE_SIZE, x2, y2 + self.TILE_SIZE, walked),
               self.plot_path_to_goal(x1, y1 - self.TILE_SIZE, x2, y2 - self.TILE_SIZE, walked))):
            return True
        if walked['Goal'] == 1 and walked['Coin'] == len(self.field.find_withtag('Coin')):
            return True

    def level_info_validate(self, name: str, description: str, window: tk.Toplevel):
        if not name:
            return tk.messagebox.showwarning('No level name', 'A level name is required.')
        if not exists("My Saved Levels.csv"):
            with open("My Saved Levels.csv", 'a', newline='') as csvfile:
                csv.writer(csvfile).writerow(('Name', 'Description', 'Version', 'Grid Size', 'Player', 'Wall', 'Trap',
                                              'V Trap', 'H Trap', 'Coin', 'Checkpoint', 'Goal'))
        overwrite = -1
        with open('My Saved Levels.csv', newline='') as csvfile:
            contents = tuple(csv.DictReader(csvfile))
        for row_number, row in enumerate(contents):
            if name == row['Name']:
                overwrite = tk.messagebox.askyesno('Level name already exists', 'A level with this name already '
                                                                        'exists. Would you like to overwrite it?')
                if not overwrite:
                    return
                overwrite = row_number + 1
                break
        try:
            with open('My Saved Levels.csv', 'a', newline='') as csvfile:
                self.save_level(name, description, csvfile)
            self.level_name = name
            self.level_desc = description
            self.master.title("Level Creator - " + name)
            if overwrite >= 0:
                new = prepare_csv_backup(filename='My Saved Levels.csv', trim=True)
                new[overwrite] = new[-1]
                del new[-1]
                with open('My Saved Levels.csv', 'w+', newline='') as csvfile:
                    csv.writer(csvfile).writerows(new)
        except PermissionError as e:
            return tk.messagebox.showerror(e, "Saved levels file could not be accessed.\nMake sure the file is not "
                                              "already open in another program.")
        tk.messagebox.showinfo('Level saved', f'Level "{name}" successfully saved.')
        window.destroy()

    def save_level(self, name: str, description: str, csvfile):
        level_data = {'Name': name, 'Description': description, 'Version': self.VERSION,
                      'Grid Size': f"{int(self.HEIGHT/self.TILE_SIZE)} {int(self.WIDTH/self.TILE_SIZE)}"}
        for category in ('Player', 'Wall', 'Trap', 'V Trap', 'H Trap', 'Coin', 'Checkpoint', 'Goal'):
            if items := self.field.find_withtag(category):
                level_data[category] = '|'.join([f"{int(self.field.coords(item)[0]/self.TILE_SIZE)} "
                                                 f"{int(self.field.coords(item)[1]/self.TILE_SIZE)} "
                                                 f"{' '.join(self.field.gettags(item)[1:])}".rstrip() for item in items])
        csv.DictWriter(csvfile, fieldnames=('Name', 'Description', 'Version', 'Grid Size', 'Player', 'Wall', 'Trap',
                                            'V Trap', 'H Trap', 'Coin', 'Checkpoint', 'Goal')).writerow(level_data)


def prepare_csv_backup(filename, trim=False):
    with open(filename, 'r', newline='') as csvfile:
        full_file = []
        full_file.extend(csv.reader(csvfile))
    with open(f"{filename}.bak", 'w+', newline='') as csvfile:
        if trim:
            csv.writer(csvfile).writerows(full_file[:-1])
        else:
            csv.writer(csvfile).writerows(full_file)
    return full_file


def main():
    (settings := Setup()).mainloop()
    level_creator = LevelCreator(*settings.settings_list)
    del settings
    setrecursionlimit(2000)
    level_creator.mainloop()


if __name__ == "__main__":
    main()
