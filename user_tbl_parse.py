from itertools import zip_longest

def chunker(data, query_size, fillvalue = '0'):

    ''' Take a bytes object, return an iterable that will iterate in chunks of query_size. '''
        
    args = [iter(data)] * query_size
    return zip_longest(*args, fillvalue=fillvalue)


def string_cleaner(data):

    ''' The tbl file format has blocks allocated for string data. If the data doesn't fill the full block, it will be
        padded with 00s. These 00s must be removed. Strip functions won't work because 00 is not a whitespace character. '''
    
    # Create a list to hold the data without the 00s.
    data_clean = []
    
    for chunk in chunker(data, 2):
        if chunk != (0, 0):
            data_clean.append(chr(chunk[0]))
    
    # Convert the list back to a string
    clean_data_str = ''.join(data_clean) # Convert 
    
    # Return the string
    return(clean_data_str)   
    

class userTable:

    def __init__(self, infile_content):
    
        self.infile_content = infile_content
        
        # self.entries format is [username, domain NetBios (short) name, domain/workgroup FQDN, machine name, machine hardware specs]
        #                            0                   1                       2                    3                4
        self.entries = []
        
    def parse_entries(self):
        
        ''' Search the file for locations of table entries. '''
        doc_length = len(self.infile_content)
        
        user_name = self.infile_content[44:558]
        user_name = string_cleaner(user_name)
        self.entries.append(user_name)
        
        short_domain = self.infile_content[558:1110]
        short_domain = string_cleaner(short_domain)
        self.entries.append(short_domain)
        
        machine_name = self.infile_content[1124:1156]
        machine_name = string_cleaner(machine_name)
        self.entries.append(machine_name)
        
        full_domain = self.infile_content[1156:1670]
        full_domain = string_cleaner(full_domain)
        self.entries.append(full_domain)
        
        specs = self.infile_content[2196:2356]
        specs = string_cleaner(specs)
        self.entries.append(specs)
