#A python script for updating a the A records on list of domains on a cloudflare to support DDNS.

`ddns.py` is intended to be run as a service at intervals to check for changes of the IP address of the server the service is running on.  If the IP address changes, the correspoding A records in Cloudflare will be updated.

The only user inputs are:

1) `API_TOKEN` - the Cloudflare API token - Created on Cloudfare web interface under My proifile -> API Tokens -> User API Tokens (versus API Keys)


2) Zone IDs - 32 character identfiers - Found in Main Menu -> Websites -> <Specific Website Button> then scroll down the right hand column.

`ddns.py` will check for a cache file, `IP_Address_Cache.pkl`, containing the A record IP addresses currently set on Cloudflare and their corresponding Cloudflare record IDs.  If the file is absent or a new site has been added, `ddns.py` will query Cloudflare for the new information.  Using the cache eliminates unneeded queries.  If a site / recoard needs to be deleted, delete the cache file and remove the corresponding Zone ID from the `zone_ids` dictionary.  The cache will be auto-populated the next time it runs.

If the reported IP address for the server does not match any of the cached values in the A record, the Cloudflare API call to update the DNS record will be performed.

To support automation of the script, I've created a systemd service and corresponding timer.  For details see the following two sections.

##Enabling initialization at boot (auto launch)

Edit values of `ExecStart` and `WorkingDirectory` in `ddns.service` to match your setup.

Copy `ddns.service` into `/etc/systemd/system` as root:

> sudo cp ddns.service /etc/systemd/system/ddns.service

Attempt to start the service using the following command:

> sudo systemctl start ddns.service

Stop it using following command:

> sudo systemctl stop ddns.service

To have it start automatically on reboot by using this command:

> sudo systemctl enable ddns.service

The systemctl command can also be used to restart the service or disable it



##Enabling a timer to restart the service at regular intervals

Note the file prefix for the timer must match the prefix for the service.  The timer is setup for running every 5 minutes.

Copy `ddns.timer` into `/etc/systemd/system` as root, for example:

> sudo cp ddns.timer /etc/systemd/system/ddns.timer

Once this has been copied, the timer needs to be enabled:

> sudo systemctl enable ddns.timer

Then the timer needs to be started:

> sudo systemctl start ddns.timer

Check status with:

> systemctl status ddns.service

Example status from working system:

> ● ddns.service - DDNS Client for Cloudflare
>      Loaded: loaded (/etc/systemd/system/ddns.service; disabled; vendor preset: enabled)
>      Active: inactive (dead) since Thu 2024-03-07 01:05:08 UTC; 48s ago
> TriggeredBy: ● ddns.timer
>     Process: 251334 ExecStart=/usr/bin/python3 -u ddns.py --serviceMode (code=exited, status=0/SUCCESS)
>    Main PID: 251334 (code=exited, status=0/SUCCESS)
> 
> Mar 07 01:05:08 odroid python3[251334]: 200
> Mar 07 01:05:08 odroid python3[251334]: <Response [200]>

##Cloudflare docs:


Query DNS records:

[https://developers.cloudflare.com/api/operations/dns-records-for-a-zone-list-dns-records]()

Set DNS records:

[https://developers.cloudflare.com/api/operations/dns-records-for-a-zone-update-dns-record
]()

Some code and concept lifted from:

[https://github.com/creimers/cloudflare-ddns]()

##Python & Package Revisions:

Python 3.8.10

##Testing:

###Python
The two Cloudfare interface calls are split and pretty easily isolated for testing; alhtough, they shouls just work.  The curl command in the comments of `ddns.py` is a simple method to test out your zone IDs and API Token.

###systemd service
Once both the service and timer are running `systemctl status ddns.service` provides commpact but useful feedback on the state of the service including the time since it was last run.  A simple metric to use when bringing up the service is to delete `IP_Address_Cache.pkl` as it will be regenerated if deleted every time the service is run.

###DNS propagation
It was acceptable and easisted for me to test the propagation by changing the DNS reecord through Cloudfare's web portal to an incorrect value and watch for the creation of `IP_Address_Cache.pkl` or the roll over of the timer from `systemctl status ddns.service` to check to see if the service correctly updated the A record.

