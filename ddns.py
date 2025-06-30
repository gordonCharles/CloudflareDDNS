'''
ddns.py is intended to be run as a service at intervals to check for changes of the IP address of the server
the service is running on.  If the IP address changes, the corresponding A records in Cloudflare will be updated.
The only user inputs are:

1) API_TOKEN - the Cloudflare API token - Created under My profile -> API Tokens -> User API Tokens (versus API Keys)

2) Zone IDs - 32 character identifiers - Found in Main Menu -> Websites -> <Specific Website Button> then scroll down
                                        the right hand column.

ddns.py will check for a cache file containing the A record IP addresses currently set on Cloudflare and their corresponding
Cloudflare record IDs.  If the file is absent or a new site has been added, ddns.py will query Cloudflare for the
new information.  Using the cache eliminates unneeded queries.  If a site / record needs to be deleted, delete the cache
file and remove the corresponding Zone ID from the zone_ids dictionary.  The cache will be auto-populated the next time 
it runs.

If the reported IP address for the server does not match any of the cached values in the A record, the Cloudflare API
call to update the DNS record will be performed.


Cloudflare docs:
================

Query DNS records:

https://developers.cloudflare.com/api/operations/dns-records-for-a-zone-list-dns-records

Set DNS records:

https://developers.cloudflare.com/api/operations/dns-records-for-a-zone-update-dns-record

Some code and concept lifted from:

https://github.com/creimers/cloudflare-ddns
'''

import json
import os
import requests
from pprint import pprint
import pickle

"""
curl call used to 

1) debug security API 
2) optionally get record ID in the response.  The record ID is required for changing the record; 
   however, the Cloudflare web portal does not display the record ID unless it has just been saved.
   The python implementation, automatically pulls the record IDs based on the the supplied zone IDs
   and stores the record IDs in a cache.

Note this does not match the curl call supplied in Cloudflare's API example:

https://developers.cloudflare.com/api/operations/dns-records-for-a-zone-list-dns-records

which appears to be incomplete and for a different method of authentication.  This method was taken from:

https://dash.cloudflare.com/profile/api-tokens


curl --request GET \
  --url https://api.cloudflare.com/client/v4/zones/398a6ba0a4d64bd818ec0f0f3ea7186e/dns_records \
  --header 'Content-Type: application/json' \
  --header 'Authorization: Bearer WrR-_5offZOlPL6GxssPN5rZiVQziYsr'
"""

API_TOKEN = 'Bearer WrR-_5offZOlPL6GxssPN5rZiVQziYsr'

zone_ids = {'yourdomain1.com' : '398a6ba0a4d64bd818ec0f0f3ea7186e', 
            'yourdomain2.net' : '507c755e637bc1dfd0c396be464f4f00', 
            'yourdomain3.net' : 'ba6d295e048e63ee7b4c866ca6eb2ccb'}

cached_ip_add = {}

for record_name, zone_id in zone_ids.items():
    cached_ip_add[record_name] = ('0.0.0.0', '00000000000000000000000000000000')

CACHE_FILENAME   = os.path.abspath((os.path.join(os.path.dirname(__file__), 'IP_Address_Cache.pkl')))

def saveCache():
    """
    stores the cached IP addresses and record IDs.  File should never be empty after first run.
    """
    with open(CACHE_FILENAME, 'wb') as CacheFile:
        pickle.dump(cached_ip_add, CacheFile)

def loadCache():
    """
    loads the cached IP addresses and record IDs.  If no cache file is present cache values created
    by querying Cloulfare, via get_ip_record() calls.
    """
    global cache_updated

    try: # Open NVM file if it exists otherwise use defaults
        with open(CACHE_FILENAME, 'rb') as CacheFile:
            tmp_cached_ip_add = pickle.load(CacheFile)
        for key in tmp_cached_ip_add:
            cached_ip_add[key] = tmp_cached_ip_add[key]
    except:
        for record_name, zone_id in zone_ids.items():
            current_ip_record = get_ip_record(record_name, zone_id)
            cached_ip_add[record_name] = current_ip_record
        cache_updated = True


def get_ip() -> str:
    """
    get the ip address of whoever executes the script
    """
    url = "http://icanhazip.com"
    response = requests.get(url)
    return str(response.text.strip())


def set_ip(current_ip, zone_id, record_id, record_name):
    """
    sets the ip in via cloudflare api
    """

    url = (
        "https://api.cloudflare.com/client/v4/zones/%(zone_id)s/dns_records/%(record_id)s"
        % {"zone_id": zone_id, "record_id": record_id}
    )

    headers = {
        "Authorization": API_TOKEN,
        "Content-Type": "application/json",
    }

    payload = {"type": "A", "name": record_name, "content": current_ip}
    response = requests.put(url, headers=headers, data=json.dumps(payload))
    print(response.status_code)
    pprint(response)


def get_ip_record(record_name, zone_id):
    """
    gets the current A record IP address and record ID in via cloudflare api
    """
    

    url = (
        "https://api.cloudflare.com/client/v4/zones/%(zone_id)s/dns_records/"
        % {"zone_id": zone_id}
    )

    headers = {
        "Authorization": API_TOKEN,
        "Content-Type": "application/json",
    }

    cloudflare_dns_respon = requests.get(url, headers=headers)
    '''
    if cloudflare_dns_respon.status_code == 200:
        print("Ok")
    else:
        print(cloudflare_dns_respon.status_code)    
'''
    dns_data = json.loads(cloudflare_dns_respon.text)
    for record in range(0, len(dns_data['result'])):
        if dns_data['result'][record]['type'] == 'A':
            return( (dns_data['result'][record]['content'], dns_data['result'][record]['id']) )


def main():
    global cache_updated

    cache_updated = False
    current_ip = get_ip()
    #print(current_ip)

    loadCache()
    for record_name, zone_id in zone_ids.items():
        if current_ip != cached_ip_add[record_name][0]:
            record_id = cached_ip_add[record_name][1]
            set_ip(current_ip, zone_id, record_id, record_name)
            cached_ip_add[record_name] = (current_ip, cached_ip_add[record_name][1])
            cache_updated = True

    if cache_updated == True:
        saveCache()

if __name__ == "__main__":
    main()
