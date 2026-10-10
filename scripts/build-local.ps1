param(
    [string]$PythonVersion = "3.12",
    [string]$Proxy = ""
)

$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

if ($Proxy) {
    $env:HTTP_PROXY = $Proxy
    $env:HTTPS_PROXY = $Proxy
}

Push-Location (Join-Path $root "explorer")
try {
    npm ci
    npm run build
} finally {
    Pop-Location
}

$buildVenv = Join-Path $root ".build-venv"
$buildPython = Join-Path $buildVenv "Scripts\python.exe"
if (-not (Test-Path -LiteralPath $buildPython)) {
    uv venv $buildVenv --python $PythonVersion
    uv pip install --python $buildPython build setuptools==84.0.0 wheel==0.48.0
}

Push-Location $root
try {
    $buildDir = Join-Path $root "build"
    if (Test-Path -LiteralPath $buildDir) {
        Remove-Item -LiteralPath $buildDir -Recurse -Force
    }
    & $buildPython -m build --wheel --no-isolation
} finally {
    Pop-Location
}

$runtimeVenv = Join-Path $root ".venv"
uv venv --clear $runtimeVenv --python $PythonVersion
$runtimePython = Join-Path $runtimeVenv "Scripts\python.exe"
$wheel = Get-ChildItem (Join-Path $root "dist\semantica-0.7.0+tcl.3-*.whl") |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1
if (-not $wheel) {
    throw "Built Wheel was not found under $root\dist"
}

uv pip install --python $runtimePython "semantica[explorer,project-kb] @ file:///$($wheel.FullName.Replace('\', '/'))"
uv pip install --python $runtimePython pytest
Push-Location $env:TEMP
try {
    & $runtimePython -c "import importlib.metadata as m, pathlib; d=m.distribution('semantica'); print('semantica', m.version('semantica')); print((pathlib.Path(d._path)/'direct_url.json').read_text(encoding='utf-8'))"
} finally {
    Pop-Location
}
& (Join-Path $runtimeVenv "Scripts\semantica-project-kb.exe") --help
Get-FileHash -LiteralPath $wheel.FullName -Algorithm SHA256
