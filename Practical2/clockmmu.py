from mmu import MMU


class ClockMMU(MMU):
    def __init__(self, frames):
        # TODO: Constructor logic for EscMMU
        super().__init__()
        self.frames = frames
        self.frame_list = [None] * frames #Pages
        self.num_disk_read = 0
        self.num_disk_write = 0
        self.num_page_fault = 0
        self.debug = False
        self.use_bit = [(0, 0) for _ in range(frames)]  #Use bit, Dirty bit
        self.pointer = 0 # Clock hand

    def set_debug(self):
        # TODO: Implement the method to set debug mode
        self.debug = True

    def reset_debug(self):
        # TODO: Implement the method to reset debug mode
        self.debug = False

    def find_replacement_index(self):
        while True:
            #Loop till replacement is found (use = 0)
            if self.use_bit[self.pointer][0] == 0:  
                return self.pointer
            #Set use = 1 to use = 0 if looped through
            self.use_bit[self.pointer] = (0, self.use_bit[self.pointer][1])  
            #Circular rotation
            self.pointer = (self.pointer + 1) % self.frames


    def page_access(self, page_number, rw_mode):
        if page_number in self.frame_list:
            #Update used bit index and dirty bit
            index = self.frame_list.index(page_number)
            self.use_bit[index] = (1, self.use_bit[index][1] or rw_mode == "W")
            
            if self.debug:
                WorR = "writing" if rw_mode == "W" else "reading"
                print(f"{WorR}\t{page_number: <16}")
        else:
            #Page fault occurred
            self.num_page_fault += 1
            self.num_disk_read += 1
            
            if self.debug:
                print(f"Page fault\t{page_number: <16}")

            index_to_replace = self.find_replacement_index()
            
            #Check if page to be replaced is dirty
            if self.use_bit[index_to_replace][1]:  
                self.num_disk_write += 1
                if self.debug:
                    print(f"Disk write\t{self.frame_list[index_to_replace]: <16}")
                
            self.frame_list[index_to_replace] = page_number
            self.use_bit[index_to_replace] = (1, rw_mode == "W")
            
            if self.debug:
                WorR = "writing" if rw_mode == "W" else "reading"
                print(f"{WorR}\t{page_number: <16}")
            
            #Clock hand loop to next frame
            self.pointer = (index_to_replace + 1) % self.frames
        

    def read_memory(self, page_number):
        # TODO: Implement the method to read memory
        self.page_access(page_number, "R")

    def write_memory(self, page_number):
        # TODO: Implement the method to write memory
        self.page_access(page_number, "W")

    def get_total_disk_reads(self):
        # TODO: Implement the method to get total disk reads
        return self.num_disk_read

    def get_total_disk_writes(self):
        # TODO: Implement the method to get total disk writes
        return self.num_disk_write

    def get_total_page_faults(self):
        # TODO: Implement the method to get total page faults
        return self.num_page_fault
