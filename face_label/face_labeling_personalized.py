import os
import skimage.io as io
from camera import test_camera
from camera import take_picture
import numpy as np
from dlib_models import load_dlib_models
load_dlib_models()
from dlib_models import models
face_detect = models["face detect"]
face_rec_model = models["face rec"]
shape_predictor = models["shape predict"]

tooManyString = "Too many faces"
noMatchString = "I don't know"


#this is a terrible hack
def numsfromrect(k):
    """ Given a rectangle k will return x1,y1,x2,y2 of k

    Parameters
    ----------
    k: rectangle to get data from
    
    Returns
    -------
    list [x1,y1,x2,y2]
    """
    return list(map(int,str(k).replace('(','').replace('[','').replace(')','').replace(']','').replace(',','').split(' ')))

def get_desc(img):
    """
    Get a single face description from a pic.
    Returns -1 if there isn't exactly one face.
    
    Used for loading images and labels to avoid bad data.

    Parameters
    ----------
    img: image to get face from
    """
    k=face_detect(img)
    if len(k)!= 1:
        print("Wrong number of faces detected.")
        return -1
    shape=shape_predictor(img,k[0])
    descv = face_rec_model.compute_face_descriptor(img,shape)
    return np.array(descv)

def eucd(vect1,vect2):
    """ Euclidian distance of two vectors.

    Parameters
    ----------
    vect1: first vector
    vect2: second vector
    
    Returns
    -------
    the distance between them
    """
    return np.sqrt(((vect1-vect2)**2).sum())

def descriptions(img):
    """
    Given an image will return the list of descriptions of faces in it.

    Parameters
    ----------
    img: the image to get all descriptions from
    
    Returns
    -------
    list of face descriptors
    """
    faces=face_detect(img)
    lst = []
    for k in faces:
        shape=shape_predictor(img,k)
        descv = face_rec_model.compute_face_descriptor(img,shape)
        lst.append(descv)
    return np.array(lst)
def loadDBimgs(dirt,splt='\\'):
    """
    Loads a db from directory dirt.
    Dirt must be formated like such:
    Folders with names of the desired labels (ie: 'Daschel Cooper')
    Within them .jpg files.
    They will converted to numpy arrays when loaded.
        
    splt = \ in windows
         = / in mac
    splt is currently not used, but if errors are encountered it can be useful
    """
    lstOfDirs = [x[0] for x in os.walk(dirt)][1:]
    splt = os.sep
    db = []
    
    for rootDir in lstOfDirs:
        print(rootDir)
        fileSet = set()

        

        for dir_, _, files in os.walk(rootDir):
            for fileName in files:
                relDir = os.path.relpath(dir_, rootDir)
                relFile = os.path.join(rootDir, fileName)
                if not fileName.startswith('.'):
                    fileSet.add(relFile)
        for file in fileSet:
            img_array = io.imread(file)
            name = rootDir.split(splt)[1]
            db.append((descriptions(img_array)[0], name))
    
    return db

def findMatch(d, db,conf=0.6):
    """ Match a face descriptor with name in a database

    Parameters
    ----------
    d: face vector to match
    db: database of face vectors
    conf: the distance d must be before it is considered a match
    
    Returns
    -------
    the name or a default string for too many matches
    """
    if type(d) == int and d == -1:
        return tooManyString
    dists = []
    for i in db:
        dists.append(np.linalg.norm(d-i[0]))
    b = np.argmin(dists)
    print(np.min(dists))
    if(dists[b] < conf):
        print(db[b][1],dists[b])
        return db[b][1]
    else:
        return noMatchString
def label_faces_text(img,db):
    """ returns text describing the faces seen
    Parameters
    ----------
    img: the image with faces to be described
    db: the database with which to match the faces
    
    Returns
    -------
    a string labeling the faces
    'I see john, pual, and 2 people I don't know'
    """
    upscale = 1

    detections = face_detect(img, upscale)  # returns sequence of face-detections
    detections = list(detections)
    names = []
    for det in detections:
        # bounding box dimensions for detection
        shape = shape_predictor(img, det)
        descriptor = (np.array(face_rec_model.compute_face_descriptor(img, shape)))
        text = findMatch(descriptor, db)
        names.append(text)
    if len(names) == 0:
        return "I see no one."
    else:
        alexasay = "I see "
        numUnk = 0
        first = True
        for name in names:
            if name == "I don't know":
                numUnk += 1
            else:
                if first:
                    alexasay += name
                    first = False
                else:
                    alexasay += ", $ " + name 
        if numUnk == len(names):
            return "I see " + str(numUnk) + " people I don't know."
        if numUnk != 0:
            if numUnk != 1:
                alexasay += " $ " + str(numUnk) + " people I don't know."
            else:
                alexasay += " $ " + str(numUnk) + " person I don't know."
        if len(names) > 1:
            alexasay = rreplace(alexasay,"$",'and',1)
        alexasay = alexasay.replace('$', '')
        return alexasay
def rreplace(s,old,new,occurence):
    """ replace instances in a string stating from the back

    Parameters
    ----------
    s: the string to work with
    old: the substring to replace
    new: what to replace old with
    occurence: how many times to replace

    
    Returns
    -------
    a string with the last 'occurence' instances of 'old' replaced with 'new'
    """
    li = s.rsplit(old,occurence)
    return new.join(li)

def saveDBnp(dirt,db,splt='\\'):
    """
    Saves a db to directory dirt.
    
    splt = \ in windows
         = / in mac
    splt is not used at the moment
    """
    it = 0
    prevname = db[0][1]
    for entr in db:
        ray, name = entr[0],entr[1]
        if name != prevname:
            prevname = name
            it = 0
        direc = os.path.join(dirt , name)

        if not os.path.exists(direc):
            os.makedirs(direc)
            
        
        direc = os.path.join(direc , "vct" + str(it))
            
        np.savez(direc,ray=ray)
        it = it + 1
        
def loadDBnp(dirt,splt = '\\'):
    """
    Loads a db from directory dirt.
    Dirt must be formated like such:
    Folders with names of the desired labels (ie: 'Daschel Cooper')
    Within them .npz files storing arrays named 'ray'
        (this naming and format is done automatically by saveDBnp)
        
    splt = \ in windows
         = / in mac
    splt is not used at the moment
    """
    import skimage.io as io
    import os
    splt = os.sep
    lstOfDirs = [x[0] for x in os.walk(dirt)][1:]
    
    db = []
    
    for rootDir in lstOfDirs:
        print(rootDir)
        fileSet = set()

        

        for dir_, _, files in os.walk(rootDir):
            for fileName in files:
                relDir = os.path.relpath(dir_, rootDir)
                relFile = os.path.join(rootDir, fileName)
                if not fileName.startswith('.'):
                    fileSet.add(relFile)
                    
        for file in fileSet:
            vector = np.load(file)['ray']
            name = rootDir.split(splt)[1]
            db.append( (vector , name) )
    
    return db

def addImgToDB(db,img,label,dirt):
    """ Adds the face vector in img with label 'label' to db

    Parameters
    ----------
    db: database of faces to work with
    img: image with a face
    label: the label to apply to the face, in most applications the name of the person
    dirt: the directory to save the database to
    
    Returns
    -------
    either a success string or failure string
    """
    desc = get_desc(img)
    if np.isscalar( desc ) == -1:
        print("error")
        return "Failed to identify a singular face."
    db.append( (desc,label) )
    saveDBnp(dirt,db)
    return "Successfuly added to database."