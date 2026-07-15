import struct

class checksummer:
    
    def __init__(self, vbios):
        self.vbios = vbios
        self.image_boundaries = self.get_vbios_image_boundaries()
        self.OG_checksum_list = self.get_OG_checksum() #len = number of images = usefull (either 1 or 2)
    
    def get_vbios_image_boundaries(self):
        """
        The aim of this fonction is to check if the vbios image is split into two IDENTICAL (or almost) images
        Important because the cheksum must be applied to each subsection individually.
        
        Therefore this function will return a list that has tupples : first value is beginning of image length, last value is end of image
        """
        
        # The way to be "sure" to know if we have a dual vbios is if the "NVGI" string (found in header) is present with FF FF values before
        # This supposes that all dual image vbios have a header !!
        
        search_string = struct.pack(">IIIII", 0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF, 0x4E564749)
        return_list=[(0, len(self.vbios))]
        
        search_result = self.vbios.find(search_string)
        
        if search_result != -1:
            return_list = [(0, search_result+16), (search_result+16, len(self.vbios))]
        return return_list
    
    def get_OG_checksum(self):
        """
        This function must return the original checksum value (to be stored in internal variables)
        It will be a list with :
        - first item being first image checksum 
        - second item being second image checksum (not filled if no second image)
        """            
        image_list = self.get_vbios_image_boundaries()
        data = self.vbios
        checksum_list = []
        
        for tupple in image_list :
            total_sum = sum(data[tupple[0]: tupple[1]])
            checksum_list.append(total_sum)
        
        return checksum_list  
    
    def get_PLEASE_img_area(self):
        """
        This function will return the offset of the "PLEASE" area from the vbios img that can be overwritten to fix checksums
        It will be a list : first entry = offset for img1, second entry = offset for img2
        
        USELESS FUNCTION TO REMOVE
        
        """
        search_string = struct.pack(">I", 0x504C4541)
        return_list = []
        start = 0
        for i in range(len(self.OG_checksum_list)):
            result = self.vbios.find(search_string, start)
            return_list.append(result+6)
            start = result + 12
        
        return return_list
         
    def calculate_vbios_checksum(self):
        """
        TESTING FUNCTION
        """ 
        data = self.vbios 
        
        # The text explains that the checksum is derived from 
        # adding all 2-digit HEX codes together.
        total_sum = sum(data)

        # In an 8-bit checksum, we care about the value modulo 256
        # This gives us the "2-digit HEX" result (00 through FF)
        checksum_8bit = total_sum % 256

        """
        print(f"--- BIOS Analysis ---")
        print(f"Total Bytes: {len(data)}")
        print(f"Full Mathematical Sum: {hex(total_sum).upper()}")
        print(f"8-bit Checksum (HEX): {hex(checksum_8bit).upper()[2:]}")
        print(f"8-bit Checksum (DEC): {checksum_8bit}")
        print()
        print()
        """
    
    def VP_checksum_data_finder(self, vbios2fix, start_offset, offset_VP_header):
        """
        This function is used to find the boundaries of the section containing the virtual P state table in order to then fix the checksum after modification
        
        It returns a list containing : VP_section_checksum, value of edit byte, adress of edit byte
        """
        number_string = struct.pack(">I",0x37343030) #7400 string located 5 bytes after the end of the NVGI header
        
        number_adress = vbios2fix[start_offset:offset_VP_header].find(number_string)-5+start_offset
        
        padding_string = struct.pack(">IIIIIIIIIIIIIIIIIIIIIIII", 0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF)
        
        search_result = vbios2fix[offset_VP_header:].find(padding_string) + offset_VP_header + 5 # Whatever the + 5 doesn't change anything
        
        #Algorithm to find the checksum edit byte adress
        found = False
        i=search_result
        while not found:
            cursor = struct.unpack(">B", self.vbios[i:i+1])[0]
            if cursor != 255:
                found = True
            i+=1
        
        adress_edit_byte = i
        
        checksum_VP_section = sum(vbios2fix[number_adress:adress_edit_byte])
        
        value_edit_byte = struct.unpack(">B", self.vbios[i-1:i])[0]

        return_list = [checksum_VP_section%256, value_edit_byte, adress_edit_byte-1]
        
        #print(return_list)
        return return_list

    def fix_VP_section_checksum(self, vbios_2_fix, VP_table_data):
        
        for i in range(len(self.image_boundaries)) :
            start_offset = self.image_boundaries[i][0]
            VP_table_offset = VP_table_data[i]
            
            checksum_list = self.VP_checksum_data_finder(vbios_2_fix, start_offset, VP_table_offset)     
            
            #Now to fix the 8bit checksum :
            fix_byte_value = struct.unpack("B", vbios_2_fix[checksum_list[2]:checksum_list[2]+1])[0]
            
            if checksum_list[1] - checksum_list[0] > 0:
                fix_byte_value = checksum_list[1] - checksum_list[0]
            if checksum_list[1] - checksum_list[0] < 0:
                fix_byte_value = checksum_list[1] + (256 - checksum_list[0])
                
            vbios_2_fix[checksum_list[2]:checksum_list[2]+1] = struct.pack("B", fix_byte_value)
            

    def fix_checksum_of_vbios(self, vbios_2_fix, VP_table_offset):
        """
        This function fixes the checksum of vbios_2_fix that is only read between start and end, by editing
        values found in the please string (found locally in this var). Then fixing it to the original value
        """
        
        self.fix_VP_section_checksum(vbios_2_fix, VP_table_offset)
        """
        OG_checksum_list = self.get_OG_checksum()
        img_boundaries_list = self.get_vbios_image_boundaries()
        please_locations_list = self.get_PLEASE_img_area()
        difference_list = []
        
        for i in range(len(OG_checksum_list)):
            total_sum = sum(vbios_2_fix[img_boundaries_list[i][0]: img_boundaries_list[i][1]])
            difference_list.append(total_sum- OG_checksum_list[i]) #In case the difference is not the same (it should be)
        
        
        
        if difference_list[0] == difference_list[1]:
            
        
            for i in range(2):
                please_location = please_locations_list[i]
                j= 0
                
                while difference_list[i] !=0:
                    letter = struct.unpack("B", vbios_2_fix[please_location+j:please_location+1+j])[0]
                    print(f"letter is {letter} and difference = {difference_list[i]}")
                    print()
                    
                    if difference_list[i] > 0:
                        if letter < difference_list[i]:
                            difference_list[i] -= letter
                            vbios_2_fix[please_location+j:please_location+1+j] = struct.pack("B", 0)
                            j+=1
                        else:
                            print(letter - difference_list[i])
                            vbios_2_fix[please_location+j:please_location+1+j] = struct.pack("B", letter - difference_list[i])
                            difference_list[i] = 0
                            j+=1
                        
                    else :
                        if letter < -1*difference_list[i]:
                            difference_list[i] += (255-letter)
                            vbios_2_fix[please_location+j:please_location+1+j] = struct.pack("B", 255)
                            j+=1
                        else :
                            print(letter + difference_list[i])
                            vbios_2_fix[please_location+j:please_location+1+j] = struct.pack("B", (letter + difference_list[i]))
                            difference_list[i] = 0
                            j+=1
                    
                    print(f"now difference is = {difference_list[i]}")
            
            
            
        # GEMINI (AI) code as I was getting deperate debuggin my code that is commented just above :(
        
        for i in range(len(OG_checksum_list)):
            total_sum = sum(vbios_2_fix[img_boundaries_list[i][0]: img_boundaries_list[i][1]])
            # This tracks exactly how much the sum needs to change to reach the OG target
            difference_list.append(total_sum - OG_checksum_list[i])
            
            # We only proceed if both images have the same discrepancy (as per your logic)
            please_location = please_locations_list[i]
            j = 0
            
            while difference_list[i] != 0:
                # Get the current byte
                letter = struct.unpack("B", vbios_2_fix[please_location+j:please_location+1+j])[0]
                
                if difference_list[i] > 0:
                    # The current sum is too HIGH. We need to decrease bytes.
                    if letter >= difference_list[i]:
                        # This byte can absorb the entire difference
                        new_val = letter - difference_list[i]
                        vbios_2_fix[please_location+j:please_location+1+j] = struct.pack("B", new_val)
                        difference_list[i] = 0
                    else:
                        # Drain this byte to 0 and move to the next
                        vbios_2_fix[please_location+j:please_location+1+j] = struct.pack("B", 0)
                        difference_list[i] -= letter 
                
                else:
                    # The current sum is too LOW (difference is negative). We need to increase bytes.
                    # How much 'room' is left in this byte to reach 255?
                    room = 255 - letter
                    needed = abs(difference_list[i])
                    
                    if room >= needed:
                        # This byte can absorb the entire negative difference
                        new_val = letter + needed
                        vbios_2_fix[please_location+j:please_location+1+j] = struct.pack("B", new_val)
                        difference_list[i] = 0
                    else:
                        # Fill this byte to 255 and move to the next
                        vbios_2_fix[please_location+j:please_location+1+j] = struct.pack("B", 255)
                        difference_list[i] += room # We reduced the negative gap by the amount of 'room' used
            
                j += 1      
        """   
        return vbios_2_fix
        
        
"""
# TESTING
data = 0
with open("1060M.bin", "rb") as f:
    data = f.read()
vbios_checksum = checksummer(data)
vbios_checksum.calculate_vbios_checksum()
vbios_checksum.find_VP_image_limits(data,0,108656)
"""

