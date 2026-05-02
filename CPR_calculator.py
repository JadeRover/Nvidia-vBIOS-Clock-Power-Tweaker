import struct
  
class parsed_data():
    def __init__(self, data):
        self.data = data
        self.VP_offset_list = self.find_v_p_table_offsets()    
    
    def find_v_p_table_offsets(self): #MODIFIED TO RETURN SEVERAL OFFSETS
        # This functions looks for the virtual p state table (VP table) that contains the max GPU clocks + mem clocks that 
        # the nvidia firware tells te GPU to apply, it scales voltage based on frequency (automatic) 
        # It returns the first clock offset
        
        # looks for hex string "20 XX 01" where XX is a variable between 8 and 25 = it's the VP table header length
        data = self.data
        
        offset2send = [] # Keep empty list of no entries found
    
        for i in range(9,28) :
            search_string = struct.pack("BBB", 0x20, i, 0x01)
            
            for entry in self.check_return_offset(data, 0, search_string):
                
                #print(f"entry is at offset {hex(entry)}")
                
                header_length = i +1 #The +1 is to not count the "0F" (or other denominator byte) indicating first VP entry
                chunk = data[(entry + header_length) : (entry + header_length + 4)]
                first_clock = struct.unpack("<I", chunk)[0] 
                
                #print(hex(first_clock))
                realfirstclock = first_clock/32768
                #print(realfirstclock)
                
                if realfirstclock > 100 and realfirstclock < 2000:
                    offset2send.append(entry + header_length) #Shouldn't be more than 2 VP tables inside vbios (from testing)
              
        return offset2send
    
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
                chunk = data[(offset + i*offset_jump) : (offset + 4 + i*offset_jump)]
                clock_entry = struct.unpack("<I", chunk)[0] 
                
                clock_value = clock_entry/32768
                
                if clock_value > 100 and clock_value < 3000:
                    clock_table.append(clock_value)
                else :
                    break
                i+= 1
                
            clock_table_2D.append(clock_table)
            
        return clock_table_2D
    
    def get_MEM_clock_list(self):
        data = self.data
        VP_table_offset_list = self.VP_offset_list
        MEM_clock_list_2D = []
        
        for offset in VP_table_offset_list :
            
            MEM_clock_list = []
            
            # Third memory clock is ALWAYS 8 bytes after the first VP table entry  = easiest to find        
            MEM_clock_list.append((struct.unpack("<I", data[offset + 8: offset +8 +4])[0]/32768, offset + 8))
            
            ### ADD CODE for getting first and second clock entry
            
            # Search starting 52 bytes before the first VP table entry, all the way to 100 bytes for a 4 byte little endian value
            # This is chosen for compatibility between pascal up to blackwell vbios that have it this way (non go all the way
            # up to 100 bytes before the first VP table entry)
            # containing the 2nd memory clock, first memory clock is the double of this value and coded only on 2 bytes
            # it is placed just before this 2nd memory clock : just have to look 2 bytes before it to read it
            
            # This search is done this way because sometimes 2nd and 3rd memory entry are not the same (few decimals off up  to 200Mhz+ off for Px200 cards)
            i = 45
            while i < 200:
                entry = struct.unpack("<I", data[offset - i: offset - i + 4])[0]/32768
                if entry > (MEM_clock_list[0][0] - 50) and entry < (MEM_clock_list[0][0] + 300) :
                    
                    #SECOND CHECK doe by checking if first MEM entry is more or less the double (+-1Mhz) of the 2nd MEM entry
                    second_clock = struct.unpack("<h", data[offset - i - 2: offset - i ])[0]
                    
                    if (entry > second_clock/2 -2) and (entry < second_clock/2 +2) :
                        MEM_clock_list.insert(0, (entry, offset - i))
                        break
                i += 1
            
            #Add the first clock entry
            MEM_clock_list.insert(0,((struct.unpack("<h", data[offset - i - 2: offset - i ])[0],offset - i - 2)))
            
            
            MEM_clock_list_2D.append(MEM_clock_list)
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
        
            #assumes there won't be 2 different values in the same vbios...
        
                for entry in self.check_return_offset(snippet1, 0, slider_false):
                    slider_list.append((False, entry + offset - 200))   
                for entry in self.check_return_offset(snippet1, 0, slider_true):
                    slider_list.append((True, entry + offset -200))    
        
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
    
    def get_card_architecture(self):
        """
        Returns a string : either "Pascal" or "Turing & newer"
        So that the rest of the program know if it must apply corrections to clock values (time 2 or divide by 2)
        """        
        clock_list = []
        if len(self.get_CORE_clock_list()) > 0:
            clock_list = sorted(set(self.get_CORE_clock_list()[0]))
        return_string = "Pascal"
        if len(clock_list) > 9:
            return_string = "Turing & newer"
        return return_string
        
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
        print(f"clock list = {clock_list}")
        # len = 4 is the usual structure :
        if len(clock_list) == 4 :
            sorted_list = clock_list
            sorted_list.append(self.get_MEM_clock_list()[0][0][0]) 
            
        # len > 4 is not usual structure = 1650M, 10x0M, and other possibly
        elif len(clock_list) > 4:
            sorted_list.append(clock_list[0])
            for i in range(4):
                if clock_list[i+1]-clock_list[i] > 55 : # IF NOT 10x0M gpus don't show correct clocks due to an "intermediate" base clock value 
                    sorted_list.append(clock_list[i+1])     
                if len(sorted_list) > 4: # If NOT 1650 WON'T WORK + BRAKES PROGRAM BRUH
                    sorted_list.pop()
            sorted_list.append(self.get_MEM_clock_list()[0][0][0])                 
        # len < 4 is UNSUPPORTED STRUCTURE (for now) no clock info will be given            
        else :
            sorted_list=[-1,-1,-1,-1,-1] #Dumb way of making sure no errors
           
        # CORRECTION OF CLOCK VALUES    
        multiplier = 1
        
        if self.get_card_architecture() == "Turing & newer":
            multiplier = 2
            
        for i in range(len(sorted_list)-1):
            sorted_list[i] = round(sorted_list[i] * multiplier)
        return sorted_list
    
# TESTING
"""    
with open("5060M.bin", "rb") as f:
        data = f.read()

parsed_vbios = parsed_data(data)

# print(check_return_offset(data, 0, struct.pack(">I", 0x201501)))

print("")
print(parsed_vbios.get_CORE_clock_list())
print("")
print("")

print("Power table (base, limit, power slider enabled [can be 2 identical entries @ different offsets]?)")
print("")
print(parsed_vbios.get_power_table_list())
print("")
print("")

print(parsed_vbios.get_card_architecture())
"""