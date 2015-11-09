# -*- coding: utf-8 -*-
"""
Created on Tue Apr 09 22:25:26 2013

@author: ran110
"""

import httplib
import urllib
import inspect
import csv
import glob
import sys
import os
import getopt
import sqlite3
import hashlib
import platform
import logging 
from urlparse import urlparse


logging.basicConfig(level=logging.INFO)
l = logging.getLogger(__name__)

try:
    import rdflib
except ImportError:
    l.error("RDFLib module is required to run this script. It can be installed with")
    l.error("easy_install or pip. E.g. easy_install rdflib or pip install rdflib.")
    raise

#Setting global scope variables to respective default values
contentHeader = {"Content-Type": "application/x-turtle;charset=UTF-8"}
acceptHeader = {"Accept": "text/plain, */*;q=0.5"}
fileFormat = "n3"
failureList = ""

class CSVFileCleaner:
    '''Simple comment stripper to enable cleaning of CSVs'''
    def __init__ (self, file_to_wrap, comment_starts=('#', '//', '-- ')):
        self.wrapped_file = file_to_wrap
        self.comment_starts = comment_starts
    def next (self):
        line = self.wrapped_file.next()
        while line.strip().startswith(self.comment_starts) or len(line.strip())==0:
            line = self.wrapped_file.next()
        return line
    def __iter__ (self):
        return self

