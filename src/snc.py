#!/usr/bin/env python
import time
import json
import rospy
import string
import requests
import traceback
from snc_sensors_publisher.msg import SnCSensor
from snc_sensors_publisher.msg import SnCSensorsMsg


import datetime

def init():
    rospy.init_node("snc_sensors_publisher")

    api_url = rospy.get_param('~api_url', 'https://dev.encontrol.io/api/')
    username = rospy.get_param('~username', 'gstavrinos')
    password = rospy.get_param('~password', 'test')
    installationid = rospy.get_param('~installation_id', '00000000-0000-0000-0000-b827eb9a72ca')
    userid = rospy.get_param('~user_id', 543)
    sensor_topic = rospy.get_param('~sensor_topic', 'snc_sensors/status')
    event_topic = rospy.get_param('~event_topic', 'snc_sensors/events')
    interval = rospy.get_param('~interval', 10)

    publisher = rospy.Publisher(sensor_topic, SnCSensorsMsg, queue_size=1)
    publisher2 = rospy.Publisher(event_topic, SnCSensorsMsg, queue_size=1)

    s = requests.Session()
    auth = False
    while not auth:
        try:
            s.post(api_url + 'auth?format=json&username=' + username + '&password=' + password)
            auth = True
        except:
            print traceback.format_exc()
            time.sleep(10)
    jsn =  json.loads(s.get(api_url + '/installations/'+installationid+'/sensors?format=json').text)
    
    sensor_ids = []
    sensor_names = []
    printable = set(string.printable)

    for j in jsn['Sensors']:
        sensor_names.append(str(filter(lambda x: x in printable,j['Name'])))
        sensor_ids.append(str(filter(lambda x: x in printable,j['Id'])))

    while not rospy.is_shutdown():
        msg = SnCSensorsMsg()
        sensors = []

        try:
            for i in range(len(sensor_ids)):
                sensor = SnCSensor()

                jsn =  json.loads(s.get(api_url + 'sensors/' + sensor_ids[i] + '/details?format=json').text)
                jsn = jsn['Sensor']
                sensor.id = sensor_ids[i]
                sensor.name = sensor_names[i]

                try:
                    sensor.status = jsn['Status']
                except:
                    sensor.status = 'N/A'
                try:
                    sensor.value = jsn['Value']
                except:
                    sensor.value = -999999

                sensors.append(sensor)

            msg.header.stamp = rospy.Time.now()
            msg.sensors = sensors
            publisher.publish(msg)
            #print datetime.datetime.now()

            time.sleep(interval/2)

            msg = SnCSensorsMsg()
            events = []

            jsn =  json.loads(s.get(api_url + '/events?UserId='+str(userid)+'&Type=control').text)
            #https://dev.encontrol.io/api/events?UserId=543&Type=control
            jsn = jsn['Events']
            cnt = 0
            for j in jsn:
                if j['InstallationId'] == installationid:
                    event = SnCSensor()
                    event.id = j['InstallationId']
                    event.name = j['Description']
                    event.status = j['Date']
                    event.value = 0
                    events.append(event)
                    # Add the ten latest only, because the json response includes days of events!
                    cnt += 1
                    if cnt >= 10:
                        break

            msg.header.stamp = rospy.Time.now()
            msg.sensors = events
            publisher2.publish(msg)

            time.sleep(interval/2)
        except:
            # Do we get here because of an expired session?
            print traceback.format_exc()
            try:
                s.post(api_url + 'auth?format=json&username=' + username + '&password=' + password)
            except:
                print traceback.format_exc()


if __name__ == '__main__':
    init()
