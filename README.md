# Tuya smart plug/socket exporter for Prometheus

This is a Prometheus exporter for [Tuya](https://en.tuya.com/) compatible WiFi Smart Plugs/Sockets. It uses the [tuyapower](https://github.com/jasonacox/tuyapower) python library.

Exposed metrics include state (on/off), power (W), current (mA), voltage (V).
```
# HELP tuyapower_state Tuya plug/socket state
# TYPE tuyapower_state gauge
tuyapower_state{device_id="bf0c....",device_ip="10.0.1.59",device_name="plug 2",device_version="3.3"} 1.0
tuyapower_state{device_id="bf82....",device_ip="10.0.1.61",device_name="plug 1",device_version="3.3"} 1.0
# HELP tuyapower_power Tuya plug/socket power (W)
# TYPE tuyapower_power gauge
tuyapower_power{device_id="bf0c....",device_ip="10.0.1.59",device_name="plug 2",device_version="3.3"} 49.4
tuyapower_power{device_id="bf82....",device_ip="10.0.1.61",device_name="plug 1",device_version="3.3"} 23.5
# HELP tuyapower_current Tuya plug/socket current (A)
# TYPE tuyapower_current gauge
tuyapower_current{device_id="bf0c....",device_ip="10.0.1.59",device_name="plug 2",device_version="3.3"} 0.255
tuyapower_current{device_id="bf82....",device_ip="10.0.1.61",device_name="plug 1",device_version="3.3"} 0.128
# HELP tuyapower_voltage Tuya plug/socket voltage (V)
# TYPE tuyapower_voltage gauge
tuyapower_voltage{device_id="bf0c....",device_ip="10.0.1.59",device_name="plug 2",device_version="3.3"} 230.3
tuyapower_voltage{device_id="bf82....",device_ip="10.0.1.61",device_name="plug 1",device_version="3.3"} 230.2
```

## Setup

This exporter reads a JSON file (devices.json) to get name, device ID and device key for a set of smart devices.
```
[
  {
    "name": "plug 1",
    "id": "bf82..................",
    "key": "f3d2............"
  },
  {
    "name": "plug 2",
    "id": "bf0c..................",
    "key": "6159............"
  }
]
```

### Device keys

**IMPORTANT!** For most newer devices **you need a device key**. However, they are not easily to get. For me it worked to install an old version of the Smart Life - Smart Living app on a rooted Android phone. You can watch an extensive video guide to retrieve the keys even with an Android emulator from [Mark Watt Tech on Youtube](https://youtu.be/YKvGYXw-_cE).

Short description:

1. Install [Smart Life - Smart Living 3.6.1](https://www.apkmirror.com/apk/volcano-technology-limited/smart-life-smart-living/smart-life-smart-living-3-6-1-release/smart-life-smart-living-3-6-1-android-apk-download/) on your **rooted** Android phone
2. Login with your Smart Life account. Your already paired devices should be visible. If not, you need to pair them.
3. Find the file named *preferences_global_keyeu<123xyz...>.xml* in /data/data/com.tuya.smartlife/shared_prefs/ and search for *localKey*

## Running
```
$ python3 tuyapower_exporter.py
loaded 2 devices
metrics available on port 9067
discovered device bf0c.... (plug 2) at 10.0.1.59
discovered device bf82.... (plug 1) at 10.0.1.61
...
```

### Docker

```
docker build -t tuyapower_exporter .

docker run --rm -p 9067:9067 -p 6666:6666/udp -p 6667:6667/udp tuyapower_exporter
```

You can also mount your devices.json in your container without rebuilding the image:
```
docker run --rm -v `pwd`/devices.json:/devices.json -p 9067:9067 -p 6666:6666/udp -p 6667:6667/udp tuyapower_exporter
```
