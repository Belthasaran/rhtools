
# This file was generated by the Tkinter Designer by Parth Jadhav
# https://github.com/ParthJadhav/Tkinter-Designer


from pathlib import Path
import tkinter as tk
import tkinter.messagebox
import loadsmwrh
import gui_launchoptions
import pb_repatch
import pb_sendtosnes
import pb_lvlrand
import re
import time

# from tkinter import *
# Explicit imports to satisfy Flake8
from tkinter import Tk, Canvas, Entry, Text, Button, PhotoImage, StringVar, Frame, Label
from tkinter.ttk import Treeview, Scrollbar, Style


OUTPUT_PATH = Path(__file__).parent
ASSETS_PATH = OUTPUT_PATH / Path(r"assets/frame0")

hackdict = loadsmwrh.get_hackdict(skipdups=True)
notedict = loadsmwrh.get_note_dict()
#tree_items = []
detached_items = []


def relative_to_assets(path: str) -> Path:
    return ASSETS_PATH / Path(path)

def tva_selection_changed(root, tva, button_7, x):
    current = tva.focus()
    item = tva.item(current)
    if not('values' in item) or len(item['values']) < 1  or pb_lvlrand.randlevel_count(item['values'][0]) < 1:
        button_7.configure(state=tk.DISABLED)
    else:
        button_7.configure(state=tk.NORMAL)

    if not('values' in item) or len(item['values']) < 1:
        button_4.configure(state=tk.DISABLED)
    else:
        button_4.configure(state=tk.NORMAL)
    root.update()
    pass

def launch_options_click(root):
    gui_launchoptions.launch_options_click(root)

def btn_randomhack_any(root,tva):
    #ohash = loadsmwrh.get_local_options()
    pass

def button_mark_done(root,tva,label_status):
    current = tva.focus()
    item = tva.item(current)
    notedict = loadsmwrh.get_note_dict()
    if not('values' in item) or len(item['values'])<1:
       tkinter.messagebox.showerror(message='Please choose a hack from the list')
       return
    hidval = str(item['values'][0])
    if not(hidval in notedict):
        notedict[hidval] = {}
    if not('done' in notedict[hidval]) or not(notedict[hidval]["done"]):
        label_status.configure(text=f'Marked {hidval} as done.')
        notedict[hidval]["done"] = "Done"
        notedict[hidval]["done_at"] = int(time.time())
    else:
       label_status.configure(text=f'Unmarked {hidval}')
       del notedict[hidval]["done"]
    pass
  
def button_play_hack(root,tva,label_status):
   current = tva.focus()
   item = tva.item(current)
   ohash = loadsmwrh.get_local_options()
   if not('values' in item) or len(item['values'])<1:
       tkinter.messagebox.showerror(message='Please choose a hack from the list')   
   else:
       print('S' + str(item))  
       if label_status:
           label_status.configure(text='Patching %s. %s' % (str(item['values'][0]), item['values'][1]))
           root.update()
       result = pb_repatch.repatch_function(['launch1',str(item['values'][0])] )
       if result:
           print(str(result))
           if label_status:
               label_status.configure(text='Sending ' + str(result) + ' to SNES')
               root.update()
           sendresult = pb_sendtosnes.sendtosnes_function(['launch1', result, 'launch1'])
           if not(sendresult):
               tkinter.messagebox.showerror(message='Launcher1 failed to run (please check launch options)')
           else:
               if label_status:
                   label_status.configure(text='Ok, ' + str(result) + ' should be running.')

  #import gui_launchoptions


def button_play_randlevel(root,tva):
   current = tva.focus()
   item = tva.item(current)
   ohash = loadsmwrh.get_local_options()
   if not('values' in item) or len(item['values'])<1:
       tkinter.messagebox.showerror(message='Please choose a hack from the list')
   else:
       print('S' + str(item))
       result = pb_lvlrand.randlevel_function(['guilaunch', str(item['values'][0])  ] )
       #result = pb_repatch.repatch_function(['launch1', str(item['values'][0]]))
       if result:
           print(str(result))
       #    sendresult = pb_sendtosnes.sendtosnes_function(['launch1', result, 'launch1'])
       else:
            tkinter.messagebox.showerror(message='(lvlrand.py) Process failed')
       #    if not(sendresult):
       #        tkinter.messagebox.showerror(message='Launcher1 failed to run (please check launch options)')




