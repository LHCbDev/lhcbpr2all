set path = ( $PWD/scripts $path )
if ( "$PYTHONPATH" == "" ) then
  setenv PYTHONPATH $PWD/python
else
  setenv PYTHONPATH $PWD/python:$PYTHONPATH
endif
