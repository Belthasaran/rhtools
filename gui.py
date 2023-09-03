
# This file was generated by the Tkinter Designer by Parth Jadhav
# https://github.com/ParthJadhav/Tkinter-Designer


from pathlib import Path
import tkinter as tk
import loadsmwrh
import gui_launchoptions

# from tkinter import *
# Explicit imports to satisfy Flake8
from tkinter import Tk, Canvas, Entry, Text, Button, PhotoImage, StringVar, Frame, Label
from tkinter.ttk import Treeview, Scrollbar


OUTPUT_PATH = Path(__file__).parent
ASSETS_PATH = OUTPUT_PATH / Path(r"assets/frame0")


def relative_to_assets(path: str) -> Path:
    return ASSETS_PATH / Path(path)

def launch_options_click(root):
    gui_launchoptions.launch_options_click(root)
  
def button_play_hack(root,tva):
   print('S' + str(tva))  

  #import gui_launchoptions


window = Tk()

#window.geometry("719x464")
window.geometry("800x600")
window.configure(bg = "#FFFFFF")

canvas = Canvas(
    window,
    bg = "#FFFFFF",
#    height = 600, 
#    width = 719,
    bd = 0,
    highlightthickness = 0,
    relief = "ridge"
)
##canvas.place(x = 0, y = 0)
#canvas.grid(column=0,row=0,rowspan=2,sticky="news")
canvas.pack(side=tk.TOP,fill=tk.BOTH, expand=True)
prect  = canvas.create_rectangle(
    18.0,
    79.0,
    528.0,
    413.0,
    fill="#F3F5FF",
    outline="") ##PANEL

canvas.columnconfigure(0, weight=5)
canvas.columnconfigure(1, weight=1)
#canvas.columnconfigure(2, weight=1)

dataframe1 = Frame(canvas)
dataframe1.grid(row=1,rowspan=10,column=0,pady=60,sticky="news")
dataframe1.rowconfigure(0, weight=1)
dataframe1.rowconfigure(1, weight=1)
dataframe1.rowconfigure(2, weight=1)
dataframe1.rowconfigure(3, weight=1)
dataframe1.rowconfigure(4, weight=5)
dataframe1.columnconfigure(0, weight=10)
dataframe1.columnconfigure(1, weight=1)
dataframe1.columnconfigure(2, weight=1)

tva = Treeview(dataframe1, columns=['id','name','type','author','length'], show='headings')
tva.heading('id', text='Id')
tva.column('id', width=100, anchor=tk.W)

tva.heading('name', text='Name')
tva.column('name', width=220, anchor=tk.W)

tva.heading('type', text='Type')
tva.column('type', width=130, anchor=tk.W)

tva.heading('author', text='Author')
tva.column('author', width=100, anchor=tk.W)

tva.heading('length', text='Length')
tva.column('length', width=50, anchor=tk.W)

canvas.rowconfigure(0,weight=1)
canvas.rowconfigure(1,weight=1)
canvas.rowconfigure(2,weight=1)
canvas.rowconfigure(3,weight=1)
canvas.rowconfigure(4,weight=1)
canvas.rowconfigure(5,weight=1)
canvas.rowconfigure(6,weight=1)
canvas.rowconfigure(7,weight=1)
canvas.rowconfigure(8,weight=1)
canvas.rowconfigure(9,weight=1)
canvas.rowconfigure(10,weight=1)

tva.grid(row=2, rowspan=5,column=0,sticky="news")
#tva.insert('', tk.END, values=['a','b','c','d'])
#tva.place(
#    x=33.0,
#    y=16.0,
#    width=360.0, #360
#    height=54.0
#)
#tva.pack(side=tk.BOTTOM, fill=tk.X, expand=True)

# name type author length description
for he in loadsmwrh.get_hacklist_data():
    tva.insert('', tk.END, values=[  he['id'],
               he['name'],
               he['type'],
               he['authors'],
               he['length'],
               he['description']
           ])

#for g in range(10):
#    tva.insert('', tk.END, values=['a','b','c','d'])
scrollbar = Scrollbar(dataframe1, orient=tk.VERTICAL, command=tva.yview)
tva.configure(yscroll=scrollbar.set)
scrollbar.grid(row=2,rowspan=5,column=1,sticky='ns')

entry_image_1 = PhotoImage(
    file=relative_to_assets("entry_1.png"))
entry_bg_1 = canvas.create_image(
    213.0,
    44.0,
    image=entry_image_1
)

filterText = StringVar()
filterframe = Frame(canvas)
entry_1 = Entry(filterframe,
    bd=0,
    bg="#F1F5FF",
    fg="#000716",
    highlightthickness=0,
    textvariable = filterText,
    width=40
)

label_1 = Label(filterframe,text="Filter  ")
label_1.grid(column=0,row=0,sticky="news")
#entry_1.bind('<<Insert>>', lambda: print('entry_1'))
#entry_1.place(
#    x=33.0,
#    y=16.0,
#    width=360.0,
#    height=54.0
#)
filterframe.grid(row=0,column=0,sticky="news")
entry_1.grid(row=0,column=1,padx=4)
def filterChanged(var):
   print('filter: '+str(var.get()))
