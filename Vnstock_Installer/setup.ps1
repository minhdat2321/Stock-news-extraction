###############################################################################
# setup.ps1
# A PowerShell installation script for Windows.
# - Detects Python versions (>= 3.10), sorts them ascending (oldest -> newest).
# - If only one version is found, auto-selects it; otherwise, prompts the user.
# - Optionally creates a virtual environment.
# - Installs basic packages and then runs setup_wizard.exe.
###############################################################################

$VENV_DIR = "venv_vnstock"

function Display-Logo {
    Write-Host " __      __ _   _  _____ _______ ____   _____ _  __" -ForegroundColor Cyan
    Write-Host " \ \    / /| \ | |/ ____|__   __/ __ \ / ____| |/ /" -ForegroundColor Cyan
    Write-Host "  \ \  / / |  \| | (___    | | | |  | | |    | ' / " -ForegroundColor Cyan
    Write-Host "   \ \/ /  | . ` |\___ \   | | | |  | | |    |  <  " -ForegroundColor Cyan
    Write-Host "    \  /   | |\  |____) |  | | | |__| | |____| . \ " -ForegroundColor Cyan
    Write-Host "     \/    |_| \_|_____/   |_|  \____/ \_____|_|\_\" -ForegroundColor Cyan
    Write-Host "       Cong Cu Phan Tich Thi Truong Chung Khoan Viet Nam" -ForegroundColor Yellow
    Write-Host ""
}

function Print-InstallationOverview {
    Write-Host "============= Installation Overview (Tom tat qua trinh cai dat) =============" -ForegroundColor Magenta
    Write-Host "1. Detect Python versions (>= 3.10) and allow you to choose." -ForegroundColor Yellow
    Write-Host "2. (Optional) Create a virtual environment and install basic packages (requests, numpy, etc.)." -ForegroundColor Yellow
    Write-Host "3. Run setup_wizard.exe with the selected Python to complete installation." -ForegroundColor Yellow
    Write-Host "===================================================" -ForegroundColor Magenta
    Write-Host "Press Enter to begin installation (nhan Enter de bat dau qua trinh cai dat)..." -ForegroundColor Blue
    Read-Host
}

function Check-VirtualEnv {
    if ($env:VIRTUAL_ENV) {
        Write-Host "Already running in virtual environment: $($env:VIRTUAL_ENV) (dang chay trong moi truong ao: $($env:VIRTUAL_ENV))" -ForegroundColor Green
        return $true
    }
    return $false
}

function Rank-PythonVersion ($version) {
    $parts = $version.Split('.')
    if ($parts.Length -ge 2) {
        [int]$major = $parts[0]
        [int]$minor = $parts[1]
        return ($major * 100 + $minor)
    } else {
        return 0
    }
}

