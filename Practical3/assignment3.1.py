
import argparse
import threading
import socket  # Import the socket module
import time


class Node:
    def __init__(self, data, book_title=None):
        self.data = data
        self.next = None
        self.book_next = None
        self.book_title = book_title
        self.next_frequent_search = None
        self.pattern_count = 0
        self.index = None

class SharedList:
    def __init__(self):
        self.head = None
        self.tail = None
        self.lock = threading.Lock()
        self.current_search_pointer = None
        self.last_processed_node = None
        self.node_index = 0  
        self.last_node_with_pattern = None  


    def append(self, node):
        with self.lock:
            if self.tail:
                self.tail.next = node
            else:
                self.head = node
            self.tail = node

    def get_next_unprocessed_node(self):
        with self.lock:
            current = self.head
            while current:
                if not hasattr(current, "processed") or not current.processed:
                    current.processed = True
                    return current
                current = current.next
            return None
        
    def update_next_frequency_search(self, current_node_with_pattern):
        with self.lock:  # acquire lock
            # if there exists node with the pattern
            if hasattr(self, 'last_node_with_pattern') and self.last_node_with_pattern:
                # determin if the current node should be the next frequent search node
                if (not self.last_node_with_pattern.next_frequent_search) or \
                (self.last_node_with_pattern.next_frequent_search.index > current_node_with_pattern.index):
                    self.last_node_with_pattern.next_frequent_search = current_node_with_pattern
            self.last_node_with_pattern = current_node_with_pattern  # update the last node with the pattern




class ClientHandler:
    def __init__(self, conn, shared_list, book_number):
        self.conn = conn
        self.shared_list = shared_list
        self.book_number = book_number
        self.book_head = None
        self.book_tail = None

    def handle_client(self):
        try:
            while True:
                data = self.conn.recv(1024)
                if not data:
                    break
                self.process_data(data)
        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            self.conn.close()
            self.save_book()

    def process_data(self, data):
        decoded_data = data.decode('utf-8', errors='ignore')
        node = Node(decoded_data, f"Book {self.book_number}")
        if not self.book_head:
            self.book_head = node
        else:
            self.book_tail.book_next = node
        self.book_tail = node
        self.shared_list.append(node)

    def save_book(self):
        filename = f'book_{str(self.book_number).zfill(2)}.txt'
        with open(filename, 'w', encoding='utf-8') as file:
            current = self.book_head
            while current:
                file.write(current.data)
                current = current.book_next
        print(f"Saved book_{str(self.book_number).zfill(2)} to {filename}")



class EchoServer:
    def __init__(self, host, port, shared_list):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((host, port))
        self.server_socket.listen(5)
        self.shared_list = shared_list
        self.book_counter = 1

    def run(self):
        try:
            print("Server is listening...")
            while True:
                conn, _ = self.server_socket.accept()
                handler = ClientHandler(conn, self.shared_list, self.book_counter)
                threading.Thread(target=handler.handle_client).start()
                self.book_counter += 1
        except KeyboardInterrupt:
            print("Server shutting down.")
        finally:
            self.server_socket.close()

    def accept_client(self):
        conn, addr = self.server_socket.accept()
        print(f"Connection from: {addr}")
        return conn



class AnalysisThread(threading.Thread):
    def __init__(self, shared_list, pattern, thread_id):
        super().__init__()
        self.shared_list = shared_list
        self.pattern = pattern
        self.thread_id = thread_id
        self.pattern_count = {}

    def run(self):
        while True:
            node = self.shared_list.get_next_unprocessed_node()
            if node is None:
                time.sleep(2)
                continue

            if self.pattern in node.data:
                book_title = node.book_title
                self.pattern_count[book_title] = self.pattern_count.get(book_title, 0) + 1

            if time.time() % 5 == 0:  # Output every 5 seconds
                self.output_results()

    def output_results(self):
        sorted_books = sorted(self.pattern_count.items(), key=lambda x: x[1], reverse=True)
        print(f"Thread {self.thread_id} Analysis Results:")
        for book, count in sorted_books:
            print(f"{book}: {count} occurrences of '{self.pattern}'")

class AnalysisThreadHandler:
    def __init__(self, shared_list, pattern, thread_count):
        self.shared_list = shared_list
        self.pattern = pattern
        self.threads = [AnalysisThread(shared_list, pattern, i) for i in range(thread_count)]

    def start_threads(self):
        for thread in self.threads:
            thread.start()

    def join_threads(self):
        for thread in self.threads:
            thread.join()

def main():
    parser = argparse.ArgumentParser(description='Multi-threaded network server for text processing.')
    parser.add_argument('-l', '--listen', type=int, required=True, help='Listening port')
    parser.add_argument('-p', '--pattern', type=str, required=True, help='Search pattern')
    args = parser.parse_args()

    shared_list = SharedList()  # Create an instance of SharedList
    analysis_handler = AnalysisThreadHandler(shared_list, args.pattern, 2)  # 2 analysis threads

    # Initialize and start the server
    server = EchoServer('localhost', args.listen, shared_list)
    server_thread = threading.Thread(target=server.run)
    server_thread.start()

    # Start analysis threads
    analysis_handler.start_threads()

    # Wait for the server thread to finish
    server_thread.join()
    analysis_handler.join_threads()

if __name__ == "__main__":
    main()
