# LHCbPR web site

## Installation

**Prerequisites:**

1. You need to have [git](https://git-scm.com/)  and [nodejs](https://nodejs.org/en/) tools
1. You need to install `bower` tool for retriving external javascript dependencies: `npm install -g bower`

**Get the source and run development server:**

```sh
$> git clone ssh://git@gitlab.cern.ch:7999/lhcb-core/LHCbPR2FE.git
$> cd LHCbPR2FE
$> ./scripts/runserver  # Run development server. Watches for changes in the source files and live reload if they are updated.
```
You can configure API and ROOT service at `./scripts/runserver` script. By default it uses production services

**Build for a production server:**

```sh
$>  ./scripts/build-prod  
```
- put compiled files to dist/prod folder. The content of the folder can be placed as static source to a web server.


See detailed [documentation](https://gitlab.cern.ch/lhcb-core/LHCbPR2FE/blob/master/backend-angular/app/documentation/readme.md) on how to use development tools.

## Creating Modules

See [LHCbPR Modules Development Guide](https://gitlab.cern.ch/lhcb-core/LHCbPR2FE/blob/master/documentation/modules-guide.md)