function Detect-PythonVersions {
    $pythonExecutables = @("python3", "python3.12", "python3.11", "python3.10", "python", "python3.9", "python3.8", "python3.7")
    $versionsList = @()
    $aliasesList = @()
    
    foreach ($exe in $pythonExecutables) {
        $cmd = Get-Command $exe -ErrorAction SilentlyContinue
        if ($cmd) {
            try {
                $versionOutput = & $exe --version 2>&1
                # Extract version string (e.g. "3.10" from "Python 3.10.8")
                if ($versionOutput -match "(\d+\.\d+)") {
                    $ver = $matches[1]
                    $parts = $ver.Split('.')
                    if ($parts.Length -ge 2) {
                        [int]$major = $parts[0]
                        [int]$minor = $parts[1]
                        if ($major -eq 3 -and $minor -ge 10) {
                            if (-not ($versionsList -contains $ver)) {
                                $versionsList += $ver
                                $aliasesList += $exe
                            }
                        }
                    }
                }
            } catch {
                # Ignore errors
            }
        }
    }
    
    if ($versionsList.Count -eq 0) {
        Write-Host "Python >= 3.10 not found. Please install Python and try again (khong tim thay Python >= 3.10. Vui long cai dat Python va thu lai)." -ForegroundColor Red
        exit 1
    }
    
    $combined = @()
    for ($i = 0; $i -lt $versionsList.Count; $i++) {
        $rank = Rank-PythonVersion $versionsList[$i]
        $combined += [PSCustomObject]@{
            Version = $versionsList[$i]
            Alias   = $aliasesList[$i]
            Rank    = $rank
        }
    }
    
    $combined = $combined | Sort-Object Rank
    
    if ($combined.Count -eq 1) {
        $single = $combined[0]
        $pythonPath = (Get-Command $single.Alias).Source
        $global:PYTHON_EXE = $pythonPath
        $global:PYTHON_VER = $single.Version
        Write-Host "Only one Python version found: $pythonPath (version $($single.Version)) (chi tim thay mot phien ban Python: $pythonPath (phien ban $($single.Version)))." -ForegroundColor Green
        Write-Host "Automatically selected without showing menu (tu dong chon, khong hien thi menu)." -ForegroundColor Green
        return
    }
    
    Write-Host "Detected Python versions (oldest -> newest): (cac phien ban Python duoc phat hien tu cu den moi):" -ForegroundColor Blue
    $index = 1
    $finalList = @()
    foreach ($item in $combined) {
        $finalList += $item
        Write-Host "$index. $($item.Alias) version $($item.Version) ($($item.Alias) phien ban $($item.Version))" -ForegroundColor Yellow
        $index++
    }
    
    $defaultIndex = 1
    $choice = Read-Host "Press Enter to select default (option $defaultIndex) or enter a number to choose (nhan Enter de chon mac dinh (option $defaultIndex) hoac nhap so de chon)"
    
    if ([string]::IsNullOrWhiteSpace($choice)) {
        $chosenIndex = $defaultIndex
    } elseif ($choice -as [int] -and $choice -ge 1 -and $choice -le $finalList.Count) {
        $chosenIndex = [int]$choice
    } else {
        Write-Host "Invalid selection. Default option ($defaultIndex) will be used (lua chon khong hop le. Su dung mac dinh option $defaultIndex)." -ForegroundColor Yellow
        $chosenIndex = $defaultIndex
    }
    
    $picked = $finalList[$chosenIndex - 1]
    $pythonPath = (Get-Command $picked.Alias).Source
    $global:PYTHON_EXE = $pythonPath
    $global:PYTHON_VER = $picked.Version
    Write-Host "Selected Python: $pythonPath (version $($picked.Version)) (da chon $pythonPath (phien ban $($picked.Version)))." -ForegroundColor Green
}

function Create-VirtualEnv {
    if (Check-VirtualEnv) {
        return
    }
    
    Write-Host "Do you want to create a virtual environment for this installation? (ban co muon tao moi truong ao cho cai dat nay khong?)" -ForegroundColor Blue
    Write-Host "Press Enter to skip (default) or type 'OK' to create virtual environment (nhan Enter de bo qua (mac dinh) hoac nhap 'OK' de tao moi truong ao):" -ForegroundColor Yellow
    $answer = Read-Host "Your choice (lua chon cua ban)"
    
    if ($answer -eq "OK" -or $answer -eq "ok") {
        Write-Host "Creating virtual environment, please wait... (dang tao moi truong ao, vui long cho...)" -ForegroundColor Blue
        $currentDir = Get-Location
        $FULL_VENV_PATH = Join-Path $currentDir $VENV_DIR
        & $global:PYTHON_EXE -m venv $FULL_VENV_PATH
        if (-not (Test-Path $FULL_VENV_PATH)) {
            Write-Host "Failed to create virtual environment. (tao moi truong ao that bai.)" -ForegroundColor Red
            return 1
        }
        # Activate the virtual environment
        $activateScript = Join-Path $FULL_VENV_PATH "Scripts\Activate.ps1"
        if (Test-Path $activateScript) {
            . $activateScript
        } else {
            Write-Host "Activation script not found. (khong tim thay script kich hoat.)" -ForegroundColor Red
            return 1
        }
        if (-not $env:VIRTUAL_ENV) {
            # Manually set VIRTUAL_ENV if not set
            $env:VIRTUAL_ENV = $FULL_VENV_PATH
        }
        Write-Host "Virtual environment created at: $env:VIRTUAL_ENV (moi truong ao duoc tao tai: $env:VIRTUAL_ENV)" -ForegroundColor Green
        $global:PYTHON_EXE = "python"
    } else {
        Write-Host "Skipping virtual environment creation. Using system Python (bo qua tao moi truong ao. Su dung Python he thong)." -ForegroundColor Yellow
    }
}

