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


import concurrent.futures
import os
from typing import (
    List,
    Optional,
)

from picard import PICARD_APP_ID
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


class Pipe:
    NO_RESPONSE_MESSAGE: str = "No response from FIFO"
    MESSAGE_TO_IGNORE: str = "Ignore this message, just testing the pipe"
    TIMEOUT_SECS: float = 1.5

    PIPE_WIN_DIR = "\\\\.\\pipe\\"
    PIPE_MAC_DIR = os.path.join(os.path.expanduser("~/Library/Application Support/"), PICARD_APP_ID)
    PIPE_UNIX_DIR = os.getenv('XDG_RUNTIME_DIR')
    PIPE_UNIX_FALLBACK_DIR = os.path.expanduser("~/.config/MusicBrainz/Picard/pipes/")

    def __init__(self, app_name: str, app_version: str, args=None):
        if args is None:
            args = tuple()
        else:
            try:
                args = tuple(args)
            except TypeError as exc:
                raise PipeErrorInvalidArgs(exc) from None

        if not args:
            args = (self.MESSAGE_TO_IGNORE,)

        if not isinstance(app_name, str) or not isinstance(app_version, str):
            raise PipeErrorInvalidAppData

        self.__is_mac: bool = IS_MACOS
        self.__is_win: bool = IS_WIN

        # named pipe values needed by windows API
        if self.__is_win:
            # win32pipe.CreateNamedPipe
            # more about the arguments: https://docs.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-createnamedpipea
            self.__MAX_INSTANCES: int = 1
            self.__BUFFER_SIZE: int = 65536
            # timeout doesn't really matter, concurrent.futures ensures that connections are closed in declared time
            # the value is in milliseconds
            self.__DEFAULT_TIMEOUT: int = 300

            # win32file.CreateFile
            # more about the arguments: http://timgolden.me.uk/pywin32-docs/win32file__CreateFile_meth.html
            self.__SHARE_MODE: int = 0
            self.__FLAGS_AND_ATTRIBUTES: int = 0

            # pywintypes.error error codes
            # more about the error codes: https://docs.microsoft.com/en-us/openspecs/windows_protocols/ms-erref/18d8fbe8-a967-4f1c-ae50-99ca8e491d2d
            self.__FILE_NOT_FOUND_ERROR_CODE: int = 2
            self.__BROKEN_PIPE_ERROR_CODE: int = 109

        self.path: str = self.__generate_filename(app_name, app_version)

        self.is_pipe_owner: bool = False

        if self.__is_win:
            for arg in args:
                if not self.send_to_pipe(arg):
                    self.is_pipe_owner = True
                    break
        else:
            try:
                self.__create_unix_pipe()
            except FileExistsError:
                for arg in args:
                    if not self.send_to_pipe(arg):
                        self.__create_unix_pipe()
                        break

    def __generate_filename(self, app_name: str, app_version: str) -> str:
        if self.__is_win:
            app_version = app_version.replace(".", "-")
            self.__pipe_parent_dir = self.PIPE_WIN_DIR
        elif self.__is_mac:
            self.__pipe_parent_dir = self.PIPE_MAC_DIR
        else:
            self.__pipe_parent_dir = self.PIPE_UNIX_DIR
            if not self.__pipe_parent_dir:
                self.__pipe_parent_dir = self.PIPE_UNIX_FALLBACK_DIR

        pipe_name = f"{app_name}_v{app_version}_pipe_file"
        return os.path.join(self.__pipe_parent_dir, pipe_name)

    def __create_unix_pipe(self) -> None:
        try:
            try:
                # just to be sure that there's no broken pipe left
                os.unlink(self.path)
            except FileNotFoundError:
                pass

            os.makedirs(self.__pipe_parent_dir, exist_ok=True)
            os.mkfifo(self.path)
            self.is_pipe_owner = True
        except PermissionError as exc:
            raise PipeErrorNoPermission(exc) from None

    def __win_sender(self, message: str) -> bool:
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

    def __unix_sender(self, message: str) -> bool:
        with open(self.path, 'a') as fifo:
            fifo.write(message)
        return True

    def send_to_pipe(self, message: str, timeout_secs: Optional[float] = None) -> bool:
        if timeout_secs is None:
            timeout_secs = self.TIMEOUT_SECS

        __pool = concurrent.futures.ThreadPoolExecutor()

        # we're sending only filepaths, so it's safe to append newline
        # this newline helps with handling collisions of messages
        message += "\n"

        if self.__is_win:
            sender = __pool.submit(self.__win_sender, message)
        else:
            sender = __pool.submit(self.__unix_sender, message)

        try:
            if sender.result(timeout=timeout_secs):
                return True
        except concurrent.futures._base.TimeoutError:
            # hacky way to kill the sender
            self.read_from_pipe()

        return False

    def read_from_pipe(self, timeout_secs: Optional[float] = None) -> List[str]:
        if timeout_secs is None:
            timeout_secs = self.TIMEOUT_SECS

        __pool = concurrent.futures.ThreadPoolExecutor()

        if self.__is_win:
            reader = __pool.submit(self.__win_reader)
        else:
            reader = __pool.submit(self.__unix_reader)

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

        return [Pipe.NO_RESPONSE_MESSAGE]

    def __win_reader(self) -> str:
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
            return Pipe.NO_RESPONSE_MESSAGE

    def __unix_reader(self) -> str:
        response: str = ""
        while not response:
            try:
                with open(self.path, 'r') as fifo:
                    response = fifo.read().strip()
            except FileNotFoundError:
                raise PipeErrorNotFound from None

        return response or Pipe.NO_RESPONSE_MESSAGE
