# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2022 skelly37
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

from abc import ABCMeta, abstractmethod
import concurrent.futures
import os
from tempfile import NamedTemporaryFile
from typing import (
    List,
    Optional,
)

from picard import (
    PICARD_APP_ID,
    log,
)
from picard.const.sys import (
    IS_MACOS,
    IS_WIN,
)


if IS_WIN:
    import win32pipe  # type: ignore
    import win32file  # type: ignore
    from pywintypes import error as WinApiError  # type: ignore


class PipeError(Exception):
    MESSAGE = None

    def __init__(self, *messages):
        if self.MESSAGE:
            self.messages = (self.MESSAGE,) + tuple(messages)
        else:
            self.messages = tuple(messages)

    def __str__(self):
        messages_str = "\n  ".join(str(m) for m in self.messages)
        if not messages_str:
            messages_str = "unknown"
        return f"ERROR: {messages_str}"


class PipeErrorInvalidArgs(PipeError):
    MESSAGE = "Pipe() args argument has to be iterable"


class PipeErrorInvalidAppData(PipeError):
    MESSAGE = "Pipe() app_name and app_version arguments have to be str"


class PipeErrorNotFound(PipeError):
    MESSAGE = "Pipe doesn't exist"


class PipeErrorBroken(PipeError):
    MESSAGE = "Pipe is broken"


class PipeErrorInvalidResponse(PipeError):
    MESSAGE = "Invalid response from pipe"


class PipeErrorWin(PipeError):
    MESSAGE = "Windows API error"


class PipeErrorNoPermission(PipeError):
    MESSAGE = "No permissions for creating a pipe"


class PipeErrorNoDestination(PipeError):
    MESSAGE = "No available dirs to place a pipe"


class AbstractPipe(metaclass=ABCMeta):
    NO_RESPONSE_MESSAGE: str = "No response from FIFO"
    MESSAGE_TO_IGNORE: str = "Ignore this message, just testing the pipe"
    TIMEOUT_SECS: float = 1.5

    @classmethod
    @property
    @abstractmethod
    def PIPE_DIRS(cls):
        raise NotImplementedError

    def __init__(self, app_name: str, app_version: str, args=None, forced_path=None):
        if args is None:
            self._args = tuple()
        else:
            try:
                self._args = tuple(args)
            except TypeError as exc:
                raise PipeErrorInvalidArgs(exc) from None

        if not self._args:
            self._args = (self.MESSAGE_TO_IGNORE,)

        if not isinstance(app_name, str) or not isinstance(app_version, str):
            raise PipeErrorInvalidAppData
        elif IS_WIN:
            app_version = app_version.replace(".", "-")

        if forced_path:
            self._paths = (forced_path,)
        elif IS_WIN or os.getenv("HOME"):
            self._paths = self.__generate_filenames(app_name, app_version)
            self.path_was_forced = False
        else:
            self._paths = (NamedTemporaryFile(delete=False).name,)
            self.path_was_forced = True
            log.debug("Pipe path had to be mocked by a temporary file")
        self.is_pipe_owner: bool = False

        self.__thread_pool = concurrent.futures.ThreadPoolExecutor()

    def _remove_temp_attributes(self):
        del self._args
        del self._paths

    def __generate_filenames(self, app_name: str, app_version: str):
        _pipe_names = []

        for dir in self.PIPE_DIRS:
            if dir:
                _pipe_names.append(os.path.join(os.path.expanduser(dir),
                                                        f"{app_name}_v{app_version}_pipe_file"))

        if _pipe_names:
            return _pipe_names

        raise PipeErrorNoDestination

    def _reader(self) -> str:
        raise NotImplementedError()

    def _sender(self, message) -> bool:
        raise NotImplementedError()

    def read_from_pipe(self, timeout_secs: Optional[float] = None) -> List[str]:
        if timeout_secs is None:
            timeout_secs = self.TIMEOUT_SECS

        reader = self.__thread_pool.submit(self._reader)
        out = []

        try:
            res = reader.result(timeout=timeout_secs)
            if res:
                res = res.split("\n")
                for r in res:
                    if res == self.MESSAGE_TO_IGNORE:
                        out = []
                        break
                    elif r:
                        out.append(r)

        except concurrent.futures._base.TimeoutError:
            # hacky way to kill the file-opening loop
            self.send_to_pipe(self.MESSAGE_TO_IGNORE)

        if out:
            return out

        return [self.NO_RESPONSE_MESSAGE]

    def send_to_pipe(self, message: str, timeout_secs: Optional[float] = None) -> bool:
        if timeout_secs is None:
            timeout_secs = self.TIMEOUT_SECS

        # we're sending only filepaths, so it's safe to append newline
        # this newline helps with handling collisions of messages
        message += "\n"

        sender = self.__thread_pool.submit(self._sender, message)

        try:
            if sender.result(timeout=timeout_secs):
                return True
        except concurrent.futures._base.TimeoutError:
            # hacky way to kill the sender
            self.read_from_pipe()

        return False


