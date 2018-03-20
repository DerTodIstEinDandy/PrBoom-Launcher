import tkinter as tk
from tkinter import ttk
from tkinter import filedialog as fd
import fnmatch as fn
import shell as sh
from shell import Shell, ShellCustom
import os
import os.path


help_msg = '''- If a custom wad you're going to play is designed for the original MS-DOS Doom.exe \
(classic releases like Memento Mori, or modern releases that have "Vanilla compatible" in their description),\
 select one of the compatibility modes depending on the base IWAD file: DOOM2 mode, Ultimate Doom mode \
 or Final Doom mode.\n\n- If a custom wad has "BOOM compatible" in its description, select "BOOM compatible mode"\
 \n\n- If a custom wad has "MBF compatible" in its description, select "MBF compatible mode"\n\n\
- "Don't set -complevel" option is useful when you're going to watch a demo and you want PrBoom+ to auto detect \
the correct compatibility option for it.'''


def center(win):
    """Center window"""

    win.update_idletasks()
    width = win.winfo_width()
    height = win.winfo_height()
    x = (win.winfo_screenwidth() // 2) - (width // 2)
    y = (win.winfo_screenheight() // 2) - (height // 2)
    win.geometry('{}x{}+{}+{}'.format(width, height, x, y))


class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.__gamemgr = Shell()
        self.__custommgr = ShellCustom()
        self.__ini_mgr = sh.IniManager(self.__custommgr)
        self.__ini_mgr.load()
        self.__gui = GUI(
            gamemgr=self.__gamemgr, custommgr=self.__custommgr, inimgr=self.__ini_mgr, master=self
        )
        self.protocol("WM_DELETE_WINDOW", self.__quit)
        center(self)

    def __quit(self, *args):
        self.__ini_mgr.save()
        self.destroy()


class GUIPopup(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.transient(parent)
        self._parent = parent
        self._popup_frame = tk.Frame(master=self)
        self.grab_set()
        self.focus_set()

    def _close(self):
        self._parent.grab_set()
        self._parent.focus_set()
        self.destroy()


class GUIPopupHelp(GUIPopup):
    def __init__(self, parent):
        super().__init__(parent)
        tk.Message(master=self._popup_frame, text=help_msg, justify=tk.CENTER, width=384).pack()
        self._popup_frame.pack()
        center(self)


class GUIPopupExeSet(GUIPopup):
    def __init__(self, parent):
        super().__init__(parent)
        self.__prboom = tk.StringVar(self._popup_frame)
        self.__prboom.set(Shell.prboom)
        self.__glboom = tk.StringVar(self._popup_frame)
        self.__glboom.set(Shell.glboom)
        tk.Label(master=self._popup_frame, text="Name of software mode executable:").pack(padx=10)
        tk.Entry(master=self._popup_frame, textvariable=self.__prboom, width=30).pack(pady=6, padx=10)
        tk.Label(master=self._popup_frame, text="Name of OpenGL executable:").pack(padx=10)
        tk.Entry(master=self._popup_frame, textvariable=self.__glboom, width=30).pack(pady=6, padx=10)
        tk.Button(master=self._popup_frame, text="Accept", command=self.__accept).pack(pady=3, padx=10)
        tk.Button(master=self._popup_frame, text="Quit", command=self._close).pack(pady=3, padx=10)
        self._popup_frame.pack()
        center(self)

    def __accept(self):
        Shell.prboom = self.__prboom.get()
        Shell.glboom = self.__glboom.get()
        self._close()


class GUIPopupScreenSet(GUIPopup):
    def __init__(self, parent):
        super().__init__(parent)
        self.__opengl_opt = GUIOpenGLSet(master=self._popup_frame, bd=2, relief=tk.GROOVE)
        self.__software_opt = GUISWRenderSet(master=self._popup_frame, bd=2, relief=tk.GROOVE)
        self.__button_panel = tk.Frame(master=self._popup_frame)
        self.__warning = tk.StringVar(self._popup_frame)
        self.__warning.set("")
        self.__deploy_widgets()
        center(self)

    def __accept(self):
        try:
            self.__opengl_opt.apply()
            self.__software_opt.apply()
        except tk._tkinter.TclError as err:
            self.__warning.set("Invalid resolution value!")
            return
        self._close()

    def __deploy_widgets(self):
        tk.Label(master=self._popup_frame, text="OpenGL executable options:").pack()
        self.__opengl_opt.pack(pady=4, padx=5)
        tk.Label(master=self._popup_frame, text="Software executable options:").pack()
        self.__software_opt.pack(pady=4, padx=5)
        tk.Label(master=self._popup_frame, textvariable=self.__warning, fg="red").pack()
        tk.Button(self.__button_panel, text="Accept", command=self.__accept).grid(column=0, row=0, padx=10)
        tk.Button(self.__button_panel, text="Quit", command=self._close).grid(column=1, row=0, padx=10)
        self.__button_panel.pack(pady=4)
        self._popup_frame.pack()


class GUIOpenGLSet(tk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master=master, **kwargs)
        self._res_x = tk.IntVar(self)
        self._res_y = tk.IntVar(self)
        self._fullscreen = tk.BooleanVar(self)
        self._res_x.set(Shell.gl_res_x)
        self._res_y.set(Shell.gl_res_y)
        self._fullscreen.set(Shell.gl_fullscreen)
        self.__res_frame = tk.Frame(self)
        self.__screenmode_frame = tk.Frame(self)
        self._deploy_widgets()

    def apply(self):
        Shell.gl_fullscreen = self._fullscreen.get()
        Shell.gl_res_x = self._res_x.get()
        Shell.gl_res_y = self._res_y.get()

    def _deploy_widgets(self):
        tk.Label(master=self.__res_frame, text="Width:").grid(row=0, column=0, sticky=tk.E)
        tk.Entry(
            master=self.__res_frame, textvariable=self._res_x, width=8
        ).grid(row=0, column=1, sticky=tk.W, padx=3)
        tk.Label(master=self.__res_frame, text="x").grid(row=0, column=2, padx=3)
        tk.Label(master=self.__res_frame, text="Height:").grid(row=0, column=3, sticky=tk.E)
        tk.Entry(
            master=self.__res_frame, textvariable=self._res_y, width=8
        ).grid(row=0, column=4, sticky=tk.W, padx=3)
        tk.Radiobutton(
            master=self.__screenmode_frame, text="Fullscreen", value=True, variable=self._fullscreen
        ).grid(row=0, column=1, sticky=tk.E)
        tk.Radiobutton(
            master=self.__screenmode_frame, text="Window", value=False, variable=self._fullscreen
        ).grid(row=0, column=3, sticky=tk.W)
        self.__res_frame.grid(column=0, row=0, padx=5, pady=2)
        self.__screenmode_frame.grid(column=0, row=1, padx=5, pady=2)


class GUISWRenderSet(GUIOpenGLSet):
    def __init__(self, master, **kwargs):
        super().__init__(master=master, **kwargs)
        self._no_fsdesktop = tk.BooleanVar()
        self._no_fsdesktop.set(not Shell.fsdesktop)
        self._res_x.set(Shell.res_x)
        self._res_y.set(Shell.res_y)
        self._fullscreen.set(Shell.fullscreen)
        self._add_widgets()

    def _add_widgets(self):
        tk.Checkbutton(
            master=self, text="Disable fullscreen desktop mode", variable=self._no_fsdesktop
        ).grid(row=2, column=0, sticky=tk.W)

    def apply(self):
        Shell.fsdesktop = not self._no_fsdesktop.get()
        Shell.fullscreen = self._fullscreen.get()
        Shell.res_x = self._res_x.get()
        Shell.res_y = self._res_y.get()


class GUIDropdown(tk.OptionMenu):
    def __init__(self, gamemgr: Shell, master, var: tk.StringVar, var_list, *args):
        super().__init__(master, var, *var_list, *args)
        self._master = master
        self._gamemgr = gamemgr
        self._var = var
        self._var.trace_add("write", self.pass_var_index)

    def pass_var_index(self, *a):
        return


class GUIDropdownSkill(GUIDropdown):
    def __init__(self, gamemgr: Shell, master, skill_var, *args):
        super().__init__(gamemgr, master, skill_var, sh.skill_list, *args)

    def pass_var_index(self, *a):
        self._gamemgr.skill_index = sh.skill_list.index(self._var.get())


class GUIDropdownComplevel(GUIDropdown):
    def __init__(self, gamemgr: Shell, master, comp_var, *args):
        super().__init__(gamemgr, master, comp_var, sh.compat_list, *args)

    def pass_var_index(self, *a):
        self._gamemgr.comp_index = sh.compat_list.index(self._var.get())


class GUIDropdownIWAD(GUIDropdown):
    def __init__(self, gamemgr: Shell, master, iwad_var, *args):
        super().__init__(gamemgr, master, iwad_var, sh.iwad_list, *args)
        self.ultdoom_maplist = tk.BooleanVar()
        self.__set_maplist_style()

    def pass_var_index(self, *a):
        self._gamemgr.iwad_index = sh.iwad_list.index(self._var.get())
        self.__set_maplist_style()

    def __set_maplist_style(self):
        current = self._var.get()
        self.ultdoom_maplist.set(True) if current == "DOOM.WAD" else self.ultdoom_maplist.set(False)


class GUIDropdownUltDoomMaps(GUIDropdown):
    def __init__(self, gamemgr: Shell, master, map_ult_var, *args):
        super().__init__(gamemgr, master, map_ult_var, sh.ultimate_levels, *args)

    def pass_var_index(self, *a):
        self._gamemgr.level_index = sh.ultimate_levels.index(self._var.get())


class GUIDropdownDoom2Maps(GUIDropdown):
    def __init__(self, gamemgr: Shell, master, map_doom2_var, *args):
        super().__init__(gamemgr, master, map_doom2_var, sh.doom2_levels, *args)

    def pass_var_index(self, *a):
        self._gamemgr.level_index = sh.doom2_levels.index(self._var.get())


class GUIIwadLevelMenus(tk.Frame):
    def __init__(self, custommgr: ShellCustom, master, **kwargs):
        super().__init__(master=master, **kwargs)
        self.__custommgr = custommgr
        self.__iwad = tk.StringVar(self)
        self.__map_ult = tk.StringVar(self)
        self.__map_doom2 = tk.StringVar(self)
        self.__menu_ult_maps = GUIDropdownUltDoomMaps(self.__custommgr, self, self.__map_ult)
        self.__menu_doom2_maps = GUIDropdownDoom2Maps(self.__custommgr, self, self.__map_doom2)
        self.__menu_iwad = GUIDropdownIWAD(self.__custommgr, self, self.__iwad)
        self.__ultdoom_maplist = self.__menu_iwad.ultdoom_maplist
        self.__ultdoom_maplist.trace_add("write", self.__toggle_map_menu)
        self.__deploy_widgets()
        # self.update_widget_state()

    def __deploy_widgets(self):
        tk.Label(master=self, text="IWAD:").grid(row=0, column=0)
        tk.Label(master=self, text="Map:").grid(row=0, column=1)
        self.__menu_iwad.grid(row=1, column=0, padx=10)
        self.__menu_ult_maps.grid(row=1, column=1, padx=15)
        self.__menu_doom2_maps.grid(row=1, column=1, padx=15)

    def __toggle_map_menu(self, *args):
        if self.__ultdoom_maplist.get():
            self.__menu_ult_maps.grid()
            self.__menu_doom2_maps.grid_remove()
            self.__menu_ult_maps.pass_var_index()
        else:
            self.__menu_ult_maps.grid_remove()
            self.__menu_doom2_maps.grid()
            self.__menu_doom2_maps.pass_var_index()

    def update_widget_state(self, *args):
        self.__map_ult.set(sh.ultimate_levels[self.__custommgr.level_index])
        if self.__custommgr.level_index < len(sh.doom2_levels):
            self.__map_doom2.set(sh.doom2_levels[self.__custommgr.level_index])
        else:
            self.__map_doom2.set(sh.doom2_levels[0])
        self.__iwad.set(sh.iwad_list[self.__custommgr.iwad_index])


class GUITabVanilla(tk.Frame):
    def __init__(self, gamemgr: Shell, master, **kwargs):
        super().__init__(master=master, **kwargs)
        self.__gamemgr = gamemgr
        self.__game = tk.StringVar(self)
        self.__skill = tk.StringVar(self)
        self.__levels = tk.StringVar(self)
        self.__level_list = tk.Listbox(
            master=self, selectmode=tk.SINGLE, listvariable=self.__levels, exportselection=0,
            height=16, width=16
        )
        self.__scroll = tk.Scrollbar(
            master=self, command=self.__level_list.yview, orient=tk.VERTICAL
        )
        self.__game.set(self.__gamemgr.game)
        self.__skill.set(sh.skill_list[self.__gamemgr.skill_index])
        self.__deploy_widgets()

    def __deploy_widgets(self):
        self.__deploy_radiobuttons()
        self.__deploy_level_list()
        tk.Label(master=self, text="Skill:").grid(column=0, row=7)
        GUIDropdownSkill(self.__gamemgr, self, self.__skill).grid(column=0, row=8)
        tk.Button(
            master=self, text="Play!", command=self.__gamemgr.start_game, width=12
        ).grid(row=9, column=0, pady=5)

    def __deploy_radiobuttons(self):
        tk.Label(master=self, text="Select Game").grid(column=0, row=0)
        options = [tk.Radiobutton(master=self, value=game, text=sh.games[game]) for game in sh.games]
        for i, radiobutton in enumerate(options):
            radiobutton.configure(variable=self.__game, command=self.__pass_game)
            radiobutton.grid(column=0, columnspan=1, row=i + 1, sticky=tk.W + tk.E, padx=15)

    def __deploy_level_list(self):
        tk.Label(master=self, text="Select Level").grid(column=1, row=0, sticky=tk.W + tk.E)
        self.__level_list.grid(column=1, row=1, rowspan=10, sticky=tk.E)
        self.__scroll.grid(column=2, row=1, rowspan=10, sticky=tk.N + tk.S + tk.E)
        self.__level_list.configure(yscrollcommand=self.__scroll.set)
        self.__level_list.bind("<<ListboxSelect>>", self.__pass_level_index)
        self.__refresh_level_list()

    def __refresh_level_list(self):
        self.__levels.set(' '.join(sh.level_lists[self.__gamemgr.game]))
        self.__level_list.select_clear(0, tk.END)
        self.__level_list.select_set(0)
        self.__level_list.event_generate("<<ListboxSelect>>")

    def __pass_game(self):
        self.__gamemgr.game = self.__game.get()
        self.__refresh_level_list()

    def __pass_level_index(self, evt):
        # print(evt)
        index = self.__level_list.curselection()
        self.__gamemgr.level_index = index[0] if bool(index) else 0


class GUITabCustom(tk.Frame):
    def __init__(self, custommgr: ShellCustom, master, **kwargs):
        super().__init__(master=master, **kwargs)
        self.__custommgr = custommgr
        self.__skill = tk.StringVar(self)
        self.__complevel = tk.StringVar(self)
        self.__fast = tk.BooleanVar(self)
        self.__resp = tk.BooleanVar(self)
        self.__cmds = tk.StringVar(self)
        self.__files_select = GUIFileSelect(self.__custommgr, self)
        self.__iwad_panel = GUIIwadLevelMenus(self.__custommgr, self, bd=2, relief=tk.GROOVE)
        self.__demo_panel = GUIDemoOptions(self.__custommgr, self, bd=2, relief=tk.GROOVE)
        self.__deploy_widgets()
        self.__fast.trace_add("write", lambda *a: setattr(self.__custommgr, "fast", self.__fast.get()))
        self.__resp.trace_add("write", lambda *a: setattr(self.__custommgr, "respawn", self.__resp.get()))
        self.__cmds.trace_add("write", lambda *a: setattr(self.__custommgr, "cmdline", self.__cmds.get()))

    def __deploy_widgets(self):
        self.__files_select.grid(row=0, column=0, rowspan=11, sticky=tk.N + tk.W)
        ttk.Separator(self, orient=tk.VERTICAL).grid(column=1, row=0, rowspan=11, sticky=tk.N+tk.S)
        self.__iwad_panel.grid(row=0, column=2, columnspan=2, pady=2)
        tk.Label(master=self, text="Skill:").grid(row=2, column=2, columnspan=2)
        GUIDropdownSkill(self.__custommgr, self, self.__skill).grid(row=3, column=2, columnspan=2)
        tk.Label(master=self, text="Compatibility mode:").grid(row=4, column=2, columnspan=2)
        GUIDropdownComplevel(self.__custommgr, self, self.__complevel).grid(row=5, column=2, columnspan=2)
        tk.Checkbutton(master=self, text="Fast monsters", variable=self.__fast).grid(row=6, column=2)
        tk.Checkbutton(master=self, text="Respawning monsters", variable=self.__resp).grid(row=6, column=3)
        self.__demo_panel.grid(row=7, column=2, columnspan=2, pady=6, padx=5)
        tk.Label(master=self, text="Additional parameters:").grid(row=8, column=2, columnspan=2)
        tk.Entry(master=self, textvariable=self.__cmds, width=40).grid(row=9, column=2, columnspan=2)
        tk.Button(
            master=self, text="Play!", command=self.__custommgr.start_game, width=12
        ).grid(row=10, column=2, columnspan=2, pady=5)
        # self.update_widget_state()

    def update_widget_state(self, *args):
        self.__skill.set(sh.skill_list[self.__custommgr.skill_index])
        self.__complevel.set(sh.compat_list[self.__custommgr.comp_index])
        self.__fast.set(self.__custommgr.fast)
        self.__resp.set(self.__custommgr.respawn)
        self.__cmds.set(self.__custommgr.cmdline)
        self.__files_select.update_widget_state()
        self.__iwad_panel.update_widget_state()
        self.__demo_panel.update_widget_state()


class GUIFileSelect(tk.Frame):
    def __init__(self, custommgr: ShellCustom, master, **kwargs):
        super().__init__(master=master, **kwargs)
        self.__custommgr = custommgr
        self.__pwaddir_list = []
        self.__file_list = tk.Listbox(master=self, selectmode=tk.MULTIPLE, exportselection=0, height=18, width=24)
        self.__file_list.bind("<<ListboxSelect>>", self.__pass_files)
        self.__load_order = tk.StringVar(self)
        self.__load_order_widget = tk.Message(
            master=self, textvariable=self.__load_order, justify=tk.CENTER,
            bd=2, width=120, anchor=tk.W
        )
        self.__listscroll = tk.Scrollbar(master=self, command=self.__file_list.yview, orient=tk.VERTICAL)
        self.__button_frame = tk.Frame(master=self)
        self.__deploy_widgets()
        # self.update_widget_state()

    def __deploy_widgets(self):
        self.__file_list.grid(row=1, column=1, rowspan=2,)
        self.__file_list.configure(yscrollcommand=self.__listscroll.set)
        self.__listscroll.grid(row=1, column=0, rowspan=2, sticky=tk.N + tk.S + tk.E)
        self.__load_order_widget.grid(row=1, column=2, sticky=tk.N, padx=10)
        tk.Label(master=self, text="Select custom files").grid(row=0, column=1)
        tk.Label(master=self, text="Load order:").grid(row=0, column=2)
        tk.Button(
            master=self.__button_frame, text="Refresh list", command=self.update_widget_state
        ).grid(row=0, column=0, padx=10)
        tk.Button(master=self.__button_frame, text="Clear all", command=self.__clear).grid(row=0, column=1, padx=10)
        self.__button_frame.grid(row=3, column=0, columnspan=3, pady=5)
        self.columnconfigure(2, minsize=160)

    def update_widget_state(self, *args):
        self.__pwaddir_list = [wad for wad in self.__match_extension("*.wad")]
        self.__pwaddir_list.extend([deh for deh in self.__match_extension("*.deh")])
        self.__pwaddir_list.extend([bex for bex in self.__match_extension("*.bex")])
        self.__pwaddir_list = sorted(self.__pwaddir_list, key=lambda name: name.lower())
        self.__file_list.delete(0, tk.END)
        for i, file in enumerate(self.__pwaddir_list):
            self.__file_list.insert(i, file)
        self.__sync_selection()

    def __match_extension(self, extension: str):
        for file in os.listdir(Shell.pwadpath):
            if fn.fnmatch(file, extension):
                yield file

    def __pass_files(self, evt):
        # print(evt)
        selection = self.__file_list.curselection()
        new_list = [self.__pwaddir_list[i] for i in selection] if bool(selection) else []
        added = [item for item in new_list if item not in self.__custommgr.files]
        if not bool(added):
            self.__custommgr.files = [item for item in self.__custommgr.files if item in new_list]
        else:
            self.__custommgr.files.extend(added)
        self.__load_order_upd()

    def __sync_selection(self):
        if bool(self.__custommgr.files):
            self.__custommgr.files = [item for item in self.__custommgr.files if item in self.__pwaddir_list]
            for item in self.__custommgr.files:
                self.__file_list.select_set(self.__pwaddir_list.index(item))
            if bool(self.__file_list.curselection()):
                self.__file_list.see(self.__file_list.curselection()[0])
        self.__load_order_upd()

    def __clear(self):
        self.__file_list.select_clear(0, tk.END)
        self.__custommgr.files = []
        self.__load_order_upd()

    def __load_order_upd(self):
        self.__load_order.set('\n'.join(self.__custommgr.files))


class GUIDemoOptions(tk.Frame):
    def __init__(self, custommgr: ShellCustom, master, **kwargs):
        super().__init__(master=master, **kwargs)
        self.__custommgr = custommgr
        self.__record_demo = tk.BooleanVar(self)
        self.__record_demo.set(self.__custommgr.demorec)
        self.__record_demo_name = tk.StringVar(self)
        self.__frame_rec = tk.Frame(self)
        self.__checkbox_rec = tk.Checkbutton(self.__frame_rec, text="Record demo:", variable=self.__record_demo)
        self.__entry_rec = tk.Entry(self.__frame_rec, textvariable=self.__record_demo_name, width=24)
        self.__play_demo = tk.BooleanVar(self)
        self.__play_demo.set(self.__custommgr.demoplay)
        self.__play_demo_name = tk.StringVar(self)
        self.__frame_play = tk.Frame(self)
        self.__checkbox_play = tk.Checkbutton(self.__frame_play, text="Play demo:", variable=self.__play_demo)
        self.__button_play = tk.Button(
            self.__frame_play, textvariable=self.__play_demo_name, width=25, command=self.__ask_demofile
        )
        self.__button_clear = tk.Button(self.__frame_play, text="Clear", command=self.__clear_play_demo)
        self.__play_demo.trace_add("write", self.__pass_demoplay)
        self.__record_demo.trace_add("write", self.__pass_demorec)
        self.__record_demo_name.trace_add(
            "write", lambda *a: setattr(self.__custommgr, "demorec_name", self.__record_demo_name.get())
        )
        self.__deploy_widgets()

    def __deploy_widgets(self):
        self.__checkbox_rec.grid(row=0, column=0, sticky=tk.E)
        self.__entry_rec.grid(row=0, column=1, sticky=tk.W, padx=5)
        self.__frame_rec.grid(row=0, column=0)
        self.__checkbox_play.grid(row=0, column=0, sticky=tk.E)
        self.__button_play.grid(row=0, column=1, sticky=tk.W, padx=3, pady=2)
        self.__button_clear.grid(row=0, column=2, sticky=tk.W, padx=2, pady=2)
        self.__frame_play.grid(row=1, column=0)

    def __demo_mode(self):
        if self.__record_demo.get() and not self.__play_demo.get():
            self.__checkbox_play.configure(state=tk.DISABLED)
            self.__button_play.configure(state=tk.DISABLED)
            self.__button_clear.configure(state=tk.DISABLED)
        elif self.__play_demo.get() and not self.__record_demo.get():
            self.__checkbox_rec.configure(state=tk.DISABLED)
            self.__entry_rec.configure(state=tk.DISABLED)
        else:
            self.__checkbox_play.configure(state=tk.NORMAL)
            self.__button_play.configure(state=tk.NORMAL)
            self.__button_clear.configure(state=tk.NORMAL)
            self.__checkbox_rec.configure(state=tk.NORMAL)
            self.__entry_rec.configure(state=tk.NORMAL)

    def __pass_demorec(self, *args):
        self.__demo_mode()
        self.__custommgr.demorec = self.__record_demo.get()

    def __pass_demoplay(self, *args):
        self.__demo_mode()
        self.__custommgr.demoplay = self.__play_demo.get()

    def __play_demo_name_widget_update(self, dem: str):
        self.__play_demo_name.set("..." + dem[len(dem) - 24:]) if len(dem) > 24 else self.__play_demo_name.set(dem)

    def __ask_demofile(self):
        demo = fd.askopenfilename(
            title="Locate demo to play", initialdir=Shell.demopath,
            filetypes=[("Demo lumps", "*.lmp"), ("All files", "*.*")]
        )
        if bool(demo):
            self.__custommgr.demoplay_name = demo
            self.__play_demo_name_widget_update(demo)

    def __clear_play_demo(self):
        self.__custommgr.demoplay_name = ""
        self.__play_demo_name.set("")

    def update_widget_state(self):
        self.__record_demo.set(self.__custommgr.demorec)
        self.__record_demo_name.set(self.__custommgr.demorec_name)
        self.__play_demo.set(self.__custommgr.demoplay)
        self.__play_demo_name_widget_update(self.__custommgr.demoplay_name)


class GUIMenuBar(tk.Menu):
    def __init__(self, master, inimgr: sh.IniManager, **kwargs):
        super().__init__(master, **kwargs)
        self.__master = master
        self.__ini_mgr = inimgr
        self.__make_savedirs = tk.BooleanVar(self)
        self.__opengl = tk.BooleanVar(self)
        self.__paths_menu = tk.Menu(self, tearoff=0)
        self.__video_menu = tk.Menu(self, tearoff=0)
        self.__presets_menu = tk.Menu(self, tearoff=0)
        self.__help_menu = tk.Menu(self, tearoff=0)
        self.update_state_required = tk.BooleanVar()
        self.update_widget_state()
        self.__deploy_menus()

    def __deploy_menus(self):
        self.__deploy_paths_menu()
        self.__deploy_presets_menu()
        self.__deploy_video_menu()
        self.__help_menu.add_command(
            label="Compatibility hint", command=lambda: GUIPopupHelp(self.master.winfo_toplevel())
        )
        self.add_cascade(label="Files", menu=self.__paths_menu)
        self.add_cascade(label="Video", menu=self.__video_menu)
        self.add_cascade(label="Presets", menu=self.__presets_menu)
        self.add_cascade(label="Help", menu=self.__help_menu)

    def __deploy_paths_menu(self):
        self.__paths_menu.add_command(
            label="IWADs location...", command=DirPath("Locate IWADs folder:", "iwadpath").request
        )
        self.__paths_menu.add_command(
            label="NERVE.WAD location...", command=DirPath("Locate NERVE.WAD folder:", "nrftlpath").request
        )
        self.__paths_menu.add_command(
            label="Master Levels location...", command=DirPath("Locate Master Levels folder:", "mlpath").request
        )
        self.__paths_menu.add_command(label="PWADs location...", command=self.__pwadpath_change)
        self.__paths_menu.add_command(
            label="Saves location...", command=DirPath("Locate save folder:", "iwadpath").request
        )
        self.__paths_menu.add_command(
            label="Config file...", command=FilePath(
                "Select PrBoom+ .cfg file:", "conf", initialdir=".",
                filetypes=[("Config files", "*.cfg"), ("All files", "*.*")]
            ).request
        )
        self.__paths_menu.add_checkbutton(
            label="Auto create save subfolders", variable=self.__make_savedirs,
            command=lambda: setattr(Shell, "make_savedirs", self.__make_savedirs.get())
        )
        self.__paths_menu.add_command(
            label="Demos location...", command=DirPath("Locate demos folder:", "demopath").request
        )
        self.__paths_menu.add_command(
            label="Executables", command=lambda: GUIPopupExeSet(self.__master.winfo_toplevel())
        )
        self.__paths_menu.add_separator()
        self.__paths_menu.add_command(label="Quit", command=self.__exit_app)

    def __deploy_video_menu(self):
        self.__video_menu.add_checkbutton(
            label="Use OpenGL executable", variable=self.__opengl,
            command=lambda: setattr(Shell, "opengl", self.__opengl.get())
        )
        self.__video_menu.add_command(
            label="Screen settings", command=lambda: GUIPopupScreenSet(self.__master.winfo_toplevel())
        )

    def __deploy_presets_menu(self):
        self.__presets_menu.add_command(label="Save current...", command=self.__save)
        self.__presets_menu.add_command(label="Load preset...", command=self.__load)
        self.__presets_menu.add_separator()
        self.__presets_menu.add_command(label="Restore defaults", command=self.__restore_defaults)

    def __pwadpath_change(self):
        DirPath("Locate custom WADs folder:", "pwadpath").request()
        self.update_state_required.set(True)

    def __restore_defaults(self):
        Shell.default_settings()
        self.update_state_required.set(True)

    def __save(self):
        file = fd.asksaveasfilename(
            title="Save current preset as...", initialdir="./inis",
            filetypes=[(".INI config files", "*.ini"), ("All files", "*.*")],
            defaultextension=".ini"
        )
        if bool(file):
            self.__ini_mgr.save(file)

    def __load(self):
        file = fd.askopenfilename(
            title="Select preset to load...", initialdir="./inis",
            filetypes=[(".INI config files", "*.ini"), ("All files", "*.*")]
        )
        if bool(file):
            self.__ini_mgr.load(file)
            self.update_state_required.set(True)

    def __exit_app(self):
        self.__ini_mgr.save()
        self.__master.winfo_toplevel().destroy()

    def update_widget_state(self, *args):
        self.__make_savedirs.set(Shell.make_savedirs)
        self.__opengl.set(Shell.opengl)


class DirPath(object):
    def __init__(self, title: str, attr: str, initialdir=None, obj=Shell):
        self._path = getattr(obj, attr, None) if initialdir is None else initialdir
        self._locate = None
        self._obj = obj
        self._attr = attr
        self._title = title

    def request(self):
        self._locate = fd.askdirectory(title=self._title, initialdir=self._path)
        self._apply()

    def _apply(self):
        if bool(self._locate):
            setattr(self._obj, self._attr, self._locate)


class FilePath(DirPath):
    def __init__(self, title: str, attr: str, filetypes, initialdir=None, obj=Shell):
        super().__init__(title, attr, initialdir, obj)
        self._filetypes = filetypes

    def request(self):
        self._locate = fd.askopenfilename(title=self._title, initialdir=self._path, filetypes=self._filetypes)
        self._apply()


class GUI(tk.Frame):
    def __init__(self, master=None, gamemgr=None, custommgr=None, inimgr=None, **kwargs):
        super().__init__(master=master, **kwargs)
        self.__master = master
        self.__gamemgr = Shell() if gamemgr is None else gamemgr
        self.__custommgr = ShellCustom() if custommgr is None else custommgr
        self.__ini_mgr = sh.IniManager(self.__custommgr) if inimgr is None else inimgr
        self.__menu = GUIMenuBar(self, self.__ini_mgr)
        self.__tabs = ttk.Notebook(master=self)
        self.__tab_vanilla = GUITabVanilla(self.__gamemgr, master=self.__tabs)
        self.__tab_vanilla.pack()
        self.__tab_custom = GUITabCustom(self.__custommgr, master=self.__tabs)
        self.__tab_custom.pack()
        self.__tabs.add(self.__tab_vanilla, text="Official Releases")
        self.__tabs.add(self.__tab_custom, text="Custom Game")
        self.__tabs.tab(0, sticky=tk.N + tk.S)
        self.__tabs.grid()
        self.winfo_toplevel().config(menu=self.__menu)
        self.update_all()
        self.__update_state_required = self.__menu.update_state_required
        self.__update_state_required.trace_add("write", self.update_all)
        self.pack()

    def update_all(self, *args):
        for attr in (a for a in dir(self)):
            item = getattr(self, attr, None)
            if bool(getattr(item, "update_widget_state", None)):
                item.update_widget_state()


if __name__ == '__main__':
    root = MainWindow()
    root.title("PrBoom+ Launcher v0.1beta")
    root.mainloop()
