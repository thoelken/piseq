
#############MotorControlSkript#############

from time import sleep
import RPi.GPIO as GPIO
import tkinter as tk
import math as m
from threading import Thread
from configparser import ConfigParser


def load_config(filename='GPIO.conf'):
    cfg = ConfigParser()
    cfg.read(filename)
    return cfg


#### class parameter für speed, steps und control functions
class Parameter():
    def __init__(self, flow, steps, dir_pin, step_pin, aus_pin, light_pin, disp_flow, disp_vol, disp_status, entry):
        self.flow = flow
        self.steps = steps
        self.task = 'waiting'
        self.dir_pin = dir_pin
        self.step_pin = step_pin
        self.aus_pin = aus_pin
        self.light_pin = light_pin
        self.disp_flow = disp_flow
        self.disp_vol = disp_vol
        self.disp_status = disp_status
        self.entry = entry

    def setup(self):
        GPIO.setup(self.dir_pin, GPIO.OUT)
        GPIO.output(self.dir_pin, False)
        GPIO.setup(self.step_pin, GPIO.OUT)
        GPIO.output(self.step_pin, False)
        GPIO.setup(self.aus_pin, GPIO.OUT)
        GPIO.output(self.aus_pin, False)
        GPIO.setup(self.light_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    def save_volume(self):
        volume = float(self.entry.get())
        self.steps = round(volume*6400/(2.36)*(2.36)*m.pi)
        self.disp_vol['text'] = '%d ul' % volume

    def save_flow(self):
        rate = float(self.entry.get())
        self.flow = 3600/(rate/(((2.36)*(2.36))*m.pi*1.25/6400))
        self.disp_flow['text'] = '%d ul' % rate
        
    def start(self):
        self.task = 'running'
        
    def stop(self):
        self.task = 'waiting'
        
    def load(self):
        self.task = 'reset'
      
      
        
def NOT_AUS(par):
    for p in par:
        GPIO.output(p.aus_pin, True)
    disp.delete(1.0, tk.END)
    disp.insert(tk.END,'Not Aus')
    
    
def Undo_NOT_AUS(par):
    for p in par:
        GPIO.output(p.aus_pin, False)
    disp.delete(1.0, tk.END)
    disp.insert(tk.END,'Undo Not Aus') 
    
    
def Quit(par):
   for p in par:
        p.task = 'stopped'
    

class Motor():

    count = 0
    
    def __init__(self, pin_dir, pin_step, pin_off, pin_sens, num=None, state=None, ui=None):
        Motor.count += 1
        self.num = num if num else Motor.count
        self.state = state if state else 'waiting'
        self.pin_dir = pin_dir
        self.pin_step = pin_step
        self.pin_off = pin_off
        self.pin_sens = pin_sens
        self.setup()
        self.ui = ui
        if ui:
            self.create_ui()
        
    def setup(self):
        GPIO.setup(self.pin_dir, GPIO.OUT)
        GPIO.output(self.pin_dir, False)
        GPIO.setup(self.pin_step, GPIO.OUT)
        GPIO.output(self.pin_step, False)
        GPIO.setup(self.pin_off, GPIO.OUT)
        GPIO.output(self.pin_off, False)
        GPIO.setup(self.pin_sens, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        
    def create_ui(self, root):
        root = self.ui
        s = self.num
        self.dt = tk.Label(root, text='Syringe %d:' % s, width=10)
        self.dt.grid(row=s, column=0)
        self.flow = tk.Entry(root)
        self.flow.grid(row=s, column=1)
        lf = tk.Label(root, text='ul/h', width=4)
        lf.grid(row=s, column=2)
        self.volume = tk.Entry(root)
        self.volume.grid(row=s, column=3)
        lv = tk.Label(root, text='ul/h', width=4)
        lv.grid(row=s, column=4)
        self.br = tk.Button(root, text='Run' % s, bg='green', width=4, command=self.start)
        self.br.grid(row=s, column=5)
        self.bs = tk.Button(root, text='Stop' % s, bg='red', width=4, command=self.stop, state=tk.DISABLED)
        self.bs.grid(row=s, column=6)
        self.bl = tk.Button(root, text='Load' % s, bg='gold', width=4, command=self.load)
        self.bl.grid(row=s, column=7)
        self.status = tk.Label(root, text='ready', width=10)
        self.status.grid(row=s, column=8)
        
    def update(self, state=None):
        if state:
            self.state = state
        if self.ui:
            self.status['text'] = self.state   
          
    def freeze(self):
        self.flow.configure(state=tk.DISABLED)
        self.volume.configure(state=tk.DISABLED)
        self.br.configure(state=tk.DISABLED)
        self.bl.configure(state=tk.DISABLED)
        self.bs.configure(state=tk.NORMAL)
        
    def unfreeze(self):
        self.flow.configure(state=tk.NORMAL)
        self.volume.configure(state=tk.NORMAL)
        self.br.configure(state=tk.NORMAL)
        self.bl.configure(state=tk.NORMAL)
        self.bs.configure(state=tk.DISABLED)
           
    def stop(self):
        self.update('stopped')
        #self.unfreeze()
    
    def _run(self):
        rate = float(self.flow.get())
        flow = 3600/(rate/(((2.36)*(2.36))*m.pi*1.25/6400))
        while self.state == 'running':
            if GPIO.input(self.pin_sens) == 1:
                self.update('DONE!')
                break
            GPIO.output(self.p.dir_pin, True) 
            GPIO.output(self.p.step_pin,True)
            sleep(flow/2)
            GPIO.output(self.p.step_pin, False)
            sleep(flow/2)
        self.unfreeze()
            
    def start(self):
        if GPIO.input(self.pin_sens) == 1:
            self.update('already @ max')
            return
        self.update('running')
        self.freeze()
        t = Thread(target=self._run)
        t.start()
        
    def _reset(self):
        while self.state == 'reset':
            if GPIO.input(self.pin_sens) == 1:
                self.update('loading')
                break
        GPIO.output(self.p.dir_pin, False) 
        for i in range(steps):
            if self.state != 'loading':
                break
            self.status['text'] = '%s step %d' % (self.p.task, i) 
            sleep(0.1)
            GPIO.output(self.p.step_pin, False)
            sleep(0.1)
        self.unfreeze()
            
    def load(self):
        if GPIO.input(self.pin_sens) == 1:
            self.update('already @ max')
            return
        self.update('reset')
        
        self.freeze()
        t = Thread(target=self._reset)
        t.start()
        


###### thread für Motorcontrol

class Motorcontrol (th.Thread):
    def __init__(self, param, num):
        th.Thread.__init__(self)
        self.p = param
        self.p.setup()
        self.num = num
        
        GPIO.setup(self.p.step_pin, GPIO.OUT)
        GPIO.output(self.p.step_pin, False)
        
        GPIO.setup(self.p.dir_pin, GPIO.OUT)
        GPIO.output(self.p.dir_pin, False)
        
        GPIO.setup(self.p.light_pin, GPIO.IN) 
    
    def run (self):
        
        while True: #mainloop
            
            blocked = GPIO.input(self.p.light_pin) == 1
            
            if self.p.task == 'stopped':
                self.p.disp_status['text'] = self.p.task
                break
            elif self.p.task == 'reset':
                if blocked:
                    self.p.task = 'loading'
                    continue
                self.p.disp_status['text'] = self.p.task
                GPIO.output(self.p.dir_pin, True)            
                GPIO.output(self.p.step_pin,True)
                sleep(0.1)
                GPIO.output(self.p.step_pin, False)
                sleep(0.1) 
            elif self.p.task == 'waiting':
                self.p.disp_status['text'] = self.p.task
                sleep(1)
            elif self.p.task == 'running': 
                if blocked:
                    self.p.task = 'waiting'
                    continue
                GPIO.output(self.p.dir_pin, True) 
                GPIO.output(self.p.step_pin,True)
                sleep(self.p.flow/2)
                GPIO.output(self.p.step_pin, False)
                sleep(self.p.flow/2)
                self.p.disp_status['text'] = self.p.task              
            elif self.p.task == 'loading':
                self.p.disp_status['text'] = self.p.task                 
                GPIO.output(self.p.dir_pin, False) 
                for i in range(self.p.steps):
                    if self.p.task in ['waiting', 'stopped']:
                        break
                    GPIO.output(self.p.step_pin,True)
                    self.p.disp_status['text'] = '%s step %d' % (self.p.task, i) 
                    sleep(0.1)
                    GPIO.output(self.p.step_pin, False)
                    sleep(0.1)
                self.p.task = 'waiting'
                self.p.disp_status['text'] = 'done'
                sleep(1)
            else:
                self.p.disp_status['text'] = '%s (error)' % (self.p.task)
                sleep(1)
               
            


if __name__ == '__main__':

    ###############
    # Setup GPIO pin(s)
    GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(False)

    root = tk.Tk()

    ##### Displays

    entry = tk.Entry(root)
    entry.grid(row=0,columnspan=3)

    disp = tk.Text(root, height=2, width  = 50)
    disp.grid(row=0, column=5, columnspan=5)
    
    #Notau und Quit Buttons

    b_notaus = tk.Button(root,text='NOT_AUS', bg= 'firebrick', height = 2, width = 15)
    b_notaus.grid(row=0, column=3 )
    b_undonotaus = tk.Button(root,text='Undo', bg = 'chartreuse4',height = 2, width = 10)
    b_undonotaus.grid(row=0, column=4,)

    b_notaus.bind("<Button-1>", lambda x: control.NOT_AUS())
    b_undonotaus.bind("<Button-1>", lambda x: control.Undo_NOT_AUS()) 
    
    b1 = tk.Button(root,text='1', bg = 'grey70', width = 5)
    b1.grid(row=1,column=0)
    b2 = tk.Button(root,text='2', bg = 'grey70', width = 5)
    b2.grid(row=1,column=1)
    b3 = tk.Button(root,text='3', bg = 'grey70', width = 5)
    b3.grid(row=1,column=2)
    b4 = tk.Button(root,text='4', bg = 'grey70', width = 5)
    b4.grid(row=2,column=0)
    b5 = tk.Button(root,text='5', bg = 'grey70', width = 5)
    b5.grid(row=2,column=1)
    b6 = tk.Button(root,text='6', bg = 'grey70', width = 5)
    b6.grid(row=2,column=2)
    b7 = tk.Button(root,text='7', bg = 'grey70', width = 5)
    b7.grid(row=3,column=0)
    b8 = tk.Button(root,text='8', bg = 'grey70', width = 5)
    b8.grid(row=3,column=1)
    b9 = tk.Button(root,text='9', bg = 'grey70', width = 5)
    b9.grid(row=3,column=2)
    b0 = tk.Button(root,text='0', bg = 'grey70', width = 5)
    b0.grid(row=4,column=1)
    bp = tk.Button(root,text='.', bg = 'grey70', width = 5)
    bp.grid(row=4,column=2)
    bdel = tk.Button(root,text='del', bg = 'grey', width = 5)
    bdel.grid(row=4,column=0)

    b1.bind("<Button-1>", lambda x: entry.insert(tk.END,"1"))

    b2.bind("<Button-1>", lambda x: entry.insert(tk.END,"2"))
    b3.bind("<Button-1>", lambda x: entry.insert(tk.END,"3"))
    b4.bind("<Button-1>", lambda x: entry.insert(tk.END,"4"))
    b5.bind("<Button-1>", lambda x: entry.insert(tk.END,"5"))
    b6.bind("<Button-1>", lambda x: entry.insert(tk.END,"6"))
    b7.bind("<Button-1>", lambda x: entry.insert(tk.END,"7"))
    b8.bind("<Button-1>", lambda x: entry.insert(tk.END,"8"))
    b9.bind("<Button-1>", lambda x: entry.insert(tk.END,"9"))
    b0.bind("<Button-1>", lambda x: entry.insert(tk.END,"0"))
    bp.bind("<Button-1>", lambda x: entry.insert(tk.END,"."))
    bdel.bind("<Button-1>", lambda x: entry.delete(0,tk.END))

    disp_flow, disp_vol, disp_text, disp_status = [], [], [], []
    btn_flow, btn_vol, btn_run, btn_stop, btn_load = [], [], [], [], []
    for i in range(4):
        s = i+1

        bf = tk.Button(root,text='set flow M%d' % s, bg='DodgerBlue', width = 8)
        bf.grid(row=s, column=3)
        btn_flow.append(bf)

        df = tk.Label(root, text='ul/h', width=10)
        df.grid(row=s, column=4)
        disp_flow.append(df)
        
        bv = tk.Button(root,text='set vol M%d' % s, bg='DodgerBlue', width = 8)
        bv.grid(row=s, column=5)
        btn_vol.append(bv)
        
        dv = tk.Label(root, text='ml', width=10)
        dv.grid(row=s, column=6)
        disp_vol.append(dv)
        
        br = tk.Button(root,text='run M%d' % s, bg='chartreuse1', width = 8)
        br.grid(row=s, column=7)
        btn_run.append(br)
        
        bs = tk.Button(root,text='stop M%d' % s, bg='DarkOrange', width = 8)
        bs.grid(row=s, column=8)
        btn_stop.append(bs)
        
        bl = tk.Button(root,text='loading M%d' % s, bg='gold', width = 8)
        bl.grid(row=s, column=9)
        btn_load.append(bl)
        
        dt = tk.Label(root, text='Syringe %d:' % s, width=10)
        dt.grid(row=s+4, column=3)
        disp_text.append(dt)
        
        ds = tk.Label(root, text='ready', width=10)
        ds.grid(row=s+4, column=4)
        disp_status.append(ds)

        
    params = [Parameter(flow=0, steps=0, dir_pin=3, step_pin=5, aus_pin=7, light_pin=40, disp_flow=disp_flow[0], disp_vol=disp_vol[0], disp_status=disp_status[0], entry=entry),
              Parameter(0, 0, 13, 15, 11, 21, disp_flow[1], disp_vol[1], disp_status[1], entry),
              Parameter(0, 0, 21, 23, 19, 37, disp_flow[2], disp_vol[2], disp_status[2], entry),
              Parameter(0, 0, 33, 31, 29, 36, disp_flow[3], disp_vol[3], disp_status[3], entry)]
              
              
    for i in range(4):
        btn_flow[i].bind("<Button-1>", lambda x: params[i].save_flow())
        btn_vol[i].bind("<Button-1>", lambda x: params[i].save_volume())
        btn_run[i].bind("<Button-1>", lambda x: params[i].start())
        btn_stop[i].bind("<Button-1>", lambda x: params[i].stop())
        btn_load[i].bind("<Button-1>", lambda x: params[i].load())

    btn_run[2].configure(background='white')
    
    threads = [Motorcontrol(p, i) for i, p in enumerate(params)]
    for t in threads:
        t.start()
        
        #Notau und Quit Buttons

    b_notaus = tk.Button(root,text='NOT_AUS', bg= 'firebrick', height = 2, width = 15)
    b_notaus.grid(row=0, column=3 )
    b_undonotaus = tk.Button(root,text='Undo', bg = 'chartreuse4',height = 2, width = 10)
    b_undonotaus.grid(row=0, column=4,)

    b_notaus.bind("<Button-1>", lambda x: NOT_AUS(params))
    b_undonotaus.bind("<Button-1>", lambda x: Undo_NOT_AUS(params)) 

    bquit = tk.Button(root,text='Quit', bg = 'firebrick', width = 15, height= 2)
    bquit.grid(row=6,columnspan = 3)

    bquit.bind("<Button-1>", lambda x: Quit(params))

    root.mainloop()   