function Install-PythonPackages {
    Write-Host "Installing basic Python packages... (dang cai dat cac goi Python co ban...)" -ForegroundColor Blue
    if (-not $env:VIRTUAL_ENV) {
        & $global:PYTHON_EXE -m pip install --upgrade pip | Out-Null
    } else {
        & $global:PYTHON_EXE -m pip install --upgrade pip | Out-Null
    }
    
    $packages = @("requests", "numpy", "pandas", "requests_oauthlib", "beautifulsoup4", "tenacity", "openpyxl")
    foreach ($pkg in $packages) {
        Write-Host "Installing $pkg... (dang cai dat $pkg...)" -ForegroundColor Yellow
        & $global:PYTHON_EXE -m pip install $pkg | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Installed $pkg successfully! (cai dat $pkg thanh cong!)" -ForegroundColor Green
        } else {
            Write-Host "Installation of $pkg failed. (cai dat $pkg that bai.)" -ForegroundColor Red
            Write-Host "Trying to install with --user... (thu cai dat lai voi --user...)" -ForegroundColor Yellow
            if (-not $env:VIRTUAL_ENV) {
                & $global:PYTHON_EXE -m pip install --user $pkg | Out-Null
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "Installed $pkg with --user successfully! (cai dat $pkg voi --user thanh cong!)" -ForegroundColor Green
                } else {
                    Write-Host "Failed to install $pkg. (khong the cai dat $pkg.)" -ForegroundColor Red
                }
            } else {
                Write-Host "Cannot install $pkg in a virtual environment. (khong the cai dat $pkg trong moi truong ao.)" -ForegroundColor Red
            }
        }
    }
    Write-Host "Basic packages installation complete! (cai dat cac goi co ban hoan tat!)" -ForegroundColor Green
}

function Run-SetupWizard {
    Write-Host "Running setup_wizard.exe... (dang chay setup_wizard.exe...)" -ForegroundColor Blue
    if (-not (Test-Path "setup_wizard.exe")) {
        Write-Host "setup_wizard.exe not found in current directory. (khong tim thay setup_wizard.exe trong thu muc hien tai.)" -ForegroundColor Yellow
        return 1
    }
    # Run the executable directly instead of through Python.
    & ".\setup_wizard.exe"
    $setupStatus = $LASTEXITCODE
    if ($setupStatus -eq 0) {
        Write-Host "Setup completed successfully! (cai dat hoan tat thanh cong!)" -ForegroundColor Green
    } else {
        Write-Host "An error occurred during setup. Error code: $setupStatus (co loi xay ra trong qua trinh cai dat. Ma loi: $setupStatus)" -ForegroundColor Red
    }
    return $setupStatus
}

function Main {
    Clear-Host
    Display-Logo
    Print-InstallationOverview

    Write-Host "====================================" -ForegroundColor Magenta
    Detect-PythonVersions
    Create-VirtualEnv
    $pythonCmd = (Get-Command $global:PYTHON_EXE -ErrorAction SilentlyContinue).Source
    Write-Host "Using Python: $global:PYTHON_EXE ($pythonCmd) (su dung Python: $global:PYTHON_EXE ($pythonCmd))" -ForegroundColor Blue
    Install-PythonPackages
    Run-SetupWizard
    $finalStatus = $LASTEXITCODE
    exit $finalStatus
}

Main
