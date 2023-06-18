# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2022 Bob Swift
# Copyright (C) 2022 Kamil
# Copyright (C) 2022 Laurent Monin
# Copyright (C) 2022 skelly37
# Copyright (C) 2022-2023 Philipp Wolfer
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


from abc import (
    ABCMeta,
    abstractmethod,
)
import concurrent.futures
import os
from tempfile import NamedTemporaryFile
from typing import (
    Any,
    Iterable,
    List,
    Optional,
    Tuple,
)

from picard import (
    PICARD_APP_ID,
    log,
)
from picard.const.sys import (
    IS_HAIKU,
    IS_MACOS,
    IS_WIN,
)
from picard.util import sanitize_filename


if IS_WIN:
    from pywintypes import error as WinApiError  # type: ignore
    import win32file  # type: ignore
    import win32pipe  # type: ignore


class PipeError(Exception):
    MESSAGE: str = ""

    def __init__(self, *messages):
        if self.MESSAGE:
            self.messages: Tuple[str] = (self.MESSAGE,) + tuple(messages)
        else:
            self.messages: Tuple[str] = tuple(messages)     # type: ignore

    def __str__(self) -> str:
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
    MESSAGE_TO_IGNORE: str = '\0'
    TIMEOUT_SECS: float = 1.5

    @classmethod
    @property
    @abstractmethod
    def PIPE_DIRS(cls):
        """
        Tuple of dirs where pipe could possibly be created

        **Virtual**, implement in child classes
        """
        raise NotImplementedError

    def __init__(self, app_name: str, app_version: str, args: Optional[Iterable[str]] = None,
                 forced_path: Optional[str] = None, identifier: Optional[str] = None):
        """
        :param app_name: (str) Name of the app, included in the pipe name
        :param app_version: (str) Version of the app, included in the pipe name
        :param identifier: (Optional[str]) config file / standalone identifier, included in pipe name
        :param args: (Optional[Iterable[str]]) Will be passed to an existing instance of app if possible
        :param forced_path: (Optional[str]) Testing-purposes only, bypass of no $HOME on testing machines
        """
        if args is None:
            self._args: Tuple[str] = tuple()    # type: ignore
        else:
            try:
                self._args = tuple(args)    # type: ignore
            except TypeError as exc:
                raise PipeErrorInvalidArgs(exc) from None

        if not self._args:
            self._args = (self.MESSAGE_TO_IGNORE,)

        if not isinstance(app_name, str) or not isinstance(app_version, str):
            raise PipeErrorInvalidAppData

        self._identifier = identifier or "main"

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

        # 2 workers for reader
        # 2 workers for sender (they both need a worker to *hacky kill the job*)
        # 2 workers just in case
        #self.__thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=6)

        self.pipe_running = False

        self.unexpected_removal = False

        for path in self._paths:
            self.path = path
            for arg in self._args:
                if not self.send_to_pipe(arg):
                    self.is_pipe_owner = True
                    break
            if self.path:
                log.debug("Using pipe: %r", self.path)
                break

    def _remove_temp_attributes(self) -> None:
        """
        Removing self._args and self._paths when child classes don't need them anymore.

        Should be called by child classes.
        """
        del self._args
        del self._paths

    def __generate_filenames(self, app_name: str, app_version: str) -> List[str]:
        """
        Returns list of paths available for pipe

        :param app_name: (str) Name of the app, included in the pipe name
        :param app_version: (str) Version of the app, included in the pipe name
        :return: List of available pipe paths
        :rtype: List[str]
        """
        _pipe_names = []

        for directory in self.PIPE_DIRS:
            if directory:
                _pipe_names.append(os.path.join(os.path.expanduser(directory),
                                                sanitize_filename(f"{app_name}_v{app_version}_{self._identifier}_pipe_file")))

        if _pipe_names:
            return _pipe_names

        raise PipeErrorNoDestination

    def _reader(self) -> str:
        """
        Listens on the pipe for messages

        **Virtual**, implement in child classes

        :return: What has been read from pipe
        :rtype: str
        """
        raise NotImplementedError()

    def _sender(self, message: str) -> bool:
        """
        Sends message to the pipe

        **Virtual**, implement in child classes

        :param message: (str)
        :return: True if operation went successfully, False otherwise
        :rtype: bool
        """
        raise NotImplementedError()

    def read_from_pipe(self, timeout_secs: Optional[float] = None) -> List[str]:
        """
        Common interface for the custom _reader implementations

        :param timeout_secs: (Optional[float]) Timeout for the function, by default it fallbacks to self.TIMEOUT_SECS
        :return: List of messages or {self.NO_RESPONSE_MESSAGE} (if no messages received)
        :rtype: List[str]
        """
        if timeout_secs is None:
            timeout_secs = self.TIMEOUT_SECS

        executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

        try:
            reader = executor.submit(self._reader)
            # Without this the Python interpreter cannot stop when the user writes an infinite loop
            # Even though all threads in ThreadPoolExecutor are created as daemon threads
            # They are not stopped on Python's shutdown but Python waits for them to stop on their own
            # See https://stackoverflow.com/a/49992422/13160001
            del concurrent.futures.thread._threads_queues[list(executor._threads)[0]]
            res = reader.result(timeout=timeout_secs)
            if res:
                out = [r for r in res.split(self.MESSAGE_TO_IGNORE) if r]
                if out:
                    return out
        except concurrent.futures._base.TimeoutError:
            # hacky way to kill the file-opening loop
            self.send_to_pipe(self.MESSAGE_TO_IGNORE)
        except Exception as e:
            # https://docs.python.org/3/library/concurrent.futures.html#concurrent.futures.Future.result
            # If the call raised an exception, this method will raise the same exception.
            log.error("pipe reader exception: %s", e)
        finally:
            executor.shutdown(wait=False)

        return [self.NO_RESPONSE_MESSAGE]

    def send_to_pipe(self, message: str, timeout_secs: Optional[float] = None) -> bool:
        """
        Common interface for the custom _sender implementations

        :param message: (str) Message that will be sent to the pipe
        :param timeout_secs: (Optional[float]) Timeout for the function, by default it fallbacks to self.TIMEOUT_SECS
        :return: True if operation went successfully, False otherwise
        :rtype: bool
        """
        if timeout_secs is None:
            timeout_secs = self.TIMEOUT_SECS

        executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        try:
            # we're sending only filepaths, so we have to create some kind of separator
            # to avoid any potential conflicts and mixing the data
            sender = executor.submit(self._sender, message + self.MESSAGE_TO_IGNORE)
            del concurrent.futures.thread._threads_queues[list(executor._threads)[0]]
            if sender.result(timeout=timeout_secs):
                return True
        except concurrent.futures._base.TimeoutError:
            if self.pipe_running:
                log.warning("Couldn't send: %r", message)
            # hacky way to kill the sender
            self.read_from_pipe()
        except Exception as e:
            # https://docs.python.org/3/library/concurrent.futures.html#concurrent.futures.Future.result
            # If the call raised an exception, this method will raise the same exception.
            log.error("pipe sender exception: %s", e)
        finally:
            executor.shutdown(wait=False)

        return False

    def stop(self):
        log.debug("Stopping pipe")
        self.pipe_running = False
        self.send_to_pipe(self.MESSAGE_TO_IGNORE)


