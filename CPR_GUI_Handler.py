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
                self.GUI.architecture.set("Unknown")
            #self.load_checksum_to_GUI()
            self.load_display_to_GUI()
            
            self.GUI.save_button["state"] = "normal"
            
            self.GUI.console.see(tk.END)
        
    def load_clocks_to_GUI(self):
        
        # Loads to stock clocks into the entries of the clock tab of the GUI
        clock_list = self.vbios_parsed.return_sorted_calculated_clock_list()  
        
        
        # CHECK IF DIFFERENT MEM VALUES = IMPORTANT TO NOTIFY THE USER
        self.legal_mem_clocks = True
        mem_list = self.vbios_parsed.MEM_clock_list
        #print(mem_list)
        if mem_list == [] : #NOT VBIOS
            self.legal_mem_clocks = False
            
            
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
        self.GUI.architecture.set(self.vbios_parsed.get_card_architecture())
    
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
        
        index_of_OF_vp = 0
        
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
  
        
        # "0F" VP profile saving clocks, NEW TO V1.2.4 !!
        # The first limit clock must be set above the max clock, that's it, nothing too hard
        # The second limit clock = first limit clock - 50 Mhz
        # The third limit clock = first limit clock - 100 Mhz
  
        # This is completely arbitrary, since the second and third limit don't seem to do anything anyway...
        
        # Look for the "0xF" ID of the VP:
        
            dict_list = ["first_limit_clock", "second_limit_clock", "third_limit_clock"]
            
            
            
            for VP_table in self.vbios_parsed.VP_profile_list:
                i = 0   
                
                while i<10:
                    if VP_table[i]["ID"] == "0xf":
                        break
                    i += 1
                
                index_of_OF_vp = i
                
                for j in range(3):
                    offset = VP_table[i][dict_list[j]][1]
                    temp_vbios[offset:offset+2] = struct.pack("<H", round((int(self.GUI.custom_max.get())-j*50)/multiplier))
               
            
        #=====================================================================================================#
        
             
        # MEM CLOCK SAVING CHECKS    
 
        if self.legal_mem_clocks == False or int(self.GUI.custom_mem.get()) > 10000 or int(self.GUI.custom_mem.get()) == -1:
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
            
            #print(self.vbios_parsed.MEM_clock_list)
            
            # COMPLETE REWRITE OF THIS SECTION IN v1.24 !!
            
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
                
                clock_value_first_2_bytes = self.vbios_parsed.calculate_correct_mem_data(mem_clock, temp_vbios, value[1])
                

                # Last 2 bytes is easy...
                clock_value_last_2_bytes = mem_clock/(4)
                
                # Write the clocks at the correct adress
                temp_vbios[(value[1]) : (value[1] + 2)] = struct.pack("<H", round(clock_value_first_2_bytes))
                temp_vbios[(value[1] + 2) : (value[1] + 4)] = struct.pack("<H", round(clock_value_last_2_bytes))
                
                
                #===========
                # SECOND EDIT = CHANGE THE MEM CLOCK FOUND IN THE 0F VP PROFILE
                #===========        
                
                # This clock is in 3*2 bytes:
                # - first 2 : full clock value little endian (same as the one found in GUI, DDR format)
                # - middle 2 : coded clock value little endian
                # - last 2 : half clock value little endian
                
                
                selected_VP_profile = self.vbios_parsed.VP_profile_list[i][index_of_OF_vp]
                
                mem_data = selected_VP_profile["mem_clock_long"]
                
                clock_value_first_2_bytes = mem_clock
                clock_value_middle_2_bytes = self.vbios_parsed.calculate_correct_mem_data(mem_clock, temp_vbios, mem_data[1])
                clock_value_last_2_bytes = mem_clock/(4)
                                        
                temp_vbios[(mem_data[1]-2) : (mem_data[1])] = struct.pack("<H", round(clock_value_first_2_bytes))
                temp_vbios[(mem_data[1]) : (mem_data[1]+2)] = struct.pack("<H", round(clock_value_middle_2_bytes))
                temp_vbios[(mem_data[1]+2) : (mem_data[1]+4)] = struct.pack("<H", round(clock_value_last_2_bytes))
                
                #===========
                # THIRD EDIT = CHANGE THE MEM CLOCK FOUND IN THE 0F VP FOOTER
                #===========        
                
                # The program expects there two be :
                # - 2 first bytes (hard to read) -> applies algorithm
                # - 2 last bytes (easy to read)
                
                # 
                
                # FIRST BYTES CALCULATIONS
                
                clock_value_first_2_bytes = self.vbios_parsed.calculate_correct_mem_data(mem_clock, temp_vbios, value[1])
                

                # Last 2 bytes is easy...
                clock_value_last_2_bytes = mem_clock/(4)
                
                for footer in self.vbios_parsed.VP_footer_list[i]:
                    if footer[0] == 15: #Only applies to the 0F profile aka profile 15
                        temp_vbios[(footer[2]) : (footer[2] + 2)] = struct.pack("<H", round(clock_value_first_2_bytes))
                        temp_vbios[(footer[2] + 2) : (footer[2] + 4)] = struct.pack("<H", round(clock_value_last_2_bytes))
                
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
            
            
            
            
            
            