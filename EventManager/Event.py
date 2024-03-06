from enum import Enum, auto
from PyQt5.QtCore import QObject,pyqtSignal as Signal
class Evt_State(Enum):
    INIT = 1
    PROGRESS = 2
    DONE = 3

class Event(QObject):

    opts = dict()
    cur_state = ''
    next_state = ''
    m_start_time = -1
    m_end_time = -1
    m_min_start_time = -1
    child_method_operation = None
    started = None
    completed = None

    def __init__(self,**kwargs):

        self.opts['name'] = kwargs['name']
        self.opts['min_start_time'] = kwargs['min_start_time']
        self.opts['layer_time'] = kwargs['layer_time']
        self.opts['cur_time'] = kwargs['cur_time']
        self.opts['process_time'] = kwargs['process_time']
        self.opts['event'] = kwargs['event']
        self.opts['event_tracker'] = kwargs['event_tracker']
        self.opts['linkevt'] = kwargs['linkevt']
        self.cur_state = Evt_State.INIT

        self.started = Signal(int)
        self.completed = Signal(int)

        return

    def __del__(self):
        return

    def set_min_start_time(self,done_next_time):
        self.m_min_start_time = done_next_time
        return

    def get_min_start_time(self):
        return self.m_min_start_time

    def state_check(self,cur_time):

        if self.cur_state == Evt_State.INIT:
            if self.opts['min_start_time'] > 0:
                self.progress_operation()
            else:
                self.next_state = Evt_State.INIT

        elif self.cur_state == Evt_State.PROGRESS:
            if self.m_end_time <= cur_time:
                self.next_state = Evt_State.DONE
            elif self.m_end_time > cur_time:
                self.next_state = Evt_State.PROGRESS

        elif self.cur_state == Evt_State.DONE:
            self.done(cur_time)

    def progress_operation(self):
        if self.opts['process_time'] > 0:
            self.m_start_time = self.opts['layer_time'] + 1
            self.m_end_time = self.m_start_time + self.opts['process_time']
            if self.child_method_operation != None:
                self.child_method_operation()
            self.cur_state = Evt_State.PROGRESS
            return
        else:
            self.cur_state = Evt_State.INIT
            return

    def update_progress_time(self,update_end_time):
        self.opts['process_time'] = update_end_time - self.m_start_time
        return

    def done(self,current_time):
        if (self.m_end_time > current_time):
            self.opts['event_tracker'].append((self.m_start_time,self.m_end_time,self.opts['name']))
            if self.opts['linkevt']:
                self.opts['linkevt'].set_min_start_time(self.m_end_time)
            del self
            return
        else:
            self.next_state = Evt_State.DONE
