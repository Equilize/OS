import selectors
import socket
import threading 
import time
import argparse

class BookNode:
    def __init__(self, data, book_title=None):
        self.data = data  # store the data
        self.next = None  # pointer to next node
        self.bookNext = None  # pointer to next node in the same book
        self.index = None  # search index assigned to the node
        self.patternCountNum = 0  # count num of pattern showed
        self.next_frequent_search = None  # pointer to the next node which has search mode
        self.bookTitle = ''
        self.book_title = book_title

class SharedList:
    def __init__(self):
        self.head = None
        self.tail = None
        self.lock = threading.Lock()  # use lock function from the threading library
        self.indexIncrement = 0  # assign a new index for the new
        self.lastProcessedNode = None
        self.lastPatternNode = None  # store the last node with pattern

    def append(self, node):
        # acquire lock
        with self.lock:  
            node.index = self.indexIncrement  # assign index for the new node
            self.indexIncrement += 1  # update next index number
            # add new node to the tail
            if self.tail:  
                self.tail.next = node
            # or become the head node
            else:
                self.head = node
                self.lastProcessedNode = self.head
            self.tail = node  # set tail node as new node

    def get_next_unprocessed_node(self):
        with self.lock:  # acquire lock
            current = self.lastProcessedNode
            while current:
                # search unproccessed node
                if not hasattr(current, "processed") or not current.processed:
                    current.processed = True
                    self.lastProcessedNode = current  # update the last processed node
                    return self.lastProcessedNode
                current = current.next
            return None

    def refine_next_frequent_search(self, current_node_with_pattern):
        with self.lock:  # acquire lock
            # if there exists node with the pattern
            if hasattr(self, 'lastPatternNode') and self.lastPatternNode:
                # determin if the current node should be the next frequent search node
                if (not self.lastPatternNode.next_frequent_search) or current_node_with_pattern.index < self.lastPatternNode.next_frequent_search.index:
                    self.lastPatternNode.next_frequent_search = current_node_with_pattern
            self.lastPatternNode = current_node_with_pattern  # update the last node with the pattern


class ClientProcessor:
    def __init__(self, conn, shared_list, book_number):
        self.selector = selectors.DefaultSelector()
        self.conn = conn 
        self.shared_list = shared_list
        self.book_head = None
        self.book_tail = None
        self.book_number = book_number
        self.last_received_time = time.time()
        self.conn.setblocking(False)  # set connection as not blocking
        self.selector.register(self.conn, selectors.EVENT_READ, self.read)

    def save_book(self):
        filename = f'book_{str(self.book_number).zfill(2)}.txt'  # define file name
        fileTitle = ''
        with open(filename, 'w', encoding='utf-8') as file:
            current = self.book_head
            while current:
                file.write(current.data)
                if not current.bookNext:
                    fileTitle = current.bookTitle
                current = current.bookNext
        # output book saved info
        print(f"Saved book_{str(self.book_number).zfill(2)} {fileTitle} to {filename}")

    def run(self):
        while True:  # keep listening
            events = self.selector.select(timeout=1)
            if events:
                for key, _ in events:
                    callback = key.data
                    callback()
            # if no data in 8 sec, close the connection
            if time.time() - self.last_received_time > 8:
                print("No data received for 8 seconds. Closing connection.")
                self.selector.unregister(self.conn)
                self.conn.close()
                self.save_book()
                return

    def process_data(self, data):
        decoded_data = data.decode('utf-8', errors='ignore')
        node = BookNode(decoded_data, f"Book {self.book_number}")
        if self.book_head is None:  # if the first time to receive data
            node.bookTitle = decoded_data.split('\n')[0]
            self.book_head = node
            #print(node.bookTitle)
        else:
            node.bookTitle = self.book_tail.bookTitle
            self.book_tail.bookNext = node
            #print(node.bookTitle)
        self.book_tail = node
        self.shared_list.append(node)
        print(f"Data received from Book {self.book_number}. \n{decoded_data}\n---------------------------")

    def read(self):
        try:
            data = self.conn.recv(1024)
            if data:
                self.last_received_time = time.time()  # update the last time of data received
                self.process_data(data)
            # if no data, then connection closed. usually timedout. has never executed these code
            else:  
                print("Disconnected from:", self.conn.getpeername())
                self.selector.unregister(self.conn)  # cancel register
                self.conn.close()  # close connection
                self.save_book()  # save book
        except Exception as e:
            print(f"Error reading from client: {e}")  # print error info
            self.selector.unregister(self.conn) 
            self.conn.close()

