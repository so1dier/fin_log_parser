import getopt
import sys
import os.path
import commands
import binascii


from py8583 import Iso8583
from py8583spec import *

verbose=False

def show_help(name):
    """
    Show help and basic usage
    """
    print('Usage: python {} [OPTIONS]... '.format(name))
    print('ISO8583 message parser')
    print('  -v, --verbose\t\tRun transactions verbosely')
    print('  -i, --input\t\tInput file name')
    print('  -o, --output\t\tOutput file name')

def get_log_time(line):
    line_array = line.split()
    return ("{} {}".format(line_array[0], line_array[1]))

def get_card_number(line):
    line_until_D = line.split('D',1)[0]
    card = line_until_D[-16:]
    return card

def get_time_and_card(line):
    log_time = get_log_time(line)
    card_number = get_card_number(line)
    return ("{} {}".format(log_time, card_number))

def get_iso_message(line):
    message = line.split()[2]
    if not (len(message) % 2 == 0):
        message = message[:len(message)-1]
    return message


def Print(message):
    if (verbose):
        print(message)

def GetFixedColumnsCommand(file_in, cmd_idebitc, cmd_iheritage):
    if "idebitc" in file_in:
        cmd = cmd_idebitc
    elif "iHeritage" in file_in:
        cmd = cmd_iheritage
    elif "iMastercard" in file_in:
        cmd = cmd_iheritage
    return cmd

def GetCardNumber(IsoPacket):
    card = IsoPacket.FieldData(2)
    if (card == None):
        card = IsoPacket.FieldData(35)
        if (card != None):
            card = card[:16]
    return card

def ParseRawMessage(file_in, message_in):
    if "idebitc" in file_in:
        IsoPacket = Iso8583(message_in[2:], IsoSpec1987_idebitc())
    elif "iHeritage" in file_in:
        IsoPacket = Iso8583(message_in[2:], IsoSpec1987ASCII())
    elif "iMastercard" in file_in:
        IsoPacket = Iso8583(message_in[2:], IsoSpec1987ASCII())
    else:
        IsoPacket = Iso8583(message_in[2:], IsoSpec1987ASCII())
    return IsoPacket

def Process(file_in, file_out):
    cmd_get_response_code_91_with_whole_trn_block = 'awk \'BEGIN{RS=ORS="Execution "}/39 Response Code........... 91/;END{printf \"\\n\"}\' '
    cmd_get_iso_message_with_noise =                'awk \'/Received.*Bytes/{flag=1; next} /Incoming .../{flag=0;print ""} flag \' '
    #cmd_get_time_and_iso_columns =                  'awk \'{print$1,$2,$4$5$6$7$8$9$10$11}\''
    cmd_get_time_and_iso_columns_idebitc =                  'awk \'BEGIN{ FIELDWIDTHS="10 1 12 7 4 1 4 1 4 1 4 1 4 1 4 1 4 1 4"}{print$1,$3,$5$7$9$11$13$15$17$19}\' '
    cmd_get_time_and_iso_columns_heritage =                  'awk \'BEGIN{FIELDWIDTHS="10 1 12 13 4 1 4 1 4 1 4 1 4 1 4 1 4 1 4"}{print$1,$3,$5$7$9$11$13$15$17$19}\' '
    cmd_get_time_and_iso_one_line =                 'awk \'!NF {print line; line=""; next} {line=(line?line $NF:$0)} END {print line}\' '

    cmd_get_time_and_iso_columns = GetFixedColumnsCommand(file_in, cmd_get_time_and_iso_columns_idebitc, cmd_get_time_and_iso_columns_heritage) 

    cmd_full = cmd_get_response_code_91_with_whole_trn_block + file_in \
               + " | " + cmd_get_iso_message_with_noise \
               + " | " + cmd_get_time_and_iso_columns \
               + " | " + cmd_get_time_and_iso_one_line

    if (verbose):
        print "Full command: {}".format(cmd_full)

    time_and_iso_container = commands.getoutput(cmd_full)

    if (verbose):
        print "RESULT = " + time_and_iso_container
    
    for line in time_and_iso_container.splitlines():
        #time_and_card = get_time_and_card(line)
        time_and_date = get_log_time(line)
        hex_message = get_iso_message(line)
        if (verbose): print hex_message
        #converted_message = text_from_bits(message)
        #converted_message = message.decode("hex")
        #converted_message = bytearray.fromhex(message).decode()
        #print time_and_card
        #message_in = ISO8583()
        #message_in.setNetworkISO(converted_message)
        message_in = binascii.unhexlify(hex_message)
        if (verbose): print message_in
       
        IsoPacket = ParseRawMessage(file_in, message_in)

        #IsoPacket.PrintMessage()
        #print IsoPacket.FieldData(2)
        card_number = GetCardNumber(IsoPacket)
        print ("{} {}").format(time_and_date, card_number) 
        #sys.exit()

if __name__ == '__main__':
    #verbose = False
    file_in = None
    file_out = None

    try:
        #optlist, args = getopt.getopt(sys.argv[1:], 'hp:s:t:m:k:K:f:v', ['help', 'port=', 'server=', 'terminal=', 'merchant=', 'terminal-key=', 'master-key=', 'file=', 'verbose'])
        optlist, args = getopt.getopt(sys.argv[1:], 'hp:v:i:o', ['help', 'port=', 'server=', 'terminal=', 'merchant=', 'terminal-key=', 'master-key=', 'file=', 'verbose'])
        for opt, arg in optlist:
            if opt in ('-h', '--help'):
                show_help(sys.argv[0])
                sys.exit()
            
            if opt in ('-v', '--verbose'):
                verbose = True

            elif opt in ('-i', '--input'):
                file_in = arg
                if not os.path.isfile(file_in):
                    print "File does not exist"
                    sys.exit()
    
            elif opt in ('-o', '--output'):
                file_out = arg
    
    except getopt.GetoptError:
        show_help(sys.argv[0])
        sys.exit()

    if (file_in==None):
        print "Input file name is empty (-i)"
        sys.exit()
    
    Process(file_in, file_out)    
