# CHANGELOG - wmi_check

## 1.5.0 / 2019-10-11

* [Added] Upgrade pywin32 to 225. See [#4563](https://github.com/DataDog/integrations-core/pull/4563).

## 1.4.2 / 2019-07-13

* [Fixed] Avoid WMISampler inheriting from Thread. See [#4051](https://github.com/DataDog/integrations-core/pull/4051).

## 1.4.1 / 2019-07-04

* [Fixed] Make WMISampler hashable. See [#4043](https://github.com/DataDog/integrations-core/pull/4043).

## 1.4.0 / 2019-05-14

* [Added] Adhere to code style. See [#3584](https://github.com/DataDog/integrations-core/pull/3584).

## 1.3.0 / 2019-02-18

* [Added] Support Python 3 for WMI. See [#3031](https://github.com/DataDog/integrations-core/pull/3031).

## 1.2.0 / 2018-10-12

* [Added] Pin pywin32 dependency. See [#2322][1].

## 1.1.2 / 2018-09-04

* [Fixed] Moves WMI Check to Pytest. See [#2133][2].
* [Fixed] Add data files to the wheel package. See [#1727][3].

## 1.1.1 / 2018-03-23

* [BUGFIX] change `constant_tags` field in configuration to `tags` for consistency.

## 1.0.0 / 2017-03-22

* [FEATURE] adds wmi_check integration.
[1]: https://github.com/DataDog/integrations-core/pull/2322
[2]: https://github.com/DataDog/integrations-core/pull/2133
[3]: https://github.com/DataDog/integrations-core/pull/1727
