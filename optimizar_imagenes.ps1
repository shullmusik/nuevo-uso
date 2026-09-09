# =============================================================================
#  optimizar_imagenes.ps1
#  Comprime las fotos de la carpeta "imagenes" para que el catalogo cargue
#  rapido en el celular.
#
#  Usalo SOLO si no pudiste instalar Pillow en Python. Hace lo mismo que hace
#  fetch_drive_data.py cuando Pillow si esta disponible.
#
#  Como usarlo (clic derecho > "Ejecutar con PowerShell", o en una terminal):
#
#      powershell -ExecutionPolicy Bypass -File optimizar_imagenes.ps1
#
#  Los archivos que terminan en "-mini.jpg" se dejan en 600 px de ancho
#  (los que se ven en las tarjetas) y el resto en 1400 px (el visor grande).
# =============================================================================

param(
    [string]$Carpeta = "imagenes",
    [int]$AnchoGrande = 1400,
    [int]$AnchoMini = 600,
    [int]$Calidad = 82
)

Add-Type -AssemblyName System.Drawing

$codec = [System.Drawing.Imaging.ImageCodecInfo]::GetImageEncoders() |
         Where-Object { $_.MimeType -eq 'image/jpeg' }

function Optimize-Foto {
    param([string]$Ruta, [int]$AnchoMax, [int]$Q)

    $original = [System.Drawing.Image]::FromFile($Ruta)
    try {
        $w = $original.Width
        $h = $original.Height
        if ($w -le $AnchoMax) {
            $nuevoW = $w; $nuevoH = $h
        } else {
            $nuevoW = $AnchoMax
            $nuevoH = [int][Math]::Round($h * ($AnchoMax / $w))
        }

        $destino = New-Object System.Drawing.Bitmap($nuevoW, $nuevoH)
        $g = [System.Drawing.Graphics]::FromImage($destino)
        $g.InterpolationMode  = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
        $g.SmoothingMode      = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
        $g.PixelOffsetMode    = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
        $g.DrawImage($original, 0, 0, $nuevoW, $nuevoH)
        $g.Dispose()

        $params = New-Object System.Drawing.Imaging.EncoderParameters(1)
        $params.Param[0] = New-Object System.Drawing.Imaging.EncoderParameter(
            [System.Drawing.Imaging.Encoder]::Quality, [long]$Q)

        $temporal = "$Ruta.tmp"
        $destino.Save($temporal, $codec, $params)
        $destino.Dispose()
        $params.Dispose()
        return $temporal
    }
    finally {
        $original.Dispose()
    }
}

if (-not (Test-Path $Carpeta)) {
    Write-Host "No existe la carpeta '$Carpeta'. Ejecuta primero fetch_drive_data.py." -ForegroundColor Red
    exit 1
}

$fotos = Get-ChildItem -Path $Carpeta -Recurse -Include *.jpg, *.jpeg -File
$antes = ($fotos | Measure-Object -Property Length -Sum).Sum
$n = 0

foreach ($foto in $fotos) {
    $ancho = if ($foto.Name -like '*-mini.jpg') { $AnchoMini } else { $AnchoGrande }
    try {
        $tmp = Optimize-Foto -Ruta $foto.FullName -AnchoMax $ancho -Q $Calidad
        Move-Item -Path $tmp -Destination $foto.FullName -Force
        $n++
        if ($n % 25 -eq 0) { Write-Host "  $n de $($fotos.Count)..." }
    } catch {
        Write-Host "  No se pudo procesar $($foto.Name): $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

$despues = (Get-ChildItem -Path $Carpeta -Recurse -Include *.jpg, *.jpeg -File |
            Measure-Object -Property Length -Sum).Sum

$mbAntes   = [Math]::Round($antes / 1MB, 1)
$mbDespues = [Math]::Round($despues / 1MB, 1)

Write-Host ""
Write-Host "Listo: $n fotos optimizadas." -ForegroundColor Green
Write-Host "Tamano: $mbAntes MB  ->  $mbDespues MB"
