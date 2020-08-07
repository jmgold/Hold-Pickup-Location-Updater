# Hold Pickup Location Batch Updater

Script will batch update the pickup location for all holds with a status of "on hold" with a specified location code
to a new pickup location code

Two excel log files will be generated in the same directory as this script
One that will include all holds prior to the update
A second with any holds the script was unable to update

Within the dist folder you will find a deployable for windows executable version of the script created using pyinstaller

Prerequistes

In order to function you must complete the api_info.ini file in the same directory
and add your cacert.pem file to the certifi folder

api_info.ini
Requires valid credentials for both the Sierra holds API and sql access
The file should be formatted like so

[api]
base_url = https://[local domain]/iii/sierra-api/v5
client_key = [enter Sierra API key]
client_secret = [enter Sierra API secret]
sql_host = [enter host for Sierra SQL server]
sql_user = [enter sql username]
sql_pass = [enter sql password]

cacert.pem file
To find where this file is located on your computer you may run the following python script

import certifi
certifi.where()

Once you've located the file, copy it to the certifi folder