filterText.trace("w", lambda name, index, mode, var=filterText: filterChanged(var))


canvas.create_rectangle(
    539.0,
    16.0,
    706.0,
    262.0,
    fill="#F2F6FF",
    outline="")

canvas.create_rectangle(
    544.0,
    270.0,
    706.0,
    442.0,
    fill="#F2F6FF",
    outline="")

actionframe = Frame(canvas)
actionframe.grid(row=0,column=1,rowspan=2)

subactionframe = Frame(canvas)
subactionframe.grid(row=3,column=1,rowspan=2)

button_image_1 = PhotoImage(
    file=relative_to_assets("button_1.png"))
button_1 = Button(actionframe,
    #image=button_image_1,
    borderwidth=1,
    highlightthickness=1,
    command=lambda: print("button_1 clicked"),
    text="Hack Options",
    state=tk.DISABLED
    #relief="flat"
)
#button_1.place(
#    x=568.0,
#    y=164.0,
#    width=122.0,
#    height=47.0
#)
button_1.grid(row=2,column=0)
#button_1.grid(row=0,column=5) # H. Options

button_image_2 = PhotoImage(
    file=relative_to_assets("button_2.png"))
button_2 = Button(actionframe,
    text="Play this hack",
    #image=button_image_2,
    borderwidth=1,
    highlightthickness=1,
    command=lambda: button_play_hack(window,tva),
    #relief="flat"
)
#button_2.place(
#    x=568.0,
#    y=71.0,
#    width=122.0,
#    height=47.0
#)
button_2.grid(row=0,column=0) # Play this hack
#button_2.grid(row=0,column=5)  Play this hack

button_image_3 = PhotoImage(
    file=relative_to_assets("button_3.png"))
button_3 = Button(actionframe,
    #image=button_image_3,
    borderwidth=0,
    highlightthickness=0,
    command=lambda: print("button_3 clicked"),
    relief="flat",
    text=".. Specific Level",
    state=tk.DISABLED
)
#button_3.place(
#    x=568.0,
#    y=211.0,
#    width=122.0,
#    height=47.0
#)
#button_3.grid(row=0,column=5) # Specific Levels
button_3.grid(row=3,column=0)

button_image_4 = PhotoImage(
    file=relative_to_assets("button_4.png"))
button_4 = Button(actionframe,
    text="Mark as done",
    #image=button_image_4,
    state=tk.DISABLED,
    borderwidth=1,
    highlightthickness=1,
    command=lambda: print("button_4 clicked"),
    #relief="flat"
)
#button_4.place(
#    x=568.0,
#    y=118.0,
#    width=122.0,
#    height=47.0
#)
#button_4.grid(row=0,column=5) # Mark as done
button_4.grid(row=1,column=0)

button_image_5 = PhotoImage(
    file=relative_to_assets("button_5.png"))
button_5 = Button(filterframe,
    #image=button_image_5,
    text="Random Hack (filtered)",
    borderwidth=3,
    highlightthickness=1,
    command=lambda: print("button_5 clicked"),
    #relief="flat"
)
#button_5.place(
#    x=411.0,
#    y=21.0,
#    width=117.0,
#    height=51.0
#)
button_5.grid(row=0,column=2,sticky="news") # Random filtered

button_image_6 = PhotoImage(
    file=relative_to_assets("button_6.png"))
button_6 = Button(subactionframe,
    #image=button_image_6,
    borderwidth=1,
    highlightthickness=1,
    command=lambda: print("button_6 clicked"),
    #relief="flat",
    text="Random Hack (any)"
)
#button_6.place(
#    x=568.0,
#    y=281.0,
#    width=127.0,
#    height=41.0
#)
#button_6.grid(row=0,column=5) # Random hack any
button_6.grid(row=0,column=0)

button_image_7 = PhotoImage(
    file=relative_to_assets("button_7.png"))
button_7 = Button(subactionframe,
    image=button_image_7,
    borderwidth=1,
    highlightthickness=1,
    command=lambda: print("button_7 clicked"),
    #relief="flat",
    text="Random Level"
)
#button_7.place(
#    x=568.0,
#    y=334.0,
#    width=127.0,
#    height=47.0
#)
#button_7.grid(row=0,column=5) # Random level
button_7.grid(row=1,column=0)

button_image_8 = PhotoImage(
    file=relative_to_assets("button_8.png"))
button_8 = Button(subactionframe,
    image=button_image_8,
    borderwidth=1,
    highlightthickness=1,
    command=lambda: launch_options_click(window),
    #relief="flat"
)
#button_8.place(
#    x=568.0,
#    y=389.0,
#    width=127.0,
#    height=53.0
#)
#Launch options button_8.grid(row=0,column=5)
button_8.grid(row=3,column=0)

canvas.create_rectangle(
    22.0,
    416.0,
    528.0,
    442.0,
    fill="#D9D9D9",
    outline="")

canvas.create_text(
    62.0,
    420.0,
    anchor="nw",
    text="Show Hidden",
    fill="#000000",
    font=("Inter", 12 * -1)
)
window.resizable(True, True)
window.mainloop()



