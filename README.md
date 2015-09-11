# LHCbPR Web Application 2

The second version of the LHCbPR client web application

## Contents

...

## Goals

This version is trying to hide the complexity of AngularJS and to make the analysis modules development an easy process.

## Features

### New Files structure

```
build/
gulp/
  |-- tasks/
  |		|-- core.js
  |		|-- vendors.js
  |		|-- default.js
  |-- utils/
  |		|-- helper.js
  |		|-- run.js
  |-- config.json
src/
  |-- core/
  |		|-- imgs/
  |		|-- scripts/
  |		|	  |-- classes/
  |		|	  |-- controllers/
  |		|	  |-- directives/
  |		|	  |-- factories/
  |		|	  |-- services/
  |		|	  |-- init.js
  |		|-- styles/
  |		|-- views/
  |-- modules/
  |-- index.jade
gulpfile.js
```



### Adding a library to base vendors

Base vendors are libraries loaded initialy with the application. They are libraries required by some core components of the application (example: The `Restangular` vendor is required by the `api`). To add new base vendor simply install it using bower:

```
bower install <package-name> --save
```

Then add its files to the `gulp/config.json` under the vendors.base object.

### Adding a library to lazy loaded vendors

