
#############MotorControlSkript#############

from time import sleep
import RPi.GPIO as GPIO
import tkinter as tk
import math as m
from threading import Thread


class Motor():

    instances = []  # list of all motor instances
    ui = None  # UI element to which Elemens should be added

    def __init__(self, pin_dir, pin_step, pin_off, pin_sens, num=None, state=None, ui=None):
        self.num = num if num else len(Motor.instances)+1  # get number by parameter or counter
        self.state = state if state else 'waiting'  # default state is waiting
        self.pin_dir = pin_dir  # direction
        self.pin_step = pin_step  # step
        self.pin_off = pin_off  # kill switch
        self.pin_sens = pin_sens  # lightsensor at the end of syringe track (empty volume)
        self.setup()  # setup GPIO pins
        Motor.ui = ui if ui else Motor.ui  # overwrite Class wide UI parent element if specified
        self.create_ui()  # make buttons
        Motor.instances.append(self)  # keep track of this instance Class wide

    def setup(self):
        GPIO.setup(self.pin_dir, GPIO.OUT)
        GPIO.output(self.pin_dir, False)
        GPIO.setup(self.pin_step, GPIO.OUT)
        GPIO.output(self.pin_step, False)
        GPIO.setup(self.pin_off, GPIO.OUT)
        GPIO.output(self.pin_off, False)
        GPIO.setup(self.pin_sens, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    # create all the UI elements for one motor control
    def create_ui(self):
        if not Motor.ui:
            return
        root = Motor.ui
        s = len(Motor.instances)+1
        lt = tk.Label(root, text='Syringe %d:' % self.num, width=10)
        lt.grid(row=s, column=0)
        self.flow = tk.Entry(root, width=6)
        self.flow.grid(row=s, column=1)
        lf = tk.Label(root, text='ul/h', width=4)
        lf.grid(row=s, column=2)
        self.volume = tk.Entry(root, width=6)
        self.volume.grid(row=s, column=3)
        lv = tk.Label(root, text='ul', width=4)
        lv.grid(row=s, column=4)
        self.btn_run = tk.Button(root, text='Run', bg='green', width=4, command=self.start)
        self.btn_run.grid(row=s, column=5)
        self.btn_stop = tk.Button(root, text='Stop', bg='red', width=4, command=self.stop, state=tk.DISABLED)
        self.btn_stop.grid(row=s, column=6)
        self.btn_load = tk.Button(root, text='Load', bg='gold', width=4, command=self.load)
        self.btn_load.grid(row=s, column=7)
        self.status = tk.Label(root, text='ready', width=20)
        self.status.grid(row=s, column=8)

    # update state and change status label text
    def update(self, state=None):
        if state:  # if state not specify, just update UI element
            self.state = state
        if Motor.ui:  # only if UI is used
            self.status['text'] = self.state

    def freeze(self):  # disable all buttons except STOP
        self.flow.configure(state=tk.DISABLED)
        self.volume.configure(state=tk.DISABLED)
        self.btn_run.configure(state=tk.DISABLED)
        self.btn_load.configure(state=tk.DISABLED)
        self.btn_stop.configure(state=tk.NORMAL)

    def unfreeze(self):  # enable all buttons exept STOP
        self.flow.configure(state=tk.NORMAL)
        self.volume.configure(state=tk.NORMAL)
        self.btn_run.configure(state=tk.NORMAL)
        self.btn_load.configure(state=tk.NORMAL)
        self.btn_stop.configure(state=tk.DISABLED)

    def stop(self):  # signal to thead to stop
        self.update('stopped')

    def blocked(self):  # check lightbarrier
        return GPIO.input(self.pin_sens) == 0

    # actual pumping function run in thread
    def run(self):
        rate = self.flow.get()
        try:
            rate = float(rate)
        except:
            self.status['text'] = 'illegal flow'
            return
        flow = 3600/(rate/(((2.36)*(2.36))*m.pi*1.25/6400))
        while self.state == 'running':
            if self.blocked():
                self.update('DONE!')
                break
            self.move(wait=flow/2)
        self.unfreeze()

    # start normal pumping action in a new thread
    def start(self):
        if self.blocked():
            self.update('already @ max')
            return
        self.update('running')
        self.freeze()
        t = Thread(target=self.run)
        t.start()

    # move motor by one step in given direction
    def move(self, forward=True, wait=0.1):
        GPIO.output(self.pin_dir, forward)
        GPIO.output(self.pin_step, True)
        sleep(wait)
        GPIO.output(self.pin_step, False)
        sleep(wait)

    # loading routine run in thread
    def reset(self):
        volume = self.volume.get()
        try:
            volume = float(volume)
        except:
            self.status['text'] = 'illegal volume'
            return
        steps = int(volume*6400/(2.36)*(2.36)*m.pi)
        # reset the motor into empty volume position first
        while self.state == 'reset':
            if self.blocked():
                self.update('loading')
                break
            self.move()
        for i in range(steps):
            if self.state != 'loading':
                break
            self.status['text'] = 'loading step %d' % i
            self.move(forward=False, wait=0.01)
        self.unfreeze()

    # start loading thread
    def load(self):
        self.update('reset')
        self.freeze()
        t = Thread(target=self.reset)
        t.start()

    def NOT_AUS():
        for i in Motor.instances:
            GPIO.output(i.pin_off, True)
            i.stop()
            i.freeze()

    def UNDO():
        for i in Motor.instances:
            GPIO.output(i.pin_off, False)
            i.stop()
            i.unfreeze()


def press(key):  # function for the keypad action
    entry = root.focus_get()
    if not isinstance(entry, tk.Entry):
        return
    if key == 'del':
        entry.delete(len(entry.get())-1, tk.END)
    elif key == 'clear':
        entry.delete(0, tk.END)
    else:
        entry.insert(tk.END, key)


if __name__ == '__main__':

    ###############
    # Setup GPIO pin(s)
    GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(False)


    ### UI
    root = tk.Tk()

    ### Keypad
    keypad = tk.Frame(root)
    keypad.grid(row=0, column=0)
    for i in range(1, 10):
        s = '%d' % i
        tk.Button(keypad, text=s, bg='grey50', width=4,
                  command=lambda x=s: press(x)).grid(row=int((i-1)/3), column=(i-1)%3)

    tk.Button(keypad, text='.', bg='grey70', width=4,
              command=lambda x='.': press(x)).grid(row=3, column=0)
    tk.Button(keypad, text='0', bg='grey50', width=4,
              command=lambda x='0': press(x)).grid(row=3, column=1)
    tk.Button(keypad, text='del', bg='grey70', width=4,
              command=lambda x='del': press(x)).grid(row=3, column=2)
    tk.Button(keypad, text='clear', bg='grey80', width=15,
              command=lambda x='clear': press(x)).grid(row=4, columnspan=3)

    tk.Button(keypad, text='NOT_AUS', bg='firebrick', height=1, width=15,
              command=Motor.NOT_AUS).grid(row=0, column=4)
    tk.Button(keypad, text='UNDO', bg='chartreuse4', height=1, width=15,
              command=Motor.UNDO).grid(row=1, column=4)

    ### Motor controls
    motor_frame = tk.Frame(root)  # motor controls have their own frame
    motor_frame.grid(row=1, columnspan=2)

    # set UI parent element for all motors
    Motor.ui = motor_frame

    motors = [Motor(pin_dir=3, pin_step=5, pin_off=7, pin_sens=40),
              Motor(13, 15, 11, 21),
              Motor(21, 23, 19, 37),
              Motor(33, 31, 29, 36)]

    root.mainloop()
