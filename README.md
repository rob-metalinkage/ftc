# Feature Type Catalog Linked Data API

status: this is a development spike that may be revived at some future time - but may be made irrelevant by an alternative frame-based approach to data modelling in RDF such as SHACL

Implements convenience APIs to access ontologies describing "Feature Types" - i.e. models for spatial objects.

The FTC API allows clients to access definitions described using OWL formalisms, without dealing with the complexities and depth of OWL syntax and inheritance patterns. 

A key feature of the FTC is to discover relationships between Feature Types "mapped" to a standard definition. This allows discovery of heterogeneous implementations (as exist in the "real web") given a concept.

It extends a more basic FTC published under the SIRF project by CSIRO - and adds support for two key additional requirements:
1) Ability to publish a pure OWL/RDF model, without dependencies on the full ISO harmonised model
2) Support for the canonical version of the ISO model

This implementation uses the patterns and some default resources for deploying ELDA configurations provided by CSIRO as part of the SISSVOC vocabulary service. https://github.com/jyucsiro/sissvoc

For compatibility it uses the same LGPL licence.

Sample data includes mappings between the HY_Features hydrology model and various hydrology data sets exposed via web service interfaces.

This work is provided by Rob Atkinson (Metalinkage.com.au)  as a contribution to the OGC Geosemantics, Spatial Data on the Web and Hydrology Domain Working Group activities.

The intention is to provide this functionality as an upgrade to the SIRF software suite once its planned Open Source release takes place. In the meantime it provides a fully functional capability and represents the place where best practices can be developed and tested.

Contributions welcome - contact rob <at> metalinkage.com.au
