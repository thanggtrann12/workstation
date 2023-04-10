
# pylint: disable=W0212
from inspect import currentframe
from win32com import storagecon as stc
try:
    import queue as Queue
except ImportError:
    import Queue

# import logging
import os.path
import pythoncom
import random
import re
import socket
import subprocess
import threading
import time
import win32com.client
import winerror

# LOGDBG   = logging.getLogger('TTFisClient')
# LOGTRACE = logging.getLogger('TTFisTrace')
# LOGCMD   = logging.getLogger('TTFisCmd')
# import traceback


def _print(farg, *args):
    # print(farg % args)
    # for line in traceback.format_stack():
    #    print(line.strip())
    pass


class LOGDBG:
    def debug(farg, *args):
        _print(farg, *args)
        pass

    def warning(farg, *args):
        _print(farg, *args)
        pass

    def error(farg, *args):
        _print(farg, *args)

    def fatal(farg, *args):
        _print(farg, *args)


class LOGTRACE:
    def print(farg, *args):
        print(farg, *args)
        pass


class LOGCMD:
    def info(farg, *args):
        _print(farg, *args)
        pass


def error(farg, *args):
    _print(farg, *args)
    pass


def Wait(time2wait, unit='ms'):
    """
    Suspend the control flow for the specified period of time.

    Parameter:
    time2wait   : Time information as an integer value
    unit: Unit information as a string. Supported units are 'ms', 's', 'min'
    """
    if unit in ['min', 's', 'ms']:
        if time2wait >= 0:
            LOGCMD.info('Wait for %s %s', time2wait, unit)
            if unit == 'min':
                time.sleep(time2wait * 60.0)
            elif unit == 's':
                time.sleep(float(time2wait))
            else:
                time.sleep(time2wait / 1000.0)
        else:
            LOGCMD.error('Time information is negative')
            raise ValueError('Time information is negative')
    else:
        LOGCMD.error('Unit %s not supported', unit)


def WaitRandom(start, stop, step, unit='ms'):
    """
    Suspend the control flow for a period of time which is randomly selected element from range(start, stop, step).

    Parameter:
    start: Minimum value for random range of time as an integer value
    stop : Maximum value for random range of time as an integer value
    step : Step value for random range of time as an integer value
    unit : Unit information as a string. Supported units are 'ms', 's', 'min'
    """
    rtime = random.randrange(start, stop, step)
    Wait(rtime, unit)


