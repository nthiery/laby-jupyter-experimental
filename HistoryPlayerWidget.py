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


# Current bug: when playing at the end while new values are being produced, the current clock can't be cancelled
# GIL issue?

# In[2]:


class Clock(threading.Thread):
    """
    Execute a command every x seconds
    """
    def __init__(self, delay, command, name=""):
        self.cancelled = False
        self.delay = delay
        self.command = command
        self._command_name = name
        threading.Thread.__init__(self)

    def run(self):
        while not self.cancelled:
            print("Running command {}".format(self._command_name))
            if self.command():
                time.sleep(self.delay)
            else:
                self.cancel()

    def cancel(self):
        print("canceling")
        self.cancelled = True


# In[3]:


class PlayerModel:
    """
    The model for the player on a sequence (history) of values. It
    manages the history and provides the following operations:
    - asynchronously adding a new value (blocking method)
    - navigating the history, synchronously (change frame) or in the background (continous play)
    - sending updates to the view and control pannel

    @view: the widget used to display the current value
    @controler: the control pannel for the player; used to display the frame number
    """
    def __init__(self, view, controler):
        # Invariant: -1 <= time <= len(history) -1
        # If time <> -1, history[time] is the currently displayed value
        self._view = view
        self._controler = controler
        self._clock = None
        self._finished = False
        self.reset()
        #self.play()

    def reset(self):
        self.stop()
        self._history = []
        self._new_values = queue.Queue(maxsize=1)
        self._time = -1
        self._direction = 1
        self._speed = 1

    def set_value(self, value):
        """
        Add a new value; blocks if the queue is full, that is no new value is needed at this point
        """
        # This is the producer for the queue of new values
        self._new_values.put(value)

    def update(self):
        self._view.value = self._history[self._time]
        self._controler._frame.value = str(self._time)

    def stop(self):
        #print("stop", self._clock)
        if self._clock:
            self._clock.cancel()
            self._clock = None

    def begin(self):
        print("begin")
        self.stop()
        assert self._history
        self._time = 0
        self.update()
        print("begin done")

    def end(self):
        print("end")
        # Could trigger a clock if not finished
        self.stop()
        self._time = len(self._history) - 1
        self.update()
        print("end done")

    def step_backward(self):
        print("step_backward")
        self.stop()
        self.step(direction=-1)
        print("step_backward done")

    def step_forward(self):
        print("step_forward")
        self.stop()
        self.step(direction=1)
        print("step_backward done")

    # Atomic operations
    def try_step_backward(self):
        assert self._time >= 0
        if self._time == 0:
            return False
        self._time -= 1;
        self.update()
        return True

    def try_step_forward(self):
        assert self._time < len(self._history)
        if self._time == len(self._history) - 1:
            pass
        self._time += 1
        self.update()

    def try_increase_history(self):
        try:
            self._history.append(self._new_values.get(timeout=1))
            print("consumed new value")
            return True
        except queue.Empty:
            print("consuming new value timed out; time: {} / {}".format(self._time, len(self._history)))
            return False

    # Other operations

    def step(self, direction=1):
        if direction < 0:
            return self.try_step_backward()
        else:
            while self._time == len(self._history) - 1:
                if self._finished:
                    return False
                else:
                    self.try_increase_history()
            assert self._time < len(self._history) - 1
            self.try_step_forward()
            return True

    def play(self, direction=None):
        """
        Start or restart the playing in the background
        """
        self.stop()
        if direction is None:
            direction = self._direction
        else:
            self._direction = direction
        self._clock = Clock(abs(1./self._speed), lambda: self.step(direction), "step {}".format(direction))
        self._clock.start()

    def set_speed(self, speed):
        self._speed = 2**speed
        if self._clock: # Restart the clock
            self.play()


# In[4]:


class Player(VBox):
    value = traitlets.Any()
    def __init__(self, view):
        model = PlayerModel(view, self)
        self._model = model

        layout  = Layout(width="initial")
        step_backward = Button(tooltip="Step backward", icon="step-backward", layout=layout)
        step_forward  = Button(tooltip="Step forward",  icon="step-forward",  layout=layout)
        begin         = Button(tooltip="Begin",         icon="fast-backward", layout=layout)
        end           = Button(tooltip="End",           icon="fast-forward",  layout=layout)
        backward      = Button(tooltip="Play backward", icon="backward",      layout=layout)
        play          = Button(tooltip="Play",          icon="play",          layout=layout)
        pause         = Button(tooltip="Pause",         icon="pause",         layout=layout)

        step_backward.on_click(lambda button: model.step_backward())
        step_forward .on_click(lambda button: model.step_forward())
        begin        .on_click(lambda button: model.begin())
        end          .on_click(lambda button: model.end())
        play         .on_click(lambda button: model.play(1))
        backward     .on_click(lambda button: model.play(-1))
        pause        .on_click(lambda button: model.stop())
        frame_label = Label("frame: ")
        frame = Label("")
        self._frame = frame
        speed_label = Label("speed: ")
        speed_slider = IntSlider(0,0,10,1)
        speed_slider.observe(lambda slider: model.set_speed(speed_slider.value))
        controller = HBox([begin, backward, step_backward, pause, play, step_forward, end, frame_label, frame, speed_label, speed_slider])
        VBox.__init__(self, [view, controller])

    @traitlets.observe("value")
    def value_changed(self, change):
        self._model.set_value(change.new)