window = Tk()

#window.geometry("719x464")
window.geometry("1024x768")
window.configure(bg = "#35393e")

canvas = Canvas(
    window,
    bg = "#35393e",
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
    fill="#35393e",
    outline="") ##PANEL

canvas.columnconfigure(0, weight=5)
canvas.columnconfigure(1, weight=1)
#canvas.columnconfigure(2, weight=1)

dataframe1 = Frame(canvas)
dataframe1.configure(bg = "#35393e")
dataframe1.grid(row=1,rowspan=10,column=0,pady=60,sticky="news")
dataframe1.rowconfigure(0, weight=1)
dataframe1.rowconfigure(1, weight=1)
dataframe1.rowconfigure(2, weight=1)
dataframe1.rowconfigure(3, weight=1)
dataframe1.rowconfigure(4, weight=5)
dataframe1.columnconfigure(0, weight=10)
dataframe1.columnconfigure(1, weight=1)
dataframe1.columnconfigure(2, weight=1)

tvStyle = Style()
tvStyle.theme_use("default")
tvStyle.configure("Treeview",
         selectmode="browse",
         background="black",
         fieldbackground="black",
         rowheight=30,
         foreground="#f6f6f6",
         font=(None,12))
tvStyle.configure("Treeview.Heading", font=(None,14), background="darkgray")
#tvStyle.configure("Treeview.cell", font=(None,20))
#tvStyle.map('Treeview', background=[('selected', 'red')])

tva = Treeview(dataframe1, columns=['id','name','type','author','length','done'], show='headings')
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

tva.heading('done', text='Done')
tva.column('done', width=25, anchor=tk.W)

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

ipos = 0
for hek in hackdict.keys():
 ipos = ipos + 1
 he = hackdict[hek]
 doneval = ''
 if hek in notedict:
     if 'done' in notedict[hek]:
         doneval = str( notedict[hek]['done']  )
 ti = (    tva.insert('', tk.END, values=[  str(he['id']),
               he['name'],
               he['type'],
               he['authors'],
               he['length'],
               doneval,
               he['tags'],
               he['description'], 
               '0'
           ]))
 if ipos > 2000 :
     tva.detach(ti)
     detached_items.append(ti)

#for g in range(10):
#    tva.insert('', tk.END, values=['a','b','c','d'])
scrollbar = Scrollbar(dataframe1, orient=tk.VERTICAL, command=tva.yview)
tva.configure(yscroll=scrollbar.set)
scrollbar.grid(row=2,rowspan=5,column=1,sticky='ns')

#entry_image_1 = PhotoImage(
#    file=relative_to_assets("entry_1.png"))
#entry_bg_1 = canvas.create_image(
#    213.0,
#    44.0,
#    image=entry_image_1
#)

filterText = StringVar()
filterframe = Frame(canvas)
filterframe.configure(bg = "#35393e")
entry_1 = Entry(filterframe,
    bd=0,
    #bg="#35393e",
    bg="#99aab5",
    fg="#f6f6f6",
#    bg="#F1F5FF",
#    fg="#000716",
    highlightthickness=0,
    textvariable = filterText,
    width=40
)

label_1 = Label(filterframe,text="Filter  ")
label_1.configure(bg = "#35393e", foreground="white")
label_1.grid(column=0,row=0,sticky="news")
#entry_1.bind('<<Insert>>', lambda: print('entry_1'))
#entry_1.place(
#    x=33.0,
#    y=16.0,
#    width=360.0,
#    height=54.0
#)

tva.bind('<<TreeviewSelect>>', lambda x: tva_selection_changed(window, tva, button_7, x)) 


filterframe.grid(row=0,column=0,sticky="news")
entry_1.grid(row=0,column=1,padx=4)

