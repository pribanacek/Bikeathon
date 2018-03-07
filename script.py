import sys, socket, math, time, threading, http.client, http.server
import RPi.GPIO as gpio

wheelRadius = 0.30 #in metres
gpio.setmode(gpio.BOARD)
gpio.setup(5, 1)

distanceThread = None

class DistanceThread(threading.Thread):
    def __init__(self, interval):
        threading.Thread.__init__(self)
        self.interval = interval
        self.currentSpeed = 0.0
        self.distance = 0.0
        self.stopTracking = False
    def sendData(self, i):
        SendDataThread('10.0.0.100', 80, self.distance, self.currentSpeed, i).start() #change to method, if this is inefficient
        self.distance = 0.0
        self.currentSpeed = 0.0
    def run(self):
        timeSent = time.time() # time since the last data was sent
        read = True
        timeRead = -1.0 # time of last distance reading
        while True:
            if self.stopTracking == True:
                self.sendData(int(time.time() - timeSent))
                break
            
            if gpio.input(5) == 0 and read == True:
                self.distance += 2 * math.pi * wheelRadius
                read = False
                if timeRead > 0:
                    speed = 2 * math.pi * wheelRadius / (time.time() - timeRead)
                    if speed > self.currentSpeed:
                        self.currentSpeed = speed
                timeRead = time.time()
            elif gpio.input(5) == 1:
                read = True
            
            if time.time() - timeSent >= self.interval:
                self.sendData(self.interval)
                timeSent = time.time()


class SendDataThread(threading.Thread):
    def __init__(self, host, port, distance, currentSpeed, interval):
        threading.Thread.__init__(self)
        self.host = host
        self.port = port
        self.distance = distance / 1000 #converts to km
        self.currentSpeed = currentSpeed * 3.6 # converts to km/h
        self.interval = interval
        print(self.distance, '\n', self.currentSpeed)

    def getDataFromFile(filename):
        file = open(filename, 'r')
        data = []
        for line in file:
            if len(line) >= 6:
                data.append(line.strip("\n").split(','))
        file.close()
        return data
    def writeDataToFile(filename, data):
        if data == None:
            return
        with open(filename, 'w') as file:
            for i in data:
                file.write(str(i[0]) + ',' + str(i[1]) + ',' + str(i[2]) + '\n')

    def run(self):
        filename = 'stack.txt'
        data = SendDataThread.getDataFromFile(filename)
        data.append([self.interval, self.distance, self.currentSpeed])
        try:
            connection = http.client.HTTPConnection(self.host, self.port) #timeout = 1?
            connection.connect()
            intervals = str([i[0] for i in data]).strip('[').strip(']').replace(' ', '').replace('\'', '')
            distances = str([i[1] for i in data]).strip('[').strip(']').replace(' ', '').replace('\'', '')
            speeds = str([i[2] for i in data]).strip('[').strip(']').replace(' ', '').replace('\'', '')
            connection.request('POST', '/php/send.php', headers = {'Content-type': 'application/x-www-form-urlencoded'}, body = 'interval=' + intervals + '&distance=' + distances + '&speed=' + speeds)
            print(connection.getresponse().read())
            connection.close()
            SendDataThread.writeDataToFile(filename, [])
        except Exception as e:
            print('Tramsission failed.\nWriting to stack.')
            print(e)
            SendDataThread.writeDataToFile(filename, data)

class CommandHandler(http.server.BaseHTTPRequestHandler):
    def __init__(self, request, client_address, server):
        http.server.BaseHTTPRequestHandler.__init__(self, request, client_address, server)
    def do_POST(self):
        global distanceThread
        try:
            self.data_string = self.rfile.read(int(self.headers['Content-Length']))
            data = self.data_string.decode('utf-8').strip('&').replace('=', '&').split('&')
            response = '-1'
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            print(self.data_string)
        
            if len(data) <= 0 or len(data) % 2 != 0:
                self.wfile.write(bytes(response, 'utf-8'))
                return
            if 'cmd' in data:
                cmd = data[data.index('cmd') + 1]
                if cmd == 'start':
                    if distanceThread != None and distanceThread.isAlive():
                        distanceThread.stopTracking = True
                        distanceThread.join()
                    distanceThread = DistanceThread(2)
                    distanceThread.start()
                    response = '1'
                elif cmd == 'stop':
                    if distanceThread != None:
                        distanceThread.stopTracking = True
                        distanceThread.join()
                    response = '0'
                elif cmd == 'status':
                    if distanceThread != None: 
                        if distanceThread.isAlive():
                            response = '1'
                        else:
                            response = '0'
                    else:
                        response = '0'
            if 'interval' in data and distanceThread != None:
                if distanceThread.isAlive():
                    interval = data[data.index('interval') + 1]
                    distanceThread.interval = int(interval)
                    response = '1'
            self.wfile.write(bytes(response, 'utf-8'))
            print(response)
        except Exception as e:
            self.wfile.write(bytes('-1','utf-8'))
            print(e)

serverName = '0.0.0.0'
port = 80

server = http.server.HTTPServer((serverName, port), CommandHandler)
print('Started server... everything will be just fine')
server.serve_forever()
