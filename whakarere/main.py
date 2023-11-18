# MIT License
#
# Copyright (c) 2023 Thiago Fernandes
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# SPDX-License-Identifier: MIT

import subprocess, threading, os, sys, gi, traceback, argparse, json
from time import sleep

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from whakarere.windows.whakarere import WhakarereWindow
from gi.repository import Gio, Adw, Gtk, Gdk

# Define the path to your icons
icons_directory = f'/app/share/icons/hicolor'

# Get the default icon theme and append your custom icon directory
icon_theme = Gtk.IconTheme.get_for_display(Gdk.Display.get_default())
icon_theme.add_search_path(icons_directory)

class WhakarereApplication(Adw.Application):
    def __init__(self, debug=False, dev=False):
        super().__init__(application_id='com.mudeprolinux.whakarere',
                         flags=Gio.ApplicationFlags.DEFAULT_FLAGS)
        self.debug = debug
        self.dev = dev
        self.window = None

    def do_activate(self):
        self.window = self.props.active_window
        if not self.window:
            self.window = WhakarereWindow(self, debug=self.debug, dev=self.dev)
        self.window.present()

    def do_startup(self):
        Adw.Application.do_startup(self)
        Adw.init()  # Initialize libadwaita

def main():
    if not os.path.exists(os.path.expanduser("~/.config/whakarere/")):
        print('Creating whakarere config directory')
        os.makedirs(os.path.dirname(os.path.expanduser("~/.config/whakarere/")), exist_ok=True)

    if not os.path.exists(os.path.expanduser("~/.config/whakarere/config.json")):
        os.makedirs(os.path.dirname(os.path.expanduser("~/.config/whakarere/config.json")), exist_ok=True)
        with open(os.path.expanduser("~/.config/whakarere/config.json"), 'w') as config_file:
            json.dump({}, config_file)

    if not os.path.exists(os.path.expanduser("~/.config/whakarere/sessions")):
        os.makedirs(os.path.dirname(os.path.expanduser("~/.config/whakarere/sessions/")), exist_ok=True)

    if not os.path.exists(os.path.expanduser("~/.config/whakarere/")):
        print('Whakaere config directory not found')
        
    parser = argparse.ArgumentParser(description='Whakarere Application')
    parser.add_argument('--debug', action='store_true', help='Debug mode enabled')
    parser.add_argument('--dev', action='store_true', help='Running in development mode')
    args = parser.parse_args()
    
    if args.debug:
        print('Debug mode enabled')
        debug = True
    else:
        debug = False

    if args.dev:
        print('Running in development mode')
        dev = True
    else:
        dev = False
        thread = threading.Thread(target=run_whatsapp_manager)
        thread.start()
        sleep(1)
    
    app = WhakarereApplication(debug=debug, dev=dev)
    app.run(None)
    
def run_whatsapp_manager():
    original_dir = os.getcwd()
    os.chdir('/app/lib/python3.11/site-packages/whakarere/')
    subprocess.run(['./whakarere-api'])

if __name__ == "__main__":
    main()