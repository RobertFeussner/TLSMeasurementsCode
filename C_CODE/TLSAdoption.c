#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <curl/curl.h>

size_t write_data(char *buffer, size_t size, size_t nmemb, void *userp)
{
    /*Since we are not interested in the response just do nothing here.*/
    return size * nmemb;
}

int main(int argc, char* argv[]) 
{
	//First check for arguments and their initialization
	if(argc != 2){
		fprintf(stderr, "Wrong use of arguments!\n");
		exit(EXIT_FAILURE);
	}
	char *url = malloc(strlen(argv[1])+1);
	strcpy (url, argv[1]);
	
	printf("%s",url);
	
	//Initialization of curl
	curl_global_init(CURL_GLOBAL_DEFAULT);
	CURLcode response;
	/*
	//With TLS1.1
	for(int i=0; i<6; i++){
                CURL *curl;
                curl = curl_easy_init();
                if(i < 3){
                        curl_easy_setopt(curl, CURLOPT_IPRESOLVE, CURL_IPRESOLVE_V4);
                }else{
                        curl_easy_setopt(curl, CURLOPT_IPRESOLVE, CURL_IPRESOLVE_V6);
                        curl_easy_setopt(curl, CURLOPT_NOPROXY, url);
                }
                if(i % 3 == 0){
                        curl_easy_setopt(curl, CURLOPT_SSLVERSION, CURL_SSLVERSION_TLSv1_3 | CURL_SSLVERSION_MAX_TLSv1_3);
                }else if(i % 3 == 1){
                        curl_easy_setopt(curl, CURLOPT_SSLVERSION, CURL_SSLVERSION_TLSv1_2 | CURL_SSLVERSION_MAX_TLSv1_2);
                }else{
                        curl_easy_setopt(curl, CURLOPT_SSLVERSION, CURL_SSLVERSION_TLSv1_1 | CURL_SSLVERSION_MAX_TLSv1_1);
                }
	*/
	//Result "WEBSITE;IPV4_TLS13;IPV4_TLS13_LONG;IPV4_TLS12;IPV4_TLS12_LONG;IPV6_TLS13;IPV6_TLS13_LONG;IPV6_TLS12;IPV6_TLS12_LONG"
	//For each version the code and the String
	for(int i=0; i<4; i++){
		CURL *curl;
		curl = curl_easy_init();
		if(i < 2){
			curl_easy_setopt(curl, CURLOPT_IPRESOLVE, CURL_IPRESOLVE_V4);
		}else{
			curl_easy_setopt(curl, CURLOPT_IPRESOLVE, CURL_IPRESOLVE_V6);
			//With the proxy, there is no IPv6 host resolution possible. Is turned off here:
			curl_easy_setopt(curl, CURLOPT_NOPROXY, url);
		}
		if(i % 2 == 0){
			curl_easy_setopt(curl, CURLOPT_SSLVERSION, CURL_SSLVERSION_TLSv1_3 | CURL_SSLVERSION_MAX_TLSv1_3);
		}else{
			curl_easy_setopt(curl, CURLOPT_SSLVERSION, CURL_SSLVERSION_TLSv1_2 | CURL_SSLVERSION_MAX_TLSv1_2);
		}
		curl_easy_setopt(curl, CURLOPT_URL, url);
		curl_easy_setopt(curl, CURLOPT_DEFAULT_PROTOCOL, "https");
		curl_easy_setopt(curl, CURLOPT_PORT, 443);
		curl_easy_setopt(curl, CURLOPT_SSL_VERIFYPEER, 1L);
		curl_easy_setopt(curl, CURLOPT_TIMEOUT, 15L);
		curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_data);
		
		response = curl_easy_perform(curl);
		if(response == CURLE_OPERATION_TIMEDOUT){
			for(int j=i; j<4; j++){
				printf(";%d", response);
			}
			break;
		}
		printf(";%d", response);
		curl_easy_cleanup(curl);
	}
	printf("\n");
	curl_global_cleanup();
	return (EXIT_SUCCESS);
}