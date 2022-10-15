import os
import socket
import requests
import time
import subprocess
from datetime import datetime
from dotenv import dotenv_values

# Load the .env file
config = dotenv_values(".env")


# Gets the IPV4 address of the active network adapter.
def get_network_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # 8.8.8.8 is the primary DNS server for Google DNS. It is assumed that this DNS server will always be up.
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip


# Gets the active network interface name.
def get_active_network_interface_name():
    return subprocess.run('ip route | grep default | sed -e "s/^.*dev.//" -e "s/.proto.*//"', shell=True, stdout=subprocess.PIPE).stdout.decode('utf-8').split(" ")[0]

interfaceName = get_active_network_interface_name(get_network_ip_address()).strip()
print("Selected interface: {}".format(interfaceName))

# Create pcaps folder
try:
    os.mkdir("pcaps")
except:
    print("pcaps folder exists")


def check_ping(hostname):
    response = os.system("ping -c 1 {} > /dev/null 2>&1".format(hostname))
    if response == 0:
        return 1
    else:
        return 0
        
# Check for network on startup.
if check_ping("4.2.2.2") == 0:
    print("icmp disabled for this machine or 4.2.2.2 is down, exiting.")
    quit()

def doHook():
    try:
        return requests.post(config["DISCORD_WEBHOOKURL"],  {"content": "Was not able to check ping on {}".format(socket.gethostname()), "username": "CheckDos"}, timeout=5)
    except:
        print("webhook failed")

def record():
    # Fuck, DDoS
    now = datetime.now().strftime("%d-%m-%Y---%H-%M-%S")
    print("DDoS Detected on {}".format(now))

    # Keep the last 4 pcaps
    for filename in sorted(os.listdir("pcaps"))[:-3]:
        filename_relPath = os.path.join("pcaps", filename)
        os.remove(filename_relPath)

    # Send the webhook if we already can.
    response = doHook()

    # Run the packet capture
    filter = ""
    if config["FILTER_EXTERNAL_IP"] == "True":
        ip = get_network_ip_address()
        filter = "'dst {} or src {}'".format(ip, ip)
    # -Q in: only capture incoming traffic -Z root is required for writing pcap files, -i sets the interface name
    os.system("timeout {} tcpdump -Q in -Z root -i {} -w pcaps/ddos-{}.pcap {}".format(config["CAPTURE_DURATION"], interfaceName, now, filter)) #  and write to file

    # Retry sending webhook.
    if response is None or response.status_code != 204:
        response = doHook()

    # sleep 10 minutes, so we don't capture again within that timeframe and try to send the webhook one last time
    time.sleep(600)
    if response is None or response.status_code != 204:
        response = doHook()
    
    # Do not bother sending the file for analysis if we are still under attack
    # Optional
    if response is not None and response.status_code == 204 and config["ANALYSIS_ENABLED"] == "True":
        os.system('curl -X POST -H "key:{}" -F "filename=capture" -F "file=@/srv/checkdos/checkdos/pcaps/ddos-{}.pcap" {}'.format(config["ANALYSIS_KEY"], now, config["ANALYSIS_HOST"]))


# Main Loop
while True:
    # 1 = online, 0 = offline
    status = check_ping("4.2.2.2")
    if status == 0:
        time.sleep(15)
        # Retry on another ip, network can be dodgy
        status = check_ping("1.1.1.1")
        if status == 0:
            # Calculate PPS
            startCount = int(subprocess.check_output("cat /sys/class/net/{}/statistics/rx_packets".format(interfaceName), shell=True))
            time.sleep(1)
            endCount = int(subprocess.check_output("cat /sys/class/net/{}/statistics/rx_packets".format(interfaceName), shell=True))

            pps = (endCount - startCount)
            print("{} packets per second".format(pps))
            if pps > 100:
                record()
            else:
                requests.post(config["DISCORD_WEBHOOKURL"],  {"content": "Was not able to check ping on {}. But pps {} is below threshold 100/s".format(socket.gethostname(), pps), "username": "CheckDos"}, timeout=5)

    time.sleep(10)
