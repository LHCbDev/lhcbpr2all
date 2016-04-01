# CERN ROOT's http server in python

This web server returns objects from **ROOT** files in **json** format
## Install
### Prerequisites
1. PYTHONPATH environment variable should contain path to ROOT lib directory
2. Python's major version should be the same as used for ROOT compilation

### Virtualenv
```sh
$> virtualenv venv
$> source venv/bin/activate
$> pip install -r requirements.txt
```
## Run
From application's folder:
```sh
$> python run.py
```

By default the application runs with environments loaded from `envs/default.env`. You can change it by setting the enveronments' file in ENV environment. For example:
```
$> ENV=default python run.py # Will load env/default.env
$> ENV=production python run.py # Will load env/production.env
```

### Configuration

The application configured through envirnment variables (see the section above). Default configuration:

```
ROOT_DATA=data
FLASK_PORT=8081
FLASK_HOST=0.0.0.0
DEBUG=True
```

* ROOT_DATA --- path to the root directory with ROOT files.
* FLASK_PORT and FLASK_HOST --- port and host for the web server
* DEBUG --- on/off debug mode

## Usage

### Args: 
* **files**: [REQUIRED] list of root files to be processed.
* **items**: list of objects that need to be retrieved; first uses the *Get* function
             to retrieve it, if fails uses *FindObjectAny*, if fails again returns *None*.
* **folders**: list of directories to be parsed (NB It is not recursive). 

### Returns "result", a list of dictionaries (one per file) with:
* **root**: the filename processed
* **items**: a dictionary with all the processed items.
* **trees**: a dictionary with all the processed paths. For each path there are two lists: 
    * **folders**: sorted list of sub-directories Titles
    * **objects**: sorted list of objects Names


## Request example

```
/?files=file1,file2,file3&items=item1,item2
```

## Response example
```json
{
  "result": [
    {
      "items": {
        "item1": {
          "_typename": "TGraph",
          ...
        },
        "item2": {
          "_typename": "TGraph",
          ...
        }
      },
      "root": "file1"
    },
    {
      "items": {
        "item1": {
          "_typename": "TGraph",
          ...
        },
        "item2": {
          "_typename": "TGraph",
          ...
        }
      },
      "root": "file2"
    }
  ]
}
```

## Request example

```
/?files=file1,file2&items=item1,path/item2&folders=path1,path2
```

## Response example
```json
{
  "result": [
    {
      "items": {
        "item1": {
          "_typename": "TH2D",
          ...
        },
        "path/item2": {
          "_typename": "TGraph",
          ...
        }
      },
      "root": "file1"
      "trees": {
        "path1": {
          "folders": [...], 
          "objects": [...]
        },
        "path2": {
          "folders": [...],
          "objects": [...]
        }
      }
    },
    {
      "items": {
        "item1": {
          "_typename": "TGraph",
          ...
        },
        "path/item2": {
          "_typename": "TH1D",
          ...
        }
      },
      "root": "file2",
      "trees": {
        "path1": {
          "folders": [...],
          "objects": [...]
        },
        "path2": {
          "folders": [...],
          "objects": [...]
        }
      }

    }
  ]
}
```



