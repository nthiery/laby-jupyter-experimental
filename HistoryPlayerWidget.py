#!/usr/bin/env python
# coding: utf-8

# # A value history player widget
#
# Consider a value widget `w`.
# Player(`w`) wraps this widget to maintain a history of all the values that have been assigned to it.
# In addition, it adds controls analogous to those of audio/video/... players to
# replay that history.

# In[1]:


from ipywidgets import HBox, VBox, Button, Text, Layout, Output, IntSlider, Label
import traitlets
import threading, queue, os, time

infinity = 1000000

class PlayerModel:
    """
    The model for the player on a sequence (history) of values. It
    manages the history and provides the following operations:
    - asynchronously adding a new value (non blocking method)
    - navigating the history, synchronously (change frame) or in the background (continous play)
    - sending updates to the view and control pannel

    @view: the widget used to display the current value
    @controler: the control pannel for the player; used to display the frame number
    """
    def __init__(self, view, controler):
        # Invariant: -1 <= time < len(history)
        # If time >=0, history[time] is the currently displayed value
        # 0 <= desired_time
        self._view = view
        self._controler = controler
        self._clock = None
        self._finished = False
        self._lock = threading.Condition()
        self._waiting_for_new_value_lock = threading.Condition()
        self.reset()
        self.UpdateThread(self).start()

    def reset(self):
        with self._lock:
            self._history = []
            self._time = -1
            self._desired_time = infinity
            self._steps_per_iteration = 1
            self._delay = 1 # delay between frames
            self._time_previous_step = 0
            self._waiting_for_new_value = True

    def check(self):
        assert self._time >= -1
        assert self._time < len(self._history)
        assert self._desired_time >= 0
        if self._finished:
            assert self._desired_time < len(self._history)

    # Update thread

    def update(self):
        # to be called only by the update thread
        # no other method change the values below, so no need to be atomic
        assert threading.current_thread().name == "update thread"
        self._view.value = self._history[self._time]
        self._controler._frame.value = str(self._time)

    def print(player):
        print(threading.current_thread().name, player._time, player._desired_time, player._steps_per_iteration, player._waiting_for_new_value, player._history)

    def notify(self):
        with self._lock:
            self._lock.notify()

    class UpdateThread(threading.Thread):
        def __init__(self, player):
            self._player = player
            threading.Thread.__init__(self, name="update thread")

        def run(self):
            player = self._player
            player._lock.acquire()
            while player._lock.wait():
                player.print()
                if player._desired_time == player._time:
                    # Nothing to do
                    continue
                if player._desired_time < player._time:
                    if player._steps_per_iteration == infinity:
                        player._time = player._desired_time
                    else:
                        player._time -= 1
                        self.timer()
                if player._desired_time > player._time:
                    # request new value and pause until available
                    if player._time == len(player._history) - 1:
                        with player._waiting_for_new_value_lock:
                            player._waiting_for_new_value = True
                            player._waiting_for_new_value_lock.notify()
                        continue
                    if player._steps_per_iteration == infinity:
                        player._time = len(player._history) - 1;
                    else:
                        player._time += 1
                        self.timer()
                # player._time was changed
                player.update()

        def timer(self):
            threading.Timer(1./self._player._delay, self._player.notify).start()

    # Operations for the main thread
    def set_value(self, value):
        """
        Add a new value; blocks if the queue is full, that is no new value is needed at this point
        """
        self.print()
        self._history.append(value)
        with self._lock:
            self._lock.notify()

    # Operations for the "user interaction" thread

    def stop(self):
        with self._lock:
            self._desired_time = max(self._time, 0)
            self._steps_per_iteration = infinity
            # maybe not needed
            self._lock.notify()

    def begin(self, steps_per_iteration=infinity):
        with self._lock:
            self._desired_time = 0
            self._steps_per_iteration = steps_per_iteration
            self._lock.notify()

    def end(self, steps_per_iteration=infinity):
        with self._lock:
            if self._finished:
                self._desired_time = len(self._history) - 1
            else:
                self._desired_time = infinity
            self._steps_per_iteration = steps_per_iteration
            self._lock.notify()

    def play_forward(self):
        self.end(steps_per_iteration=1)

    def play_backward(self):
        self.begin(steps_per_iteration=1)

    def step_backward(self):
        with self._lock:
            self.check()
            if self._desired_time >= 0:
                self._desired_time -= 1;
            self._steps_per_iteration = infinity
            self._lock.notify()

    def step_forward(self):
        self.print()
        with self._lock:
            self.check()
            if self._desired_time < len(self._history) or not self._finished:
                self._desired_time += 1;
                self._lock.notify()

    def set_speed(self, speed):
        with self._lock:
            self._delay = 2.**-speed
            self._lock.notify()

# In[4]:

class PlayerThread(threading.Thread):
    def __init__(self, model, view):
        threading.Thread.__init__(self)
        self._model = model
        self._view = view

    def run(self):
        model = self._model
        view = self._view

        view._step_backward.on_click(lambda button: model.step_backward())
        view._step_forward .on_click(lambda button: model.step_forward())
        view._begin        .on_click(lambda button: model.begin())
        view._end          .on_click(lambda button: model.end())
        view._play         .on_click(lambda button: model.play_forward())
        view._backward     .on_click(lambda button: model.play_backward())
        view._pause        .on_click(lambda button: model.stop())
        view._speed_slider .observe (lambda slider: model.set_speed(speed_slider.value))

class Player(VBox):
    value = traitlets.Any()
    def __init__(self, view):
        layout  = Layout(width="initial")
        self._step_backward = Button(tooltip="Step backward", icon="step-backward", layout=layout)
        self._step_forward  = Button(tooltip="Step forward",  icon="step-forward",  layout=layout)
        self._begin         = Button(tooltip="Begin",         icon="fast-backward", layout=layout)
        self._end           = Button(tooltip="End",           icon="fast-forward",  layout=layout)
        self._backward      = Button(tooltip="Play backward", icon="backward",      layout=layout)
        self._play          = Button(tooltip="Play",          icon="play",          layout=layout)
        self._pause         = Button(tooltip="Pause",         icon="pause",         layout=layout)
        self._frame_label = Label("frame: ")
        self._frame = Label("")
        self._speed_label = Label("speed: ")
        self._speed_slider = IntSlider(0,0,10,1)
        player_controls = HBox([self._begin, self._backward, self._step_backward,
                                self._pause,
                                self._play, self._step_forward, self._end,
                                self._frame_label, self._frame,
                                self._speed_label, self._speed_slider])
        VBox.__init__(self, [view, player_controls])

        self._model      = PlayerModel(view, self)
        self._controller = PlayerThread(self._model, self).start()

    @traitlets.observe("value")
    def value_changed(self, change):
        self._model.set_value(change.new)
