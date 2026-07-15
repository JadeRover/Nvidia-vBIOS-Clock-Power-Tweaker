import struct
  
class parsed_data():
    def __init__(self, data):
        #VARS
        #==========================
        self.data = data
        self.VP_generation = 0 #Default of 0, this variable gets modified by find_v_p_table_offsets() to become a string of the generation name

        self.VP_header_length = 0 #Used to store the length of the VP header + 1 (to get to the beginning of the VP table)
        self.VP_profile_list = [] # 2D List !! Contains the lists of each VP table (= CAN BE 2 !!) -> containing individual dictionaries relating to each VP profile
        self.VP_footer_list = [] # 2D List !! Contains the lists of each VP footer (= CAN BE 2 !!) -> containing individual dictionaries relating to each VP profile
        
        self.clock_multiplier = 1
        self.header_list = []
        
        # DEFINITION OF THE OFFSETS INSIDE THE VP PROFILE !
        # Values in this order :
        #
        # first_limit_clock -> second_limit_clock -> mem_clock_short -> mem_clock_long -> third_limit_clock
        
        # Define the pascal offsets
        self.pascal_offset_list = [7, 13, 15, 17, 25]
        
        # Define the offsets for all non pascal cards
        self.non_pascal_offset_list = [9, 15, 17, 19, 39]
        
        # Define the length of the values (same for pascal or non pascal)
        self.offset_length = [2, 2, 2, 4, 2]
        
        
        #FUNCTIONS / FILLING VARs
        #==========================
        self.VP_offset_list = self.find_v_p_table_offsets()
        self.get_card_architecture()
        self.get_VP_profiles_list()
        self.get_VP_footers_list()
        
        core_tables = self.get_CORE_clock_list()
        
        self.VP_core_clock_list = core_tables[0] if core_tables else []  # simple list; empty for unsupported/new formats



        self.MEM_clock_list = self.get_MEM_clock_list()
        self.POWER_list = self.get_power_table_list()

        self.get_header_info()
        print(self.header_list)
    
    def find_v_p_table_offsets(self): 
        """
        
        MODIFIED TO RETURN SEVERAL OFFSETS + more reliable way to find VP table added
        
        && Will give the generation of the card based on the VP state header length (in hex) according to this table
        
        Pascal = either 10 or 12
        Turing = 13
        Ampere = 15
        Ada lovelace = 17
        Blackwell = Nan (no VP table)
        ===
        
        This functions looks for hex string "20 XX 01" where XX is a variable between 10 and 17 (see above) defining the VP table length
        This string is the header for the the virtual p state table (VP table) 
        """

        data = self.data
        
        offset2send = [] # Keep empty list of no entries found
    
        generation_dictionnary = {
            16 : "Pascal",
            18 : "Pascal",
            19 : "Turing",
            21 : "Ampere",
            23 : "Ada Lovelace"
            }    
    
        for i in range(16,24) :
            search_string = struct.pack("BBB", 0x20, i, 0x01)
            
            for entry in self.check_return_offset(data, 0, search_string):
                
                # 1st check - For confirming the VP table is to see if the clock value (found just after the header) is coherent
                header_length = i +1 #The +1 is to not count the "0F" (or other denominator byte) indicating first VP entry
                chunk = data[(entry + header_length) : (entry + header_length + 4)]
                first_clock = struct.unpack("<I", chunk)[0] 
                
                realfirstclock = first_clock/32768
                
                #================================================#
                
                # 2nd check - The denominator byte of 0x0F = 15 decimal for the first clock being located directly after the VP table should always be present
                chunk2 = data[entry+i : entry+i+1]
                F_value = struct.unpack("<B", chunk2)[0] 
                
                if realfirstclock > 100 and realfirstclock < 2000 and F_value == 15:
                    offset2send.append(entry + header_length) #Shouldn't be more than 2 VP tables inside vbios (from testing)
                    self.VP_header_length = header_length
                    self.VP_generation = generation_dictionnary[i] #Can be executed twice but value is the same
        return offset2send
    
    def get_VP_profiles_list(self):
        """
        Function that counts what VP profiles are present + their respective offset + their ID
        
        Returns a list of all this data in the form of a dictionary that has the VP profile ID as the ID
        
        This fonction ASSUMES that the first VP profile is of index 0x07 !! Might not be the case for ALL vbios !!
        Just in case the fonction stops at 10 repetitions...
        """        
        #Define the length of a VP profile based on known lengths
        profile_length = 65
        
        data = self.data
        if self.VP_generation == "Pascal":
            profile_length = 57
            
        #Count and define the VP profiles -> place into dictionary    
        for VP_offset in self.VP_offset_list: #can be 2 VP tables
        
            sub_list_of_profiles = []
            
            start_offset = VP_offset - self.VP_header_length
            end = False
            i = 1
            
            while not end:
                offset = start_offset-i*profile_length
                
                ID = struct.unpack("<B", data[offset:offset+1])[0]
                
                if ID == 7 or i == 10:
                    end = True
                
                sub_list_of_profiles.append(self.get_VP_profiles_details(offset))    
                
                i += 1
            
            self.VP_profile_list.append(sub_list_of_profiles)
        
        #print(self.VP_profile_list)
    
    def get_VP_footers_list(self):
        """
        This functions looks for the footers and parses them into a 2D list containing (one list for each vbios image):
            - footer ID
            - footer associated memory clock
            - footer memory clock offset !!WATCH OUT MEMORY offset !! and not ID
        """
        
        profile_length = 41
        
        data = self.data
            
        #Count and define the VP profiles -> place into dictionary    
        for VP_offset in self.VP_offset_list: #can be 2 VP tables
        
            sub_list_of_footers = []
            
            
            #look for the "00 00 10 0E" string that is at the end of the footers to define as the start offset
            start_offset = VP_offset + self.data[VP_offset:].find(struct.pack(">I", 0x0000100E))+2
            
            end = False
            i = 1
            
            while not end:
                offset = start_offset-i*profile_length
                
                ID = struct.unpack("<B", data[offset:offset+1])[0]
                
                if ID == 7 or i == 20:
                    end = True
                
                #Memory clock is always 9 bytes after the ID !!
                mem_clock = struct.unpack("<I", data[offset+9:offset+13])[0]/32768
                sub_list_of_footers.append((ID, mem_clock, offset+9))    
                
                i += 1
            
            self.VP_footer_list.append(sub_list_of_footers)
        
        #print(self.VP_footer_list)
        
    def get_VP_profiles_details(self, adress):
        """
        Is called by the above fonction to create a dictionary containing the info of each VP profile to place into the VP list
        
        Needs the offset of the VP profiles to do it's work
        """
        
        data = self.data
        
        dictionary_2_send = {
            "ID" : 0,
            "first_limit_clock" : 0,
            "second_limit_clock" : 0,
            "mem_clock_short" :0,
            "mem_clock_long" : 0,
            "third_limit_clock" :0            
            }
        
        # First element, never changes
        ID = struct.unpack("<B", data[adress:adress+1])[0]
        dictionary_2_send["ID"] = hex(ID)
        
        #Multiplier to apply to the clock values:
        multiplier = self.clock_multiplier*2
        
        #All the different data :::::
        list_of_offsets_2_use = self.non_pascal_offset_list
        if self.VP_generation == "Pascal":
            list_of_offsets_2_use = self.pascal_offset_list
        
        for i in range(5):
            offset_from_adress = list_of_offsets_2_use[i] + adress
            length_of_value = self.offset_length[i]
            value_ID = list(dictionary_2_send.keys())[i+1]
            
            # Dumb way of making the 'unpack' function work...
            unpack_string = "<H"
            if length_of_value == 4:
                unpack_string = "<I"

            dictionary_2_send[value_ID] = [struct.unpack(unpack_string, self.data[offset_from_adress:offset_from_adress+length_of_value])[0]*multiplier,offset_from_adress]
        
        #CORRECTIONS AFTER THE FACT FOR THE MEM CLOCKS !
        dictionary_2_send["mem_clock_short"][0] = dictionary_2_send["mem_clock_short"][0]/multiplier
        dictionary_2_send["mem_clock_long"][0] = dictionary_2_send["mem_clock_long"][0]/multiplier/32768 #TO lazy to actually calculate it correctly with the -32768 -> -16384... good enough
            
        return dictionary_2_send
    
    def get_CORE_clock_list(self):
        """
        Returns a 2D list containing the clock values, max 2 sub lists inside this big list (based on searching diff card vbios)
        IF you have 2 sub lists, they should be identical
        """
        data = self.data
        
        VP_table_offset_list = self.VP_offset_list
        clock_table_2D = [] #a list containing the lists of the clock tables -> clock_table_2D[Clock_entry][0] for table 1
        offset_jump = 41 #number of bytes of data between clock entries
        
        for offset in VP_table_offset_list :
            clock_table = []
            i = 0
            while True:
                """
                # OLD METHOD !! now use the 2 dirst bytes to get a super accurate clock...
                
                chunk = data[(offset + i*offset_jump) : (offset + 4 + i*offset_jump)]
                clock_entry = struct.unpack("<I", chunk)[0] 
                
                clock_value = clock_entry/32768
                
                if clock_value > 100 and clock_value < 3000:
                    clock_table.append(clock_value)
                else :
                    break
                i+= 1
                """
                
                #New method, using the 2 last bytes of the entry to get a precise value
                
                chunk = data[(offset + i*offset_jump) : (offset + 2 + i*offset_jump)]
                clock_entry = self.calculate_correct_clock_data(struct.unpack("<H", chunk)[0]) 
                
                clock_value = clock_entry/2*self.clock_multiplier #NEW CHANGE !
                
                if clock_value > 100 and clock_value < 3500:
                    clock_table.append(clock_value)
                else :
                    break
                i+= 1
                
            clock_table_2D.append(clock_table)
            
        return clock_table_2D
    
    def get_MEM_clock_list(self):
        """
        This "legacy" fonction gets the memory clock list found inside the "0F"clock values in the VP section of vbios
        
        Probably useless now due to the use of the VP profiles to find the other mem clocks of the vbios
        
        Hence it is now very simple (just reads 1 clock value found at one adress)
        """
        data = self.data
        VP_table_offset_list = self.VP_offset_list
        MEM_clock_list_2D = []
        
        for offset in VP_table_offset_list :
            
            # Third memory clock is ALWAYS 8 bytes after the first VP table entry  = easiest to find  
            
            #UPDATE -> This is kept...
            
            MEM_clock_list_2D.append((struct.unpack("<H", data[offset + 10: offset +10 +2])[0]*4, offset + 8))

        return MEM_clock_list_2D
        
    def check_return_offset(self, data, start_offset, bytes2check):
        """"
        will return empty list if nothing is found, else it will return the list 
        of all the BEGINNING offsets of the data (no overlap condition but shouldn't be a problem)
        """
        return_list = []
        while True:
            list_entry_wannabe = data.find(bytes2check, start_offset)
            if list_entry_wannabe == -1:
                break
            else:
                return_list.append(list_entry_wannabe)
                start_offset = list_entry_wannabe + len(bytes2check)
        #print(return_list)
        return return_list
    
    def get_power_table_list(self):
        
        """
        This functions looks for the power table table that contains the power limits + power slider
         It returns tupples (offset;calculated value) of : in order 
        - default power limit
        - limit power limit
        - power slider (True = enabled, False = disabled) CAN be 2 returns !! ada has 2 identical values !!
        
        It works by looking for hex string "28 46 0F 00 28 46 0F" That is present somewhere at the top of power limit table
        
        The returned list is 2D and can contain 2 sub lists -> Both sub lists should be identical but at different offsets!
        """
        data = self.data
        
        search_bytes = struct.pack("BBBBBBB", 0x28, 0x46, 0x0F, 0x00, 0x28, 0x46, 0x0F)
        power_list_2D = []
        
        if len(self.check_return_offset(data, 0, search_bytes)) > 0 and len(self.VP_offset_list) > 0:

            for offset in self.check_return_offset(data, 0, search_bytes) :  
            
                snippet1 = data[offset-200 : offset+200] # -200 to get before table
        
                # get the list of sliders
            
                slider_list = []
                slider_true = struct.pack("BBBBB", 0x0F, 0x02, 0xFF, 0xFF, 0xFF)
                slider_false = struct.pack("BBBBB", 0x0F, 0xFF, 0xFF, 0xFF, 0x02)
                slider_weird = struct.pack("BBBBB", 0x0F, 0x02, 0xFF, 0xFF, 0x02)
        
            #assumes there won't be 2 different values in the same vbios...
        
                for entry in self.check_return_offset(snippet1, 0, slider_false):
                    slider_list.append((False, entry + offset - 200))   
                for entry in self.check_return_offset(snippet1, 0, slider_true):
                    slider_list.append((True, entry + offset -200))
                for entry in self.check_return_offset(snippet1, 0, slider_weird):
                    slider_list.append((False, entry + offset -200))   
        
                # looks for the power values -> Only works for GPUS wit 2 power values aka all mobile gpus, 3090 desktop won't work for example
                # Method : count 3x"0x01" bytes after the offset string, power values are located 7 bytes after
                
                power_list = []
                
                snippet2 = data[offset : offset+200]
                
                power_offset = self.check_return_offset(snippet2, 0, struct.pack("BBB", 0x00, 0x01, 0x00))[2] + offset +7    
                
                power_list.append((struct.unpack("<I", data[power_offset: power_offset+4])[0], power_offset))
                
                power_list.append((struct.unpack("<I", data[power_offset +4: power_offset+8])[0], power_offset+4))
                
                power_list_2D.append(power_list + slider_list)
        else :
            power_list_2D = [-1]
        return power_list_2D
    
    def get_pci_device_id(self):
        """Return NVIDIA PCI device ID from a valid PCIR structure when possible."""
        data = self.data
        pos = 0
        while True:
            off = data.find(b"PCIR", pos)
            if off == -1 or off + 8 > len(data):
                break
            vendor = struct.unpack("<H", data[off + 4:off + 6])[0]
            device = struct.unpack("<H", data[off + 6:off + 8])[0]
            if vendor == 0x10DE and device not in (0x0000, 0xFFFF):
                return device
            pos = off + 1

        # Fallback only: scan for a plausible NVIDIA vendor/device pair.
        for i in range(0, max(0, len(data) - 4)):
            if data[i:i+2] == b"\xDE\x10":
                dev = struct.unpack("<H", data[i+2:i+4])[0]
                if 0x1000 <= dev <= 0x3FFF:
                    return dev
        return None
    
    def get_header_info(self):
        """
        This function returns a list of max 2 elements (1 for each vbios image), containing :
            - list containing :
                - vbios header start adress
                - vbios header end adress
        
        If no header is found the return list is None        
        """
        return_list = None
        # The check to know if there is a header is to read the first 4 bytes an make sure they are the universal "NVGI" string
        beginning_string = struct.pack(">I", 0x37343030) # the 7400 string
        
        list_of_beginning_offset = self.check_return_offset(self.data, 0, beginning_string)
        
        header_length = list_of_beginning_offset[0]-5
        
        if header_length != 0 :
            return_list = []
            for offset in list_of_beginning_offset:

                start = offset-header_length-5
                end = offset-5
                return_list.append([start, end])
        
        self.header_list = return_list
            

    def get_card_family(self):
        did = self.get_pci_device_id()
        if did is None:
            return "Unknown"
        # Blackwell mobile samples seen so far: 2C58 / 2C59.  Keep this range broad
        # enough for adjacent 50-series laptop SKUs without affecting older cards.
        if 0x2C00 <= did <= 0x2CFF:
            return "Blackwell"
        if 0x2700 <= did <= 0x27FF:
            return "Ada/Lovelace"
        if 0x2400 <= did <= 0x25FF:
            return "Ampere"
        if 0x1E00 <= did <= 0x21FF:
            return "Turing"
        if 0x1B00 <= did <= 0x1DFF:
            return "Pascal"
        return "Unknown"

    def get_card_architecture(self):
        """
        Returns a string : either "Pascal" or "Turing & newer"
        So that the rest of the program know if it must apply corrections to clock values (time 2 or divide by 2)
        
        NOW uses the length of the VP header !!
        New method !!
        """  
        
        return_string = "Pascal"  
        
        if self.VP_generation != "Pascal":
            return_string = "Turing & newer"
            self.clock_multiplier = 2
        
        family = self.get_card_family()
        if family == "Blackwell":
            # Existing clock/power edit logic does not yet understand Blackwell tables,
            # but the GUI must not crash; show read-only/unknown values and allow DCB viewing.
            self.clock_multiplier = 2
            return_string = "Blackwell"

        return return_string
    
    def calculate_correct_mem_data(self, value, vbios, adress):
        """
        This function calculates the corrected mem data based on the NEW value to code
        and the vbios to work on that contains the original values
        
        It returns a list of:
            - first 2 bytes
            - last 2 bytes
        """
        read_2_first_bytes = struct.unpack("<H", vbios[adress : (adress + 2)])[0]
        
        # FIRST BYTES CALCULATIONS
        
        clock_value_first_2_bytes = 0
        
        if read_2_first_bytes - 32768 - 16384 > 0:
            clock_value_first_2_bytes = value + 32768 + 16384
        elif read_2_first_bytes - 32768 > 0:
             clock_value_first_2_bytes = value + 32768
        elif read_2_first_bytes - 16384 > 0:
            clock_value_first_2_bytes = value + 16384
        else:
            clock_value_first_2_bytes = value #No clue if this is needed probably not
        
        return clock_value_first_2_bytes
        
    def calculate_correct_clock_data(self, value):
        """
        This function calculates the corrected mem data based on the Nvidia clock format
        
        -> Used when reading the core clock values
        
        It returns the corrected value:
        """
        return_value = 0
        
        if value - 32768 - 16384 > 0:
            return_value = value - 32768 - 16384
        elif value - 32768 > 0:
             return_value = value - 32768
        elif value - 16384 > 0:
            return_value = value - 16384
        else:
            return_value = value #No clue if this is needed probably not
        
        #print(return_value)
        return return_value
        
    def return_sorted_calculated_clock_list(self):
        """
        return sorted & calculated list going from :
        idle clock -> base clock -> boost clock -> max clock -> MEM clock
        all clocks are in MHz
        """
        # ONLY TAKES 4 FIRST VALUES BECAUSE OF PROBLEM WITH 1650M vbios
        
        clock_list = []
        if len(self.get_CORE_clock_list()) > 0:
            clock_list = sorted(set(self.get_CORE_clock_list()[0]))
        sorted_list = []
        
        # len = 4 is the usual structure :
        if len(clock_list) == 4 :
            sorted_list = clock_list
            sorted_list.append(self.MEM_clock_list[0][0]) 
            
        # len > 4 is not usual structure = 1650M, 10x0M, and other possibly
        
        
        elif len(clock_list) == 3: #Add compatibility for cards with only 3 values, supposing boost = max = like T1000 and P6
            clock_list.append(clock_list[2])
            clock_list.append(self.MEM_clock_list[0][0])
            sorted_list = clock_list
        
        elif len(clock_list) > 4:
            sorted_list.append(clock_list[0])
            for i in range(4):
                if clock_list[i+1]-clock_list[i] > 55 : # IF NOT 10x0M gpus don't show correct clocks due to an "intermediate" base clock value 
                    sorted_list.append(clock_list[i+1])     
                if len(sorted_list) > 4: # If NOT 1650 WON'T WORK + BRAKES PROGRAM BRUH
                    sorted_list.pop()
            sorted_list.append(self.MEM_clock_list[0][0])                 
        
        # len < 2 is UNSUPPORTED STRUCTURE (for now) no clock info will be given            
        else :
            sorted_list=[-1,-1,-1,-1,-1] #Dumb way of making sure no errors
        """
        # USELESS !!
        
        # CORRECTION OF CLOCK VALUES    
        multiplier = 1
        
        if self.get_card_architecture() == "Turing & newer":
            multiplier = 2
            
        for i in range(len(sorted_list)-1):
            sorted_list[i] = sorted_list[i] * multiplier
        """
        return sorted_list
    
# TESTING
""" 
with open("1060M.bin", "rb") as f:
        data = f.read()

parsed_vbios = parsed_data(data)
"""