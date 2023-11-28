public class ListNode {
    public String bookName;
    public byte[] data;
    public int dataLength;
    public ListNode next;
    public ListNode book_next;
    public boolean freqLog = false;

    public ListNode(String bookname, byte[] data, ListNode next, ListNode book_next) {
        this.bookName = bookname;
        this.data = data;
        this.next = next;
        this.book_next = book_next;
    }

    public ListNode(String bookname, byte[] data, int dataLength) {
        this.bookName = bookname;
        this.data = data;
        this.dataLength = dataLength;
        this.next = null;
        this.book_next = null;
    }
}
