import tkinter as tk
import os
from tkinter import filedialog as fd
from CPR_calculator import parsed_data
from CPR_Checksum import checksummer
from CPR_DCB import DCBParser
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
        
        #VARS
        self.custom_clock_list = []
        self.OG_clock_list =[]
        # Both lists are to be filled when saving the vbios
        
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

            # Parse once, but keep the GUI alive for newer unsupported formats.
            try:
                self.vbios_parsed = parsed_data(self.vbios_data)
            except Exception as exc:
                self.vbios_parsed = None
                self.GUI.console["state"] = "normal"
                self.GUI.console.insert(tk.INSERT, "\n\n"+"ERROR : Clock/power parser could not read this VBIOS: " + str(exc))
                self.GUI.console.insert(tk.INSERT, "\nDisplay/DCB and checksum will still be attempted.")
                self.GUI.console["state"] = "disabled"

            self.checksum_data = checksummer(self.vbios_data)

            if self.vbios_parsed is not None:
                self.load_clocks_to_GUI()
                self.load_power_to_GUI()
                self.set_architecture()
                self.load_header_to_GUI()
            else:
                self.GUI.architecture_var.set("Unknown")
                
            # ================= LOADING UI ELEMENTS ================= #
            #self.load_checksum_to_GUI()
            self.load_display_to_GUI()
            self.load_VP_Profiles_to_GUI()
            self.load_VP_Footers_to_GUI()
            
            self.GUI.save_button["state"] = "normal"
            
            self.GUI.console.see(tk.END)
        
    def load_clocks_to_GUI(self):
        
        # Loads to stock clocks into the entries of the clock tab of the GUI
        clock_dictionnary = self.vbios_parsed.clock_dictionnary 
        #print("==VOID==")
        #print(clock_dictionnary)
        
        """ 
        # OLD... Changed in V1.4
        # CHECK IF DIFFERENT MEM VALUES = IMPORTANT TO NOTIFY THE USER
        self.legal_mem_clocks = True
        mem_list = self.vbios_parsed.MEM_clock_list
        #print(mem_list)
        if mem_list == [] : #NOT VBIOS
        self.legal_mem_clocks = False
        
        """
        
        clock_dictionnary_ids = ["idle", "base", "boost", "max"]
            
        OG_entry_list = [self.GUI.OG_idle, self.GUI.OG_base, self.GUI.OG_boost, self.GUI.OG_max]
        CUSTOM_entry_list = [self.GUI.CUSTOM_idle_clock_entry, self.GUI.CUSTOM_base_clock_entry, self.GUI.CUSTOM_boost_clock_entry, self.GUI.CUSTOM_max_clock_entry]
        CUSTOM_stringvar = [self.GUI.custom_idle, self.GUI.custom_base, self.GUI.custom_boost,self.GUI.custom_max]
        
        for index in range(4): #Fixed size of 4 since everything get's filled up...
            clock_value = clock_dictionnary[clock_dictionnary_ids[index]]
            CUSTOM_entry_list[index].config(state="normal")
            if clock_value == 0:
                clock_value = "No Value"
                CUSTOM_entry_list[index].config(state="disabled")
            OG_entry_list[index].config(state="normal")
            OG_entry_list[index].delete(0, "end")
            OG_entry_list[index].insert(0, clock_value)
            OG_entry_list[index].config(state="disabled")
            
            # 2. Update Custom Spinboxes via their TextVariables
            # This is the ONLY way to update a StringVar/IntVar   
            
            CUSTOM_stringvar[index].set(clock_value)
        
        mem_value = self.vbios_parsed.MEM_clock_list[0][0]
        
        #MEM CLOCKS
        self.GUI.OG_mem.config(state="normal")
        self.GUI.OG_mem.delete(0, "end")
        self.GUI.OG_mem.insert(0, mem_value)
        self.GUI.OG_mem.config(state="disabled")
        
        self.GUI.custom_mem.set(mem_value)
        
        self.legal_core_clocks = True
        self.legal_mem_clocks = True
        
        """
        #VERY IMPORTANT -> Discarded in v1.4
        self.legal_core_clocks = True
        if clock_list[0] == -1:
            self.GUI.console["state"] = "normal"
            self.GUI.console.insert(tk.INSERT, "\n\n"+"ERROR : Clock table is not in the expected format, values will be all -1 and uneditable")
            self.GUI.console["state"] = "disabled"                
            self.legal_core_clocks = False
        """
        
    def load_power_to_GUI(self):
        COMPLETE_power_list = self.vbios_parsed.POWER_list[0]
        
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
            #COMPLETE_power_list.pop(0)
            #COMPLETE_power_list.pop(0)
            #Remove the 2 power values
            
            slider_var = 0
            self.legal_slider = True
            if len(COMPLETE_power_list) == 3: #If there is only one slider value
                slider_var = str(COMPLETE_power_list[2][0])
            elif len(COMPLETE_power_list) == 2:
                self.GUI.console["state"] = "normal"
                self.GUI.console.insert(tk.INSERT, "\n\n"+"ERROR : Power slider unfindable ! (not even unknown !) do not set anything ! happens for P6 quadro cards")
                self.GUI.console["state"] = "disabled"
                self.legal_slider = False
            else:
                if COMPLETE_power_list[2][0] == COMPLETE_power_list[3][0]:
                    slider_var = str(COMPLETE_power_list[2][0])
                else :
                    slider_var = "Unknown"
                    self.GUI.console["state"] = "normal"
                    self.GUI.console.insert(tk.INSERT, "\n\n"+"ERROR : Power slider is unknown (2 values that are different inside power table aka quadro RTX AX000 cards)")
                    self.GUI.console["state"] = "disabled"
            
            self.GUI.OG_slider.set(slider_var)
            self.GUI.custom_slider.set(slider_var)
        
        else :
            self.GUI.console["state"] = "normal"
            self.GUI.console.insert(tk.INSERT, "\n\n"+"ERROR : Clock/power tables are not in the expected Pascal-Ada format")
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
        """
        Function modified in V1.4
        -> Now it sets the architecture precisely based on the clock table as well as the power table (mobile/desktop)
        """
        self.GUI.architecture_var.set(self.vbios_parsed.VP_generation)
        self.GUI.plateform_var.set(self.vbios_parsed.PT_plateform)
    
        
    """
    
    # REMOVED FOR NOW
    
    def load_checksum_to_GUI(self):
        self.GUI.checksum_entry["state"] = "normal"
        self.GUI.checksum_entry.delete(0, "end")
        for checksum in self.checksum_data.get_OG_checksum():
            self.GUI.checksum_entry.insert(0, hex(checksum))
            self.GUI.checksum_entry.insert(0, " - ")
            
        self.GUI.checksum_entry["state"] = "disabled"  
    """
    
    def load_header_to_GUI(self):
        header_list = self.vbios_parsed.header_list
        
        if header_list == None:
            self.GUI.header.set("None")
            self.GUI.header_radio_remove.config(state="disabled")
            self.GUI.header_radio_keep.config(state="disabled")
        else:
            self.GUI.header.set("Remove")
            self.GUI.header_radio_remove.config(state="normal")
            self.GUI.header_radio_keep.config(state="normal")
    
    def load_display_to_GUI(self):
        """Load Pascal-Ada/Blackwell DCB display configuration into the Display / DCB tab."""
        try:
            summary = DCBParser(self.vbios_data).summarize(include_duplicates=False)
        except Exception as exc:
            summary = "Display/DCB parser error: " + str(exc)
        self.GUI.display_config_text["state"] = "normal"
        self.GUI.display_config_text.delete("1.0", tk.END)
        self.GUI.display_config_text.insert(tk.INSERT, summary)
        self.GUI.display_config_text["state"] = "disabled"
        
    def load_VP_Profiles_to_GUI(self):
        """Load VP table profiles & headers !!"""
        if self.vbios_parsed.VP_profile_list != []: #If there is no error
            self.GUI.VP_text["state"] = "normal"
            self.GUI.VP_text.delete("1.0", tk.END)
            self.GUI.VP_text.insert(tk.INSERT, f"\n\n======== PROFILES ========\n\n")
            self.GUI.VP_text.insert(tk.INSERT, f"Total number of profiles : {len(self.vbios_parsed.VP_profile_list[0])}\n")
            self.GUI.VP_text.insert(tk.INSERT, f"Number of non empty profiles : {self.vbios_parsed.number_of_non_empty_VP_profiles}\n\nIndividual Profiles (values in Mhz) :\n")
            self.GUI.VP_text.insert(tk.INSERT, "ID     Limit 1      Limit 2      Limit 3      Mem clock    Mem clock DDR\n")
            self.GUI.VP_text.insert(tk.INSERT, "-----  -----------  -----------  -----------  -----------  -------------\n")
            
            for profile in self.vbios_parsed.VP_profile_list[0]: #Only for the first sub-list as they are the same for the second sub-list
                string = self.vbios_parsed.printout_VP_profile_info(profile)
                self.GUI.VP_text.insert(tk.INSERT, string)
                self.GUI.VP_text.insert(tk.INSERT, "\n")
                
            self.GUI.VP_text["state"] = "disabled"
    
    def load_VP_Footers_to_GUI(self):
        """Load VP table footers"""
        if self.vbios_parsed.VP_footer_list != []: #If there is no error
            self.GUI.VP_text["state"] = "normal"
            #self.GUI.VP_text.delete("1.0", tk.END)
            
            self.GUI.VP_text.insert(tk.INSERT, f"\n\n======== FOOTERS ========\n\n")
            
            self.GUI.VP_text.insert(tk.INSERT, f"Total number of footers : {len(self.vbios_parsed.VP_footer_list[0])}\n")
            self.GUI.VP_text.insert(tk.INSERT, f"Number of non empty footers : {self.vbios_parsed.number_of_non_empty_VP_footers}\n\nIndividual Footers (values in Mhz) :\n")
            self.GUI.VP_text.insert(tk.INSERT, "ID     Mem clock    Mem clock DDR\n")
            self.GUI.VP_text.insert(tk.INSERT, "-----  -----------  --------------\n")
            
            for footer in self.vbios_parsed.VP_footer_list[0]: #Only for the first sub-list as they are the same for the second sub-list
                string = self.vbios_parsed.printout_VP_footer_info(footer)
                self.GUI.VP_text.insert(tk.INSERT, string)
                self.GUI.VP_text.insert(tk.INSERT, "\n")
                
            self.GUI.VP_text["state"] = "disabled"
                
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
        
        # REWORKED FOR V1.2.4 !!
        multiplier = self.vbios_parsed.clock_multiplier*2
        
        modified_clock_dictionnary = self.get_modified_clock_dictionnary()
        #Also fills out self.custom_clock_list & self.OG_clock_list
        index_of_OF_vp = 0
        
        #Important to leave this 0F index here !
        i = 0   
        
        while i<10:
            if self.vbios_parsed.VP_profile_list[0][i]["ID"] == "0xf":
                break
            i += 1
        
        index_of_OF_vp = i
        
        equal = False

        if self.OG_clock_list == self.custom_clock_list:
            equal = True
        
        if self.legal_core_clocks == False:
            self.GUI.console["state"] = "normal"
            self.GUI.console.insert(tk.INSERT, "\n\n"+"SAVE ERROR : Did not change any core clock values due to previous error")
            self.GUI.console["state"] = "disabled"    
        
        elif equal == True:
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
            
                       # CORE CLOCK SAVING
        
            #print(modified_clock_dictionnary)
        
            for offset in self.vbios_parsed.find_v_p_table_offsets():
                offset_jump = 41
                
                i = 0
                for clock in self.vbios_parsed.clock_map :
                    if clock != "skip":
                        
                        read_bytes_2_first_bytes = struct.unpack("<H", temp_vbios[(offset + i*offset_jump) : (offset + 2 + i*offset_jump)])[0]
                        
                        correction_2_first_bytes = self.vbios_parsed.calculate_correct_clock_data(read_bytes_2_first_bytes)
                        
                        corrected_first_2_bytes = modified_clock_dictionnary[clock]*4/multiplier + correction_2_first_bytes
                        
                        # Saving value on the last 2 bytes
                        temp_vbios[(offset + 2+ i*offset_jump) : (offset + 4 + i*offset_jump)] = struct.pack("<H", round(modified_clock_dictionnary[clock]/multiplier-0.4))   
                        
                        # Saving value on the first 2 bytes
                        temp_vbios[(offset + i*offset_jump) : (offset + 2 + i*offset_jump)] = struct.pack("<H", round(corrected_first_2_bytes-0.4))
                    i += 1
        # ================================= #      
  
        # "0F" VP profile saving clocks, NEW TO V1.2.4 !!
        # The first limit clock must be set above the max clock, that's it, nothing too hard
        # The second limit clock = first limit clock - 50 Mhz
        # The third limit clock = first limit clock - 100 Mhz
  
        # This is completely arbitrary, since the second and third limit don't seem to do anything anyway...
        
        # Look for the "0xF" ID of the VP:
        
            dict_list = ["first_limit_clock", "second_limit_clock", "third_limit_clock"]
            print(self.vbios_parsed.VP_profile_list)
            for VP_table in self.vbios_parsed.VP_profile_list:
                
                for j in range(3):
                    offset = VP_table[index_of_OF_vp][dict_list[j]][1]
                    temp_vbios[offset:offset+2] = struct.pack("<H", round((int(self.GUI.custom_max.get())-j*50)/multiplier))
               
            
        #=====================================================================================================#
        
             
        # MEM CLOCK SAVING CHECKS    
 
        if self.legal_mem_clocks == False or int(self.GUI.custom_mem.get()) > 10000 or int(self.GUI.custom_mem.get()) < 100 :
            self.GUI.console["state"] = "normal"
            self.GUI.console.insert(tk.INSERT, "\n\n"+"SAVE ERROR : Did not change any Memory clock values due to value being out of range (100-10000Mhz)")
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
            
            #print(self.vbios_parsed.MEM_clock_list)
            
            # COMPLETE REWRITE OF THIS SECTION IN v1.24 !!
            
            print()
            print("mem list")
            print(self.vbios_parsed.MEM_clock_list)
            for i in range(len(self.vbios_parsed.MEM_clock_list)) :
                
                value = self.vbios_parsed.MEM_clock_list[i]
                #===========
                # FIRST EDIT = CHANGE THE MEM CLOCK FOUND IN THE CORE CLOCK VALUES
                #===========
                
                # The program expects there two be :
                # - 2 first bytes (hard to read) -> applies algorithm
                # - 2 last bytes (easy to read)
                
                # 
                
                # FIRST BYTES CALCULATIONS
                
                #print(mem_clock)                
                clock_value_first_2_bytes = struct.unpack("<H", temp_vbios[value[1]:value[1]+2])[0]
                clock_value_first_2_bytes = mem_clock + self.vbios_parsed.calculate_correct_clock_data(clock_value_first_2_bytes)
                

                # Last 2 bytes is easy...
                clock_value_last_2_bytes = mem_clock/(4)
                
                # Write the clocks at the correct adress
                temp_vbios[(value[1]) : (value[1] + 2)] = struct.pack("<H", round(clock_value_first_2_bytes))
                temp_vbios[(value[1] + 2) : (value[1] + 4)] = struct.pack("<H", round(clock_value_last_2_bytes-0.5))
                
                
                #===========
                # SECOND EDIT = CHANGE THE MEM CLOCK FOUND IN THE 0F VP PROFILE
                #===========        
                
                # This clock is in 3*2 bytes:
                # - first 2 : full clock value little endian (same as the one found in GUI, DDR format)
                # - middle 2 : coded clock value little endian
                # - last 2 : half clock value little endian
                
                
                selected_VP_profile = self.vbios_parsed.VP_profile_list[i][index_of_OF_vp]
                
                mem_data = selected_VP_profile["mem_clock_short"]
                
                clock_value_middle_2_bytes = struct.unpack("<H", temp_vbios[mem_data[1]+2:mem_data[1]+4])[0]
                
                #mem_data[1] == the adress of the FIRST clock value (out of 3)
                
                clock_value_first_2_bytes = mem_clock
                clock_value_middle_2_bytes = mem_clock + self.vbios_parsed.calculate_correct_clock_data(clock_value_middle_2_bytes)
                clock_value_last_2_bytes = mem_clock/(4)
                
                #print((clock_value_first_2_bytes,clock_value_middle_2_bytes,clock_value_last_2_bytes)) 

                temp_vbios[(mem_data[1]) : (mem_data[1]+2)] = struct.pack("<H", clock_value_first_2_bytes)
                temp_vbios[(mem_data[1]+2) : (mem_data[1]+4)] = struct.pack("<H", clock_value_middle_2_bytes)
                temp_vbios[(mem_data[1]+4) : (mem_data[1]+6)] = struct.pack("<H", round(clock_value_last_2_bytes-0.5)) #-0.5 is very important !!
                
                #===========
                # THIRD EDIT = CHANGE THE MEM CLOCK FOUND IN THE 0F VP FOOTER
                #===========        
                
                # The program expects there two be :
                # - 2 first bytes (hard to read) -> applies algorithm
                # - 2 last bytes (easy to read)
                
                # 
                
                # FIRST BYTES CALCULATIONS
                
                clock_value_first_2_bytes = struct.unpack("<H", temp_vbios[value[1]:value[1]+2])[0]
                clock_value_first_2_bytes = mem_clock + self.vbios_parsed.calculate_correct_clock_data(clock_value_first_2_bytes)
                

                # Last 2 bytes is easy...
                clock_value_last_2_bytes = mem_clock/(4)
                
                for footer in self.vbios_parsed.VP_footer_list[i]:
                    if footer[0] == 15: #Only applies to the 0F profile aka profile 15
                        temp_vbios[(footer[2]) : (footer[2] + 2)] = struct.pack("<H", round(clock_value_first_2_bytes))
                        temp_vbios[(footer[2] + 2) : (footer[2] + 4)] = struct.pack("<H", round(clock_value_last_2_bytes-0.5))
                
        #=====================================================================================================#
        
        #POWER TABLE SAVING
        
        if self.legal_power == False or int(self.GUI.custom_target.get()) > 850 or int(self.GUI.custom_limit.get()) > 850 or int(self.GUI.custom_limit.get()) < int(self.GUI.custom_target.get()):
            self.GUI.console["state"] = "normal"
            self.GUI.console.insert(tk.INSERT, "\n\n"+"SAVE ERROR : Did not change any power values due to previous error or because value is too high, or because target > limit")
            self.GUI.console["state"] = "disabled"
        
        else:
            limit_power = int(self.GUI.custom_limit.get())
            target_power = int(self.GUI.custom_target.get())
            slider_value = self.GUI.custom_slider.get()
            self.GUI.console["state"] = "normal"
            self.GUI.console.insert(tk.INSERT, "\n\n"+"SAVE INFORMATION: Custom Power values correctly saved to vbios")
            self.GUI.console["state"] = "disabled"
            print()
            print()
            print(self.vbios_parsed.POWER_list)
            for img in self.vbios_parsed.POWER_list:
                temp_vbios[(img[0][1]) : (img[0][1] + 4)] = struct.pack("<I", target_power*1000)
                temp_vbios[(img[1][1]) : (img[1][1] + 4)] = struct.pack("<I", limit_power*1000)
                if slider_value == "False":
                    temp_vbios[(img[2][1]) : (img[2][1] + 5)] = struct.pack("BBBBB", 0x0F, 0xFF, 0xFF, 0xFF, 0x02)
                if slider_value == "True":
                    temp_vbios[(img[2][1]) : (img[2][1] + 5)] = struct.pack("BBBBB", 0x0F, 0x02, 0xFF, 0xFF, 0xFF)
                    
        #=====================================================================================================#     

        # FIX THE CHECKSUM

        temp_vbios = self.checksum_data.fix_checksum_of_vbios(temp_vbios, self.vbios_parsed.VP_offset_list)
        
        # Fixes first the VP section image (new feature)
        # Then fixes the checksum of the entire vbios


        #=====================================================================================================# 
        
        # REMOVING THE HEADER IF NEED BE
        
        #Important, you must go backwards !!
        if self.GUI.header.get() == "Remove":
            for i in range(1, len(self.vbios_parsed.header_list)+1) :
                adress = self.vbios_parsed.header_list[-i]
                temp_vbios = temp_vbios[:adress[0]] + temp_vbios[adress[1]:]

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
        self.GUI.console["state"] = "normal"
        self.GUI.console.insert(tk.INSERT, "\n\n"+f"============= SAVE ATTEMPT =============")
        self.GUI.console["state"] = "disabled"
        
        self.GUI.console.see(tk.END)
    
    def get_modified_clock_dictionnary(self):
        """
        Function returns the modified clock dictionnary
        """
        CUSTOM_entry_list = [self.GUI.custom_idle, self.GUI.custom_base, self.GUI.custom_boost, self.GUI.custom_max]
        custom_clocks = []
        
        OG_entry_list = [self.GUI.OG_idle, self.GUI.OG_base, self.GUI.OG_boost, self.GUI.OG_max]
        OG_clock_list = []

        for i in range(4):
            clock_custom = CUSTOM_entry_list[i].get()
            clock_og = OG_entry_list[i].get()
            
            if clock_og == "No Value":
                clock_og= -1 #To pass the checks !!! The value isn't saved anywhere due to the clock map list
            else :
                clock_og = int(clock_og)
                
            if clock_custom == "No Value":
                clock_custom= -1 #To pass the checks !!! The value isn't saved anywhere due to the clock map list
            else :
                clock_custom = int(clock_custom)
                
            custom_clocks.append(clock_custom)
            OG_clock_list.append(clock_og)
        
        #Dictionary
        custom_clocks_dictionnary = {
            "idle" : custom_clocks[0],
            "base" : custom_clocks[1],
            "boost" : custom_clocks[2],
            "max" : custom_clocks[3]
            } 
        
        self.custom_clock_list = custom_clocks
        self.OG_clock_list = OG_clock_list
        
        #print(self.custom_clock_list)
        #print(self.OG_clock_list)
        
        return custom_clocks_dictionnary
        
    def check_custom_clocks_correct_order(self):
        """
        Function returns true if clocks are in correct order, false if not
        """   
        return_bool = True
        custom_clock_list = self.custom_clock_list
            
        for i in range(1, len(custom_clock_list)):
            if (custom_clock_list[i-1] > custom_clock_list[i] or custom_clock_list[i-1] > 3000 or custom_clock_list[i-1] < 100) and custom_clock_list[i-1] != -1:
                return_bool = False
                break
        return return_bool
            
            
            
            
            
            