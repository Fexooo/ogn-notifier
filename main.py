import requests
from ogn.client import AprsClient
from ogn.parser import parse, AprsParseError
import os

telegram_token = os.getenv("TELEGRAM_TOKEN", "")
chat_id = os.getenv("CHAT_ID", "")

ids = os.getenv("OGN_IDS", "").split(",")
plates = os.getenv("OGN_PLATES", "").split(",")
id_map = dict(zip(ids, plates))

plane_meta = {id_: {"plate": label, "wasBelowThreshold": False} for id_, label in id_map.items()}

threshold_altitude = 1400

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    try:
        requests.post(url, data=payload, timeout=5)
    except Exception as e:
        print(f"Telegram Fehler: {e}")

def process_beacon(raw_message):
    if raw_message[0] == '#':
        print('Server Status: {}'.format(raw_message))
        return
 
    try:
        beacon = parse(raw_message)
        if(beacon["name"] in ids):
            print(plane_meta[beacon["name"]]["plate"] + ': ' + str(beacon["altitude"]) + ' altitude, position ' + str(beacon["latitude"]) + ' lat and ' + str(beacon["longitude"]) + ' long')
            if(float(beacon["altitude"]) < threshold_altitude):
                if(plane_meta[beacon["name"]]["wasBelowThreshold"] == False):
                    try:
                        send_telegram_message(plane_meta[beacon["name"]]["plate"] + " ist unter " + str(threshold_altitude) + "m! Höhe: " + str(beacon["altitude"]))
                        plane_meta[beacon["name"]]["wasBelowThreshold"] = True
                    except Exception:
                        print("ERROR WHEN SENDING MESSAGE")
            else:
                if(plane_meta[beacon["name"]]["wasBelowThreshold"] == True):
                    try:
                        send_telegram_message(plane_meta[beacon["name"]]["plate"] + " ist wieder über " + str(threshold_altitude) + "m! Höhe: " + str(beacon["altitude"]))
                        plane_meta[beacon["name"]]["wasBelowThreshold"] = False
                    except Exception:
                        print("ERROR WHEN SENDING MESSAGE")

            
    except AprsParseError as e:
        #print('Error, {}'.format(e.message))
        pass
 
client = AprsClient(aprs_user='N0CALL')
client.connect()

message_string = "Verbindung mit OGN hergestellt.\nFolgende Flugzeuge werden beobachtet:\n"
for plane in ids:
    message_string += plane + " => " + plane_meta[plane]["plate"] + "\n"

message_string += "Eingestellte Threshold Höhe: " + str(threshold_altitude)

send_telegram_message(message_string)
 
try:
    client.run(callback=process_beacon, autoreconnect=True)
except KeyboardInterrupt:
    print('\nStop ogn gateway')
    client.disconnect()