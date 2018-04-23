from tkinter import *
import time


class FullScreenApp(object):
    def __init__(self, master, **kwargs):
        self.master = master
        self.master.config(menu=None)
        pad = 3
        self._geom = '200x200+0+0'
        master.geometry("{0}x{1}+0+0".format(
            master.winfo_screenwidth() - pad, master.winfo_screenheight() - pad))

    def toggle_geom(self, event):
        geom = self.master.winfo_geometry()
        print(geom, self._geom)
        self.master.geometry(self._geom)
        self._geom = geom


root = Tk()
time1 = ''
clock = Label(root, font=('times', 20, 'bold'), bg='black', fg='white')
clock.pack(fill=BOTH, expand=1)


def tick():
    global time1
    # get the current local time from the PC
    time2 = time.strftime('%H:%M:%S')
    # if time string has changed, update it
    if time2 != time1:
        time1 = time2
        clock.config(text=time2)
    # calls itself every 200 milliseconds
    # to update the time display as needed
    # could use >200 ms, but display gets jerky
    clock.after(200, tick)


tick()

app = FullScreenApp(root)

root.overrideredirect(1)
root.mainloop()
