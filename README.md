# checkDos
Internal tool to automatically capture ddos captures that bypass mitigation.
Continuusly checks the network connectivity and starts capturing if the network is down.



## Analysis
The checkdos tool supports automatically sending pcaps off for analysis.
This analysis tool will be open-sourced later if there is any demand. It could use quite a bit of clean-up.


## Setup
This program will need some tuning for your environment.
To start, copy the `.env.example` to `.env` and fill in your details.
A checkdos.service file is provided but you might have to change some paths for it to work on your system.