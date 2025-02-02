
import os
import pickle
import multiprocessing 
from pathlib import Path

import numpy as np
import pandas as pd
import pyBigWig as BW
import conorm





def getIndex(l, nP):
    """
    This function splits list of regions into smaller chunks.
    """
    total = len(l)

    ppr = np.floor( total / nP)

    currents = []
    targets = []
    for pj in range(nP):
        if (pj+1) * ppr + ppr > total:
            currents.append(int(targets[-1]))
            targets.append(total)
            break
        currents.append(int(pj * ppr))
        targets.append(int((pj+1) * ppr))
    return currents, targets



def getSignal(poss, files, mi, Nbins,h, type_="mean", scaled=False, igv=False):
    """
    This function gets signal.
    """
    S = np.zeros((len(poss), len(files), Nbins))
    for j,file in enumerate(files):
        print(f"{mi}: {file.split('/')[-1]}", end=" :: ")
        bw = BW.open(file)
        sizes = bw.chroms()
        for i,pos in enumerate(poss):
            
            if scaled:
                start = pos[1]
                end = pos[2]
                                
                startCrop = 0
                endCrop = 0
                
                hbin = Nbins // 4
                bins = startCrop + endCrop + 2*hbin
                
                tmp = bw.stats(pos[0], start, end, nBins=Nbins-bins,  type=type_)
                
                hbin1 = bw.stats(pos[0], start-h, start, nBins=hbin,  type=type_)
                hbin2 = bw.stats(pos[0], end, end+h, nBins=hbin,  type=type_)
                
                tmp = np.concatenate((hbin1, tmp,hbin2))            
            
            elif igv:
                
                start_ = pos[1]
                end_ = pos[2]
                    
                l = end_ - start_
                h = l
                      
                if start_-h < 0:
                    start = 1
                    startCrop = (Nbins//2) - (abs(start_ - start) // 20)
                else:
                    start = start_ -h
                    startCrop = 0
                
                if end_ +h > sizes[pos[0]]:
                    end = sizes[pos[0]]
                    endCrop = (Nbins//2) - (abs(end_ - end) // 20)
                else:
                    end = end_ +h
                    endCrop = 0
                bins = startCrop + endCrop
                
                tmp = bw.stats(pos[0], start, end, nBins=Nbins-bins,  type=type_)

            else:
                center = (pos[1]+pos[2]) // 2
                if center-h < 0:
                    start = 1
                    startCrop = (Nbins//2) - (abs(center - start) // 20)
                else:
                    start = center -h
                    startCrop = 0
                if center +h > sizes[pos[0]]:
                    end = sizes[pos[0]]
                    endCrop = (Nbins//2) - (abs(center - end) // 20)
                else:
                    end = center +h
                    endCrop = 0
                bins = startCrop + endCrop
                
                try:
                    tmp = bw.stats(pos[0], start, end, nBins=Nbins-bins,  type=type_)
                except: 
                    print(pos)
                    
                    
            try:
                S[i,j,:] = np.nan_to_num(np.concatenate((np.zeros((startCrop)), tmp, np.zeros((endCrop)))))
            except:
                print(pos)
    pickle.dump(S, open(f".tmp/{mi}.p", "wb"))




def readFile(path):
    poss = []
    with open(path, "r") as f:
        for line in f.readlines():
            row = line.strip().split("\t")
            poss.append((row[0], int(row[1]), int(row[2])))
    return poss




def concatSignal(out, nP):
    """
    This function concatenates multiple pickle files into one pickle file.
    """
    for i in range(nP):
        with open(f".tmp/{i}.p","rb") as f:
            tmp = pickle.load(f)
            if i == 0:
                A = tmp
            else:                
                A = np.concatenate((A, tmp), 0)
    print("Writing...")
    
    A = np.nan_to_num(A)
    with open(out, "wb") as f:
        pickle.dump(A, f)
        
