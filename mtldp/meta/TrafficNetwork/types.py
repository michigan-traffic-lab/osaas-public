# -*- coding: utf-8 -*-
from typing import Literal

Direction = Literal['E', 'W', 'N', 'S']
OsmDirection = Literal['forward', 'backward']
Turn = Literal['l', 'r', 's', 'ls', 'rs', 'lr', 'lsr']
NodeType = Literal['ordinary', 'connector', 'signalized', 'unsignalized', 'end']
