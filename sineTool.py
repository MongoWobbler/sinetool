import pymel.core as pm
from math import pow,sqrt

 
def getDistance(objA, objB):
	gObjA = pm.xform(objA, q=True, t=True, ws=True)
	gObjB = pm.xform(objB, q=True, t=True, ws=True)
	
	return sqrt(pow(gObjA[0]-gObjB[0],2)+pow(gObjA[1]-gObjB[1],2)+pow(gObjA[2]-gObjB[2],2))

	
def offsetCreator(list, name='offset'):

    returnList = []

    for object in list:
        
        # get the objectsParent
        objectParent = object.getParent()

        # create a empty transform node and parent it to the object to position and orient
        offset = pm.createNode('transform', n=name + '_' + object)
        pm.parentConstraint(object, offset)
        pm.delete(pm.listRelatives(offset, type='parentConstraint'))
        pm.makeIdentity(offset, apply=True, t=True, r=True, s=True)
        pm.delete(offset, ch=True)

        # if the object has a parent, parent the offset under the object parents, and the parent the object under the offset
        if objectParent:
            pm.parent(offset, objectParent)
            pm.makeIdentity(offset, apply=True, t=True, r=True, s=True)
            pm.parent(object, offset)

        # if the object doesnt have a parent it means that it is already in worldspace, in which case, just parent the object to the offset
        elif objectParent is None:
            pm.parent(object, offset)
        
        returnList.append(offset)    
    
    return returnList


def placeSine(sineTool, cntrlList):

    tempGrp = pm.group(pm.parent(pm.duplicate(cntrlList), w=True))

    pm.setToolTo('Move')
    pos = pm.manipMoveContext('Move', q=1, p=1)

    pm.delete(tempGrp)
    pm.select(clear=True)

    pm.move(sineTool, pos)

    distanceNum = getDistance(cntrlList[0], cntrlList[-1])

    sineTool.scale.set([distanceNum, distanceNum, distanceNum])

    pm.aimConstraint(cntrlList[-1], sineTool)
    pm.delete(pm.listRelatives(sineTool, type='aimConstraint'))
    
    return distanceNum


