#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <curl/curl.h>

int main(int argc, char* argv[]) 
{
	FILE *fptr;
	fptr = fopen("CURL_ERROR_CODES.csv","w");
	fprintf(fptr,"ERROR;ERROR_STRING\n");
	for(int i = 0; i <= 96; i++){
		fprintf(fptr,"%d;%s\n", i, curl_easy_strerror(i));
	}
	fclose(fptr);
	
}
