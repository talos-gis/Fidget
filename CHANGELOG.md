# Fidget Changelog
## 0.0.6- unreleased
## Added
* tabs can now handle arrow keys to switch tabs
## Changed
* Major Code refactoring in `widgets`, including:
    * Common superclass to `FidgetDict` and `FidgetTabs`
## 0.0.5- 2019-03-21
## Added
* FidgetSpin has initial value parameter
* Parsers and printers can now be prioritized with the `low_priority`, `high_priority`, `mid_priority` decorators
* added the `FidgetTabs` aggregate
* FidgetCombo's options is now a dual parameter
## Changed
* errors on arguments not provided now also include self
* the name and fields of namedtuple type of FidgetTable and FidgetTuple is now automatically adjusted to an identifier.
* fidget now uses its own embedded icons, courtesy of [feather](https://feathericons.com/).
## Fixed
* error when setting initial value for minimal
* minimal dialog will have correct parent
* optional plaintext printer misbehaving
* FidgetCombo's parse can now handle any printed value
## 0.0.4- 2019-03-18
### Added
* Initial release