class EchoServer:
    def __init__(self, host, port, shared_list):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((host, port))
        self.server_socket.listen(5)
        self.shared_list = shared_list
        self.book_counter = 1

    def run(self):
        print("Server is initiated. Listening:")
        while True:
            conn, addr = self.server_socket.accept()  #accept new connection
            print(f"Connection from port number {addr}")
            handler = ClientProcessor(conn, self.shared_list, self.book_counter)
            threading.Thread(target=handler.run).start()  # initiate new thread to process the client connection
            self.book_counter += 1  # increment the number of book processed

# inherit from class threading
class AnalysisThread(threading.Thread):
    def __init__(self, shared_list, pattern, thread_id):
        super().__init__()
        self.pattern = pattern  # pattern to tbe searched
        self.thread_id = thread_id  # set thread ID
        self.shared_list = shared_list  # set the shared list

    # the function to sort the books by frequency of the pattern
    def sort_by_pattern(self):
        with self.shared_list.lock:  #use lock
            books = {}  # to store the books and its current frequency
            current = self.shared_list.head
            while current:
                if current.book_title in books:  # if the book has been stored
                    books[current.book_title] += current.patternCountNum  # add the number of pattern in the new node
                else:
                    books[current.book_title] = current.patternCountNum  # initiate with the num count of the first pattern
                current = current.next 
            return sorted(books.items(), key = lambda x: x[1], reverse = True)  # sort books by frequency

    # function to print the analysis
    def output_results(self):
        with AnalysisProcessors.output_lock:  # use lock
            current_time = time.time()
            if current_time - AnalysisProcessors.last_output_time >= 2:  # output the analysis result once in 2s
                sorted_books = self.sort_by_pattern()  # acquire sorted frequencies
                #print(sorted_books)
                print("========================================")
                print(f"Analysis Thread {self.thread_id}:     ")
                # print the ranking
                for title, count in sorted_books:
                    print(f"{title}: {count} occurrences  ")
                print("========================================")
                # update the last output time
                AnalysisProcessors.last_output_time = current_time

    # rewrite run function
    def run(self):
        while True:
            # find the next node to be processed
            node = self.shared_list.get_next_unprocessed_node()
            # if no data to be processed
            if node is None:
                # put into sleep for 2 sec
                time.sleep(2)
                continue
            if self.pattern in node.data:
                with self.shared_list.lock:  # use lock
                    # add num of pattern found
                    node.patternCountNum += node.data.count(self.pattern)
                # update the next node with pattern
                self.shared_list.refine_next_frequent_search(node)
            self.output_results()

class AnalysisProcessors:
    output_lock = threading.Lock()  # to be used in analysis thread
    last_output_time = 0  # record last output time

    def __init__(self, shared_list, pattern, thread_count):
        self.pattern = pattern  # pattern to tbe searched
        self.shared_list = shared_list  # set the shared list
        self.thread_count = thread_count
        self.threads = []  # to store the threads

    def start_threads(self):
        for _ in range(self.thread_count):
            # create new analysis thread
            thread = AnalysisThread(self.shared_list, self.pattern, len(self.threads) + 1)
            thread.start()
            self.threads.append(thread)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--listen", type=int, required=True, help="Listening port")
    parser.add_argument("-p", "--pattern", type=str, required=True, help="Search pattern")
    args = parser.parse_args()

    shared_list = SharedList()
    server = EchoServer('localhost', args.listen, shared_list)

    Number_of_Thread = 4 # number of analysis threads to be used. can be redefined
    analysis_handler = AnalysisProcessors(shared_list, args.pattern, Number_of_Thread)
    analysis_handler.start_threads()
    print(f"{Number_of_Thread} analysis threads are runnning-----------------\n")
    print(f"Echo server started on port {args.listen} \n")
    server.run()