class UnixPipe(AbstractPipe):

    PIPE_DIRS = (
        os.getenv('XDG_RUNTIME_DIR'),
        "~/.config/MusicBrainz/Picard/pipes/",
    )

    def __init__(self, app_name: str, app_version: str, args=None, forced_path=None):
        super().__init__(app_name, app_version, args, forced_path)

        for path in self._paths:
            self.path = path
            for arg in self._args:
                if not self.send_to_pipe(arg):
                    self.__create_pipe()
                    break
            if self.path:
                break

        if not self.path:
            raise PipeErrorNoPermission
        else:
            log.debug("Using pipe: %r", self.path)

        self._remove_temp_attributes()

    def __create_pipe(self) -> None:
        try:
            try:
                # just to be sure that there's no broken pipe left
                os.unlink(self.path)
            except FileNotFoundError:
                pass
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            os.mkfifo(self.path)
            self.is_pipe_owner = True
        except PermissionError:
            self.path = ""

    def _sender(self, message: str) -> bool:
        if not os.path.exists(self.path):
            return False

        with open(self.path, 'a') as fifo:
            fifo.write(message)
        return True

    def _reader(self) -> str:
        response: str = ""
        while not response:
            try:
                with open(self.path, 'r') as fifo:
                    response = fifo.read().strip()
            except FileNotFoundError:
                raise PipeErrorNotFound from None

        return response or self.NO_RESPONSE_MESSAGE


class MacOSPipe(UnixPipe):
    PIPE_DIRS = (os.path.join("~/Library/Application Support/", PICARD_APP_ID),)


class WinPipe(AbstractPipe):
    # win32pipe.CreateNamedPipe
    # more about the arguments: https://docs.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-createnamedpipea
    __MAX_INSTANCES: int = 1
    __BUFFER_SIZE: int = 65536

    # timeout doesn't really matter, concurrent.futures ensures that connections are closed in declared time
    # the value is in milliseconds
    __DEFAULT_TIMEOUT: int = 300

    # win32file.CreateFile
    # more about the arguments: http://timgolden.me.uk/pywin32-docs/win32file__CreateFile_meth.html
    __SHARE_MODE: int = 0
    __FLAGS_AND_ATTRIBUTES: int = 0

    # pywintypes.error error codes
    # more about the error codes: https://docs.microsoft.com/en-us/openspecs/windows_protocols/ms-erref/18d8fbe8-a967-4f1c-ae50-99ca8e491d2d
    __FILE_NOT_FOUND_ERROR_CODE: int = 2
    __BROKEN_PIPE_ERROR_CODE: int = 109

    PIPE_DIRS = ("\\\\.\\pipe\\",)

    def __init__(self, app_name: str, app_version: str, args=None, forced_path=None):
        super().__init__(app_name, app_version, args, forced_path)

        for path in self._paths:
            self.path = path
            for arg in self._args:
                if not self.send_to_pipe(arg):
                    self.is_pipe_owner = True
                    break

        log.debug("Using pipe: %r", self.path)
        self._remove_temp_attributes()

    def _sender(self, message: str) -> bool:
        pipe = win32pipe.CreateNamedPipe(
            self.path,
            win32pipe.PIPE_ACCESS_DUPLEX,
            win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_WAIT,
            self.__MAX_INSTANCES,
            self.__BUFFER_SIZE,
            self.__BUFFER_SIZE,
            self.__DEFAULT_TIMEOUT,
            None)
        try:
            win32pipe.ConnectNamedPipe(pipe, None)
            win32file.WriteFile(pipe, str.encode(message))
        finally:
            win32file.CloseHandle(pipe)

        return True

    def _reader(self) -> str:
        response = ""  # type: ignore

        try:
            pipe = win32file.CreateFile(
                self.path,
                win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                self.__SHARE_MODE,
                None,
                win32file.OPEN_EXISTING,
                self.__FLAGS_AND_ATTRIBUTES,
                None
            )
            while not response:
                response = win32file.ReadFile(pipe, self.__BUFFER_SIZE)

        except WinApiError as err:
            if err.winerror == self.__FILE_NOT_FOUND_ERROR_CODE:
                raise PipeErrorNotFound from None
            elif err.winerror == self.__BROKEN_PIPE_ERROR_CODE:
                raise PipeErrorBroken from None
            else:
                raise PipeErrorWin(f"{err.winerror}; {err.funcname}; {err.strerror}") from None

        # response[0] stores an exit code while response[1] an actual response
        if response:
            if response[0] == 0:
                return str(response[1].decode("utf-8"))  # type: ignore
            else:
                raise PipeErrorInvalidResponse(response[1].decode('utf-8'))  # type: ignore
        else:
            return self.NO_RESPONSE_MESSAGE


if IS_WIN:
    Pipe = WinPipe
elif IS_MACOS:
    Pipe = MacOSPipe
else:
    Pipe = UnixPipe
