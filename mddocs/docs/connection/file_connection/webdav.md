# WebDAV connection { #DBR-onetl-connection-file-connection-webdav-connection }


::: onetl.connection.file_connection.webdav.WebDAV
    options:
        show_root_heading: true
        members:
            - check
            - path_exists
            - is_file
            - is_dir
            - get_stat
            - resolve_dir
            - resolve_file
            - create_dir
            - remove_file
            - remove_dir
            - rename_file
            - list_dir
            - walk
            - download_file
            - upload_file

::: onetl.connection.file_connection.webdav.WebDAVExtra
    options:
        show_root_heading: true
        members:
          - timeout
          - retry
          - ssl_verify
