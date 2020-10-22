from config import *
from util import *
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/posv2v2/api/status', methods=['GET'])
def get_status():
    # Get supermajority status from debug.log
    fileHandle = open(debug_log, "r")
    lineList = fileHandle.readlines()
    fileHandle.close()
    supermajority_pos_num = 0
    supermajority_percentage = 0
    for x in range(60):
        line = lineList[-x]
        if "Version 5 block" in line:
            current_pos_from = line.find("Version 5 block") + 17
            current_pos_to = line.find("Version 5 block") + 21
            supermajority_pos_num = line[current_pos_from:current_pos_to].strip()
            break
    if int(supermajority_pos_num) > 0:
        supermajority_percentage = get_decimal(OP_DIV, supermajority_pos_num, 9000) * 100
        supermajority_percentage = format_number(supermajority_percentage, True, 2)

    status = [
        {
            'v5_blocks': supermajority_pos_num,
            'percentagewise': supermajority_percentage
        }
    ]

    return jsonify({'status': status})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8089, debug=True)
