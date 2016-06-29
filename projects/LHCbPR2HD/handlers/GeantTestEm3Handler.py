import os
import json

from BaseHandler import BaseHandler


class GeantTestEm3Handler(BaseHandler):

    def __init__(self):
        super(self.__class__, self).__init__()

    def collectResults(self, directory):
        """ Collect  results """

        file = 'Selectedresults.root'
        txtfile = 'selectedresults.txt'
        filename = os.path.join(directory, 'CaloTest', file)
        txtfilename = os.path.join(directory, 'CaloTest', txtfile)
        
        if not os.path.exists(filename):
            raise Exception("File %s does not exist" % filename)
        
        if not os.path.exists(txtfilename):
            raise Exception("File %s does not exist" % txtfilename)
        
        self.saveFile(file, filename)
        
        with open(txtfilename, mode='r') as f:
            lines = f.readlines()
            _,res_val, res_err = lines[1].split(',')
            print(res_val, res_err)
            res_val, res_err = float(res_val), float(res_err.split(';')[0])

            _,const_val, const_err = lines[2].split(',')
            const_val, const_err = float(const_val), float(const_err.split(';')[0])
            


            table = []
            for line in lines[6:]:
                e_en, e_val, e_err = line.split(',')
                e_en, e_val, e_err = float(e_en), float(e_val), float(e_err.split(';')[0])
                table.append((e_en, e_val,e_err))

            self.saveFloat("TESTEM3_FIT_RESOLUTION_VALUE", res_val)
            self.saveFloat("TESTEM3_FIT_RESOLUTION_ERROR", res_err)

            self.saveFloat("TESTEM3_FIT_CONSTANT_VALUE", const_val)
            self.saveFloat("TESTEM3_FIT_CONSTANT_ERROR", const_err)

            self.saveString("TESTEM3_TABLE", json.dumps(table))
