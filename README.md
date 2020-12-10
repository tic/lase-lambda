# LASE Lambda functions
This repository contains the lambda functions and velocity templates used by the LASE API.

### Primary Lambda Functions
Primary API endpoints are all handled by the same lambda function, located in `/main-lambdas`. Here is a quick rundown of what is in each file:

| File  | Purpose
| :------------|:------------
| `errors.py`       | Contains generic error messages which are returned by the lambda function when bad things happen.  |
| `lambda_function.py` | Main file where the magic happens. |
| `ObjectConverter.py` | Contains helper functions for converting the arrays which SQL queries return into clean and easy to understand objects for the API to return. |
| `QueryManager.py` | Constructs SQL queries from the various API inputs. |
| `requirements.txt` | Pip-formatted list (`pip freeze`) of packages which need to be installed when running locally, or included in the zip when uploading to AWS. |
| `run.py` | An example of how the lambda function could be run locally to test. |
| `keys.py` | Not included in the repository for security reasons. The keys file contains all login information. The format for this file is simply `variable = 'string'` for each of the variables imported on line 7 of `lambda_function.py`.  |


#### Prerequisites
* The main lambda function requires the `PyMySQL` python package. As of writing this, it is only available for Python 2.7, thus the rest of the function code is also written in this version of Python.
* A control block must be written and included in the integration request mapping template for endpoints using the main lambda function. Specifications for this control block can be found below in the Velocity Control Block section.
* Everything here was created using AWS. The code could be adapted for other platforms, but YMMV.

### STO Lambda Function
STO generation for LASE essentially refers to the creation of a machine readable recipe based on a set of input arrays. The file which done recipe generation was originally built for manual usage in a command line, so this was adapted by repurposing Python's default print function.

#### Prerequisites
* STO Generation is done in Python 3.7.
* In `/sto-lambda` a velocity template for the integration request of the endpoint is provided. It ensures that each unput is valid (an array). It is not *necessarily* required, but the lambda and generator files have relatively little capability to handle errors.


### Velocity Control Block
All endpoints which utilize the generic lambda function must provide a control block in the mapping template for the endpoint's integration request. Examples of control blocks of every endpoint used by LASE and where to put the control block can be found in `/vtl`.

Below, you will find some brief documentation on the different keys within the control block, including how they are used and ways you can use them to achieve the desired lambda functionality.

**Note:** User inputs should be properly escaped in `/main-lambdas/QueryManager.py`. Escaping user input does not need to be considered in the velocity template.

| Key            | Used In | Type   | Function            |
|:---------------|:--------|:-------|:--------------------|
| `method`       | ALL     | string | Determines which of the main lambda sections is used to handle the request. |
| `table`        | GET+DEL | string | Controls which table the operation will be conducted on. Some control blocks use "$tbl" for this, which the template will replace with a path parameter called "substrate". This can be hard-coded or populated at runtime depending on what you need to do, providing the appropriate changes to the velocity template are made. |
| `machine`      | ALL     | string | Similar to `table`, this control which database the request will use. If hard-coded to "user_given", the lambda will search for a path parameter called "machine" to use for this value. |
| `returnKey`    | GET     | string | The response object served by the API contains the requested information under a certain dictionary key, which is configured using this value. |
| `source`       | GET     | string | Selects the conversion function used to convert the array returned from the internal SQL query to the JSON object returned by the API. Options for conversion functions are located at the bottom of `/main-lambdas/ObjectConverter.py`. |
| `queryFilters` | GET     | bool   | Whether or not the lambda should listen to any querystring parameters that were provided. If set to true, querystring arguments are automatically applied as filters to the backend SQL query. |
| `singleItem`   | GET     | bool   | By default, backend SQL search results are brought back as an array. If only a single item is expected, set this key to true and the first array element will be the only thing that is returned, instead of single element arrays. |
| `pathParams`   | GET     | array  | Array of strings where each string is the name of the path parameter the lambda function should consider. You should *not* include path parameters the lambda function already knows to look for, such as "machine", "substrate", etc. if the other keys have been set to values which indicate such a path parameter is present. In other words, this key would be `[]` in the event that "user_given" is supplied to `machine` or "$tbl" is used by the `table` key. |
| `fields`       | PUT     | array  | Explains how to read the data contained within the body of a given PUT request. See below for some documentation on the format of entries into this array. |
| `key`          | DELETE  | string | Controls which table column is used to isolate items for deletion. Most tables use `id`, but this can be changed to match whatever table is being operated on. |

#### Entries in the `fields` array
Each entry in the `fields` array is an object containing certain keys. Documentation on these keys is found below. The order of entries in this array is important, as they are "executed"/"read" in order. See the description of the `master` key for more information.
**Reminder:** `fields` is only used by PUT requests. It will be ignored by any other handlers.

| Key           | Type   | Function |
|:--------------|:-------|:---------|
| `name`        | string | Name of the key used to find the insertion data in the body of the PUT request. |
| `table`       | string | Controls which table the data should be inserted into. |
| `type`        | string | Accepts "single" or "list". If this particular field only contains a single item, use "single", but if multiple rows of data are being submitted at once via an array, "list" is the way to go. |
| `independent` | bool   | If an entry is independent, it does not need any information from other insertions to be carried out. If this is set to false, the ID of the master entry will be supplied as a value to the column named by the `link_fk` key. |
| `link_fk`     | string | Sets the name of the column where foreign keys are linked in dependent entries. If `independent` is true, this key may be omitted. |
| `master`      | bool   | If an entry is designated as the master, subsequent field entries marked as dependent will be supplied the insertion ID of this item. This is why the order of entries in the `fields` array is important -- they should be placed in an order such that the relevant master entries are followed by any dependent insertions. |

<sup>This markdown file was tested using [pandao's](https://github.com/pandao) online [markdown editor](https://pandao.github.io/editor.md/en.html).</sup>
