# vim: ft=python fileencoding=utf-8 sts=4 sw=4 et:

# Copyright 2014 Florian Bruhin (The Compiler) <mail@qutebrowser.org>
#
# This file is part of qutebrowser.
#
# qutebrowser is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# qutebrowser is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with qutebrowser.  If not, see <http://www.gnu.org/licenses/>.

"""Parser for line-based configurations like histories."""

import os
import os.path

from PyQt5.QtCore import pyqtSlot

from qutebrowser.utils import log, utils


class LineConfigParser:

    """Parser for configuration files which are simply line-based.

    Attributes:
        data: A list of lines.
        _configdir: The directory to read the config from.
        _configfile: The config file path.
        _fname: Filename of the config.
        _binary: Whether to open the file in binary mode.
    """

    def __init__(self, configdir, fname, limit=None, binary=False):
        """Config constructor.

        Args:
            configdir: Directory to read the config from.
            fname: Filename of the config file.
            limit: Config tuple (section, option) which contains a limit.
            binary: Whether to open the file in binary mode.
        """
        self._configdir = configdir
        self._configfile = os.path.join(self._configdir, fname)
        self._fname = fname
        self._limit = limit
        self._binary = binary
        if not os.path.isfile(self._configfile):
            self.data = []
        else:
            log.init.debug("Reading config from {}".format(self._configfile))
            self.read(self._configfile)

    def __repr__(self):
        return utils.get_repr(self, constructor=True,
                              configdir=self._configdir, fname=self._fname,
                              limit=self._limit, binary=self._binary)

    def __iter__(self):
        """Iterate over the set data."""
        return self.data.__iter__()

    def read(self, filename):
        """Read the data from a file."""
        if self._binary:
            with open(filename, 'rb') as f:
                self.data = [line.rstrip(b'\n') for line in f.readlines()]
        else:
            with open(filename, 'r', encoding='utf-8') as f:
                self.data = [line.rstrip('\n') for line in f.readlines()]

    def write(self, fp, limit=-1):
        """Write the data to a file.

        Args:
            fp: A file object to write the data to.
            limit: How many lines to write, or -1 for no limit.
        """
        if limit == -1:
            data = self.data
        else:
            data = self.data[-limit:]
        if self._binary:
            fp.write(b'\n'.join(data))
        else:
            fp.write('\n'.join(data))

    def save(self):
        """Save the config file."""
        if not self.data:
            log.destroy.debug("No data to save.")
            return
        # We need to import this here because config needs LineConfigParser.
        from qutebrowser.config import config
        limit = -1 if self._limit is None else config.get(*self._limit)
        if limit == 0:
            return
        if not os.path.exists(self._configdir):
            os.makedirs(self._configdir, 0o755)
        log.destroy.debug("Saving config to {}".format(self._configfile))
        if self._binary:
            with open(self._configfile, 'wb') as f:
                self.write(f, limit)
        else:
            with open(self._configfile, 'w', encoding='utf-8') as f:
                self.write(f, limit)

    @pyqtSlot(str, str)
    def on_config_changed(self, section, option):
        """Delete the file if the limit was changed to 0."""
        if self._limit is None:
            return
        # We need to import this here because config needs LineConfigParser.
        from qutebrowser.config import config
        value = config.get(section, option)
        if (section, option) == self._limit and value == 0:
            if os.path.exists(self._configfile):
                os.remove(self._configfile)
