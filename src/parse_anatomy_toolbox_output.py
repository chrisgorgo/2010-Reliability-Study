'''
Created on 22 Aug 2011

@author: filo
'''
import sys,re
from subprocess import Popen, PIPE

def get_label(atlas_name, x, y, z):
    output = Popen(["/usr/bin/atlasquery", '-a', atlas_name, '-c', '%s, %s, %s'%(x,y,z)], stdout=PIPE).communicate()[0]
    #print output
    output = output.split("<br>")[1].split(',')[0]
    p_label = re.compile(r'(?P<perc>\d+)% (?P<name>.+)')
    res = p_label.match(output)
    if res:
        name = res.group('name').strip().replace("No label found!","N/A")
        perc = res.group('perc')
    else:
        name = output.strip()
        perc = "N/A"
    return (name, perc)

if __name__ == '__main__':
    f = open(sys.argv[1], 'r')
    cluster_overlap_out = open(sys.argv[1].replace(".txt", "_cluster_overlap.csv"), 'w')
    cluster_overlap_out.write("Size (vox), Percentage of cluster, Side, Area name, Percentage of area\n")
    
    cluster_maximas_out = open(sys.argv[1].replace(".txt", "_cluster_maximas.csv"), 'w')
    cluster_maximas_out.write("'t value', X, Y, Z, Julich (main), Julich (cytoarchitectonic), Julich probability, Harvard-Oxford Cortical, Probability, Harvard-Oxford Subcortical, Probability, Talairach\n")
    
    p_maximum = re.compile(r'Maximum \d+\s+= (?P<value>\d+\.\d+)\s+X / Y / Z =\s+[-]*\d+\s+[-]*\d+\s+[-]*\d+\s+MNI:\s+(?P<x>[-]*\d+)\s+(?P<y>[-]*\d+)\s+(?P<z>[-]*\d+)\s+(?P<area_name>.+)')
    p_maximum_probability = re.compile('\s+Probability for\s+(?P<name>[^\t]+)\s+(?P<perc>\d+)\s+%.*')
    
    p_cluster_header = re.compile(r'Cluster (?P<cluster_id>\d+) \((?P<cluster_size>\d+) vox\):.*')
    p_cluster_overlap = re.compile(r'(?P<size>\d+\.\d)\s+voxel =\s+(?P<perc_of_cluster>\d+\.\d)\s+% in\s+(?P<side>[a-z]+)\s+(?P<area_name>.+)\s+(?P<perc_of_area>\d+\.\d)\s+% of this area activated')
    line = f.readline()
    while line:
        res = p_cluster_header.match(line)
        if res:
            print "Cluster %s (%s vox)"%(res.group('cluster_id'), res.group('cluster_size'))
            cluster_overlap_out.write("Cluster %s (%s vox)\n"%(res.group('cluster_id'), res.group('cluster_size')))
            cluster_maximas_out.write("Cluster %s (%s vox)\n"%(res.group('cluster_id'), res.group('cluster_size')))
        res = p_cluster_overlap.match(line)
        if res:
            print "%s, %s, %s, %s, %s"%(res.group('size'), res.group('perc_of_cluster'),res.group('side'),res.group('area_name').strip(), res.group('perc_of_area'))
            cluster_overlap_out.write("%s, %s, %s, %s, %s\n"%(res.group('size'), res.group('perc_of_cluster'),res.group('side'),res.group('area_name').strip(), res.group('perc_of_area')))
        res = p_maximum.match(line)
        if res:
            line = f.readline()
            res2 = p_maximum_probability.match(line)
            if res2:
                sub_name = res2.group('name')
                sub_perc = res2.group('perc')
            else:
                sub_name = "N/A"
                sub_perc = "N/A"
            (x,y,z) = res.group('x'),res.group('y'),res.group('z')
            ho_subcor_name, ho_subcor_perc =  get_label("Harvard-Oxford Subcortical Structural Atlas", x, y, z)
            ho_cor_name, ho_cor_perc =  get_label("Harvard-Oxford Cortical Structural Atlas", x, y, z)
            t_name, _ =  get_label("Talairach Daemon Labels", x, y, z)
            print "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s"%(res.group('value'),x,y,z,res.group('area_name').split('->')[0].strip(), sub_name.strip(), sub_perc, ho_cor_name, ho_cor_perc, ho_subcor_name, ho_subcor_perc, t_name)
            cluster_maximas_out.write("%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s\n"%(res.group('value'),x,y,z,res.group('area_name').split('->')[0].strip(), sub_name.strip(), sub_perc, ho_cor_name, ho_cor_perc, ho_subcor_name, ho_subcor_perc, t_name))
        line = f.readline()
    cluster_overlap_out.close()
    cluster_maximas_out.close()
            