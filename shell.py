import collections
import configparser as cp
import os
import os.path
import subprocess

# Global constants

ULTIMATE = "ultimate"
DOOM2 = "doom2"
PLUTONIA = "plutonia"
TNT = "tnt"
NRFTL = "nrftl"
MASTER = "master"

games = collections.OrderedDict({
    ULTIMATE: "THE ULTIMATE DOOM", DOOM2: "DOOM 2: HELL ON EARTH",
    PLUTONIA: "FINAL DOOM: THE PLUTONIA EXPERIMENT", TNT: "FINAL DOOM: TNT EVILUTION",
    NRFTL: "DOOM 2: NO REST FOR THE LIVING", MASTER: "MASTER LEVELS FOR DOOM 2"
})

iwad_list = ("DOOM.WAD", "DOOM2.WAD", "PLUTONIA.WAD", "TNT.WAD", "freedoom1.wad", "freedoom2.wad")

iwads_with_episodes = ("DOOM.WAD", "freedoom1.wad")

skill_list = (
    "I'm Too Young to Die!", "Hey, Not Too Rough",
    "Hurt Me Plenty", "Ultra-Violence", "Nightmare!"
)

compat_list = (
    "DOOM2 mode (-complevel 2)", "Ultimate DOOM mode (-complevel 3)",
    "Final DOOM mode (-complevel 4)", "BOOM compatible mode (-complevel 9)",
    "MBF compatible mode (-complevel 11)", "Don't set -complevel"
)

master_levels = (
    "ATTACK", "BLACKTWR", "BLOODSEA", "CANYON", "CATWALK", "COMBINE",
    "FISTULA", "GARRISON", "GERYON", "MANOR", "MEPHISTO", "MINOS", "NESSUS",
    "PARADOX", "SUBSPACE", "SUBTERRA", "TEETH", "TEETH2", "TTRAP", "VESPERAS", "VIRGIL"
)

ultimate_levels = (
    "NONE", "E1M1", "E1M2", "E1M3", "E1M4", "E1M5", "E1M6", "E1M7", "E1M8", "E1M9",
    "E2M1", "E2M2", "E2M3", "E2M4", "E2M5", "E2M6", "E2M7", "E2M8", "E2M9",
    "E3M1", "E3M2", "E3M3", "E3M4", "E3M5", "E3M6", "E3M7", "E3M8", "E3M9",
    "E4M1", "E4M2", "E4M3", "E4M4", "E4M5", "E4M6", "E4M7", "E4M8", "E4M9"
)

doom2_levels = (
    "NONE", "MAP1", "MAP2", "MAP3", "MAP4", "MAP5", "MAP6", "MAP7", "MAP8",
    "MAP9", "MAP10", "MAP11", "MAP12", "MAP13", "MAP14", "MAP15", "MAP16",
    "MAP17", "MAP18", "MAP19", "MAP20", "MAP21", "MAP22", "MAP23", "MAP24",
    "MAP25", "MAP26", "MAP27", "MAP28", "MAP29", "MAP30", "MAP31", "MAP32"
)

level_lists = {
    ULTIMATE: ultimate_levels, MASTER: master_levels, DOOM2: doom2_levels,
    PLUTONIA: doom2_levels, TNT: doom2_levels, NRFTL: doom2_levels[1:10]
}


