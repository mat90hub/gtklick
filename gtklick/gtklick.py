#!/usr/bin/env python
# -*- coding: utf-8 -*-

# gtklick
#
# Copyright (C) 2008  Dominic Sacré  <dominic.sacre@gmx.de>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.


import pygtk
pygtk.require('2.0')
import gtk
import gtk.glade
import gobject

import getopt
import sys
import os.path

import liblo

from klick_backend import *
from gtklick_config import *
from main_window import *
from preferences_dialog import *
from misc import *


help_string = """Usage:
  gtklick [ options ]

Options:
  -o port   specify OSC port of klick instance to connect to
  -h        show this help"""


class GTKlick:
    def __init__(self, args, share_dir):
        # parse command line arguments
        self.klick_port = None
        try:
            r = getopt.getopt(args, 'o:h');
            for opt in r[0]:
                if opt[0] == '-o':
                    self.klick_port = opt[1]
                elif opt[0] == '-h':
                    print help_string
                    sys.exit(0)
        except getopt.GetoptError, e:
            sys.exit(e.msg)

        gtk.gdk.threads_init()

        try:
            self.wtree = gtk.glade.XML(os.path.join(share_dir, 'gtklick.glade'))

            if not self.klick_port:
                # load config from file
                self.config = GTKlickConfig()
                self.config.read()

            # start klick process
            self.klick = KlickBackend(self.klick_port, 'gtklick')

            # the actual windows are created by glade, this basically just connects GUI and OSC callbacks
            self.win = MainWindow(self.wtree, self.klick, self.config)
            self.prefs = PreferencesDialog(self.wtree, self.klick, self.config)

            self.klick.add_method(None, None, self.fallback)

            # wassup?
            self.klick.send('/query')

        except KlickBackendError, e:
            self.error_message(e.msg)
            sys.exit(1)

        # start timer to check if klick is still running
        if self.klick.process:
            self.timer = gobject.timeout_add(1000, weakref_method(self.check_klick))

    def __del__(self):
        if not self.klick_port:
            self.config.write()

    def run(self):
        gtk.main()

    def check_klick(self):
        if not self.klick.check_process():
            self.error_message("klick seems to have been killed, can't continue without it")
            sys.exit(1)
        return True

    def fallback(self, path, args, types, src):
        print "message not handled:", path, args, src.get_url()

    def error_message(self, msg):
        m = gtk.MessageDialog(self.wtree.get_widget('window_main'),
                              0, gtk.MESSAGE_ERROR, gtk.BUTTONS_OK, msg)
        m.set_title("gtklick error")
        m.run()


if __name__ == '__main__':
    app = GTKlick(sys.argv[1:], 'share')
    app.run()