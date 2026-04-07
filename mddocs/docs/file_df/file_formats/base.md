# Base interface { #DBR-onetl-file-df-file-formats-base-interface }


::: onetl.base.base_file_format.BaseReadableFileFormat
    options:
        members:
            - check_if_supported
            - apply_to_reader

::: onetl.base.base_file_format.BaseWritableFileFormat
    options:
        members:
            - check_if_supported
            - apply_to_writer