class Singleton(object):  # pylint: disable=R0903
    """
    Class to implement Singleton Design Pattern. This class is used to derive the TTFisClient as only a single
    instance of this class is allowed.

    Disabled pyLint Messages:
    R0903:  Too few public methods (%s/%s)
            Used when class has too few public methods, so be sure it's really worth it.

            This base class implements the Singleton Design Pattern required for the TTFisClient.
            Adding further methods does not make sense.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if not cls._instance:
                cls._instance = super(Singleton, cls).__new__(
                    cls, *args, **kwargs)
        return cls._instance


class TTFisClient(Singleton):
    """
    Windows COM-Interface wrapper class to access TTFis COM Server (i.e. CSM.EXE).
    For details, refer to document API_TTFis_CSM.doc in the TTFis installation directory.
    """
    EVENT_WAIT_TIMEOUT = 60.00  # seconds
    CMDQUEUE_POLLING_INTERVAL = 1.00  # seconds
    CMDQUEUE_RESULT_STD_TIMEOUT = 1.00  # seconds
    RECEIVE_TRACES_POLLING_INTERVAL = 0.01  # seconds
    REGEX_TIMESTAMP = re.compile(r'(<\w*@\w*>)(\(core.\)|)TIME_STAMP:.*')

    _csm = None
    _csm_client_id = None
    _coma = None
    _csmconndevex = None
    _csmdevprop = None

    _CmdQueue = Queue.Queue()

    _call_thrd_obj = None
    _call_thrd_init = threading.Event()
    _call_thrd_term = threading.Event()

    _recv_thrd_obj = None
    _recv_thrd_term = threading.Event()

    _prof_thrd_obj = None
    _prof_thrd_term = threading.Event()
    _prof_intervall = 1.0

    _forceseq_lock = threading.RLock()

    _traceq_handle = 0
    _traceq_obj = {}
    _traceq_lock = threading.Lock()

    SupportedDevices = []

    _dev_active = None
    _dev_set = set([])
    _trcfiledict = {}
    _portaddrlist = []

    _UpdateTraceCallback = None

    def __init__(self):
        """
        Contructor called when a TTFisClient object is created.

        Disabled pyLint Messages:
        W0703:    Catch 'Exception' Used when an except catches Exception instances.

        There is no specific exception to be handled and script should continue in any case.
        The code inside the try-except block should only generate a warning for debugging purpose.
        """
        _mident = '%s.%s()' % (self.__class__.__name__, currentframe().f_code.co_name)
        LOGDBG.debug('Execute %s', _mident)
        Singleton.__init__(self)
        if not self._csm:
            # Just to support the analysis in case of COM exceptions:
            #   Check if an instance of csm.exe is already running without Console_IO application.
            #   The result of this check is just logged but NOT used inside TTFisClient
            try:
                wmi = win32com.client.GetObject('winmgmts:')
                proctmp = wmi.InstancesOf('Win32_Process')
                process_list = [pr.Properties_('Name')() for pr in proctmp]
                if 'csm.exe' in process_list and 'console_io.exe' not in process_list and 'console_io_mcore.exe' not in process_list:
                    LOGDBG.warning(
                        '%s: Process csm.exe is running without Console_IO application! Is this OK?', _mident)
            except Exception:  # pylint: disable=W0703
                LOGDBG.warning(
                    '%s: Check for a running csm.exe process failed.', _mident)
            # Start the thread for calling the COM-methods of the CSM.exe for device operations
            # and command handling.
            self._call_thrd_init.clear()
            self._call_thrd_term.clear()
            self.__class__._call_thrd_obj = threading.Thread(
                target=self.__Thrd_CallCmdsFromCSM)
            self.__class__._call_thrd_obj.setDaemon(True)
            self._call_thrd_obj.start()
            self._call_thrd_init.wait(self.EVENT_WAIT_TIMEOUT)
            if self._call_thrd_init.isSet():
                # Complete constructor execution only if the list of supported devices is not empty
                if self.SupportedDevices == []:
                    LOGDBG.error(
                        '%s: List of supported trace devices is empty', _mident)
                    raise RuntimeError(
                        '%s: List of supported trace devices is empty' % _mident)
                else:
                    # Now start the thread which receives and handles all trace messages
                    self._recv_thrd_term.clear()
                    self.__class__._recv_thrd_obj = threading.Thread(
                        target=self.__Thrd_ReceiveTracesFromCSM)
                    self.__class__._recv_thrd_obj.setDaemon(True)
                    self._recv_thrd_obj.start()
                    # Initialize set of connected devices and active device
                    self.__class__._dev_active = None
                    self.__class__._dev_set = set([])
            else:
                LOGDBG.error(
                    '%s: Initialisation of Thread __Thrd_CallCmdsFromCSM was not successfull', _mident)
                raise RuntimeError(
                    '%s: Initialisation of Thread __Thrd_CallCmdsFromCSM was not successfull' % _mident)
        else:
            LOGDBG.debug('%s: _csm object already created', _mident)
        LOGDBG.debug('Completed %s', _mident)

    def __del__(self):
        """
        Destructor called when the last reference to the TTFisClient object is freed.
        """
        _mident = '%s.%s()' % (self.__class__.__name__, currentframe().f_code.co_name)
        LOGDBG.debug('Execute %s', _mident)
        self.Quit()
        LOGDBG.debug('Completed %s', _mident)

    def registerUpdateTraceCallback(self, fptr_):
        self._UpdateTraceCallback = fptr_

    def Quit(self, disconnectall=True):
        """
        This method initiates the shutdown of the COM-Interface to TTFis COM Server. Call this method at the end of your script.
        """
        _mident = '%s.%s()' % (self.__class__.__name__, currentframe().f_code.co_name)
        LOGDBG.debug('Execute %s', _mident)
        with self._forceseq_lock:
            # Stop a running profiling thread
            if self._prof_thrd_obj and self._prof_thrd_obj.isAlive():
                self._prof_thrd_term.set()
                self._prof_thrd_obj.join(20.0)
                self.__class__._prof_thrd_obj = None
            # Disconnect all connected Trace devices
            if disconnectall:
                LOGDBG.debug('%s: Disconnecting devices ...', _mident)
                for device in self._dev_set.copy():
                    self.Disconnect(device)
            # Stop the Thread executing method __Thrd_CallCmdsFromCSM
            if self._recv_thrd_obj and self._recv_thrd_obj.isAlive():
                self._recv_thrd_term.set()
                self._recv_thrd_obj.join(20.0)
                self.__class__._recv_thrd_obj = None
            # Stop the Tread executing method __Thrd_CallCmdsFromCSM
            if self._call_thrd_obj and self._call_thrd_obj.isAlive():
                self._call_thrd_term.set()
                self._call_thrd_obj.join(20.0)
                self.__class__._call_thrd_obj = None
        LOGDBG.debug('Completed %s', _mident)

    def Restart(self):
        """
        This method resolves communication problems between Target and TTFis COM Server. Use this method very carefully!
        """
        _mident = '%s.%s()' % (self.__class__.__name__, currentframe().f_code.co_name)
        LOGDBG.debug('Execute %s', _mident)
        with self._forceseq_lock:
            # Remember currently active trace device
            old_dev_active = self._dev_active
            # Remember all connected trace devices
            old_dev_set = self._dev_set
            # Try to shut down TTFis COM Server communication
            self.Quit(False)
            # Kill csm.exe
            Wait(10, 's')
            subprocess.call('taskkill /F /IM csm.exe')
            Wait(20, 's')
            # Re-Intialize communication to TTFis COM server:
            #   If an exception is raised,
            try:
                self.__init__()
            except Exception as emsg:
                LOGDBG.fatal(
                    '%s: an Exception occurred during communication set-up to TTFis COM-Server.', _mident)
                LOGDBG.fatal('Error Message: %s', repr(emsg))
                raise
            # Re-Connect all previously attached trace device and reload TRC-Files
            resstate = winerror.S_OK
            for device in old_dev_set:
                if device in self._trcfiledict:
                    if not self.Connect(device, self._trcfiledict[device]):
                        resstate = winerror.E_FAIL
                else:
                    if not self.Connect(device):
                        resstate = winerror.E_FAIL
            # Set previously active trace device
            if old_dev_active:
                self.DevSelect(old_dev_active)
            # Re-enable Sockets
            old_portaddrlist = self._portaddrlist
            self.__class__._portaddrlist = []
            for portaddr in old_portaddrlist:
                self.EnableMSTSocket(portaddr)
        LOGDBG.debug('Completed %s', _mident)
        return resstate == winerror.S_OK

    def __CreateiUnkDataStream(self, files):
        """
        This private method creates a COM stream object, fills it with the file data of given
        TRC files and returns.

        The return value is the data stream converted to the COM type IID_IUnknown and a list of processed
        TRC-Files.
        """
        _mident = '%s.%s()' % (self.__class__.__name__, currentframe().f_code.co_name)
        LOGDBG.debug('Execute %s', _mident)
        trcfilelist = []
        flags = stc.STGM_CREATE | stc.STGM_READWRITE | stc.STGM_TRANSACTED | stc.STGM_SHARE_EXCLUSIVE | stc.STGM_DELETEONRELEASE
        sto = pythoncom.StgCreateDocfile(None, flags, 0)
        fst = sto.CreateStream(
            'TRTFiles.trt', stc.STGM_READWRITE | stc.STGM_SHARE_EXCLUSIVE, 0, 0)
        for trcfile in files:
            if os.path.exists(trcfile):
                LOGDBG.debug('%s: Reading TRC-File <%s>', _mident, trcfile)
                trcfilelist.append(trcfile)
                header = '\n;FilePath=[%s]%s\n' % (
                    socket.gethostname(), trcfile)
                infhandle = open(trcfile, 'r')
                buf = infhandle.read()
                fst.Write(header.encode())
                fst.Write(buf.encode())
                infhandle.close()
            else:
                LOGDBG.warning('%s: File does not exist: %s', _mident, trcfile)
        fst.Commit(stc.STGC_OVERWRITE)
        iunkdatastream = fst.QueryInterface(pythoncom.IID_IUnknown)
        sto.Commit(stc.STGC_OVERWRITE)
        LOGDBG.debug('Completed %s', _mident)
        return trcfilelist, iunkdatastream, sto

    def __AppendDevice(self, device, trcfilelist):
        """
        This private method updates the class attributes _dev_active, _dev_set, and _trcfiledict. It is intended
        to be used in the public methods Connect and LoadTRCFiles.
        """
        self.__class__._dev_active = device
        if device not in self._dev_set:
            self._dev_set.add(device)
        if device not in self._trcfiledict:
            self._trcfiledict[device] = trcfilelist
        else:
            for trcfile in trcfilelist:
                if trcfile not in self._trcfiledict[device]:
                    self._trcfiledict[device].append(trcfile)

    def Connect(self, device, files=None):
        """
        This method connects a named device to TTFis.

        Parameter:
            device: name of device as a string (e.g. 'paramount@usb')
            files : list of filenames as strings which refer to the TRC-files to be loaded

        Return Value:
            <devicename>: Returns the device name as a string if connection is successful
            None        : Connection failed
        """
        _mident = '%s.%s()' % (self.__class__.__name__, currentframe().f_code.co_name)
        LOGDBG.debug('Execute %s', _mident)
        # Check type of parameter device
        if (not isinstance(device, str)) and (not isinstance(device, unicode)):
            LOGDBG.error(
                '%s: Parameter <device> is not of type string/unicode', _mident)
            raise RuntimeError(
                '%s: Parameter <device> is not of type string/unicode' % _mident)
        LOGDBG.debug('%s: Connect to device <%s>', _mident, device)
        # Check if device is supported
        if device.upper() not in self.SupportedDevices:
            LOGDBG.error(
                '%s: Device <%s> in not supported by TTFis-Installation', _mident, device)
            raise RuntimeError(
                '%s: Device <%s> in not supported by TTFis-Installation' % (_mident, device))
        # Check if parameter files is of type list
        if files and not isinstance(files, list):
            LOGDBG.error('%s: Parameter <files> is not of type list', _mident)
            raise RuntimeError(
                '%s: Parameter <files> is not of type list' % _mident)
        with self._forceseq_lock:
            # Check if device is already connected
            if device in self._dev_set:
                self.DevSelect(device)
                LOGDBG.debug(
                    'Completed %s. Device %s already connected.', _mident, device)
                return device
            # Check if _csm object is valid.
            # As we are here within a locked sequence, a single check is sufficient
            if not self._csm:
                LOGDBG.error(
                    '%s: Reference to TTFis COM Server object was freed. Quit() method already called?', _mident)
                return None
            # Check if device is already connected
            cmdresqueue = Queue.Queue()
            self._CmdQueue.put(
                (self._csm.IsDeviceConnected, (self._csm_client_id, device), cmdresqueue), False)
            (success, conn) = cmdresqueue.get(True)
            cmdresqueue.task_done()
            if success:
                if conn == 1 or not files:
                    trcfilelist = []
                    self._CmdQueue.put(
                        (self._csm.ConnectDevice, (self._csm_client_id, device, 0, None), cmdresqueue), False)
                    (success, dummy) = cmdresqueue.get(True)
                    cmdresqueue.task_done()
                else:
                    trcfilelist, iunkdatastream, storageobject = self.__CreateiUnkDataStream(
                        files)
                    # the object <storageobject> must be existent until the connect device is completed
                    self._CmdQueue.put((self._csmconndevex.ConnectDeviceEx, (
                        self._csm_client_id, device, iunkdatastream), cmdresqueue), False)
                    (success, dummy) = cmdresqueue.get(True)
                    cmdresqueue.task_done()
                    del storageobject
                if success:
                    self.__AppendDevice(device, trcfilelist)
                    LOGDBG.debug('Completed %s', _mident)
                    return device
        LOGDBG.debug('Completed %s with errors', _mident)
        return None

    def Disconnect(self, device):
        """
        This method disconnects a named device from TTFis.

        Parameter:
            device: name of device as a string (e.g. 'paramount@usb')
        """
        _mident = '%s.%s()' % (self.__class__.__name__, currentframe().f_code.co_name)
        LOGDBG.debug('Execute %s', _mident)
        if (not isinstance(device, str)) and (not isinstance(device, unicode)):
            LOGDBG.error(
                '%s: Parameter <device> is not of type string/unicode', _mident)
            raise RuntimeError(
                '%s: Parameter <device> is not of type string/unicode' % _mident)
        LOGDBG.debug('%s: Disconnect device <%s>', _mident, device)
        with self._forceseq_lock:
            if self._csm:
                if device in self._dev_set:
                    cmdresqueue = Queue.Queue()
                    self._CmdQueue.put(
                        (self._csm.DisconnectDevice, (self._csm_client_id, device), cmdresqueue), False)
                    (success, dummy) = cmdresqueue.get(True)
                    cmdresqueue.task_done()
                    del cmdresqueue
                    if success:
                        self._dev_set.remove(device)
                        del self._trcfiledict[device]
                        if device == self._dev_active:
                            if len(self._dev_set) > 0:
                                # Select only the first element of set _dev_set and call method DevSelect
                                for cur_dev in self._dev_set:
                                    self.DevSelect(cur_dev)
                                    break
                            else:
                                self.__class__._dev_active = None
                else:
                    LOGDBG.error(
                        '%s: Disconnect failed. Device <%s> not connected.', _mident, device)
            else:
                LOGDBG.error(
                    '%s: Reference to TTFis COM Server object was freed. Quit() method already called?', _mident)
        LOGDBG.debug('Completed %s', _mident)

    def DevSelect(self, device):
        """
        This method selects an already connected device.

        Parameter:
            device: name of device as a string (e.g. 'paramount@usb')
        """
        _mident = '%s.%s()' % (self.__class__.__name__, currentframe().f_code.co_name)
        LOGDBG.debug('Execute %s', _mident)
        if (not isinstance(device, str)) and (not isinstance(device, unicode)):
            LOGDBG.error(
                '%s: Parameter <device> is not of type string/unicode', _mident)
            raise RuntimeError(
                '%s: Parameter <device> is not of type string/unicode' % _mident)
        LOGDBG.debug('%s: Select device <%s>', _mident, device)
        with self._forceseq_lock:
            if self._csm:
                if device == self._dev_active:
                    pass
                elif device != self._dev_active and device in self._dev_set:
                    cmdresqueue = Queue.Queue()
                    self._CmdQueue.put(
                        (self._csm.SetActiveDevice, (self._csm_client_id, device), cmdresqueue), False)
                    (success, dummy) = cmdresqueue.get(True)
                    cmdresqueue.task_done()
                    del cmdresqueue
                    if success:
                        self.__class__._dev_active = device
                else:
                    LOGDBG.error('%s: Device <%s> not connected.',
                                 _mident, device)
            else:
                LOGDBG.error(
                    '%s: Reference to TTFis COM Server object was freed. Quit() method already called?', _mident)
        LOGDBG.debug('Completed %s', _mident)

    def GetActiveDevice(self):
        """
        This method returns the currently connected and active device.
        Be aware that the active device might change any time (e.g. by a parallel thread).
        """
        return self._dev_active

    def IsDeviceConnected(self, device):
        """
        This method returns True if the device is already connected.
        """
        return device in self._dev_set

    def EnableMSTSocket(self, portaddr=12300):
        """
        This method enables the MST Socket Hook (e.g. of the paramount@usb device).

        Parameter:
            portaddr: Socket port address. If not specified, the default port 12300 is used.
        """
        _mident = '%s.%s()' % (self.__class__.__name__, currentframe().f_code.co_name)
        LOGDBG.debug('Execute %s', _mident)
        with self._forceseq_lock:
            if self._csm:
                cmdresqueue = Queue.Queue()
                self._CmdQueue.put((self._csmdevprop.ConnectMSTClient,
                                   (self._csm_client_id, True, portaddr), cmdresqueue), False)
                (success, dummy) = cmdresqueue.get(True)
                cmdresqueue.task_done()
                del cmdresqueue
                if success:
                    self._portaddrlist.append(portaddr)
            else:
                LOGDBG.error(
                    '%s: Reference to TTFis COM Server object was freed. Quit() method already called?', _mident)
        LOGDBG.debug('Completed %s', _mident)

    def Cmd(self, *args):
        """
        Send TTFis command to selected device.

        Syntax-Variants:
            Cmd( cmdstr )
            Cmd( device, cmdstr)

        Parameter:
            cmdstr: TTFis command as a string (multiple lines separated by '\\n' are possible, leading blanks/tabs are ignored)
            device: Device name to be selected before the command is issued
        """
        _mident = '%s.%s()' % (self.__class__.__name__, currentframe().f_code.co_name)
        LOGDBG.debug('Execute %s', _mident)
        if len(args) == 1:
            device = None
            cmd_sequence = args[0]
        elif len(args) == 2:
            device = args[0]
            cmd_sequence = args[1]
        else:
            LOGDBG.error('%s: Invalid number of arguments', _mident)
            raise RuntimeError('%s: Invalid number of arguments' % _mident)
        for cmd in cmd_sequence.splitlines():
            cmd = cmd.lstrip(' \t\n\r\f\v.')
            if len(cmd) == 0:
                continue
            LOGCMD.info(cmd)
            if cmd[0] == '#':
                continue
            substrings = cmd.split(' ', 2)
            if len(substrings) == 2 and substrings[0] == 'w+' or substrings[0] == 'W+':
                Wait(int(substrings[1]), 'ms')
            else:
                self._CmdQueue.put(
                    (self.__SendCommand, (device, cmd), None), False)
        LOGDBG.debug('Completed %s', _mident)

    def LoadTRCFiles(self, files=None):
        """
        This method loads addtional TRC-Files to the active device of TTFis.

        Parameter:
            files : list of filenames as strings which refer to the TRC-files to be loaded

        Return Value:
            True:  Loading of TRC-Files successful
            False: Loading of TRC-Files failed
        """
        _mident = '%s.%s()' % (self.__class__.__name__, currentframe().f_code.co_name)
        LOGDBG.debug('Execute %s', _mident)
        # Check if parameter files is of type list
        if files and not isinstance(files, list):
            LOGDBG.error('%s: Parameter <files> is not of type list', _mident)
            raise RuntimeError(
                '%s: Parameter <files> is not of type list' % _mident)
        with self._forceseq_lock:
            # Check if _csm object is valid.
            # As we are here within a locked sequence, a single check is sufficient
            if not self._csm:
                LOGDBG.error(
                    '%s: Reference to TTFis COM Server object was freed. Quit() method already called?', _mident)
                return False
            device = self._dev_active
            if len(files) > 0:
                trcfilelist, iunkdatastream, storageobject = self.__CreateiUnkDataStream(
                    files)
                cmdresqueue = Queue.Queue()
                self._CmdQueue.put((self._csmconndevex.SendCmdOptnNFilesEx,
                                   (self._csm_client_id, 'n', iunkdatastream), cmdresqueue), False)
                (success, dummy) = cmdresqueue.get(True)
                cmdresqueue.task_done()
                del storageobject
                if success:
                    self.__AppendDevice(device, trcfilelist)
                    LOGDBG.debug('Completed %s', _mident)
                    return True
        LOGDBG.debug('Completed %s with errors', _mident)
        return False

    def Wait4Trace(self, searchobj, dotall=False, timeout=0, fctobj=None, *fctargs):
        """
        Suspend the control flow until a Trace message is received which matches to a specified regular expression.

        Syntax-Variants:
            Wait4Trace(searchobj)
            Wait4Trace(searchobj, timeout)
            Wait4Trace(searchobj, timeout, fctobj, fctarg1, ...)

        Parameter:
            searchobj: Regular expression all received trace messages are compare to.
                        Can be passed either as a string or a regular expression object. Refer to Python documentation for module 're'.
            timeout:   Optional timeout parameter specified as a floating point number in the unit 'seconds'.
            fctobj:    Optional function object to be excuted after the search is initiated but before control flow is suspended.
            *fctargs:   Optional list of function arguments passed to 'fctobj'

        Return Value:
            None:    If no trace message matched to the specified regular expression and a timeout occurred.
            <match>: If a trace message has matched to the specified regular expression, a match object is returned as the result.
                      The complete trace message can be accessed by the 'string' attribute of the match object.
                      For access to groups within the regular expression, use the group() method.
                      For more information, refer to Python documentation for module 're'.

        Disabled pyLint Messages:
        W0703:    Catch 'Exception' Used when an except catches Exception instances.

        There is no specific exception to be handled and script should continue in any case.
        This method calls a function object passes as an argument. So it has no knowledge about possible exception classes.
        """
        _mident = '%s.%s()' % (self.__class__.__name__, currentframe().f_code.co_name)
        LOGDBG.debug('Execute %s', _mident)
        if (True == dotall):
            search_regex = re.compile(searchobj, re.DOTALL)
        else:
            search_regex = re.compile(searchobj)
        trq = Queue.Queue()
        trq_handle = self.TraceQActivate(search_regex, trq)
        if fctobj is not None:
            try:
                fctobj(*fctargs)
            except Exception as emsg:  # pylint: disable=W0703
                LOGDBG.error(
                    '%s: An Exception occurred executing function object: %s', _mident, repr(fctobj))
                LOGDBG.error('Function Arguments: %s', repr(fctargs))
                LOGDBG.error('Error Message: %s', repr(emsg))
        success = True
        try:
            (dummy, match) = trq.get(True, timeout)
        except Queue.Empty:
            success = False
        finally:
            self.TraceQDeactivate(trq_handle)
            del trq
        LOGDBG.debug('Completed %s', _mident)
        if success:
            return match
        else:
            return None

    def TraceQActivate(self, searchobj, tracequeue):
        """
        Activates a trace message filter specified as a regular expression. All matching trace messages are put in the specified queue object.

        Parameter:
            searchobj:  Regular expression all received trace messages are compare to.
                         Can be passed either as a string or a regular expression object. Refer to Python documentation for module 're'.#
            tracequeue: A queue object all trace message which matches the regular expression are put in.
                         The using application must assure, that the queue is emptied or deleted.

        Return Value:
            <int>: Handle to deactivate the message filter.
        """
        _mident = '%s.%s()' % (self.__class__.__name__, currentframe().f_code.co_name)
        LOGDBG.debug('Execute %s', _mident)
        with self._traceq_lock:
            self.__class__._traceq_handle += 1
            regexob = re.compile(searchobj)
            self._traceq_obj[self._traceq_handle] = (regexob, tracequeue)
            return self._traceq_handle
        LOGDBG.debug('Completed %s', _mident)

    def TraceQDeactivate(self, handle):
        """
        Deactivates a trace message filter previously activated by ActivateTraceQ() method.

        Parameter:
            handle:  Integer object returned by ActivateTraceQ() method.

        Return Value:
            False: No trace message filter active with the specified handle (i.e. handle is not in use).
            True:  Trace message filter successfully deleted.
        """
        _mident = '%s.%s()' % (self.__class__.__name__, currentframe().f_code.co_name)
        LOGDBG.debug('Execute %s', _mident)
        with self._traceq_lock:
            if handle in self._traceq_obj:
                del self._traceq_obj[handle]
                return True
            else:
                return False
        LOGDBG.debug('Completed %s', _mident)

    def MiniProfilerStart(self, intervall=1.0, device=None):
        """
        This method starts a separate Python thread which triggers the embedded MiniProfiler output at a specified rate.
        At the moment, there is no graphical front-end for this feature. The trace output needs to evaluated by separate tooling offline.

        Parameter:
            intervall:  Optional polling intervall parameter specified as a floating point number in the unit 'seconds'.
        """
        _mident = '%s.%s()' % (self.__class__.__name__, currentframe().f_code.co_name)
        LOGDBG.debug('Execute %s', _mident)
        with self._forceseq_lock:
            if self._prof_thrd_obj and self._prof_thrd_obj.isAlive():
                self._prof_thrd_term.set()
                self._prof_thrd_obj.join(20.0)
            self.__class__._prof_intervall = intervall
            if device and device in self._dev_set:
                devarg = device
            else:
                devarg = self._dev_active
            self.__class__._prof_thrd_obj = threading.Thread(
                target=self.__ProfilerBody, args=(devarg,))
            self.__class__._prof_thrd_obj.setDaemon(True)
            self._prof_thrd_obj.start()
        LOGDBG.debug('Completed %s', _mident)

    def MiniProfilerStop(self):
        """
        This method stops a separate Python thread which triggered the embedded MiniProfiler output.
        """
        _mident = '%s.%s()' % (self.__class__.__name__, currentframe().f_code.co_name)
        LOGDBG.debug('Execute %s', _mident)
        with self._forceseq_lock:
            if self._prof_thrd_obj and self._prof_thrd_obj.isAlive():
                self._prof_thrd_term.set()
        if self._prof_thrd_obj:
            self._prof_thrd_obj.join(20.0)
            self.__class__._prof_thrd_obj = None
        LOGDBG.debug('Completed %s', _mident)

    def __CreateCOMConnection(self):
        """
        Internal (pseudo private) method which is executed in a separate Python thread.

        This method calls the COM-methods of the CSM.exe for device operations and command handling.
        It runs in a separate thread to allow multi-threaded application of the TTFisClient object
        in single-threaded COM-apartment model.

        It uses a queue object to transfer the command and arguments as well as the results.
        """
        _mident = '%s.%s()' % (self.__class__.__name__, currentframe().f_code.co_name)
        LOGDBG.debug('Execute %s', _mident)
        try:
            pythoncom.CoInitialize()
            try:
                # Per default try to create the interface-wrapper files in the gen_py folder.
                # If this fails, then try to use the files existing in the folder.
                temp_csm_object = win32com.client.Dispatch('CSM.CoCSM')
                self.__class__._csm = win32com.client.gencache.EnsureDispatch(
                    temp_csm_object)
            except Exception as emsg:  # pylint: disable=W0703
                # Creating of the interface files in gen_py failed. Try now to use the existing files.
                LOGCMD.info(
                    'Creating of CSM.exe interface files in gen_py failed!')
                LOGCMD.info('Error Message: %s', repr(emsg))
                self.__class__._csm = win32com.client.Dispatch('CSM.CoCSM')
            print(dir(self._csm.CoCSM))
            self.__class__._coma = pythoncom.CoMarshalInterThreadInterfaceInStream(
                self._csm.CLSID, self._csm)
            self.__class__._csm_client_id = self._csm.Initialize(0x1)
            self.__class__._csmconndevex = win32com.client.CastTo(
                self._csm, 'ICSMConnDevEx')
            self.__class__._csmdevprop = win32com.client.CastTo(
                self._csm, 'ICSMDevProp')
        except Exception as emsg:
            LOGDBG.fatal(
                '%s: an Exception occurred during communication set-up to TTFis COM-Server.', _mident)
            LOGDBG.fatal('Error Message: %s', repr(emsg))
            self.__class__._csm = None
            self.__class__._coma = None
            self.__class__._csm_client_id = None
            self.__class__._csmconndevex = None
            self.__class__._csmdevprop = None
            raise
        else:
            # Communication to TTFis COM-Server is set up successfully.
            # Now get list of supported Trace devices
            self.__class__.SupportedDevices = []
            try:
                nr_of_devices = self._csm.GetAvailableDeviceCount(
                    self._csm_client_id)
            except pythoncom.com_error as error_message:
                LOGDBG.error(
                    '%s: COM Exception detected. Method GetAvailableDeviceCount failed', _mident)
                LOGDBG.error('Error message: %s', repr(error_message))
                raise
            else:
                LOGDBG.debug(
                    '%s: GetAvailableDeviceCount return %d devices', _mident, nr_of_devices)
                # Now try to get the names of the supported devices:
                #   In case of an COM exception, the error will be logged but execution will continue
                for dev_id in range(0, nr_of_devices):
                    try:
                        dev_name = self._csm.GetNameOfDeviceId(
                            self._csm_client_id, dev_id)
                        LOGDBG.debug("Device name %s", dev_name)
                    except pythoncom.com_error as error_message:
                        LOGDBG.error(
                            '%s: COM Exception detected. Method GetNameOfDeviceId failed for Device ID %d', _mident, dev_id)
                        LOGDBG.error('Error message: %s', repr(error_message))
                    else:
                        self.__class__.SupportedDevices.append(dev_name)
                    # self.SupportedDevices.sort()
        LOGDBG.debug('Completed %s', _mident)

    def getSupportedDevices(self):
        supportedDevices = self.SupportedDevices.copy()
        supportedDevices.sort()
        return supportedDevices

    def __SendCommand(self, device, command):
        """
        This private method combines the TTFis-COM-Server interface SetActiveDevice and SendCommandOption.
        It assures that all TTFis commands are send to the right Trace-Device.
        """
        if device and device != self._dev_active and device in self._dev_set:
            self._csm.SetActiveDevice(self._csm_client_id, device)
            self.__class__._dev_active = device
        self._csm.SendCommandOption(self._csm_client_id, command)

    def __Thrd_CallCmdsFromCSM(self):
        """
        Internal (pseudo private) method which is executed in a separate Python thread.

        This method calls the COM-methods of the CSM.exe for device operations and command handling.
        It runs in a separate thread to allow multi-threaded application of the TTFisClient object
        in single-threaded COM-apartment model.

        It uses a queue object to transfer the command and arguments as well as the results.

        Disabled pyLint Messages:
        W0142:  Used * or * magic* Used when a function or method is called using *args or **kwargs to
                dispatch arguments. This doesn't improve readability and should be used with are.

        This is a worker-thread method which executes arbitrary functions in its context.

        W0703:  Catch 'Exception' Used when an except catches Exception instances.

        There is no specific exception to be handled and script should continue in any case.
        This is a worker-thread method which executes arbitrary functions in its context.
        So it has no knowledge about possible exception classes.
        """
        _mident = '%s.%s()' % (self.__class__.__name__, currentframe().f_code.co_name)
        LOGDBG.debug('Execute %s', _mident)
        self.__CreateCOMConnection()
        # Initialization of thread is completed. Constructor can continue execution ...
        self._call_thrd_init.set()
        error_counter = 0
        while True:
            try:
                (fctobj, fctargs, resqueue) = self._CmdQueue.get(
                    True, self.CMDQUEUE_POLLING_INTERVAL)
            except Queue.Empty:
                pass
            else:
                success = False
                result = None
                try:
                    result = fctobj(*fctargs)
                except Exception as emsg:  # pylint: disable=W0703
                    error_counter += 2
                    LOGDBG.error(
                        '%s: An Exception occurred executing function object: %s', _mident, repr(fctobj))
                    LOGDBG.error('Function Arguments: %s', repr(fctargs))
                    LOGDBG.error('Error Message: %s', repr(emsg))
                else:
                    if error_counter > 0:
                        error_counter -= 1
                    success = True
                if resqueue:
                    resqueue.put((success, result), False)
            if self._call_thrd_term.isSet():
                self._call_thrd_term.clear()
                break
            if error_counter > 100:
                LOGDBG.error(
                    '%s: Too many Exceptions detected. Terminating ...', _mident)
                break
        try:
            self._csm.Uninitialize(self._csm_client_id)
            if (0 == self._csm.IsLastClient(self._csm_client_id)):
                subprocess.call('taskkill /f /im csm.exe')
        except pythoncom.com_error as error_message:
            LOGDBG.error(
                '%s: COM Exception detected. Method Uninitialize failed', _mident)
            LOGDBG.error('Errormessage: %s', repr(error_message))
            self.__class__._csm = None
            raise
        else:
            self.__class__._csm = None
        LOGDBG.debug('Completed %s', _mident)

    def __Thrd_ReceiveTracesFromCSM(self):  # pylint: disable=R0912
        """
        Internal (pseudo private) method which is executed in a separate Python thread.

        This method periodically checks for received trace messages. All output analysis, e.g. logging or filtering is done here.
        """
        _mident = '%s.%s()' % (self.__class__.__name__, currentframe().f_code.co_name)
        LOGDBG.debug('Execute %s', _mident)
        pythoncom.CoInitialize()
        csm_clone = pythoncom.CoGetInterfaceAndReleaseStream(
            self._coma, pythoncom.IID_IDispatch)
        csm_clone = win32com.client.Dispatch(csm_clone)
        error_counter = 0
        ttfists = None
        while not self._recv_thrd_term.isSet():  # pylint: disable=too-many-nested-blocks
            try:
                remaining = csm_clone.IsMsgQEmpty(self._csm_client_id)
            except pythoncom.com_error as error_message:
                error_counter += 2
                LOGDBG.error(
                    '%s: COM Exception detected. Method IsMsgQEmpty failed', _mident)
                LOGDBG.error('Error message: %s', repr(error_message))
                time.sleep(10 * self.RECEIVE_TRACES_POLLING_INTERVAL)
            else:
                if remaining == 0:
                    time.sleep(self.RECEIVE_TRACES_POLLING_INTERVAL)
                while remaining > 0:
                    remaining -= 1
                    try:
                        (msgid, data) = csm_clone.GetCSMMessage(
                            self._csm_client_id)
                    except pythoncom.com_error as error_message:
                        error_counter += 1
                        LOGDBG.error(
                            '%s: COM Exception detected. Method GetCSMMessage failed', _mident)
                        LOGDBG.error('Error message: %s', repr(error_message))
                    else:
                        if error_counter > 0:
                            error_counter -= 1
                        if msgid != 1 and data:
                            result = self.REGEX_TIMESTAMP.search(data)
                            if result:
                                ttfists = (result.group(1), result.group(0))
                                continue
                            if ttfists and data.startswith(ttfists[0]):
                                data = ttfists[1] + ':' + \
                                    data[len(ttfists[0]):]
                                ttfists = None

                            if (self._UpdateTraceCallback):
                                self._UpdateTraceCallback(data)

                            # dstr = data.encode('utf-8', 'replace')
                            # for line in dstr.splitlines():
                            #     LOGTRACE.print(line)

                            with self._traceq_lock:
                                if self._traceq_obj:
                                    now = time.time()
                                    for (regex, msgq) in self._traceq_obj.values():
                                        result = regex.search(data)
                                        if result:
                                            msgq.put((now, result), False)
            if error_counter > 100:
                LOGDBG.error(
                    '%s: Too many COM Exceptions detected. Terminating ...', _mident)
                break
        self._recv_thrd_term.clear()
        LOGDBG.debug('Completed %s', _mident)
        del csm_clone

    def __ProfilerBody(self, device):
        """
        Internal (pseudo private) method which is executed in a separate Python thread.

        This method periodically triggers the embedded MiniProfiler output at the given rate.
        """
        _mident = '%s.%s()' % (self.__class__.__name__, currentframe().f_code.co_name)
        LOGDBG.debug('Execute %s', _mident)
        while True:
            self._CmdQueue.put(
                (self.__SendCommand, (device, 'tt'), None), False)
            time.sleep(self._prof_intervall)
            if self._prof_thrd_term.isSet():
                self._prof_thrd_term.clear()
                break
        LOGDBG.debug('Completed %s', _mident)
