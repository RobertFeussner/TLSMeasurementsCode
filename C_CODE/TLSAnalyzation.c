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
		printf("\tThis function analyzes the TLS connection to a given url.\n");
		printf("\tInput parameters:\n\t\tURL\t- e.g. google.com\n\t\tIP Version\t- 4 or 6\n\t\tTLS Version\t- 1,2 or 3\n");
		printf("\tOptional input:\n\t\tCipher type\t- 1,2 or 3. If one uses a TLS1.3 specific cipher, 3 must be chosen, else 1 or 2\n\t\tCipher\t- Cipher, e.g. AES128-SHA256\n");
		printf("\tOutput:\n");
		printf("\t\tURL;IP_VERSION;TLS_VERSION;CIPHER;ERROR;ERROR_STRING;NAMELOOKUP_TIME;CONNECT_TIME;APPCONNECT_TIME;TOTAL_TIME\n");
		printf("\tExample:\n");
		printf("\t\t./TLSAnalyzation google.com 4 3 2 AES128-SHA256\n");
		exit(EXIT_SUCCESS);
	}
	//First check for arguments and their initialization
	if(argc != 4 && argc != 6){
		fprintf(stderr, "Wrong use of arguments!\nUse the -h flag for help.");
		exit(EXIT_FAILURE);
	}
	char *url = malloc(strlen(argv[1])+1);
	strcpy (url, argv[1]);
	int ipVersion = atoi(argv[2]);
	int tlsVersion = atoi(argv[3]);
	
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
	}else if(tlsVersion == 1){
		curl_easy_setopt(curl, CURLOPT_SSLVERSION, CURL_SSLVERSION_TLSv1_1 | CURL_SSLVERSION_MAX_TLSv1_1);
	}else{
		fprintf(stderr, "TLS Version invalid. Please choose 1,2 or 3.\n");
		curl_easy_cleanup(curl);
		curl_global_cleanup();
		return (EXIT_FAILURE);
	}
	
	
	printf("%s;%d;%d;", url, ipVersion, tlsVersion);
	
	
	//ALLOWED CIPHERS
	if(argc == 6){
		int cipherType = atoi(argv[4]);
		char *cipher = malloc(strlen(argv[5])+1);
		strcpy (cipher, argv[5]);
		printf("%s;",cipher);
		if(cipherType == 3){
			curl_easy_setopt(curl, CURLOPT_TLS13_CIPHERS, cipher);
		}else if(cipherType == 1 || cipherType == 2){
			curl_easy_setopt(curl, CURLOPT_SSL_CIPHER_LIST, cipher);
		}else{
			fprintf(stderr, "TLS Cipher Type not specified. Please choose 3 for TLS1.3 Cipher and 1 or 2 for other ciphers.\n");
			curl_easy_cleanup(curl);
			curl_global_cleanup();
			return (EXIT_FAILURE);
		}
	}else{
		printf("No cipher specified;");
	}
	
	//Definition of the rest of connection options
	curl_easy_setopt(curl, CURLOPT_URL, url);
	curl_easy_setopt(curl, CURLOPT_DEFAULT_PROTOCOL, "https");
	curl_easy_setopt(curl, CURLOPT_PORT, 443);
	curl_easy_setopt(curl, CURLOPT_SSL_VERIFYPEER, 1L);
	curl_easy_setopt(curl, CURLOPT_TIMEOUT, 20L);
	curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_data);
	
	//Execution and presentation of result
	response = curl_easy_perform(curl);
	printf("%d;%s;", response, curl_easy_strerror(response));
	
	//Write the different times in ms, errors considered 0
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
	curl_global_cleanup();
	return (EXIT_SUCCESS);
}