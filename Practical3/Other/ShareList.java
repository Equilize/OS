import java.util.HashMap;

public class ShareList {
    public ListNode listHead;
    public HashMap<String, ListNode> bookLastNode;

    public ShareList() {
        listHead = null;
        bookLastNode = new HashMap<>();
    }

    public void addNode(String bookName, byte[] data, int dataLength) {
        synchronized(this) {
            ListNode node = new ListNode(bookName, data, dataLength);
            if (listHead == null) {
                listHead = node;
            } else {

                // insert into the books's last node
                if (bookLastNode.containsKey(bookName)) {
                    ListNode lastNode = bookLastNode.get(bookName);
                    lastNode.book_next = node;
                }

                // insert into tail
                ListNode tail = this.listHead;
                while(tail.next != null) {
                    tail = tail.next;
                }
                tail.next = node;
            }

            bookLastNode.put(bookName, node);
        }
    }


    public ListNode getFirstNode(String bookName) {
        ListNode node = this.listHead;
        if (this.listHead == null) {
            return null;
        }
        while(node!= null) {
            if (node.bookName.equals(bookName)) {
                return node;
            }
            node = node.next;
        }
        return null;
    }
}
