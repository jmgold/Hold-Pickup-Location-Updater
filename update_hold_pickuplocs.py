#Jeremy Goldstein
#Minuteman Library Network

#Script to batch change the pickup location for all holds with a given pickup location
#designed for cases where a location is forced to close and holds are made available at a neighboring location
#Fails for cases where a patron has multiple holds on a single bib record

import requests
import json
import configparser
from base64 import b64encode
import psycopg2

def get_token():
    # config api    
    config = configparser.ConfigParser()
    config.read('api_info.ini')
    base_url = config['api']['base_url']
    client_key = config['api']['client_key']
    client_secret = config['api']['client_secret']
    auth_string = b64encode((client_key + ':' + client_secret).encode('ascii')).decode('utf-8')
    header = {}
    header["authorization"] = 'Basic ' + auth_string
    header["Content-Type"] = 'application/x-www-form-urlencoded'
    body = {"grant_type": "client_credentials"}
    url = base_url + '/token'
    response = requests.post(url, data=json.dumps(body), headers=header)
    json_response = json.loads(response.text)
    token = json_response["access_token"]
    return token

def mod_hold(hold_id,is_frozen,new_location):
    config = configparser.ConfigParser()
    config.read('api_info.ini')
    token = get_token()
    url = config['api']['base_url'] + "/patrons/holds/" + hold_id
    header = {"Authorization": "Bearer " + token, "Content-Type": "application/json;charset=UTF-8"}
    payload = {"pickupLocation" : new_location, "freeze": is_frozen}
    request = requests.put(url, data=json.dumps(payload), headers = header)
    
def main():
    config = configparser.ConfigParser()
    config.read('api_info.ini')
    old_location = input("Enter location code to search, or type \'q\' to quit.\n")
    new_location = input("enter location code you wish to change to.\n")
    while old_location != 'q':
        if not old_location.endswith('z'):
            print('Invalid location code entered, please try again')
            break
        if not new_location.endswith('z'):
            print('Invalid location code entered, please try again')
            break
        confirm = input("This will change holds with location " + old_location + " to " + new_location + ".  Do you wish to proceed?  type \'y\' to continue.\n")
        if not confirm == 'y':
            print('\nThis program will now quit.  Goodbye.')
            break
        query = "select id, is_frozen from sierra_view.hold where pickup_location_code = '" + old_location
        #Connecting to Sierra PostgreSQL database
        conn = psycopg2.connect("dbname='iii' user='" + config['api']['sql_user'] + "' host='" + config['api']['sql_host'] + "' port='1032' password='" + config['api']['sql_pass'] + "' sslmode='require'")

        #Opening a session and querying the database for weekly new items
        cursor = conn.cursor()
        cursor.execute(query)
        #For now, just storing the data in a variable. We'll use it later.
        rows = cursor.fetchall()
        conn.close()
        for hold_id, is_frozen in rows:
            print("hold id: " + str(hold_id))
            print("is_frozen: " + str(is_frozen))
            mod_hold(str(hold_id),is_frozen,new_location)
            
        old_location = input("\nEnter another location code, or press \'q\' to quit.\n")
        
    print("\nThis program will now quit.  Goodbye.")
    
   
                    
main()

