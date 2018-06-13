# TBL Parser
# Arguments: sln.tbl path, evt.tbl path, output file (csv)

import sys
import csv
from sln_tbl_parse import *
from evt_tbl_parse import *
from user_tbl_parse import *

def check_args():

    ''' Make sure that the correct number of arguments were passed to the script.
        If not, display help and exit. '''

    if len(sys.argv) != 5:
    
        help_text = '\n\nMicrosoft Telemetry Parser.\nUsage: python telemparser.py input_sln_file input_evt_file input_user_file output_file.\n\nInput files should be Microsoft .tbl files. Output is csv.\n'
        help_text += 'You MUST have an sln, evt, and user files for this parser to work.\n\n'
        sys.exit(help_text)

        
def validate_tbl_format(infile_content):

    ''' Validate file header of .tbl file. First 8 bytes must be 20 00 00 00 53 44 44 54. 
        Second 8 bytes determine which file (sln, etv, user). '''

    tbl_type = '' # Will hold type of tbl file
    byte = 0
    
    # Grab the first 8 bytes of the file
    test_block_1 = infile_content[0:8]

    # Header should be 2000000053444454
    if test_block_1.hex() == '2000000053444454':
        print('Valid .tbl file found. Checking tbl type...')
    else:
        sys.exit('Invalid .tbl file!')

    # Test the next 8 bytes to determine the type of .tbl file.
    test_block_2 = infile_content[8:16]
    if test_block_2.hex() == '01000000564e4953':
        tbl_type = 'sln'
        print('sln file detected.')
    elif test_block_2.hex() == '01000000544e5645':
        tbl_type = 'evt'
        print('evt file detected.')
    elif test_block_2.hex() == '0100000052455355':
        tbl_type = 'user'
        print('user file detected.')
        
    return(tbl_type)


def build_entry_dict(sln_table, evt_table):

    ''' Build a dict from the entries parsed from sln_table and evt_table, to associate
        each docid with the offsets of entries in both tables. '''

    # docid_offsets is a dict with the format:
    # docid : [[sln_table_offsets], [evt_table_offsets]]
    docid_offsets = {}

    # Build a list of unique docids from the sln table.
    table_entries = set()
    for entry in sln_table.entries:
        table_entries.add(sln_table.entries[entry][1])
    
    # Add the offsets from the sln table into docid_offsets
    for entry in sln_table.entries:
        if sln_table.entries[entry][1] not in docid_offsets:
            # Add a new entry to docid_offsets. Add the value for this sln entry.
            docid_offsets[sln_table.entries[entry][1]] = [[entry,],[]]
        else:
            # Append the value for this sln entry
            # TODO: It doesn't appear the SLN table will contain duplicate DOCID entries.
            docid_offsets[sln_table.entries[entry][1]][0].append(entry)
    
    for entry in evt_table.entries:
        if evt_table.entries[entry][3] not in docid_offsets:
            print("DOCID %s found in evt table but not sln table!")
        else:
            docid_offsets[evt_table.entries[entry][3]][1].append(entry)
            
    return(docid_offsets)
    
    
if __name__ == '__main__':

    # Check to make sure the appropriate number of arguments were provided.
    check_args()
    
    # Open the sln.tbl file in binary mode
    sln_infile_name = sys.argv[1]
    with open(sln_infile_name, 'rb') as infile:
    
        # Read the file contents into memory
        infile_content = infile.read()

    # Validate that the  file is the correct format by checking the file header, else quit with error.
    tbl_type = validate_tbl_format(infile_content)
        
    if tbl_type == 'sln':    
        sln_table = slnTable(infile_content)
        sln_table.parse_entries()
    else:
        sys.exit('Invalid sln.tbl file!')
    
    # Open the evt.tbl file in binary mode
    evt_infile_name = sys.argv[2]
    with open(evt_infile_name, 'rb') as infile:
    
        # Read the file contents into memory
        infile_content = infile.read()

    # Validate that the  file is the correct format by checking the file header, else quit with error.
    tbl_type = validate_tbl_format(infile_content)

    if tbl_type == 'evt':    
        evt_table = evtTable(infile_content)
        evt_table.parse_entries()
    else:
        sys.exit('Invalid evt.tbl file!')
    
    user_infile_name = sys.argv[3]
    with open(user_infile_name, 'rb') as infile:
    
        # Read the file contents into memory
        infile_content = infile.read()
        
    # Validate that the  file is the correct format by checking the file header, else quit with error.
    tbl_type = validate_tbl_format(infile_content)
    
    if tbl_type == 'user':
        user_table = userTable(infile_content)
        user_table.parse_entries()
    else:
        sys.exit('Invalid user.tbl file!')
    
    # docid offsets will be a dict formatted as:
    # docid : [[sln_table_offsets], [evt_table_offsets]]
    docid_offsets = build_entry_dict(sln_table, evt_table)

    # Create a 2 dimensional list to hold the final entries before writing to file.
    # Each entry will be appended to this list as a sub-list.
    results = []
    
    for docid in docid_offsets:
        
        # Get all the sln table values for this document
        # Assume the SLN table does not contain duplicate entries for this.
        doc_path   = sln_table.entries[docid_offsets[docid][0][0]][3] + "\\" + sln_table.entries[docid_offsets[docid][0][0]][2]
        doc_id     = sln_table.entries[docid_offsets[docid][0][0]][1]
        doc_type   = sln_table.entries[docid_offsets[docid][0][0]][0]
        doc_title  = sln_table.entries[docid_offsets[docid][0][0]][4]
        doc_author = sln_table.entries[docid_offsets[docid][0][0]][5]
        addin_name = sln_table.entries[docid_offsets[docid][0][0]][6]
        desc       = sln_table.entries[docid_offsets[docid][0][0]][7]
        
        # Get the evt table values for this document. There can be multiple entries per docid.
        for entry in range(len(docid_offsets[docid][1])):
            timestamp  = evt_table.entries[docid_offsets[docid][1][entry]][4].strftime('%Y-%m-%d %H:%M:%S.%f')
            entry_num  = evt_table.entries[docid_offsets[docid][1][entry]][0]
            event_id   = evt_table.entries[docid_offsets[docid][1][entry]][1]
            event_desc = evt_table.entries[docid_offsets[docid][1][entry]][2]
            results.append([timestamp, entry_num, event_id, event_desc, doc_id, doc_title, doc_path, doc_type, doc_author, addin_name, desc])
    
    with open(sys.argv[4], 'w', newline = '') as csvfile:
        writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        # Write the header row
        writer.writerow(['Timestamp','Entry #', 'Event ID', 'Event Description', 'Document ID', 'Document Title', 'Document Path', 'Document Type', 'Document Author', 'Add-in Name', 'Description'])
        # Add all of the parsed results
        for result in results:
            writer.writerow(result)
            
        