def doesMatch(hinfo,varText,ipos):
       match = False
       lenvt = len(varText)
       if len(varText) < 4 and ipos <= 2000:
           match = True
       if lenvt >= 4 and re.search(varText.lower(), hinfo["name"].lower(), re.I):
           match = True
       if lenvt >= 4 and re.search(varText.lower(), hinfo["type"].lower(), re.I):
           match = True
       if lenvt >= 4 and re.search(varText.lower(), hinfo["authors"].lower(), re.I):
           match = True
       if lenvt >= 3 and re.search(varText.lower(), hinfo["id"].lower(), re.I):
           match = True
       if lenvt >= 4 and re.search(varText.lower(), hinfo["description"].lower(), re.I):
           match = True
       if lenvt >= 5 and re.search(varText.lower(), hinfo["added"].lower(), re.I):
           match = True
       if lenvt >= 4 and hinfo["tags"]:
           for tagt in hinfo["tags"]:
               if re.search(varText.lower(), tagt.lower(), re.I):
                   match = True
       return match


def filterChanged(var,tva):
   varText = var.get()

   #if len(varText) < 3 :
   #    varText = ''
   print('filter: '+str(var.get()))
   global detached_items
   detached_items2=[]
   ip = 0

   detached_items.extend(tva.get_children())
   tva.detach(*tva.get_children())

   for ti in detached_items:
       ip = ip + 1
       match = False
       tientry = tva.item(ti)
       tivalues = tientry['values']
       hackid = tivalues[0]
       hinfo = None
       if str(hackid) in hackdict:
           hinfo = hackdict[str(hackid)]
       #
       if hinfo and doesMatch(hinfo,varText,len(tva.get_children()) + ip):
            tva.reattach(ti,'',0)
       else:
            detached_items2.append(ti)
   detached_items = detached_items2

   if len(varText) < 3:
       return

   ipos = 0
   for ti in tva.get_children():
       ipos = ipos + 1
       match = False
       #itemId ti
       tientry = tva.item(ti)
       tivalues = tientry['values']
       hackid = tivalues[0]
       hinfo = None
       if str(hackid) in hackdict:
           hinfo = hackdict[str(hackid)]

       match = hinfo and doesMatch(hinfo,varText,ipos)
       if match == True:
           #tva.item(ti, values=tivalues)
           pass
       else:
           detached_items.append(ti)
           tva.detach(ti)
       tva.update()

   #for he in hacklist: # loadsmwrh.get_hacklist_data():
   #     pass
    #   tva.insert('', tk.END, values=[  he['id'],
    #               he['name'],
    #               he['type'],
    #               he['authors'],
    #               he['length'],
    #               he['description']
    #           ])

filterText.trace("w", lambda name, index, mode, var=filterText: filterChanged(var,tva))


#canvas.create_rectangle(
#    539.0,
#    16.0,
#    706.0,
#    262.0,
#    fill="#000000",
#    #fill="#F2F6FF",
#    outline="")

canvas.create_rectangle(
    544.0,
    270.0,
    706.0,
    442.0,
    fill="#000000",
    #fill="#F2F6FF",
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
    command=lambda: button_play_hack(window,tva,label_xnum),
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
    command=lambda: button_mark_done(window,tva,label_xnum)
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
    state=tk.DISABLED
    #relief="flat"
)
#button_5.place(
#    x=411.0,
#    y=21.0,
#    width=117.0,
#    height=51.0
#)
button_5.grid(row=0,column=2,sticky="news") # Random filtered


label_xnum = Label(filterframe, font=(None,14),
  text=("* DB: Loaded %d hacks: %s" % ( len(hackdict.keys()), loadsmwrh.rhmd_path()  )),
)

label_xnum.configure(bg = "#35393e", foreground="white")
label_xnum.grid(column=3,row=0,sticky="news")


button_image_6 = PhotoImage(
    file=relative_to_assets("button_6.png"))
button_6 = Button(subactionframe,
    #image=button_image_6,
    borderwidth=1,
    highlightthickness=1,
    command=lambda: btn_randomhack_any(window),
    #relief="flat",
    text="Random Hack (any)",
    state=tk.DISABLED
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
    command= lambda: button_play_randlevel(window,tva),
    #command=lambda: print("button_7 clicked"),
    #relief="flat",
    text="Random Level",
    state=tk.DISABLED
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
    #fill="#D9D9D9",
    fill="#000000",
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



