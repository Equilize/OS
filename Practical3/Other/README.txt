Compile:
    javac *.java

Run:
    java assignment3 -l <port> -p <pattern> -i <interval>

<port>    : the port that server will listen on
<pattern> : the pattern to report by analyser
<interval>: the interval between each report

This project starts 5 analysis threads and controls the thread's access to resources through a blockingqueue.