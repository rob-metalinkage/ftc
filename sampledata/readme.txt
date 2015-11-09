DEPLOYMENT.PY README

Overview
--------

The main purpose of this script is to simplify the loading of RDF datasets/vocabularies into a triplestore. It can be manually run or used in conjunction with Jenkins CI server to automatate it execution.

Prerequisite
------------

You need the following software installed to run the deployment script:
1. Python 2.7
2. rdflib 4.0.1 module (https://github.com/RDFLib/rdflib)

Usage notes
-----------

1. It can be run without any argument and in that case, a local repository will be used.

   E.g.:   
   python deployment.py

2. It can be run with a single argument i.e. the target repository argument.

   E.g.:   
   python deployment.py http://hostname:port/openrdf-sesame/repositories

3. Regardless of how it is run, the deployment script requires 'deployment.csv' file present in the directory where the script is run.

4. The 'deployment.csv' has the following file structure:
   a. header (fields separated by comma)
   b. body/content (data files with their respective repository related configuration and post-processing file)

   E.g.:
   files,targetRepos,targetContext,clearTargetContext,tmpRepos,tmpContext,clearTmpContext,postProcFile
   void.ttl,%REPOSURI%/sirf-datanetwork,http://vocab.deri.ie/void,true,,,,none
   lid_metamodel.ttl,%REPOSURI%/sirf-datanetwork,http://def.seegrid.csiro.au/def/lid,true,,,,none
   sirf_metamodel.ttl,%REPOSURI%/sirf-datanetwork,http://def.seegrid.csiro.au/def/sirf,true,,,,none
   http://localhost/files/misc_lod.ttl,%REPOSURI%/sirf-datanetwork,http://id.sirf.net/other,true,,,,none
   ahgf_demo.ttl,%REPOSURI%/sirf-datanetwork,http://115.146.86.108/id/geo/ahgf_hrc/,true,,,,postdeployment1.csv
   http://example.com/demo1.rdf,%REPOSURI%/sirf-datanetwork,na,na,%REPOSURI%/tmp,http://id.sirf.net/siset/tmp1/,true,none
   http://localhost/files/demo2.ttl,%REPOSURI%/sirf-datanetwork,na,na,%REPOSURI%/tmp,http://id.sirf.net/siset/tmp2/,true,postprocessing2.csv

5. The following provides detailed description of each header field in 'deployment.csv' file:

   files 
   - Local or remote RDF files to be loaded into target repository.
   - Currently only support RDF file in ttl and rdf/xml formats.
   - Wildcard can be used for local file. It is not supported for remote file.
   - Remote RDF file needs to be specified as an HTTP/HTTPS URL.

   targetRepos 
   - The URL of an openrdf-sesame or triplestore repository where the data is to be loaded.
   - An environment variable called %REPOSURI% can be used in conjunction with specifying the repository location. 
     It is set via an OS environment variable or through an argument when running 'deployment.py' script.

   targetContext 
   - A namespace or context in the repository where the data is to be loaded.
   - If this is not specified, data will be loaded into root namespace.

   clearTargetContext 
   - A boolean flag to indicate whether the data stored in the targetContext is to be cleared before loading the data file.
   - PLEASE BE AWARE that if targetContext is not specified, all data contents in the targetRepos will be cleared.

   tmpRepos (only applicable for remote RDF file)
   - A temporary openrdf-sesame or triplestore repository for storing external RDF file content.
   - It is intended to be used as an intermediary storage for further data massaging before loading the massaged 
     data into target repository.

   tmpContext (only applicable for remote RDF file)
   - A namespace or context in the temporary repository where the data is to be loaded.
   - The data stored in tmpContext will be cleared if and only if (a) the data file has a post-processing job and 
     (b) the job has successfully been executed.

   clearTmpContext (only applicable for remote RDF file)
   - A boolean flag to indicate whether the data stored in the tmpContext is to be cleared before loading external
     data file content into it.
   - PLEASE BE AWARE that if tmpContext is not specified, all data contents in the tmpRepos will be cleared.

   postProcFile 
   - A post-processing csv file which contains one or more 'rq' files to be executed for loading inferred or 
     massaged datasets into target repository.
   - It needs to be ended with '.csv' file extension otherwise it won't be executed.
   - None can be specified as its value if the data file doesn't have a post-processing requirement.
  
6. Can a remote RDF file be loaded directly into a target repository?

   Yes. To do this, leave tmpRepos, tmpContext and clearTmpContext fields blank. In addition, regardless of whether a remote
   RDF file  will be directly loaded a target repository or into a temporary repository, a remote RDF file will be downloaded
   into a local working directory.

   E.g.
   files,targetRepos,targetContext,clearTargetContext,tmpRepos,tmpContext,clearTmpContext,postProcFile
   http://localhost/files/misc_lod.ttl,%REPOSURI%/sirf-datanetwork,http://id.sirf.net/other,true,,,,none

7. Is there a data validation function to ensure data being loaded is of good quality?
 
   Yes. The RDF data file/content will be parsed to ensure its validity. If the parsing failed, the data file content won't be loaded into the repository.

8. The post-processing csv file has the following file structure:
   a. header (fields separated by comma)
   b. body/content

   E.g.:
   rqInFile,rqContext,rqOutFile,targetContext,clearTargetContext,rqOutFileLoad
   infer_features_1.rq,,infer_features_1.ttl,http://def.seegrid.csiro.au/def/lid/inferred,true,true
   infer_features_1.rq,,infer_features_1a.ttl,http://def.seegrid.csiro.au/def/lid/inferred,false,true
   infer_features_1.rq,,infer_features_1b.ttl,http://def.seegrid.csiro.au/def/lid/inferred,false,true
   infer_features_2.rq,,infer_features_2.ttl,http://def.seegrid.csiro.au/def/lid/inferred,false,true
   infer_formats.rq,,infer_formats.ttl,http://def.seegrid.csiro.au/def/lid/inferred,false,true
   infer_formats_1.rq,,infer_formats_1.ttl,http://def.seegrid.csiro.au/def/lid/inferred,false,true

9. The following provides detailed description of each header field in post-processing csv file:

   rqInFile
   - An ASCII file that contains SPARQL query. The SPARQL query needs to be assigned to a property named 'query'.

     E.g.
     query=PREFIX void:<http://rdfs.org/ns/void#>
     PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
     PREFIX rdfs:<http://www.w3.org/2000/01/rdf-schema#>
     PREFIX owl:<http://www.w3.org/2002/07/owl#>

     CONSTRUCT { 
         ?s void:feature ?f  
     }
     WHERE {
        %context% {
            ?s a void:Dataset .
            ?p void:subset+ ?s .
            ?p void:feature ?f .
        }
     }

   rqContext
   - A namespace or graph in which the SPARQL query is to be executed against. 
   - Its value will be made available in 'rq' file as a variable named %context%.

   rqOutFile
   - An output file that stores the results of SPARQL query in turtle/ttl format.

   targetContext
   - A namespace or context in target repository (specified in deployment.csv file) where 
     the content of rqOutFile is to be loaded.

   clearTargetContext
   - A boolean flag to indicate whether the data stored in the targetContext is to be cleared 
     before loading the rqOutFile content.
   - PLEASE BE AWARE that if targetContext is not specified, all data contents in the 
     targetRepos will be cleared.

   rqOutFileLoad
   - A boolean flag to indicate whether the rqOutFile content is to be loaded into targetContext.
 
10. How is 'deployment.py' script being used in Jenkins?

    The shell script demonstrates how the it is being in Jenkins:

    for csvFile in `find . -iname "deployment.csv" -print | sort`; 
    do 
        echo "Found deployment.csv in $csvFile"
        folder=$(basename $(dirname $csvFile))
        dirname=$(dirname $csvFile)
        workspace=`pwd`
        echo "The dirname is $dirname"
        echo "The folder is $folder"
        echo "The workspace is $workspace"

        cd $dirname
        python $workspace/deployment.py
        cd $workspace
    done