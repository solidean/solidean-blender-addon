#!/usr/bin/env pwsh
# Build the Solidean Blender addon zip, verifying that all required files
# (including a platform-appropriate native library) are present.

$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

$pkg = 'solidean'
$out = 'solidean.zip'

if (-not (Test-Path $pkg -PathType Container)) {
    throw "Package folder '$pkg' not found."
}

$required = @(
    '__init__.py',
    'blender_manifest.toml',
    'live.py',
    'utils.py',
    'solidean.py'
)
$missing = $required | Where-Object { -not (Test-Path (Join-Path $pkg $_) -PathType Leaf) }
if ($missing) {
    throw "Missing required file(s) in $pkg/: $($missing -join ', ')"
}

$libs = @('solidean.dll', 'libsolidean.so', 'libsolidean.dylib')
$found = $libs | Where-Object { Test-Path (Join-Path $pkg $_) -PathType Leaf }
if (-not $found) {
    throw "No Solidean native library found in $pkg/. Expected one of: $($libs -join ', '). See https://solidean.com/download/solidean/."
}
Write-Host "Native library: $($found -join ', ')"

Get-ChildItem -Path $pkg -Filter '__pycache__' -Directory -Recurse |
    Remove-Item -Recurse -Force

if (Test-Path $out) { Remove-Item $out -Force }
Compress-Archive -Path $pkg -DestinationPath $out
Write-Host "Created $out"
