import selectors
import socket
import threading
import os
import time

class DataNode:
    """ Node to store received data batches. """
    def __init__(self, content):
        self.content = content
        self.next_node = None
        self.book_next_node = None
        self.next_frequent_search = None  # This seems unused in current context. 

class ConcurrentDataList:
    """ A thread-safe list to store data nodes. """
    def __init__(self):
        self.tail_node = None
        self.lock = threading.Lock()

    def append(self, node):
        with self.lock:
            if self.tail_node:
                self.tail_node.next_node = node
            self.tail_node = node

class BookReceiver:
    """ Handles a book data sent by client. """
    
    def __init__(self, connection, data_list, book_id):
        self.selector = selectors.DefaultSelector() 
        self.connection = connection
        self.data_list = data_list
        self.connection.setblocking(False)
        self.selector.register(self.connection, selectors.EVENT_READ, self.receive_data)
        self.book_start = None
        self.book_end = None
        self.book_id = book_id
        self.last_data_time = time.time()

    def receive_data(self):
        """ Receives data from the client. """
        try:
            data = self.connection.recv(4096)
            if data:
                self.last_data_time = time.time()
                text_data = data.decode('utf-8', errors='ignore')
                node = DataNode(text_data)
                if not self.book_start:
                    self.book_start = node
                else:
                    self.book_end.book_next_node = node
                self.book_end = node
                self.data_list.append(node)
                print(f"From Book {self.book_id}, added Node with batch data: \n{text_data}\n")
            else:
                print("Disconnected from:", self.connection.getpeername())
                self.selector.unregister(self.connection)
                self.connection.close()
                self.save_to_file()

        except Exception as e:
            print(f"Error reading from client: {e}")
            self.selector.unregister(self.connection)
            self.connection.close()

    def save_to_file(self):
        """ Save received book data to a file. """
        if not os.path.exists('received_books'):
            os.makedirs('received_books')
        
        filepath = f'received_books/book_{str(self.book_id).zfill(2)}.txt'
        
        with open(filepath, 'w', encoding='utf-8') as file:
            current_node = self.book_start
            while current_node:
                file.write(current_node.content)
                current_node = current_node.book_next_node

        print(f"Saved book_{str(self.book_id).zfill(2)} to {filepath}")

    def run(self):
        """ Monitor connection for incoming data. """
        while True:
            events = self.selector.select(timeout=1)
            if events:
                for key, _ in events:
                    data_handler = key.data
                    data_handler()
                
            if time.time() - self.last_data_time > 10:
                print("No data received for 10 seconds. Closing connection.")
                self.selector.unregister(self.connection)
                self.connection.close()
                self.save_to_file()
                return

class TextReceiverServer:
    """ Server to receive text data (like books). """
    
    def __init__(self, host, port):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((host, port))
        self.server_socket.listen()
        self.received_books_count = 0
        self.data_list = ConcurrentDataList()

    def handle_client(self):
        """ Continuously accept client connections. """
        while True:
            client_connection, client_address = self.server_socket.accept()
            print("Connected to:", client_address)
            self.received_books_count += 1
            client_data_handler = BookReceiver(client_connection, self.data_list, self.received_books_count)
            threading.Thread(target=client_data_handler.run).start()

    def run(self):
        accept_clients_thread = threading.Thread(target=self.handle_client)
        accept_clients_thread.start()
        accept_clients_thread.join()

if __name__ == "__main__":
    server = TextReceiverServer('localhost', 1234)
    print("Text Receiver server started on port 1234...")
    server.run()
