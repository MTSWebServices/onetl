# How to install { #DBR-onetl-install-how-to-install-0 }

Base `onetl` package contains:

* `DBReader`, `DBWriter` and related classes
* `FileDownloader`, `FileUploader`, `FileMover` and related classes, like file filters & limits
* `FileDFReader`, `FileDFWriter` and related classes, like file formats
* Read Strategies & HWM classes
* Plugins support

It can be installed via:

```bash
pip install onetl
```

!!! warning

    This method does NOT include any connections.

    This method is recommended for use in third-party libraries which require for `onetl` to be installed,
    but do not use its connection classes.


## Installation in details { #DBR-onetl-install-installation-in-details }

### How to install { #DBR-onetl-install-how-to-install-1 }

* [How to install][DBR-onetl-install-how-to-install-0]
* [Minimal installation][DBR-onetl-install-minimal-installation]
* [Spark][DBR-onetl-install-spark]
* [File connections][DBR-onetl-install-files-file-connections]
* [Kerberos support][DBR-onetl-install-kerberos-support]
* [Full bundle][DBR-onetl-install-full-bundle]
