import java.io.BufferedOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.net.ServerSocket;
import java.net.Socket;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.concurrent.LinkedBlockingQueue;

public class Server{
    public static void run(int port, String pattern, int interval) throws Exception {
        ServerSocket serverSocket = new ServerSocket(port);
        System.out.println("server started at port " + port);
        ShareList list = new ShareList();
        int bookId = 1;


        // create 5 Analyser threads
        HashMap<String, Integer> frequency = new HashMap<>();
        LinkedBlockingQueue<Integer> queue = new LinkedBlockingQueue<>();

        for(int i = 0; i < 5; i++) {
            Analyser a = new Analyser(list, pattern, frequency, queue);
            a.setDaemon(true);
            a.start();
        }

        // create 1 producer thread, 
        // Put a number into the queue every once in a while so that only one of multiple analysts can be started.
        Producer p = new Producer(queue, interval);
        p.setDaemon(true);
        p.start();

        try {

            while(true) {
                Socket clientSocket = serverSocket.accept();
                System.out.println("new client!");
                Handler t = new Handler(clientSocket, list, bookId);
                t.setDaemon(true);
                t.start();
                bookId++;
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
        serverSocket.close();
    }
}


class Handler extends Thread {
    Socket client;
    InputStream input;
    BufferedOutputStream output;
    ShareList list;
    String bookName;
    public static String getBookName(int id) {
        if (id < 10) {
            return "book_0" + id + ".txt";
        } else {
            return "book_" + id + ".txt";
        }
    }


    public Handler(Socket s, ShareList l, int bookID){
        this.client = s;
        this.list = l;
        this.bookName = getBookName(bookID);
    }

    public void handle() throws Exception {
        input = client.getInputStream();
        output = new BufferedOutputStream(client.getOutputStream());

        byte buffer[] = new byte[1024];
        int len = -1;

        int sumLen = 0;
        while((len = input.read(buffer)) != -1) {
            // String dataRecv = new String(buffer);
            // if (bookName == null) {
            //     String[] dataSplit = dataRecv.split("\n", 2);
            //     bookName = dataSplit[0];
            //     // dataRecv = dataSplit[1];
            // }
            sumLen += len;
            this.list.addNode(bookName, buffer.clone(), len);
            System.out.println("receive book: " + bookName + " len: " + len);
        }
        System.out.println("client exit. data received: " + sumLen);

        // wirte to file
        String prefix = "";
        // prefix = "data/";
        FileOutputStream of = new FileOutputStream(new File(prefix + bookName));
        ListNode node = list.getFirstNode(bookName);
        while(node!=null) {
            of.write(node.data, 0, node.dataLength);
            node = node.book_next;
        }
        of.flush();
        of.close();
    }


    @Override
    public void run() {
        try {
            handle();
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}


class Analyser extends Thread {
    ShareList list;
    String pattern;
    HashMap<String, Integer> frequency;
    LinkedBlockingQueue<Integer> q;

    public Analyser(ShareList list, String pattern, HashMap<String, Integer> frequency, LinkedBlockingQueue<Integer> q) {
        this.list = list;
        this.pattern = pattern;
        this.frequency = frequency;
        this.q = q;
    }


    public void handle() throws Exception {
        q.take();
        // update frequency
        ListNode node = list.listHead;
        while(node != null) {
            if (node.freqLog == true) {
                node = node.next;
                continue;
            }

            if (!frequency.containsKey(node.bookName)) {
                frequency.put(node.bookName, 0);
            }

            // search in this part of data
            String data = new String(node.data);
            int count = data.split(pattern).length-1 + frequency.get(node.bookName);
            frequency.put(node.bookName, count);
            node = node.next;
        }

        // print frequency
        System.out.println("Frequency of " + pattern);
        
        ArrayList<BookFreq> datas =new ArrayList<>();
        for(String k: frequency.keySet()) {
            datas.add(new BookFreq(k, frequency.get(k)));
        }

        Collections.sort(datas);
        Collections.reverse(datas);
        System.out.println("###############");
        System.out.println("Analyser Thread: ");
        for(int i = 0; i < datas.size(); i++) {
            BookFreq b = datas.get(i);
            System.out.println("" + (i+1) + ". " + b.bookName + " freq:" + b.count);
        }
        System.out.println("###############");
    }


    @Override
    public void run() {
        try {
            while(true) {
                handle();
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}


// data class
class BookFreq implements Comparable{
    public String bookName;
    public int count;

    @Override
    public int compareTo(Object arg0) {
        BookFreq b2 = (BookFreq)arg0;
        return this.count - b2.count;
    }

    public BookFreq(String bookName, int count) {
        this.bookName = bookName;
        this.count = count;
    }
}

class Producer extends Thread {
    public LinkedBlockingQueue<Integer> q;
    int interval;
    public Producer(LinkedBlockingQueue<Integer> q, int interval) {
        this.q = q;
        this.interval = interval;
    }

    @Override
    public void run() {
        try {
            while(true) {
                Thread.sleep(this.interval*1000);
                q.put(0);
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}