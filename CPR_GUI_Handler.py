import tkinter as tk
import os
from tkinter import filedialog as fd
from CPR_calculator import parsed_data
from CPR_Checksum import checksummer
import struct

class GUI_handler:
    
    def __init__(self):
        self.GUI = 0
        self.vbios_data = 0
        self.vbios_parsed = 0
        self.checksum_data = 0 
        
        #Vars used when saving the vbios = making sure the user can't save crap to his vbios (True by default):
        self.legal_core_clocks = False
        self.legal_mem_clocks = False
        self.legal_power = False
        self.legal_slider = False
        
        self.critical_save_vbios_error = False
        
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
            initialdir='/aéà',
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
                    self.vbios_data = f.read()
                    self.vbios_parsed = parsed_data(self.vbios_data)
            
            #EXECUTE OTHER FUNCTIONS
            
            self.checksum_data = checksummer(self.vbios_data)
            
            self.load_clocks_to_GUI()
            self.load_power_to_GUI()
            self.set_architecture()
            self.load_checksum_to_GUI()
            
            self.GUI.save_button["state"] = "normal"
            
            self.GUI.console.see(tk.END)
        
    def load_clocks_to_GUI(self):
        
        # Loads to stock clocks into the entries of the clock tab of the GUI
        clock_list = self.vbios_parsed.return_sorted_calculated_clock_list()  
        
        default_mem_value = 0
        
        
        # CHECK IF DIFFERENT MEM VALUES = IMPORTANT TO NOTIFY THE USER
        self.legal_mem_clocks = True
        mem_list = self.vbios_parsed.MEM_clock_list
        print(mem_list)
        if mem_list == [] : #NOT VBIOS
            mem_list=[[]]
            self.legal_mem_clocks = False
        if len(mem_list[0]) < 3:
            clock_list.pop()
            clock_list.append(default_mem_value)
            self.GUI.console["state"] = "normal"
            self.GUI.console.insert(tk.INSERT, "\n\n"+"ERROR : Memory table is not in the expected format, values will be null")
            self.GUI.console["state"] = "disabled"
            
            #VERY IMPORTANT
            self.legal_mem_clocks = False
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
        
        for index in range(len(clock_list)):
            OG_entry_list[index].config(state="normal")
            OG_entry_list[index].delete(0, "end")
            OG_entry_list[index].insert(0, round(clock_list[index]))
            OG_entry_list[index].config(state="disabled")
            
            # 2. Update Custom Spinboxes via their TextVariables
            # This is the ONLY way to update a StringVar/IntVar
            CUSTOM_entry_list[index].set(round(clock_list[index]))          
        
        
        #VERY IMPORTANT
        self.legal_core_clocks = True
        if clock_list[0] == -1:
            self.GUI.console["state"] = "normal"
            self.GUI.console.insert(tk.INSERT, "\n\n"+"ERROR : Clock table is not in the expected format, values will be all -1 and uneditable")
            self.GUI.console["state"] = "disabled"                
            self.legal_core_clocks = False
        
    def load_power_to_GUI(self):
        COMPLETE_power_list = self.vbios_parsed.get_power_table_list()[0]
        
        OG_entry_list = [self.GUI.OG_target, self.GUI.OG_limit]
        CUSTOM_entry_list = [self.GUI.custom_target, self.GUI.custom_limit]
        
        if COMPLETE_power_list != -1:
        
            power_list = [COMPLETE_power_list[0][0]/1000,COMPLETE_power_list[1][0]/1000] 
            
            self.legal_power = True
            
            if COMPLETE_power_list[0][0] == 0:
                self.GUI.console["state"] = "normal"
                self.GUI.console.insert(tk.INSERT, "\n\n"+"ERROR : Power values unfindable, set to 0 as default, happens for desktop cards, power slider reading should work however")
                self.GUI.console["state"] = "disabled"
                self.legal_power = False
            
            for index in range(len(power_list)):
                OG_entry_list[index].config(state="normal")
                OG_entry_list[index].delete(0, "end")
                OG_entry_list[index].insert(0, round(power_list[index]))
                OG_entry_list[index].config(state="disabled")
                
                CUSTOM_entry_list[index].set(round(power_list[index]))
            
            # Slider calculationss :
            COMPLETE_power_list.pop(0)
            COMPLETE_power_list.pop(0)
            #Remove the 2 power values
            
            slider_var = 0
            self.legal_slider = True
            if len(COMPLETE_power_list) == 1: #If there is only one slider value
                slider_var = str(COMPLETE_power_list[0][0])
            elif len(COMPLETE_power_list) == 0:
                self.GUI.console["state"] = "normal"
                self.GUI.console.insert(tk.INSERT, "\n\n"+"ERROR : Power slider unfindable ! (not even unknown !) do not set anything ! happens for P6 quadro cards")
                self.GUI.console["state"] = "disabled"
                self.legal_slider = False
            else:
                if COMPLETE_power_list[0][0] == COMPLETE_power_list[1][0]:
                    slider_var = str(COMPLETE_power_list[0][0])
                else :
                    slider_var = "Unknown"
                    self.GUI.console["state"] = "normal"
                    self.GUI.console.insert(tk.INSERT, "\n\n"+"ERROR : Power slider is unknown (2 values that are different inside power table aka quadro RTX AX000 cards)")
                    self.GUI.console["state"] = "disabled"
            
            self.GUI.OG_slider.set(slider_var)
            self.GUI.custom_slider.set(slider_var)
        
        else :
            self.GUI.console["state"] = "normal"
            self.GUI.console.insert(tk.INSERT, "\n\n"+"ERROR : File is not a (Pascal-Lovelace) vBIOS structure")
            self.GUI.console["state"] = "disabled" 
            
            self.legal_power = False
            self.legal_slider = False
            
            self.GUI.OG_slider.set("Unknown")
            self.GUI.custom_slider.set("Unknown")
            
            for index in range(2):
                OG_entry_list[index].config(state="normal")
                OG_entry_list[index].delete(0, "end")
                OG_entry_list[index].insert(0, 0)
                OG_entry_list[index].config(state="disabled")
                
                CUSTOM_entry_list[index].set(0)
        
    def set_architecture(self):
        self.GUI.architecture.set(self.vbios_parsed.get_card_architecture())
    
    def load_checksum_to_GUI(self):
        self.GUI.checksum_entry["state"] = "normal"
        self.GUI.checksum_entry.delete(0, "end")
        for checksum in self.checksum_data.get_OG_checksum():
            self.GUI.checksum_entry.insert(0, hex(checksum))
            self.GUI.checksum_entry.insert(0, " - ")
            
        self.GUI.checksum_entry["state"] = "disabled"  
    
    def save_vbios(self):
        """
        This big function call several sub functions to :
            - check if the modifications of the user are legal + he actually modified stuff
            - copy vbios then modify all the entries to the users entries
            - recalculate checksum for the bios images (can be several)
            - open save file dialog so that the user can save the vbios with corrected checksum somewhere
        """
        
        self.critical_save_vbios_error = False #No error at first
        
        #Critical error = clocks in incorrect order + no values to save (all illegal = not a vbios) + no changes made 
        
        temp_vbios = bytearray(self.vbios_data)
       
        #=====================================================================================================#
     
        # CORE CLOCK SAVING CHECKS
        multiplier = self.vbios_parsed.clock_multiplier
        
        if self.legal_core_clocks == False:
            self.GUI.console["state"] = "normal"
            self.GUI.console.insert(tk.INSERT, "\n\n"+"SAVE ERROR : Did not change any core clock values due to previous error")
            self.GUI.console["state"] = "disabled"    
        
        elif self.modified_clock_list()[1] == True:
            self.GUI.console["state"] = "normal"
            self.GUI.console.insert(tk.INSERT, "\n\n"+"SAVE ERROR : Did not change any core clock values because custom values are identical to the stock values")
            self.GUI.console["state"] = "disabled" 
        
        elif self.check_custom_clocks_correct_order() == False:
            self.GUI.console["state"] = "normal"
            self.GUI.console.insert(tk.INSERT, "\n\n"+"CRITICAL SAVE ERROR : Custom clock values not in correct order ! idle < base < boost =< max (boost and max can be equal) &  one or more values are too high")
            self.GUI.console["state"] = "disabled"
            
            self.critical_save_vbios_error = True #Will stop the bios saving completely
        
        else: # IF SAVING IS ALLOWED
            self.GUI.console["state"] = "normal"
            self.GUI.console.insert(tk.INSERT, "\n\n"+"SAVE INFORMATION: Custom Core clock values correctly saved to vbios")
            self.GUI.console["state"] = "disabled"
         
        
        #IMPORTANT :
            """
            Each clock entry is 4 bytes and it is in a 2 + 2 bytes fashion
            
            For turing and above :
                clock value = custom value / 2 ==> Simpler this way
                
                - the last 2 bytes are the clock_value / 2 (little endian)
                (- the first 2 bytes are the clock_value (little endian))
            
            For pascal :
                - the last 2 bytes are the clock_value / 2 (little endian)
                (- the first 2 bytes are the (clock_value *2 + 32768))
            
            IF the first 2 OG bytes -32768 > 0
                first 2 bytes must be clock value * 2 + 32768
            IF the first 2 OG bytes -16384 > 0
                first 2 bytes must be clock value * 2 + 16384
            ELSE
                first 2 bytes must be clock value * 2
            """
        
        
            for offset in self.vbios_parsed.find_v_p_table_offsets():
                offset_jump = 41
                da_clock_list = self.modified_clock_list()[0]
    
                
                for i in range(len(da_clock_list)):
                    #clock_value_corrected_multiplier = da_clock_list[i]/multiplier Not needed
                    clock_value_corrected_multiplier = da_clock_list[i]
                    
                    clock_value_last_2_bytes = clock_value_corrected_multiplier / 2
                    
                    read_bytes_2_first_bytes = struct.unpack("<H", temp_vbios[(offset + i*offset_jump) : (offset + 2 + i*offset_jump)])[0]
                    if read_bytes_2_first_bytes - 32768 > 0:
                        clock_value_first_2_bytes = clock_value_corrected_multiplier*2+32768
                    elif read_bytes_2_first_bytes - 16384 > 0:
                         clock_value_first_2_bytes = clock_value_corrected_multiplier*2+16384
                    else:
                        clock_value_first_2_bytes = clock_value_corrected_multiplier*2
                    
                    # Saving value on the last 2 bytes
                    temp_vbios[(offset + 2+ i*offset_jump) : (offset + 4 + i*offset_jump)] = struct.pack("<H", round(clock_value_last_2_bytes-0.2))   
                    
                    # Saving value on the first 2 bytes
                    temp_vbios[(offset + i*offset_jump) : (offset + 2 + i*offset_jump)] = struct.pack("<H", round(clock_value_first_2_bytes-0.2))
  
        #=====================================================================================================#
        
             
        # MEM CLOCK SAVING CHECKS    
 
        if self.legal_mem_clocks == False or int(self.GUI.custom_mem.get()) > 10000:
            self.GUI.console["state"] = "normal"
            self.GUI.console.insert(tk.INSERT, "\n\n"+"SAVE ERROR : Did not change any Memory clock values due to previous error or because value is too high")
            self.GUI.console["state"] = "disabled"    
        
        else:
            mem_clock = int(self.GUI.custom_mem.get())
            
            """
            3 different values of 2 bytes each :
                - first 2 bytes (present only in header) = mem_clock (little endian)
                - middle 2 bytes (present header + core_clocks) = MORE CALULATIONS NEEDED:
                    If READ_value - 32768 - 16384 > 0 : middle_value = CUSTOM_value + 32768 + 16384
                    If READ_value - 32768 > 0 : middle_value = CUSTOM_value + 32768
                    If READ_value - 16384 > 0 : middle_value = CUSTOM_value + 16384
                    
                - last 2 bytes (present header + core_clocks) = mem_clock / 4
            
            """
            
            self.GUI.console["state"] = "normal"
            self.GUI.console.insert(tk.INSERT, "\n\n"+"SAVE INFORMATION: Custom Memory clock value correctly saved to vbios")
            self.GUI.console["state"] = "disabled"
            #print(mem_clock)
            for img in self.vbios_parsed.MEM_clock_list :
                
                read_2_middle_bytes = struct.unpack("<H", temp_vbios[(img[1][1]) : (img[1][1] + 2)])[0]
                
                # MIDDLE BYTES CALCULATIONS
                
                if read_2_middle_bytes - 32768 - 16384 > 0:
                    clock_value_middle_2_bytes = mem_clock + 32768 + 16384
                elif read_2_middle_bytes - 32768 > 0:
                     clock_value_middle_2_bytes = mem_clock + 32768
                elif read_2_middle_bytes - 16384 > 0:
                    clock_value_middle_2_bytes = mem_clock + 16384
                else:
                    clock_value_middle_2_bytes = mem_clock #No clue if this is needed probably not
                    
                # Other bytes calulations
                
                clock_value_first_2_bytes = mem_clock
                clock_value_last_2_bytes = mem_clock/4
                
                temp_vbios[(img[0][1]) : (img[0][1] + 2)] = struct.pack("<H", round(clock_value_first_2_bytes))
                temp_vbios[(img[1][1]) : (img[1][1] + 2)] = struct.pack("<H", round(clock_value_middle_2_bytes))
                temp_vbios[(img[1][1]) + 2 : (img[1][1] + 4)] = struct.pack("<H", round(clock_value_last_2_bytes))
                
                temp_vbios[(img[2][1]) : (img[2][1] + 2)] = struct.pack("<H", round(clock_value_middle_2_bytes))
                temp_vbios[(img[2][1]) + 2 : (img[2][1] + 4)] = struct.pack("<H", round(clock_value_last_2_bytes))
        
        #=====================================================================================================#
        
        #POWER TABLE SAVING
        
        if self.legal_power == False or int(self.GUI.custom_target.get()) > 350 or int(self.GUI.custom_limit.get()) > 350 or int(self.GUI.custom_limit.get()) < int(self.GUI.custom_target.get()):
            self.GUI.console["state"] = "normal"
            self.GUI.console.insert(tk.INSERT, "\n\n"+"SAVE ERROR : Did not change any power values due to previous error or because value is too high, or because targe > limit")
            self.GUI.console["state"] = "disabled"
        
        else:
            limit_power = int(self.GUI.custom_limit.get())
            target_power = int(self.GUI.custom_target.get())
            slider_value = self.GUI.custom_slider.get()
            self.GUI.console["state"] = "normal"
            self.GUI.console.insert(tk.INSERT, "\n\n"+"SAVE INFORMATION: Custom Power values correctly saved to vbios")
            self.GUI.console["state"] = "disabled"
            #print(self.vbios_parsed.POWER_list)
            for img in self.vbios_parsed.POWER_list:
                temp_vbios[(img[0][1]) : (img[0][1] + 4)] = struct.pack("<I", target_power*1000)
                temp_vbios[(img[1][1]) : (img[1][1] + 4)] = struct.pack("<I", limit_power*1000)
                if slider_value == "False":
                    temp_vbios[(img[2][1]) : (img[2][1] + 5)] = struct.pack("BBBBB", 0x0F, 0xFF, 0xFF, 0xFF, 0x02)
                if slider_value == "True":
                    temp_vbios[(img[2][1]) : (img[2][1] + 5)] = struct.pack("BBBBB", 0x0F, 0x02, 0xFF, 0xFF, 0xFF)
                    
        #=====================================================================================================#     

        # FIX THE CHECKSUM

        temp_vbios = self.checksum_data.fix_checksum_of_vbios(temp_vbios)


        #=====================================================================================================# 
        
        # ACTUALLY SAVING VBIOS PART
        
        if not self.critical_save_vbios_error : #If vbios can be saved
            file_path = fd.asksaveasfilename(
                defaultextension=".bin",
                filetypes=[("Binary files", "*.bin"), ("All files", "*.*")],
                title="Save your modified vbios"
            )
        
            # 3. Check if the user selected a path or cancelled
            if file_path:
                try:
                    with open(file_path, 'wb') as f:
                        f.write(temp_vbios) #IMPORTNAT LINEEEEE
                        self.GUI.console["state"] = "normal"
                        self.GUI.console.insert(tk.INSERT, "\n\n"+f"SAVED vBIOS: Successfully saved vBIOS {file_path}")
                        self.GUI.console["state"] = "disabled"
                
                except Exception as e:
                    #print(f"Error saving file: {e}")
                    """
                    """
            else:
                #print("Save operation cancelled.") 
                """
                """
        
        self.GUI.console.see(tk.END)
    
    def modified_clock_list(self):
        """
        Function returns the modified clock list in the correct order and with values correctly placed
        """
        CUSTOM_short_list = []
        CUSTOM_entry_list = [self.GUI.custom_idle, self.GUI.custom_base, self.GUI.custom_boost, self.GUI.custom_max, self.GUI.custom_mem]
        OG_short_list = self.vbios_parsed.return_sorted_calculated_clock_list()
        for var in CUSTOM_entry_list:
            CUSTOM_short_list.append(int(var.get()))
        
        CUSTOM_short_list.pop() #Remove MEM clock
        OG_short_list.pop()#Remove MEM clock
        equal = False
        if OG_short_list == CUSTOM_short_list:
            equal = True
        final_list = []
        for clock in self.vbios_parsed.VP_core_clock_list:
            for i in range(len(OG_short_list)):
                if clock > OG_short_list[i]/self.vbios_parsed.clock_multiplier - 1 and OG_short_list[i]/self.vbios_parsed.clock_multiplier + 1 > clock:
                    final_list.append(CUSTOM_short_list[i]/self.vbios_parsed.clock_multiplier)
                    break
        return [final_list, equal]
        
    def check_custom_clocks_correct_order(self):
        """
        Function returns true if clocks are in correct order, false if not
        """   
        return_bool = True
        CUSTOM_entry_list = [self.GUI.custom_idle, self.GUI.custom_base, self.GUI.custom_boost, self.GUI.custom_max, self.GUI.custom_mem]
        for i in range(1, len(CUSTOM_entry_list)):
            if int(CUSTOM_entry_list[i-1].get()) > int(CUSTOM_entry_list[i].get()) or int(CUSTOM_entry_list[i-1].get()) > 3000:
                return_bool = False
                break
        return return_bool
            
            
            
            
            
            