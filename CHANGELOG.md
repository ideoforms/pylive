# Changelog

## [v0.3.0](https://github.com/ideoforms/pylive/releases/tag/v0.3.0) (2023-07-14)

- Completely overhaul implementation to use [AbletonOSC](https://github.com/ideoforms/AbletonOSC) as a Live API, retiring support for LiveOSC

## [v0.2.2](https://github.com/ideoforms/pylive/releases/tag/v0.2.2) (2022-06-19)

- Add support for [python-osc](https://pypi.org/project/python-osc/) (thanks to [Tom O'Connell](https://github.com/tom-oconnell))

## [v0.2.1](https://github.com/ideoforms/pylive/releases/tag/v0.2.1) (2019-09-30)

- Fix bug in which `Set.currently_open()` sometimes does not return the correct path
- Add support in `Track` for creating/deleting clips

## [v0.2.0](https://github.com/ideoforms/pylive/releases/tag/v0.2.0) (2019-05-28)

 - Comprehensive tidyup and overhaul, with support for Python 3
 - Add unit test suite with `pytest`
 - Switch to using `logging` for configurable log output
 - Add dedicated `LiveException` subclasses
 - `Clip`: Add support for adding and querying notes

## [v0.1.4](https://github.com/ideoforms/pylive/releases/tag/v0.1.4) (2015-09-01)

- Make playback of Group clips set the correct status of any contained Track/Clip objects
- Add mutexes for beat/startup events

## [v0.1.2](https://github.com/ideoforms/pylive/releases/tag/v0.1.2) (2015-05-07)

- Switch to using `liblo` for OSC communications
- Add support for opening Live sets programmatically
- Add `startup_callback`, triggered on Live startup
- Add support for getting/setting clip names, mute, quantization
- Add `Scene` object


## [v0.1.1](https://github.com/ideoforms/pylive/releases/tag/v0.1.1) (2013-10-02)

Initial public release.

- Add `Set`, `Track`, `Group`, `Clip`, `Device`
- Add basic examples

