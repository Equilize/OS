#版本说明：实现Analysis Thread竞争。
import selectors
import socket
import threading 
import os
import time
import argparse

class Node:
    def __init__(self, data, book_title=None):
        self.data = data  # store the data
        self.next = None  # pointer to next node
        self.book_next = None  # pointer to next node in the same book
        self.next_frequent_search = None  # pointer to the next node which has search mode
        self.book_title = book_title  
        self.pattern_count = 0  # count num showed
        self.index = None  # search index assigned to the node

    def contains_pattern(self, pattern):
        # check if there is the pattern contained
        return pattern in self.data


class SharedList:
    def __init__(self):
        self.head = None
        self.tail = None
        self.lock = threading.Lock()  # use lock function from the threading library
        self.current_search_pointer = None
        self.last_processed_node = None
        self.node_index = 0  # assign a new index for the new node
        self.last_node_with_pattern = None  # store the last node with pattern

    def append(self, node):
        with self.lock:  # acquire lock
            node.index = self.node_index  # assign index for the new node
            self.node_index += 1  # update next index number
            if self.tail:  # add new node to the tail
                self.tail.next = node
            else:  # or become the head node
                self.head = node
            self.tail = node  # set tail node as new node

    def get_next_unprocessed_node(self):
        with self.lock:  # acquire lock
            current = self.head
            while current:
                # search unproccessed node
                if not hasattr(current, "processed") or not current.processed:
                    current.processed = True
                    self.last_processed_node = current  # update the last processed node
                    return current
                current = current.next
            return None

    def update_next_frequent_search(self, current_node_with_pattern):
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
        self.selector = selectors.DefaultSelector()
        self.conn = conn 
        self.shared_list = shared_list
        self.conn.setblocking(False)  # set connection as not blocking
        self.selector.register(self.conn, selectors.EVENT_READ, self.read)
        self.book_head = None
        self.book_tail = None
        self.book_number = book_number
        self.last_received_time = time.time()

    def read(self):
        try:
            data = self.conn.recv(1024)
            if data:
                self.last_received_time = time.time()  # update the last time of data received
                decoded_data = data.decode('utf-8', errors='ignore')
                node = Node(decoded_data, f"Book {self.book_number}")
                if self.book_head is None:  # if the first time to receive data
                    self.book_head = node
                else:
                    self.book_tail.book_next = node
                self.book_tail = node
                self.shared_list.append(node)
                print(f"Data received from Book {self.book_number}. Added Node with batch data: \n{decoded_data}\n")
            else:  # if no data, then connection closed. usually timedout. has never executed these code
                print("Disconnected from:", self.conn.getpeername())
                self.selector.unregister(self.conn)  # cancel register
                self.conn.close()  # close connection
                self.save_book()  # save book
        except Exception as e:
            print(f"Error reading from client: {e}")  # 输出错误信息
            self.selector.unregister(self.conn)  # 取消注册
            self.conn.close()  # 关闭连接

    def save_book(self):
        filename = f'book_{str(self.book_number).zfill(2)}.txt'  # 定义保存的文件名
        with open(filename, 'w', encoding='utf-8') as file:  # 打开文件进行写入
            current = self.book_head  # 从头节点开始
            while current:  # 遍历每个节点
                file.write(current.data)  # 写入数据
                current = current.book_next  # 移动到下一个节点
        print(f"Saved book_{str(self.book_number).zfill(2)} to {filename}")  # 输出保存成功的信息

    def run(self):
        while True:  # 持续监听
            events = self.selector.select(timeout=1)  # 使用selector等待事件，超时时间为1秒
            if events:  # 如果有事件发生
                for key, _ in events:  # 遍历所有事件
                    callback = key.data  # 获取回调函数
                    callback()  # 执行回调函数
            if time.time() - self.last_received_time > 5:  # 如果超过5秒没有接收到任何数据
                print("No data received for 5 seconds. Closing connection.")  # 输出信息
                self.selector.unregister(self.conn)  # 取消注册
                self.conn.close()  # 关闭连接
                self.save_book()  # 保存书籍
                return  # 结束此方法


