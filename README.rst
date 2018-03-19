cerbapi
=======

A Python wrapper for the Cerb.ai API.

Usage
-----

Enable the API and generate an API key-pair using the instructions
provided by Cerb.ai: https://cerb.ai/guides/api/configure-plugin/

In your python environment, install cerbapi:

.. code:: bash

    pip install cerbapi

In your python project import and create a Cerb instance

.. code:: python


    from cerbapi import Cerb

    cerb = Cerb(
            access_key='accesskeyex',
            secret='DontStoreThisInCodePythonLikeThis',
            base='https://example.com/index.php/base/'
            )

    print(cerb.get_record('ticket', 1))
    print(cerb.get_contexts())
    print(cerb.search_records('comment', query='author.worker:Rob'))

For details on interacting with the API visit the website:
https://cerb.ai/docs/api/