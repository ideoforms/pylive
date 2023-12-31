# Contributing 

## Testing

A test suite is included which automatically opens a predetermined set in Ableton Live and runs an array of unit tests. To run the tests:

```
python3 setup.py test
```

## Publishing on pypi

```
# Update version in setup.py 
git tag vX.Y.Z
python3 setup.py sdist
twine upload dist/*
```