def checkHTTPresponse(response, userOk=200):
    if (response.status // 100 == 2):
        l.info("Ok - response = %s" % (response.status))
    elif (response.status == userOk):
        l.info("OK by user - response = %s, reason = %s" % (response.status, response.reason))
    else:
        l.error(response.status, response.reason)
        l.error(response.read())
        raise Exception("Failed HTTP interaction")

def createRepo(workbenchURI, repoID, repoTitleText):
    '''
    workbenchURI: the name of the workbench. ie - http://sirf-dev.csiro.au/openrdf-workbench
    repoName: the name of the repository. ie - RobATestRepo

1. http://sirf-dev.csiro.au/openrdf-workbench/repositories/NONE/create?Repository%20ID=test-id-create&Repository%20title=test-title-create&Triple%20indexes=spoc%2Cposc&type=native-rdfs-dt

Repository ID=create-id-test
Repository title=create-title-test
Triple indexes=spoc,posc
type=native-rdfs-dt
'''
    createParams = { 'Repository ID' : repoID,
                     'Repository title' : repoTitleText,
                     'Triple indexes' : 'spoc,posc',
                     'type' : 'native-rdfs-dt',
                    }
    host = urlparse(workbenchURI)[1]
    conn = httplib.HTTPConnection(host)
    conn.request("POST", workbenchURI+'/repositories/NONE/create?' + urllib.urlencode(createParams), '', acceptHeader)
    checkHTTPresponse(conn.getresponse(), 302)


def deleteRepo(repository):
    ''' DELETE /openrdf-sesame/repositories/mem-rdf '''
    host = urlparse(repository)[1]
    conn = httplib.HTTPConnection(host)
    conn.request("DELETE", repository, '', acceptHeader)
    checkHTTPresponse(conn.getresponse())


def createSingleNamespace(repository, prefix, uri):
    if prefix != "":
        host = urlparse(repository)[1]
        repo = urlparse(repository)[2]

        conn = httplib.HTTPConnection(host)
        conn.request("PUT", repo+"/namespaces/"+prefix, uri, acceptHeader)
        response = conn.getresponse()
        checkHTTPresponse(response)
    else:
        raise Exception("prefix can not be empty")

def cleanStart(repoFileName):
    '''
    Open up the file
    delete if existing
    create with DEFAULTS - not options in file....
    '''
    
    try:
        repoconfigfile = open(repoFileName, 'r')
        filelist = csv.DictReader(CSVFileCleaner(repoconfigfile))
    except IOError, e:
        l.error(e)
        raise Exception("Could not open '%s' file!" % deploymentFile)

    serverURI = "http://localhost:8080/openrdf-"
    remoteRepoList = getRepoList(serverURI+'sesame')

    for repo in filelist:
        l.info("found: %s [%s], IGNORING type: %s, options: %s" % (repo['id'], repo['title'], repo['type'], repo['options']))

        if repo['id'] in remoteRepoList:
            l.info("deleteing remote repo: %s" % repo['id'])
            deleteRepo(serverURI+"sesame/repositories/%s" % repo['id'])

        l.info("creating new repo: %s" % repo['id'])
        createRepo(serverURI+"workbench", repo['id'], repo['title'])

def getRepoList(serverURI):
    '''GET /openrdf-sesame/repositories HTTP/1.1
Host: localhost
Accept: application/sparql-results+xml, */*;q=0.5
'''
    host = urlparse(serverURI)[1]
    conn = httplib.HTTPConnection(host)
    conn.request("GET", serverURI+"/repositories", '', acceptHeader)
    response = conn.getresponse()
    checkHTTPresponse(response)
    return response.read()
     

def deleteAllNamespaces(repository):
    host = urlparse(repository)[1]
    repo = urlparse(repository)[2]

    conn = httplib.HTTPConnection(host)
    conn.request("DELETE", repo+"/namespaces", '', acceptHeader)
    response = conn.getresponse()
    checkHTTPresponse(response)
    
def deleteSpecificNamespace(repository, prefix):
    if prefix != "":
        host = urlparse(repository)[1]
        repo = urlparse(repository)[2]

        conn = httplib.HTTPConnection(host)
        conn.request("DELETE", repo+"/namespaces/"+prefix, '', acceptHeader)
        response = conn.getresponse()
        checkHTTPresponse(response)
    else:
        raise Exception("prefix can not be empty")


def clearRepo(repository, context):
    host = urlparse(repository)[1]
    conn = httplib.HTTPConnection(host)

    if context:
        ctxParam = { 'context': '<%s>' % context }
        repos = urlparse(repository)[2] + "?" + urllib.urlencode(ctxParam)
    else:
        repos = urlparse(repository)[2]

    l.info("Clearing repository '%s'..." % repos)

    conn.request("DELETE", repos, '', acceptHeader)
    
    response = conn.getresponse()
    checkHTTPresponse(response)

'''simple upload function'''
def upload(fileToUpload, headers, repository):
    host = urlparse(repository)[1]
    conn = httplib.HTTPConnection(host)
    filedata = open(fileToUpload, 'r').read()

    if urlparse(repository)[4]:
        conn.request("POST", urlparse(repository)[2]+'?'+urlparse(repository)[4], filedata, headers)
    else:
        conn.request("POST", urlparse(repository)[2], filedata, headers)
    response = conn.getresponse()
    checkHTTPresponse(response)


'''Query function. It supports only query written in turtle format.'''
def queryRepo(repository, context, query):
    host = urlparse(repository)[1]
    conn = httplib.HTTPConnection(host)

    if context:
        query = query.replace('%context%', 'GRAPH <%s>' % context)
    else:
        query = query.replace('%context%', '')

    params = {
        'query': query
    }
    headers = {
        'content-type': 'application/x-www-form-urlencoded',
        'accept': 'application/x-turtle;charset=UTF-8'
    }

    conn.request("POST", urlparse(repository)[2], urllib.urlencode(params), headers)
    response = conn.getresponse()
    checkHTTPresponse(response)

    return response.read()

'''Validate RDF file function'''
def isValidRDF(fileToValidate,fileFormat):
    try:
        l.info( "Validating '%s' detected fileFormat '%s'..." % (fileToValidate, fileFormat))
        g = rdflib.Graph()
        g.parse(fileToValidate, format=fileFormat)
        l.info("Ok")
        return True
    except Exception as e:
        l.error("Parsing error '%s'" % e)
        return False

'''Function to check if a file is new or modified.'''
def isNewOrModified(file, repository, deploymentFile):
    filePath = os.path.abspath(file)
    curChecksum = md5Checksum(filePath)

    con = sqlite3.connect(deploymentDBFile)
    with con:
        result = getFileDetailsInDB(file, repository, deploymentFile, con)
        if result:
            checksumInDB = result[1]
            if curChecksum == checksumInDB:
                return False;
            else:
                return True;
        else:
            return True

'''Helper function to retrieve file details from databasea'''
def getFileDetailsInDB(file, repository, deploymentFile, con):
    try:
        hostname = platform.node()
        filePath = os.path.abspath(file)

        cur = con.cursor()
        cur.execute("SELECT id, checksum FROM deployment WHERE hostname=:host AND source_file=:filePath AND repository=:repos AND deployment_file=:deploymentFile",
            {"host": hostname, "filePath": filePath, "repos":repository, "deploymentFile":deploymentFile})
        row = cur.fetchone()

        return row
    except sqlite3.Error, e:
        l.error("Get file details in database failed. Error: %s" % e.args[0])
        raise e

'''Function to create or update file checksum in database'''
def updateFileChecksumInDB(file, repository, deploymentFile):
    try:
        hostname = platform.node()
        filePath = os.path.abspath(file)
        curChecksum = md5Checksum(filePath)

        con = sqlite3.connect(deploymentDBFile)
        with con:
            cur = con.cursor()
            result = getFileDetailsInDB(file, repository, deploymentFile, con)
            if result:
                #Update existing record
                cur.execute("UPDATE deployment SET checksum=?, last_modified=datetime('now', 'localtime') WHERE id=?",
                    (curChecksum, result[0]))
            else:
                #Insert a new record
                cur.execute("INSERT INTO deployment (hostname, source_file, repository, deployment_file, checksum) VALUES (?, ?, ?, ?, ?)",
                    (hostname, filePath, repository, deploymentFile, curChecksum))
    except sqlite3.Error, e:
        l.error("Update file checksum in database failed. Error: %s" % e.args[0])
        raise

'''
Function to calculate the MD5 hash or checksum of a file.
Author: Joel Verhagen
Website: http://www.joelverhagen.com/blog/2011/02/md5-hash-of-file-in-python/
'''
def md5Checksum(filePath):
    with open(filePath, 'rb') as fh:
        m = hashlib.md5()
        while True:
            data = fh.read(8192)
            if not data:
                break
            m.update(data)
        return m.hexdigest()

'''Main processing loop'''
def process_deploy(reposBaseURI, deploymentFile):
    try:
        deploymentCsv = open(deploymentFile, 'r')
        filelist = csv.DictReader(CSVFileCleaner(deploymentCsv))
    except IOError:
        l.error("Could not open '%s' file!" % deploymentFile)
        raise

    for row in filelist:
        #Retrieve and massage the data before using...
        targetRepos = row["targetRepos"].replace('%REPOSURI%',reposBaseURI)
        tmpRepos = row["tmpRepos"]
        if tmpRepos is not None:
           tmpRepos = tmpRepos.replace('%REPOSURI%',reposBaseURI)
        targetCtx = row["targetContext"]
        tmpCtx = row["tmpContext"]
        clearTargetCtx = row["clearTargetContext"]
        if clearTargetCtx is not None:
            clearTargetCtx = clearTargetCtx.lower()
        clearTmpCtx = row["clearTmpContext"]
        if clearTmpCtx is not None:
            clearTmpCtx = clearTmpCtx.lower()
        filename = row["files"]

        # first see if filename is actually a subdirectory with its own deployment file...
        if os.path.isdir(filename):
            l.info( "Recursively processing directory '%s' " % filename)
            os.chdir(filename)
            if not os.path.exists(deploymentFile):
                l.warn("unable to locate deployment file %s - defaulting to %s" % ( deploymentFile, "deployment.csv" ))
                deploymentFile = "deployment.csv"
            process_deploy(reposBaseURI, deploymentFile)
            os.chdir("..")
            continue
        #Check to ensure only supported file format is processed.
        elif ( filename.endswith('.ttl') or filename.endswith('.n3') or filename.endswith('.nt') ) :
            contentHeader = {"Content-Type": "application/x-turtle;charset=UTF-8"}
            fileFormat = "n3"
        elif filename.endswith('.rdf'):
            contentHeader = {"Content-Type": "application/rdf+xml"}
            fileFormat = "xml"
        else:
            l.warn("File not found or format not supported '%s'" % filename)
            continue

        #Download external rdf or ttl file (wildcard not supported).
        #TODO: This should probably be done in a function of its own.
        if filename.startswith('http'):
            #Download and store external file in current working directory.
            try:
                l.info("Downloading external file '%s'..." % filename)
                filehandle = urllib.urlopen(filename)
                filename = "%s" % os.path.basename(urlparse(filename)[2])
                output = open(filename,'wb')
                output.write(filehandle.read())
                filehandle.close()
                output.close()
                l.info("Ok")
            except IOError:
                l.warn("External file download failed %s" % filename)
                continue
#            finally:
          
            #Overwrite targetRepos and targetContext if tmpRepos is provided.
            if tmpRepos:
                targetRepos = tmpRepos
                targetCtx = tmpCtx
                clearTargetCtx = clearTmpCtx

        l.info("Looking for '%s' on disk..." % filename)
        filesToFind = glob.glob(filename)
        if filesToFind :
            l.info("Found '%s'" % filesToFind)
        else:
            l.warn("\nFailed to find '%s'" % filename)
            global failureList
            failureList = failureList + filename + ' '

        #Upload data file(s) content into targetRepos.
        clearRepoExecutedOnce = False
        for match in filesToFind:
            if pauseFlag :
                raw_input("Press Enter to continue...")               
            l.info("Reading '%s'..." % match)
            if forceLoad or isNewOrModified(match, targetRepos, deploymentFile):
                #Clean up target repository before uploading data file content (run once).
                if ((clearTargetCtx == "true") and (not clearRepoExecutedOnce)):
                    clearRepo('%s/statements' % targetRepos, targetCtx)
                    clearRepoExecutedOnce = True

                #Upload the data if its content is valid.
                if isValidRDF(match, fileFormat):
                    l.info("Uploading dataset '%s' into '%s' inside '%s'..." % (match, targetRepos, targetCtx))
                    if targetCtx:
                        upload(match, contentHeader, '%s/statements?context=<%s>' % (targetRepos, targetCtx))
                    else:
                        upload(match, contentHeader, '%s/statements' % (targetRepos))
                    updateFileChecksumInDB(match, targetRepos, deploymentFile)
                else:
                    l.error("Uploading skipped. Not a valid RDF file '%s'." % match)
            else:
                l.info("Uploading skipped. File content hasn't been changed since last upload.")

        #Do post-processing if a post-processing csv file is provided.
        postProcFile = row["postProcFile"]
        if postProcFile.endswith('.csv'):
            try:
                l.info("--- Run '%s' post-processing workflow '%s' ---" % (filename, postProcFile))
                doPostProcessing(targetRepos, tmpRepos, tmpCtx, postProcFile)
                l.info("Post-processing workflow successfully run.")
            except Exception as e:
                l.error("--- Post-processing failed '%s' ---" % e)
                continue
        else:
            l.info("No post-processing workflow found.")

'''Post processing function'''
def doPostProcessing(targetRepos, tmpRepos, tmpCtx, postProcFile):
    try:
        postProcCsv = open(postProcFile, 'r')
        filelist = csv.DictReader(CSVFileCleaner(postProcCsv))
    except IOError:
        raise

    for row in filelist:
        #Retrieve and massage the data before using...
        filename = row["rqInFile"]
        targetContext = row["targetContext"]
        rqCtx = row["rqContext"]
        targetCtx = row["targetContext"]
        rqOutFile = row["rqOutFile"]
        clearTargetCtx = row["clearTargetContext"].lower()

        if filename.endswith('.rq'):
            #Run the query against tmpRepos if it is provided
            if tmpRepos:
                queryRepos = tmpRepos
            else:
                queryRepos = targetRepos
            l.debug( "queryRepos '%s'" % queryRepos)

            l.debug("Looking for '%s' on disk..." % filename)
            filesToFind = glob.glob(filename)

            #Clean up target repository before uploading inferred/filter data file content.
            if filesToFind:
                l.info("Found '%s'" % filesToFind)
                if clearTargetCtx == "true":
                    clearRepo('%s/statements' % targetRepos, targetCtx)

            for match in filesToFind:
                l.info("Reading '%s'..." % match)

                #Run the query file and store its results in a data output file.
                try:
                    queryStr = open(match, 'r').read()
#                   result = queryRepo(queryRepos, rqCtx, queryStr[6:])
                    result = '\n'.join(queryRepo(queryRepos, rqCtx, queryStr[6:]).splitlines())
					
                    fo = open(rqOutFile,"w")
                    fo.writelines(result)
                finally:
                    fo.close()

                #Upload inferred/filtered dataset in turtle format into targetRepos.
                contentHeader = {"Content-Type": "application/x-turtle;charset=UTF-8"}
                if row["rqOutFileLoad"].lower() == "true":
                    l.info( "Uploading inferred/filtered dataset '%s' into '%s' inside '%s'..." % (rqOutFile, targetRepos, targetContext))
                    if targetContext:
                        upload(rqOutFile, contentHeader, '%s/statements?context=<%s>' % (targetRepos, targetContext))
                    else:
                        upload(rqOutFile, contentHeader, '%s/statements' % (targetRepos))
                else:
                    l.warn("Inferred/filtered dataset '%s' not loaded." % rqOutFile)

            #Clean up temporary repository.
            if tmpRepos:
                clearRepo('%s/statements' % tmpRepos, tmpCtx)
        else:
            l.warn("Post processing file format not supported '%s'." % filename)
            continue

def main(argv):
    l.info('deployment.py version $Revision: 2045 $')
    #Setting properties default values which can be overwritten by user parameters
    reposBaseURI = "http://localhost:8080/openrdf-sesame/repositories"
    deploymentFile = 'deployment.csv'
    global deploymentDBFile
    deploymentDBFile = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))) + os.sep + "deployment.db"
    defReposWarning = True
    global forceLoad
    forceLoad = False    
    global pauseFlag
    pauseFlag = False    
 
    try:
        opts, args = getopt.getopt(argv, "hr:f:d:p:i", ["reposBaseURI=", "file=", "dbfile=","pause","ignore"])
    except getopt.GetoptError:
        l.error('deployment.py -r <repository> -f <csvfile> -d <dbfile>')
        raise

    for opt, arg in opts:
        if opt == '-h':
            print 'deployment.py -r <repository> -f <csvfile> -d <dbfile> -i'
            return
        elif opt in ("-r", "--reposBaseURI"):
            reposBaseURI = arg
            defReposWarning = False
        elif opt in ("-f", "--file"):
            deploymentFile = arg
        elif opt in ("-i", "--ignore"):
            forceLoad = True
        elif opt in ("-p", "--pause"):
            pauseFlag = True
        elif opt in ("-d", "--dbfile"):
            deploymentDBFile = arg
