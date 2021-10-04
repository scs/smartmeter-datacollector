# Licensing Rules

`smartmeter-datacollector` is provided under the GNU General Public License v2.0 as provided in **[GPL-2.0-only](../LICENSE)**.

## Dual Licensing
As explained above `smartmeter-datacollector` is primarily provided under **[GPL-2.0-only](../LICENSE)**. Since the main dependency [Gurux.DLMS.Python](https://github.com/Gurux/Gurux.DLMS.Python) is provided under a **[dual licensing model](https://www.gurux.fi/duallicense)** the same model is applied to `smartmeter-datacollector`.

By acquiring `Gurux.DLMS.Python` under its commercial license it becomes possible to use `smartmeter-datacollector` in commercial products without the restrictions of *GPL-2.0-only* i.e. there is no obligation to publish the source code of the applications based on `smartmeter-datacollector`. 

Furthermore by acquiring the commercial license for `Gurux.DLMS.Python`  [Gurux](https://www.gurux.fi/) provides additional commercial support for their products. **This support does not extend to `smartmeter-datacollector` and using it under the commercial license does not provide any additional support or benefits** apart from lifting the restrictions of *GPL-2.0-only*. If you require additional support or custom extensions to `smartmeter-datacollector` please [contact Supercomputing Systems AG](https://www.scs.ch/kontakt-anfahrt/lageplan/).

Using dual licensing to provide `smartmeter-datacollector` combines the benefits of licensing the product under *GPL-2.0-only* with the possibility to use it in situations where *GPL-2.0-only* is not applicable.

## Contributing
`smartmeter-datacollector` has been developed by **[Supercomputing Systems AG](https://www.scs.ch/)** on behalf of and funded by **[EKZ](https://www.ekz.ch/)** but is meant to be used and extended by the open source community. Therefore **every contribution is welcome** in the form of [pull requests](https://docs.github.com/en/github/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests).

Every developer contributing to `smartmeter-datacollector` must do so under the license(s) described above.

## The SPDX License Identifier
`smartmeter-datacollector` uses `Software Package Data Exchange` (`SPDX`) license identifiers in each source file. These are machine parsable and  unambiguously specify under which license the content of a source file is contributed.

SPDX license identifiers are managed by the SPDX Workgroup at the Linux Foundation and have been agreed on by partners throughout the industry, tool vendors, and legal teams. For further information see **[spdx.org](https://spdx.org/)**.

### Tools
Since `smartmeter-datacollector` requires the exact SPDX license identifier at the top of every source file there is tool support to take care of this.

Running the pre-defined `pipenv run license` from [Pipfile](../Pipfile) will use [licenseheaders](https://github.com/johann-petrak/licenseheaders) in combination with a pre-defined [template](../.copyright.tmpl) to make sure the SPDX license identifier is present at the top of every source file. The resulting license header will look like
```
#
# Copyright (C) 2021 Supercomputing Systems AG
# This file is part of smartmeter-datacollector.
#
# SPDX-License-Identifier: GPL-2.0-only
# See LICENSES/README.md for more information.
#
```