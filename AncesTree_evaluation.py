import numpy as np
import pandas as pd
import random
import networkx as nx
import pygraphviz as pgv
import itertools
import subprocess
import time
import ast
   
def AncesTree_Acessment(G_Dir,new_mutation_in_clone,n_mutation,tree,muta): 
    muta_relation_inp = np.zeros((n_mutation,n_mutation))#remember the table must be read from rows for correct relation     
    node_com = itertools.combinations(G_Dir.nodes(),2)
    node_com = list(node_com)
    for pair in node_com:
        node1 = pair[0];node2 = pair[1]
        if nx.has_path(G_Dir, node1, node2):
            for i in new_mutation_in_clone[node1]:
                for j in new_mutation_in_clone[node2]:
                    muta_relation_inp[i,j] = 1
        if nx.has_path(G_Dir, node2, node1): 
            for i in new_mutation_in_clone[node1]:
                for j in new_mutation_in_clone[node2]:
                    muta_relation_inp[j,i] = 1                            
        if G_Dir.predecessors(node1) == G_Dir.predecessors(node2):
            for i in new_mutation_in_clone[node1]:
                for j in new_mutation_in_clone[node2]:
                    muta_relation_inp[i,j] = 2
    
    unique, counts = np.unique(muta_relation_inp, return_counts=True)
    relation_counts = dict(zip(unique, counts))
    
    G_outp = pgv.AGraph(tree)
    G_outp_nx = nx.DiGraph()

    for edge in G_outp.edges():
        if edge[0][0] != 's' and edge[0][0] != 'd' and edge[1][0] != 's' and edge[1][0] != 'd':
            G_outp_nx.add_edge(int(edge[0]),int(edge[1]))
    
    muta_group = {}
    for node in G_outp.nodes():
        if node[0] != 's' and node[0] != 'd':
            label = node.attr['label'].encode('utf8')
            muta_group[int(node)] = label.split('\\n')[0]

    f = open(muta).readlines();j = 0
    for i in range(len(f)):
        if 'sample0' in f[i]:j = j+1
        if j == 2: m = f[i+1].split(' ')[:-1];break
            
    for k in muta_group.keys():
        for a in m:
            if muta_group[k] in a.split(';'):muta_group[k]=map(int,a.split(';'))
    
    muta_fraction = 0
    for k in muta_group.keys():
        muta_fraction = muta_fraction + len(muta_group[k])
        
    muta_relation_outp = np.zeros((n_mutation,n_mutation))#only read from row,1 is AD, 2 is Sib,0 is no relation
    node_com = itertools.combinations(G_outp_nx.nodes(),2)
    node_com = list(node_com)
    for pair in node_com:
        node1 = pair[0];node2 = pair[1]
        if nx.has_path(G_outp_nx, node1, node2):
            for i in muta_group[node1]:
                for j in muta_group[node2]:
                    muta_relation_outp[i,j] = 1
        if nx.has_path(G_outp_nx, node2, node1):
            for i in muta_group[node1]:
                for j in muta_group[node2]:
                    muta_relation_outp[j,i] = 1
        if G_outp_nx.predecessors(node1) == G_outp_nx.predecessors(node2):
            for i in muta_group[node1]:
                for j in muta_group[node2]:
                    muta_relation_outp[i,j] = 2
            
    Acc = pd.DataFrame(np.zeros((1,7)),index=None,columns=['%Corr(AD+Sib)','%Corr AD','%AD reverse','%Corr Sib','%AD->Sib','%Sib->AD','%SSNVs'])  
    muta_com = itertools.combinations(range(n_mutation),2)
    muta_com = list(muta_com)    
    for pair in muta_com:
        muta1 = pair[0];muta2 = pair[1]
        if muta_relation_inp[muta1,muta2] == 1:
            if muta_relation_outp[muta1,muta2] == 1:Acc['%Corr AD']+=1;Acc['%Corr(AD+Sib)']+=1
            if muta_relation_outp[muta2,muta1] == 1:Acc['%AD reverse']+=1
            if muta_relation_outp[muta1,muta2] == 2 or muta_relation_outp[muta2,muta1] == 2:Acc['%AD->Sib']+=1
        if muta_relation_inp[muta2,muta1] == 1:
            if muta_relation_outp[muta2,muta1] == 1:Acc['%Corr AD']+=1;Acc['%Corr(AD+Sib)']+=1
            if muta_relation_outp[muta1,muta2] == 1:Acc['%AD reverse']+=1
            if muta_relation_outp[muta1,muta2] == 2 or muta_relation_outp[muta2,muta1] == 2:Acc['%AD->Sib']+=1
        if muta_relation_inp[muta1,muta2] == 2 or muta_relation_inp[muta2,muta1] == 2:
            if muta_relation_outp[muta1,muta2] == 1 or muta_relation_outp[muta2,muta1] == 1:Acc['%Sib->AD']+=1
            if muta_relation_outp[muta1,muta2] == 2 or muta_relation_outp[muta2,muta1] == 2:Acc['%Corr Sib']+=1;Acc['%Corr(AD+Sib)']+=1
    
    Acc['%Corr AD'] = Acc['%Corr AD']/relation_counts[1.0]
    Acc['%AD reverse'] = Acc['%AD reverse']/relation_counts[1.0]
    Acc['%AD->Sib'] = Acc['%AD->Sib']/relation_counts[1.0]    
    Acc['%SSNVs'] = muta_fraction/(n_mutation+0.0)
    if 2 in relation_counts:
        Acc['%Corr(AD+Sib)'] = Acc['%Corr(AD+Sib)']/(relation_counts[1.0]+relation_counts[2.0])
        Acc['%Corr Sib'] = Acc['%Corr Sib']/relation_counts[2.0]
        Acc['%Sib->AD'] = Acc['%Sib->AD']/relation_counts[2.0]
    else:
        Acc['%Corr(AD+Sib)'] = 0
        Acc['%Corr Sib'] = 0
        Acc['%Sib->AD'] = 0    
    
    Acc2 = pd.DataFrame(np.zeros((1,4)),index=None,columns=['Precision','Recall','True Negative Rate','Accuracy'])  
    muta_com = itertools.combinations(range(n_mutation),2)
    muta_com = list(muta_com)
    tp = 0;fn = 0;fp = 0;tn = 0
    for pair in muta_com:
        muta1 = pair[0];muta2 = pair[1]
        if muta_relation_inp[muta1,muta2] == 1:#AD
            if muta_relation_outp[muta1,muta2] == 1:tp = tp +1
            else:fn = fn + 1
        elif muta_relation_outp[muta1,muta2] == 1:fp = fp + 1
        else:tn = tn + 1
        if muta_relation_inp[muta2,muta1] == 1:#AD
            if muta_relation_outp[muta2,muta1] == 1:tp = tp +1
            else:fn = fn + 1
        elif muta_relation_outp[muta2,muta1] == 1:fp = fp + 1
        else:tn = tn + 1
    
    if tp+fp == 0:
        Acc2['Precision'] = None
    else:
        Acc2['Precision'] = tp/(tp+fp+0.0)
    if tp+fn == 0:
        Acc2['Recall'] = None
    else:
        Acc2['Recall'] = tp/(tp+fn+0.0)
    if tn+fp == 0:
        Acc2['True Negative Rate'] = None
    else:
        Acc2['True Negative Rate'] = tn/(tn+fp+0.0)
    if tp+fn+fp+tn == 0:
        Acc2['Accuracy'] = None
    else:
        Acc2['Accuracy'] = (tp+tn)/(tp+fn+fp+tn+0.0)
     
    result = pd.concat([Acc, Acc2], axis=1)

    return result
      
def parse_arguments():  
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("graph", type=str)
    parser.add_argument("textfile", type=str)
    parser.add_argument("solfile", type=str)
    parser.add_argument("dotfile", type=str)
    
    args = parser.parse_args()
    
    graph = args.graph
    textfile = args.textfile
    solfile = args.solfile
    dotfile = args.dotfile
    
    return graph, textfile, solfile, dotfile

############################################################################################
#parse the command line arguments
graph, textfile, solfile, dotfile = parse_arguments()

#read in ground truth tree topology and mutations in its clones
G_Dir = nx.read_gpickle(graph)
f = open(textfile,'r')             
lines = f.readlines()                        
new_mutation_in_clone = ast.literal_eval(lines[2].rstrip('\n').lstrip('\r'))
f.close()
n_mutation = 0
for c in new_mutation_in_clone:
    n_mutation = n_mutation + len(new_mutation_in_clone[c])

#acessment by comparing the ground truth tree with the predicted tree
result = AncesTree_Acessment(G_Dir,new_mutation_in_clone,n_mutation,tree=dotfile,muta=solfile)

#print out results            
print result.to_string(index=False)

