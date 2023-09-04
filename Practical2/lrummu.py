from mmu import MMU

class LruMMU(MMU):
    def __init__(self, frames):
        # TODO: Constructor logic for LruMMU
        self.frames = frames
        self.num_disk_read = 0
        self.num_disk_write = 0
        self.num_page_fault = 0
        self.debug = False
        self.list_page = [] #to staore page number and if it is dirty page
        self.page_set = set()

    def set_debug(self):
        # TODO: Implement the method to set debug mode
        self.debug = True

    def reset_debug(self):
        # TODO: Implement the method to reset debug mode
        self.debug = False

    def page_access(self, page_number, rw_mode):
        #an indicator to handle reading after a writing operation before this page being replaced
        r_after_w = False
        #if the page is not in the frame, then increment page fault and disk reading by 1
        if page_number not in self.page_set:
            self.num_page_fault += 1
            self.num_disk_read += 1
            if self.debug:
                print(f"Page fault\t{page_number: <16} ")
            #check if the frame is full
            if self.frames == len(self.list_page):
                #if yes, then pop the first one in the list, which is the least recently used
                replaced_page, dirty = self.list_page.pop(0)
                self.page_set.remove(replaced_page)
                #if the page is dirty, then operate disk write
                if dirty:
                    self.num_disk_write += 1
                    if self.debug:
                        print(f"Disk write\t{replaced_page: <16}")
                #else, discard the page, no disk write
                else:
                    if self.debug:
                        print(f"Discard\t\t{replaced_page: <16}")
        #if the page can be accessed from the frame
        else:
            #find the page to be operated
            for i in range(0, len(self.list_page)):
                if self.list_page[i][0] == page_number:
                    #if the page to be accessed has been written
                    if self.list_page[i][1]:
                        r_after_w = True
                    #move the page to the last position of the list
                    replaced_page, dirty = self.list_page.pop(i)
                    self.page_set.remove(page_number)
                    break
            #self.list_page = [(page_num, d) for page_num, d in self.list_page if page_num != page_number]
        #handle the circumstance that not changing the dirty control to false if the page has been written
        if not r_after_w:
            self.list_page.append((page_number, rw_mode == "W"))
        else:
            self.list_page.append((page_number, True))
        self.page_set.add(page_number)
        #print reading or writing
        if self.debug:
            WorR = "wirtting" if rw_mode == "W" else "reading"
            print(f"{WorR}\t{page_number: <16}")


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
