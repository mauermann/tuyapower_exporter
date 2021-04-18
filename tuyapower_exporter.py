from prometheus_client import start_http_server, Gauge
import json
import tuyapower
import time
import os
import socket
from hashlib import md5
from Crypto.Cipher import AES

DEBUG = False
PORT = 9067
CONFIG = "devices.json"

# env variables
DEBUG = os.getenv("DEBUG", DEBUG)
PORT = int(os.getenv("PORT", PORT))
CONFIG = os.getenv("CONFIG", CONFIG)

# UDP packet payload decryption - credit to tuya-convert
pad = lambda s: s + (16 - len(s) % 16) * chr(16 - len(s) % 16)
unpad = lambda s: s[:-ord(s[len(s) - 1:])]
encrypt = lambda msg, key: AES.new(key, AES.MODE_ECB).encrypt(pad(msg).encode())
decrypt = lambda msg, key: unpad(AES.new(key, AES.MODE_ECB).decrypt(msg)).decode()
udpkey = md5(b"yGAdlopoPVldABfn").digest()
decrypt_udp = lambda msg: decrypt(msg, udpkey)


if __name__ == '__main__':

    # load configured devices
    with open(CONFIG, "r") as f:
    	config = json.load(f)
    print("loaded %d devices from %s" % (len(config), CONFIG))

    devices = {}
    for d in config:
        devices[d['id']] = d
        devices[d['id']]['lastseen'] = False

    # initialize metrics
    labels = ['device_name', 'device_id', 'device_ip', 'device_version']
    gs = Gauge('tuyapower_state', 'Tuya plug/socket state', labels)
    gp = Gauge('tuyapower_power', 'Tuya plug/socket power (W)', labels)
    ga = Gauge('tuyapower_current', 'Tuya plug/socket current (A)', labels)
    gv = Gauge('tuyapower_voltage', 'Tuya plug/socket voltage (V)', labels)

    start_http_server(PORT)
    print("metrics available on port %d" % PORT)

    # Enable UDP listening broadcasting mode on UDP port 6666 - 3.1 Devices
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    client.bind(("", 6666)) # Tuya 3.1 UDP Port
    client.settimeout(0)
    # Enable UDP listening broadcasting mode on encrypted UDP port 6667 - 3.3 Devices
    clients = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    clients.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    clients.bind(("", 6667)) # Tuya 3.3 encrypted UDP Port
    clients.settimeout(0)


    while True:

        data = False

        # read from socket for 3.1 devices
        try:
            data, addr = client.recvfrom(4048)
        except socket.error:
            pass
        # read from socket for 3.3 devices
        try:
            data, addr = clients.recvfrom(4048)
        except socket.error:
            pass

        if not data:
            time.sleep(1)
            continue

        # decode data
        try:
            data = data[20:-8]
            try:
                data = decrypt_udp(data)
            except:
                data = data.decode()
            data = json.loads(data)
            if (DEBUG):
                print(data)
        except:
            print("*  Unexpected payload=%r\n", data)
            time.sleep(1)
            continue

        gwid = data['gwId']
        # skip devices that are not configured
        if not data['gwId'] in devices:
            print("ignoring unconfigured device %s at %s" % (data['gwId'], data['ip']))
            continue

        if not devices[gwid]['lastseen']:
            print("discovered device %s (%s) at %s" % (gwid, devices[gwid]['name'], data['ip']))

        devices[gwid]['ip'] = data['ip']
        devices[gwid]['version'] = data['version']

        # poll device and set metrics if successful
        (on, w, mA, V, err) = tuyapower.deviceInfo(gwid, data['ip'], devices[gwid]['key'], data['version'])
        if(err == "OK"):
            if (DEBUG):
                print("%s (%s) - %s - Power: %sW, %smA, %sV"%(gwid, devices[gwid]['name'], on, w, mA, V))

            label_values = [devices[gwid]['name'], gwid, data['ip'], data['version']]
            gs.labels(*label_values).set(on)
            gp.labels(*label_values).set(w)
            ga.labels(*label_values).set(mA / 1000)
            gv.labels(*label_values).set(V)

            devices[gwid]['lastseen'] = time.time()
        else:
            print("Error: %s %s. Wrong device key?" % (err, gwid))

        # cleanup metrics if device offline for more than 30 sec
        for d in devices:
            if devices[d]['lastseen'] and devices[d]['lastseen'] < time.time() - 30:
                print("device %s (%s) gone offline" % (devices[d]['id'], devices[d]['name']))
                devices[d]['lastseen'] = False

                label_values = [devices[d]['name'], d, devices[d]['ip'], devices[d]['version']]
                gs.remove(*label_values)
                gp.remove(*label_values)
                ga.remove(*label_values)
                gv.remove(*label_values)
