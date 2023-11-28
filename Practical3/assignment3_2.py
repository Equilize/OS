import socket             
from _thread import *
import threading
import time
import sys
from collections import defaultdict
from queue import Queue
import argparse

shared_list = Queue()
print_lock = threading.Lock()
analysis_lock = threading.Lock()
search_pattern = sys.argv[1] if len(sys.argv) > 1 else "default_pattern"
analysis_interval = 5  # seconds

# thread function
def thread_tttt(c):
    while True:
        # print("id is:",threading.get_ident())
        # data received from client
        data = c.recv(1024)
        if not data:
            print('All done~ ')
             
            # lock released on exit
            #print_lock.release()
            break
 
            #add book shared list;
            with print_lock:
                shared_list.append(data)
            
            #add a lock
            
            
 
        # reverse the given string from client
        #data = data[::-1]
        print("id is:",threading.get_ident(),"\nmessage:",data)
        # send back reversed string to client
        c.send(data)
 
    # connection closed
    c.close()
    
    
    

def analysis_worker():
    occurrences = defaultdict(int)
    last_output_time = time.time()
    
    while True:
        try:
            # Try to get data from the shared list with a timeout
            data = shared_list.get(timeout=1)
            occurrences[data] += data.lower().count(search_pattern.lower())
        except Queue.Empty:
            pass
        current_time = time.time()
        if current_time - last_output_time >= analysis_interval:
            with analysis_lock:
                # Check again to make sure no other thread has printed the results
                if current_time - last_output_time >= analysis_interval:
                    sorted_occurrences = sorted(occurrences.items(), key=lambda x: x[1], reverse=True)
                    print("\nAnalysis Results:")
                    for book_title, count in sorted_occurrences:
                        print(f"{book_title}: {count}")
                    last_output_time = current_time
                    print("\nEnd of Analysis Results")

def create_files():
    for i in range(1,11):
        fileName = f"book_{i:02}.txt"
        content = str(i)
        
        with open(fileName,"w") as file:
            file.write(content)
        
        print(f"my file'{fileName}'already write in~ ")


if __name__ == "__main__":
    create_files()
   
# next create a socket object 
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)     
print ("Socket successfully created")
 
# reserve a port on your computer in our 
# case it is 12345 but it can be anything 
port = 12345 

s.bind(('', port))         
print ("socket binded to %s" %(port)) 
 
# put the socket into listening mode 
s.listen(5)     
print ("socket is listening")            
 
# a forever loop until we interrupt it or 
# an error occurs 
while True: 
 
# Establish connection with client. 
  c, addr = s.accept()     
  #print ('Got connection from', addr )
 
  # send a thank you message to the client. encoding to send byte type. 
  #c.send('Thank you for connecting'.encode()) 
  start_new_thread(thread_tttt, (c,))
 

  # Close the connection with the client 
  #c.close()
   
  # Breaking once connection closed
  #break