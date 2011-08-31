'''
Created on 29 Aug 2011

@author: filo
'''
import glob
from parse_line_bisection_log import parse_line_bisection_log
import numpy as np

logs = glob.glob("/media/data/2010reliability/data/*/*/logs/*-Line_Bisection.log")

print logs

task_accuracy = []
task_responses = []
rest_responses = []

for logfile in logs:
    _,pictures ,correct_pictures, incorrect_pictures, noresponse_pictures = parse_line_bisection_log(logfile, 4*2.5)
    cur_accuracy = float(len(correct_pictures['task']))/(len(correct_pictures['task'])+len(incorrect_pictures['task']))
    task_accuracy.append(cur_accuracy)
    
    cur_task_responses = float(len(pictures['task'])-len(noresponse_pictures['task']))/len(pictures['task'])
    task_responses.append(cur_task_responses)
    
    cur_rest_responses = float(len(pictures['rest'])-len(noresponse_pictures['rest']))/len(pictures['rest'])
    rest_responses.append(cur_rest_responses)
    
    
print "task correct answers - mean: %f, std: %f"%(np.array(task_accuracy).mean(), np.array(task_accuracy).std())
print "task responses - mean: %f, std: %f"%(np.array(task_responses).mean(), np.array(task_responses).std())
print "rest responses - mean: %f, std: %f"%(np.array(rest_responses).mean(), np.array(rest_responses).std())