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
	if(argc == 2 && ((strcmp("-h", argv[1]) == 0) || (strcmp("--help", argv[1]) == 0))){
		printf("\tThis function records the time for a connection to a given url for TLS 1.3 or TLS 1.2 with a list of ciphers.\n");
		printf("\tInput parameters:\n\t\tURL\t- e.g. google.com\n\t\tIP version\t- 4 or 6\n");
		printf("\tOptional parameters:\n\t\tTLS Version\t- 2 or 3. (Default 3)\n");
		printf("\tOutput:\n");
		printf("\t\tWEBSITE;IP_VERSION;TLS_VERSION;CIPHER;ERROR;ERROR_STRING;NAMELOOKUP_TIME;CONNECT_TIME;APPCONNECT_TIME;TOTAL_TIME\n");
		exit(EXIT_SUCCESS);
	}
	//First check for arguments and their initialization
	if(argc != 3 && argc != 4){
		fprintf(stderr, "Wrong use of arguments!\n");
		exit(EXIT_FAILURE);
	}
	int tlsVersion;
	if(argc == 4){
		tlsVersion = atoi(argv[3]);
	}else{
		tlsVersion = 3;
	}
		
	char *url = malloc(strlen(argv[1])+1);
	strcpy (url, argv[1]);
	int ipVersion = atoi(argv[2]);
	
	#define NUMBER_OF_CIPHER 7
	#define NUMBER_OF_TLS13 5
	#define MAX_STRING_SIZE 40
	
	char ciphers[NUMBER_OF_CIPHER][MAX_STRING_SIZE] =
	{
		"TLS_AES_256_GCM_SHA384",
		"TLS_CHACHA20_POLY1305_SHA256",
		"TLS_AES_128_GCM_SHA256",
		"TLS_AES_128_CCM_8_SHA256",
		"TLS_AES_128_CCM_SHA256",
		//beginning here we have a different way of specifying the cipher:
		"AES128-SHA256",
		//NO Cipher for normal performance at the end
		"NO_CIPHER"
	};
	int start = 0;
	if(tlsVersion != 3){
		start = NUMBER_OF_TLS13;
	}
	
	for(int i = start;i < NUMBER_OF_CIPHER; i++){
		//Initialization of curl
		curl_global_init(CURL_GLOBAL_DEFAULT);
		CURL *curl;
		CURLcode response;
		curl = curl_easy_init();
		
		//IP Version
		if(ipVersion == 4){
			curl_easy_setopt(curl, CURLOPT_IPRESOLVE, CURL_IPRESOLVE_V4);
		}else if(ipVersion == 6){
			curl_easy_setopt(curl, CURLOPT_IPRESOLVE, CURL_IPRESOLVE_V6);
			//With the proxy, there is no IPv6 host resolution possible. Is turned off here:
			curl_easy_setopt(curl, CURLOPT_NOPROXY, url);
		}else{
			fprintf(stderr, "IP Version invalid. Please choose 4 or 6.\n");
			curl_easy_cleanup(curl);
			curl_global_cleanup();
			return (EXIT_FAILURE);
		}
		//TLS Version
		if(tlsVersion == 3){
			curl_easy_setopt(curl, CURLOPT_SSLVERSION, CURL_SSLVERSION_TLSv1_3 | CURL_SSLVERSION_MAX_TLSv1_3);
		}else if(tlsVersion == 2){
			curl_easy_setopt(curl, CURLOPT_SSLVERSION, CURL_SSLVERSION_TLSv1_2 | CURL_SSLVERSION_MAX_TLSv1_2);
		}else{
			fprintf(stderr, "TLS Version invalid. Please choose 1,2 or 3.\n");
			curl_easy_cleanup(curl);
			curl_global_cleanup();
			return (EXIT_FAILURE);
		}
		
		//ALLOWED CIPHERS
		if(i < NUMBER_OF_TLS13){
			curl_easy_setopt(curl, CURLOPT_TLS13_CIPHERS, ciphers[i]);
		}else if (i < (NUMBER_OF_CIPHER -1)){
			//Last Cipher: no specification of cipher needed
			curl_easy_setopt(curl, CURLOPT_SSL_CIPHER_LIST, ciphers[i]);
		}
		//Definition of the rest of connection options
		curl_easy_setopt(curl, CURLOPT_URL, url);
		curl_easy_setopt(curl, CURLOPT_DEFAULT_PROTOCOL, "https");
		curl_easy_setopt(curl, CURLOPT_PORT, 443);
		curl_easy_setopt(curl, CURLOPT_SSL_VERIFYPEER, 1L);
		curl_easy_setopt(curl, CURLOPT_TIMEOUT, 15L);
		curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_data);
		
		//Execution and presentation of result
		response = curl_easy_perform(curl);
		
		printf("%s;%d;%d;%s;%d;%s;", url, ipVersion, tlsVersion, ciphers[i], response, curl_easy_strerror(response));
		
		//Write the different times in ms, errors considered no entry
		double nameTime, connectTime, appconnectTime, totalTime;
		if(response == CURLE_OK){
			response = curl_easy_getinfo(curl, CURLINFO_NAMELOOKUP_TIME, &nameTime);
			if(response == CURLE_OK){
				printf("%.2f;", nameTime*1000.0);
			}else{
				printf(";");
			}
			
			response = curl_easy_getinfo(curl, CURLINFO_CONNECT_TIME, &connectTime);
			if(response == CURLE_OK){
				printf("%.2f;", connectTime*1000.0);
			}else{
				printf(";");
			}
			
			response = curl_easy_getinfo(curl, CURLINFO_APPCONNECT_TIME, &appconnectTime);
			if(response == CURLE_OK){
				printf("%.2f;", appconnectTime*1000.0);
			}else{
				printf(";");
			}
			
			response = curl_easy_getinfo(curl, CURLINFO_TOTAL_TIME, &totalTime);
			if(response == CURLE_OK){
				printf("%.2f\n", totalTime*1000.0);
			}else{
				printf("\n");
			}
			
		}else{
			printf(";;;\n");
		}	
		
		//Cleanup
		curl_easy_cleanup(curl);
	}
	curl_global_cleanup();
	return (EXIT_SUCCESS);
}