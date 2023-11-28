********************************************************************************************************
Use Instruction
********************************************************************************************************

When running on UNIX system, open multiple terminals. One for server, multiple for client. 
(Not on Windows)

Ensure server side is runnning first before sending books on the client side

Server side terminal command

python assignment3.py -l [port-number] -p "[search-pattern]"

Client side terminal command

nc localhost [port-number] -i 1 < [bookname.txt]

To hang any running process --> ^z

bookTitle is variable used to save the book title of the saved books, and in the output message of analysis thread, it is represented as the index of the book being saved. Eg. Book 1