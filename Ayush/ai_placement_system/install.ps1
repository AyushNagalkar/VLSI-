# AI-Powered Macro Placement System - Installation Script
# For Windows PowerShell

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                                                                   ║" -ForegroundColor Cyan
Write-Host "║          AI-POWERED MACRO PLACEMENT SYSTEM                        ║" -ForegroundColor Cyan
Write-Host "║                  Installation Script                              ║" -ForegroundColor Cyan
Write-Host "║                                                                   ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Check Python
Write-Host "Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found! Please install Python 3.8+ first." -ForegroundColor Red
    exit 1
}

# Check pip
Write-Host "`nChecking pip..." -ForegroundColor Yellow
try {
    $pipVersion = pip --version
    Write-Host "✓ pip is installed" -ForegroundColor Green
} catch {
    Write-Host "✗ pip not found!" -ForegroundColor Red
    exit 1
}

# Install dependencies
Write-Host "`n" + ("="*70) -ForegroundColor Cyan
Write-Host "Installing dependencies..." -ForegroundColor Yellow
Write-Host ("="*70) -ForegroundColor Cyan

Write-Host "`n[1/3] Installing core packages..." -ForegroundColor Yellow
pip install numpy matplotlib tqdm psutil seaborn

Write-Host "`n[2/3] Installing PyTorch..." -ForegroundColor Yellow
Write-Host "Choose your installation:" -ForegroundColor Cyan
Write-Host "  1. CPU only (no GPU)" -ForegroundColor White
Write-Host "  2. CUDA 11.8 (NVIDIA GPU)" -ForegroundColor White
Write-Host "  3. CUDA 12.1 (NVIDIA GPU)" -ForegroundColor White
$choice = Read-Host "Enter choice (1/2/3)"

switch ($choice) {
    "1" {
        Write-Host "Installing PyTorch (CPU)..." -ForegroundColor Yellow
        pip install torch --index-url https://download.pytorch.org/whl/cpu
    }
    "2" {
        Write-Host "Installing PyTorch (CUDA 11.8)..." -ForegroundColor Yellow
        pip install torch --index-url https://download.pytorch.org/whl/cu118
    }
    "3" {
        Write-Host "Installing PyTorch (CUDA 12.1)..." -ForegroundColor Yellow
        pip install torch --index-url https://download.pytorch.org/whl/cu121
    }
    default {
        Write-Host "Invalid choice. Installing CPU version..." -ForegroundColor Yellow
        pip install torch --index-url https://download.pytorch.org/whl/cpu
    }
}

Write-Host "`n[3/3] Installing DGL (Deep Graph Library)..." -ForegroundColor Yellow
switch ($choice) {
    "1" {
        pip install dgl -f https://data.dgl.ai/wheels/repo.html
    }
    "2" {
        pip install dgl -f https://data.dgl.ai/wheels/cu118/repo.html
    }
    "3" {
        pip install dgl -f https://data.dgl.ai/wheels/cu121/repo.html
    }
    default {
        pip install dgl -f https://data.dgl.ai/wheels/repo.html
    }
}

# Create output directories
Write-Host "`n" + ("="*70) -ForegroundColor Cyan
Write-Host "Creating output directories..." -ForegroundColor Yellow
Write-Host ("="*70) -ForegroundColor Cyan

New-Item -ItemType Directory -Force -Path ".\trained_models" | Out-Null
New-Item -ItemType Directory -Force -Path ".\placement_results" | Out-Null

Write-Host "✓ Created trained_models/" -ForegroundColor Green
Write-Host "✓ Created placement_results/" -ForegroundColor Green

# Run verification
Write-Host "`n" + ("="*70) -ForegroundColor Cyan
Write-Host "Running system verification..." -ForegroundColor Yellow
Write-Host ("="*70) -ForegroundColor Cyan

python test_system.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n" + ("="*70) -ForegroundColor Green
    Write-Host "✓ INSTALLATION COMPLETE!" -ForegroundColor Green
    Write-Host ("="*70) -ForegroundColor Green
    
    Write-Host "`nYou can now run:" -ForegroundColor Cyan
    Write-Host "  python main.py --mode demo" -ForegroundColor White
    Write-Host "`nFor help:" -ForegroundColor Cyan
    Write-Host "  python main.py --help" -ForegroundColor White
    Write-Host "`nFor full documentation, see:" -ForegroundColor Cyan
    Write-Host "  README.md" -ForegroundColor White
    Write-Host "  QUICKSTART.md" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host "`n" + ("="*70) -ForegroundColor Red
    Write-Host "⚠ INSTALLATION INCOMPLETE" -ForegroundColor Red
    Write-Host ("="*70) -ForegroundColor Red
    Write-Host "`nSome tests failed. Please check the output above." -ForegroundColor Yellow
    Write-Host ""
}
