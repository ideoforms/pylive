# Contributing 

## Publishing on pypi

```
# Update version in setup.py 
git tag vX.Y.Z
python3 setup.py sdist
twine upload dist/*
```
