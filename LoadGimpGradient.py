"""
Script to import a GIMP gradient ".ggr" file into c4d
by: Pappy Bedard, 2/25/2021
YouTube tutorials: https://www.youtube.com/channel/UCMMAnW3rkECfaRrtyrhGoTQ
"""

import c4d
import os
from c4d import storage

def Interp(i,color_left,color_right):
    if int(i) == 0:
        Interpolation = c4d.GRADIENTSUBCHANNEL_INTERPOLATION_LINEARKNOT
    elif int(i) == 1:
        Interpolation = c4d.GRADIENTSUBCHANNEL_INTERPOLATION_SMOOTHKNOT
    elif int(i) == 2:
        Interpolation = c4d.GRADIENTSUBCHANNEL_INTERPOLATION_CUBICKNOT
    elif int(i) == 3:
        Interpolation = c4d.GRADIENTSUBCHANNEL_INTERPOLATION_EXP_UP
    elif int(i) == 4:
        Interpolation = c4d.GRADIENTSUBCHANNEL_INTERPOLATION_EXP_DOWN
    else:
        Interpolation = c4d.GRADIENTSUBCHANNEL_INTERPOLATION_LINEARKNOT

    if color_left == color_right:
        Interpolation = c4d.GRADIENTSUBCHANNEL_INTERPOLATION_NONE

    return Interpolation


def main():
    filepath = storage.LoadDialog(title = 'Select Gimp Gradient File', flags = c4d.FILESELECT_LOAD)

    gradient = c4d.Gradient()
    name = os.path.basename(filepath)

    f = open(filepath,'r')
    KNOTS = []
    for line in f:
        if 'name' in line.lower():
            n = str(line.split(':')[1]).strip()
            if n!="":
                name = n
        ldata = line.strip().split(' ')
        if len(ldata)>=13:
            left = float(ldata[0])
            right = float(ldata[2])
            b = float(ldata[1])
            bias = (b-left)/(right-left)
            color_left = c4d.Vector(float(ldata[3]), float(ldata[4]), float(ldata[5]))
            alpha_left = float(ldata[6])
            color_right = c4d.Vector(float(ldata[7]), float(ldata[8]), float(ldata[9]))
            alpha_right = float(ldata[10])
            Interpolation = Interp(ldata[11],color_left,color_right)

            KNOTS.append([color_left,alpha_left,left,bias,0,Interpolation])
            KNOTS.append([color_right,alpha_right,right,bias,0,Interpolation])
    f.close()

    #insert the knots but don't include the duplicate ones
    Included = []
    for i,KT in enumerate(KNOTS):
        Include = True
        #always include the first and last knot
        if (i==0) or (i==len(KNOTS)-1):
            Include = True
        else:
            #do not include if the color is the same as the prior knot and its a new position
            if KNOTS[i][0]==KNOTS[i-1][0] and KNOTS[i][2]!=KNOTS[i-1][2]:
                Include = False
            #do not include if the color and position is the same as the next knot
            if KNOTS[i][0]==KNOTS[i+1][0] and KNOTS[i][2]==KNOTS[i+1][2]:
                Include = False
        if Include:
            Included.append(i)
            gradient.InsertKnot(KT[0], 1, KT[2], KT[3])

    #Add a new null and name it the same as the gradient
    newNull = c4d.BaseList2D(c4d.Onull)
    newNull.SetName(name)
    doc.InsertObject(newNull)

    #for R20+ only
    #the knots inserted do not have the saved gradient interpolation
    #so loop through and add them here
    gk = gradient.GetData(c4d.GRADIENT_KNOT)
    for i,l in enumerate(gk):
        l[1][c4d.GRADIENTKNOT_INTERPOLATION] = KNOTS[Included[i]][5]
    gradient.SetData(c4d.GRADIENT_KNOT,gk)

    #for R19
    #be aware that this will give incorrect interpolation for GIMP gradients
    #that may have different interpolations for each knot
    #gradient.SetData(c4d.GRADIENT_INTERPOLATION, KNOTS[0][5])

    #create a new base container for the gradient UserData
    bc = c4d.GetCustomDataTypeDefault(c4d.CUSTOMDATATYPE_GRADIENT)
    bc[c4d.DESC_NAME] = name
    #for R20+ only
    #change these properies to True to allow editing alpha
    bc[c4d.GRADIENTPROPERTY_ALPHA_WITH_COLOR] = True
    bc[c4d.GRADIENTPROPERTY_ALPHA] = True

    descid = newNull.AddUserData(bc)
    newNull[descid] = gradient
    c4d.EventAdd()

if __name__=='__main__':
    main()
