"""
FastAPI Parameter Functions Module

Dieses Modul stellt alle FastAPI Parameter-Funktionen zur Verfügung.
"""

# Importiere alle Original Parameter-Funktionen
from fastapi.param_functions import (
    Body as OriginalBody,
    Cookie as OriginalCookie,
    Depends as OriginalDepends,
    File as OriginalFile,
    Form as OriginalForm,
    Header as OriginalHeader,
    Path as OriginalPath,
    Query as OriginalQuery,
    Security as OriginalSecurity,
)

# Re-exportiere die Original-Funktionen
Body = OriginalBody
Cookie = OriginalCookie
Depends = OriginalDepends
File = OriginalFile
Form = OriginalForm
Header = OriginalHeader
Path = OriginalPath
Query = OriginalQuery
Security = OriginalSecurity