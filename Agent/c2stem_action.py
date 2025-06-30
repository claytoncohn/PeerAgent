import re
import logging

class C2STEMAction:
    """
    Parse and hold a single **C2STEM** (NetsBlox) action message.

    The class extracts a timestamp, action type, and (if present) the
    value of the ``s="..."`` attribute inside the first XML‐like block
    found in ``data["args"][0]``.

    Parameters
    ----------
    data : dict[str, Any]
        JSON-style dictionary representing one action emitted by the
        C2STEM client.  The dictionary **must** contain at least the
        keys::

            "time"  : <int>   # epoch milliseconds
            "type"  : <str>   # e.g. "addBlock"
            "args"  : <list>  # first element is an XML snippet

    Attributes
    ----------
    data : dict[str, Any]
        The raw action payload that was passed in.
    t : int
        The Unix time (milliseconds since 1970-01-01 UTC) at which the
        action occurred, taken directly from ``data["time"]``.
    action_type : str
        The value stored in ``data["type"]`` (for example,
        ``"addBlock"``).
    block : str or None
        The command name found in the first XML snippet’s ``s="..."``
        attribute (for example, ``"setXVelocity"``).  If the attribute
        is absent, the value is ``None`` and a log entry at *error*
        level is emitted.

    Notes
    -----
    The XML snippet is **not** validated beyond a simple regular-
    expression search.  If the incoming message format evolves, update
    the regex in :pycode:`re.search(r's="([^"]+)"', block_str)`.

    Examples
    --------
    >>> msg = {
    ...     "time": 1751304246864,
    ...     "type": "addBlock",
    ...     "args": [
    ...         '<script><block collabId="item_454" s="setXVelocity">'
    ...         '<l>0</l></block></script>',
    ...         "item_0", 98, 225, ["item_454"]
    ...     ]
    ... }
    >>> action = C2STEMAction(msg)
    setXVelocity
    >>> action.block
    'setXVelocity'
    """

    def __init__(self,data):
        """
        Initialize a :class:`C2STEMAction` instance.

        Parameters
        ----------
        data : dict[str, Any]
            The raw event payload.

        Raises
        ------
        KeyError
            If *data* does not contain one of the required keys
            ``"time"``, ``"type"``, or ``"args"``.
        """
        # Store raw payload
        self.data = data
        
        # Store time and type of action
        self.t = self.data["time"]
        self.action_type = self.data["type"]

        # Extract the <block … s="…"> attribute
        block_str = self.data['args'][0]
        mtch = re.search(r's="([^"]+)"', block_str)
        if mtch:
            self.block = mtch.group(1)
            print(self.block)
            logging.info(f"Action received at {self.t}: action={self.action_type}, block={self.block}")
        else:
            logging.error(f"No 's' attribute found in block string: {data}")
            self.block = ""