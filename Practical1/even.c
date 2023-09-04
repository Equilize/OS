/*
Takes input parameter n from command line and prints the first 'n' even numbers
Place sleep(5) after every print statement
Compile check

SIGHUP & SIGINT signal
HUP signal --> print 'Ouch' and continue
INT signal --> print 'Yeah' and continue
*/

#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>
#include <signal.h>

void sig_handler_HUP(int signum){ //Handles HUP signal
    write(STDOUT_FILENO, "Ouch!\n",6);
}

void sig_handler_INT(int signum){ //Handles INT signal
    write(STDOUT_FILENO, "Yeah!\n",6);
}

int main(int argc, char* argv[]) {
    if(argc != 2){ //Handles error if input argument number exceeds expected
        write(STDERR_FILENO, "One number only!\n",15);
        return 1;
    }

    int n = atoi(argv[1]);

    if(n <= 0) { //Handles error if argument value is not expected
        write(STDERR_FILENO,"Enter a positive integer!\n",23);
        return 1;
    }
    
    signal(SIGHUP, sig_handler_HUP);
    signal(SIGINT, sig_handler_INT);

    for(int i = 0; n > 0; i++) { 
        if (i % 2 == 0){ 
            printf("%d\n", i);
            n--;
            sleep(5);
        }
    /*Loop n as count, decrement whenever a even number is printed*/
    }
    return 0;
}
