@echo off
setlocal

where uv >nul 2>nul
if errorlevel 1 (
    >&2 echo Error: `uv` was not found in PATH.
    exit /b 1
)

pushd "%~dp0" >nul || exit /b 1

if "%~1"=="" (
    echo $ uv run ruff check . --fix
    uv run ruff check . --fix
    if errorlevel 1 goto :fail

    echo $ uv run ruff format .
    uv run ruff format .
    if errorlevel 1 goto :fail
) else (
    echo $ uv run ruff check %* --fix
    uv run ruff check %* --fix
    if errorlevel 1 goto :fail

    echo $ uv run ruff format %*
    uv run ruff format %*
    if errorlevel 1 goto :fail
)

popd >nul
exit /b 0

:fail
set "EXIT_CODE=%ERRORLEVEL%"
popd >nul
exit /b %EXIT_CODE%
