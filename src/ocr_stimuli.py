'''
Created on 23 Aug 2011

@author: filo
'''
from subprocess import Popen
import re
import numpy

data_dir = "/media/data/2010reliability/fmri_protocols/Stimuli/"

freq_list = []

if __name__ == '__main__':
    f = open(data_dir + "words_as_pics/words.txt")
    for line in f:
        if line.strip() != "":
            print line.strip()
            f_corpus = open(data_dir + "bnc_corpus.txt")
            #print r'(?P<freq>\d+) ' + line.strip() + r' nn1 .*'
            p = re.compile(r'(?P<freq>\d+)\s+' + line.strip() + r'\s+nn1\s+.*')
            for corpus_line in f_corpus:
                #print corpus_line
                res = p.match(corpus_line)
                if res:
                    freq_list.append(float(res.group('freq'))/100106029.0)
                    print "'%s' frequency: %s"%(line.strip(), float(res.group('freq'))/100106029.0)
                    break
            f_corpus.close()
            
    freq_list = numpy.array(freq_list)
    print "min: %f, max: %f, mean: %f, std: %f"%(freq_list.min(), freq_list.max(), freq_list.mean(), freq_list.std())