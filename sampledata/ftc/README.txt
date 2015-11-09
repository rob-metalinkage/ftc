Feature Type catalog loading environment

Domain Models are OWL encodings, typically from UML Application Schema using ISO 19150 (draft) rules  

The Feature Type Catalog has specific requirements regarding the context each model is loaded into.

post-processing is used to infer a graph that can be easily presented via the FTC API.

SIRF models are the default dev environment, for the auto-deploy capabilities for SIRF infrastructure

ftc-common is a base model set for all FTC instances, containing key owl, ISO librarys, void metamodel etc.
ogc-lib is the OGC model baseline comprising mainly the iso model libraries. This library is intended to support domain models using a common domain model pattern, typically Observations and Measurements.
sirf-models contain domain models needed for object and attribute definitions for the common SIRF environment
other models are grouped pragmatically according to the testing and publishing regime (project based) and may be refactored as status changes.



