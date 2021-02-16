# envDataSystem Network

User settings include host:port for the UIServer. This also needs to be set in the daq_server settings. In a dockerized environment, it will depend if the servers are on the same or different machines. 

### On different machines
This is the easiest/most straighforward case. Set the UI_HOSTNAME setting to be the same in both configurations. 

### On the same machine
Set the UI_HOSTNAME as you normally would but for the daq_server, specify "envdsys" as the UI_HOSTNAME. This will use the docker container network to communicate.

