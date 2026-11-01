$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Drawing
$root=Split-Path $PSScriptRoot -Parent
$out=Join-Path $root 'out\render\feeder_sheet.png'
$w=1800;$h=1380;$bmp=[System.Drawing.Bitmap]::new($w,$h);$g=[System.Drawing.Graphics]::FromImage($bmp)
$g.SmoothingMode='AntiAlias';$g.InterpolationMode='HighQualityBicubic';$g.TextRenderingHint='AntiAliasGridFit';$g.Clear([System.Drawing.Color]::White)
$navy=[System.Drawing.Color]::FromArgb(24,51,77);$blue=[System.Drawing.Color]::FromArgb(32,82,118);$orange=[System.Drawing.Color]::FromArgb(220,117,29);$ink=[System.Drawing.Color]::FromArgb(32,42,53);$muted=[System.Drawing.Color]::FromArgb(82,98,112);$line=[System.Drawing.Color]::FromArgb(205,215,222);$pale=[System.Drawing.Color]::FromArgb(244,247,249)
function Font([float]$size,[bool]$bold=$false){$style=if($bold){[System.Drawing.FontStyle]::Bold}else{[System.Drawing.FontStyle]::Regular};[System.Drawing.Font]::new('Arial',$size,$style,[System.Drawing.GraphicsUnit]::Pixel)}
function Text($g,[string]$text,[int]$x,[int]$y,[float]$size,[System.Drawing.Color]$color,[bool]$bold=$false){$f=Font $size $bold;$b=[System.Drawing.SolidBrush]::new($color);$g.DrawString($text,$f,$b,$x,$y);$b.Dispose();$f.Dispose()}
function PlaceImage($g,[string]$path,[int]$x,[int]$y,[int]$maxw,[int]$maxh){$im=[System.Drawing.Image]::FromFile($path);$scale=[Math]::Min($maxw/$im.Width,$maxh/$im.Height);$dw=[int]($im.Width*$scale);$dh=[int]($im.Height*$scale);$dx=$x+[int](($maxw-$dw)/2);$dy=$y+[int](($maxh-$dh)/2);$g.DrawImage($im,$dx,$dy,$dw,$dh);$im.Dispose()}
function Panel($g,[int]$x,[int]$y,[int]$w,[int]$h,[string]$title){$b=[System.Drawing.SolidBrush]::new($pale);$p=[System.Drawing.Pen]::new($line,2);$g.FillRectangle($b,$x,$y,$w,$h);$g.DrawRectangle($p,$x,$y,$w,$h);$b.Dispose();$p.Dispose();Text $g $title ($x+14) ($y+9) 20 $blue $true}
$head=[System.Drawing.SolidBrush]::new($navy);$g.FillRectangle($head,0,0,$w,132);$head.Dispose();$g.DrawLine([System.Drawing.Pen]::new($orange,7),55,150,$w-55,150)
Text $g 'TBW-FEEDER v3.0 - CURRENT CAD RENDER SHEET' 60 28 36 ([System.Drawing.Color]::White) $true
Text $g 'Generated from the current FreeCAD source model - 2026-10-31' 60 82 19 ([System.Drawing.Color]::FromArgb(220,232,240)) $false
Panel $g 55 175 1065 760 '1  Eight-lane feeder bank in the machine layout'
Panel $g 1145 175 600 390 '2  Lane mechanism: servo, rack and one-way feed'
Panel $g 1145 595 600 470 '3  Peel head exploded view'
PlaceImage $g (Join-Path $root 'out\render\feeder.png') 70 215 1035 690
PlaceImage $g (Join-Path $root 'out\render\feeder_mech.png') 1160 220 570 330
PlaceImage $g (Join-Path $PSScriptRoot 'out\peel_exploded.png') 1160 640 570 405
Text $g '8 lanes  |  22 mm pitch  |  each lane has its own servo' 65 965 23 $ink $true
Text $g 'One Nano controls servo signals D2-D9; external 5 V rail supplies servo current.' 65 1003 18 $muted $false
Text $g 'Feed path: SG90 crank -> slider rack -> idler -> pinion -> HF0612 drive roller.' 1160 1082 17 $muted $false
Text $g 'Peel path uses the second one-way bearing, pinch roller, idler and side plate.' 1160 1110 17 $muted $false
$g.DrawLine([System.Drawing.Pen]::new($line,2),55,1170,$w-55,1170)
Text $g 'Render sources: pnp.py render --views feeder,feeder_mech; feeder.ps1 explode.' 60 1194 17 $muted $false
Text $g 'The electronics/schematic diagrams are separate. This sheet describes current v3.0 geometry, not tolerances or a printed-part acceptance report.' 60 1226 17 $muted $false
$bmp.Save($out,[System.Drawing.Imaging.ImageFormat]::Png);$g.Dispose();$bmp.Dispose()
Get-Item $out | Select-Object FullName,Length,LastWriteTime | Format-List
