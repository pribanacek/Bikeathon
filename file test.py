def getDataFromFile(filename):
    file = open(filename, 'r')
    data = []
    for line in file:
        if len(line) >= 6:
            data.append(line.strip("\n").split(','))
    file.close()
    return data

def writeDataToFile(filename, data):
    with open(filename, 'w') as file:
        for i in data:
            file.write(str(i[0]) + ',' + str(i[1]) + ',' + str(i[2]) + '\n')

filename = 'stack.txt'

##intervals = str([i[0] for i in data]).strip('[').strip(']').replace(' ', '')
##distances = str([i[1] for i in data]).strip('[').strip(']').replace(' ', '')
##speeds = str([i[2] for i in data]).strip('[').strip(']').replace(' ', '')