class UnixPipe(AbstractPipe):

    PIPE_DIRS: Tuple[str] = (
        os.getenv('XDG_RUNTIME_DIR'),
        "~/.config/MusicBrainz/Picard/pipes/",
    )   # type: ignore

    def __init__(self, app_name: str, app_version: str, args: Optional[Iterable[str]] = None,
                 forced_path: Optional[str] = None, identifier: Optional[str] = None):
        super().__init__(app_name, app_version, args, forced_path)

        if not self.path:
            raise PipeErrorNoPermission
        elif self.is_pipe_owner:
            self.__create_pipe()

        self._remove_temp_attributes()

    def __create_pipe(self) -> None:
        """
        Create pipe on Unix, if it doesn't exist
        """
        # setting false to set make it true only when really created
        self.is_pipe_owner = False
        try:
            try:
                # just to be sure that there's no broken pipe left
                os.unlink(self.path)
            except FileNotFoundError:
                pass
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            os.mkfifo(self.path)
            self.is_pipe_owner = True
            log.debug("Pipe successfully created: %r", self.path)
        except PermissionError as e:
            log.warning("Couldn't create pipe: %r (%s)", self.path, e)
            self.path = ""

    def _sender(self, message: str) -> bool:
        if not os.path.exists(self.path):
            return False

        try:
            with open(self.path, 'w') as fifo:
                fifo.write(message)
            return True
        except BrokenPipeError:
            log.warning("BrokenPipeError happened for %r", message)

        return False

    def _reader(self) -> str:
        response: str = ""
        while not response:
            try:
                with open(self.path, 'r') as fifo:
                    response = fifo.read()
            except FileNotFoundError:
                log.error("Pipe file removed unexpectedly")
                self.pipe_running = False
                self.unexpected_removal = True
                raise PipeErrorNotFound from None
            except BrokenPipeError:
                log.warning("BrokenPipeError happened while listening to the pipe")
                break

        return response or self.NO_RESPONSE_MESSAGE


class MacOSPipe(UnixPipe):
    PIPE_DIRS: Tuple[str] = (os.path.join("~/Library/Application Support/", PICARD_APP_ID),)


class HaikuPipe(UnixPipe):
    PIPE_DIRS: Tuple[str] = ("~/config/var/MusicBrainz/Picard/",)


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

    PIPE_DIRS: Tuple[str] = ("\\\\.\\pipe\\",)

    def __init__(self, app_name: str, app_version: str, args: Optional[Iterable[str]] = None,
                 forced_path: Optional[str] = None, identifier: Optional[str] = None):
        # type checking is already enforced in the AbstractPipe
        try:
            app_version = app_version.replace(".", "-")
        except AttributeError:
            pass
        super().__init__(app_name, app_version, args, forced_path)

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
                # we just keep reopening the pipe, nothing wrong is happening
                pass
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
    Pipe: Any = WinPipe
elif IS_MACOS:
    Pipe = MacOSPipe
elif IS_HAIKU:
    Pipe = HaikuPipe
else:
    Pipe = UnixPipe
