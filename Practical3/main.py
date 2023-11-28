import selectors
import socket
import threading
import os
import time
class BookBookNode:
    def __init__(self,data):
        self.data = data
        self.next = None
        self.book_next = None
        self.next_frequent_search = None

class SharedList:
   def __init__(self):
      self.tail = None
      self.lock = threading.Lock()

def append(self, node):
    with self.lock:
        if self.tail:
            self.tail.next = node
        self.tail = node

class ClientHandler:
    def __init__(self, conn, shared_list, book_number):
        self.selector = selectors.DefaultSelector()
        self.conn = conn
        self.shared_list = shared_list
        self.conn.setblocking(False)
        self.selector.register(self.conn,selectors.EVENT_READ, self.read)
        self.book_head = None
        self.book_tail = None
        self.book_number = book_number
        self.last_received_time = time.time()
    
    def read(self):
        try:
            data = self.conn.recv(1024)
            if data:
                self.last_received_time = time.time()
                decoded_data = data.decode('utf-8', errors='ignore')
                node = BookNode(decoded_data)
                if self.book_head is None:
                    self.book_head = node
                else:
                    self.book_tail.book_next = node
                self.book_tail= node
                self.shared_list.append(node)
                print(f"from Book {self.book_number}, added BookNode with batch data: \n{decoded_data}\n")
            else:
                print("Disconnected from:", self.conn.getpeername())
                self.selector.unregister(self.conn)
                self.conn.close()
                self.save_book()

        except Exception as e:
            print(f"Error reading from client: {e}")
            self.selector.unregister(self.conn)
            self.conn.close()

    def save_book(self):
        if not os.path.exists('received_output_folder'):
            os.makedirs('received_output_folder')

        filename = f'received_output_folder/book_{str(self.book_number).zfill(2)}.txt'

        with open(filename,'w',encoding='utf-8') as file:
            current = self.book_head
            while current:
                file.write(current.data)
                current = current.book_next
        print(f"Saved book_{str(self.book_number).zfill(2)} to {filename}")

    def run(self):
        while True:
            events = self.selector.select(timeout=1) 
            if events:
                for key, _ in events:
                    callback = key.data
                    callback()
            if time.time() - self.last_received_time > 5: 
                print("No data received for 5 seconds. Closing connection.")
                self.selector.unregister(self.conn)
                self.conn.close()
                self.save_book()
                return

class EchoServer:
    def init__(self, host, port):
        self.server_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.server_socket.bind((host, port))
        self.server_socket.listen()
        self.book_count = 0
        self.shared_list = SharedList()

    def accept_client(self):
        while True:
            conn, addr = self.server_socket.accept()
            print("Connected to:", addr)
            self.book_count += 1
            client_handler = ClientHandler(conn, self.shared_list, self.book_count)
            threading.Thread(target=client_handler.run).start()
    
    def run(self):
        accept_thread = threading.Thread(target=self.accept_client)
        accept_thread.start()
        accept_thread.join()

if __name__ == "__main__":
    server = EchoServer('localhost', 12345)
    print("Echo server started on port 12345...")
    server.run()


