import configparser
import os
import logging
import json
import re

from io import StringIO

from os import path

logger = logging.getLogger("KlipperScreen.config")

class ConfigError(Exception):
    pass

class KlipperScreenConfig:
    config = None
    configfile_name = "KlipperScreen.conf"
    do_not_edit_line = "#~# --- Do not edit below this line. This section is auto generated --- #~#"
    do_not_edit_prefix = "#~#"

    def __init__(self, configfile, lang=None):
        _ = lang.gettext

        self.configurable_options = [
            {"invert_x": {"section": "main", "name": _("Invert X"), "type": "binary", "value": "False"}},
            {"invert_y": {"section": "main", "name": _("Invert Y"), "type": "binary", "value": "False"}},
            {"invert_z": {"section": "main", "name": _("Invert Z"), "type": "binary", "value": "False"}},
            {"print_estimate_method": {"section": "main", "name": _("Estimated Time Method"), "type": "dropdown",
                "value": "file","options":[
                    {"name": _("File Estimation (default)"), "value": "file"},
                    {"name": _("Duration Only"), "value": "duration"},
                    {"name": _("Filament Used"), "value": "filament"},
                    {"name": _("Slicer"), "value": "slicer"}
            ]}}
            #{"": {"section": "main", "name": _(""), "type": ""}}
        ]

        self.default_config_path = "%s/ks_includes/%s" % (os.getcwd(), self.configfile_name)
        self.config = configparser.ConfigParser()
        self.config_path = self.get_config_file_location(configfile)
        logger.debug("Config path location: %s" % self.config_path)
        self.defined_config = None

        try:
            self.config.read(self.default_config_path)
            if self.config_path != self.default_config_path:
                user_def, saved_def = self.separate_saved_config(self.config_path)
                self.defined_config = configparser.ConfigParser()
                self.defined_config.read_string(user_def)
                self.log_config(self.defined_config)
                self.config.read_string(user_def)
                if saved_def != None:
                    self.config.read_string(saved_def)
        except KeyError:
            raise ConfigError(f"Error reading config: {self.config_path}")

        self.get_menu_items("__main")
        for item in self.configurable_options:
            name = list(item)[0]
            vals = item[name]
            if vals['section'] not in self.config.sections():
                self.config.add_section(vals['section'])
            if name not in list(self.config[vals['section']]):
                self.config.set(vals['section'], name, vals['value'])
        #self.build_main_menu(self.config)

    def separate_saved_config(self, config_path):
        user_def = []
        saved_def = None
        found_saved = False
        if not path.exists(config_path):
            return [None, None]
        with open(config_path) as file:
            for line in file:
                line = line.replace('\n','')
                if line == self.do_not_edit_line:
                    found_saved = True
                    saved_def = []
                    continue
                if found_saved == False:
                    user_def.append(line.replace('\n',''))
                else:
                    if line.startswith(self.do_not_edit_prefix):
                        saved_def.append(line[(len(self.do_not_edit_prefix)+1):])
        return ["\n".join(user_def), None if saved_def == None else "\n".join(saved_def)]

    def get_config_file_location(self, file):
        if not path.exists(file):
            file = "%s/%s" % (os.getcwd(), self.configfile_name)
            if not path.exists(file):
                file = self.default_config_path

        logger.info("Found configuration file at: %s" % file)
        return file

    def get_config(self):
        return self.config

    def get_configurable_options(self):
        return self.configurable_options

    def get_main_config(self):
        return self.config['main']

    def get_main_config_option(self, option, default=None):
        return self.config['main'].get(option, default)

    def get_menu_items(self, menu="__main", subsection=""):
        if subsection != "":
            subsection = subsection + " "
        index = "menu %s %s" % (menu, subsection)
        items = [i[len(index):] for i in self.config.sections() if i.startswith(index)]
        menu_items = []
        for item in items:
            split = item.split()
            if len(split) == 1:
                menu_items.append(self._build_menu_item(menu, index + item))

        return menu_items

    def get_menu_name(self, menu="__main", subsection=""):
        name = ("menu %s %s" % (menu, subsection)) if subsection != "" else ("menu %s" % menu)
        if name not in self.config:
            return False
        return self.config[name].get('name')


    def get_preheat_options(self):
        index = "preheat "
        items = [i[len(index):] for i in self.config.sections() if i.startswith(index)]

        preheat_options = {}
        for item in items:
            preheat_options[item] = self._build_preheat_item(index + item)

        return preheat_options

    def get_printer_power_name(self):
        return self.config['settings'].get("printer_power_name", "printer")

    def get_user_saved_config(self):
        if self.config_path != self.default_config_path:
            print("Get")

    def save_user_config_options(self):
        save_config = configparser.ConfigParser()
        for item in self.configurable_options:
            name = list(item)[0]
            opt = item[name]
            curval = self.config[opt['section']].get(name)
            if curval != opt["value"] or (
                    self.defined_config != None and opt['section'] in self.defined_config.sections() and
                    self.defined_config[opt['section']].get(name,None) not in (None, curval)):
                if opt['section'] not in save_config.sections():
                    save_config.add_section(opt['section'])
                save_config.set(opt['section'], name, str(curval))

        if "displayed_macros" in self.config.sections():
                for item in self.config.options('displayed_macros'):
                    value = self.config['displayed_macros'].getboolean(item, fallback=True)
                    if value == False or (self.defined_config != None and
                            "displayed_macros" in self.defined_config.sections() and
                            self.defined_config['displayed_macros'].getboolean(item, fallback=True) == False and
                            self.defined_config['displayed_macros'].getboolean(item, fallback=True) != value):
                        if "displayed_macros" not in save_config.sections():
                            save_config.add_section("displayed_macros")
                        save_config.set("displayed_macros", item, str(value))

        save_output = self._build_config_string(save_config).split("\n")
        for i in range(len(save_output)):
            save_output[i] = "%s %s" % (self.do_not_edit_prefix, save_output[i])

        if self.config_path == self.default_config_path:
            user_def = ""
            saved_def = None
        else:
            user_def, saved_def = self.separate_saved_config(self.config_path)

        extra_lb = "\n" if saved_def != None else ""
        contents = "%s\n%s%s\n%s\n%s\n%s\n" % (user_def, self.do_not_edit_line, extra_lb,
            self.do_not_edit_prefix, "\n".join(save_output), self.do_not_edit_prefix)

        if self.config_path != self.default_config_path:
            path = self.config_path
        else:
            path =  os.path.expanduser("~/KlipperScreen.conf")

        try:
            file = open(path, 'w')
            file.write(contents)
            file.close()
        except:
            logger.error("Error writing configuration file")

    def set(self, section, name, value):
        self.config.set(section, name, value)


    def log_config(self, config):
        lines = [
            " "
            "===== Config File =====",
            re.sub(
                r'(moonraker_api_key\s*=\s*\S+)',
                'moonraker_api_key = [redacted]',
                self._build_config_string(config)
            ),
            "======================="
        ]
        logger.info("\n".join(lines))

    def _build_config_string(self, config):
        sfile = StringIO()
        config.write(sfile)
        sfile.seek(0)
        return sfile.read().strip()

    def _build_menu_item(self, menu, name):
        if name not in self.config:
            return False
        cfg = self.config[name]
        item = {
            "name": cfg.get("name"),
            "icon": cfg.get("icon"),
            "panel": cfg.get("panel", False),
            "method": cfg.get("method", False),
            "confirm": cfg.get("confirm", False),
            "enable": cfg.get("enable", True)
        }

        try:
            item["params"] = json.loads(cfg.get("params", "{}"))
        except:
            logger.debug("Unable to parse parameters for [%s]" % name)
            item["params"] = {}

        return {name[(len(menu) + 6):]: item}

    def _build_preheat_item(self, name):
        if name not in self.config:
            return False
        cfg = self.config[name]
        item = {
            "extruder": cfg.getint("extruder", 0),
            "bed": cfg.getint("bed", 0)
        }
        return item
