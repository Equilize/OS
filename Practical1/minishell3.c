/*********************************************************************
   Program  : miniShell                   Version    : 1.3
 --------------------------------------------------------------------
   skeleton code for linix/unix/minix command line interpreter
 --------------------------------------------------------------------
   File			: minishell.c
   Compiler/System	: gcc/linux

********************************************************************/
/*
- Put commands ended by an "&" into background mode and report when they finish
- Properly interpret the shell cd command
- include an appropriate perror statement after each and every system call
- Fix the minishell so that if the exec system call fails, the child process is correctly terminated
*/

#include <sys/types.h>
#include <sys/wait.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <stdlib.h>
#include <signal.h>

#define NV 20			/* max number of command tokens */
#define NL 100			/* input buffer size */
#define NBG 100
char            line[NL];	/* command input buffer */
char *bg_cmds[NBG];
pid_t bg_pids[NBG];

/*
	shell prompt
 */

void prompt(void)
{
  //fprintf(stdout, "\n msh> ");
  fflush(stdout);

}


int main(int argk, char *argv[], char *envp[])
/* argk - number of arguments */
/* argv - argument vector from command line */
/* envp - environment pointer */

{
  int             frkRtnVal;	/* value returned by fork sys call */
  int             wpid;		/* value returned by wait */
  char           *v[NV];	/* array of pointers to command line tokens */
  char           *sep = " \t\n";/* command line token separators    */
  int             i;		/* parse index */

  int bg_count = 0;
  /* prompt for and process one command line at a time  */

  while (1) {			/* do Forever */
    prompt();
    fgets(line, NL, stdin);
    fflush(stdin);

    if (feof(stdin)) {		/* non-zero on EOF  */

      // fprintf(stderr, "EOF pid %d feof %d ferror %d\n", getpid(),
	    //   feof(stdin), ferror(stdin));
      exit(0);
    }
    if (line[0] == '#' || line[0] == '\n' || line[0] == '\000')
      continue;			/* to prompt */

    v[0] = strtok(line, sep);
    for (i = 1; i < NV; i++) {
      v[i] = strtok(NULL, sep);
      if (v[i] == NULL) {
	      break;
      }
    }
    /* assert i is number of tokens + 1 */

    //cd
    if (strcmp(v[0], "cd") == 0) {
      if (chdir(v[1]) != 0) {
        perror("cd error");
      }
      continue;
    }

    /* fork a child process to exec the command in v[0] */

    switch (frkRtnVal = fork()) {
    case -1:			/* fork returns error to parent process */
      {
        perror("Fork error");
	      break;
      }
    case 0:			/* code executed only by child process */
      {
	      if(execvp(v[0], v) == -1) {
          perror("execvp error");
          exit(1);
        }
        break;
      }
    default:			/* code executed only by parent process */
      if(strcmp(v[i-1], "&") == 0) {
        v[i-1] = NULL;
        bg_count++;
        printf("[%d] %d\n", bg_count, frkRtnVal);
      } else {       
        wpid = wait(0);
        //printf("%s done \n", v[0]);
      }
    }				/* switch */
    int status;
    for(i = 1; i<= bg_count; i++) {
      wpid = waitpid(bg_pids[i], &status, WNOHANG);
        if(wpid > 0) {
          printf("[%d] + Done %s\n", i , bg_cmds[i]);
          free(bg_cmds[i]);
          bg_cmds[i] = bg_cmds[bg_count];
          bg_pids[i] = bg_pids[bg_count];
          bg_count--;
        }

    }
  }				/* while */
}				/* main */