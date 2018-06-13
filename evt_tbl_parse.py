from datetime import datetime, timedelta

def convert_time(timestamp):

    ''' Windows NT time is specified as the number of 100 nanosecond intervals since 
        01/01/1601 00:00:00 UTC. It is stored as a 64 bit value. Python time libraries use
        the format of seconds since 01/01/1970. '''
    
    epoch_as_filetime = 116444736000000000
    hundreds_of_ns = 10000000
    
    # Convert to little endian before converting to int. Timestamp is a string containing a hex value.
    # Split into a list (1 byte per element), reverse the list, and convert back to string.
    timestamp_le = []
    for offset in range(0, 16, 2):
        timestamp_le.append(timestamp[offset:offset+2])
    timestamp_le = timestamp_le[::-1]
    timestamp_le = ''.join(timestamp_le)
    
    # Convert timestamp_le to int
    timestamp_int = int(timestamp_le, 16)

    return(datetime.utcfromtimestamp((timestamp_int - epoch_as_filetime) / hundreds_of_ns))

class evtTable:

    def __init__(self, infile_content):
        self.infile_content = infile_content
        
        # dict containing information about each table entry
        self.entries = {}
        # entries structure is:
            # key: offset
            # value: list [entry_num,  event_id, event_desc, doc_id, timestamp]
            #                 0            1          2         3         4
 
        # dict containing definitions for the event_id codes. These are listed in full at:
        # https://msdn.microsoft.com/en-us/library/office/jj230106.aspx
        self.event_codes = {
            1: "Document loaded successfully",
            2: "Document failed to load",
            3: "Template loaded successfully",
            4: "Template failed to load",
            5: "Add-in loaded successfully",
            6: "Add-in failed to load",
            7: "Add-in manifest downloaded successfully",
            8: "Add-in manifest did not download",
            9: "Add-in manifest could not be parsed",
            10:"Add-in used too much CPU",
            11:"Application crashed on load",
            12:"Application closed due to a problem",
            13:"Document closed successfully",
            14:"Application session extended",
            15:"Add-in disabled due to string search time-out",
            16:"Document open when applcation crashed",
            17:"Add-in closed successfully",
            18:"App closed successfully",
            19:"Add-in encountered runtime error",
            20:"Add-in failed to verify licensing"
        }

    def parse_entries(self):
        
        doc_length = len(self.infile_content)
        byte = 44 # Start reading the evt file at the first entry

        # Search through the file content in memory, looking for the table entries.
        while(byte < doc_length):
        
            offset = byte
            self.entries[offset] = []
        
            # The entry number is the first byte
            entry_num = self.infile_content[byte]
            self.entries[offset].append(entry_num)
            
            # The event ID is at offset 32 (one byte)
            event_id = self.infile_content[byte+32]
            self.entries[offset].append(event_id)
            # Event ID can be mapped to a text description in self.event_codes
            if event_id in self.event_codes:
                event_desc = self.event_codes[event_id]
            else:
                event_desc = 'Unknown'
            self.entries[offset].append(event_desc)
            
            # The docid is offsets 36-51
            self.entries[offset].append(self.infile_content[byte+36:byte+52].hex())
            
            # The event timestamp is offsets 132 - 139
            timestamp = self.infile_content[byte+132:byte+140]
            timestamp_hex = timestamp.hex()
            self.entries[offset].append(convert_time(timestamp_hex))
            
            # Print some results
            #print(entry_num)
            #print(event_id)
            #print(self.entries[offset][2]) # description
            #print(self.entries[offset][3]) # docid
            #print(self.entries[offset][4]) # timestamp (UTC)
            #print("\n")
        
            byte += 156 # Jump to next entry
