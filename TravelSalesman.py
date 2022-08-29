import tsp
from geopy.distance import geodesic
def fetchTravelPattern(data):
    nodepostidMap={}
    datalen = len(data)
    for idx in range(datalen):
        nodepostidMap[idx]=data[idx]
    distmatrix=[]
    for i in range(datalen):
        temp=[0]*datalen
        distmatrix.append(temp)
    print(distmatrix)
    for i in range(datalen):
        for j in range(datalen):
            if(i!=j):
                distmatrix[i][j]=geodesic( (nodepostidMap[i][1],nodepostidMap[i][2]) , (nodepostidMap[j][1],nodepostidMap[j][2]) ).kilometers   
    print(distmatrix)
    shortestpath={(i,j):distmatrix[i][j] for i in range(datalen) for j in range(datalen)}
    r=range(datalen)
    pathpattern = tsp.tsp(r,shortestpath)
    pathpattern = pathpattern[1]
    
    postorder=[]
    for path in pathpattern:
        postorder.append(nodepostidMap[path][0])
    return postorder    


