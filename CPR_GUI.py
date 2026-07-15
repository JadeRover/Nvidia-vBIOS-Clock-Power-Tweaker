import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext

import os
import sys #FOR icon bruh

class CPR_GUI(tk.Tk):
    
    def __init__(self, GUI_handler):
        super().__init__()
        
        #VERY IMPORTANT TO LINK HANDLER
        
        self.GUI_handler = GUI_handler
        GUI_handler.link_GUI(self)
        
        ###
        
        self.geometry("820x720")
        self.resizable(False, False)
        
        self.title("Clock Power Reader v1.3.4")
        
        try:
            self.iconbitmap(self.resource_path('favicon.ico'))
        except Exception:
            pass
        
        
        # CONFIGURE ROWS for the entire "windows" = for the fixed elements such as tabs, console, info/actions
        
        self.grid_columnconfigure(0, weight=60)
        self.grid_columnconfigure(1, weight=40)
        
        self.grid_rowconfigure(0, weight=55)
        self.grid_rowconfigure(1, weight=23)
        self.grid_rowconfigure(2, weight=22)
        
        #================================================================================#
        # DEFINE TABS SECTION
        
        tabs_frame = tk.Frame(self, bg="grey", bd=3, relief="raised")
        tabs_frame.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=3, pady=3)
        
        tab_control = ttk.Notebook(tabs_frame)
        tab_control.pack(expand=1,fill="both")
        
        #================================================================================#
        
        # DEFINE GUI ELEMENTS OF THE CLOCK TAB
        
        clock_tab = ttk.Frame(tab_control)
        tab_control.add(clock_tab, text ='  Clocks  ')
        
        clock_tab.grid_columnconfigure(0, weight=5)
        clock_tab.grid_columnconfigure(1, weight=10)
        clock_tab.grid_columnconfigure(2, weight=10)
        
        clock_tab.grid_propagate(False)
        
        ttk.Label(clock_tab, text ="Stock vBIOS values (MHz) :").grid(column = 1, row = 0, padx=3, pady=3)  
        ttk.Label(clock_tab, text ="Custom values (MHz) :").grid(column = 2, row = 0,padx=3, pady=3)  
        
        ttk.Label(clock_tab, text ="Idle Clock :").grid(column = 0, row = 1, padx=3, pady=3)  
        ttk.Label(clock_tab, text ="Base Clock :").grid(column = 0, row = 2,padx=3, pady=3)
        ttk.Label(clock_tab, text ="Boost Clock :").grid(column = 0, row = 3, padx=3, pady=3)  
        ttk.Label(clock_tab, text ="Max clock :").grid(column = 0, row = 4,padx=3, pady=3)
        ttk.Label(clock_tab, text ="").grid(column = 0, row = 5,padx=3, pady=3)
        ttk.Label(clock_tab, text ="MEM boost clock :").grid(column = 0, row = 6,padx=3, pady=3)   
        
        # The OG entries from the vbios
        
        self.OG_idle = ttk.Entry(clock_tab, state="disabled")
        self.OG_idle.grid(column = 1, row = 1,padx=10, pady=3, sticky="ew")
        
        self.OG_base = ttk.Entry(clock_tab, state="disabled")
        self.OG_base.grid(column = 1, row = 2,padx=10, pady=3, sticky="ew")
        
        self.OG_boost = ttk.Entry(clock_tab, state="disabled")
        self.OG_boost.grid(column = 1, row = 3,padx=10, pady=3, sticky="ew")
        
        self.OG_max = ttk.Entry(clock_tab, state="disabled")
        self.OG_max.grid(column = 1, row = 4,padx=10, pady=3, sticky="ew")
        
        self.OG_mem = ttk.Entry(clock_tab, state="disabled")
        self.OG_mem.grid(column = 1, row = 6, padx=10, pady=3, sticky="ew")
        
        #VARIABLES of the clock entries :
            
        self.custom_idle = tk.StringVar(self, 0)
        self.custom_base = tk.StringVar(self, 0)
        self.custom_boost = tk.StringVar(self, 0)
        self.custom_max = tk.StringVar(self, 0)
        self.custom_mem =tk.StringVar(self, 0)
        
        # The custom entries set by the user, you :)
        
        self.CUSTOM_idle_clock_entry = ttk.Spinbox(clock_tab, textvariable=self.custom_idle ,from_=100,to=2500,increment=1,validate="key",
            validatecommand=(self.register(self._validate), "%P"))
        self.CUSTOM_idle_clock_entry.grid(column= 2, row=1, padx=10, pady=3, sticky="ew")
        self.CUSTOM_base_clock_entry = ttk.Spinbox(clock_tab, textvariable=self.custom_base ,from_=100,to=2500,increment=1,validate="key",
            validatecommand=(self.register(self._validate), "%P"))
        self.CUSTOM_base_clock_entry.grid(column= 2, row=2, padx=10, pady=3, sticky="ew")
        self.CUSTOM_boost_clock_entry = ttk.Spinbox(clock_tab, textvariable=self.custom_boost ,from_=100,to=2500,increment=1,validate="key",
            validatecommand=(self.register(self._validate), "%P"))
        self.CUSTOM_boost_clock_entry.grid(column= 2, row=3, padx=10, pady=3, sticky="ew")
        self.CUSTOM_max_clock_entry = ttk.Spinbox(clock_tab, textvariable=self.custom_max ,from_=100,to=2500,increment=1,validate="key",
            validatecommand=(self.register(self._validate), "%P"))
        self.CUSTOM_max_clock_entry.grid(column= 2, row=4, padx=10, pady=3, sticky="ew")
        self.CUSTOM_mem_clock_entry = ttk.Spinbox(clock_tab, textvariable=self.custom_mem ,from_=100,to=10000,increment=1,validate="key",
            validatecommand=(self.register(self._validate), "%P"))
        self.CUSTOM_mem_clock_entry.grid(column= 2, row=6, padx=10, pady=3, sticky="ew")
        
        ttk.Label(clock_tab, text="").grid(column = 0, columnspan=3, row = 7,padx=10, pady=3, sticky="ew")
        ttk.Label(clock_tab, text =
                  "Note : Max clock value might not be reached by the card if it runs into voltage \nlimit or power limit. The card adjustes voltage and power based on clock \nvalues defined here."
                  ).grid(column = 0, columnspan=5, row = 8,padx=30, pady=3, sticky="ew")
        
        #================================================================================#
        
        # DEFINE GUI ELEMENTS OF THE POWER TAB        
        
        power_tab = ttk.Frame(tab_control)
        
        tab_control.add(power_tab, text ='  Power  ')
        
        power_tab.grid_columnconfigure(0, weight=5)
        power_tab.grid_columnconfigure(1, weight=10)
        power_tab.grid_columnconfigure(2, weight=10)
        
        power_tab.grid_propagate(False)
        
        ttk.Label(power_tab, text ="Stock vBIOS values (W):").grid(column = 1, row = 0, padx=3, pady=3)  
        ttk.Label(power_tab, text ="Custom values (W):").grid(column = 2, row = 0,padx=3, pady=3)  
        
        ttk.Label(power_tab, text ="Target power :").grid(column = 0, row = 1, padx=3, pady=3)  
        ttk.Label(power_tab, text ="Limit power").grid(column = 0, row = 2,padx=3, pady=3)
        ttk.Label(power_tab, text ="Power slider :").grid(column = 0, row = 3, padx=3, pady=3)  
        ttk.Label(power_tab, text ="").grid(column = 0, row = 4,padx=3, pady=3)
        
        # The OG entries from the vbios
        
        self.OG_target = ttk.Entry(power_tab, state="disabled")
        self.OG_target.grid(column = 1, row = 1,padx=10, pady=3, sticky="ew")
        
        self.OG_limit = ttk.Entry(power_tab, state="disabled")
        self.OG_limit.grid(column = 1, row = 2,padx=10, pady=3, sticky="ew")
        
        self.OG_slider = tk.StringVar(self)
        
        ttk.Radiobutton(power_tab, text = "Enabled", variable = self.OG_slider,value = "True", state="disabled").grid(column=1, row=3, padx = 40, pady=3, sticky="w")
        ttk.Radiobutton(power_tab, text = "Disabled", variable = self.OG_slider,value = "False", state="disabled").grid(column=1, row=4, padx = 40, pady=3, sticky="w")
        ttk.Radiobutton(power_tab, text = "Unknown", variable = self.OG_slider,value = "Unknown", state="disabled").grid(column=1, row=5, padx = 40, pady=3, sticky="w")
        
        #VARIABLES of the power entries :
            
        self.custom_target = tk.StringVar(self)
        self.custom_limit = tk.StringVar(self)
        self.custom_slider = tk.StringVar(self)
        
        # The custom entries set by the user, you :)*2
        
        self.CUSTOM_target = ttk.Spinbox(power_tab, textvariable=self.custom_target ,from_=5,to=350,increment=1,validate="key",
            validatecommand=(self.register(self._validate), "%P"))
        self.CUSTOM_target.grid(column= 2, row=1, padx=10, pady=3, sticky="ew")
        self.CUSTOM_limit= ttk.Spinbox(power_tab, textvariable=self.custom_limit ,from_=5,to=350,increment=1,validate="key",
            validatecommand=(self.register(self._validate), "%P"))
        self.CUSTOM_limit.grid(column= 2, row=2, padx=10, pady=3, sticky="ew")
        
        ttk.Radiobutton(power_tab, text = "Enabled", variable = self.custom_slider,value = "True").grid(column=2, row=3, padx = 40, pady=3, sticky="w")
        ttk.Radiobutton(power_tab, text = "Disabled", variable = self.custom_slider,value = "False").grid(column=2, row=4, padx = 40, pady=3, sticky="w")
        ttk.Radiobutton(power_tab, text = "Leave as is", variable = self.custom_slider,value = "Unknown").grid(column=2, row=5, padx = 40, pady=3, sticky="w")

        
        ttk.Label(power_tab, text="").grid(column = 0, columnspan=3, row = 7,padx=10, pady=3, sticky="ew")
        ttk.Label(power_tab, text =

                  'Note : Limit power must be greater than or equal to target power\n"Unknown" slider only happens for ada quadro cards\n"Leave as is" is to not break these cards as other options \nwill force enabled or disabled power slider '

                  ).grid(column = 0, columnspan=5, row = 8,padx=30, pady=3, sticky="ew")
        
        #================================================================================#

        # DEFINE GUI ELEMENTS OF THE DISPLAY / DCB TAB

        display_tab = ttk.Frame(tab_control)
        tab_control.add(display_tab, text ='  Display / DCB  ')
        display_tab.grid_columnconfigure(0, weight=1)
        display_tab.grid_rowconfigure(0, weight=1)
        display_tab.grid_propagate(False)

        self.display_config_text = scrolledtext.ScrolledText(display_tab, wrap=tk.NONE, height=18)
        self.display_config_text.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.display_config_text.insert(tk.INSERT, "Open a vBIOS to view Pascal-Ada/Blackwell DCB display configuration.\nInternal eDP connector type is shown as 0x47.")
        self.display_config_text["state"] = "disabled"
        
        #================================================================================#
        
        # CONSOLE (bottom left of the windows)
        
        console_frame = tk.Frame(self, bg="white", bd=3, relief="raised")
        console_frame.grid(row=1, rowspan=2, column=0, sticky="nsew", padx=3, pady=3)
        console_frame.pack_propagate(False)
        console_frame.grid_propagate(False)
        
        console_label = tk.Label(console_frame, text="CONSOLE - OPERATIONS/ERRORS")
        console_label.pack(side='top', fill="x")
        
        self.console=scrolledtext.ScrolledText(console_frame)
        self.console.pack(side="top", fill='both', expand=0)
        self.console.insert(tk.INSERT, "Errors and operations \nwill appear in this window.")
        self.console["state"] = "disabled" #Annoying but works for now
        
        #================================================================================#
        
        # ACTION BUTTONS
        action_frame = tk.Frame(self, bg="lightgrey", bd=3, relief="raised")
        action_frame.grid(row=2, column=1, padx=3, pady=3, sticky="nsew")
        action_frame.grid_propagate(False)
        action_frame.grid_columnconfigure(0, weight=10)
        
        open_button = tk.Button(action_frame, text="OPEN FILE", command=self.GUI_handler.select_file)
        open_button.grid(row=0, column=0, padx=4, pady= 4, sticky="nsew")
        
        self.bios_name_entry = tk.Entry(action_frame, state="disabled")
        self.bios_name_entry.grid(row=1, column=0, rowspan=2, padx=4, pady= 4, sticky="nsew")
        
        self.save_button = tk.Button(action_frame, text="SAVE AS", command=self.GUI_handler.save_vbios, state="disabled")
        self.save_button.grid(row=4,padx=4, column=0, pady= 4, sticky="nsew")
        
        #================================================================================#
        
        # STRUCTURE windows
        
        structure_frame = tk.Frame(self, bg="lightgrey", bd=3, relief="raised")
        structure_frame.grid(row=1, column=1, padx=3, pady=3, sticky="nsew")
        structure_frame.grid_propagate(False)
        structure_frame.grid_columnconfigure(0, weight=33)
        structure_frame.grid_columnconfigure(1, weight=33)
        structure_frame.grid_columnconfigure(2, weight=33)
        
        structure_label = tk.Label(structure_frame, text='vBIOS ARCHITECTURE :')
        structure_label.grid(row=0, column=0, columnspan=3, sticky='ew')
        
        self.architecture = tk.StringVar(self)        
        
        ttk.Radiobutton(structure_frame, text = "Pascal", variable = self.architecture,value = "Pascal", state="disabled").grid(row=1, column=0, padx=2, pady=5, sticky='ew')
        ttk.Radiobutton(structure_frame, text = "Turing+", variable = self.architecture,value = "Turing & newer", state="disabled").grid(row=1, column=1, padx=2, pady=5, sticky='ew')
        ttk.Radiobutton(structure_frame, text = "Blackwell", variable = self.architecture,value = "Blackwell", state="disabled").grid(row=1, column=2, padx=2, pady=5, sticky='ew')

        # CHECKSUM section is removed -> Replaced by the "HEADER" section might add back later...
        
        """
        checksum_label = tk.Label(structure_frame, text='CHECKSUM (hex):')
        checksum_label.grid(row=2, column=0, columnspan=3, pady=5, sticky='ew')

        self.checksum_entry = tk.Entry(structure_frame, state="disabled")
        self.checksum_entry.grid(row=3, column=0, columnspan=3, padx=4, pady= 2, sticky="nsew") 
        """
        
        # HEADER sectioon :
        
        self.header = tk.StringVar(self)
        self.header.set("Remove")
        
        header_label = tk.Label(structure_frame, text='vBIOS HEADER :')
        header_label.grid(row=2, column=0, columnspan=3, pady=5, sticky='ew')
        
        # 2 OPTIONS : either none is found = text saying none is found
        #             one is found : create radio buttons to decide on weither to keep the header or not...
        
        self.header_radio_keep = ttk.Radiobutton(structure_frame, text = "Keep", variable = self.header,value = "Keep", state="disabled")
        self.header_radio_keep.grid(row=3, column=0, padx=2, pady=5, sticky='ew')
        self.header_radio_remove = ttk.Radiobutton(structure_frame, text = "Remove", variable = self.header,value = "Remove", state="disabled")
        self.header_radio_remove.grid(row=3, column=1, padx=2, pady=5, sticky='ew')
        ttk.Radiobutton(structure_frame, text = "None found", variable = self.header,value = "None", state="disabled").grid(row=3, column=2, padx=2, pady=5, sticky='ew')
        #================================================================================#
        
        # CODE for the UI elements #
        
    def _validate(self, P):
        return P.isdigit()
        
        #open_button.bind("<Button-1>", self.GUI_handler.select_file)
    
    #================================================================================#
    
    # BIND UI ELEMENTS TO CODE#  
        

    def resource_path(self,relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            # If not running as an EXE, use the normal current directory
            base_path = os.path.abspath(".")
    
        return os.path.join(base_path, relative_path)

#  TESTING = RUNNING