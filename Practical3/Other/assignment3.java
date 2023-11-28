public class assignment3 {
    public static void main(String[] args) throws Exception {
        int port = 12345;
        String pattern = null;
        int interval = 5;

        for (int i = 0; i < args.length; i++) {
            if (args[i].equals("-l") && i + 1 < args.length) {
                port = Integer.parseInt(args[i + 1]);
            } else if (args[i].equals("-p") && i + 1 < args.length) {
                pattern = args[i+1];
            } else if (args[i].equals("-i") && i+1 < args.length) {
                interval = Integer.parseInt(args[i+1]);
            }
        }

        Server.run(port, pattern, interval); 
    }
}