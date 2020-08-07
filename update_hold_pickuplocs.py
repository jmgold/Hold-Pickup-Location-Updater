'''
Jeremy Goldstein
Minuteman Library Network
jgoldstein@minlib.net

In order to function you must complete the api_info.ini file in the same directory
and add your cacert.pem file to the certifi folder per instructions in the readme

Script will batch update the pickup location for all holds with a status of "on hold" with a specified location code
to a new pickup location code

Two excel log files will be generated in the same directory as this script
One that will include all holds prior to the update
A second with any holds the script was unable to update
'''

import requests
import json
import os
import configparser
from base64 import b64encode
import psycopg2
import xlsxwriter
from datetime import date
#used for pyintaller
#from multiprocessing import Process, freeze_support

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

#updates pickup location via sierra holds API
def mod_hold(hold_id,is_frozen,new_location):
    config = configparser.ConfigParser()
    config.read('api_info.ini')
    token = get_token()
    url = config['api']['base_url'] + "/patrons/holds/" + hold_id
    header = {"Authorization": "Bearer " + token, "Content-Type": "application/json;charset=UTF-8"}
    payload = {"pickupLocation" : new_location, "freeze": is_frozen}
    request = requests.put(url, data=json.dumps(payload), headers = header)

#convert sql query results into formatted excel file
def excelWriter(query_results,excelfile):
    workbook = xlsxwriter.Workbook(excelfile,{'remove_timezone': True})
    worksheet = workbook.add_worksheet()

    #Formatting our Excel worksheet
    worksheet.set_landscape()
    worksheet.hide_gridlines(0)

    #Formatting Cells
    eformat= workbook.add_format({'text_wrap': True, 'valign': 'top', 'align': 'center'})
    eformatlabel= workbook.add_format({'text_wrap': True, 'valign': 'top', 'bold': True, 'align': 'center'})

    # Setting the column widths
    worksheet.set_column(0,0,13.14)
    worksheet.set_column(1,1,10.29)

    #Inserting a header
    worksheet.set_header('UpdatePickupLocations')

    # Adding column labels
    worksheet.write(0,0,'Hold ID', eformatlabel)
    worksheet.write(0,1,'Is Frozen', eformatlabel)

    # Writing the report for staff to the Excel worksheet
    for rownum, row in enumerate(query_results):
        worksheet.write(rownum+1,0,row[0], eformat)
        worksheet.write(rownum+1,1,row[1], eformat)
        
    workbook.close()
    
def main():
	#certificate file needed for pyinstaller
    os.environ['REQUESTS_CA_BUNDLE'] = "certifi/cacert.pem"
    
    #config for both API and SQL access
    config = configparser.ConfigParser()
    config.read('api_info.ini')
    
    #prompt user for pickup location codes to use, ignoring case
    old_location = input("Enter pickup location code to change\nor type \'q\' to quit.\n\n").lower()
    new_location = input("enter new pickup location code.\n").lower()
    
    
    while old_location != 'q':
        #checks if the entered location codes are 4 characters long and end in a z
        if not (old_location.endswith('z') and len(old_location) == 4):
            print('Invalid location code entered, please try again')
            break
        if not (new_location.endswith('z')  and len(old_location) == 4):
            print('Invalid location code entered, please try again')
            break
        
        #confirm before proceeding
        confirm = input("This will change all holds with the pickup location " + old_location + " to " + new_location + ".  Do you wish to proceed?  type \'y\' to continue.\n").lower()
        if not confirm == 'y':
            #print('\nThis program will now quit.  Goodbye.')
            break
        
        #Connecting to Sierra PostgreSQL database
        query = "select h.id, h.is_frozen from sierra_view.hold h where h.pickup_location_code = '" + old_location + "' AND h.status = '0'"
        conn = psycopg2.connect("dbname='iii' user='" + config['api']['sql_user'] + "' host='" + config['api']['sql_host'] + "' port='1032' password='" + config['api']['sql_pass'] + "' sslmode='require'")

        #Opening a session and querying the database for weekly new items
        cursor = conn.cursor()
        cursor.execute(query)
        #For now, just storing the data in a variable. We'll use it later.
        rows = cursor.fetchall()
        conn.close()
        
        #printing to screen to show progress
        print("\nGenerating log")
        
        #Generate log of holds the script is attempting to update
        excelFile =  old_location+'UpdatePickupLoc{}.xlsx'.format(date.today())
        excelWriter(rows,excelFile)
        
        #Iterate through results of SQL query to update each hold
        print("\nUpdating locations")
        for hold_id, is_frozen in rows:
            print("hold id: " + str(hold_id))
            print("is_frozen: " + str(is_frozen))
            mod_hold(str(hold_id),is_frozen,new_location)
        
        #run query again to find holds that could not be updated
        conn = psycopg2.connect("dbname='iii' user='" + config['api']['sql_user'] + "' host='" + config['api']['sql_host'] + "' port='1032' password='" + config['api']['sql_pass'] + "' sslmode='require'")

        #Opening a session and querying the database for weekly new items
        cursor = conn.cursor()
        cursor.execute(query)
        #For now, just storing the data in a variable. We'll use it later.
        rows = cursor.fetchall()
        conn.close()
        
        #Generate log of holds that could not be updated
        excelFile2 =  old_location+'FailedToUpdate{}.xlsx'.format(date.today())
        excelWriter(rows,excelFile2)
            
        #Run again for a different location or quit
        old_location = input("\nEnter another location, or type \'q\' to quit.\n").lower()
        
    print("\nThis program will now quit.  Goodbye.")
    
#used for executable created by pyinstaller
if __name__ == '__main__':
    main()

