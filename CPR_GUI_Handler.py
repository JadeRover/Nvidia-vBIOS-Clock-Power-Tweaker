import tkinter as tk
import os
from tkinter import filedialog as fd
from CPR_calculator import parsed_data

class GUI_handler:
    def __init__(self):
        self.GUI = 0
        self.vbios_data = 0
        
    def link_GUI(self, GUI):
        self.GUI = GUI
        
    def select_file(self):
        
        filetypes = (
            ('bin files', '*.bin'),
            ('rom files', '*.rom'),
            ('All files', '*.*')
        )

        filename = fd.askopenfilename(
            title='Open a file',
            initialdir='/',
            filetypes=filetypes)
        
        if len(filename) > 0 :
            self.GUI.bios_name_entry["state"] = 'normal'
            self.GUI.bios_name_entry.delete(0, tk.END)
            self.GUI.bios_name_entry.insert(tk.INSERT, os.path.split(filename)[1])
            self.GUI.bios_name_entry["state"] = 'disabled'
            
            self.GUI.console["state"] = "normal"
            self.GUI.console.insert(tk.INSERT, "\n\n"+"=======================")
            self.GUI.console.insert(tk.INSERT, "\n\n" + "Opened " + filename +" vbios file")
            self.GUI.console["state"] = "disabled"
            
            with open(filename, "rb") as f:
                    self.vbios_data = parsed_data(f.read())
            
            self.load_clocks_to_GUI()
            self.load_power_to_GUI()
            self.set_architecture()
        
    def load_clocks_to_GUI(self):
        
        # Loads to stock clocks into the entries of the clock tab of the GUI
        clock_list = self.vbios_data.return_sorted_calculated_clock_list()  
        
        default_mem_value = 0
        # CHECK IF DIFFERENT MEM VALUES = IMPORTANT TO NOTIFY THE USER
        mem_list = self.vbios_data.get_MEM_clock_list()
        if mem_list == [] : #NOT VBIOS
            mem_list=[[]]
        if len(mem_list[0]) < 3:
            clock_list.pop()
            clock_list.append(default_mem_value)
            self.GUI.console["state"] = "normal"
            self.GUI.console.insert(tk.INSERT, "\n\n"+"ERROR : Memory table is not in the expected format, values will be null")
            self.GUI.console["state"] = "disabled"
        else :
            minimum = mem_list[0][1][0]
            if minimum > (mem_list[0][2][0] +2):
                minimum = round(mem_list[0][2][0] * 2) 
                clock_list.pop()
                clock_list.append(minimum)
                self.GUI.console["state"] = "normal"
                self.GUI.console.insert(tk.INSERT, "\n\n"+"2 different memory clock values found")
                self.GUI.console.insert(tk.INSERT, " stock vbios set to minimum out of the two")
                self.GUI.console.insert(tk.INSERT, " saving vbios will overwrite both to the one you set")
                self.GUI.console["state"] = "disabled"
            
    
            
        OG_entry_list = [self.GUI.OG_idle, self.GUI.OG_base, self.GUI.OG_boost, self.GUI.OG_max, self.GUI.OG_mem]
        CUSTOM_entry_list = [self.GUI.custom_idle, self.GUI.custom_base, self.GUI.custom_boost, self.GUI.custom_max, self.GUI.custom_mem]
        
        if clock_list[0] == -1:
            self.GUI.console["state"] = "normal"
            self.GUI.console.insert(tk.INSERT, "\n\n"+"ERROR : Clock table is not in the expected format, values will be all -1")
            self.GUI.console["state"] = "disabled"
        for index in range(len(clock_list)):
            OG_entry_list[index].config(state="normal")
            OG_entry_list[index].delete(0, "end")
            OG_entry_list[index].insert(0, clock_list[index])
            OG_entry_list[index].config(state="disabled")
            
            # 2. Update Custom Spinboxes via their TextVariables
            # This is the ONLY way to update a StringVar/IntVar
            CUSTOM_entry_list[index].set(clock_list[index])           
        
        
        
    def load_power_to_GUI(self):
        COMPLETE_power_list = self.vbios_data.get_power_table_list()[0]
        
        OG_entry_list = [self.GUI.OG_target, self.GUI.OG_limit]
        CUSTOM_entry_list = [self.GUI.custom_target, self.GUI.custom_limit]
        
        if COMPLETE_power_list != -1:
        
            power_list = [COMPLETE_power_list[0][0]/1000,COMPLETE_power_list[1][0]/1000] 
    
            
            if COMPLETE_power_list[0][0] == 0:
                self.GUI.console["state"] = "normal"
                self.GUI.console.insert(tk.INSERT, "\n\n"+"ERROR : Power values unfindable, set to 0 as default, happens for desktop cards, power slider reading should work however")
                self.GUI.console["state"] = "disabled"
            
            for index in range(len(power_list)):
                OG_entry_list[index].config(state="normal")
                OG_entry_list[index].delete(0, "end")
                OG_entry_list[index].insert(0, power_list[index])
                OG_entry_list[index].config(state="disabled")
                
                CUSTOM_entry_list[index].set(power_list[index])
            
            # Slider calculationss :
            COMPLETE_power_list.pop(0)
            COMPLETE_power_list.pop(0)
            #Remove the 2 power values
            
            slider_var = 0
            if len(COMPLETE_power_list) == 1: #If there is only one slider value
                slider_var = str(COMPLETE_power_list[0][0])
            elif len(COMPLETE_power_list) == 0:
                self.GUI.console["state"] = "normal"
                self.GUI.console.insert(tk.INSERT, "\n\n"+"ERROR : Power slider unfindable ! (not even unknown !) do not set anything ! happens for P6 quadro cards")
                self.GUI.console["state"] = "disabled"
            else:
                if COMPLETE_power_list[0][0] == COMPLETE_power_list[1][0]:
                    slider_var = str(COMPLETE_power_list[0][0])
                else :
                    slider_var = "Unknown"
            
            self.GUI.OG_slider.set(slider_var)
            self.GUI.custom_slider.set(slider_var)
        
        else :
            self.GUI.console["state"] = "normal"
            self.GUI.console.insert(tk.INSERT, "\n\n"+"ERROR : File is not a (Pascal-Lovelace) vBIOS structure")
            self.GUI.console["state"] = "disabled"            
            
            self.GUI.OG_slider.set("Unknown")
            self.GUI.custom_slider.set("Unknown")
            
            for index in range(2):
                OG_entry_list[index].config(state="normal")
                OG_entry_list[index].delete(0, "end")
                OG_entry_list[index].insert(0, 0)
                OG_entry_list[index].config(state="disabled")
                
                CUSTOM_entry_list[index].set(0)
        
    def set_architecture(self):
        self.GUI.architecture.set(self.vbios_data.get_card_architecture())
        