#       elif opt in ("-c", "--clear"):
#            clearAll = true

    l.info("reposBaseURI: %s" % reposBaseURI)
    l.info("deploymentFile: %s" % deploymentFile)
    l.info("deploymentDBFile: %s" % deploymentDBFile)

    #Performs necessary validations and display user warning before we proceed...
    if not(reposBaseURI.startswith("http")):
        raise Exception("Sesame's base repositories URI is invalid. Example valid URI: http://hostname:port/openrdf-sesame/repositories")

    if defReposWarning and pauseFlag :
        l.warn("\nDefault repositories base URI is used. Data will be loaded into repositories on localhost.")
        raw_input("Press Enter to continue...")

    try:
        #Creates deployment database for tracking of file content changes.
        con = sqlite3.connect(deploymentDBFile)
        with con:
            con.execute('''CREATE TABLE IF NOT EXISTS deployment
                (id             INTEGER     PRIMARY KEY AUTOINCREMENT,
                hostname        TEXT        NOT NULL,
                source_file     TEXT        NOT NULL,
                repository      TEXT        NOT NULL,
                deployment_file TEXT        NOT NULL,
                checksum        TEXT        NOT NULL,
                last_modified   DATETIME    DEFAULT (datetime('now','localtime')),
                UNIQUE(hostname, source_file, repository, deployment_file));''')

        process_deploy(reposBaseURI, deploymentFile)
        
        l.warn('Failures:')
        l.warn(failureList)

    except Exception as e:
        l.error(e)
        raise e

def testBunchOfCommands(TestCase):
    deleteRepo("http://localhost:8080/openrdf-sesame/repositories/TerryRTestRepo")
    createRepo("http://localhost:8080/openrdf-workbench", 'TerryRTestRepo', 'some text label')

    createSingleNamespace("http://localhost:8080/openrdf-sesame/repositories/TerryRTestRepo", "mmm", "http://www.example.com")
    deleteSpecificNamespace("http://localhost:8080/openrdf-sesame/repositories/TerryRTestRepo", "mmm")

    createSingleNamespace("http://localhost:8080/openrdf-sesame/repositories/TerryRTestRepo", "mmm", "http://www.example.com")
    createSingleNamespace("http://localhost:8080/openrdf-sesame/repositories/TerryRTestRepo", "bbb", "http://www.example.com")
    createSingleNamespace("http://localhost:8080/openrdf-sesame/repositories/TerryRTestRepo", "ccc", "http://www.example.com/ccc")
    deleteAllNamespaces("http://localhost:8080/openrdf-sesame/repositories/TerryRTestRepo")

    cleanStart("repo-config.csv")


if __name__ == "__main__":
    main(sys.argv[1:])
