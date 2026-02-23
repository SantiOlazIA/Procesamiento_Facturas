---
description: Analyze any type of similar entry (e.g. sales reports), ask clarifying questions to the user about data paths/formats, and create a similar file as a result.
---
When the user asks to analyze the Vtas CW pipeline or a similar sales report entry:

1. Request that the user identify exactly which file(s) they want to process. Do not proceed until you have the explicit file paths.
2. Read a sample of the input file(s) to carefully observe the format, structure, columns, and data types (e.g., old vs new formats, dates, rates).
3. Search the data to identify the IVA condition (e.g., Responsable Inscripto, Monotributista) and then ask the user for confirmation that this detected condition is correct. 
4. Use this confirmed IVA condition to detect strange data (for example, if a verified Responsable Inscripto has "Facturas C" in the sales section, flag that as an anomaly).
5. Identify any unclear paths, mappings, missing information, or variables that need clarification to perform the transformation accurately.
6. If there are ambiguities, missing information, or anomalies (like the IVA condition mismatch), ask the user specific questions about how the data should be handled or what the expected output columns are. Wait for their confirmation before proceeding.
7. Once fully clarified, process the entry data and create a similar consolidated file or dashboard report, either by directly processing the data or generating a python script matching the output requirements.
