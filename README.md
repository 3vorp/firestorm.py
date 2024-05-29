<div align="center">
<img src="https://raw.githubusercontent.com/TheRolfFR/firestorm-db/main/img/firestorm-128.png">

<h1>firestorm-db</h1>

</div>

*Self hosted Firestore-like database with API endpoints based on micro bulk operations*

# Python Client

This module is simply a port of the [JavaScript package of the same name](https://npmjs.com/package/firestorm-db), which has the relevant documentation on installing the PHP backend and other details. Thus, this README won't duplicate that information.

## Python setup

First, set your API address (and your writing token if needed) using the `address()` and `token()` functions:

```py
# only needed in Node.js, including the script tag in a browser is enough otherwise.
import firestorm

firestorm.address("http://example.com/path/to/firestorm/root/")

# only necessary if you want to write or access private collections
# must match token stored in tokens.php file
firestorm.token("my_secret_token_probably_from_an_env_file")
```

Now you can use Firestorm to its full potential.

## Create your first collection

Firestorm is based around the concept of a `Collection`, which is akin to an SQL table or Firestore document. The Firestorm collection constructor only needs the name of the collection as a `str`. You can also inject methods to query results using the `collection.add_method` decorator, which takes a queried element as an argument, modifies it in the decorated function, and returns the modified element at the end.

```py
import firestorm

user_collection = firestorm.collection("users")

@user_collection.add_method
def add_methods(el):
    # assumes you have a 'users' table with a printable field called 'name'
    el["hello"] = f"{el.name} says hello!"
    # return the modified element back with the injected data
    return el

john_doe = user_collection.get(123456789)
# gives { "name": "John Doe", "hello": str }

print(johnDoe.hello) # "John Doe says hello!"
```

# Differences between the JavaScript wrapper and Python

The main differences between the Python and JavaScript clients are how methods are cased (camelCase vs snake_case), what libraries power them ([HTTPX](https://www.npmjs.com/package/https://www.python-httpx.org/) and [Axios](https://axios-http.com/)), and how files are handled, respectively.

## Casing

`snake_case` is used for all collection methods (e.g. `searchKeys` becomes `search_keys`). This does not apply to search criteria (e.g. `endsWith` is preserved as `camelCase`).

## Backend

Virtually all modern request systems in JavaScript are inherently asynchronous from how the event loop works, and are usually implemented with Promises. The Python client uses synchronous HTTPX requests with threading.

## File Handling

JavaScript has first-class support for the `multipart/form-data` encoding with the `FormData` object. Python doesn't have this feature natively, so files uploaded with `firestorm.files` use keyword arguments instead for each part of the data.