#function to to make the sin tool
def create(cntrlList=[], axis='x', num=0):
    
    if not cntrlList:
        cntrlList = pm.selected()
        
    if not cntrlList:
        pm.warning('Must select controls to create sine tool on')
        return
    
    #variables
    cubePos = -.5
    axis = axis.upper()
    time = pm.PyNode('time1')
    cubeList = []
    digitList = []
    sineList = pm.ls('*sineTool_grp*', type='transform')

    #num are the cubes, if its 0 the the cubes will be the same as the cntrls (default accuracy)
    if num == 0:
       num = len(cntrlList)
    
    #distance between each cube
    if num == 1:
        cubeDist = 0.0
    else:
        cubeDist = 1/(float(num-1))

    #figure out what prefix our SineTool will have, allows up to 10 sinetool in one scene at a time
    if sineList != []:

        for sine in sineList:
            for x in sine:
                if x.isdigit() == True:
                    digitList.append(x)

        prefix = 'SN' + str(int(max(digitList)) + 1) + axis
    else:
        prefix = 'SN1' + axis

    #master group
    sineTool = pm.group(name=prefix + 'sineTool_grp', empty=True)

    #Sine Cntrl
    sineCntrl = pm.circle(n=prefix + 'sineController', ch=False)[0]
    pm.parent(sineCntrl, sineTool)

    #adding atributes to sineCntrl
    pm.addAttr(sineCntrl, longName='outputVisibility', k=True, min=0, max=1, dv=1, at='bool')
    pm.addAttr(sineCntrl, longName='resultVisibility', k=True, min=0, max=1, dv=1, at='bool')
    pm.addAttr(sineCntrl, longName='sineLength', k=True)
    pm.addAttr(sineCntrl, longName='sineValue', k=True)
    pm.addAttr(sineCntrl, longName='sineSpeed', k=True)
    pm.addAttr(sineCntrl, longName='_', k=True, at='enum', en='_')
    pm.addAttr(sineCntrl, longName='proportion', k=True, dv=1)
    sineCntrl._.lock()

    #groups to keep everything separated
    sineValueMaster = pm.group(name=prefix + 'sineValue_grp', empty=True, parent=sineCntrl)
    outputGrp = pm.group(name=prefix + 'sineOutput_grp', empty=True, parent=sineTool)
    resultGrp = pm.group(name=prefix + 'sineResult_grp', empty=True, parent=sineTool)

    #connecting time and visibility
    sineMult = pm.shadingNode('multiplyDivide', n='sineSpeedMult', au=True)
    time.outTime >> sineMult.input1X
    sineCntrl.sineSpeed >> sineMult.input2X
    sineMult.outputX >> sineValueMaster.rz
    sineCntrl.outputVisibility >> sineValueMaster.visibility
    sineCntrl.resultVisibility >> resultGrp.visibility

    for i in range(num):
        
        #for the first sineValueGrp we make, parent it to the master group. Parent the rest to the previous sineValueGrp
        if i == 0:
            sineValueGrp = pm.group(name=prefix + 'sineValue_grp_' + str(1), empty=True, parent=sineValueMaster)
        else:
            sineValueGrp = pm.group(name=prefix + 'sineValue_grp_' + str(i + 1), empty=True, parent=sineValueGrp)
        
        #makes locators that will be the points in our circle
        sineLoc = pm.spaceLocator(name=prefix + 'sineLoc_' + str(i + 1))
        pm.parent(sineLoc, sineValueGrp)
        sineCntrl.sineLength >> sineValueGrp.rz
        sineCntrl.sineValue >> sineLoc.tx
        
        #makes outputs so that we can grab the Y value of our locators in world space
        output = pm.group(name=prefix + 'sineOutput_' + str(i + 1), empty=True, parent=outputGrp)
        pm.pointConstraint(sineLoc, output)

        #the cube is a visual representation of our output
        cube = pm.polyCube(d=.1, w=.1, h=.1, ch=False, n=prefix + 'sineResult_' + str(i + 1))[0]
        pm.parent(cube, resultGrp)
        cube.tx.set(cubePos)
        cubePos = cubePos + cubeDist
        
        #add influence attribute to control how much each cube is influenced by our outputs
        pm.addAttr(sineCntrl, longName='influence_' + str(i + 1), k=True, min=0, max=1, dv=((i+1)/float(num))**2)
        influenceMult = pm.shadingNode('multiplyDivide', n=prefix + 'influenceMult_' + str(i + 1), au=True)
        
        output.ty >> influenceMult.input1X
        pm.connectAttr(sineCntrl + '.influence_' + str(i + 1), influenceMult.input2X)
        
        influenceMult.outputX >> cube.ty
        
        cubeList.append(cube)

    #place the sine tool in the middle of our selected cntrls and gets the distance between the cntrls    
    distance = placeSine(sineTool, cntrlList)
    
    #set the attribute proportion to be distance/10
    sineCntrl.proportion.set(distance/float(10))
    
    #create our offsets that are the groups that will be rotated, these will be parents of our cntrls
    offsetList = offsetCreator(cntrlList, name=prefix + 'offset')
    
    for cntrl, offset in zip(cntrlList, offsetList):
        distanceList = []
        
        #for each cntrl, get how far each cube is from the cntrl
        for cube in cubeList:    
            distanceList.append(getDistance(cube, cntrl))
        
        #the minCube is the closest cube to the current cntrl    
        minCube = cubeList[distanceList.index(min(distanceList))]    
        
        #connect each cube with our offsets based on whatever axis we specified
        proportionMult = pm.shadingNode('multiplyDivide', n=prefix + 'sineProportion' + offset + 'Mult', au=True)        
        pm.connectAttr(minCube + '.ty', proportionMult.input1X)
        pm.connectAttr(sineCntrl.proportion, proportionMult.input2X)
        pm.connectAttr(proportionMult.outputX, offset + '.rotate' + axis)
            
    pm.select(clear=True)
    pm.select(sineCntrl)