class AnalysisThread(threading.Thread):  # 分析线程类，继承自threading.Thread类
    def __init__(self, shared_list, pattern, thread_id):
        super().__init__()  # 调用父类的初始化方法
        self.shared_list = shared_list  # 设置共享链表对象
        self.pattern = pattern  # 设置要搜索的关键字
        self.thread_id = thread_id  # 设置线程ID

    def run(self):  # 重写Thread类的run方法
        while True:
            node = self.shared_list.get_next_unprocessed_node()  # 获取下一个未处理的节点
            if node is None:  # 如果没有找到未处理的节点
                time.sleep(2)  # 线程休眠2秒
                continue  # 继续下一个循环

            contains_pattern = node.contains_pattern(self.pattern)  # 检查节点中是否包含模式或关键字
            if contains_pattern:  # 如果包含
                with self.shared_list.lock:  # 使用锁确保线程安全
                    node.pattern_count += 1  # 增加节点的模式计数
                self.shared_list.update_next_frequent_search(node)  # 更新节点的下一个包含”关键词“的节点

            self.attempt_to_output_results()  # 尝试输出结果

    def attempt_to_output_results(self):  # 尝试输出结果方法
        with AnalysisThreadHandler.output_lock:  # 使用锁确保线程安全
            current_time = time.time()  # 获取当前时间
            if current_time - AnalysisThreadHandler.last_output_time >= 2:  # 如果上次输出时间已经超过5秒
                self.output_results()  # 输出结果
                AnalysisThreadHandler.last_output_time = current_time  # 更新最后输出时间

    def output_results(self):  # 输出结果方法
        sorted_books = self.get_sorted_books_by_pattern_count()  # 获取按模式计数排序的书籍
        print("--------------------------")
        print(f"| Analysis Thread {self.thread_id}:     ")
        for title, count in sorted_books:  # 遍历排序后的书籍
            print(f"| {title}: {count} occurrences  ")
        print("--------------------------")

    def get_sorted_books_by_pattern_count(self):  # [Optional] 获取按模式计数排序的书籍的方法  学校好像没有要求，但方便我对比
        with self.shared_list.lock:  # 使用锁确保线程安全
            books = {}  # 初始化一个空字典，用于存储书籍和模式计数
            current = self.shared_list.head  # 设置当前节点为链表的头节点
            while current:  # 遍历链表中的每个节点
                if current.book_title not in books:  # 如果当前节点的书籍标题不在字典中
                    books[current.book_title] = current.pattern_count  # 将书籍标题和模式计数添加到字典中
                else:  # 如果当前节点的书籍标题已经在字典中
                    books[current.book_title] += current.pattern_count  # 增加模式计数
                current = current.next  # 设置当前节点为下一个节点

            return sorted(books.items(), key=lambda x: x[1], reverse=True)  # 返回按模式计数降序排序的书籍


class AnalysisThreadHandler:
    last_output_time = 0  # 类级别变量，记录最后一次输出的时间
    output_lock = threading.Lock()  # 锁对象，确保在多线程环境中线程安全的输出

    def __init__(self, shared_list, pattern, thread_count):
        self.shared_list = shared_list  # 设置共享的链表对象
        self.pattern = pattern  # 设置要搜索的模式或关键字
        self.thread_count = thread_count  # 设置要创建的分析线程的数量
        self.threads = []  # 初始化一个空列表，用于存储创建的线程对象

    def start_threads(self):
        for _ in range(self.thread_count):  # 对于每一个要创建的线程
            thread = AnalysisThread(self.shared_list, self.pattern, len(self.threads)+1)  # 创建新的分析线程对象
            thread.start()  # 启动这个线程
            self.threads.append(thread)  # 将线程对象添加到线程列表中

    def join_threads(self):
        for thread in self.threads:  # 对于线程列表中的每一个线程
            thread.join()  # 等待这个线程完成


class EchoServer:
    def __init__(self, host, port, shared_list):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # 初始化TCP套接字
        self.server_socket.bind((host, port))  # 将套接字绑定到提供的主机和端口
        self.server_socket.listen(5)  # 开始监听连接，队列大小为5
        self.shared_list = shared_list  # 保存共享列表
        self.book_counter = 1  # 初始化书籍计数器

    def accept_client(self):
        conn, addr = self.server_socket.accept()  # 使用accept方法等待并接受客户端连接
        print(f"Connection from: {addr}")  # 打印客户端的地址信息
        handler = ClientHandler(conn, self.shared_list, self.book_counter)  # 创建一个ClientHandler实例
        threading.Thread(target=handler.run).start()  # 在新线程中启动客户端处理程序
        self.book_counter += 1  # 递增书籍计数器

    def run(self):
        print("Server is listening...")  # 打印出服务器监听的消息
        while True:
            self.accept_client()  # 持续接受新的客户端连接


if __name__ == "__main__":
    parser = argparse.ArgumentParser()  # 创建一个新的命令行参数解析器对象
    parser.add_argument("-l", "--listen", type=int, required=True, help="Listening port")  # 添加需要的命令行参数 -l/--listen
    parser.add_argument("-p", "--pattern", type=str, required=True, help="Search pattern")  # 添加需要的命令行参数 -p/--pattern
    args = parser.parse_args()  # 解析命令行参数

    shared_list = SharedList()  # 创建一个共享的链表对象
    server = EchoServer('localhost', args.listen, shared_list)  # 初始化EchoServer对象

    Number_of_Thread = 4  # 定义要启动的分析线程的数量
    analysis_handler = AnalysisThreadHandler(shared_list, args.pattern, Number_of_Thread)  # 创建AnalysisThreadHandler对象
    analysis_handler.start_threads()  # 启动分析线程
    print(f"{Number_of_Thread} analysis threads are runnning...\n")  # 打印分析线程已开始运行的消息
    print(f"Echo server started on port: {args.listen}... \n")  # 打印服务器已经开始监听的消息
    server.run()  # 开始运行服务器


