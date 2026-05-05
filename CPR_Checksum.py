import os
import struct

class checksummer:
    
    def __init__(self, vbios):
        self.vbios = vbios
        self.OG_checksum_list = self.get_OG_checksum() #len = number of images = usefull (either 1 or 2)
    
    def get_vbios_image_boundaries(self):
        """
        The aim of this fonction is to check if the vbios image is split into two IDENTICAL images
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
        - second item being second image checksum (nul if no second image)
        """            
        image_list = self.get_vbios_image_boundaries()
        
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
            return_list.append(result)
            start = result + 5
        
        return return_list
         
    def calculate_vbios_checksum(self):
            
            data = self.vbios 
            
            # The text explains that the checksum is derived from 
            # adding all 2-digit HEX codes together.
            total_sum = sum(data)
    
            # In an 8-bit checksum, we care about the value modulo 256
            # This gives us the "2-digit HEX" result (00 through FF)
            checksum_8bit = total_sum % 256
    
            print(f"--- BIOS Analysis ---")
            print(f"Total Bytes: {len(data)}")
            print(f"Full Mathematical Sum: {hex(total_sum).upper()}")
            print(f"8-bit Checksum (HEX): {hex(checksum_8bit).upper()[2:]}")
            print(f"8-bit Checksum (DEC): {checksum_8bit}")

    def fix_checksum_of_snippet(self, vbios_2_fix, start, end, OG_checksum_value):
        """
        This function fixes the checksum of vbios_2_fix that is only read between start and end, by editing
        values found in the please string (found locally in this var). Then fixing it to the original value
        """
        

# TESTING
"""
data = 0
with open("RTX3000.bin", "rb") as f:
    data = f.read()
vbios_checksum = checksummer(data)
vbios_checksum.calculate_vbios_checksum()
"""