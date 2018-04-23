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

    
class slnTable:


    def __init__(self, infile_content):
        self.infile_content = infile_content
 
        # dict containing information about each table entry
        self.entries = {}
        # entries structure is:
            # key: offset
            # value: list [type, doc_id,doc_name, doc_path, doc_title, doc_author, addin_name, description]
            #                 0     1      2         3         4          5             6           7

        # dict containing pattern matches for entry types
        self.item_type_dict = {'user_document':'ffffffff', 'application_dll':'09000000'}

    def parse_entries(self):
    
        ''' Search the file for locations of table entries. ''' 
        
        doc_length = len(self.infile_content)
        byte = 0

        # Search through the file content in memory, looking for the table entries.
        while(byte < doc_length):

            # 1st byte should be 0x94
            if hex(self.infile_content[byte]) == '0x94':
        
                # test_block will be compared against the pattern header for table entries.
                test_block = self.infile_content[byte:byte+4]

                # If block matches, 
                if test_block.hex() == '940b0000':

                    # The offset is the current byte number
                    offset = byte
                    self.entries[offset] = []
                
                    # Item type is determined by bytes 1116 - 1119
                    item_type = self.infile_content[byte+1116:byte+1120]
                    found_item_type = False
                    for key, value in self.item_type_dict.items():
                        if item_type.hex() == value:
                            self.entries[offset].append(key)
                            found_item_type = True
                    if not found_item_type:
                        self.entries[offset].append('Unknown')
                
                    # The docid is the 16 bytes after 0x940b
                    self.entries[offset].append(self.infile_content[byte+4:byte+20].hex())
                
                    # The document name is bytes 48 - 567, encoded in UTF-16LE
                    # Extra whitespace is removed.
                    # In some cases, the doc_name is just a BOM with no additional text. These entries will be ignored for the time being.
                    doc_name = self.infile_content[byte+48:byte+568]
                    if doc_name.hex()[0:8] == 'fffe0000':
                        del self.entries[offset]
                        byte += 1
                        continue
                    # Remove trailing 00s from doc_name
                    doc_name = string_cleaner(doc_name)
                    self.entries[offset].append(doc_name)
   
                    # The document path is bytes 568 - 1087. Because there could be any number of 00s at the end
                    # of this segment, they need to be removed before converting to text.
                    doc_path = self.infile_content[byte+568:byte+1088]
                    # Remove trailing 00s from doc_path
                    doc_path = string_cleaner(doc_path)
                    self.entries[offset].append(doc_path)
                
                    # The document title is bytes 1144 - 1401 for user documents, and
                    # 1672-1804 for application dlls.
                    if self.entries[offset][0] == 'application_dll':
                        #doc_title = infile_content[byte+1156:byte+1402]
                        doc_title = self.infile_content[byte+1672:byte+1804]
                    else:
                        doc_title = self.infile_content[byte+1144:byte+1402]
                    if doc_title.hex()[0:8] != 'fffe0000':
                        # Remove trailing 00s from doc_author
                        doc_title = string_cleaner(doc_title)
                        self.entries[offset].append(doc_title)
                    else:
                        self.entries[offset].append('')
                
                    # The document author is bytes 1402 - 2192 for user documents, and
                    # 2706 - 2963 for application dlls.
                    # Make sure author is not blank before adding the to doc_authors list.
                    if self.entries[offset][0] == 'application_dll':
                        doc_author = self.infile_content[byte+2706:byte+2963]
                    else:
                        doc_author = self.infile_content[byte+1402:byte+1672]
                    if doc_author.hex()[0:8] != 'fffe0000':
                        # Remove trailing 00s from doc_author
                        doc_author = string_cleaner(doc_author)
                        self.entries[offset].append(doc_author)
                    else:
                        self.entries[offset].append('')
                
                    # Application_dlls have an add-in name field between offsets 1156 - 1227
                    if self.entries[offset][0] == 'application_dll':
                        addin_name = self.infile_content[byte+1156:byte+1228]
                        if addin_name.hex()[0:8] != 'fffe0000':
                            # Remove trailing 00s from addin_name
                            addin_name = string_cleaner(addin_name)
                            self.entries[offset].append(addin_name)
                        else:
                            self.entries[offset].append('')
                    else:
                        self.entries[offset].append('')
                
                    # Application_dlls also have descriptions between offsets 2192-2705
                    if self.entries[offset][0] == 'application_dll':
                        desc = self.infile_content[byte+2192:byte+2706]
                        if desc.hex()[0:8] != 'fffe0000':
                            # Remove trailing 00s from desc
                            desc = string_cleaner(desc)
                            self.entries[offset].append(desc)
                        else:
                            self.entries[offset].append('')
                    else:
                        self.entries[offset].append('')

                
                # Print some results to the screen        
                #print("Found table entry at offset %d" % offset)
                #print("Item Type = %s" % self.entries[offset][0])
                #print("DocID = %s" % self.entries[offset][1])
                #print("Document = %s\\%s" % (self.entries[offset][3], self.entries[offset][2]))
                #print("Title = %s" % self.entries[offset][4])
                #print("Add-In Name = %s" % self.entries[offset][6])
                #print("Author = %s" % self.entries[offset][5])
                #print("Description = %s" % self.entries[offset][7])
                #print("\n")
            
            byte += 1    

    