# convert single-number level destinations to Ultimate Doom two-number format
def calculate_ultdoom_warp(i: int) -> tuple:
    return (0, 0) if i == 0 else ((i - 1) // 9 + 1, (i - 1) % 9 + 1)


def wrap(paths: list):
    wrapped = ['"{}"'.format(path) for path in paths]
    return ' '.join(wrapped)


class BaseShell(object):

    def __init__(self):
        self.level_index = 0
        self.skill_index = 2

    @property
    def skill_index(self) -> int:
        return self.__skill_index

    @skill_index.setter
    def skill_index(self, skill: int):
        if 0 <= skill < len(skill_list):
            self.__skill_index = skill

    @property
    def level_index(self) -> int:
        return self.__level_index

    @level_index.setter
    def level_index(self, index: int):
        if 0 <= index < 40:
            self.__level_index = index


class Shell(BaseShell):
    """Store global settings and settings for vanilla game sessions"""

    iwadpath = "."
    mlpath = "./master"
    nrftlpath = "."
    pwadpath = "."
    savepath = "./saves"
    demopath = "."
    make_savedirs = True   # whether to autogenerate save file subfolders for each specific game/mod combination

    prboom = "prboom-plus"  # software renderer executable

    fsdesktop = True
    conf = ""

    def __init__(self):
        super().__init__()
        self.game = ULTIMATE

    @property
    def game(self) -> str:
        return self.__game

    @game.setter
    def game(self, game: str):
        if game in games:
            self.__game = game

    @classmethod
    def default_settings(cls):
        defaults = {
            "prboom": "prboom-plus",
            "glboom": "glboom-plus",
            "iwadpath": ".",
            "mlpath": "./master",
            "nrftlpath": ".",
            "pwadpath": ".",
            "savepath": "./saves",
            "demopath": ".",
            "make_savedirs": True,
            "conf": ""
        }
        for default in defaults:
            setattr(cls, default, defaults[default])

    def start_game(self):
        game_sessions = {
            ULTIMATE: UltimateSession, DOOM2: GameSession, PLUTONIA: PlutoniaSession,
            TNT: TNTSession, NRFTL: NRFTLSession, MASTER: MLSession
        }
        current = game_sessions[self.game]()
        current.launch_params(self.skill_index, self.level_index)
        current.launch()


class ShellCustom(Shell):
    """Store settings for custom game sessions"""

    def __init__(self):
        super().__init__()
        self.comp_index = 0
        self.iwad_index = 1
        self.files = []
        self.fast = False
        self.respawn = False
        self.cmdline = ""
        self.demorec = False
        self.demorec_name = "MyDemo"
        self.demoplay = False
        self.demoplay_name = ""

    @property
    def files(self) -> list:
        return self.__files

    @files.setter
    def files(self, files: list):
        self.__files = files

    @property
    def iwad_index(self) -> int:
        return self.__iwad_index

    @iwad_index.setter
    def iwad_index(self, index: int):
        if 0 <= index < len(iwad_list):
            self.__iwad_index = index

    @property
    def comp_index(self) -> int:
        return self.__comp_index

    @comp_index.setter
    def comp_index(self, index: int):
        if 0 <= index < len(compat_list):
            self.__comp_index = index

    def start_game(self):
        if self.demoplay and not self.demorec:
            current = DemoSession(
                self.iwad_index, self.comp_index, self.files,
                self.fast, self.respawn, self.cmdline, self.demoplay_name, True
            )
            # Don't pass the options for skill and level destination when playing a demo
            current.launch()
        elif self.demorec and not self.demoplay:
            current = DemoSession(
                self.iwad_index, self.comp_index, self.files,
                self.fast, self.respawn, self.cmdline, self.demorec_name, False
            )
            current.launch_params(self.skill_index, self.level_index)
            current.launch()
        else:
            current = CustomSession(
                self.iwad_index, self.comp_index, self.files, self.fast, self.respawn, self.cmdline
            )
            current.launch_params(self.skill_index, self.level_index)
            current.launch()


class Session(object):
    """Generate a command line string and launch an executable with it,
    also create a save folder if it doesn't exist yet (the executable doesn't do it currently)"""

    def __init__(
            self, exe_name: str, conf: str, fullscreen: bool,
            res_x: int, res_y: int, fsdesktop=True
    ):
        self._cmd_args = {}
        self.__exe = exe_name
        self.__savedir = ""
        self._arg_conf(conf)
        self._arg_fullscreen(fullscreen)
        self._arg_fsdesktop(fsdesktop)
        self._arg_res(res_x, res_y)

    def _arg_conf(self, conf: str):
        if bool(conf):
            self._cmd_args["conf"] = '{} "{}"'.format("-config", conf)
        else:
            self._cmd_args.pop("conf", None)



    def _arg_res(self, res_x: int, res_y: int):
        if 299 < res_x < 8000 and 199 < res_y < 4500:
            self._cmd_args["x"] = "-width " + str(res_x)
            self._cmd_args["y"] = "-height " + str(res_y)

    def _arg_savedir(self, savedir: str):
        if bool(savedir):
            self._cmd_args["savedir"] = '{} "{}"'.format("-save", savedir)
            self.__savedir = savedir
        else:
            self._cmd_args.pop("savedir", None)
            self.__savedir = ""

    def _arg_comp(self, comp: int):
        if bool(comp):
            self._cmd_args["comp"] = "-complevel " + str(comp)
        else:
            self._cmd_args.pop("comp", None)

    def _arg_fast(self, fast: bool):
        if fast:
            self._cmd_args["fast"] = "-fast"
        else:
            self._cmd_args.pop("fast", None)

    def _arg_respawn(self, resp: bool):
        if resp:
            self._cmd_args["respawn"] = "-respawn"
        else:
            self._cmd_args.pop("respawn", None)

    def _arg_none(self, resp: bool)
        if none:
            self._cmd_args["none"] = "-nomonsters"
        else
            self._cmd_args.pop("none", None)

    def _arg_warp(self, warp: tuple):
        if len(warp) > 1 and warp[0] != 0:
            arg = "-warp " + str(warp[0])
            if warp[1] != 0:
                arg += " " + str(warp[1])
            self._cmd_args["warp"] = arg
        else:
            self._cmd_args.pop("warp", None)

    def _arg_skill(self, skill: int):
        if 0 < skill < 7:
            self._cmd_args["skill"] = "-skill " + str(skill)

    def _arg_files(self, files: list):
        if bool(files):
            self._cmd_args["files"] = "-file " + wrap(files)
        else:
            self._cmd_args.pop("files", None)

    def _arg_deh(self, deh: str):
        if bool(deh):
            self._cmd_args["deh"] = '{} "{}"'.format("-deh", deh)
        else:
            self._cmd_args.pop("deh", None)

    def _arg_iwad(self, iwad: str):
        self._cmd_args["iwad"] = '{} "{}"'.format("-iwad", iwad)

    def _arg_custom_cmds(self, cmds: str):
        if bool(cmds):
            self._cmd_args["cmds"] = cmds
        else:
            self._cmd_args.pop("cmds", None)

    def _arg_playdemo(self, demo: str):
        if bool(demo):
            self._cmd_args["playdemo"] = '{} "{}"'.format("-playdemo", demo)
        else:
            self._cmd_args.pop("playdemo", None)

    def _arg_recorddemo(self, demo: str):
        if bool(demo):
            self._cmd_args["rec"] = '{} "{}"'.format("-record", demo)
        else:
            self._cmd_args.pop("rec", None)

    def _make_cmdline(self):
        """Assemble a command line starting with the name of an executable"""
        cmdline = [self._cmd_args[arg] for arg in self._cmd_args]
        cmdline.insert(0, self.__exe)
        return ' '.join(cmdline)

    def launch(self):
        if bool(self.__savedir) and not os.path.exists(self.__savedir):
            os.makedirs(self.__savedir)
        print(self._make_cmdline())
        try:
            subprocess.call(self._make_cmdline())
        except FileNotFoundError as err:
            print(err)


class GameSession(Session):
    """A basic game session, which is also vanilla DOOM2 game session"""

    def __init__(self):
        if Shell.prboom
              
        if not Shell.make_savedirs:
            self._arg_savedir(Shell.savepath)
        if Shell.make_savedirs:
            self._arg_savedir("{}/{}".format(Shell.savepath, DOOM2))
        self._arg_iwad('{}/{}'.format(Shell.iwadpath, "DOOM2.WAD"))
        self._arg_comp(2)

    def _skill(self, skill_index, level_index=1):
        # Only pass skill setting when we go to a level, NOT to main menu screen
        if bool(level_index):
            self._arg_skill(skill_index + 1)

    def launch_params(self, skill_index, level_index):
        self._skill(skill_index, level_index)
        self._arg_warp((level_index, 0))


class UltimateSession(GameSession):
    """Vanilla Ultimate Doom game session"""

    def __init__(self):
        super().__init__()
        self._arg_iwad('{}/{}'.format(Shell.iwadpath, "DOOM.WAD"))
        self._arg_comp(3)
        if Shell.make_savedirs:
            self._arg_savedir("{}/{}".format(Shell.savepath, ULTIMATE))

    def launch_params(self, skill_index, level_index):
        self._skill(skill_index, level_index)
        self._arg_warp(calculate_ultdoom_warp(level_index))


class PlutoniaSession(GameSession):
    """Vanilla Final Doom: Plutonia game session"""

    def __init__(self):
        super().__init__()
        self._arg_iwad('{}/{}'.format(Shell.iwadpath, "PLUTONIA.WAD"))
        self._arg_comp(4)
        if Shell.make_savedirs:
            self._arg_savedir("{}/{}".format(Shell.savepath, PLUTONIA))


class TNTSession(GameSession):
    """Vanilla Final Doom: TNT game session"""

    def __init__(self):
        super().__init__()
        self._arg_iwad('{}/{}'.format(Shell.iwadpath, "TNT.WAD"))
        self._arg_comp(4)
        # Always try to load the patch for TNT.WAD
        self._arg_files(['{}/{}'.format(Shell.iwadpath, "tnt31.wad")])
        if Shell.make_savedirs:
            self._arg_savedir("{}/{}".format(Shell.savepath, TNT))


class NRFTLSession(GameSession):
    """No Rest for the Living expansion session.
    Don't allow to launch the game without warping to a level, because
    the startup demo is going to be desynced and look ugly"""

    def __init__(self):
        super().__init__()
        campaign = '{}/{}'.format(Shell.nrftlpath, "NERVE.WAD")
        self._arg_files([campaign])
        if Shell.make_savedirs:
            self._arg_savedir("{}/{}".format(Shell.savepath, NRFTL))


class MLSession(GameSession):
    """Master Levels for Doom 2 expansion session: individual maps are stored in separate
    game files and must be accessed with correct level number"""

    def __init__(self):
        super().__init__()
        # level access
        self.master_warps = (
            (1, 0), (25, 0), (7, 0), (1, 0), (1, 0), (1, 0),
            (1, 0), (1, 0), (8, 0), (1, 0), (7, 0), (5, 0), (7, 0),
            (1, 0), (1, 0), (1, 0), (31, 0), (32, 0), (1, 0), (9, 0), (3, 0)
        )
        if Shell.make_savedirs:
            self._arg_savedir("{}/{}".format(Shell.savepath, MASTER))

    def launch_params(self, skill_index, level_index):
        self._skill(skill_index)
        # handle special case of TEETH2 located in the same file as TEETH
        level = master_levels[level_index] if level_index != 17 else "TEETH"
        file = '{}/{}'.format(Shell.mlpath, level + ".WAD")
        self._arg_files([file])
        self._arg_warp(self.master_warps[level_index])


class CustomSession(GameSession):
    """A game session with various customizable options"""

    def __init__(self, iwad_index: int, comp_index: int, files: list, fast: bool, resp: bool, cmds: str):
        super().__init__()
        self.__iwadname = iwad_list[iwad_index]
        self._arg_iwad('{}/{}'.format(Shell.iwadpath, self.__iwadname))
        self.__complevels = (2, 3, 4, 9, 11, 0)
        self._arg_comp(self.__complevels[comp_index])
        self.__savedir = self.__generate_savedir_name(self.__iwadname)
        # always try to load the patch for TNT.WAD
        self.__files = ['{}/{}'.format(Shell.iwadpath, "tnt31.wad")] if self.__iwadname == "TNT.WAD" else []
        if bool(files):
            dehs = [deh for deh in files if ".deh".lower() in deh.lower() or ".bex".lower() in deh.lower()]
            if bool(dehs):
                # only add a single dehacked patch
                self._arg_deh("{}/{}".format(Shell.pwadpath, dehs[0]))
            wads = [file for file in files if file not in dehs]
            # generate a name for save folder based on the .WAD files in the load order
            self.__savedir = self.__generate_savedir_name(self.__iwadname, wads)
            self.__files.extend(["{}/{}".format(Shell.pwadpath, wad) for wad in wads])
        self._arg_files(self.__files)
        if Shell.make_savedirs:
            self._arg_savedir(self.__savedir)
        self._arg_fast(fast)
        self._arg_respawn(resp)
        self._arg_custom_cmds(cmds)

    def launch_params(self, skill_index, level_index):
        self._skill(skill_index, level_index)
        self._arg_warp(calculate_ultdoom_warp(level_index)) if self.__iwadname in iwads_with_episodes else \
            self._arg_warp((level_index, 0))

    def __generate_savedir_name(self, iwadname, wads=None):
        if wads is None or not bool(wads):
            return "{}/{}_{}".format(Shell.savepath, iwadname.rstrip("wadWAD").rstrip("."), "CustomGame")
        else:
            wadstring = '_'.join([wadname.rstrip("wadWAD").rstrip(".") for wadname in wads])
            wadstring = wadstring[:32] if len(wadstring) > 32 else wadstring
            return "{}/{}_{}".format(Shell.savepath, iwadname.rstrip("wadWAD").rstrip("."), wadstring)


class DemoSession(CustomSession):
    """A custom game with demo recording/playback"""

    def __init__(
            self, iwad_index: int, comp_index: int, files: list,
            fast: bool, resp: bool, cmds: str, demofile: str, demoplay_mode: bool
    ):
        super().__init__(iwad_index, comp_index, files, fast, resp, cmds)
        self.__demoplay_mode = demoplay_mode
        self.__demofile = demofile
        if self.__demoplay_mode:
            self._arg_savedir("")
            self._arg_playdemo(self.__demofile)
        else:
            self._arg_recorddemo('{}/{}.lmp'.format(Shell.demopath, self.__demofile))


class IniManager(object):
    """Save and load global settings and custom game presets"""

    def __init__(self, custommgr: ShellCustom):
        self.INI_DIR = "./inis"
        self.INI_DEFAULT = "launcher.ini"
        self.SECT_GLOB = "GlobalSettings"
        self.SECT_CUSTM = "CustomGame"
        self.__custommgr = custommgr
        self.__ini = cp.ConfigParser()
        self.__ini[self.SECT_GLOB] = {}
        self.__ini[self.SECT_CUSTM] = {}
        if not os.path.exists(self.INI_DIR):
            os.makedirs(self.INI_DIR)
        self.__default_ini_file = '{}/{}'.format(self.INI_DIR, self.INI_DEFAULT)

        self.string_globals = (
            "prboom", "iwadpath", "mlpath", "nrftlpath",
            "pwadpath", "savepath", "demopath", "conf"
        )
        self.bool_globals = ("make_savedirs")
        self.int_custommgr = ("iwad_index", "comp_index", "level_index", "skill_index")
        self.bool_custommgr = ("fast", "respawn", "demorec", "demoplay")
        self.string_custommgr = ("cmdline", "demorec_name", "demoplay_name")

    def save(self, ini_file=None):
        self.__save_section(Shell, self.SECT_GLOB, self.string_globals, self.int_globals, self.bool_globals)
        self.__save_section(
            self.__custommgr, self.SECT_CUSTM, self.string_custommgr, self.int_custommgr, self.bool_custommgr
        )
        self.__ini[self.SECT_CUSTM]["files"] = ';'.join(self.__custommgr.files)
        target = ini_file if bool(ini_file) else self.__default_ini_file
        with open(target, "w") as saved_ini:
            self.__ini.write(saved_ini)

    def load(self, ini_file=None):
        ini_loaded = self.__ini.read(ini_file) if bool(ini_file) else self.__ini.read(self.__default_ini_file)
        if ini_loaded:
            self.__load_section(Shell, self.SECT_GLOB, self.string_globals, self.int_globals, self.bool_globals)
            self.__load_section(
                self.__custommgr, self.SECT_CUSTM, self.string_custommgr, self.int_custommgr, self.bool_custommgr
            )
            files = self.__ini[self.SECT_CUSTM]["files"] if "files" in self.__ini[self.SECT_CUSTM] else []
            self.__custommgr.files = files.split(';') if bool(files) else []

    def __load_section(self, obj, section, string_vars=(), int_vars=(), bool_vars=()):
        temp = [
            {var: self.__ini.getint(section, var) for var in int_vars if var in self.__ini[section]},
            {var: self.__ini.getboolean(section, var) for var in bool_vars if var in self.__ini[section]},
            {var: self.__ini[section][var] for var in string_vars if var in self.__ini[section]}
        ]
        all_vars = {key: dic[key] for dic in temp for key in dic}
        for var in all_vars:
            setattr(obj, var, all_vars[var])

    def __save_section(self, obj, section, *var_lists):
        all_vars = [var for var_list in var_lists for var in var_list]
        for var in all_vars:
            self.__ini[section][var] = str(getattr(obj, var, None))

